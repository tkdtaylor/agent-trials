# Configuration

**Project:** Armor Eval
**Last updated:** 2026-05-16

Every knob the system exposes — env vars, config files, runtime parameters.

---

## Environment variables

| Variable | Type | Default | Required | Effect |
|----------|------|---------|----------|--------|
| `ARMOR_API_KEY` | string | — | Only if using Armor | API key for the Armor SDK |
| `ANTHROPIC_API_KEY` | string | — | Only for RAG/multi-turn agents | API key for Claude model access |
| `ARMOR_DAEMON_SOCKET` | string | `/var/run/armor.sock` | No | Unix socket path for Armor daemon |

**Hook profile env vars** (consumed by `.claude/scripts/`, not the application):
- `CLAUDE_HOOK_PROFILE` — `minimal` / `standard` / `strict` (default `standard`)
- `CLAUDE_DISABLED_HOOKS` — comma-separated list of hook names to disable

---

## Runtime flags

See `interfaces.md` CLI section for flags passed to benchmark runs. Key runtime parameters:

| Parameter | Where set | Default | Effect |
|-----------|-----------|---------|--------|
| `enable_armor` | `run_single_attack(attack, enable_armor=True)` | `True` | Toggle Armor for a single run |
| `iterations` | `run_benchmark(attacks, iterations=1)` | `1` | Number of benchmark repetitions |

---

## Secrets

| Secret | Source | Used for |
|--------|--------|----------|
| `ARMOR_API_KEY` | `.env` or shell env | Armor SDK authentication |
| `ANTHROPIC_API_KEY` | `.env` or shell env | Claude API calls in agent implementations |

**Rule:** Secrets are never pasted into chat, never logged, and never written into the repo. The `protect-secrets` hook blocks writes to common credential filenames.

---

## Defaults policy

Defaults are safe — Armor is disabled by default when `armor_client=None`, and no destructive or exfiltration-capable behavior is enabled unless explicitly constructed. Agent instantiation never reads secrets from disk; callers pass them in via constructor arguments.
