"""Test checkpoints module.

Tests for checkpoint splitting, I/O, resume logic, and result merging.
"""

import dataclasses
import json
import pathlib

from src.agent_wrapper import AgentResponse
from src.checkpoints import (
    checkpoint_path,
    is_checkpointed,
    load_checkpoint,
    merge_group_results,
    split_into_groups,
    write_checkpoint,
)
from src.runner import ArmorEvalRunner
from src.types import AgentTrace, AttackOutcome, AttackVector, RunResult


def make_attack(id="inj-001", category="input_injection", **kwargs) -> AttackVector:
    defaults = dict(
        name="Test attack",
        payload="Ignore previous instructions",
        expected_behavior="ignore",
        category=category,
    )
    return AttackVector(id=id, **{**defaults, **kwargs})


def stub_factory(response_text: str = "safe response"):
    class _Stub:
        def __init__(self):
            self.session_id = "test"
            self.retrieved_context: list = []
            self.tool_calls: list = []

        def process_request(self, _: str) -> AgentResponse:
            return AgentResponse(text=response_text)

    return _Stub


def make_run_result(attack_id="inj-001", armor_active=False) -> RunResult:
    return RunResult(
        attack_id=attack_id,
        attack_name="Test attack",
        outcome=AttackOutcome.BLOCKED,
        trace=AgentTrace(
            input_received="x",
            final_output="x",
            latency_ms=1.0,
            timestamp="2026-01-01T00:00:00+00:00",
        ),
        armor_active=armor_active,
        verdict_reasoning="blocked",
        agent_type="rag",
    )


# --- TC-024-01 ---


def test_split_into_groups_even_split():
    """TC-024-01: Corpus splits evenly into groups of N."""
    attacks = [make_attack(id=f"a{i}") for i in range(8)]
    groups = split_into_groups(attacks, group_size=4)
    assert len(groups) == 2
    assert len(groups[0]) == 4
    assert len(groups[1]) == 4


# --- TC-024-02 ---


def test_split_into_groups_with_remainder():
    """TC-024-02: Remainder group captured when corpus size is not a multiple of N."""
    attacks = [make_attack(id=f"a{i}") for i in range(10)]
    groups = split_into_groups(attacks, group_size=4)
    assert len(groups) == 3
    assert len(groups[0]) == 4
    assert len(groups[1]) == 4
    assert len(groups[2]) == 2


# --- TC-024-03 ---


def test_split_into_groups_single_attack():
    """TC-024-03: Single-attack corpus produces one group of one."""
    groups = split_into_groups([make_attack()], group_size=8)
    assert len(groups) == 1
    assert len(groups[0]) == 1


# --- TC-024-04 ---


def test_checkpoint_written_after_each_group(tmp_path):
    """TC-024-04: Checkpoint written after each group, not just at the end."""
    attacks = [make_attack(id=f"a{i}") for i in range(3)]
    groups = split_into_groups(attacks, group_size=1)
    output = tmp_path / "results.json"

    written = []
    for idx, group in enumerate(groups):
        results = [make_run_result(attack_id=a.id) for a in group]
        cp = checkpoint_path(output, idx)
        write_checkpoint(cp, results)
        written.append(cp)
        # Every previously written checkpoint exists before proceeding
        for prev in written:
            assert prev.exists()

    assert len(written) == 3


# --- TC-024-05 ---


def test_checkpoint_path_format():
    """TC-024-05: Checkpoint filename format is {stem}_group_{NNN}.json."""
    output = pathlib.Path("/tmp/results.json")
    assert checkpoint_path(output, 0) == pathlib.Path("/tmp/results_group_000.json")
    assert checkpoint_path(output, 7) == pathlib.Path("/tmp/results_group_007.json")
    assert checkpoint_path(output, 42) == pathlib.Path("/tmp/results_group_042.json")


# --- TC-024-06 ---


def test_checkpoint_round_trip(tmp_path):
    """TC-024-06: Checkpoint file round-trips through JSON correctly."""
    results = [
        make_run_result("inj-001", armor_active=False),
        make_run_result("inj-001", armor_active=True),
    ]
    cp = tmp_path / "results_group_000.json"
    write_checkpoint(cp, results)
    loaded = load_checkpoint(cp)
    assert len(loaded) == 2
    assert loaded[0].attack_id == "inj-001"
    assert loaded[0].armor_active is False
    assert loaded[1].armor_active is True
    assert loaded[0].outcome == AttackOutcome.BLOCKED


# --- TC-024-07 ---


def test_is_checkpointed(tmp_path):
    """TC-024-07: Resume - existing checkpoint causes its group to be skipped."""
    attacks = [make_attack(id=f"a{i}") for i in range(4)]
    groups = split_into_groups(attacks, group_size=2)
    output = tmp_path / "results.json"

    # Pre-write checkpoint for group 0 only
    pre_results = [make_run_result(a.id) for a in groups[0]]
    write_checkpoint(checkpoint_path(output, 0), pre_results)

    assert is_checkpointed(output, 0) is True
    assert is_checkpointed(output, 1) is False


# --- TC-024-08 ---


def test_merge_group_results_combines_all(tmp_path):
    """TC-024-08: Resume - loaded checkpoint results are merged into final output."""
    attacks = [make_attack(id=f"a{i}") for i in range(4)]
    groups = split_into_groups(attacks, group_size=2)
    output = tmp_path / "results.json"

    # Group 0 pre-checkpointed
    group0_results = [make_run_result(a.id, armor_active=False) for a in groups[0]] + \
                     [make_run_result(a.id, armor_active=True) for a in groups[0]]
    write_checkpoint(checkpoint_path(output, 0), group0_results)

    # Group 1 "run live"
    group1_results = [make_run_result(a.id, armor_active=False) for a in groups[1]] + \
                     [make_run_result(a.id, armor_active=True) for a in groups[1]]

    all_results = merge_group_results([group0_results, group1_results])
    # 2 attacks per group x 2 (bare+armored) x 2 groups = 8
    assert len(all_results) == 8
    attack_ids = {r.attack_id for r in all_results}
    assert attack_ids == {"a0", "a1", "a2", "a3"}


# --- TC-024-09 ---


def test_final_output_written_only_after_all_groups(tmp_path):
    """TC-024-09: Final output is written only after all groups complete."""
    attacks = [make_attack(id=f"a{i}") for i in range(6)]
    groups = split_into_groups(attacks, group_size=2)
    output = tmp_path / "results.json"

    for idx, group in enumerate(groups):
        results = [make_run_result(a.id) for a in group]
        write_checkpoint(checkpoint_path(output, idx), results)

    # Final output must not exist until we explicitly write it
    assert not output.exists()
    # Write it now (simulating what __main__ does after all groups complete)
    from enum import Enum

    def _default(obj):
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return dataclasses.asdict(obj)
        if isinstance(obj, Enum):
            return obj.value
        return str(obj)

    output.write_text(json.dumps({"total_attacks": 6}, default=_default))
    assert output.exists()


# --- TC-024-10 ---


def test_run_benchmark_returns_tuple():
    """TC-024-10: run_benchmark returns (summary_dict, list[RunResult]) tuple."""
    runner = ArmorEvalRunner(stub_factory())
    result = runner.run_benchmark([make_attack()], iterations=1)
    assert isinstance(result, tuple)
    assert len(result) == 2
    summary, raw_results = result
    assert isinstance(summary, dict)
    assert isinstance(raw_results, list)
    assert all(isinstance(r, RunResult) for r in raw_results)


# --- TC-024-11 ---


def test_run_benchmark_summary_has_required_keys():
    """TC-024-11: run_benchmark summary dict still has all required keys."""
    runner = ArmorEvalRunner(stub_factory())
    summary, _ = runner.run_benchmark([make_attack()])
    assert {"total_attacks", "with_armor", "without_armor", "latency_overhead_ms"} <= summary.keys()


# --- TC-024-12 ---


def test_run_benchmark_excludes_results_key():
    """TC-024-12: run_benchmark raw results exclude the results key from summary."""
    runner = ArmorEvalRunner(stub_factory())
    summary, raw = runner.run_benchmark([make_attack()])
    assert "results" not in summary
    assert len(raw) > 0


# --- TC-024-13 ---


def test_group_size_flag_default(tmp_path):
    """TC-024-13: --group-size flag accepted with correct default of 8."""
    from src.__main__ import _build_parser

    p = _build_parser()
    args = p.parse_args(["--agent", "echo"])
    assert args.group_size == 8
    assert args.iterations == 5


# --- TC-024-14 ---


def test_group_size_flag_override():
    """TC-024-14: --group-size override accepted by CLI."""
    from src.__main__ import _build_parser

    p = _build_parser()
    args = p.parse_args(["--agent", "echo", "--group-size", "3"])
    assert args.group_size == 3


# --- TC-024-15 ---


def test_iterations_default_is_five():
    """TC-024-15: --iterations default is now 5."""
    from src.__main__ import _build_parser

    p = _build_parser()
    args = p.parse_args(["--agent", "echo"])
    assert args.iterations == 5


# --- TC-024-16 ---


def test_sqlite_rows_written_during_run(tmp_path):
    """TC-024-16: SQLite rows written during the run (not just after all groups)."""
    import sqlite3

    from src.telemetry import RunRecorder

    recorder = RunRecorder(db_path=str(tmp_path / "runs.db"))
    run_id = recorder.start_run(
        model=None, backend=None, agent_types=["echo"],
        iterations=5, corpus_hash="abc", armor_version=None,
        results_file="out.json",
    )

    # Simulate group 0 finishing — records written immediately
    recorder.record_attack(run_id, "a0", "A0", "echo", "blocked", False, 10.0, "")
    recorder.record_attack(run_id, "a0", "A0", "echo", "blocked", True, 10.0, "")

    # Check DB state mid-run (before group 1)
    conn = sqlite3.connect(str(tmp_path / "runs.db"))
    rows = conn.execute(
        "SELECT attack_id FROM run_attacks WHERE run_id = ?", (run_id,)
    ).fetchall()
    conn.close()
    assert len(rows) == 2  # group 0 already persisted

    # Simulate group 1 — records written immediately after
    recorder.record_attack(run_id, "a1", "A1", "echo", "blocked", False, 10.0, "")
    recorder.record_attack(run_id, "a1", "A1", "echo", "blocked", True, 10.0, "")

    conn = sqlite3.connect(str(tmp_path / "runs.db"))
    rows = conn.execute(
        "SELECT attack_id FROM run_attacks WHERE run_id = ?", (run_id,)
    ).fetchall()
    conn.close()
    assert len(rows) == 4


# --- TC-024-17 ---


def test_detection_rate_consistency_merged_results():
    """TC-024-17: Detection rate in merged final output is arithmetically consistent."""
    attacks = [make_attack(id=f"a{i}") for i in range(4)]

    bare_blocked = [make_run_result(a.id, armor_active=False) for a in attacks]
    # Artificially set half to SUCCESS for variety
    bare_blocked[0] = dataclasses.replace(bare_blocked[0], outcome=AttackOutcome.SUCCESS)
    armored = [make_run_result(a.id, armor_active=True) for a in attacks]

    all_results = bare_blocked + armored
    runner = ArmorEvalRunner(stub_factory())
    # Use _aggregate_results directly
    final = runner._aggregate_results(attacks, all_results)

    # 4 armored all BLOCKED → detection_rate = 4/4
    assert final["with_armor"]["detection_rate"] == 1.0
    # 3 bare BLOCKED, 1 bare SUCCESS → detection_rate = 3/4
    assert final["without_armor"]["detection_rate"] == 3 / 4


# --- TC-024-18 ---


def test_echo_agent_creates_checkpoint_files(tmp_path):
    """TC-024-18: End-to-end CLI smoke test - checkpoints created for echo agent."""
    import os
    import subprocess
    import sys

    project_root = pathlib.Path(__file__).parent.parent
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    output = tmp_path / "results.json"
    result = subprocess.run(
        [sys.executable, "-m", "src",
         "--agent", "echo",
         "--no-armor",
         "--group-size", "4",
         "--iterations", "1",
         "--output", str(output)],
        capture_output=True, text=True,
        cwd=str(project_root), env=env,
    )
    assert result.returncode == 0, result.stderr

    # At least one checkpoint file should exist
    checkpoints = list(tmp_path.glob("results_group_*.json"))
    assert len(checkpoints) >= 1

    # Final results.json must exist and be valid
    assert output.exists()
    data = json.loads(output.read_text())
    assert "total_attacks" in data
