import json
import os

import pytest

from dashboard.helpers import load_results, save_results
from src.agents.echo_agent import EchoAgent
from src.corpus import load_corpus
from src.runner import ArmorEvalRunner


def _real_summary():
    attacks = load_corpus("attacks/corpus.yaml")
    return ArmorEvalRunner(EchoAgent).run_benchmark(attacks[:2], iterations=1)


# --- save_results ---


def test_save_results_creates_file(tmp_path):
    # TC-018-01
    path = str(tmp_path / "out.json")
    save_results({"total_attacks": 1}, path)
    assert os.path.exists(path)


def test_save_results_writes_valid_json(tmp_path):
    # TC-018-02
    path = str(tmp_path / "out.json")
    save_results({"total_attacks": 1}, path)
    with open(path) as f:
        data = json.load(f)
    assert isinstance(data, dict)


def test_save_results_raises_on_unwritable_path():
    # TC-018-03
    with pytest.raises(OSError):
        save_results({}, "/no/such/dir/results.json")


# --- Round-trip ---


def test_round_trip_preserves_top_level_keys(tmp_path):
    # TC-018-04
    summary = _real_summary()
    path = str(tmp_path / "results.json")
    save_results(summary, path)
    loaded = load_results(path)
    assert set(summary.keys()) == set(loaded.keys())


def test_round_trip_preserves_total_attacks(tmp_path):
    # TC-018-05
    summary = _real_summary()
    path = str(tmp_path / "results.json")
    save_results(summary, path)
    assert load_results(path)["total_attacks"] == summary["total_attacks"]
