from __future__ import annotations

from collections import defaultdict

from bookworm.models.probe import ProbeAttempt
from bookworm.models.session import LearningSession
from bookworm.models.skill import SkillGraph, SkillScore


def update_scores_from_attempts(
    session: LearningSession, attempts: list[ProbeAttempt]
) -> None:
    for attempt in attempts:
        if attempt.correct is None:
            # Ungraded: still count as an attempt only if you want — skip for gaps
            continue
        for skill_id in attempt.skill_ids:
            session.upsert_score(skill_id, correct=attempt.correct)


def diagnose_gaps(
    session: LearningSession,
    skill_graph: SkillGraph,
    *,
    max_gaps: int = 5,
) -> list[str]:
    """Return ordered skill ids that need study (worst first, prereqs preferred)."""
    scores = session.skill_scores
    gap_ids: list[str] = []

    # Prefer skills that were attempted and look weak
    ranked: list[tuple[float, str]] = []
    for skill in skill_graph.skills:
        score = scores.get(skill.id) or SkillScore(skill_id=skill.id)
        if score.is_gap:
            # Lower accuracy + more attempts = clearer gap
            severity = 1.0 - score.accuracy
            if score.attempts == 0:
                severity = 0.3  # unknown but untested — lower priority
            ranked.append((severity, skill.id))

    ranked.sort(key=lambda x: (-x[0], x[1]))
    for _, skill_id in ranked:
        # Pull prerequisites first if they are also gaps
        for pre in skill_graph.prerequisite_ids(skill_id):
            pre_score = scores.get(pre) or SkillScore(skill_id=pre)
            if pre_score.is_gap and pre not in gap_ids:
                gap_ids.append(pre)
        if skill_id not in gap_ids:
            gap_ids.append(skill_id)
        if len(gap_ids) >= max_gaps:
            break

    session.gap_skill_ids = gap_ids
    return gap_ids


def skill_heatmap(session: LearningSession) -> dict[str, dict[str, float | int]]:
    out: dict[str, dict[str, float | int]] = {}
    for skill_id, score in session.skill_scores.items():
        out[skill_id] = {
            "attempts": score.attempts,
            "correct": score.correct,
            "accuracy": round(score.accuracy, 3),
        }
    return out


def aggregate_failures(attempts: list[ProbeAttempt]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for a in attempts:
        if a.correct is False:
            for s in a.skill_ids:
                counts[s] += 1
    return dict(counts)
