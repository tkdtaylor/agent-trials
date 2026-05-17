# Tech Stack

**Project:** Agent Trials
**Last updated:** 2026-05-18

## Core stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Language | Python 3.12 | Strong typing support, dataclasses, Protocol — good fit for the schema-heavy eval harness |
| Eval harness | Custom (src/runner.py) | Thin layer over agent factories — no framework needed |
| Agent archetypes | `BackendProtocol` adapters (`src/backends/adapters.py`) → `OllamaBackend` or `LlamaCppBackend`; default model `qwen2.5:14b` | Agents are decoupled from the LLM via a single `chat(messages) -> str` contract; local inference avoids the Anthropic API dependency (see ADR 001) |
| LLM runtime (HTTP) | Ollama | Default local inference server; required when `--backend ollama` (the default) |
| LLM runtime (in-process) | llama-cpp-python | GGUF-file inference; required when `--backend llamacpp` |
| Tool sandbox | Docker | `--network none --read-only` containers for safe execution of successful tool-use attack payloads; required when `--sandbox` is active (see ADR 003) |
| Attack corpus | YAML | Human-readable, version-controllable, no parse overhead |
| Dashboard | Streamlit | Minimal boilerplate for a local results viewer |
| Security layer | Armor SDK | Optional toggle — all calls gated on `armor_client` presence |

## Development tooling

| Tool | Purpose |
|------|---------|
| Git | Version control |
| ruff | Lint + format (replaces flake8, isort, black) |
| pre-commit | Enforce ruff before every commit |
| pytest | Test runner |
| pytest-cov | Coverage measurement |

## Testing

| Tool | Scope |
|------|-------|
| pytest | Unit tests (runner, judge, agent protocol) |
| pytest-cov | Coverage reporting (`--cov-fail-under=80`) |
| Dummy agent fixtures | End-to-end harness tests without calling real APIs |

## Notes

- Python 3.12+ required for `type` alias syntax and improved `Protocol` inference.
- All agent archetypes talk to LLMs through `BackendProtocol` (`src/backends/protocol.py`); `src/backends/adapters.py` converts a backend instance into the per-agent callables each archetype expects (`rag_generate`, `tool_use_decide`, `multi_turn_generate`, …). Agents never import a concrete backend type — swapping Ollama for llama.cpp is a runner-level flag, not a code change.
- Streamlit is a dev dependency only — not needed for benchmark runs.
