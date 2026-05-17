# Architecture Overview

**Project:** Armor Eval
**Last updated:** 2026-05-16

## What this is

Armor Eval is an adversarial benchmarking framework for AI agents. It runs a curated corpus of attack vectors against pluggable agent archetypes — with and without the Armor security layer active — and produces a structured report card showing detection rates, latency overhead, and per-attack traces.

## High-level design

The framework has four moving parts:

1. **Attack Corpus** (`attacks/corpus.yaml`) — a curated YAML file of attack vectors across four threat classes: input injection, exfiltration, tool-call abuse, and multi-turn chunked attacks.

2. **Agent Archetypes** (`src/agents/`) — four concrete implementations of `AgentProtocol`: Echo (offline/testing), RAG Q&A, tool-use (API/browser), and multi-turn conversational. The runner instantiates these via a factory function so the harness never depends on concrete classes. The Echo agent requires no backend and is the default for offline benchmarking; the others require a `BackendProtocol` implementation.

2a. **Backend Layer** (`src/backends/`) — pluggable LLM backend abstraction. `BackendProtocol` defines a single `chat(messages) -> str` interface. `OllamaBackend` and `LlamaCppBackend` implement it. The adapter layer (`adapters.py`) converts backend instances into the per-agent callables each archetype expects — so agent code never depends on backend types. See ADR 001.

3. **Eval Harness** (`src/runner.py`, `src/agent_wrapper.py`, `src/judge.py`) — the runner drives each attack twice (bare and armored), `ArmorGuard` provides the inline Armor toggle, and the judge determines the outcome independently of the runner.

4. **Dashboard** (`dashboard/app.py`) — a Streamlit UI that reads benchmark results and renders a side-by-side comparison (bare agent vs. armored agent) with per-attack trace viewer.

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

Attack vectors from the corpus are loaded at benchmark start. The runner iterates over attacks, instantiating a fresh agent per run. For armored runs, the payload passes through `ArmorGuard` before reaching the agent (and the output passes through again on egress). The agent response goes to the judge, which returns an `AttackOutcome`. The runner collects all `RunResult` objects and aggregates them into a summary dict. The dashboard reads that dict and renders it.

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
