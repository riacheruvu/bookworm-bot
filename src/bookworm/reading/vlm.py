"""Local multimodal page reading (Ollama vision) + offline mock."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from bookworm.models.session import StudyNote
from bookworm.reading.page_ingest import Page

VisionBackend = Literal["mock", "ollama"]

_PAGE_JSON_SCHEMA_HINT = """
Return ONLY valid JSON (no markdown fences) with this shape:
{
  "title": "short page title",
  "summary": "2-4 sentence summary of the page content",
  "key_ideas": ["bullet idea 1", "bullet idea 2"],
  "formulas": ["F = ma", "..."],
  "raw_text": "transcribed readable text from the page",
  "skill_ids": []
}
If the image is a textbook/mechanics page, extract equations carefully.
If unreadable, still return JSON with your best effort in summary/raw_text.
""".strip()


def extract_json_object(text: str) -> dict[str, Any] | None:
    """Best-effort parse of a JSON object from model output."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def mock_read_page_image(
    image_path: Path | str,
    *,
    page_id: str | None = None,
    skill_ids: list[str] | None = None,
) -> StudyNote:
    """Offline stand-in: sidecar .md/.txt next to image, else filename stub."""
    path = Path(image_path)
    pid = page_id or path.stem
    skills = list(skill_ids or [])

    raw = ""
    for sidecar in (path.with_suffix(".md"), path.with_suffix(".txt")):
        if sidecar.is_file():
            raw = sidecar.read_text(encoding="utf-8")
            break

    if not raw:
        raw = (
            f"[mock vision] No sidecar text for {path.name}. "
            f"Add {path.stem}.md next to the image, or use --backend ollama "
            f"with a vision model (ollama pull moondream)."
        )

    key_ideas: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith(("- ", "* ")):
            key_ideas.append(line[2:].strip())

    title_line = next((ln.strip("# ").strip() for ln in raw.splitlines() if ln.strip()), pid)
    summary = raw.strip().split("\n\n")[0][:400]

    return StudyNote(
        page_id=pid,
        title=title_line[:120],
        summary=summary,
        key_ideas=key_ideas[:12],
        formulas=[],
        skill_ids=skills,
        raw_text=raw,
    )


def ollama_read_page_image(
    image_path: Path | str,
    *,
    page_id: str | None = None,
    skill_ids: list[str] | None = None,
    model: str | None = None,
    extra_hint: str = "",
) -> StudyNote:
    """Read a page photo with a local Ollama vision model."""
    from bookworm.agents.ollama import chat_vision

    path = Path(image_path)
    pid = page_id or path.stem
    skills = list(skill_ids or [])

    prompt = (
        "You are helping a student study from a photo of a textbook page.\n"
        f"{_PAGE_JSON_SCHEMA_HINT}\n"
    )
    if skills:
        prompt += f"\nSuggested skill tags (use if relevant): {skills}\n"
    if extra_hint:
        prompt += f"\nContext: {extra_hint}\n"

    raw_response = chat_vision(prompt, [path], model=model)
    parsed = extract_json_object(raw_response)

    if not parsed:
        return StudyNote(
            page_id=pid,
            title=pid,
            summary=raw_response[:400],
            key_ideas=[],
            formulas=[],
            skill_ids=skills,
            raw_text=raw_response,
        )

    out_skills = parsed.get("skill_ids") or skills
    if not isinstance(out_skills, list):
        out_skills = skills
    out_skills = [str(s) for s in out_skills]

    key_ideas = parsed.get("key_ideas") or []
    if not isinstance(key_ideas, list):
        key_ideas = [str(key_ideas)]
    formulas = parsed.get("formulas") or []
    if not isinstance(formulas, list):
        formulas = [str(formulas)]

    raw_text = str(parsed.get("raw_text") or raw_response)
    summary = str(parsed.get("summary") or raw_text[:400])
    title = str(parsed.get("title") or pid)

    return StudyNote(
        page_id=pid,
        title=title[:120],
        summary=summary,
        key_ideas=[str(x) for x in key_ideas][:12],
        formulas=[str(x) for x in formulas][:12],
        skill_ids=out_skills,
        raw_text=raw_text,
    )


def read_page_image(
    image_path: Path | str,
    *,
    backend: VisionBackend = "mock",
    page_id: str | None = None,
    skill_ids: list[str] | None = None,
    model: str | None = None,
    extra_hint: str = "",
) -> StudyNote:
    if backend == "ollama":
        return ollama_read_page_image(
            image_path,
            page_id=page_id,
            skill_ids=skill_ids,
            model=model,
            extra_hint=extra_hint,
        )
    return mock_read_page_image(image_path, page_id=page_id, skill_ids=skill_ids)


def study_note_to_markdown(note: StudyNote) -> str:
    """Serialize a study note into a page .md (with optional probe hints later)."""
    lines = [
        f"# {note.title}",
        "",
        note.summary.strip(),
        "",
    ]
    if note.key_ideas:
        lines.append("## Key ideas")
        for idea in note.key_ideas:
            lines.append(f"- {idea}")
        lines.append("")
    if note.formulas:
        lines.append("## Formulas")
        for f in note.formulas:
            lines.append(f"- `{f}`")
        lines.append("")
    if note.skill_ids:
        lines.append("## Skills")
        for s in note.skill_ids:
            lines.append(f"- {s}")
        lines.append("")
    lines.append("## Transcript")
    lines.append("")
    lines.append(note.raw_text.strip())
    lines.append("")
    return "\n".join(lines)


def page_from_study_note(
    note: StudyNote,
    *,
    image_path: str | None = None,
) -> Page:
    return Page(
        id=note.page_id,
        title=note.title,
        skill_ids=list(note.skill_ids),
        book_refs=[note.page_id],
        image_path=image_path,
        text=study_note_to_markdown(note),
        key_ideas=list(note.key_ideas),
        formulas=list(note.formulas),
    )
