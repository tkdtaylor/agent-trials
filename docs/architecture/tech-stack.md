# Tech Stack

**Project:** Armor Eval
**Last updated:** 2026-05-16

## Core stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Language | Python 3.12 | Strong typing support, dataclasses, Protocol — good fit for the schema-heavy eval harness |
| Eval harness | Custom (src/runner.py) | Thin layer over agent factories — no framework needed |
| Agent archetypes | Anthropic SDK (claude-sonnet-4-6) | RAG and multi-turn agents call Claude; tool-use agent uses external APIs |
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
- Anthropic SDK used for RAG and multi-turn agents — tool-use agent uses `httpx` or equivalent for external API calls.
- Streamlit is a dev dependency only — not needed for benchmark runs.
