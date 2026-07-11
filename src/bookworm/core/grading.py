from __future__ import annotations

import re

from bookworm.models.probe import Probe, ProbeMode


def _normalize(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    # Light numeric normalization: strip trailing .0 from simple numbers
    text = re.sub(r"^(-?\d+)\.0+$", r"\1", text)
    return text


def grade_response(probe: Probe, response: str, mode: ProbeMode) -> tuple[bool | None, str]:
    """Return (correct, notes). correct is None when intentionally ungraded."""
    response = response.strip()
    if not response:
        return False, "empty response"

    if mode is ProbeMode.exploratory and not probe.all_acceptable():
        # Open-ended exploratory probes: no hard grade in v0
        return None, "exploratory — left ungraded (add an LLM judge later)"

    acceptable = [_normalize(a) for a in probe.all_acceptable()]
    if not acceptable:
        if mode is ProbeMode.flexible:
            return None, "no answer key — flexible mode left ungraded"
        return False, "no answer key configured"

    got = _normalize(response)
    if got in acceptable:
        return True, "exact match"

    # Allow answer embedded in a longer response: "the answer is 9.8"
    for ans in acceptable:
        if ans and ans in got:
            return True, f"matched substring: {ans}"

    # Numeric tolerance for simple floats
    try:
        got_f = float(got.split()[0].rstrip(".,"))
        for ans in acceptable:
            try:
                if abs(got_f - float(ans)) < 1e-6:
                    return True, "numeric match"
            except ValueError:
                continue
    except (ValueError, IndexError):
        pass

    return False, f"expected one of {probe.all_acceptable()!r}"
