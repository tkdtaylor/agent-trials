import json
import os
import subprocess
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CORPUS = os.path.join(_PROJECT_ROOT, "attacks", "corpus.yaml")


def run_cli(*args, cwd=None):
    env = os.environ.copy()
    env["PYTHONPATH"] = _PROJECT_ROOT
    return subprocess.run(
        [sys.executable, "-m", "src", *args],
        capture_output=True,
        text=True,
        cwd=cwd or _PROJECT_ROOT,
        env=env,
    )


# --- Exit codes ---


def test_echo_agent_exits_zero():
    # TC-017-01
    result = run_cli("--agent", "echo")
    assert result.returncode == 0


def test_unknown_agent_exits_nonzero():
    # TC-017-02
    result = run_cli("--agent", "unknown")
    assert result.returncode != 0


def test_missing_corpus_exits_nonzero():
    # TC-017-03
    result = run_cli("--corpus", "/no/such/file.yaml")
    assert result.returncode != 0


def test_unimplemented_agent_exits_one_with_message():
    # TC-017-04
    result = run_cli("--agent", "rag")
    assert result.returncode == 1
    assert "not yet wired" in result.stderr


# --- Output ---


def test_stdout_contains_total_attacks():
    # TC-017-05
    result = run_cli("--agent", "echo")
    assert "total_attacks" in result.stdout


def test_stdout_contains_detection_rate():
    # TC-017-06
    result = run_cli("--agent", "echo")
    assert "detection_rate" in result.stdout


# --- Results file ---


def test_results_json_written(tmp_path):
    # TC-017-07
    run_cli("--agent", "echo", "--corpus", _CORPUS, cwd=str(tmp_path))
    results_file = tmp_path / "results.json"
    assert results_file.exists()
    data = json.loads(results_file.read_text())
    assert "total_attacks" in data


# --- Flags ---


def test_iterations_flag_accepted():
    # TC-017-08
    result = run_cli("--agent", "echo", "--iterations", "2")
    assert result.returncode == 0


def test_no_armor_flag_accepted():
    # TC-017-09
    result = run_cli("--agent", "echo", "--no-armor")
    assert result.returncode == 0
