"""Free local LLM backend via Ollama HTTP API (stdlib only — no paid keys)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


DEFAULT_HOST = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama3.2"

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


def ollama_host() -> str:
    return os.environ.get("BOOKWORM_OLLAMA_HOST", DEFAULT_HOST).rstrip("/")


def list_ollama_models(timeout: float = 2.0) -> list[str]:
    host = ollama_host()
    req = urllib.request.Request(f"{host}/api/tags", method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return [m.get("name", "") for m in data.get("models", []) if m.get("name")]


def ollama_model() -> str:
    """Env override, else a small installed model, else DEFAULT_MODEL."""
    if env := os.environ.get("BOOKWORM_OLLAMA_MODEL"):
        return env
    try:
        installed = list_ollama_models()
    except Exception:  # noqa: BLE001
        return DEFAULT_MODEL
    if not installed:
        return DEFAULT_MODEL
    # Exact / prefix match against preferences
    for pref in _PREFERRED_MODELS:
        for name in installed:
            if name == pref or name.startswith(pref + ":") or name.startswith(pref):
                return name
    return installed[0]


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


def chat(
    messages: list[dict[str, str]],
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
            f"Ollama request failed ({host}). Is `ollama serve` running? "
            f"Pull a model with `ollama pull {model}`. Detail: {e}"
        ) from e

    message = data.get("message") or {}
    content = message.get("content")
    if not content:
        raise RuntimeError(f"Ollama returned empty content: {data!r}")
    return str(content).strip()
