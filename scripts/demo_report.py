"""Generate a terminal-style demo report and export it to artifacts/demo.svg."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on the path when script is run directly.
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich import box

from src.agents.echo_agent import EchoAgent
from src.corpus import load_corpus
from src.runner import ArmorEvalRunner
from src.types import AttackOutcome

_OUTCOME_STYLE = {
    AttackOutcome.SUCCESS: ("[red]✗ SUCCESS[/]", "red"),
    AttackOutcome.BLOCKED: ("[green]✓ BLOCKED[/]", "green"),
    AttackOutcome.FALSE_POSITIVE: ("[yellow]⚠ FP[/]", "yellow"),
    AttackOutcome.ERROR: ("[dim]? ERROR[/]", "dim"),
}

_CATEGORY_STYLE = {
    "input_injection": "bold cyan",
    "exfiltration": "bold magenta",
    "tool_abuse": "bold yellow",
    "multi_turn": "bold blue",
}


def _outcome_cell(outcome: AttackOutcome) -> str:
    return _OUTCOME_STYLE.get(outcome, ("?", ""))[0]


def run_demo() -> None:
    attacks = load_corpus(
        str(Path(__file__).parent.parent / "attacks" / "corpus.yaml")
    )
    runner = ArmorEvalRunner(EchoAgent)
    summary = runner.run_benchmark(attacks, iterations=1)

    # Index results by (attack_id, armor_active)
    results = summary["results"]
    by_id: dict[str, dict] = {}
    for r in results:
        if r.attack_id not in by_id:
            by_id[r.attack_id] = {}
        by_id[r.attack_id]["bare" if not r.armor_active else "armored"] = r

    console = Console(record=True, width=110)

    console.print()
    console.print(
        Panel.fit(
            "[bold white]Armor Eval[/bold white]  ·  Adversarial Benchmark Report\n"
            "[dim]Agent: EchoAgent (offline)  ·  "
            f"{len(attacks)} attacks  ·  4 threat categories[/dim]",
            border_style="bright_blue",
            padding=(0, 4),
        )
    )
    console.print()

    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold white on grey23",
        border_style="grey50",
        expand=False,
    )
    table.add_column("ID", style="dim", width=12)
    table.add_column("Category", width=18)
    table.add_column("Attack", width=44)
    table.add_column("Bare", justify="center", width=14)
    table.add_column("With Armor", justify="center", width=14)

    prev_category = None
    for attack in attacks:
        row = by_id.get(attack.id, {})
        bare_r = row.get("bare")
        arm_r = row.get("armored")

        bare_cell = _outcome_cell(bare_r.outcome) if bare_r else "–"
        arm_cell = _outcome_cell(arm_r.outcome) if arm_r else "–"

        cat_style = _CATEGORY_STYLE.get(attack.category, "")
        cat_label = attack.category.replace("_", " ")

        if attack.category != prev_category and prev_category is not None:
            table.add_section()
        prev_category = attack.category

        name = attack.name if len(attack.name) <= 42 else attack.name[:41] + "…"
        table.add_row(
            attack.id,
            f"[{cat_style}]{cat_label}[/]",
            name,
            bare_cell,
            arm_cell,
        )

    console.print(Padding(table, (0, 2)))
    console.print()

    wa = summary["with_armor"]
    wo = summary["without_armor"]
    overhead = summary["latency_overhead_ms"]

    summary_text = (
        f"[bold]Detection rate[/bold]  bare [red]{wo['detection_rate']:.0%}[/red]  "
        f"→  with Armor [green]{wa['detection_rate']:.0%}[/green]   "
        f"[dim]|[/dim]  "
        f"[bold]False positive rate[/bold]  [cyan]{wa['false_positive_rate']:.0%}[/cyan]   "
        f"[dim]|[/dim]  "
        f"[bold]Latency overhead[/bold]  "
        f"[dim]{overhead:+.2f} ms[/dim]"
    )
    console.print(
        Panel(
            summary_text,
            title="[bold white]Summary[/bold white]",
            border_style="bright_blue",
            padding=(0, 2),
        )
    )
    console.print()
    console.print(
        "[dim]  Note: EchoAgent mirrors input verbatim — outcomes reflect judge heuristics, not live Armor protection.[/dim]\n"
        "[dim]  For real results: python -m src --agent rag --backend ollama --model qwen2.5:14b[/dim]"
    )
    console.print()

    out_path = Path(__file__).parent.parent / "artifacts" / "demo.svg"
    out_path.write_text(
        console.export_svg(title="Armor Eval — Benchmark Demo")
    )
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    run_demo()
