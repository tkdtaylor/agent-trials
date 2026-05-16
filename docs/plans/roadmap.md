# Roadmap

**Project:** Armor Eval
**Last updated:** 2026-05-16

## Milestones

### v0.1 — Harness foundation

- [ ] Project setup and tooling (pyproject, ruff, pytest, pre-commit)
- [ ] Core types (`AttackVector`, `AgentTrace`, `RunResult`, `AttackOutcome`)
- [ ] `AgentProtocol` + `ArmorGuard` wrapper
- [ ] `judge.py` — outcome determination from output + tool calls
- [ ] Dummy agent (echo agent for harness testing without real APIs)
- [ ] `ArmorEvalRunner` — `run_single_attack` + `run_benchmark`
- [ ] Initial attack corpus (`attacks/corpus.yaml`) with ≥10 vectors across all four categories

### v0.2 — Agent archetypes

- [ ] RAG Q&A agent (`src/agents/rag_agent.py`)
- [ ] Tool-use agent (`src/agents/tool_use_agent.py`)
- [ ] Multi-turn conversational agent (`src/agents/multi_turn_agent.py`)
- [ ] Agent factory function
- [ ] Integration tests with dummy Armor mock

### v0.3 — Dashboard + reporting

- [ ] Streamlit dashboard (`dashboard/app.py`)
- [ ] Side-by-side bare vs. armored comparison view
- [ ] Per-attack trace viewer
- [ ] Results export (JSON)

### v1.0 — Polished demo

- [ ] Full attack corpus across all four threat classes
- [ ] CI pipeline (GitHub Actions)
- [ ] README demo GIF or screenshot

---

## Backlog

Unscheduled work lives in [`tasks/backlog/`](../tasks/backlog/). Items get promoted to a milestone when prioritized.

---

## Completed milestones

> Move sections here as milestones are reached, with a completion date.
