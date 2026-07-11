from __future__ import annotations

from bookworm.agents.student import StudentAgent
from bookworm.core.grading import grade_response
from bookworm.models.probe import Probe, ProbeAttempt, ProbeBank, ProbeMode
from bookworm.models.session import LearningSession


def select_practice_probes(
    bank: ProbeBank,
    skill_ids: list[str],
    mode: ProbeMode,
    *,
    limit: int = 5,
    exclude_ids: set[str] | None = None,
) -> list[Probe]:
    exclude_ids = exclude_ids or set()
    candidates: list[Probe] = []
    for skill_id in skill_ids:
        for probe in bank.by_skill(skill_id):
            if not probe.allowed_in(mode):
                continue
            if probe.id in exclude_ids:
                continue
            if probe not in candidates:
                candidates.append(probe)
    # Prefer slightly harder after study
    candidates.sort(key=lambda p: (-p.difficulty, p.id))
    return candidates[:limit]


def run_practice(
    session: LearningSession,
    bank: ProbeBank,
    student: StudentAgent,
    *,
    limit: int = 5,
) -> list[ProbeAttempt]:
    already = {a.probe_id for a in session.attempts}
    probes = select_practice_probes(
        bank,
        session.gap_skill_ids,
        session.mode,
        limit=limit,
        exclude_ids=already,
    )
    # If everything was already seen, allow re-practice of gap skills
    if not probes:
        probes = select_practice_probes(
            bank, session.gap_skill_ids, session.mode, limit=limit, exclude_ids=set()
        )

    attempts: list[ProbeAttempt] = []
    notes_blob = "\n".join(
        f"- {n.title}: {n.summary}" for n in session.study_notes
    )
    for probe in probes:
        response = student.answer(probe, mode=session.mode, study_context=notes_blob)
        correct, grade_notes = grade_response(probe, response, session.mode)
        attempt = ProbeAttempt(
            probe_id=probe.id,
            response=response,
            correct=correct,
            mode=session.mode,
            skill_ids=list(probe.skill_ids),
            notes=grade_notes,
            metadata={"phase": "practice"},
        )
        attempts.append(attempt)
        session.attempts.append(attempt)
        if correct is not None:
            for skill_id in probe.skill_ids:
                session.upsert_score(skill_id, correct=correct)
    return attempts
