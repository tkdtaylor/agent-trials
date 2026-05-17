# Armor Eval

A Python framework for adversarially benchmarking AI agents before deployment, with Armor wired in as the optional defense layer.

Runs attack vectors (prompt injection, exfiltration, tool-call abuse, multi-turn chunked attacks) against pluggable agent archetypes — with and without Armor active — and produces a report card showing detection rates, latency overhead, and per-attack traces.

## Demo

![Armor Eval benchmark report — 20 attacks across 4 threat categories, bare vs. armored side-by-side](artifacts/demo.svg)

> **Note:** The demo above uses `EchoAgent` (fully offline — no backend or API keys required).
> Outcomes reflect the judge's heuristics against echoed input, not live Armor protection.
> For real results against a vulnerable model: `python -m src --agent rag --backend ollama --model qwen2.5:14b`

## Tech stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Agent archetypes | Echo (offline), RAG Q&A, Tool-use, Multi-turn conversational |
| LLM backends | Ollama (`qwen2.5:14b` default), llama-cpp-python (GGUF) |
| Attack corpus | YAML (`attacks/corpus.yaml`) |
| Security layer | Armor SDK (toggled per run) |
| Dashboard | Streamlit |
| Tests | pytest + pytest-cov |
| Lint / format | ruff |

## Getting started

```bash
# Install dependencies (use anaconda or a venv with Python 3.12+)
pip install -r requirements.txt

# Run tests (offline — no backends required)
pytest

# Run the benchmark with the default echo agent (offline, no backend needed)
python -m src

# Run with Ollama backend (requires Ollama running locally)
python -m src --agent rag --backend ollama --model qwen2.5:14b

# Run with llama-cpp backend
python -m src --agent multi-turn --backend llamacpp --model-path /path/to/model.gguf

# Run the dashboard
streamlit run dashboard/app.py
```

## Project structure

```
src/              eval framework (runner, agent_wrapper, judge, types)
src/agents/       concrete agent implementations (echo, RAG, tool-use, multi-turn)
src/backends/     LLM backend abstraction (BackendProtocol, Ollama, LlamaCpp, sandbox)
attacks/          YAML attack corpus
dashboard/        Streamlit reporting UI
tests/            pytest test suite
artifacts/        non-code outputs (diagrams, schemas, exports)
docs/             documentation and spec
  spec/           authoritative current-state snapshot (architecture, interfaces, data model)
  architecture/   system design, ADRs, diagrams, tech stack
  plans/          roadmap, sprints
  tasks/          active, backlog, completed task files
    test-specs/   TDD specs (written before implementation)
```

## How to work on this project

This project follows a TDD + task-based workflow. All initial tasks are complete — the project is benchmarkable end-to-end.

To add new work:

1. **Write a test spec** in [`docs/tasks/test-specs/`](docs/tasks/test-specs/) — no implementation starts without one
2. **Create a task file** in [`docs/tasks/backlog/`](docs/tasks/backlog/)
3. **Implement** until all test cases pass
4. **Move** the task to [`docs/tasks/completed/`](docs/tasks/completed/) and commit

Tasks are scoped small — one task does one thing. When in doubt, break it smaller.

## Key files

- [CLAUDE.md](CLAUDE.md) — project context for Claude Code sessions
- [docs/architecture/overview.md](docs/architecture/overview.md) — system design
- [docs/architecture/tech-stack.md](docs/architecture/tech-stack.md) — full tech stack table
- [docs/plans/roadmap.md](docs/plans/roadmap.md) — planned work
- [docs/tasks/test-specs/coverage-tracker.md](docs/tasks/test-specs/coverage-tracker.md) — test coverage by task
