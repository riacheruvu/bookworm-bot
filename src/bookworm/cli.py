from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bookworm import __version__
from bookworm.agents.student import StudentAgent
from bookworm.core.domain_loader import list_domains, load_domain
from bookworm.core.loop import run_learning_loop, save_session
from bookworm.models.probe import ProbeMode

app = typer.Typer(
    name="bookworm",
    help="Bookworm Bot — probe gaps, read books, practice, get better.",
    no_args_is_help=True,
)
console = Console()

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SESSIONS = _REPO_ROOT / "data" / "sessions"


@app.callback()
def main() -> None:
    """Bookworm Bot CLI."""


@app.command("version")
def version() -> None:
    """Print version."""
    console.print(f"bookworm-bot {__version__}")


@app.command("domains")
def domains() -> None:
    """List available learning domains."""
    found = list_domains()
    if not found:
        console.print("[yellow]No domains found under data/domains[/yellow]")
        raise typer.Exit(1)
    for name in found:
        console.print(f" • {name}")


@app.command("run")
def run(
    domain: str = typer.Option("mechanics_demo", "--domain", "-d", help="Domain folder name"),
    mode: ProbeMode = typer.Option(
        ProbeMode.serious,
        "--mode",
        "-m",
        help="Probe seriousness: serious | exploratory | flexible",
    ),
    probe_limit: int = typer.Option(6, "--probe-limit", help="Max probes in phase 1"),
    practice_limit: int = typer.Option(4, "--practice-limit", help="Max practice items"),
    max_pages: int = typer.Option(3, "--max-pages", help="Max book pages to study"),
    allow_variants: bool = typer.Option(
        False,
        "--variants/--no-variants",
        help="Let the agent invent probe variants (also on in exploratory)",
    ),
    sessions_dir: Optional[Path] = typer.Option(
        None, "--sessions-dir", help="Where to write session JSON"
    ),
    save: bool = typer.Option(True, "--save/--no-save", help="Persist session JSON"),
) -> None:
    """Run one full learning loop on a domain."""
    skills, bank, library = load_domain(domain)
    student = StudentAgent(backend="mock")
    out_dir = sessions_dir or _DEFAULT_SESSIONS

    console.print(
        Panel.fit(
            f"[bold]domain[/bold]={domain}  [bold]mode[/bold]={mode.value}\n"
            f"skills={len(skills.skills)}  probes={len(bank.probes)}  pages={len(library.pages)}",
            title="Bookworm Bot",
        )
    )

    session = run_learning_loop(
        skill_graph=skills,
        probe_bank=bank,
        library=library,
        student=student,
        mode=mode,
        probe_limit=probe_limit,
        practice_limit=practice_limit,
        max_study_pages=max_pages,
        allow_variants=allow_variants,
        sessions_dir=out_dir if save else None,
    )

    _print_session(session)

    if save:
        path = out_dir / f"{session.id}.json"
        if not path.is_file():
            path = save_session(session, out_dir)
        console.print(f"\n[dim]session saved → {path}[/dim]")


@app.command("show-session")
def show_session(
    path: Path = typer.Argument(..., help="Path to session JSON"),
) -> None:
    """Pretty-print a saved session."""
    data = json.loads(path.read_text(encoding="utf-8"))
    console.print_json(data=data)


def _print_session(session) -> None:
    console.print("\n[bold cyan]Gaps diagnosed[/bold cyan]")
    if session.gap_skill_ids:
        for g in session.gap_skill_ids:
            console.print(f"  • {g}")
    else:
        console.print("  (none — student already strong?)")

    console.print("\n[bold cyan]Study plan[/bold cyan]")
    for ref in session.study_plan or ["(empty)"]:
        console.print(f"  • {ref}")

    if session.study_notes:
        console.print("\n[bold cyan]Pages studied[/bold cyan]")
        for note in session.study_notes:
            console.print(f"  • [green]{note.page_id}[/green] — {note.title}")
            if note.key_ideas:
                console.print(f"      ideas: {', '.join(note.key_ideas[:3])}")

    heat = Table(title="Skill heatmap")
    heat.add_column("skill")
    heat.add_column("attempts", justify="right")
    heat.add_column("correct", justify="right")
    heat.add_column("accuracy", justify="right")
    for sid, score in sorted(session.skill_scores.items()):
        heat.add_row(
            sid,
            str(score.attempts),
            str(score.correct),
            f"{score.accuracy:.0%}",
        )
    console.print()
    console.print(heat)

    report = session.post_eval or {}
    probe = report.get("probe", {})
    practice = report.get("practice", {})
    console.print(
        f"\n[bold]Probe accuracy:[/bold]  {_fmt_acc(probe.get('accuracy'))} "
        f"({probe.get('n_correct')}/{probe.get('n_graded')} graded)"
    )
    console.print(
        f"[bold]Practice accuracy:[/bold] {_fmt_acc(practice.get('accuracy'))} "
        f"({practice.get('n_correct')}/{practice.get('n_graded')} graded)"
    )
    improved = session.metadata.get("improved")
    if improved is True:
        console.print("[bold green]Signal: improved after study ✓[/bold green]")
    elif improved is False:
        console.print("[bold yellow]Signal: no improvement yet — tweak study/probes[/bold yellow]")
    else:
        console.print("[dim]Signal: inconclusive (need graded probe + practice)[/dim]")


def _fmt_acc(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.0%}"


if __name__ == "__main__":
    app()
