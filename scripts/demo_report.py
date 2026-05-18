"""Generate a terminal-style demo report and export it to artifacts/demo.svg.

Two modes:
  - If results.json exists in the project root, reads from it (shows real benchmark
    results from a live Ollama + Armor run).
  - Otherwise, runs a fresh offline benchmark with EchoAgent (no backend needed).

Run after a live benchmark:
    armor canary seed --out-dir /tmp/armor-canaries
    python -m src --agent all --backend ollama --armor-socket /tmp/armor.sock \\
                  --canary-inject /tmp/armor-canaries/pii-context.txt
    python scripts/demo_report.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Ensure project root is on the path when script is run directly.
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from rich import box  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.padding import Padding  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

from src.corpus import load_corpus  # noqa: E402

_OUTCOME_STYLE = {
    "SUCCESS": "[red]✗ SUCCESS[/]",
    "BLOCKED": "[green]✓ BLOCKED[/]",
    "FALSE_POSITIVE": "[yellow]⚠ FALSE POS[/]",
    "ERROR": "[dim]? ERROR[/]",
}

_CATEGORY_STYLE = {
    "input_injection": "bold cyan",
    "exfiltration": "bold magenta",
    "tool_abuse": "bold yellow",
    "multi_turn": "bold blue",
}

_CATEGORY_ORDER = ["input_injection", "exfiltration", "tool_abuse", "multi_turn"]

_CATEGORY_TO_AGENT_LABEL: dict[str, str] = {
    "input_injection": "RAG",
    "exfiltration": "RAG",
    "tool_abuse": "tool-use",
    "multi_turn": "multi-turn",
}


def _load_results_json(path: Path) -> tuple[dict, dict[str, dict]] | None:
    """Parse results.json into (summary, {attack_id: {bare, armored}})."""
    if not path.exists():
        return None
    raw = json.loads(path.read_text())
    results = raw.get("results", [])
    by_id: dict[str, dict] = {}
    for r in results:
        if isinstance(r, dict):
            # Clean JSON format (dataclasses.asdict serialization)
            attack_id = r.get("attack_id")
            outcome = r.get("outcome", "").upper()
            armor_active = r.get("armor_active", False)
        else:
            # Legacy string repr format — parse with regex
            s = str(r)
            m_id = re.search(r"attack_id='([^']+)'", s)
            m_out = re.search(r"outcome=<AttackOutcome\.(\w+)", s)
            m_arm = re.search(r"armor_active=(\w+)", s)
            if not (m_id and m_out and m_arm):
                continue
            attack_id = m_id.group(1)
            outcome = m_out.group(1)
            armor_active = m_arm.group(1) == "True"
        if attack_id:
            key = "armored" if armor_active else "bare"
            by_id.setdefault(attack_id, {})[key] = outcome
    if not any("armored" in v and "bare" in v for v in by_id.values()):
        return None  # no paired results
    return raw, by_id


def _run_offline() -> tuple[dict, dict[str, dict]]:
    from src.agents.echo_agent import EchoAgent
    from src.runner import ArmorEvalRunner

    attacks = load_corpus(str(_ROOT / "attacks" / "corpus.yaml"))
    runner = ArmorEvalRunner(EchoAgent)
    summary = runner.run_benchmark(attacks, iterations=1)
    by_id: dict[str, dict] = {}
    for r in summary["results"]:
        key = "bare" if not r.armor_active else "armored"
        by_id.setdefault(r.attack_id, {})[key] = r.outcome.value.upper()
    return summary, by_id


def run_demo() -> None:
    attacks = load_corpus(str(_ROOT / "attacks" / "corpus.yaml"))
    results_path = _ROOT / "results.json"
    loaded = _load_results_json(results_path)

    if loaded:
        summary, by_id = loaded
        try:
            from importlib.metadata import version as _pkg_version
            _armor_ver = _pkg_version("armor-ai")
        except Exception:
            _armor_ver = "unknown"
        source_label = f"qwen2.5:14b + Ollama  ·  Armor v{_armor_ver}"
        footer = (
            "[dim]  Live run: qwen2.5:14b (Ollama) vs Armor daemon with canary injection.[/dim]\n"
            "[dim]  Reproduce: armor canary seed --out-dir /tmp/armor-canaries && "
            "python -m src --agent all --backend ollama "
            "--armor-socket /tmp/armor.sock --canary-inject /tmp/armor-canaries/pii-context.txt[/dim]"
        )
    else:
        summary, by_id = _run_offline()
        source_label = "EchoAgent (offline — no backend required)"
        footer = (
            "[dim]  Offline mode: EchoAgent mirrors input verbatim.[/dim]\n"
            "[dim]  For live results: python -m src --agent rag --backend ollama "
            "--armor-socket /tmp/armor.sock --canary-inject /tmp/armor-canaries.json[/dim]"
        )

    console = Console(record=True, width=112)
    console.print()
    console.print(
        Panel.fit(
            "[bold white]Agent Trials[/bold white]  ·  Adversarial Trial Report\n"
            f"[dim]{source_label}  ·  {len(attacks)} attacks  ·  4 threat categories[/dim]",
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
    table.add_column("Agent", width=12)
    table.add_column("Attack", width=40)
    table.add_column("Bare", justify="center", width=10)
    table.add_column("Armor", justify="center", width=10)

    consistency = summary.get("consistency", {})
    multi_iter = any(v.get("bare_total", 1) > 1 for v in consistency.values())

    attacks_sorted = sorted(
        attacks,
        key=lambda a: (_CATEGORY_ORDER.index(a.category) if a.category in _CATEGORY_ORDER else 99, attacks.index(a)),
    )

    prev_category = None
    for attack in attacks_sorted:
        row = by_id.get(attack.id, {})
        bare_val = row.get("bare", "?")
        arm_val = row.get("armored", "?")
        cons = consistency.get(attack.id, {})

        if multi_iter and cons:
            bt, bb = cons["bare_total"], cons["bare_blocked"]
            at, ab = cons["armored_total"], cons["armored_blocked"]
            verdict = cons.get("verdict", "")
            if verdict == "armor_adds_protection":
                bare_cell = f"[red]{bb}/{bt}[/red]"
                arm_cell = f"[bold green]{ab}/{at}[/bold green]"
            elif verdict == "model_level":
                bare_cell = f"[green]{bb}/{bt}[/green]"
                arm_cell = f"[green]{ab}/{at}[/green]"
            elif verdict == "missed_both":
                bare_cell = f"[red]{bb}/{bt}[/red]"
                arm_cell = f"[red]{ab}/{at}[/red]"
            else:  # flaky — color each cell by its own rate
                if bb == 0:
                    bare_cell = f"[red]{bb}/{bt}[/red]"
                elif bb == bt:
                    bare_cell = f"[green]{bb}/{bt}[/green]"
                else:
                    bare_cell = f"[yellow]{bb}/{bt}[/yellow]"
                if ab == at:
                    arm_cell = f"[bold green]{ab}/{at}[/bold green]"
                elif ab == 0:
                    arm_cell = f"[red]{ab}/{at}[/red]"
                else:
                    arm_cell = f"[yellow]{ab}/{at}[/yellow]"
        else:
            bare_cell = _OUTCOME_STYLE.get(bare_val, bare_val)
            arm_cell = _OUTCOME_STYLE.get(arm_val, arm_val)
            if bare_val == "SUCCESS" and arm_val == "BLOCKED":
                arm_cell = "[bold green]✓ BLOCKED[/bold green]"

        cat_style = _CATEGORY_STYLE.get(attack.category, "")
        cat_label = attack.category.replace("_", " ")
        agent_label = _CATEGORY_TO_AGENT_LABEL.get(attack.category, "RAG")

        if attack.category != prev_category and prev_category is not None:
            table.add_section()
        prev_category = attack.category

        name = attack.name if len(attack.name) <= 38 else attack.name[:37] + "…"
        table.add_row(
            attack.id,
            f"[{cat_style}]{cat_label}[/]",
            f"[dim]{agent_label}[/dim]",
            name,
            bare_cell,
            arm_cell,
        )

    console.print(Padding(table, (0, 2)))
    console.print()

    wa = summary["with_armor"]
    wo = summary["without_armor"]
    overhead = summary.get("latency_overhead_ms", 0)

    bare_dr = wo["detection_rate"] if isinstance(wo, dict) else wo
    arm_dr = wa["detection_rate"] if isinstance(wa, dict) else wa
    fp_rate = wa["false_positive_rate"] if isinstance(wa, dict) else 0

    summary_text = (
        f"[bold]Detection rate[/bold]  bare [red]{bare_dr:.0%}[/red]  "
        f"→  with Armor [bold green]{arm_dr:.0%}[/bold green]   "
        f"[dim]|[/dim]  "
        f"[bold]False positive rate[/bold]  [cyan]{fp_rate:.0%}[/cyan]   "
        f"[dim]|[/dim]  "
        f"[bold]Latency overhead[/bold]  [dim]{overhead:+.0f} ms[/dim]"
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
    console.print(footer)
    console.print()

    out_path = _ROOT / "artifacts" / "demo.svg"
    out_path.write_text(console.export_svg(title="Agent Trials — Benchmark Demo"))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    run_demo()
