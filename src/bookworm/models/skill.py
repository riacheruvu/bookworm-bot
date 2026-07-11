from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class Skill(BaseModel):
    """A learnable skill node in the domain graph."""

    id: str
    name: str
    description: str = ""
    prerequisites: list[str] = Field(default_factory=list)
    # Optional links into the "library" (chapter ids, page tags, book sections)
    book_refs: list[str] = Field(default_factory=list)


class SkillScore(BaseModel):
    skill_id: str
    attempts: int = 0
    correct: int = 0
    last_seen: str | None = None

    @property
    def accuracy(self) -> float:
        if self.attempts == 0:
            return 0.0
        return self.correct / self.attempts

    @property
    def is_gap(self) -> bool:
        """Conservative: few tries or low accuracy counts as a gap."""
        if self.attempts == 0:
            return True
        if self.attempts < 2:
            return self.correct == 0
        return self.accuracy < 0.6


class SkillGraph(BaseModel):
    domain: str
    skills: list[Skill] = Field(default_factory=list)

    def by_id(self) -> dict[str, Skill]:
        return {s.id: s for s in self.skills}

    def get(self, skill_id: str) -> Skill | None:
        return self.by_id().get(skill_id)

    def prerequisite_ids(self, skill_id: str) -> list[str]:
        skill = self.get(skill_id)
        return list(skill.prerequisites) if skill else []

    @classmethod
    def from_yaml(cls, path: Path | str) -> SkillGraph:
        data: dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(data)
