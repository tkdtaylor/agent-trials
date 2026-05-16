# Behaviors

**Project:** Armor Eval
**Last updated:** 2026-05-16

What the system does, observably. Each behavior describes a triggering condition, the system's response, and any externally-visible side effects.

---

## Core behaviors

### B-001: Run a single attack vector against an agent

- **Trigger:** `ArmorEvalRunner.run_single_attack(attack, enable_armor)` is called
- **Response:** Instantiates the agent, optionally routes input through Armor, sends the attack payload, and returns a `RunResult` with an `AgentTrace` and `AttackOutcome`
- **Side effects:** None — results are returned, not persisted by the runner
- **Failure modes:** Agent crash → `AttackOutcome.ERROR` with the exception in `verdict_reasoning`

### B-002: Block an attack at the input stage

- **Trigger:** `enable_armor=True` and Armor's `check_input()` returns `blocked=True`
- **Response:** Returns `RunResult` with `outcome=BLOCKED`, `final_output="BLOCKED_BY_ARMOR_INPUT"`, and the Armor block record in `armor_blocks`
- **Side effects:** Agent is never invoked
- **Failure modes:** Armor SDK error → propagated as `AttackOutcome.ERROR`

### B-003: Block an attack at the output stage

- **Trigger:** `enable_armor=True`, the agent responds, and Armor's `check_output()` returns `blocked=True`
- **Response:** Returns `RunResult` with `outcome=BLOCKED`, the raw agent output in `final_output`, and the Armor block record in `armor_blocks`
- **Side effects:** Agent output is not returned to the caller — blocked at egress
- **Failure modes:** Armor SDK error → propagated as `AttackOutcome.ERROR`

### B-004: Judge attack outcome

- **Trigger:** `judge.py`'s `judge_outcome(attack, output, tool_calls)` is called after the agent responds without being Armor-blocked
- **Response:** Returns `(AttackOutcome, verdict_reasoning)` — `SUCCESS` if the attack succeeded, `BLOCKED` if the agent resisted, `FALSE_POSITIVE` if a benign input was rejected
- **Side effects:** None
- **Failure modes:** Unknown attack category → returns `BLOCKED` with a "unrecognized category" reasoning note

### B-005: Run full benchmark suite

- **Trigger:** `ArmorEvalRunner.run_benchmark(attacks, iterations)` is called
- **Response:** Runs each attack twice per iteration (without armor, then with armor), aggregates results, and returns a summary dict with detection rate, false positive rate, and average latency overhead
- **Side effects:** None — results are returned, not persisted
- **Failure modes:** Partial failure (one agent crash) → that `RunResult` is `ERROR`; the rest continue

### B-006: Display benchmark results in dashboard

- **Trigger:** `streamlit run dashboard/app.py`
- **Response:** Renders a Streamlit UI showing per-attack outcome table, detection rate, false positive rate, latency overhead, and per-attack trace viewer with side-by-side (bare vs. armored) comparison
- **Side effects:** None — read-only view over a results file or in-memory results
- **Failure modes:** No results loaded → dashboard shows empty state with instructions

### B-007: ArmorGuard wraps an agent for inline protection

- **Trigger:** `ArmorGuard.process(user_input)` is called
- **Response:** Routes input through Armor check, calls the wrapped agent if not blocked, routes output through Armor check, and returns the agent's response
- **Side effects:** Raises `SecurityBlockedError` if either check blocks
- **Failure modes:** Armor unavailable → if `armor_client` is None, passes through transparently (guard is inactive)

---

## Edge cases and error behaviors

### B-E001: Agent factory raises during instantiation

- **Trigger:** `agent_factory()` throws inside `run_single_attack`
- **Response:** Returns `RunResult` with `outcome=ERROR`, empty trace fields, and the exception message in `verdict_reasoning`
- **Side effects:** None

### B-E002: Attack corpus YAML is malformed or missing a required field

- **Trigger:** Loading `attacks/corpus.yaml` with a missing `id`, `payload`, or `category` field
- **Response:** Raises `ValueError` with the offending field and attack index — fast fail at load time, not mid-run
- **Side effects:** No benchmark run starts

---

## Behavioral invariants

- Every `RunResult` has a non-None `trace` — even on error, `AgentTrace` contains at minimum `input_received` and `final_output` (the exception message).
- `latency_ms` is always measured from the start of `run_single_attack` to the point of return, inclusive of Armor calls.
- `armor_active` in `RunResult` reflects the `enable_armor` argument, not whether Armor actually intervened.
- The runner never mutates the `AttackVector` passed to it.
