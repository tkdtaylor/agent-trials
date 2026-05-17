from unittest.mock import MagicMock, patch

import pytest

from src.backends.ollama import OllamaBackend
from src.backends.protocol import BackendProtocol


@pytest.fixture
def mock_client():
    with patch("src.backends.ollama.ollama.Client") as mock_cls:
        instance = MagicMock()
        instance.chat.return_value = MagicMock(message=MagicMock(content="hello from ollama"))
        mock_cls.return_value = instance
        yield instance


# --- Protocol compliance ---


def test_ollama_backend_satisfies_protocol():
    # TC-020-01
    with patch("src.backends.ollama.ollama.Client"):
        assert isinstance(OllamaBackend(), BackendProtocol)


# --- Constructor ---


def test_default_model(mock_client):
    # TC-020-02
    backend = OllamaBackend()
    assert backend.model == "qwen2.5:14b"


def test_default_host(mock_client):
    # TC-020-03
    backend = OllamaBackend()
    assert backend.host == "http://localhost:11434"


def test_model_and_host_configurable(mock_client):
    # TC-020-04
    backend = OllamaBackend(model="llama3", host="http://remote:11434")
    assert backend.model == "llama3"
    assert backend.host == "http://remote:11434"


# --- chat() ---


def test_chat_returns_string(mock_client):
    # TC-020-05
    backend = OllamaBackend()
    result = backend.chat([{"role": "user", "content": "hi"}])
    assert isinstance(result, str)


def test_chat_returns_content_from_response(mock_client):
    # TC-020-06
    backend = OllamaBackend()
    result = backend.chat([{"role": "user", "content": "hi"}])
    assert result == "hello from ollama"


def test_chat_passes_messages_to_client(mock_client):
    # TC-020-07
    backend = OllamaBackend()
    messages = [{"role": "user", "content": "hi"}]
    backend.chat(messages)
    call_kwargs = mock_client.chat.call_args
    assert call_kwargs.kwargs["messages"] == messages or call_kwargs.args[1] == messages


def test_chat_passes_model_to_client(mock_client):
    # TC-020-08
    backend = OllamaBackend(model="mistral")
    backend.chat([{"role": "user", "content": "hi"}])
    call_kwargs = mock_client.chat.call_args
    assert "mistral" in str(call_kwargs)


# --- Integration ---


@pytest.mark.integration
def test_real_ollama_round_trip():
    # TC-020-09
    try:
        backend = OllamaBackend()
        result = backend.chat([{"role": "user", "content": "Reply with the single word: hello"}])
        assert isinstance(result, str) and len(result) > 0
    except Exception as e:
        pytest.skip(f"Ollama server not reachable: {e}")
