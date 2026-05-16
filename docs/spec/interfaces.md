# Interfaces

**Project:** Armor Eval
**Last updated:** 2026-05-16

The system's contact surface — everything that calls into the system, everything the system calls out to, and the public boundaries within the system.

---

## Inbound interfaces

### Python API

The primary entry point is the `ArmorEvalRunner` class:

```python
class ArmorEvalRunner:
    def __init__(self, agent_factory: Callable[[], AgentProtocol], armor_client=None): ...
    def run_single_attack(self, attack: AttackVector, enable_armor: bool = True) -> RunResult: ...
    def run_benchmark(self, attacks: list[AttackVector], iterations: int = 1) -> dict: ...
```

### CLI (planned)

```
armor-eval run --corpus attacks/corpus.yaml [--no-armor] [--agent rag|tool-use|multi-turn]
armor-eval dashboard                        # launch Streamlit UI
```

| Flag | Type | Default | Effect |
|------|------|---------|--------|
| `--corpus` | path | `attacks/corpus.yaml` | Attack corpus file |
| `--no-armor` | flag | off | Disable Armor for this run |
| `--agent` | str | `rag` | Agent archetype to use |
| `--iterations` | int | 1 | Number of benchmark repetitions |

---

## Outbound interfaces

| Dependency | What we call | Notes |
|------------|-------------|-------|
| Armor SDK | `ArmorClient.check_input(payload, session_id)` → `CheckResult` | Optional — guarded by `if armor_client` |
| Armor SDK | `ArmorClient.check_output(text, session_id)` → `CheckResult` | Optional — guarded by `if armor_client` |
| Anthropic API | `anthropic.Anthropic().messages.create(...)` | Used by RAG and multi-turn agents |
| External tools/APIs | Varies per `ToolUseAgent` implementation | Called during tool-use agent runs |

---

## Internal public surface

### Protocol: `AgentProtocol`

```python
from typing import Protocol

class AgentProtocol(Protocol):
    session_id: str
    retrieved_context: list[str]    # populated by RAG agent after each call
    tool_calls: list[dict]          # populated by tool-use agent after each call

    def process_request(self, user_input: str) -> AgentResponse: ...
```

- **Implementors:** `RAGAgent`, `ToolUseAgent`, `MultiTurnAgent` (all in `src/agents/`)
- **Consumers:** `ArmorEvalRunner`, `ArmorGuard`
- **Stability:** Breaking changes to this protocol require updating all three agent implementations
- **Required behavior:** `process_request` must be synchronous; it must populate `retrieved_context` and `tool_calls` as a side effect before returning

### Class: `ArmorGuard`

```python
class ArmorGuard:
    def __init__(self, agent: AgentProtocol, armor_client=None, session_id: str = None): ...
    def process(self, user_input: str) -> str: ...  # raises SecurityBlockedError on block
```

- **Consumers:** Tests, direct usage as a production guard wrapper
- **Stability:** Public interface — changes require an ADR

---

## Extension points

New agent archetypes can be added by implementing `AgentProtocol` and registering in the agent factory. No other extension mechanism exists — extension is by source modification.
