from __future__ import annotations

from pathlib import Path

from bookworm.models.probe import ProbeBank
from bookworm.models.skill import SkillGraph
from bookworm.reading.page_ingest import PageLibrary

# Repo root: src/bookworm/core/domain_loader.py → parents[3] = repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_ROOT = _REPO_ROOT / "data" / "domains"


def load_domain(domain: str, data_root: Path | str | None = None) -> tuple[
    SkillGraph, ProbeBank, PageLibrary
]:
    root = Path(data_root) if data_root else DEFAULT_DATA_ROOT
    domain_dir = root / domain
    if not domain_dir.is_dir():
        available = (
            sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []
        )
        raise FileNotFoundError(
            f"Domain '{domain}' not found under {root}. Available: {available}"
        )

    skills = SkillGraph.from_yaml(domain_dir / "skills.yaml")
    probes = ProbeBank.from_json(domain_dir / "probes.json")
    library = PageLibrary.load(domain_dir / "pages")
    return skills, probes, library


def list_domains(data_root: Path | str | None = None) -> list[str]:
    root = Path(data_root) if data_root else DEFAULT_DATA_ROOT
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir())
