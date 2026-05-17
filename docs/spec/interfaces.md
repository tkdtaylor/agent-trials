# Interfaces

**Project:** Agent Trials
**Last updated:** 2026-05-16

The system's contact surface — everything that calls into the system, everything the system calls out to, and the public boundaries within the system.

---

## Inbound interfaces

### Python API

The primary entry point is the `ArmorEvalRunner` class:

```python
class ArmorEvalRunner:
    def __init__(
        self,
        agent_factories: dict[str, Callable[[], AgentProtocol]] | Callable[[], AgentProtocol],
        armor_client=None,
    ): ...
    def run_single_attack(self, attack: AttackVector, enable_armor: bool = True) -> RunResult: ...
    def run_benchmark(self, attacks: list[AttackVector], iterations: int = 1) -> dict: ...
```

### CLI

```
python -m src [--corpus PATH] [--agent ARCHETYPE] [--backend BACKEND] [--model MODEL]
              [--model-path PATH] [--iterations N] [--no-armor]
              [--armor-socket PATH] [--think] [--sandbox]
              [--canary-inject PATH] [--output PATH]
```

| Flag | Type | Default | Effect |
|------|------|---------|--------|
| `--corpus` | path | `attacks/corpus.yaml` | Attack corpus file |
| `--agent` | str | `echo` | Agent archetype: `echo`, `rag`, `tool-use`, `multi-turn`, `all` |
| `--backend` | str | None | LLM backend: `ollama` or `llamacpp`. Required for `rag`, `tool-use`, `multi-turn`. |
| `--model` | str | `qwen2.5:14b` | Model name (Ollama backend) |
| `--model-path` | path | None | Path to GGUF model file (llamacpp backend, required when `--backend llamacpp`) |
| `--iterations` | int | 1 | Number of benchmark repetitions |
| `--no-armor` | flag | off | Disable Armor for this run |
| `--armor-socket` | path | `$ARMOR_SOCKET` or `/var/run/armor.sock` | Unix socket path for the Armor daemon |
| `--think` | flag | off | Enable extended thinking for Ollama models that support it (e.g. qwen3.x) |
| `--sandbox` | flag | off | Use Docker-sandboxed tool execution for tool-use agent (requires Docker) |
| `--canary-inject` | path | None | Path to `pii-context.txt` (from `armor canary seed`) — injects fake PII and credentials into the agent system prompt so exfiltration attacks have real honeypot values to steal |
| `--output` | path | `results.json` | Path to write the results JSON |

**Note on `--agent all`:** This is a *multi-agent routing mode*, not a single-archetype choice. Each attack is dispatched to its natural archetype via the runner's `_CATEGORY_TO_AGENT` map (`input_injection` and `exfiltration` → RAG; `tool_abuse` → tool-use; `multi_turn` → multi-turn).

**Constraints:** `rag`, `tool-use`, `multi-turn`, and `all` agents require `--backend`. Running them without a backend exits with code 1 and a clear error message. `--backend llamacpp` requires `--model-path`.

Dashboard is launched separately: `streamlit run dashboard/app.py`

---

## Outbound interfaces

| Dependency | What we call | Notes |
|------------|-------------|-------|
| Armor SDK | `ArmorClient.check_input(payload, session_id)` → `CheckResult` | Optional — guarded by `if armor_client` |
| Armor SDK | `ArmorClient.check_output(text, session_id)` → `CheckResult` | Optional — guarded by `if armor_client` |
| BackendProtocol | `backend.chat(messages: list[dict]) → str` | Abstraction over any local LLM backend |
| Ollama server | `ollama.Client.chat(model, messages)` → response | Used by `OllamaBackend`; requires Ollama running locally |
| llama-cpp-python | `Llama.create_chat_completion(messages)` → response | Used by `LlamaCppBackend`; requires GGUF model file |
| Docker daemon | `docker run --rm --network none --read-only <image> python3 -c <snippet>` | Used by `SandboxedToolExecutor` when `--sandbox` is active |

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

- **Implementors:** `EchoAgent`, `RAGAgent`, `ToolUseAgent`, `MultiTurnAgent` (all in `src/agents/`)
- **Consumers:** `ArmorEvalRunner`, `ArmorGuard`
- **Stability:** Breaking changes to this protocol require updating all three agent implementations
- **Required behavior:** `process_request` must be synchronous; it must populate `retrieved_context` and `tool_calls` as a side effect before returning

### Class: `ArmorGuard`

```python
class ArmorGuard:
    def __init__(self, agent: AgentProtocol, armor_client=None, session_id: str | None = None): ...
    def process(self, user_input: str) -> str: ...  # raises SecurityBlockedError on block
```

- **Consumers:** Tests, direct usage as a production guard wrapper
- **Stability:** Public interface — changes require an ADR

---

### Protocol: `BackendProtocol`

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class BackendProtocol(Protocol):
    def chat(self, messages: list[dict]) -> str: ...
```

- **Implementors:** `OllamaBackend`, `LlamaCppBackend` (in `src/backends/`)
- **Consumers:** Adapter functions in `src/backends/adapters.py`
- **Stability:** Minimal by design — one method. Adding methods is a breaking change.

### Dataclass: `AgentResponse`

```python
@dataclass
class AgentResponse:
    text: str
```

- **Producers:** All `AgentProtocol` implementors via `process_request()`
- **Consumers:** `ArmorGuard.process()`, `ArmorEvalRunner.run_single_attack()`
- **Note:** Wraps the agent's response text; `ArmorGuard` extracts `.text` before Armor output-check

---

## Extension points

New agent archetypes can be added by implementing `AgentProtocol` and registering in `_build_agent_factory()` in `src/__main__.py`. New LLM backends can be added by implementing `BackendProtocol` and wiring into `_build_backend()`. No other extension mechanism exists — extension is by source modification.
