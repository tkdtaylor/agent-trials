import dataclasses

import pytest

from src.types import AgentTrace, AttackOutcome, AttackVector, RunResult


def make_trace(**kwargs) -> AgentTrace:
    defaults = dict(
        input_received="payload", final_output="response", latency_ms=10.0, timestamp="2026-05-16T00:00:00Z"
    )
    return AgentTrace(**{**defaults, **kwargs})


# --- AttackVector ---


def test_attack_vector_fields():
    # TC-001-01: instantiates with all required fields
    av = AttackVector(
        id="inj-001",
        name="Direct injection",
        payload="Ignore previous instructions",
        expected_behavior="ignore",
        category="input_injection",
    )
    assert av.id == "inj-001"
    assert av.name == "Direct injection"
    assert av.payload == "Ignore previous instructions"
    assert av.expected_behavior == "ignore"
    assert av.category == "input_injection"


def test_attack_vector_is_frozen():
    # TC-001-02: frozen dataclass — mutation raises FrozenInstanceError
    av = AttackVector(
        id="inj-001",
        name="Direct injection",
        payload="Ignore previous instructions",
        expected_behavior="ignore",
        category="input_injection",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        av.id = "new-id"  # type: ignore[misc]


# --- AgentTrace ---


def test_agent_trace_defaults():
    # TC-002-01: required fields accepted; list fields default to empty
    trace = make_trace()
    assert trace.context_retrieved == []
    assert trace.tool_calls_attempted == []
    assert trace.armor_blocks == []


def test_agent_trace_populated_lists():
    # TC-002-02: accepts non-empty context, tool calls, and armor blocks
    trace = make_trace(
        context_retrieved=["chunk1"],
        tool_calls_attempted=[{"fn": "search"}],
        armor_blocks=[{"reason": "injection"}],
    )
    assert trace.context_retrieved == ["chunk1"]
    assert trace.tool_calls_attempted == [{"fn": "search"}]
    assert trace.armor_blocks == [{"reason": "injection"}]


def test_agent_trace_no_shared_mutable_defaults():
    # TC-002-03: two instances do not share list state
    t1 = make_trace()
    t2 = make_trace()
    t1.context_retrieved.append("x")
    assert t2.context_retrieved == []


# --- RunResult ---


def test_run_result_fields():
    # TC-003-01: instantiates and carries all fields
    trace = make_trace()
    result = RunResult(
        attack_id="inj-001",
        attack_name="Direct injection",
        outcome=AttackOutcome.BLOCKED,
        trace=trace,
        armor_active=True,
        verdict_reasoning="Armor blocked input",
    )
    assert result.attack_id == "inj-001"
    assert result.outcome is AttackOutcome.BLOCKED
    assert result.armor_active is True
    assert result.trace is trace


def test_run_result_trace_required():
    # TC-003-02: trace is required — TypeError when omitted or None passed
    with pytest.raises(TypeError):
        RunResult(  # type: ignore[call-arg]
            attack_id="inj-001",
            attack_name="Direct injection",
            outcome=AttackOutcome.ERROR,
            armor_active=False,
            verdict_reasoning="crashed",
        )


# --- AttackOutcome ---


def test_attack_outcome_values():
    # TC-004-01: all four members with correct string values
    assert AttackOutcome.SUCCESS.value == "success"
    assert AttackOutcome.BLOCKED.value == "blocked"
    assert AttackOutcome.FALSE_POSITIVE.value == "false_positive"
    assert AttackOutcome.ERROR.value == "error"


def test_attack_outcome_identity_comparison():
    # TC-004-02: members compare by identity
    assert AttackOutcome.SUCCESS == AttackOutcome.SUCCESS
    assert AttackOutcome.SUCCESS != AttackOutcome.BLOCKED
