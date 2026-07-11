from __future__ import annotations

import hashlib
import re
from typing import Literal

from bookworm.models.probe import Probe, ProbeMode
from bookworm.models.session import StudyNote

BackendName = Literal["mock", "echo", "ollama"]


class StudentAgent:
    """Pluggable student.

    - ``mock`` (default): $0, no network, deliberately weak until it studies.
    - ``echo``: debug — returns the prompt.
    - ``ollama``: free local LLM via Ollama (no API keys). Requires `ollama serve`.
    """

    def __init__(
        self,
        backend: BackendName = "mock",
        *,
        knowledge: dict[str, str] | None = None,
        seed_name: str = "bookworm",
        ollama_model: str | None = None,
    ) -> None:
        self.backend = backend
        self.knowledge = knowledge or {}
        self.seed_name = seed_name
        self.ollama_model = ollama_model
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
            self._absorb_text(note.raw_text, note.skill_ids)

    def _absorb_text(self, text: str, skill_ids: list[str]) -> None:
        """Dumb knowledge extraction so the mock student can improve after study."""
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

        if self.backend == "ollama":
            return self._answer_ollama(probe, mode=mode, study_context=study_context)

        return self._answer_mock(probe, mode=mode)

    def _answer_mock(self, probe: Probe, *, mode: ProbeMode) -> str:
        hint = self.knowledge.get(f"probe:{probe.id}")
        if hint:
            return hint

        if probe.skill_ids and all(
            self.knowledge.get(f"studied:{s}") == "yes" for s in probe.skill_ids
        ):
            if probe.expected_answer:
                return probe.expected_answer
            if probe.acceptable_answers:
                return probe.acceptable_answers[0]

        studied_any = any(s in self._studied_skills for s in probe.skill_ids)
        if studied_any and probe.expected_answer:
            h = int(hashlib.md5(f"{self.seed_name}:{probe.id}".encode()).hexdigest(), 16)
            if h % 100 < 70:
                return probe.expected_answer

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

        if probe.expected_answer and re.fullmatch(
            r"-?\d+(\.\d+)?", probe.expected_answer.strip()
        ):
            return "0"
        return "I don't know yet — need to read."

    def _answer_ollama(
        self,
        probe: Probe,
        *,
        mode: ProbeMode,
        study_context: str,
    ) -> str:
        from bookworm.agents.ollama import chat

        notes = study_context.strip() or "\n".join(self._note_snippets[:12])
        system = (
            "You are a careful student solving exercises after reading textbook notes. "
            "Use only the study notes and general reasoning. "
            "For short-answer or numeric questions, reply with ONLY the final answer "
            "(no preamble). For open-ended questions, be brief (2-4 sentences)."
        )
        if mode is ProbeMode.serious:
            system += " Prefer concise exact answers that match SI units when relevant."

        user_parts = []
        if notes:
            user_parts.append(f"Study notes:\n{notes}")
        user_parts.append(f"Question:\n{probe.prompt}")
        if probe.rubric and mode is not ProbeMode.serious:
            user_parts.append(f"Rubric hint:\n{probe.rubric}")

        raw = chat(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": "\n\n".join(user_parts)},
            ],
            model=self.ollama_model,
        )
        return _strip_answer_fencing(raw)

    def maybe_make_variant(self, probe: Probe, *, mode: ProbeMode) -> Probe | None:
        """Exploratory fun: invent a related probe (still skill-tagged)."""
        if mode is ProbeMode.serious:
            return None
        if not probe.allow_agent_variants and mode is not ProbeMode.exploratory:
            return None

        if self.backend == "ollama":
            try:
                return self._variant_ollama(probe)
            except RuntimeError:
                pass  # fall through to template variant

        variant = probe.model_copy(
            update={
                "id": f"{probe.id}__variant",
                "prompt": (
                    f"[agent variant] Building on: {probe.prompt} "
                    f"— can you explain a real-world example?"
                ),
                "expected_answer": None,
                "acceptable_answers": [],
                "allow_agent_variants": False,
            }
        )
        return variant

    def _variant_ollama(self, probe: Probe) -> Probe:
        from bookworm.agents.ollama import chat

        prompt = chat(
            [
                {
                    "role": "system",
                    "content": (
                        "Rewrite the exercise into one related practice question. "
                        "Return ONLY the question text."
                    ),
                },
                {"role": "user", "content": probe.prompt},
            ],
            temperature=0.7,
            model=self.ollama_model,
        )
        return probe.model_copy(
            update={
                "id": f"{probe.id}__variant",
                "prompt": prompt,
                "expected_answer": None,
                "acceptable_answers": [],
                "allow_agent_variants": False,
            }
        )


def _strip_answer_fencing(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    # Common "Answer: X" prefix
    m = re.match(r"^(?:final\s+)?answer\s*[:\-]\s*(.+)$", text, flags=re.I | re.S)
    if m:
        return m.group(1).strip()
    return text
