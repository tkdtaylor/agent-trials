# Armor Eval

A Python framework for adversarially benchmarking AI agents before deployment, with Armor wired in as the optional defense layer.

Runs attack vectors (prompt injection, exfiltration, tool-call abuse, multi-turn chunked attacks) against pluggable agent archetypes — with and without Armor active — and produces a report card showing detection rates, latency overhead, and per-attack traces.

## Tech stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Agent archetypes | RAG Q&A, Tool-use, Multi-turn conversational |
| Attack corpus | YAML (`attacks/corpus.yaml`) |
| Security layer | Armor SDK (toggled per run) |
| Dashboard | Streamlit |
| Tests | pytest + pytest-cov |
| Lint / format | ruff |

## Getting started

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run the benchmark (example)
python -m src.runner

# Run the dashboard
streamlit run dashboard/app.py
```

## Project structure

```
src/              eval framework (runner, agent_wrapper, judge, types)
src/agents/       concrete agent implementations (RAG, tool-use, multi-turn)
attacks/          YAML attack corpus
dashboard/        Streamlit reporting UI
tests/            pytest test suite
artifacts/        non-code outputs (diagrams, schemas, exports)
docs/             documentation and spec
  architecture/   system design, ADRs, tech stack
  plans/          roadmap, sprints
  tasks/          active, backlog, completed task files
    test-specs/   TDD specs (written before implementation)
```

## How to work on this project

This project follows a TDD + task-based workflow:

1. **Pick a task** from [`docs/tasks/active/`](docs/tasks/active/) or [`docs/tasks/backlog/`](docs/tasks/backlog/)
2. **Read its test spec** in [`docs/tasks/test-specs/`](docs/tasks/test-specs/) — no implementation starts without one
3. **Implement** until all test cases pass
4. **Move** the task to [`docs/tasks/completed/`](docs/tasks/completed/) and commit

Tasks are scoped small — one task does one thing. When in doubt, break it smaller.

## Key files

- [CLAUDE.md](CLAUDE.md) — project context for Claude Code sessions
- [docs/architecture/overview.md](docs/architecture/overview.md) — system design
- [docs/architecture/tech-stack.md](docs/architecture/tech-stack.md) — full tech stack table
- [docs/plans/roadmap.md](docs/plans/roadmap.md) — planned work
- [docs/tasks/test-specs/coverage-tracker.md](docs/tasks/test-specs/coverage-tracker.md) — test coverage by task
