from __future__ import annotations

from bookworm.agents.student import StudentAgent
from bookworm.core.grading import grade_response
from bookworm.models.probe import Probe, ProbeAttempt, ProbeBank, ProbeMode
from bookworm.models.session import LearningSession


def select_probes(
    bank: ProbeBank,
    mode: ProbeMode,
    *,
    limit: int | None = None,
    skill_filter: list[str] | None = None,
) -> list[Probe]:
    probes = bank.for_mode(mode)
    if skill_filter:
        wanted = set(skill_filter)
        probes = [p for p in probes if wanted.intersection(p.skill_ids)]
    probes = sorted(probes, key=lambda p: (p.difficulty, p.id))
    if limit is not None:
        probes = probes[:limit]
    return probes


def run_probes(
    session: LearningSession,
    bank: ProbeBank,
    student: StudentAgent,
    *,
    limit: int | None = None,
    skill_filter: list[str] | None = None,
    allow_variants: bool = False,
) -> list[ProbeAttempt]:
    """Run the probe phase. In exploratory/flexible modes, agent may invent variants."""
    probes = select_probes(bank, session.mode, limit=limit, skill_filter=skill_filter)
    attempts: list[ProbeAttempt] = []

    for probe in probes:
        # Optional agent-authored variant (exploratory fun)
        active = probe
        variant_of = None
        if allow_variants and session.mode in (ProbeMode.exploratory, ProbeMode.flexible):
            if probe.allow_agent_variants or session.mode is ProbeMode.exploratory:
                variant = student.maybe_make_variant(probe, mode=session.mode)
                if variant is not None:
                    active = variant
                    variant_of = probe.id

        response = student.answer(active, mode=session.mode)
        correct, notes = grade_response(active, response, session.mode)
        attempt = ProbeAttempt(
            probe_id=active.id,
            response=response,
            correct=correct,
            mode=session.mode,
            skill_ids=list(active.skill_ids),
            notes=notes,
            variant_of=variant_of,
            metadata={"phase": "probe"},
        )
        attempts.append(attempt)
        session.attempts.append(attempt)

    return attempts
