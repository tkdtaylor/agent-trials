import yaml

from src.types import AttackVector

_REQUIRED_FIELDS = ("id", "name", "payload", "expected_behavior", "category")


def load_corpus(path: str) -> list[AttackVector]:
    with open(path) as f:
        data = yaml.safe_load(f)
    attacks = data.get("attacks") or []
    result = []
    for entry in attacks:
        for field in _REQUIRED_FIELDS:
            if field not in entry:
                raise ValueError(f"attack entry missing required field: '{field}'")
        result.append(
            AttackVector(
                id=entry["id"],
                name=entry["name"],
                payload=entry["payload"],
                expected_behavior=entry["expected_behavior"],
                category=entry["category"],
            )
        )
    return result
