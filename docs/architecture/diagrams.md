# Architecture Diagrams

**Project:** Armor Eval
**Last updated:** 2026-05-16

C4-structured Mermaid diagrams. See [overview.md](overview.md) for prose context and [`../spec/architecture.md`](../spec/architecture.md) for the structured element catalog these diagrams render.

---

## 1. System Context

```mermaid
C4Context
    title System Context for Armor Eval

    Person(dev, "Developer / Security Engineer", "Runs adversarial benchmarks before deploying agents")
    System(armor_eval, "Armor Eval", "Adversarial benchmarking framework for AI agents")
    System_Ext(armor_sdk, "Armor SDK", "Input/output threat detection")
    System_Ext(anthropic, "Anthropic API", "Claude model inference for agent archetypes")

    Rel(dev, armor_eval, "Runs benchmarks, views dashboard")
    Rel(armor_eval, armor_sdk, "Checks inputs/outputs", "SDK calls")
    Rel(armor_eval, anthropic, "Calls Claude", "HTTPS / API")
```

---

## 2. Containers

```mermaid
C4Container
    title Container view of Armor Eval

    Person(dev, "Developer")

    System_Boundary(boundary, "Armor Eval") {
        Container(runner, "Eval Runner", "Python", "Drives attack runs, coordinates Armor toggle, aggregates results")
        Container(agents, "Agent Archetypes", "Python", "RAG, tool-use, multi-turn — implement AgentProtocol")
        Container(guard, "ArmorGuard", "Python", "Inline Armor wrapper — checks input/output per run")
        Container(judge, "Judge", "Python", "Determines AttackOutcome from agent output and tool calls")
        Container(corpus, "Attack Corpus", "YAML", "Curated attack vectors across four threat classes")
        Container(dashboard, "Dashboard", "Streamlit", "Read-only results viewer")
    }

    System_Ext(armor_sdk, "Armor SDK")
    System_Ext(anthropic, "Anthropic API")

    Rel(dev, runner, "Invokes")
    Rel(dev, dashboard, "Views results")
    Rel(runner, corpus, "Loads attacks")
    Rel(runner, agents, "Instantiates via factory")
    Rel(runner, guard, "Wraps agent for armored runs")
    Rel(runner, judge, "Passes output for verdict")
    Rel(guard, armor_sdk, "check_input / check_output")
    Rel(agents, anthropic, "Claude inference (RAG, multi-turn)")
```

---

## 3. Components — Eval Harness

```mermaid
C4Component
    title Component view of the Eval Harness

    Container_Boundary(harness, "Eval Harness") {
        Component(runner_cls, "ArmorEvalRunner", "src/runner.py", "run_single_attack, run_benchmark, _aggregate_results")
        Component(types, "Types", "src/types.py", "AttackVector, AgentTrace, RunResult, AttackOutcome")
        Component(guard_cls, "ArmorGuard + AgentProtocol", "src/agent_wrapper.py", "Inline Armor toggle; Protocol all agents satisfy")
        Component(judge_fn, "judge_outcome()", "src/judge.py", "Determines outcome from output + tool calls")
    }

    Container(agents_c, "Agent Archetypes", "src/agents/")
    System_Ext(armor_sdk_c, "Armor SDK")

    Rel(runner_cls, types, "Uses")
    Rel(runner_cls, guard_cls, "Wraps agent")
    Rel(runner_cls, judge_fn, "Calls for verdict")
    Rel(guard_cls, armor_sdk_c, "check_input / check_output")
    Rel(runner_cls, agents_c, "Instantiates via factory")
```

**Key contracts**
- `judge_fn` has no imports from `runner_cls` — data flows one way
- `runner_cls` imports from `types` and `guard_cls` only — never from `src/agents/` directly
- `AgentProtocol` is the only coupling point between the harness and the archetypes

---

## 4. Primary runtime flow — armored attack run

```mermaid
sequenceDiagram
    autonumber
    participant Dev as Developer
    participant Runner as ArmorEvalRunner
    participant Corpus as corpus.yaml
    participant Guard as ArmorGuard
    participant Armor as Armor SDK
    participant Agent as Agent (RAG/Tool/MT)
    participant Judge as judge.py

    Dev->>Runner: run_benchmark(attacks, iterations=3)
    Runner->>Corpus: load AttackVectors
    loop for each attack × iteration
        Runner->>Guard: wrap agent (enable_armor=True)
        Runner->>Guard: process(attack.payload)
        Guard->>Armor: check_input(payload, session_id)
        alt blocked at input
            Armor-->>Guard: blocked=True
            Guard-->>Runner: RunResult(BLOCKED, trace)
        else passes input check
            Armor-->>Guard: blocked=False
            Guard->>Agent: process_request(payload)
            Agent-->>Guard: AgentResponse
            Guard->>Armor: check_output(response, session_id)
            alt blocked at output
                Armor-->>Guard: blocked=True
                Guard-->>Runner: RunResult(BLOCKED, trace)
            else passes output check
                Armor-->>Guard: blocked=False
                Guard-->>Runner: response
                Runner->>Judge: judge_outcome(attack, output, tool_calls)
                Judge-->>Runner: (AttackOutcome, reasoning)
                Runner-->>Runner: build RunResult
            end
        end
    end
    Runner-->>Dev: aggregate summary dict
```

---

## 5. Bare vs. armored comparison flow

```mermaid
sequenceDiagram
    autonumber
    participant Runner as ArmorEvalRunner
    participant Agent as Agent

    Runner->>Agent: run_single_attack(attack, enable_armor=False)
    Note over Runner,Agent: bare run — no Armor calls
    Agent-->>Runner: RunResult (bare)

    Runner->>Agent: run_single_attack(attack, enable_armor=True)
    Note over Runner,Agent: armored run — Armor wraps input + output
    Agent-->>Runner: RunResult (armored)

    Runner->>Runner: pair results → detection_rate, latency_overhead
```
