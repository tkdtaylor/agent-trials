import os
import tempfile
from collections import Counter
from pathlib import Path

import pytest
import yaml

from src.corpus import load_corpus
from src.types import AttackVector

_CORPUS_PATH = Path(__file__).parent.parent / "attacks" / "corpus.yaml"
_REQUIRED_FIELDS = {"id", "name", "payload", "expected_behavior", "category"}
_VALID_BEHAVIORS = {"ignore", "refuse", "allow"}
_CATEGORIES = {"input_injection", "exfiltration", "tool_abuse", "multi_turn"}

VALID_ATTACK = dict(
    id="t-001",
    name="Test",
    payload="payload",
    expected_behavior="ignore",
    category="input_injection",
)


def write_corpus(attacks: list[dict]) -> str:
    fd, path = tempfile.mkstemp(suffix=".yaml")
    with os.fdopen(fd, "w") as f:
        yaml.dump({"attacks": attacks}, f)
    return path


# --- Happy path ---


def test_returns_list():
    # TC-016-01
    path = write_corpus([VALID_ATTACK])
    try:
        assert isinstance(load_corpus(path), list)
    finally:
        os.unlink(path)


def test_contains_attack_vector_objects():
    # TC-016-02
    path = write_corpus([VALID_ATTACK])
    try:
        assert all(isinstance(a, AttackVector) for a in load_corpus(path))
    finally:
        os.unlink(path)


def test_fields_mapped_correctly():
    # TC-016-03
    path = write_corpus([VALID_ATTACK])
    try:
        a = load_corpus(path)[0]
        assert a.id == "t-001"
        assert a.name == "Test"
        assert a.payload == "payload"
        assert a.expected_behavior == "ignore"
        assert a.category == "input_injection"
    finally:
        os.unlink(path)


def test_multiple_attacks_returned():
    # TC-016-04
    attack2 = {**VALID_ATTACK, "id": "t-002"}
    path = write_corpus([VALID_ATTACK, attack2])
    try:
        assert len(load_corpus(path)) == 2
    finally:
        os.unlink(path)


def test_empty_attacks_returns_empty_list():
    # TC-016-05
    path = write_corpus([])
    try:
        assert load_corpus(path) == []
    finally:
        os.unlink(path)


# --- Error paths ---


def test_missing_file_raises_file_not_found():
    # TC-016-06
    with pytest.raises(FileNotFoundError):
        load_corpus("/tmp/does_not_exist_armor_eval_corpus.yaml")


def test_missing_required_field_raises_value_error():
    # TC-016-07
    bad = {k: v for k, v in VALID_ATTACK.items() if k != "id"}
    path = write_corpus([bad])
    try:
        with pytest.raises(ValueError):
            load_corpus(path)
    finally:
        os.unlink(path)


def test_value_error_names_missing_field():
    # TC-016-08
    bad = {k: v for k, v in VALID_ATTACK.items() if k != "id"}
    path = write_corpus([bad])
    try:
        with pytest.raises(ValueError, match="id"):
            load_corpus(path)
    finally:
        os.unlink(path)


# --- Real corpus ---


def test_loads_real_corpus_without_error():
    # TC-016-09
    attacks = load_corpus("attacks/corpus.yaml")
    assert len(attacks) > 0


def test_real_corpus_all_attack_vectors():
    # TC-016-10
    attacks = load_corpus("attacks/corpus.yaml")
    assert all(isinstance(a, AttackVector) for a in attacks)


# --- Corpus quality checks (task 018) ---


def _raw() -> list[dict]:
    return yaml.safe_load(_CORPUS_PATH.read_text())["attacks"]


def test_corpus_has_at_least_20_attacks():
    # T-018-01
    assert len(_raw()) >= 20


def test_all_corpus_entries_have_required_fields():
    # T-018-02
    for entry in _raw():
        missing = _REQUIRED_FIELDS - set(entry.keys())
        assert not missing, f"Entry {entry.get('id')!r} missing: {missing}"


def test_no_duplicate_attack_ids():
    # T-018-03
    ids = [e["id"] for e in _raw()]
    dupes = [x for x in set(ids) if ids.count(x) > 1]
    assert len(ids) == len(set(ids)), f"Duplicate IDs: {dupes}"


def test_category_coverage():
    # T-018-04
    counts = Counter(e["category"] for e in _raw())
    for cat in _CATEGORIES:
        assert counts[cat] >= 4, f"Category '{cat}' has {counts[cat]} vectors (need ≥4)"


def test_expected_behavior_values():
    # T-018-05
    for entry in _raw():
        assert entry["expected_behavior"] in _VALID_BEHAVIORS, (
            f"Entry {entry['id']!r} invalid expected_behavior: {entry['expected_behavior']!r}"
        )
