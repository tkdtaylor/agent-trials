"""Export a clean per-attack analysis JSON from results.json.

Produces analysis.json with full attack payloads, bare vs. armored outcomes,
agent responses, and Armor verdict details — suitable for sharing with the
Armor project to identify gaps and reach 100% detection.

Usage:
    python scripts/export_analysis.py                          # reads results.json
    python scripts/export_analysis.py --input /path/to/results.json --output analysis.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.corpus import load_corpus


def _load_results(path: Path) -> list[dict]:
    raw = json.loads(path.read_text())
    results = raw.get("results", [])
    clean = []
    for r in results:
        if isinstance(r, dict):
            clean.append(r)
        else:
            # Legacy string repr — skip; re-run benchmark with updated code to get clean JSON
            print(f"Warning: skipping legacy string repr result. Re-run the benchmark to get clean JSON.", file=sys.stderr)
    return clean


def export_analysis(input_path: Path, output_path: Path) -> None:
    attacks_by_id = {a.id: a for a in load_corpus(str(_ROOT / "attacks" / "corpus.yaml"))}
    raw = json.loads(input_path.read_text())
    results = _load_results(input_path)
    consistency = raw.get("consistency", {})
    multi_iter = any(v.get("bare_total", 1) > 1 for v in consistency.values())

    # Group by attack_id → {bare: last RunResult dict, armored: last RunResult dict}
    by_id: dict[str, dict] = {}
    for r in results:
        aid = r.get("attack_id")
        if not aid:
            continue
        key = "armored" if r.get("armor_active") else "bare"
        by_id.setdefault(aid, {})[key] = r

    rows = []
    for aid, pair in sorted(by_id.items()):
        attack = attacks_by_id.get(aid)
        bare = pair.get("bare", {})
        armored = pair.get("armored", {})
        bare_outcome = (bare.get("outcome") or "").upper()
        armored_outcome = (armored.get("outcome") or "").upper()
        cons = consistency.get(aid, {})

        if multi_iter and cons:
            verdict = cons.get("verdict", "unknown")
            armor_added = verdict == "armor_adds_protection"
            missed = verdict == "missed_both"
        else:
            armor_added = bare_outcome == "SUCCESS" and armored_outcome == "BLOCKED"
            missed = bare_outcome == "SUCCESS" and armored_outcome == "SUCCESS"

        agent_type = bare.get("agent_type") or armored.get("agent_type") or "unknown"
        row = {
            "attack_id": aid,
            "name": attack.name if attack else aid,
            "category": attack.category if attack else "",
            "agent_type": agent_type,
            "payload": attack.payload if attack else "",
            "expected_behavior": attack.expected_behavior if attack else "",
            "bare": {
                "outcome": bare_outcome,
                "response": (bare.get("trace") or {}).get("final_output", ""),
                "latency_ms": (bare.get("trace") or {}).get("latency_ms", 0),
                "verdict_reasoning": bare.get("verdict_reasoning", ""),
            },
            "armored": {
                "outcome": armored_outcome,
                "response": (armored.get("trace") or {}).get("final_output", ""),
                "latency_ms": (armored.get("trace") or {}).get("latency_ms", 0),
                "verdict_reasoning": armored.get("verdict_reasoning", ""),
                "armor_blocks": (armored.get("trace") or {}).get("armor_blocks", []),
            },
            "consistency": cons if cons else None,
            "armor_added_protection": armor_added,
            "missed_by_armor": missed,
        }
        rows.append(row)

    missed_rows = [r for r in rows if r["missed_by_armor"]]
    protected = [r for r in rows if r["armor_added_protection"]]

    output = {
        "summary": {
            "total_attacks": len(rows),
            "multi_iteration": multi_iter,
            "iterations": next(iter(consistency.values()), {}).get("bare_total", 1) if consistency else 1,
            "armor_added_protection": len(protected),
            "missed_by_armor": len(missed_rows),
            "attacks_blocked_in_both_modes": sum(
                1 for r in rows
                if (
                    (r["consistency"] or {}).get("verdict") == "model_level"
                    if multi_iter
                    else r["bare"]["outcome"] == "BLOCKED" and r["armored"]["outcome"] == "BLOCKED"
                )
            ),
        },
        "missed_by_armor": [
            {
                "attack_id": r["attack_id"], "name": r["name"], "category": r["category"],
                "payload": r["payload"],
                "consistency": r["consistency"],
                "bare_response": r["bare"]["response"],
                "armored_response": r["armored"]["response"],
            }
            for r in missed_rows
        ],
        "armor_added_protection": [
            {
                "attack_id": r["attack_id"], "name": r["name"], "category": r["category"],
                "consistency": r["consistency"],
                "armor_blocks": r["armored"]["armor_blocks"],
            }
            for r in protected
        ],
        "all_attacks": rows,
    }

    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    iters = output["summary"]["iterations"]
    iter_label = f" ({iters} iterations)" if multi_iter else " (single run)"
    print(f"Wrote {output_path}{iter_label}")
    print(f"  Total attacks: {output['summary']['total_attacks']}")
    print(f"  Armor added protection: {len(protected)}")
    print(f"  Missed by Armor: {len(missed_rows)}")
    if missed_rows:
        print("\nAttacks missed by Armor:")
        for r in missed_rows:
            cons = r["consistency"]
            rate = f"  bare {cons['bare_blocked']}/{cons['bare_total']}, armored {cons['armored_blocked']}/{cons['armored_total']}" if cons else ""
            print(f"  [{r['category']}] {r['attack_id']} — {r['name']}{rate}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export per-attack analysis from results.json")
    parser.add_argument("--input", default=str(_ROOT / "results.json"), help="Path to results.json")
    parser.add_argument("--output", default=str(_ROOT / "artifacts" / "analysis.json"), help="Output path")
    args = parser.parse_args()
    export_analysis(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()
