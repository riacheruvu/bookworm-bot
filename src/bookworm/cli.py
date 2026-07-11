from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bookworm import __version__
from bookworm.agents.student import BackendName, StudentAgent
from bookworm.core.domain_loader import list_domains, load_domain
from bookworm.core.loop import run_learning_loop, save_session
from bookworm.models.probe import ProbeMode
from bookworm.reading.vlm import VisionBackend

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


@app.command("doctor")
def doctor() -> None:
    """Check free local backends (no paid API keys required)."""
    console.print(Panel.fit("[bold]Bookworm doctor[/bold] — $0 path checks", border_style="cyan"))
    console.print("[green]✓[/green] mock student — always available (default)")
    console.print("[green]✓[/green] mock vision — sidecar .md next to images")
    console.print("[green]✓[/green] demo domain files — use `bookworm domains`")

    from bookworm.agents.ollama import (
        check_ollama,
        check_ollama_vision,
        ollama_model,
        ollama_vision_model,
    )

    ok, msg = check_ollama()
    if ok:
        console.print(f"[green]✓[/green] ollama text — {msg}")
        console.print(f"  text model: [cyan]{ollama_model()}[/cyan]")
        console.print("  try: [bold]bookworm run --backend ollama[/bold]")
    else:
        console.print(f"[yellow]○[/yellow] ollama text — {msg}")
        console.print(
            "  optional: install https://ollama.com then "
            "`ollama pull smollm2:360m`"
        )

    vok, vmsg = check_ollama_vision()
    if vok:
        console.print(f"[green]✓[/green] ollama vision — {vmsg}")
        console.print(f"  vision model: [cyan]{ollama_vision_model()}[/cyan]")
        console.print(
            "  try: [bold]bookworm ingest-pages ./photos --backend ollama[/bold]"
        )
    else:
        console.print(f"[yellow]○[/yellow] ollama vision — {vmsg}")

    console.print(
        "\n[dim]Paid cloud APIs are intentionally optional. "
        "See docs/LOCAL_STACK.md[/dim]"
    )


@app.command("ingest-pages")
def ingest_pages(
    source: Path = typer.Argument(..., help="Image file or folder of page photos"),
    domain: str = typer.Option(
        "mechanics_demo",
        "--domain",
        "-d",
        help="Domain to write pages into",
    ),
    backend: VisionBackend = typer.Option(
        "mock",
        "--backend",
        "-b",
        help="Vision backend: mock (sidecar/offline) | ollama (local VLM)",
    ),
    skills: Optional[str] = typer.Option(
        None,
        "--skills",
        "-s",
        help="Comma-separated skill ids to tag (e.g. free_body,newtons_2nd)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        help="Ollama vision model override",
    ),
    hint: str = typer.Option(
        "",
        "--hint",
        help="Optional context for the VLM (chapter topic, etc.)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Read pages but do not write into the domain",
    ),
    no_copy: bool = typer.Option(
        False,
        "--no-copy",
        help="Do not copy images into data/domains/.../pages/images/",
    ),
) -> None:
    """Read book page photos with a local multimodal model (or mock) and save notes."""
    if backend == "ollama":
        from bookworm.agents.ollama import check_ollama_vision

        ok, msg = check_ollama_vision()
        if not ok:
            console.print(f"[red]Vision backend unavailable:[/red] {msg}")
            console.print(
                "Fall back: [bold]bookworm ingest-pages ... --backend mock[/bold] "
                "(add a .md sidecar next to each image)"
            )
            raise typer.Exit(2)

    skill_ids = [s.strip() for s in skills.split(",") if s.strip()] if skills else None

    from bookworm.reading.ingest import ingest_images, save_notes_to_domain

    console.print(
        Panel.fit(
            f"[bold]source[/bold]={source}  [bold]backend[/bold]={backend}  "
            f"[bold]domain[/bold]={domain}",
            title="ingest-pages",
        )
    )

    try:
        results = ingest_images(
            source,
            backend=backend,
            skill_ids=skill_ids,
            model=model,
            extra_hint=hint,
        )
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1) from e

    for img, note in results:
        console.print(f"\n[bold green]{img.name}[/bold green] → [cyan]{note.page_id}[/cyan]")
        console.print(f"  title: {note.title}")
        console.print(f"  summary: {note.summary[:200]}{'…' if len(note.summary) > 200 else ''}")
        if note.key_ideas:
            console.print(f"  ideas: {', '.join(note.key_ideas[:4])}")
        if note.formulas:
            console.print(f"  formulas: {', '.join(note.formulas[:4])}")

    if dry_run:
        console.print("\n[dim]dry-run: nothing written[/dim]")
        return

    written = save_notes_to_domain(
        results,
        domain,
        copy_images=not no_copy,
    )
    console.print(f"\n[bold]Wrote[/bold] {len(written)} path(s) under domain [cyan]{domain}[/cyan]")
    for p in written:
        console.print(f"  • {p}")


@app.command("run")
def run(
    domain: str = typer.Option("mechanics_demo", "--domain", "-d", help="Domain folder name"),
    mode: ProbeMode = typer.Option(
        ProbeMode.serious,
        "--mode",
        "-m",
        help="Probe seriousness: serious | exploratory | flexible",
    ),
    backend: BackendName = typer.Option(
        "mock",
        "--backend",
        "-b",
        help="Student backend: mock (free default) | ollama (free local) | echo",
    ),
    vision: Optional[VisionBackend] = typer.Option(
        None,
        "--vision",
        help="Study pages with vision when image_path is set: mock | ollama",
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
    if backend == "ollama":
        from bookworm.agents.ollama import check_ollama

        ok, msg = check_ollama()
        if not ok:
            console.print(f"[red]Ollama backend unavailable:[/red] {msg}")
            console.print("Fall back with: [bold]bookworm run --backend mock[/bold]")
            console.print("Or see: [bold]docs/LOCAL_STACK.md[/bold]")
            raise typer.Exit(2)

    if vision == "ollama":
        from bookworm.agents.ollama import check_ollama_vision

        ok, msg = check_ollama_vision()
        if not ok:
            console.print(f"[red]Vision unavailable:[/red] {msg}")
            console.print("Use --vision mock or omit --vision (text pages only).")
            raise typer.Exit(2)

    skills, bank, library = load_domain(domain)
    student = StudentAgent(backend=backend)
    out_dir = sessions_dir or _DEFAULT_SESSIONS

    vision_label = vision or "off"
    console.print(
        Panel.fit(
            f"[bold]domain[/bold]={domain}  [bold]mode[/bold]={mode.value}  "
            f"[bold]backend[/bold]={backend}  [bold]vision[/bold]={vision_label}\n"
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
        vision_backend=vision,
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
