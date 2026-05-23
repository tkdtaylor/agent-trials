import json
import sqlite3

import pytest

from src.telemetry import RunRecorder


def make_recorder(tmp_path):
    db = str(tmp_path / "runs.db")
    return RunRecorder(db_path=db), db


def tables(db_path):
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    return {r[0] for r in rows}


def fetch_run(db_path, run_id):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
    return dict(row) if row else None


def fetch_attacks(db_path, run_id):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM run_attacks WHERE run_id=?", (run_id,)
        ).fetchall()
    return [dict(r) for r in rows]


# TC-022-01
def test_db_created_on_first_use(tmp_path):
    _, db = make_recorder(tmp_path)
    assert "runs" in tables(db)
    assert "run_attacks" in tables(db)


# TC-022-02
def test_start_run_returns_nonempty_string(tmp_path):
    rec, _ = make_recorder(tmp_path)
    run_id = rec.start_run(
        model="qwen2.5:14b", backend="ollama", agent_types=["rag"],
        iterations=1, corpus_hash="abc123", armor_version=None,
        results_file="results.json",
    )
    assert isinstance(run_id, str) and len(run_id) > 0


# TC-022-03
def test_start_run_inserts_row_with_started_at(tmp_path):
    rec, db = make_recorder(tmp_path)
    run_id = rec.start_run(
        model="qwen2.5:14b", backend="ollama", agent_types=["rag"],
        iterations=1, corpus_hash="abc123", armor_version=None,
        results_file="results.json",
    )
    row = fetch_run(db, run_id)
    assert row is not None
    assert row["started_at"] is not None


# TC-022-04
def test_finish_run_sets_finished_at_and_wall_clock(tmp_path):
    rec, db = make_recorder(tmp_path)
    run_id = rec.start_run(
        model=None, backend=None, agent_types=["echo"],
        iterations=1, corpus_hash=None, armor_version=None, results_file=None,
    )
    rec.finish_run(run_id, wall_clock_seconds=42.5)
    row = fetch_run(db, run_id)
    assert row["finished_at"] is not None
    assert row["wall_clock_seconds"] == pytest.approx(42.5)


# TC-022-05
def test_finish_run_sets_peak_vram_when_provided(tmp_path):
    rec, db = make_recorder(tmp_path)
    run_id = rec.start_run(
        model=None, backend=None, agent_types=["rag"],
        iterations=1, corpus_hash=None, armor_version=None, results_file=None,
    )
    rec.finish_run(run_id, wall_clock_seconds=1.0, peak_vram_bytes=8_000_000_000)
    row = fetch_run(db, run_id)
    assert row["peak_vram_bytes"] == 8_000_000_000


# TC-022-06
def test_finish_run_peak_vram_null_when_not_provided(tmp_path):
    rec, db = make_recorder(tmp_path)
    run_id = rec.start_run(
        model=None, backend=None, agent_types=["rag"],
        iterations=1, corpus_hash=None, armor_version=None, results_file=None,
    )
    rec.finish_run(run_id, wall_clock_seconds=1.0)
    row = fetch_run(db, run_id)
    assert row["peak_vram_bytes"] is None


# TC-022-07
def test_record_attack_inserts_row(tmp_path):
    rec, db = make_recorder(tmp_path)
    run_id = rec.start_run(
        model=None, backend=None, agent_types=["rag"],
        iterations=1, corpus_hash=None, armor_version=None, results_file=None,
    )
    rec.record_attack(
        run_id=run_id, attack_id="inj-001", attack_name="Direct injection",
        agent_type="rag", outcome="BLOCKED", armor_active=True,
        latency_ms=120.5, verdict_reasoning="refused",
    )
    rows = fetch_attacks(db, run_id)
    assert len(rows) == 1
    r = rows[0]
    assert r["attack_id"] == "inj-001"
    assert r["outcome"] == "BLOCKED"
    assert r["armor_active"] == 1
    assert r["latency_ms"] == pytest.approx(120.5)
    assert r["verdict_reasoning"] == "refused"


# TC-022-08
def test_record_attack_fk_links_to_run(tmp_path):
    rec, db = make_recorder(tmp_path)
    run_id = rec.start_run(
        model=None, backend=None, agent_types=["rag"],
        iterations=1, corpus_hash=None, armor_version=None, results_file=None,
    )
    rec.record_attack(
        run_id=run_id, attack_id="inj-001", attack_name="Direct injection",
        agent_type="rag", outcome="BLOCKED", armor_active=False,
        latency_ms=10.0, verdict_reasoning="",
    )
    rows = fetch_attacks(db, run_id)
    assert rows[0]["run_id"] == run_id


# TC-022-09
def test_multiple_attacks_all_recorded(tmp_path):
    rec, db = make_recorder(tmp_path)
    run_id = rec.start_run(
        model=None, backend=None, agent_types=["rag"],
        iterations=1, corpus_hash=None, armor_version=None, results_file=None,
    )
    for i in range(3):
        rec.record_attack(
            run_id=run_id, attack_id=f"inj-00{i}", attack_name=f"Attack {i}",
            agent_type="rag", outcome="BLOCKED", armor_active=True,
            latency_ms=float(i), verdict_reasoning="",
        )
    rows = fetch_attacks(db, run_id)
    assert len(rows) == 3


# TC-022-10
def test_agent_types_stored_as_json(tmp_path):
    rec, db = make_recorder(tmp_path)
    run_id = rec.start_run(
        model=None, backend=None, agent_types=["rag", "tool_use"],
        iterations=1, corpus_hash=None, armor_version=None, results_file=None,
    )
    row = fetch_run(db, run_id)
    assert json.loads(row["agent_types"]) == ["rag", "tool_use"]


# TC-022-11
def test_armor_version_null_when_not_provided(tmp_path):
    rec, db = make_recorder(tmp_path)
    run_id = rec.start_run(
        model=None, backend=None, agent_types=["rag"],
        iterations=1, corpus_hash=None, armor_version=None, results_file=None,
    )
    row = fetch_run(db, run_id)
    assert row["armor_version"] is None


# TC-022-12
def test_armor_version_stored_when_provided(tmp_path):
    rec, db = make_recorder(tmp_path)
    run_id = rec.start_run(
        model=None, backend=None, agent_types=["rag"],
        iterations=1, corpus_hash=None, armor_version="1.2.3", results_file=None,
    )
    row = fetch_run(db, run_id)
    assert row["armor_version"] == "1.2.3"


# TC-022-13
def test_get_vram_bytes_returns_none_without_ollama():
    result = RunRecorder.get_vram_bytes(model="nonexistent-model")
    assert result is None


# TC-022-14
def test_two_start_run_calls_produce_distinct_ids(tmp_path):
    rec, _ = make_recorder(tmp_path)
    id1 = rec.start_run(
        model=None, backend=None, agent_types=[],
        iterations=1, corpus_hash=None, armor_version=None, results_file=None,
    )
    id2 = rec.start_run(
        model=None, backend=None, agent_types=[],
        iterations=1, corpus_hash=None, armor_version=None, results_file=None,
    )
    assert id1 != id2


# TC-022-15
def test_recorder_works_with_string_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rec = RunRecorder(db_path="runs.db")
    run_id = rec.start_run(
        model=None, backend=None, agent_types=["echo"],
        iterations=1, corpus_hash=None, armor_version=None, results_file=None,
    )
    assert run_id
    assert "runs" in tables(str(tmp_path / "runs.db"))
