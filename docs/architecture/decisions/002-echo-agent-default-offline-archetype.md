# ADR 002 — EchoAgent as default offline archetype

**Date:** 2026-05-16
**Status:** Accepted

## Context

The three "real" agent archetypes (RAG, tool-use, multi-turn) all require a `BackendProtocol` implementation to function — i.e., a running Ollama server or a GGUF model file. This makes them unusable in CI environments, quick sanity checks, and offline dev sessions where no backend is available.

The framework needs a default agent that:
- Works with zero configuration.
- Lets the runner, ArmorGuard, judge, and corpus loading be exercised without any LLM.
- Is honest about what it does — it should not pretend to be a real agent.

## Decision

Add `EchoAgent` (`src/agents/echo_agent.py`) as a fourth archetype. It echoes the input payload back as its response, with no external calls.

`EchoAgent` is the default value for `--agent` (`echo`). Running `python -m src` with no flags uses it. The CLI guard that blocks `rag`, `tool-use`, and `multi-turn` without a backend does not apply to `echo`.

## Consequences

**Positive:**
- `pytest` suite runs fully offline — no backend fixture needed.
- New contributors can run a complete benchmark loop immediately after cloning.
- Framework bugs (runner logic, ArmorGuard wiring, judge correctness) are catchable without spinning up an LLM.

**Negative:**
- Echo responses are not realistic attack targets — `judge_outcome` will classify most attacks as `SUCCESS` since the echo output contains the attack payload verbatim. This is expected and documented.
- The archetype count is now four, not three — all documentation must reflect this.
