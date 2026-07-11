"""Free local LLM/VLM backend via Ollama HTTP API (stdlib only — no paid keys)."""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_HOST = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama3.2"
DEFAULT_VISION_MODEL = "moondream"

# Prefer tiny local models when present (stingy / low-RAM machines).
_PREFERRED_MODELS = (
    "smollm2:360m",
    "gemma3:270m",
    "qwen3:0.6b",
    "qwen2.5:0.5b",
    "llama3.2:1b",
    "llama3.2",
    "llama3.2:latest",
)

# Vision-capable model name hints (Ollama tags vary).
_VISION_HINTS = (
    "moondream",
    "llava",
    "bakllava",
    "minicpm-v",
    "minicpm",
    "llama3.2-vision",
    "llama3.2-vision:latest",
    "qwen2-vl",
    "qwen2.5-vl",
    "gemma3:4b",
    "gemma3:12b",
    "gemma3:27b",
)

_PREFERRED_VISION = (
    "moondream",
    "moondream:latest",
    "llava",
    "llava:latest",
    "llava:7b",
    "minicpm-v",
    "llama3.2-vision",
    "qwen2.5-vl",
)


def ollama_host() -> str:
    return os.environ.get("BOOKWORM_OLLAMA_HOST", DEFAULT_HOST).rstrip("/")


def list_ollama_models(timeout: float = 2.0) -> list[str]:
    host = ollama_host()
    req = urllib.request.Request(f"{host}/api/tags", method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return [m.get("name", "") for m in data.get("models", []) if m.get("name")]


def _pick_preferred(installed: list[str], preferred: tuple[str, ...], fallback: str) -> str:
    if not installed:
        return fallback
    for pref in preferred:
        for name in installed:
            if name == pref or name.startswith(pref + ":") or name.startswith(pref):
                return name
    return installed[0]


def ollama_model() -> str:
    """Env override, else a small installed model, else DEFAULT_MODEL."""
    if env := os.environ.get("BOOKWORM_OLLAMA_MODEL"):
        return env
    try:
        installed = list_ollama_models()
    except Exception:  # noqa: BLE001
        return DEFAULT_MODEL
    return _pick_preferred(installed, _PREFERRED_MODELS, DEFAULT_MODEL)


def is_likely_vision_model(name: str) -> bool:
    lower = name.lower()
    return any(h in lower for h in _VISION_HINTS)


def list_vision_models(timeout: float = 2.0) -> list[str]:
    try:
        return [m for m in list_ollama_models(timeout=timeout) if is_likely_vision_model(m)]
    except Exception:  # noqa: BLE001
        return []


def ollama_vision_model() -> str:
    """Env override, else a vision model if installed, else DEFAULT_VISION_MODEL."""
    if env := os.environ.get("BOOKWORM_OLLAMA_VISION_MODEL"):
        return env
    try:
        installed = list_ollama_models()
    except Exception:  # noqa: BLE001
        return DEFAULT_VISION_MODEL
    vision = [m for m in installed if is_likely_vision_model(m)]
    if vision:
        return _pick_preferred(vision, _PREFERRED_VISION, vision[0])
    return DEFAULT_VISION_MODEL


def check_ollama(timeout: float = 2.0) -> tuple[bool, str]:
    """Return (ok, message)."""
    host = ollama_host()
    try:
        models = list_ollama_models(timeout=timeout)
        if not models:
            return (
                True,
                f"Ollama up at {host} but no models pulled "
                f"(try: ollama pull smollm2:360m)",
            )
        return True, f"Ollama up at {host}; models: {', '.join(models[:8])}"
    except urllib.error.URLError as e:
        return False, f"Ollama not reachable at {host}: {e}"
    except Exception as e:  # noqa: BLE001 — doctor should never crash
        return False, f"Ollama check failed: {e}"


def check_ollama_vision(timeout: float = 2.0) -> tuple[bool, str]:
    """Return (ok, message) for multimodal / vision readiness."""
    ok, msg = check_ollama(timeout=timeout)
    if not ok:
        return False, msg
    vision = list_vision_models(timeout=timeout)
    chosen = ollama_vision_model()
    if not vision:
        return (
            False,
            f"Ollama up but no vision model detected. "
            f"Try: ollama pull {DEFAULT_VISION_MODEL}  "
            f"(or set BOOKWORM_OLLAMA_VISION_MODEL)",
        )
    return True, f"vision models: {', '.join(vision[:6])}; default={chosen}"


def _encode_image(path: Path | str) -> str:
    data = Path(path).read_bytes()
    return base64.b64encode(data).decode("ascii")


def chat(
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    host: str | None = None,
    temperature: float = 0.2,
    timeout: float = 120.0,
) -> str:
    """Call Ollama /api/chat and return assistant text."""
    host = (host or ollama_host()).rstrip("/")
    model = model or ollama_model()
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{host}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Ollama request failed ({host}, model={model}). "
            f"Is `ollama serve` running? Detail: {e}"
        ) from e

    message = data.get("message") or {}
    content = message.get("content")
    if not content:
        raise RuntimeError(f"Ollama returned empty content: {data!r}")
    return str(content).strip()


def chat_vision(
    prompt: str,
    image_paths: list[Path | str],
    *,
    model: str | None = None,
    host: str | None = None,
    temperature: float = 0.1,
    timeout: float = 180.0,
) -> str:
    """Multimodal chat: one user message with images (base64) + text prompt."""
    if not image_paths:
        raise ValueError("chat_vision requires at least one image path")
    images_b64 = [_encode_image(p) for p in image_paths]
    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": prompt,
            "images": images_b64,
        }
    ]
    return chat(
        messages,
        model=model or ollama_vision_model(),
        host=host,
        temperature=temperature,
        timeout=timeout,
    )
