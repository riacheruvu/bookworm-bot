from __future__ import annotations

import json
from pathlib import Path

from typing import TYPE_CHECKING

from bookworm.agents.student import StudentAgent
from bookworm.core.eval import did_improve, evaluate_session
from bookworm.core.gap_assessor import diagnose_gaps, update_scores_from_attempts
from bookworm.core.practice import run_practice
from bookworm.core.probe_runner import run_probes
from bookworm.core.study import build_study_plan, run_study
from bookworm.models.probe import ProbeBank, ProbeMode
from bookworm.models.session import LearningSession, SessionPhase
from bookworm.models.skill import SkillGraph
from bookworm.reading.page_ingest import PageLibrary

if TYPE_CHECKING:
    from bookworm.reading.vlm import VisionBackend


def run_learning_loop(
    *,
    skill_graph: SkillGraph,
    probe_bank: ProbeBank,
    library: PageLibrary,
    student: StudentAgent | None = None,
    mode: ProbeMode = ProbeMode.serious,
    probe_limit: int | None = 6,
    practice_limit: int = 4,
    max_study_pages: int = 3,
    allow_variants: bool = False,
    sessions_dir: Path | str | None = None,
    vision_backend: VisionBackend | None = None,
    vision_model: str | None = None,
) -> LearningSession:
    """Full phase loop: probe → diagnose → study → practice → evaluate."""
    student = student or StudentAgent(backend="mock")
    session = LearningSession(domain=skill_graph.domain, mode=mode)
    if vision_backend:
        session.metadata["vision_backend"] = vision_backend

    # 1) Probe
    session.phase = SessionPhase.probe
    probe_attempts = run_probes(
        session,
        probe_bank,
        student,
        limit=probe_limit,
        allow_variants=allow_variants
        or mode in (ProbeMode.exploratory, ProbeMode.flexible),
    )
    update_scores_from_attempts(session, probe_attempts)
    session.pre_eval = {
        "n": len(probe_attempts),
        "correct": sum(1 for a in probe_attempts if a.correct),
    }

    # 2) Diagnose
    session.phase = SessionPhase.diagnose
    diagnose_gaps(session, skill_graph)

    # 3) Study
    session.phase = SessionPhase.study
    build_study_plan(session, skill_graph, library)
    run_study(
        session,
        library,
        max_pages=max_study_pages,
        vision_backend=vision_backend,
        vision_model=vision_model,
    )
    # Student absorbs notes into memory for better practice answers
    student.ingest_study_notes(session.study_notes)

    # 4) Practice
    session.phase = SessionPhase.practice
    run_practice(session, probe_bank, student, limit=practice_limit)

    # 5) Evaluate
    session.phase = SessionPhase.evaluate
    evaluate_session(session)
    session.metadata["improved"] = did_improve(session)
    session.phase = SessionPhase.done

    if sessions_dir is not None:
        save_session(session, Path(sessions_dir))

    return session


def save_session(session: LearningSession, sessions_dir: Path) -> Path:
    sessions_dir.mkdir(parents=True, exist_ok=True)
    path = sessions_dir / f"{session.id}.json"
    path.write_text(session.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_session(path: Path | str) -> LearningSession:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return LearningSession.model_validate(data)
