import json

from src.types import RunResult


def load_results(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def format_outcome_table(results: list[RunResult]) -> list[dict]:
    return [
        {
            "id": r.attack_id,
            "name": r.attack_name,
            "outcome": r.outcome.value,
            "armor": r.armor_active,
            "latency_ms": r.trace.latency_ms,
        }
        for r in results
    ]


def save_results(summary: dict, path: str) -> None:
    with open(path, "w") as f:
        json.dump(summary, f, default=str, indent=2)


def compute_side_by_side(summary: dict) -> dict:
    return {
        "with_armor": summary.get("with_armor", {}),
        "without_armor": summary.get("without_armor", {}),
    }


def build_attack_table(summary: dict) -> list[dict]:
    """Return one row per unique attack_id with bare/armored outcomes side-by-side."""
    results: list[dict] = summary.get("results", [])
    consistency: dict = summary.get("consistency", {})

    # Index results by (attack_id, armor_active)
    bare_by_id: dict[str, dict] = {}
    armored_by_id: dict[str, dict] = {}
    for r in results:
        aid = r.get("attack_id", "")
        if r.get("armor_active"):
            armored_by_id[aid] = r
        else:
            bare_by_id[aid] = r

    # Collect all unique attack_ids preserving first-seen order
    seen: list[str] = []
    seen_set: set[str] = set()
    for r in results:
        aid = r.get("attack_id", "")
        if aid not in seen_set:
            seen.append(aid)
            seen_set.add(aid)

    rows: list[dict] = []
    for aid in seen:
        bare_r = bare_by_id.get(aid, {})
        arm_r = armored_by_id.get(aid, {})
        ref = bare_r or arm_r  # use whichever is available for metadata

        cons = consistency.get(aid)
        if cons:
            bare_str = f"{cons.get('bare_blocked', 0)}/{cons.get('bare_total', 0)}"
            armored_str = f"{cons.get('armored_blocked', 0)}/{cons.get('armored_total', 0)}"
            verdict = cons.get("verdict", "")
        else:
            bare_str = (bare_r.get("outcome") or "").upper() if bare_r else ""
            armored_str = (arm_r.get("outcome") or "").upper() if arm_r else ""
            verdict = ""

        rows.append(
            {
                "id": aid,
                "name": ref.get("attack_name", ""),
                "category": ref.get("category", ""),
                "agent": ref.get("agent_type", ""),
                "bare": bare_str,
                "armored": armored_str,
                "verdict": verdict,
            }
        )

    return rows
