import subprocess
from unittest.mock import MagicMock, patch

import pytest

from src.backends.sandbox import SandboxedToolExecutor


@pytest.fixture
def mock_subprocess():
    with patch("src.backends.sandbox.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="tool output", stderr="")
        yield mock_run


def _docker_available() -> bool:
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# --- Callable interface ---


def test_executor_is_callable():
    # TC-023-01
    executor = SandboxedToolExecutor({})
    assert callable(executor)


def test_call_returns_string(mock_subprocess):
    # TC-023-02
    executor = SandboxedToolExecutor({"greet": 'print("hi")'})
    result = executor("greet", {})
    assert isinstance(result, str)


def test_call_returns_stdout(mock_subprocess):
    # TC-023-03
    executor = SandboxedToolExecutor({"greet": 'print("hi")'})
    result = executor("greet", {})
    assert result == "tool output"


# --- Docker invocation ---


def test_docker_run_called(mock_subprocess):
    # TC-023-04
    executor = SandboxedToolExecutor({"greet": 'print("hi")'})
    executor("greet", {})
    assert mock_subprocess.called


def test_network_none_flag_present(mock_subprocess):
    # TC-023-05
    executor = SandboxedToolExecutor({"greet": 'print("hi")'})
    executor("greet", {})
    cmd = mock_subprocess.call_args.args[0]
    idx = cmd.index("--network")
    assert cmd[idx + 1] == "none"


def test_read_only_flag_present(mock_subprocess):
    # TC-023-06
    executor = SandboxedToolExecutor({"greet": 'print("hi")'})
    executor("greet", {})
    cmd = mock_subprocess.call_args.args[0]
    assert "--read-only" in cmd


def test_rm_flag_present(mock_subprocess):
    # TC-023-07
    executor = SandboxedToolExecutor({"greet": 'print("hi")'})
    executor("greet", {})
    cmd = mock_subprocess.call_args.args[0]
    assert "--rm" in cmd


def test_non_zero_exit_raises_runtime_error(mock_subprocess):
    # TC-023-08
    mock_subprocess.return_value = MagicMock(returncode=1, stdout="", stderr="error msg")
    executor = SandboxedToolExecutor({"greet": 'print("hi")'})
    with pytest.raises(RuntimeError):
        executor("greet", {})


# --- Fallback for unknown tool ---


def test_unknown_tool_returns_stub_string():
    # TC-023-09
    executor = SandboxedToolExecutor({})
    result = executor("unknown_tool", {})
    assert isinstance(result, str) and len(result) > 0


# --- Integration ---


@pytest.mark.integration
def test_container_executes_snippet():
    # TC-023-10
    if not _docker_available():
        pytest.skip("Docker not available")
    executor = SandboxedToolExecutor({"echo": 'print("sandbox_ok")'})
    result = executor("echo", {})
    assert "sandbox_ok" in result


@pytest.mark.integration
def test_container_network_is_blocked():
    # TC-023-11
    if not _docker_available():
        pytest.skip("Docker not available")
    executor = SandboxedToolExecutor(
        {"net_test": "import urllib.request; urllib.request.urlopen('http://example.com', timeout=2)"}
    )
    with pytest.raises(RuntimeError):
        executor("net_test", {})


@pytest.mark.integration
def test_container_removed_after_execution():
    # TC-023-12
    if not _docker_available():
        pytest.skip("Docker not available")
    executor = SandboxedToolExecutor({"echo": 'print("cleanup_test")'})
    executor("echo", {})
    containers = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True, text=True,
    ).stdout
    assert "cleanup_test" not in containers
