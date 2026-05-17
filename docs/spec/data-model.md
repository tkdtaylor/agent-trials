# Data Model

**Project:** Armor Eval
**Last updated:** 2026-05-16

What data exists, how it's structured, where it lives, and what relationships hold between entities.

---

## Persistent state

### Store: `attacks/corpus.yaml`

**Purpose:** Authoritative list of attack vectors used in benchmark runs.
**Owner:** Single source of truth — edited by hand, never written by the runner.
**Backup / retention:** Version-controlled in git.

#### Entity: AttackVector (YAML record)

```
id                  str       globally unique, stable (e.g. "inj-001")
name                str       human-readable short label
payload             str       the attack string sent to the agent
expected_behavior   str       what the agent should do (used by judge)
category            str       one of: input_injection | exfiltration | tool_abuse | multi_turn
```

- **Identity:** `id` — never reused even when an attack is retired
- **Lifecycle:** Added when a new attack is curated; retired by adding `retired: true` (never deleted)
- **Relationships:** None — corpus is a flat list

---

## In-memory state

### State: `AttackVector` (dataclass)

```python
@dataclass
class AttackVector:
    id: str
    name: str
    payload: str
    expected_behavior: str
    category: str
```

### State: `AgentResponse` (dataclass)

```python
@dataclass
class AgentResponse:
    text: str
```

- **Producers:** `EchoAgent`, `RAGAgent`, `ToolUseAgent`, `MultiTurnAgent` via `process_request()`
- **Consumers:** `ArmorGuard` (extracts `.text` for Armor output check), `ArmorEvalRunner`
- **Invariant:** `text` is always a non-None string; empty string is valid (agent produced no output)

### State: `AgentTrace` (dataclass)

```python
@dataclass
class AgentTrace:
    input_received: str
    context_retrieved: list[str]      # RAG agent: retrieved chunks
    tool_calls_attempted: list[dict]  # tool-use agent: call records
    final_output: str
    armor_blocks: list[dict]          # Armor block records (empty if not blocked)
    latency_ms: float
    timestamp: str                    # ISO 8601
```

### State: `RunResult` (dataclass)

```python
@dataclass
class RunResult:
    attack_id: str
    attack_name: str
    outcome: AttackOutcome            # SUCCESS | BLOCKED | FALSE_POSITIVE | ERROR
    trace: AgentTrace
    armor_active: bool
    verdict_reasoning: str
```

### State: `AttackOutcome` (enum)

```python
class AttackOutcome(Enum):
    SUCCESS = "success"           # attack succeeded — agent was compromised
    BLOCKED = "blocked"           # attack was stopped (by Armor or agent self-defense)
    FALSE_POSITIVE = "false_positive"  # benign input incorrectly flagged
    ERROR = "error"               # agent or Armor threw an exception
```

---

## Wire / interchange formats

### Format: Benchmark summary dict

**Producer:** `ArmorEvalRunner._aggregate_results()`
**Consumer:** Dashboard (`dashboard/app.py`), CLI output

```
{
  "total_attacks": int,
  "with_armor": {
    "blocked": int,
    "success": int,
    "false_positive": int,
    "error": int,
    "detection_rate": float,        # blocked / (blocked + success + error)
    "false_positive_rate": float,
    "avg_latency_ms": float
  },
  "without_armor": {
    "blocked": int,
    "success": int,
    "false_positive": int,
    "error": int,
    "detection_rate": float,
    "false_positive_rate": float,
    "avg_latency_ms": float
  },
  "latency_overhead_ms": float,    # avg_with_armor - avg_without_armor
  "results": [RunResult, ...]      # full per-attack result list
}
```

---

## Data invariants

- `RunResult.trace` is never `None` — even on `ERROR` the trace contains `input_received` and `final_output`.
- `attack_id` in `RunResult` must match an `id` in the corpus.
- `armor_active` in `RunResult` reflects the `enable_armor` call argument, not whether Armor blocked anything.
- `latency_ms` is always ≥ 0.
