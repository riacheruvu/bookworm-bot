from bookworm.agents.student import StudentAgent
from bookworm.core.domain_loader import load_domain
from bookworm.core.loop import run_learning_loop
from bookworm.models.probe import ProbeMode


def test_mechanics_demo_loop_improves_or_runs():
    skills, bank, library = load_domain("mechanics_demo")
    session = run_learning_loop(
        skill_graph=skills,
        probe_bank=bank,
        library=library,
        student=StudentAgent(backend="mock"),
        mode=ProbeMode.serious,
        probe_limit=6,
        practice_limit=4,
        max_study_pages=3,
        sessions_dir=None,
    )
    assert session.domain == "mechanics_demo"
    assert session.attempts
    assert session.study_notes or session.gap_skill_ids == []
    report = session.post_eval
    assert "probe" in report
    assert "practice" in report


def test_exploratory_mode_runs():
    skills, bank, library = load_domain("mechanics_demo")
    session = run_learning_loop(
        skill_graph=skills,
        probe_bank=bank,
        library=library,
        mode=ProbeMode.exploratory,
        probe_limit=4,
        practice_limit=2,
        sessions_dir=None,
    )
    assert session.mode is ProbeMode.exploratory
