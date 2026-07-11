from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from bookworm.models.probe import ProbeAttempt, ProbeMode
from bookworm.models.skill import SkillScore


class SessionPhase(str, Enum):
    probe = "probe"
    diagnose = "diagnose"
    study = "study"
    practice = "practice"
    evaluate = "evaluate"
    done = "done"


class StudyNote(BaseModel):
    page_id: str
    title: str = ""
    summary: str = ""
    key_ideas: list[str] = Field(default_factory=list)
    formulas: list[str] = Field(default_factory=list)
    skill_ids: list[str] = Field(default_factory=list)
    raw_text: str = ""


class LearningSession(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    domain: str
    mode: ProbeMode = ProbeMode.serious
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    phase: SessionPhase = SessionPhase.probe
    attempts: list[ProbeAttempt] = Field(default_factory=list)
    skill_scores: dict[str, SkillScore] = Field(default_factory=dict)
    gap_skill_ids: list[str] = Field(default_factory=list)
    study_notes: list[StudyNote] = Field(default_factory=list)
    study_plan: list[str] = Field(default_factory=list)  # book_refs or page ids
    pre_eval: dict[str, Any] = Field(default_factory=dict)
    post_eval: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def upsert_score(self, skill_id: str, correct: bool) -> None:
        score = self.skill_scores.get(skill_id) or SkillScore(skill_id=skill_id)
        score.attempts += 1
        if correct:
            score.correct += 1
        score.last_seen = datetime.now(timezone.utc).isoformat()
        self.skill_scores[skill_id] = score
