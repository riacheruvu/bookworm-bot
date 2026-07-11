from bookworm.core.grading import grade_response
from bookworm.models.probe import Probe, ProbeMode


def test_exact_match():
    probe = Probe(id="t", prompt="?", expected_answer="newton", acceptable_answers=["N"])
    ok, _ = grade_response(probe, "Newton", ProbeMode.serious)
    assert ok is True


def test_numeric():
    probe = Probe(id="t", prompt="?", expected_answer="5")
    ok, _ = grade_response(probe, "5.0", ProbeMode.serious)
    assert ok is True


def test_wrong():
    probe = Probe(id="t", prompt="?", expected_answer="5")
    ok, _ = grade_response(probe, "0", ProbeMode.serious)
    assert ok is False


def test_exploratory_ungraded_without_key():
    probe = Probe(id="t", prompt="invent something")
    ok, notes = grade_response(probe, "a story", ProbeMode.exploratory)
    assert ok is None
    assert "ungraded" in notes
