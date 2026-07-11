from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from bookworm.models.session import StudyNote


class Page(BaseModel):
    """A mocked 'physical' book page.

    Later: image_path from camera / phone photo / Reachy Mini frame.
    For v0 we ship markdown-ish text files as stand-ins for OCR/VLM output.
    """

    id: str
    title: str = ""
    skill_ids: list[str] = Field(default_factory=list)
    book_refs: list[str] = Field(default_factory=list)
    # Path to image if you drop photos in (optional)
    image_path: str | None = None
    # Pre-extracted or hand-written page text (OCR mock)
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

        # Prefer pages.json index if present
        index = pages_dir / "pages.json"
        if index.is_file():
            raw = json.loads(index.read_text(encoding="utf-8"))
            for item in raw.get("pages", raw if isinstance(raw, list) else []):
                page = Page.model_validate(item)
                # Resolve relative image / sidecar text
                if page.image_path and not Path(page.image_path).is_absolute():
                    candidate = pages_dir / page.image_path
                    if candidate.is_file():
                        page.image_path = str(candidate)
                text_sidecar = pages_dir / f"{page.id}.md"
                if not page.text and text_sidecar.is_file():
                    page.text = text_sidecar.read_text(encoding="utf-8")
                pages.append(page)
            return cls(pages=pages)

        # Fallback: one .md file per page
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
    """Mock VLM/OCR study pass — structure a page into notes."""
    skills = skill_ids or page.skill_ids
    summary = page.text.strip().split("\n\n")[0][:400] if page.text else page.title
    key_ideas = list(page.key_ideas)
    if not key_ideas and page.text:
        # crude bullets
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
) -> list[StudyNote]:
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
        notes.append(extract_study_note(page, skill_ids=skill_ids or page.skill_ids))
    return notes
