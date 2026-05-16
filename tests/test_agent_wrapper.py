from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.agent_wrapper import AgentResponse, ArmorGuard, SecurityBlockedError


class StubAgent:
    def __init__(self):
        self.session_id = "test-session"
        self.retrieved_context = []
        self.tool_calls = []

    def process_request(self, user_input: str) -> AgentResponse:
        return AgentResponse(text=f"echo: {user_input}")


class MockArmorClient:
    def __init__(self, input_blocks: bool = False, output_blocks: bool = False):
        self.input_blocks = input_blocks
        self.output_blocks = output_blocks

    def check_input(self, payload: str, session_id: str):
        return SimpleNamespace(blocked=self.input_blocks)

    def check_output(self, text: str, session_id: str):
        return SimpleNamespace(blocked=self.output_blocks)


# --- AgentResponse ---


def test_agent_response_stores_text():
    # TC-005-01
    r = AgentResponse(text="hello")
    assert r.text == "hello"


def test_agent_response_instances_are_independent():
    # TC-005-02
    r1 = AgentResponse(text="a")
    r2 = AgentResponse(text="b")
    assert r1.text != r2.text


# --- AgentProtocol ---


def test_conforming_class_process_request():
    # TC-006-01
    result = StubAgent().process_request("hi")
    assert isinstance(result, AgentResponse)
    assert result.text == "echo: hi"


def test_conforming_class_has_required_attributes():
    # TC-006-02
    agent = StubAgent()
    assert hasattr(agent, "session_id")
    assert hasattr(agent, "retrieved_context")
    assert hasattr(agent, "tool_calls")


# --- SecurityBlockedError ---


def test_security_blocked_exception_is_exception():
    # TC-008-01
    assert issubclass(SecurityBlockedError, Exception)


def test_security_blocked_exception_can_be_raised_and_caught():
    # TC-008-02
    with pytest.raises(SecurityBlockedError, match="blocked"):
        raise SecurityBlockedError("blocked")


# --- ArmorGuard ---


def test_armor_guard_passthrough_without_client():
    # TC-007-01
    guard = ArmorGuard(StubAgent(), armor_client=None)
    assert guard.process("ping") == "echo: ping"


def test_armor_guard_raises_on_input_block():
    # TC-007-02
    guard = ArmorGuard(StubAgent(), armor_client=MockArmorClient(input_blocks=True))
    with pytest.raises(SecurityBlockedError):
        guard.process("attack")


def test_armor_guard_raises_on_output_block():
    # TC-007-03
    guard = ArmorGuard(StubAgent(), armor_client=MockArmorClient(output_blocks=True))
    with pytest.raises(SecurityBlockedError):
        guard.process("attack")


def test_armor_guard_passes_through_when_both_checks_pass():
    # TC-007-04
    guard = ArmorGuard(StubAgent(), armor_client=MockArmorClient())
    assert guard.process("hello") == "echo: hello"


def test_armor_guard_does_not_call_agent_when_input_blocked():
    # TC-007-05
    agent = StubAgent()
    agent.process_request = MagicMock()
    guard = ArmorGuard(agent, armor_client=MockArmorClient(input_blocks=True))
    with pytest.raises(SecurityBlockedError):
        guard.process("attack")
    agent.process_request.assert_not_called()
