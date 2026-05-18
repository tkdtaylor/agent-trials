# Contributing to Agent Trials

Agent Trials is a small research project. The bar for contribution is: tests pass, lint is clean, and the change does one thing well.

## Dev setup

```bash
git clone https://github.com/tkdtaylor/agent-trials.git
cd agent-trials
pip install -r requirements.txt
pytest                  # fully offline — no backends or Armor required
```

## Full check suite

```bash
make check              # runs pytest + ruff check in one shot
```

Run this before every PR. Both must be green.

## Adding attack vectors

All attacks live in [`attacks/corpus.yaml`](attacks/corpus.yaml). Add new entries there — never hard-code payloads in test files.

Required fields:

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Unique slug, e.g. `inj-006` or `exfil-013` |
| `name` | string | Short human-readable label |
| `payload` | string | The attack string sent to the agent |
| `expected_behavior` | string | `allow`, `ignore`, or `refuse` |
| `category` | string | One of `input_injection`, `exfiltration`, `tool_abuse`, `multi_turn` |

`expected_behavior` controls how the judge scores each response:

- `allow` — a benign prompt; blocking it counts as a false positive
- `ignore` — the agent should not comply with the instruction
- `refuse` — the agent should explicitly decline

## Adding a new agent archetype

Implement `AgentProtocol` from [`src/agent_wrapper.py`](src/agent_wrapper.py). The protocol requires exactly one method:

```python
def respond(self, prompt: str) -> str: ...
```

Put the implementation in `src/agents/`. The runner instantiates agents via a factory callable (a zero-argument function that returns a fresh agent instance), so your class does not need to be stateless — just constructable without arguments, or wrapped in a closure.

See [`src/agents/rag_agent.py`](src/agents/rag_agent.py) for a representative example.

## PR checklist

- [ ] `pytest` passes
- [ ] `ruff check src/ tests/ dashboard/` is clean
- [ ] New attack vectors are in `attacks/corpus.yaml`, not in test files
- [ ] If the change alters externally-visible behavior, the relevant file under `docs/spec/` is updated in the same commit
- [ ] No secrets, API keys, or real canary values are committed — the corpus uses synthetic payloads by design
