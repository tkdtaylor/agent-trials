# Architecture — C4 Element Catalog

**Project:** Armor Eval
**Last updated:** 2026-05-16

The structured catalog of architectural elements that the diagrams in [`../architecture/diagrams.md`](../architecture/diagrams.md) render.

---

## 1. Persons (actors)

| Name | Description | Goals |
|------|-------------|-------|
| Developer / Security Engineer | Runs benchmarks against agents before deploying them | Validate agent safety, measure Armor's detection coverage, identify attack categories that slip through |

---

## 2. Systems

| Name | Type | Description | Owner |
|------|------|-------------|-------|
| Armor Eval | In-scope | Adversarial benchmarking framework for AI agents | This team |
| Armor SDK | External | Security layer that checks agent inputs/outputs for threats | Armor team |
| Anthropic API | External | Claude model access for agent implementations | Anthropic |

---

## 3. Containers

| Name | Technology | Responsibility | Source path | Depends on |
|------|------------|----------------|-------------|------------|
| Eval Runner | Python process | Executes attack vectors against agents, coordinates Armor toggle, aggregates results | `src/runner.py` | Agent archetypes, Armor SDK, Judge |
| Agent Archetypes | Python modules | Concrete implementations of RAG, tool-use, and multi-turn agents | `src/agents/` | Anthropic API (optional), external tools |
| Judge | Python module | Determines `AttackOutcome` from agent output and tool call trace | `src/judge.py` | — |
| ArmorGuard Wrapper | Python class | Inline Armor toggle — wraps any `AgentProtocol` implementor | `src/agent_wrapper.py` | Armor SDK |
| Attack Corpus | YAML file | Curated attack vectors across four threat classes | `attacks/corpus.yaml` | — |
| Dashboard | Streamlit app | Read-only results viewer with side-by-side bare vs. armored comparison | `dashboard/app.py` | Eval Runner output |

---

## 4. Components

| Container | Component | Source path | Responsibility | Depends on |
|-----------|-----------|-------------|----------------|------------|
| Eval Runner | ArmorEvalRunner | `src/runner.py` | Runs single attacks and full benchmark suites | AgentProtocol, ArmorClient, Judge |
| Eval Runner | Types | `src/types.py` | Shared dataclasses: AttackVector, AgentTrace, RunResult, AttackOutcome | — |
| Agent Archetypes | AgentProtocol | `src/agent_wrapper.py` | Protocol interface all agents must satisfy | — |
| Agent Archetypes | RAGAgent | `src/agents/rag_agent.py` | Retrieval-augmented Q&A agent | Anthropic API, retrieval store |
| Agent Archetypes | ToolUseAgent | `src/agents/tool_use_agent.py` | API/browser tool-use agent | External tools/APIs |
| Agent Archetypes | MultiTurnAgent | `src/agents/multi_turn_agent.py` | Multi-turn conversational agent with session memory | Anthropic API |
| ArmorGuard Wrapper | ArmorGuard | `src/agent_wrapper.py` | Wraps any AgentProtocol; raises SecurityBlockedException on block | ArmorClient |

---

## 5. Cross-cutting decisions

- **AgentProtocol** — all agent implementations must satisfy `AgentProtocol` (see `interfaces.md`). The runner and ArmorGuard never depend on concrete agent classes.
- **Armor is always optional** — the `armor_client` parameter is None by default. Every code path that touches Armor is gated on `if self.armor_client`.
- **Judgment is isolated** — `judge.py` has no imports from `runner.py` or `agent_wrapper.py`. The runner passes data to the judge; the judge never reaches back.
- **Results are pure return values** — no database, no side-effectful writes in the hot path. Persistence is the caller's responsibility.
