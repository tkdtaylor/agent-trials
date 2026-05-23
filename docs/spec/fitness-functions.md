# Fitness functions

**Project:** Agent Trials
**Last updated:** 2026-05-23

## What this file is

Fitness functions are **executable architectural invariants** — automated checks that verify the code still obeys the rules this project commits to.

## How to run

```bash
make fitness          # run all fitness functions
make fitness-<rule>   # run one rule by name
```

## Rules

| ID | Rule | Category | Asserts | Threshold | Check command | Severity | Why this rule earns its row |
|----|------|----------|---------|-----------|---------------|----------|----------------------------|
| F-001 | No inline verdict logic outside judge.py | structural | `src/runner.py` and `src/agent_wrapper.py` contain no `AttackOutcome` assignments | 0 violations | `make fitness-no-inline-verdict` | block | Judgment logic scattered across the runner defeats the isolation design. Catch at first introduction. |
| F-002 | AgentProtocol not imported from concrete agent modules | layering | `src/runner.py` imports only from `src/types.py` and `src/agent_wrapper.py` — not from `src/agents/` | 0 violations | `make fitness-layering` | block | The runner must be independent of concrete implementations for the factory pattern to hold. |
| F-003 | No hardcoded API keys or secrets in source | security | No `sk-`, `ARMOR_API_KEY=`, or `ANTHROPIC_API_KEY=` literals in `src/` or `tests/` | 0 hits | `make fitness-no-secrets` | block | Stray credentials in source get committed and rotated after the fact — catch at first appearance. |
| F-004 | Corpus YAML has all required fields | hygiene | Every entry in `attacks/corpus.yaml` has `id`, `name`, `payload`, `expected_behavior`, `category` | 0 missing | `make fitness-corpus` | block | A malformed corpus entry causes a mid-run crash; validate at load time instead. |
| F-005 | BackendProtocol satisfied by all backends | layering | `OllamaBackend` and `LlamaCppBackend` both satisfy `BackendProtocol` at import time (verified via `isinstance` check with `runtime_checkable`) | 0 violations | `make fitness-backend` | block | The whole adapter layer relies on `BackendProtocol` duck-typing; a backend that drifts from the contract silently breaks all agent archetypes. |
| F-006 | Judge exfiltration accuracy — non-possession and compliance signals present | correctness | `src/judge.py` defines both `_NON_POSSESSION_SIGNALS` and `_EXFIL_COMPLIANCE_SIGNALS` frozensets | 0 missing | `make fitness-judge` | block | The 4-step exfiltration decision tree depends on these signal sets; removing either causes the judge to fall back to binary refusal/success detection, producing false positives on "I don't have that data" responses. |

## Rules considered but rejected

| Proposed rule | Why rejected |
|---------------|--------------|
| Test coverage ≥ 90% | Coverage % drives cosmetic test additions; the spec-coverage hook plus spec-verifier agent give better signal at lower cost. |

## Source-of-truth links

- F-001 (no-inline-verdict) ← `architecture.md` §Cross-cutting decisions ("Judgment is isolated")
- F-002 (layering) ← `architecture.md` §Cross-cutting decisions ("AgentProtocol")
- F-003 (no-secrets) ← `configuration.md` §Secrets (defaults policy)
- F-004 (corpus) ← `data-model.md` §AttackVector (identity invariant)
- F-005 (backend) ← `interfaces.md` §BackendProtocol (contract invariant); ADR 001
- F-006 (judge) ← `behaviors.md` §B-004 (exfiltration 4-step decision tree); `tests/test_judge.py` TC-009-11 through TC-009-15
