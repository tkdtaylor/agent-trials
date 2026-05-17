# Agent Trials — Authoritative Spec

**Project:** Agent Trials
**Last updated:** 2026-05-16

## What this directory is

`docs/spec/` is the **authoritative current-state snapshot** of Agent Trials. It answers the question:

> "If the code were deleted tomorrow, what would I need to write down to rebuild it?"

The spec is dual-natured:

- **Output of current sessions** — every completed task that changes externally-observable behavior, the data model, an interface, or configuration must update the relevant spec file in the same commit.
- **Input to future sessions** — used for onboarding, drift audits against the code, and (in the limit) regenerating the codebase from scratch.

The code is one *realization* of this spec. If the spec and code disagree, one of them is wrong — fix the wrong one in that same change.

## Spec vs. ADRs vs. overview

| Doc | Purpose | Lifecycle |
|-----|---------|-----------|
| [`docs/spec/`](.) | What the system **does and is** today | Snapshot — supersede in place, never append |
| [`docs/architecture/decisions/`](../architecture/decisions/) | **Why** decisions were made | Append-only history; ADRs can be superseded by later ADRs |
| [`docs/architecture/overview.md`](../architecture/overview.md) | Narrative tour of the system | Snapshot, but optimized for human reading |
| [`docs/architecture/diagrams.md`](../architecture/diagrams.md) | Visual structure and flows | Snapshot, part of the spec |

## The six sub-files

| File | Covers | Read this when |
|------|--------|---------------|
| [behaviors.md](behaviors.md) | What the system does — user-facing behaviors, use cases, observable contracts | You need to know what should happen when X |
| [architecture.md](architecture.md) | C4 element catalog — persons, systems, containers, components, cross-cutting decisions | You need a structured/queryable view of the architecture |
| [data-model.md](data-model.md) | Entities, schemas, persistent state, in-memory state shape | You need to know what data exists and how it's structured |
| [interfaces.md](interfaces.md) | External and internal interfaces — CLI, APIs, public traits, wire protocols | You need to know what calls into or out of the system |
| [configuration.md](configuration.md) | Env vars, config files, runtime parameters, deployment knobs | You need to know what's tunable |
| [fitness-functions.md](fitness-functions.md) | Executable architectural invariants — layering, perf budgets, security thresholds, complexity ceilings | You're adding a continuous check, or wondering why `make fitness` exists |

## Maintenance rules

1. **Update in the same commit as the code change.** A task that changes behavior is not done until `behaviors.md` reflects it.
2. **Supersede in place. Never append.** When a decision changes, rewrite the spec entry — don't add a "previously this was X" note. The ADR carries that history.
3. **No future tense.** The spec describes what *is*, not what *will be*. Roadmap and planned work live in `docs/plans/` and `docs/tasks/`.
4. **No implementation rationale.** "We chose X because Y" belongs in an ADR. The spec just says "uses X."
5. **Audit drift periodically.** Use the `architect` agent's drift-audit mode to check the spec against the code.

## Project summary

Agent Trials is an adversarial trial framework for AI agents. It runs a curated corpus of attack vectors (prompt injection, exfiltration, tool-call abuse, multi-turn chunked attacks) against pluggable agent archetypes — both with and without the Armor security layer active — and produces a structured report card showing detection rates, false positive rates, latency overhead, and per-attack traces.

The four built-in agent archetypes are: Echo (offline/testing), RAG Q&A (retrieval-augmented), tool-use (API/browser), and multi-turn conversational.

## Top-level invariants

- All attack runs produce a `RunResult` with a complete `AgentTrace` — no silent drops.
- Armor is toggled per-run via the `enable_armor` flag; the framework never assumes Armor is present.
- Attack IDs are stable references in the corpus — never reused, even when an attack is retired.
- Judgment (pass/fail/blocked/error) is determined by `judge.py` alone — no inline verdict logic in the runner.

## Non-goals

- Production deployment of the agents under test — this framework is a dev-lifecycle gate, not a hosting platform.
- The private trading/financial agent archetype — excluded unless explicitly re-introduced.
- Real-time streaming attack runs — results are batch-collected per benchmark run.
