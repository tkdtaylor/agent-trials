import os
from unittest.mock import MagicMock, patch

import pytest

from src.backends.llamacpp import LlamaCppBackend
from src.backends.protocol import BackendProtocol


@pytest.fixture
def mock_llama():
    with patch("src.backends.llamacpp.Llama") as mock_cls:
        instance = MagicMock()
        instance.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "hello from llama"}}]
        }
        mock_cls.return_value = instance
        yield instance, mock_cls


# --- Protocol compliance ---


def test_llamacpp_backend_satisfies_protocol(mock_llama):
    # TC-021-01
    assert isinstance(LlamaCppBackend("/fake/model.gguf"), BackendProtocol)


# --- Constructor ---


def test_model_path_stored(mock_llama):
    # TC-021-02
    backend = LlamaCppBackend("/path/model.gguf")
    assert backend.model_path == "/path/model.gguf"


def test_default_n_ctx(mock_llama):
    # TC-021-03
    backend = LlamaCppBackend("/path/model.gguf")
    assert backend.n_ctx == 4096


def test_default_n_gpu_layers(mock_llama):
    # TC-021-04
    backend = LlamaCppBackend("/path/model.gguf")
    assert backend.n_gpu_layers == 0


def test_n_ctx_and_n_gpu_layers_configurable(mock_llama):
    # TC-021-05
    backend = LlamaCppBackend("/path/model.gguf", n_ctx=2048, n_gpu_layers=32)
    assert backend.n_ctx == 2048
    assert backend.n_gpu_layers == 32


# --- chat() ---


def test_chat_returns_string(mock_llama):
    # TC-021-06
    backend = LlamaCppBackend("/path/model.gguf")
    result = backend.chat([{"role": "user", "content": "hi"}])
    assert isinstance(result, str)


def test_chat_returns_content_from_response(mock_llama):
    # TC-021-07
    backend = LlamaCppBackend("/path/model.gguf")
    result = backend.chat([{"role": "user", "content": "hi"}])
    assert result == "hello from llama"


def test_chat_passes_messages_to_create_chat_completion(mock_llama):
    # TC-021-08
    instance, _ = mock_llama
    backend = LlamaCppBackend("/path/model.gguf")
    messages = [{"role": "user", "content": "hi"}]
    backend.chat(messages)
    call_kwargs = instance.create_chat_completion.call_args
    assert call_kwargs.kwargs.get("messages") == messages or (call_kwargs.args and call_kwargs.args[0] == messages)


def test_llama_instantiated_with_correct_kwargs(mock_llama):
    # TC-021-09
    _, mock_cls = mock_llama
    LlamaCppBackend("/path/model.gguf", n_ctx=2048, n_gpu_layers=4)
    call_kwargs = mock_cls.call_args
    assert call_kwargs.kwargs["model_path"] == "/path/model.gguf"
    assert call_kwargs.kwargs["n_ctx"] == 2048
    assert call_kwargs.kwargs["n_gpu_layers"] == 4


# --- Integration ---


@pytest.mark.integration
def test_real_llamacpp_round_trip():
    # TC-021-10
    model_path = os.environ.get("LLAMACPP_MODEL_PATH")
    if not model_path:
        pytest.skip("LLAMACPP_MODEL_PATH not set")
    backend = LlamaCppBackend(model_path)
    result = backend.chat([{"role": "user", "content": "Reply with the single word: hello"}])
    assert isinstance(result, str) and len(result) > 0
