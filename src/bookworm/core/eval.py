from __future__ import annotations

from typing import Any

from bookworm.models.probe import ProbeAttempt
from bookworm.models.session import LearningSession


def summarize_attempts(attempts: list[ProbeAttempt]) -> dict[str, Any]:
    graded = [a for a in attempts if a.correct is not None]
    correct = sum(1 for a in graded if a.correct)
    return {
        "n_attempts": len(attempts),
        "n_graded": len(graded),
        "n_correct": correct,
        "accuracy": (correct / len(graded)) if graded else None,
        "n_ungraded": len(attempts) - len(graded),
    }


def evaluate_session(session: LearningSession) -> dict[str, Any]:
    pre_ids = {
        a.probe_id
        for a in session.attempts
        if a.metadata.get("phase") == "probe"
    }
    practice = [a for a in session.attempts if a.metadata.get("phase") == "practice"]
    probe = [a for a in session.attempts if a.metadata.get("phase") == "probe"]

    report = {
        "session_id": session.id,
        "domain": session.domain,
        "mode": session.mode.value,
        "gaps": list(session.gap_skill_ids),
        "study_plan": list(session.study_plan),
        "pages_studied": [n.page_id for n in session.study_notes],
        "probe": summarize_attempts(probe),
        "practice": summarize_attempts(practice),
        "skill_heatmap": {
            sid: {
                "attempts": s.attempts,
                "correct": s.correct,
                "accuracy": round(s.accuracy, 3),
            }
            for sid, s in session.skill_scores.items()
        },
        "probe_ids_seen": sorted(pre_ids),
    }
    session.post_eval = report
    return report


def did_improve(session: LearningSession) -> bool | None:
    """Rough signal: practice accuracy vs probe accuracy (when both graded)."""
    probe = summarize_attempts(
        [a for a in session.attempts if a.metadata.get("phase") == "probe"]
    )
    practice = summarize_attempts(
        [a for a in session.attempts if a.metadata.get("phase") == "practice"]
    )
    if probe["accuracy"] is None or practice["accuracy"] is None:
        return None
    return practice["accuracy"] >= probe["accuracy"]
