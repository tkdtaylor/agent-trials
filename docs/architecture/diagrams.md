# Architecture Diagrams

**Project:** Agent Trials
**Last updated:** 2026-05-18 (updated for per-agent routing, canary seeding, and Armor v0.10.2)

C4-structured Mermaid diagrams. See [overview.md](overview.md) for prose context and [`../spec/architecture.md`](../spec/architecture.md) for the structured element catalog these diagrams render.

---

## 1. System Context

```mermaid
C4Context
    title System Context for Agent Trials

    Person(dev, "Developer / Security Engineer", "Runs adversarial benchmarks before deploying agents")
    System(agent_trials, "Agent Trials", "Adversarial trial framework for AI agents")
    System_Ext(armor_sdk, "Armor SDK", "Input/output threat detection")
    System_Ext(ollama, "Ollama", "Local LLM inference server")
    System_Ext(docker, "Docker", "Container runtime for sandboxed tool execution")

    Rel(dev, agent_trials, "Runs benchmarks, views dashboard")
    Rel(agent_trials, armor_sdk, "Checks inputs/outputs", "SDK calls")
    Rel(agent_trials, ollama, "LLM chat completions", "HTTP")
    Rel(agent_trials, docker, "Sandboxed tool runs", "docker run")
```

---

## 2. Containers

```mermaid
C4Container
    title Container view of Agent Trials

    Person(dev, "Developer")

    System_Boundary(boundary, "Agent Trials") {
        Container(runner, "Eval Runner", "Python", "Drives attack runs, coordinates Armor toggle, aggregates results")
        Container(agents, "Agent Archetypes", "Python", "Echo, RAG, tool-use, multi-turn — implement AgentProtocol")
        Container(backends, "Backend Layer", "Python", "BackendProtocol + Ollama/LlamaCpp adapters; converts LLMs into agent callables")
        Container(sandbox, "SandboxedToolExecutor", "Python + Docker", "Executes tool snippets in Docker (--network none, --read-only)")
        Container(guard, "ArmorGuard", "Python", "Inline Armor wrapper — checks input/output per run")
        Container(judge, "Judge", "Python", "Determines AttackOutcome from agent output and tool calls")
        Container(corpus, "Attack Corpus", "YAML", "Curated attack vectors across four threat classes")
        Container(dashboard, "Dashboard", "Streamlit", "Read-only results viewer")
    }

    System_Ext(armor_sdk, "Armor SDK")
    System_Ext(ollama, "Ollama")
    System_Ext(docker_rt, "Docker")

    Rel(dev, runner, "Invokes")
    Rel(dev, dashboard, "Views results")
    Rel(runner, corpus, "Loads attacks")
    Rel(runner, agents, "Instantiates via factory")
    Rel(runner, guard, "Wraps agent for armored runs")
    Rel(runner, judge, "Passes output for verdict")
    Rel(guard, armor_sdk, "check_input / check_output")
    Rel(agents, backends, "Receives callables from adapter layer")
    Rel(backends, ollama, "chat completions (OllamaBackend)")
    Rel(agents, sandbox, "Tool execution (--sandbox mode)")
    Rel(sandbox, docker_rt, "docker run")
```

---

## 3. Components — Eval Harness

```mermaid
C4Component
    title Component view of the Eval Harness

    Container_Boundary(harness, "Eval Harness") {
        Component(runner_cls, "ArmorEvalRunner", "src/runner.py", "run_single_attack, run_benchmark, _aggregate_results")
        Component(types, "Types", "src/types.py", "AttackVector, AgentTrace, RunResult, AttackOutcome, AgentResponse")
        Component(guard_cls, "ArmorGuard + AgentProtocol", "src/agent_wrapper.py", "Inline Armor toggle; Protocol all agents satisfy")
        Component(judge_fn, "judge_outcome()", "src/judge.py", "Determines outcome from output + tool calls")
    }

    Container_Boundary(backend_boundary, "Backend Layer") {
        Component(protocol, "BackendProtocol", "src/backends/protocol.py", "chat(messages) -> str")
        Component(adapters, "Adapters", "src/backends/adapters.py", "Factory functions: rag_generate, tool_use_decide, multi_turn_generate, etc.")
        Component(ollama_b, "OllamaBackend", "src/backends/ollama.py", "Wraps ollama.Client")
        Component(llama_b, "LlamaCppBackend", "src/backends/llamacpp.py", "Wraps llama_cpp.Llama")
        Component(sandbox_c, "SandboxedToolExecutor", "src/backends/sandbox.py", "docker run --rm --network none --read-only")
    }

    Container(agents_c, "Agent Archetypes", "src/agents/")
    System_Ext(armor_sdk_c, "Armor SDK")

    Rel(runner_cls, types, "Uses")
    Rel(runner_cls, guard_cls, "Wraps agent")
    Rel(runner_cls, judge_fn, "Calls for verdict")
    Rel(guard_cls, armor_sdk_c, "check_input / check_output")
    Rel(runner_cls, agents_c, "Instantiates via factory")
    Rel(adapters, protocol, "Accepts")
    Rel(adapters, agents_c, "Provides callables to")
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
    participant Canary as armor canary seed (CLI)
    participant Daemon as Armor daemon (Unix socket)
    participant Runner as ArmorEvalRunner
    participant Corpus as corpus.yaml
    participant Guard as ArmorGuard
    participant Client as ArmorClient (in-process)
    participant Agent as Agent (RAG/Tool/MT)
    participant Judge as judge.py

    Note over Dev,Daemon: Setup — before benchmark
    Dev->>Canary: armor canary seed
    Canary-->>Dev: canary values (honeypot tokens)
    Dev->>Daemon: start with --canary-values <tokens>
    Daemon-->>Dev: listening on Unix socket

    Dev->>Runner: run_benchmark(attacks, iterations=3)
    Runner->>Client: construct ArmorClient
    Client->>Daemon: connect (Unix socket)
    Runner->>Corpus: load AttackVectors
    loop for each attack × iteration
        Runner->>Guard: wrap agent (enable_armor=True)
        Runner->>Guard: process(attack.payload)
        Guard->>Client: check_input(payload, session_id)
        Client->>Daemon: check_input over socket
        alt blocked at input
            Daemon-->>Client: blocked=True
            Client-->>Guard: blocked=True
            Guard-->>Runner: RunResult(BLOCKED, trace)
        else passes input check
            Daemon-->>Client: blocked=False
            Client-->>Guard: blocked=False
            Guard->>Agent: process_request(payload)
            Agent-->>Guard: AgentResponse
            Guard->>Client: check_output(response, session_id)
            Client->>Daemon: check_output over socket
            alt blocked at output
                Daemon-->>Client: blocked=True
                Client-->>Guard: blocked=True
                Guard-->>Runner: RunResult(BLOCKED, trace)
            else passes output check
                Daemon-->>Client: blocked=False
                Client-->>Guard: blocked=False
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
