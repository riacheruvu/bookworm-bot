"""Ingest page photos into a domain library (local VLM or mock)."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Iterable

from bookworm.core.domain_loader import DEFAULT_DATA_ROOT
from bookworm.models.session import StudyNote
from bookworm.reading.page_ingest import Page, PageLibrary
from bookworm.reading.vlm import (
    VisionBackend,
    page_from_study_note,
    read_page_image,
    study_note_to_markdown,
)

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}


def iter_images(path: Path) -> list[Path]:
    path = Path(path)
    if path.is_file():
        if path.suffix.lower() in IMAGE_SUFFIXES:
            return [path]
        raise ValueError(f"Not an image file: {path}")
    if not path.is_dir():
        raise FileNotFoundError(path)
    files = [
        p
        for p in sorted(path.iterdir())
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
    ]
    return files


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "_", s)
    return s[:80] or "page"


def ingest_images(
    source: Path | str,
    *,
    backend: VisionBackend = "mock",
    skill_ids: list[str] | None = None,
    model: str | None = None,
    extra_hint: str = "",
) -> list[tuple[Path, StudyNote]]:
    """Read one or more images → study notes (does not write domain files)."""
    images = iter_images(Path(source))
    if not images:
        raise FileNotFoundError(f"No images found under {source}")

    results: list[tuple[Path, StudyNote]] = []
    for img in images:
        note = read_page_image(
            img,
            backend=backend,
            page_id=slugify(img.stem),
            skill_ids=skill_ids,
            model=model,
            extra_hint=extra_hint,
        )
        results.append((img, note))
    return results


def save_notes_to_domain(
    notes: Iterable[tuple[Path, StudyNote]],
    domain: str,
    *,
    data_root: Path | str | None = None,
    copy_images: bool = True,
) -> list[Path]:
    """Write notes into data/domains/<domain>/pages/ and update pages.json."""
    root = Path(data_root) if data_root else DEFAULT_DATA_ROOT
    domain_dir = root / domain
    pages_dir = domain_dir / "pages"
    images_dir = pages_dir / "images"
    pages_dir.mkdir(parents=True, exist_ok=True)
    if copy_images:
        images_dir.mkdir(parents=True, exist_ok=True)

    index_path = pages_dir / "pages.json"
    existing: list[dict] = []
    if index_path.is_file():
        raw = json.loads(index_path.read_text(encoding="utf-8"))
        existing = list(raw.get("pages", raw if isinstance(raw, list) else []))

    by_id = {p.get("id"): i for i, p in enumerate(existing) if p.get("id")}
    written: list[Path] = []

    for src_img, note in notes:
        page_id = note.page_id
        rel_image: str | None = None
        if copy_images:
            dest = images_dir / f"{page_id}{src_img.suffix.lower()}"
            shutil.copy2(src_img, dest)
            rel_image = f"images/{dest.name}"

        md_path = pages_dir / f"{page_id}.md"
        md_path.write_text(study_note_to_markdown(note), encoding="utf-8")
        written.append(md_path)

        page = page_from_study_note(note, image_path=rel_image)
        entry = page.model_dump()
        # Keep text empty in JSON if md sidecar exists (loader fills it)
        entry["text"] = ""
        if page_id in by_id:
            existing[by_id[page_id]] = entry
        else:
            by_id[page_id] = len(existing)
            existing.append(entry)

    index_path.write_text(
        json.dumps({"pages": existing}, indent=2) + "\n",
        encoding="utf-8",
    )
    written.append(index_path)
    return written


def enrich_page_with_vision(
    page: Page,
    *,
    backend: VisionBackend = "ollama",
    model: str | None = None,
) -> StudyNote:
    """If page has image_path, read via VLM; else fall back to text extract."""
    from bookworm.reading.page_ingest import extract_study_note

    if page.image_path and Path(page.image_path).is_file():
        return read_page_image(
            page.image_path,
            backend=backend,
            page_id=page.id,
            skill_ids=page.skill_ids,
            model=model,
            extra_hint=page.title,
        )
    return extract_study_note(page)
