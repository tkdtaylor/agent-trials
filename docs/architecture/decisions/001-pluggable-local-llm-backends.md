# ADR 001 — Pluggable local LLM backends over Anthropic API

**Date:** 2026-05-16
**Status:** Accepted

## Context

The initial framework design assumed agent archetypes (RAG, tool-use, multi-turn) would call the Anthropic API directly. This creates several problems for the primary use case — demonstrating how Armor protects agents before deployment:

- API costs accumulate during development and demo iterations.
- Live API calls make benchmark runs non-deterministic and require internet access.
- GPT-class models are well-aligned and harder to attack, which reduces the visible contrast between armored and unarmored runs — the opposite of what the demo needs.
- A single hardcoded provider blocks operators who want to benchmark agents running on self-hosted infrastructure.

The project already runs on hardware capable of 14B+ local models (64 GB RAM), and Ollama and llama-cpp-python are already installed.

## Decision

Replace direct Anthropic API calls with a `BackendProtocol` abstraction layer.

`BackendProtocol` is a `@runtime_checkable` `typing.Protocol` with a single method:

```python
def chat(self, messages: list[dict]) -> str: ...
```

`OllamaBackend` and `LlamaCppBackend` implement it. An adapter layer (`src/backends/adapters.py`) converts backend instances into the per-agent callables each archetype expects (`retrieve`, `generate`, `decide_tools`, `execute_tool`). Agent code receives callables — it has no dependency on backend types.

The default model is `qwen2.5:14b` (Ollama, ~9 GB Q4_K_M), chosen because it fits within the target RAM budget, is instruction-tuned, and is meaningfully vulnerable to prompt injection — which makes Armor's protection more visible in demo output.

## Consequences

**Positive:**
- Offline, zero-API-cost benchmarking.
- Smaller, more-vulnerable models make Armor's protection contrast sharper in demos.
- Adding a new backend (OpenAI-compatible proxy, vLLM, etc.) requires only a new `BackendProtocol` implementor — no agent code changes.
- Integration tests are explicitly marked `@pytest.mark.integration` and skipped by default; unit tests mock the backend.

**Negative:**
- Benchmarks against top-tier models (GPT-4o, Claude 3.5) require a new backend implementation.
- Local model quality varies; results are not directly comparable across hardware.

## Alternatives considered

- **Keep Anthropic API, make it optional:** Rejected — still requires API key for any real-agent benchmark run, and aligned models underperform the demo goal.
- **Hardcode Ollama only:** Rejected — llama-cpp-python is already available and provides a no-server path for GGUF models.
