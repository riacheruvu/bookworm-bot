from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from bookworm.models.session import StudyNote

if TYPE_CHECKING:
    from bookworm.reading.vlm import VisionBackend


class Page(BaseModel):
    """A mocked 'physical' book page.

    image_path: phone photo / screenshot / Reachy Mini frame (optional).
    text: pre-extracted or hand-written page text (OCR/VLM output or markdown).
    """

    id: str
    title: str = ""
    skill_ids: list[str] = Field(default_factory=list)
    book_refs: list[str] = Field(default_factory=list)
    image_path: str | None = None
    text: str = ""
    key_ideas: list[str] = Field(default_factory=list)
    formulas: list[str] = Field(default_factory=list)


class PageLibrary(BaseModel):
    pages: list[Page] = Field(default_factory=list)

    def get(self, page_id: str) -> Page | None:
        for p in self.pages:
            if p.id == page_id or page_id in p.book_refs:
                return p
        return None

    def pages_for_skill(self, skill_id: str) -> list[Page]:
        return [p for p in self.pages if skill_id in p.skill_ids]

    @classmethod
    def load(cls, pages_dir: Path | str) -> PageLibrary:
        pages_dir = Path(pages_dir)
        pages: list[Page] = []
        if not pages_dir.is_dir():
            return cls(pages=pages)

        index = pages_dir / "pages.json"
        if index.is_file():
            raw = json.loads(index.read_text(encoding="utf-8"))
            for item in raw.get("pages", raw if isinstance(raw, list) else []):
                page = Page.model_validate(item)
                if page.image_path and not Path(page.image_path).is_absolute():
                    candidate = pages_dir / page.image_path
                    if candidate.is_file():
                        page.image_path = str(candidate)
                text_sidecar = pages_dir / f"{page.id}.md"
                if not page.text and text_sidecar.is_file():
                    page.text = text_sidecar.read_text(encoding="utf-8")
                pages.append(page)
            return cls(pages=pages)

        for md in sorted(pages_dir.glob("*.md")):
            pages.append(
                Page(
                    id=md.stem,
                    title=md.stem.replace("_", " ").title(),
                    text=md.read_text(encoding="utf-8"),
                )
            )
        return cls(pages=pages)


def extract_study_note(page: Page, skill_ids: list[str] | None = None) -> StudyNote:
    """Text-only study pass (no vision)."""
    skills = skill_ids or page.skill_ids
    summary = page.text.strip().split("\n\n")[0][:400] if page.text else page.title
    key_ideas = list(page.key_ideas)
    if not key_ideas and page.text:
        for line in page.text.splitlines():
            line = line.strip()
            if line.startswith(("- ", "* ")):
                key_ideas.append(line[2:].strip())
    return StudyNote(
        page_id=page.id,
        title=page.title or page.id,
        summary=summary,
        key_ideas=key_ideas[:12],
        formulas=list(page.formulas),
        skill_ids=list(skills),
        raw_text=page.text,
    )


def study_pages_for_skills(
    library: PageLibrary,
    page_ids: list[str],
    skill_ids: list[str] | None = None,
    *,
    vision_backend: VisionBackend | None = None,
    vision_model: str | None = None,
) -> list[StudyNote]:
    """Build study notes for planned pages.

    vision_backend:
      None  — text/markdown only (default, free, stable)
      mock  — if image present, use sidecar/mock vision
      ollama — local multimodal LLM on page images
    """
    notes: list[StudyNote] = []
    for pid in page_ids:
        page = library.get(pid)
        if page is None:
            notes.append(
                StudyNote(
                    page_id=pid,
                    title="missing page",
                    summary=f"No page found for id/ref '{pid}'",
                    skill_ids=list(skill_ids or []),
                )
            )
            continue

        if vision_backend and page.image_path and Path(page.image_path).is_file():
            from bookworm.reading.vlm import read_page_image

            notes.append(
                read_page_image(
                    page.image_path,
                    backend=vision_backend,
                    page_id=page.id,
                    skill_ids=skill_ids or page.skill_ids,
                    model=vision_model,
                    extra_hint=page.title,
                )
            )
        else:
            notes.append(extract_study_note(page, skill_ids=skill_ids or page.skill_ids))
    return notes
