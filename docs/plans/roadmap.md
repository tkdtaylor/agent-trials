# Roadmap

**Project:** Agent Trials
**Last updated:** 2026-05-18

## Active milestones

### v1.0 — Polished demo

- [ ] CI pipeline (GitHub Actions)
- [ ] README demo GIF or screenshot
- [x] Full attack corpus expansion (39 vectors across 4 threat classes)

---

## Backlog

Unscheduled work lives in [`tasks/backlog/`](../tasks/backlog/). Items get promoted to a milestone when prioritized.

Candidate backlog items (not yet tasked):
- `--rag-docs` CLI flag to supply documents to `rag_retrieve` (currently uses empty list)
- `--tools` configuration for `SandboxedToolExecutor` (currently wired with empty `{}`)
- Custom Docker image support in `SandboxedToolExecutor` (for tool snippets needing third-party packages)
- Anthropic API backend (for benchmarking against Claude directly)

---

## Completed milestones

### v0.5 — Armor integration + per-agent routing ✅ (2026-05-18)

- [x] Extended attack corpus to 39 vectors across 4 threat classes — task 018
- [x] Armor v0.10.x daemon integration with canary honeypot seeding — task 019
- [x] `armor canary seed` one-step workflow — task 020
- [x] Per-agent routing: `--agent all` flag, `_CATEGORY_TO_AGENT` dispatch, `RunResult.agent_type` field, dict-of-factories constructor on `ArmorEvalRunner` — task 021

### v0.1 — Harness foundation ✅ (2026-05-16)

- [x] Project setup and tooling (pyproject, ruff, pytest, pre-commit)
- [x] Core types (`AttackVector`, `AgentTrace`, `RunResult`, `AttackOutcome`) — task 001
- [x] `AgentProtocol` + `ArmorGuard` wrapper — task 002
- [x] `judge.py` — outcome determination from output + tool calls — task 003
- [x] `EchoAgent` — offline archetype for harness testing without a backend — task 004
- [x] `ArmorEvalRunner` — `run_single_attack` + `run_benchmark` — task 005
- [x] Initial attack corpus (`attacks/corpus.yaml`) — task 010

### v0.2 — Agent archetypes ✅ (2026-05-16)

- [x] RAG Q&A agent (`src/agents/rag_agent.py`) — task 006
- [x] Tool-use agent (`src/agents/tool_use_agent.py`) — task 007
- [x] Multi-turn conversational agent (`src/agents/multi_turn_agent.py`) — task 008
- [x] Agent factory function (wired in `src/__main__.py`) — task 011
- [x] Integration tests with offline echo agent

### v0.3 — Dashboard + reporting ✅ (2026-05-16)

- [x] Streamlit dashboard (`dashboard/app.py`) — task 009
- [x] Side-by-side bare vs. armored comparison view
- [x] Per-attack trace viewer
- [x] Results serializer / JSON export — task 012

### v0.4 — Local LLM backends + sandboxing ✅ (2026-05-16)

- [x] `BackendProtocol` abstraction + adapter layer — task 013
- [x] `OllamaBackend` (default: `qwen2.5:14b`) — task 014
- [x] `LlamaCppBackend` (GGUF model files) — task 015
- [x] CLI `--backend`, `--model`, `--model-path` flags — task 016
- [x] `SandboxedToolExecutor` (Docker `--network none --read-only`) — task 017
