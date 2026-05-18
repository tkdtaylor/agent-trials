# Roadmap

**Project:** Agent Trials
**Last updated:** 2026-05-18

## Active milestones

### v1.0 — Polished demo

- [x] README demo screenshot (architecture diagram + per-attack SVG report)

---

## Backlog

Items get promoted to a milestone when prioritized.

Candidate backlog items (not yet tasked):
- CI pipeline (GitHub Actions) — pytest + ruff on PRs
- `--rag-docs` CLI flag to supply documents to `rag_retrieve` (currently uses empty list)
- `--tools` configuration for `SandboxedToolExecutor` (currently wired with empty `{}`)
- Custom Docker image support in `SandboxedToolExecutor` (for tool snippets needing third-party packages)
- Anthropic API backend (for benchmarking against Claude directly)

---

## Completed milestones

### v0.1 — Harness foundation ✅ (2026-05-16)

- [x] Project setup — pyproject.toml, ruff, pytest, pre-commit, Makefile
- [x] Core types: `AttackVector`, `AgentTrace`, `RunResult`, `AttackOutcome`
- [x] `AgentProtocol` + `ArmorGuard` wrapper (`src/agent_wrapper.py`)
- [x] `judge.py` — outcome determination from agent output and tool calls
- [x] `EchoAgent` — offline archetype for harness testing without a backend
- [x] `ArmorEvalRunner` — `run_single_attack` + `run_benchmark` with bare/armored pairing
- [x] Initial attack corpus (`attacks/corpus.yaml`) with `expected_behavior` scoring

### v0.2 — Agent archetypes ✅ (2026-05-16)

- [x] RAG Q&A agent (`src/agents/rag_agent.py`) — retrieval + generation callables via `BackendProtocol`
- [x] Tool-use agent (`src/agents/tool_use_agent.py`) — decide / execute / generate loop
- [x] Multi-turn conversational agent (`src/agents/multi_turn_agent.py`) — stateful history
- [x] Agent factory wired into CLI (`src/__main__.py`)
- [x] Integration tests with offline EchoAgent

### v0.3 — Dashboard + reporting ✅ (2026-05-16)

- [x] Streamlit dashboard (`dashboard/app.py`) — side-by-side bare vs. armored summary metrics
- [x] Per-attack trace viewer (expandable per-result detail)
- [x] Results serializer / JSON export (`src/results.py`)
- [x] `--output` flag for configurable results path

### v0.4 — Local LLM backends + sandboxing ✅ (2026-05-16)

- [x] `BackendProtocol` abstraction + adapter layer (`src/backends/`)
- [x] `OllamaBackend` (default model: `qwen2.5:14b`)
- [x] `LlamaCppBackend` (GGUF model files via `--model-path`)
- [x] CLI `--backend`, `--model`, `--model-path` flags
- [x] `SandboxedToolExecutor` — Docker `--network none --read-only` isolation for tool-use agent
- [x] `--sandbox` CLI flag; `--think` flag for qwen3.x thinking-mode models

### v0.5 — Armor v0.10.x integration + canary honeypot ✅ (2026-05-18)

- [x] Armor daemon integration over Unix socket (`ArmorClient`, `--armor-socket` flag)
- [x] Armor v0.10.0 — SSRF probe, sensitive-file probe, `.env` credential honeypot
- [x] Armor v0.10.1 — `regex.code_injection`, `regex.exfil_chain`, `regex.sensitive_file_probe:write-etc-privileged`
- [x] Armor v0.10.2 — PII canary patterns (exfil-011/exfil-012), `pii:fake_address` canary type, `user-profile.json` honeypot
- [x] `armor canary seed --out-dir` one-step honeypot workflow; `--canary-inject` flag wires PII context into RAG agent system prompt
- [x] Attack corpus expanded to 39 vectors across 4 threat classes (input_injection, exfiltration, tool_abuse, multi_turn)
- [x] `scripts/demo_report.py` — terminal-style SVG report with per-attack bare vs. armored breakdown
- [x] `scripts/export_analysis.py` — structured JSON export for sharing gap analysis
- [x] Per-attack consistency verdicts (`armor_adds_protection` / `model_level` / `missed_both` / `flaky`) across N iterations
- [x] Benchmark result: 44% bare DR → 99% armored DR, 0 false positives, 0 missed attacks (with canary wired)

### v0.6 — Per-agent routing + report improvements ✅ (2026-05-18)

- [x] `--agent all` flag — routes each attack category to its natural archetype (`rag`, `tool_use`, `multi_turn`)
- [x] `RunResult.agent_type` field — tracks which archetype ran each attack
- [x] Per-category grouping and agent column in demo report
- [x] Dashboard improvements — clean per-attack table with `agent_type` and consistency verdicts
- [x] Consistency verdict section in dashboard (armor_adds_protection / model_level / missed_both / flaky counts)

