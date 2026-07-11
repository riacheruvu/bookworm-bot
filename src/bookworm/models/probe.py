from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ProbeMode(str, Enum):
    """How strict / flexible probing should be.

    serious      — fixed answer key, graded objectively (default for real progress)
    exploratory  — open-ended; agent can invent follow-ups; softer grading
    flexible     — mix: structured core + optional creative stretch
    """

    serious = "serious"
    exploratory = "exploratory"
    flexible = "flexible"


class Probe(BaseModel):
    id: str
    prompt: str
    skill_ids: list[str] = Field(default_factory=list)
    # For serious mode: exact or normalized expected answer
    expected_answer: str | None = None
    # Optional multiple acceptable answers (case-insensitive match by default)
    acceptable_answers: list[str] = Field(default_factory=list)
    # Hints / rubric for exploratory or LLM judges later
    rubric: str | None = None
    difficulty: int = Field(default=1, ge=1, le=5)
    # If set, only run under these modes (empty = all modes)
    modes: list[ProbeMode] = Field(default_factory=list)
    # Optional book grounding (which pages this probe tests)
    book_refs: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    # Exploratory: agent may propose a variant of this probe
    allow_agent_variants: bool = False

    def allowed_in(self, mode: ProbeMode) -> bool:
        if not self.modes:
            return True
        return mode in self.modes

    def all_acceptable(self) -> list[str]:
        answers = list(self.acceptable_answers)
        if self.expected_answer:
            answers.insert(0, self.expected_answer)
        return answers


class ProbeAttempt(BaseModel):
    probe_id: str
    response: str
    correct: bool | None = None  # None = ungraded / exploratory
    mode: ProbeMode = ProbeMode.serious
    skill_ids: list[str] = Field(default_factory=list)
    notes: str = ""
    # If the agent mutated the probe in exploratory mode
    variant_of: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProbeBank(BaseModel):
    domain: str
    probes: list[Probe] = Field(default_factory=list)

    def for_mode(self, mode: ProbeMode) -> list[Probe]:
        return [p for p in self.probes if p.allowed_in(mode)]

    def by_skill(self, skill_id: str) -> list[Probe]:
        return [p for p in self.probes if skill_id in p.skill_ids]

    def get(self, probe_id: str) -> Probe | None:
        for p in self.probes:
            if p.id == probe_id:
                return p
        return None

    @classmethod
    def from_json(cls, path: Path | str) -> ProbeBank:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(data)
