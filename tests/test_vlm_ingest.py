import json
from pathlib import Path

from bookworm.reading.ingest import ingest_images, save_notes_to_domain, slugify
from bookworm.reading.vlm import extract_json_object, mock_read_page_image, study_note_to_markdown


def test_extract_json_object_plain():
    data = extract_json_object('{"title": "Hi", "summary": "There"}')
    assert data is not None
    assert data["title"] == "Hi"


def test_extract_json_object_fenced():
    raw = '```json\n{"title": "FBD", "key_ideas": ["isolate"]}\n```'
    data = extract_json_object(raw)
    assert data is not None
    assert data["title"] == "FBD"


def test_mock_read_uses_sidecar(tmp_path: Path):
    img = tmp_path / "page_fbd.png"
    img.write_bytes(_minimal_png())
    (tmp_path / "page_fbd.md").write_text(
        "# Free-body diagrams\n\n- Isolate one body\n\nPROBE_HINT: fbd_what => all external forces\n",
        encoding="utf-8",
    )
    note = mock_read_page_image(img, skill_ids=["free_body"])
    assert note.page_id == "page_fbd"
    assert "Isolate" in " ".join(note.key_ideas) or "Isolate" in note.raw_text
    assert "free_body" in note.skill_ids


def test_ingest_and_save(tmp_path: Path):
    photos = tmp_path / "photos"
    photos.mkdir()
    img = photos / "newton_laws.png"
    img.write_bytes(_minimal_png())
    (photos / "newton_laws.md").write_text(
        "# Newton\n\n- F = ma\n\nPROBE_HINT: n2_formula => F=ma\n",
        encoding="utf-8",
    )

    results = ingest_images(photos, backend="mock", skill_ids=["newtons_2nd"])
    assert len(results) == 1
    assert results[0][1].page_id == "newton_laws"

    domain_root = tmp_path / "domains"
    written = save_notes_to_domain(results, "demo_domain", data_root=domain_root)
    assert any(p.name == "pages.json" for p in written)

    pages_json = domain_root / "demo_domain" / "pages" / "pages.json"
    data = json.loads(pages_json.read_text(encoding="utf-8"))
    assert data["pages"][0]["id"] == "newton_laws"
    assert data["pages"][0]["image_path"].startswith("images/")

    md = domain_root / "demo_domain" / "pages" / "newton_laws.md"
    assert md.is_file()
    assert "F = ma" in md.read_text(encoding="utf-8") or "Newton" in md.read_text(
        encoding="utf-8"
    )


def test_study_note_markdown_roundtrip():
    from bookworm.models.session import StudyNote

    n = StudyNote(
        page_id="p1",
        title="T",
        summary="S",
        key_ideas=["a"],
        formulas=["F=ma"],
        skill_ids=["x"],
        raw_text="body",
    )
    md = study_note_to_markdown(n)
    assert "# T" in md
    assert "F=ma" in md


def test_slugify():
    assert slugify("My Page!!") == "my_page"


def _minimal_png() -> bytes:
    """1x1 PNG (stdlib only)."""
    import base64

    # tiny valid 1x1 PNG
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
