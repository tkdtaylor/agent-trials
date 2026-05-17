from dataclasses import dataclass, field
from enum import Enum


class AttackOutcome(Enum):
    SUCCESS = "success"
    BLOCKED = "blocked"
    FALSE_POSITIVE = "false_positive"
    ERROR = "error"


@dataclass(frozen=True)
class AttackVector:
    id: str
    name: str
    payload: str
    expected_behavior: str
    category: str


@dataclass
class AgentTrace:
    input_received: str
    final_output: str
    latency_ms: float
    timestamp: str
    context_retrieved: list[str] = field(default_factory=list)
    tool_calls_attempted: list[dict] = field(default_factory=list)
    armor_blocks: list[dict] = field(default_factory=list)
    armor_advisories: list[dict] = field(default_factory=list)


@dataclass
class RunResult:
    attack_id: str
    attack_name: str
    outcome: AttackOutcome
    trace: AgentTrace
    armor_active: bool
    verdict_reasoning: str
    agent_type: str = "unknown"
