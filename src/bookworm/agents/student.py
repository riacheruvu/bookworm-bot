from __future__ import annotations

import hashlib
import re
from typing import Literal

from bookworm.models.probe import Probe, ProbeMode
from bookworm.models.session import StudyNote


class StudentAgent:
    """Pluggable student. Default `mock` is deliberately mediocre until it studies.

    Swap `backend` later for real LLM / VLM / on-robot policies.
    """

    def __init__(
        self,
        backend: Literal["mock", "echo"] = "mock",
        *,
        knowledge: dict[str, str] | None = None,
        seed_name: str = "bookworm",
    ) -> None:
        self.backend = backend
        self.knowledge = knowledge or {}
        self.seed_name = seed_name
        self._studied_skills: set[str] = set()
        self._note_snippets: list[str] = []

    def ingest_study_notes(self, notes: list[StudyNote]) -> None:
        for note in notes:
            self._studied_skills.update(note.skill_ids)
            if note.summary:
                self._note_snippets.append(note.summary)
            for idea in note.key_ideas:
                self._note_snippets.append(idea)
            for formula in note.formulas:
                self._note_snippets.append(formula)
            # Extract answer-like tokens from page text into knowledge
            self._absorb_text(note.raw_text, note.skill_ids)

    def _absorb_text(self, text: str, skill_ids: list[str]) -> None:
        """Very dumb knowledge extraction so the mock student can improve after study."""
        # Patterns like: ANSWER_KEY: free_body -> "draw forces on isolated body"
        for match in re.finditer(
            r"ANSWER_KEY:\s*([a-z0-9_]+)\s*=>\s*(.+)$", text, flags=re.MULTILINE
        ):
            self.knowledge[match.group(1).strip()] = match.group(2).strip()
        for match in re.finditer(
            r"PROBE_HINT:\s*([a-z0-9_-]+)\s*=>\s*(.+)$", text, flags=re.MULTILINE
        ):
            self.knowledge[f"probe:{match.group(1).strip()}"] = match.group(2).strip()
        for sid in skill_ids:
            self.knowledge.setdefault(f"studied:{sid}", "yes")

    def answer(
        self,
        probe: Probe,
        *,
        mode: ProbeMode = ProbeMode.serious,
        study_context: str = "",
    ) -> str:
        if self.backend == "echo":
            return f"[echo] {probe.prompt}"

        # Direct probe hint absorbed from books
        hint = self.knowledge.get(f"probe:{probe.id}")
        if hint:
            return hint

        # If we've studied all skills on this probe, use answer key when known
        if probe.skill_ids and all(
            self.knowledge.get(f"studied:{s}") == "yes" for s in probe.skill_ids
        ):
            if probe.expected_answer:
                return probe.expected_answer
            if probe.acceptable_answers:
                return probe.acceptable_answers[0]

        # Partial study: sometimes get it right (deterministic hash)
        studied_any = any(s in self._studied_skills for s in probe.skill_ids)
        if studied_any and probe.expected_answer:
            h = int(hashlib.md5(f"{self.seed_name}:{probe.id}".encode()).hexdigest(), 16)
            if h % 100 < 70:
                return probe.expected_answer

        # Pre-study: mostly wrong / uncertain, with a few easy wins
        if probe.difficulty <= 1 and probe.expected_answer:
            h = int(hashlib.md5(f"easy:{probe.id}".encode()).hexdigest(), 16)
            if h % 100 < 40:
                return probe.expected_answer

        if mode is ProbeMode.exploratory:
            return (
                f"I'm not sure yet. Related ideas: "
                f"{'; '.join(self._note_snippets[:2]) or 'none studied'}. "
                f"I'd explore: {probe.prompt[:80]}"
            )

        # Deliberately wrong placeholder so gaps light up
        if probe.expected_answer and re.fullmatch(r"-?\d+(\.\d+)?", probe.expected_answer.strip()):
            return "0"
        return "I don't know yet — need to read."

    def maybe_make_variant(self, probe: Probe, *, mode: ProbeMode) -> Probe | None:
        """Exploratory fun: invent a related probe (still skill-tagged)."""
        if mode is ProbeMode.serious:
            return None
        if not probe.allow_agent_variants and mode is not ProbeMode.exploratory:
            return None

        variant = probe.model_copy(
            update={
                "id": f"{probe.id}__variant",
                "prompt": (
                    f"[agent variant] Building on: {probe.prompt} "
                    f"— can you explain a real-world example?"
                ),
                # Drop hard answer key for variants so grading stays soft
                "expected_answer": None,
                "acceptable_answers": [],
                "allow_agent_variants": False,
            }
        )
        return variant
