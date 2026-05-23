import json
import os
import subprocess
import sys
import tempfile

import pytest

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CORPUS = os.path.join(_PROJECT_ROOT, "attacks", "corpus.yaml")


def run_cli(*args, cwd=None, output=None):
    """Run the CLI. Writes results to a temp file by default to avoid clobbering results.json."""
    env = os.environ.copy()
    env["PYTHONPATH"] = _PROJECT_ROOT
    cmd = [sys.executable, "-m", "src", *args]
    if "--output" not in args and output is not None:
        cmd += ["--output", output]
    elif "--output" not in args:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            _tmp = f.name
        cmd += ["--output", _tmp]
    return subprocess.run(
        cmd,
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
    assert "requires a live LLM backend" in result.stderr


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
    out = str(tmp_path / "results.json")
    run_cli("--agent", "echo", "--corpus", _CORPUS, output=out)
    assert (tmp_path / "results.json").exists()
    data = json.loads((tmp_path / "results.json").read_text())
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


# --- --backend flag validation (TC-022) ---


def test_backend_ollama_accepted_with_echo():
    # TC-022-01
    result = run_cli("--backend", "ollama", "--agent", "echo")
    assert result.returncode == 0


def test_backend_llamacpp_without_model_path_exits_one():
    # TC-022-02
    result = run_cli("--backend", "llamacpp", "--agent", "echo")
    assert result.returncode == 1
    assert "--model-path" in result.stderr


def test_unknown_backend_rejected():
    # TC-022-03
    result = run_cli("--backend", "fakellm")
    assert result.returncode != 0


def test_model_flag_accepted_with_ollama():
    # TC-022-04
    result = run_cli("--backend", "ollama", "--model", "llama3", "--agent", "echo")
    assert result.returncode == 0


def test_default_model_is_qwen(tmp_path):
    # TC-022-05
    from unittest.mock import patch

    captured_model = []

    class FakeOllamaBackend:
        def __init__(self, model, think=False):
            captured_model.append(model)

        def chat(self, messages):
            return ""

    out = str(tmp_path / "out.json")
    with patch("src.backends.ollama.OllamaBackend", FakeOllamaBackend):
        from src.__main__ import main

        rc = main(["--backend", "ollama", "--agent", "echo", "--no-armor", "--output", out])

    assert rc == 0
    assert captured_model == ["qwen2.5:14b"]


def test_model_path_accepted_with_llamacpp(tmp_path):
    # TC-022-06
    from unittest.mock import patch

    class FakeLlamaCppBackend:
        def __init__(self, model_path):
            pass

        def chat(self, messages):
            return ""

    out = str(tmp_path / "out.json")
    with patch("src.backends.llamacpp.LlamaCppBackend", FakeLlamaCppBackend):
        from src.__main__ import main

        rc = main(["--backend", "llamacpp", "--model-path", "/fake/model.gguf", "--agent", "echo", "--no-armor", "--output", out])

    assert rc == 0


def test_rag_without_backend_still_exits_one():
    # TC-022-07
    result = run_cli("--agent", "rag")
    assert result.returncode == 1
    assert "requires a live LLM backend" in result.stderr


def test_echo_agent_unaffected_without_backend():
    # TC-022-09
    result = run_cli("--agent", "echo")
    assert result.returncode == 0


@pytest.mark.integration
def test_rag_with_ollama_backend_runs():
    # TC-022-08
    result = run_cli("--agent", "rag", "--backend", "ollama")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "total_attacks" in data
