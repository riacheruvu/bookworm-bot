from __future__ import annotations

from bookworm.models.session import LearningSession, StudyNote
from bookworm.models.skill import SkillGraph
from bookworm.reading.page_ingest import PageLibrary, study_pages_for_skills


def build_study_plan(
    session: LearningSession,
    skill_graph: SkillGraph,
    library: PageLibrary,
) -> list[str]:
    """Map gap skills → book page ids / refs to read next."""
    plan: list[str] = []
    by_id = skill_graph.by_id()

    for skill_id in session.gap_skill_ids:
        skill = by_id.get(skill_id)
        if not skill:
            continue
        # Prefer explicit book_refs on the skill
        for ref in skill.book_refs:
            if ref not in plan:
                plan.append(ref)
        # Fall back to pages tagged with this skill
        for page in library.pages_for_skill(skill_id):
            if page.id not in plan:
                plan.append(page.id)

    session.study_plan = plan
    return plan


def run_study(
    session: LearningSession,
    library: PageLibrary,
    *,
    max_pages: int = 3,
) -> list[StudyNote]:
    """Ingest planned pages into study notes (mock VLM/OCR for now)."""
    page_ids = session.study_plan[:max_pages]
    notes = study_pages_for_skills(library, page_ids, skill_ids=session.gap_skill_ids)
    session.study_notes.extend(notes)
    return notes
