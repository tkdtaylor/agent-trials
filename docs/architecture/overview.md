# Architecture Overview

**Project:** Agent Trials
**Last updated:** 2026-05-18

## What this is

Agent Trials is an adversarial trial framework for AI agents. It runs a curated corpus of attack vectors against pluggable agent archetypes — with and without the Armor security layer active — and produces a structured report card showing detection rates, latency overhead, and per-attack traces.

## High-level design

The framework has five moving parts:

1. **Attack Corpus** (`attacks/corpus.yaml`) — a curated YAML file of attack vectors across four threat classes: input injection, exfiltration, tool-call abuse, and multi-turn chunked attacks.

2. **Agent Archetypes** (`src/agents/`) — four concrete implementations of `AgentProtocol`: Echo (offline/testing), RAG Q&A, tool-use (API/browser), and multi-turn conversational. The runner instantiates these via a factory function so the harness never depends on concrete classes. When `agent_factories` is a single callable (i.e. `--agent rag`), every attack runs against that archetype. When it's a dict (i.e. `--agent all`), `_resolve_factory` routes each attack to its natural archetype via `_CATEGORY_TO_AGENT = {input_injection: rag, exfiltration: rag, tool_abuse: tool_use, multi_turn: multi_turn}`, so each attack class lands on the archetype it was designed to exercise. The Echo agent requires no backend and is the default for offline benchmarking; the others require a `BackendProtocol` implementation.

3. **Backend Layer** (`src/backends/`) — pluggable LLM backend abstraction. `BackendProtocol` defines a single `chat(messages) -> str` interface. `OllamaBackend` and `LlamaCppBackend` implement it. The adapter layer (`adapters.py`) converts backend instances into the per-agent callables each archetype expects — so agent code never depends on backend types. See ADR 001.

4. **Eval Harness** (`src/runner.py`, `src/agent_wrapper.py`, `src/judge.py`) — the runner drives each attack twice (bare and armored), `ArmorGuard` provides the inline Armor toggle, and the judge determines the outcome independently of the runner.

5. **Dashboard** (`dashboard/app.py`) — a Streamlit UI that reads benchmark results and renders a side-by-side comparison (bare agent vs. armored agent) with per-attack trace viewer.

Visual diagrams (component layout, runtime sequence) live in [diagrams.md](diagrams.md). The structured element catalog is in [`../spec/architecture.md`](../spec/architecture.md).

## Key decisions

| Decision | Choice | ADR |
|----------|--------|-----|
| Judgment isolated to judge.py | `judge.py` has no imports from `runner.py`; runner passes data, judge returns verdict | — |
| Armor is always optional | `armor_client=None` by default; every Armor call gated on presence | — |
| AgentProtocol for all archetypes | Runtime duck-typing via Protocol, not ABC | — |
| Results as pure return values | No database writes in the hot path | — |
| Pluggable local LLM backends over Anthropic API | `BackendProtocol` abstraction + Ollama/LlamaCpp adapters; agents receive callables, not backend objects | ADR 001 |
| EchoAgent as default offline archetype | Echoes input; default `--agent echo`; no backend required; enables offline CI and framework correctness testing | ADR 002 |
| Docker-sandboxed tool execution | `SandboxedToolExecutor` with `--network none --read-only`; opt-in via `--sandbox`; safe demo of successful attacks | ADR 003 |

## Data flow

Attack vectors from the corpus are loaded at benchmark start. The runner iterates over attacks, instantiating a fresh agent per run. The agent response goes to the judge, which returns an `AttackOutcome`. The runner collects all `RunResult` objects and aggregates them into a summary dict. The dashboard reads that dict and renders it.

For **armored runs**, the setup is:
1. Before the benchmark starts, `armor canary seed` generates a fresh set of honeypot canary values.
2. The Armor daemon is started with `--canary-values` so it knows what tokens to watch for in agent output.
3. The runner constructs an `ArmorClient` which connects to the daemon over a Unix socket — Armor itself runs as a separate process, not in-process.
4. For each attack, `ArmorGuard` calls `check_input(payload)` over the socket before the agent sees the payload. If the daemon blocks, the run terminates as `BLOCKED` with no agent call.
5. Otherwise the agent processes the request; the response goes back through `check_output(response)` before being returned to the runner.
6. When `--canary-inject` is set, the seeded canary values are also injected as honeypot PII into the RAG agent's system prompt, so an exfiltration attack that succeeds in leaking system-prompt contents will surface the canary tokens to `check_output` and be caught.

## External dependencies

| Dependency | Purpose | Notes |
|------------|---------|-------|
| Armor SDK | Input/output threat detection | Optional — guarded by `armor_client` presence |
| Ollama | Local LLM inference (HTTP) | Optional — required when `--backend ollama` |
| llama-cpp-python | Local LLM inference (GGUF files) | Optional — required when `--backend llamacpp` |
| Docker | Sandboxed tool execution | Optional — required when `--sandbox` is active |
| Streamlit | Dashboard UI | Dev/local only — not part of the benchmark core |

## Design principles

This project follows **Unix philosophy** as its default design approach — favoring **composability over monolithic design**. The operating-system analogy is deliberate: complex behavior should emerge from combining small, independent components that communicate through standardized interfaces.

### The four structural properties to design for

- **Modularity** — break the system into independent units that can be built, understood, changed, and tested on their own.
- **Interface standardization** — components communicate through stable, well-defined contracts: `AgentProtocol`, `AttackVector`, `RunResult`.
- **Maintainability** — changes to one agent archetype should not require rewriting the runner or the judge.
- **Reusability** — the runner and judge can be used with any `AgentProtocol` implementor without modification.

### Derived working rules

- **One thing, well** — runner runs, judge judges, guard guards, dashboard displays.
- **Plain text where possible** — attack corpus is YAML; results can be serialized to JSON.
- **Fail fast, crash loudly** — malformed corpus entries raise at load time, not mid-run.
- **Test in isolation** — runner, judge, and each agent archetype are testable independently.

## Constraints and non-goals

- No production hosting of agents — this is a dev-lifecycle gate, not a serving platform.
- No real-time streaming benchmark runs — results are batch-collected.
- No private trading/financial agent archetype unless explicitly re-introduced.
