"""Minimal script equivalent of `bookworm run`."""

from bookworm.core.domain_loader import load_domain
from bookworm.core.loop import run_learning_loop
from bookworm.models.probe import ProbeMode


def main() -> None:
    skills, bank, library = load_domain("mechanics_demo")
    session = run_learning_loop(
        skill_graph=skills,
        probe_bank=bank,
        library=library,
        mode=ProbeMode.serious,
    )
    print("session:", session.id)
    print("gaps:", session.gap_skill_ids)
    print("study:", session.study_plan)
    print("improved:", session.metadata.get("improved"))
    print(session.post_eval)


if __name__ == "__main__":
    main()
