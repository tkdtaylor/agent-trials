# Architecture — C4 Element Catalog

**Project:** Armor Eval
**Last updated:** 2026-05-16

The structured catalog of architectural elements that the diagrams in [`../architecture/diagrams.md`](../architecture/diagrams.md) render.

---

## 1. Persons (actors)

| Name | Description | Goals |
|------|-------------|-------|
| Developer / Security Engineer | Runs benchmarks against agents before deploying them | Validate agent safety, measure Armor's detection coverage, identify attack categories that slip through |

---

## 2. Systems

| Name | Type | Description | Owner |
|------|------|-------------|-------|
| Armor Eval | In-scope | Adversarial benchmarking framework for AI agents | This team |
| Armor SDK | External | Security layer that checks agent inputs/outputs for threats | Armor team |
| Ollama | External | Local LLM inference server (HTTP API) | Open-source |
| llama-cpp-python | External | Local LLM inference via GGUF model files | Open-source |
| Docker | External | Container runtime for sandboxed tool execution | Docker Inc |

---

## 3. Containers

| Name | Technology | Responsibility | Source path | Depends on |
|------|------------|----------------|-------------|------------|
| Eval Runner | Python process | Executes attack vectors against agents, coordinates Armor toggle, aggregates results | `src/runner.py` | Agent archetypes, Armor SDK, Judge |
| Agent Archetypes | Python modules | Concrete implementations of echo, RAG, tool-use, and multi-turn agents | `src/agents/` | BackendProtocol (via adapter layer) |
| Backend Layer | Python modules | BackendProtocol abstraction + Ollama/LlamaCpp adapters; converts LLM backends into per-agent callables | `src/backends/` | Ollama or llama-cpp-python (whichever backend is active) |
| Judge | Python module | Determines `AttackOutcome` from agent output and tool call trace | `src/judge.py` | — |
| ArmorGuard Wrapper | Python class | Inline Armor toggle — wraps any `AgentProtocol` implementor | `src/agent_wrapper.py` | Armor SDK |
| Attack Corpus | YAML file | Curated attack vectors across four threat classes | `attacks/corpus.yaml` | — |
| Dashboard | Streamlit app | Read-only results viewer with side-by-side bare vs. armored comparison | `dashboard/app.py` | Eval Runner output |
| Docker Sandbox | Docker container | Isolated execution environment for tool snippets; network-isolated, read-only filesystem | `src/backends/sandbox.py` | Docker daemon |

---

## 4. Components

| Container | Component | Source path | Responsibility | Depends on |
|-----------|-----------|-------------|----------------|------------|
| Eval Runner | ArmorEvalRunner | `src/runner.py` | Runs single attacks and full benchmark suites | AgentProtocol, ArmorClient, Judge |
| Eval Runner | Types | `src/types.py` | Shared dataclasses: AttackVector, AgentTrace, RunResult, AttackOutcome | — |
| Agent Archetypes | AgentProtocol | `src/agent_wrapper.py` | Protocol interface all agents must satisfy | — |
| Agent Archetypes | EchoAgent | `src/agents/echo_agent.py` | Echoes input back; default archetype for offline benchmarking | — |
| Agent Archetypes | RAGAgent | `src/agents/rag_agent.py` | Retrieval-augmented Q&A agent | BackendProtocol (via adapter) |
| Agent Archetypes | ToolUseAgent | `src/agents/tool_use_agent.py` | API/browser tool-use agent | BackendProtocol (via adapter), SandboxedToolExecutor (optional) |
| Agent Archetypes | MultiTurnAgent | `src/agents/multi_turn_agent.py` | Multi-turn conversational agent with session memory | BackendProtocol (via adapter) |
| ArmorGuard Wrapper | ArmorGuard | `src/agent_wrapper.py` | Wraps any AgentProtocol; raises SecurityBlockedError on block | ArmorClient |
| Backend Layer | BackendProtocol | `src/backends/protocol.py` | `@runtime_checkable` Protocol: `chat(messages) -> str` | — |
| Backend Layer | Adapters | `src/backends/adapters.py` | Factory functions converting BackendProtocol into per-agent callables | BackendProtocol |
| Backend Layer | OllamaBackend | `src/backends/ollama.py` | BackendProtocol implementation wrapping `ollama.Client` | Ollama server |
| Backend Layer | LlamaCppBackend | `src/backends/llamacpp.py` | BackendProtocol implementation wrapping `llama_cpp.Llama` | GGUF model file |
| Backend Layer | SandboxedToolExecutor | `src/backends/sandbox.py` | Executes tool snippets in Docker containers (--network none, --read-only) | Docker daemon |

---

## 5. Cross-cutting decisions

- **AgentProtocol** — all agent implementations must satisfy `AgentProtocol` (see `interfaces.md`). The runner and ArmorGuard never depend on concrete agent classes.
- **Armor is always optional** — the `armor_client` parameter is None by default. Every code path that touches Armor is gated on `if self.armor_client`.
- **Judgment is isolated** — `judge.py` has no imports from `runner.py` or `agent_wrapper.py`. The runner passes data to the judge; the judge never reaches back.
- **Results are pure return values** — no database, no side-effectful writes in the hot path. Persistence is the caller's responsibility.
- **BackendProtocol decouples agents from LLM providers** — agents receive callables (not backend objects) from the adapter layer. A backend change does not touch agent code. See ADR 001.
- **SandboxedToolExecutor is opt-in** — tool execution uses `simulated_execute_tool()` by default; the `--sandbox` flag replaces it with Docker-isolated execution. See ADR 003.
