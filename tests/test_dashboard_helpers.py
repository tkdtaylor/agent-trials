import json
import os
import tempfile

import pytest

from dashboard.helpers import compute_side_by_side, format_outcome_table, load_results
from src.types import AgentTrace, AttackOutcome, RunResult


def make_run_result(
    attack_id="a1",
    attack_name="Test",
    outcome=AttackOutcome.BLOCKED,
    armor_active=True,
    latency_ms=10.0,
    final_output="blocked",
) -> RunResult:
    return RunResult(
        attack_id=attack_id,
        attack_name=attack_name,
        outcome=outcome,
        trace=AgentTrace(
            input_received="payload",
            final_output=final_output,
            latency_ms=latency_ms,
            timestamp="2026-01-01T00:00:00+00:00",
        ),
        armor_active=armor_active,
        verdict_reasoning="reason",
    )


def write_summary_json(summary: dict) -> str:
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(summary, f, default=str)
    return path


# --- load_results ---


def test_load_results_returns_dict():
    # TC-015-01
    path = write_summary_json({"total_attacks": 1, "results": []})
    try:
        assert isinstance(load_results(path), dict)
    finally:
        os.unlink(path)


def test_load_results_has_total_attacks_key():
    # TC-015-02
    path = write_summary_json({"total_attacks": 3, "results": []})
    try:
        assert "total_attacks" in load_results(path)
    finally:
        os.unlink(path)


def test_load_results_raises_on_missing_file():
    # TC-015-03
    with pytest.raises(FileNotFoundError):
        load_results("/tmp/does_not_exist_agent_trials.json")


# --- format_outcome_table ---


def test_format_outcome_table_returns_list():
    # TC-015-04
    assert isinstance(format_outcome_table([make_run_result()]), list)


def test_format_outcome_table_each_row_is_dict():
    # TC-015-05
    rows = format_outcome_table([make_run_result()])
    assert all(isinstance(r, dict) for r in rows)


def test_format_outcome_table_row_has_required_keys():
    # TC-015-06
    row = format_outcome_table([make_run_result()])[0]
    assert {"id", "name", "outcome", "armor", "latency_ms"} <= row.keys()


def test_format_outcome_table_outcome_is_string_value():
    # TC-015-07
    row = format_outcome_table([make_run_result(outcome=AttackOutcome.BLOCKED)])[0]
    assert row["outcome"] == "blocked"


def test_format_outcome_table_empty_input_returns_empty_list():
    # TC-015-08
    assert format_outcome_table([]) == []


def test_format_outcome_table_armor_column_is_bool():
    # TC-015-09
    row = format_outcome_table([make_run_result(armor_active=True)])[0]
    assert row["armor"] is True


# --- compute_side_by_side ---


def test_compute_side_by_side_returns_dict():
    # TC-015-10
    assert isinstance(compute_side_by_side({"with_armor": {}, "without_armor": {}}), dict)


def test_compute_side_by_side_has_both_keys():
    # TC-015-11
    result = compute_side_by_side({"with_armor": {}, "without_armor": {}})
    assert "with_armor" in result and "without_armor" in result


def test_compute_side_by_side_passes_through_with_armor():
    # TC-015-12
    result = compute_side_by_side({"with_armor": {"detection_rate": 0.5}, "without_armor": {}})
    assert result["with_armor"]["detection_rate"] == 0.5
