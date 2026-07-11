from bookworm.core.domain_loader import load_domain


def test_pages_load_with_text():
    _, _, library = load_domain("mechanics_demo")
    assert len(library.pages) >= 5
    page = library.get("page_newton")
    assert page is not None
    assert "F = ma" in page.text or "ΣF" in page.text or "PROBE_HINT" in page.text
