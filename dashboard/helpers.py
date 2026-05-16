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
