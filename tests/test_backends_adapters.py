from src.backends.adapters import (
    multi_turn_generate,
    rag_generate,
    rag_retrieve,
    simulated_execute_tool,
    tool_use_decide,
    tool_use_generate,
)
from src.backends.protocol import BackendProtocol


class MockBackend:
    def __init__(self, response: str = "mock response"):
        self.response = response
        self.calls: list[list[dict]] = []

    def chat(self, messages: list[dict]) -> str:
        self.calls.append(messages)
        return self.response


# --- BackendProtocol ---


def test_mock_backend_satisfies_protocol():
    # TC-019-01
    assert isinstance(MockBackend(), BackendProtocol)


def test_plain_object_does_not_satisfy_protocol():
    # TC-019-02
    assert not isinstance(object(), BackendProtocol)


# --- rag_retrieve ---


def test_rag_retrieve_returns_callable():
    # TC-019-03
    assert callable(rag_retrieve(["doc a", "doc b"]))


def test_rag_retrieve_callable_returns_list():
    # TC-019-04
    retrieve = rag_retrieve(["doc a"])
    assert isinstance(retrieve("doc"), list)


def test_rag_retrieve_filters_by_keyword():
    # TC-019-05
    retrieve = rag_retrieve(["foo bar", "baz qux"])
    assert retrieve("foo") == ["foo bar"]


def test_rag_retrieve_case_insensitive():
    # TC-019-06
    retrieve = rag_retrieve(["foo bar"])
    assert retrieve("FOO") == ["foo bar"]


def test_rag_retrieve_returns_empty_when_no_match():
    # TC-019-07
    retrieve = rag_retrieve(["foo bar", "baz qux"])
    assert retrieve("zzz") == []


# --- rag_generate ---


def test_rag_generate_returns_callable():
    # TC-019-08
    assert callable(rag_generate(MockBackend()))


def test_rag_generate_callable_returns_string():
    # TC-019-09
    backend = MockBackend("answer")
    generate = rag_generate(backend)
    assert isinstance(generate("q", ["ctx"]), str)


def test_rag_generate_calls_backend_once():
    # TC-019-10
    backend = MockBackend()
    generate = rag_generate(backend)
    generate("prompt", ["doc"])
    assert len(backend.calls) == 1


def test_rag_generate_includes_context_in_messages():
    # TC-019-11
    backend = MockBackend()
    generate = rag_generate(backend)
    generate("prompt", ["relevant doc"])
    assert "relevant doc" in str(backend.calls[0])


# --- multi_turn_generate ---


def test_multi_turn_generate_returns_callable():
    # TC-019-12
    assert callable(multi_turn_generate(MockBackend()))


def test_multi_turn_generate_callable_returns_string():
    # TC-019-13
    backend = MockBackend("reply")
    generate = multi_turn_generate(backend)
    assert isinstance(generate("hi", [{"role": "user", "content": "hi"}]), str)


def test_multi_turn_generate_passes_history_to_backend():
    # TC-019-14
    backend = MockBackend()
    generate = multi_turn_generate(backend)
    history = [{"role": "user", "content": "hi"}]
    generate("hi", history)
    assert {"role": "user", "content": "hi"} in backend.calls[0]


def test_multi_turn_generate_calls_backend_once():
    # TC-019-15
    backend = MockBackend()
    generate = multi_turn_generate(backend)
    generate("hi", [{"role": "user", "content": "hi"}])
    assert len(backend.calls) == 1


# --- tool_use_decide ---


def test_tool_use_decide_returns_callable():
    # TC-019-16
    assert callable(tool_use_decide(MockBackend(), []))


def test_tool_use_decide_callable_returns_list():
    # TC-019-17
    backend = MockBackend("[]")
    decide = tool_use_decide(backend, [])
    assert isinstance(decide("do something"), list)


def test_tool_use_decide_parses_json_response():
    # TC-019-18
    backend = MockBackend('[{"tool": "search", "args": {"q": "x"}}]')
    decide = tool_use_decide(backend, [])
    result = decide("find x")
    assert result[0]["tool"] == "search"


def test_tool_use_decide_falls_back_on_non_json():
    # TC-019-19
    backend = MockBackend("I cannot decide")
    decide = tool_use_decide(backend, [])
    assert decide("do something") == []


def test_tool_use_decide_includes_tools_in_prompt():
    # TC-019-20
    backend = MockBackend("[]")
    decide = tool_use_decide(backend, [{"name": "search"}])
    decide("query")
    assert "search" in str(backend.calls[0])


# --- simulated_execute_tool ---


def test_simulated_execute_tool_returns_callable():
    # TC-019-21
    assert callable(simulated_execute_tool())


def test_simulated_execute_tool_returns_mapped_string():
    # TC-019-22
    execute = simulated_execute_tool({"search": "result A"})
    assert execute("search", {}) == "result A"


def test_simulated_execute_tool_returns_stub_for_unknown():
    # TC-019-23
    execute = simulated_execute_tool({"search": "result A"})
    result = execute("unknown_tool", {})
    assert isinstance(result, str) and len(result) > 0


def test_simulated_execute_tool_works_with_none():
    # TC-019-24
    execute = simulated_execute_tool(None)
    result = execute("any_tool", {})
    assert isinstance(result, str) and len(result) > 0


# --- tool_use_generate ---


def test_tool_use_generate_returns_callable():
    # TC-019-25
    assert callable(tool_use_generate(MockBackend()))


def test_tool_use_generate_callable_returns_string():
    # TC-019-26
    backend = MockBackend("final answer")
    generate = tool_use_generate(backend)
    assert isinstance(generate("prompt", [{"tool": "x", "result": "y"}]), str)


def test_tool_use_generate_calls_backend_once():
    # TC-019-27
    backend = MockBackend()
    generate = tool_use_generate(backend)
    generate("prompt", [])
    assert len(backend.calls) == 1


def test_tool_use_generate_includes_tool_results_in_messages():
    # TC-019-28
    backend = MockBackend()
    generate = tool_use_generate(backend)
    generate("prompt", [{"tool": "x", "args": {}, "result": "y"}])
    assert "y" in str(backend.calls[0])
