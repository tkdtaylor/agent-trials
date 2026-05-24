# Configuration

**Project:** Agent Trials
**Last updated:** 2026-05-23

Every knob the system exposes — env vars, config files, runtime parameters.

---

## Environment variables

| Variable | Type | Default | Required | Effect |
|----------|------|---------|----------|--------|
| `ARMOR_SOCKET` | string | `/var/run/armor.sock` | No | Unix socket path for the Armor daemon (overridable per-run via `--armor-socket`) |

**Hook profile env vars** (consumed by `.claude/scripts/`, not the application):
- `CLAUDE_HOOK_PROFILE` — `minimal` / `standard` / `strict` (default `standard`)
- `CLAUDE_DISABLED_HOOKS` — comma-separated list of hook names to disable

---

## Runtime flags

See `interfaces.md` CLI section for flags passed to benchmark runs. Key runtime parameters:

| Parameter | Where set | Default | Effect |
|-----------|-----------|---------|--------|
| `enable_armor` | `run_single_attack(attack, enable_armor=True)` | `True` | Toggle Armor for a single run |
| `iterations` | `run_benchmark(attacks, iterations=1)` or `--iterations` CLI flag | `5` | Number of benchmark repetitions |
| `group_size` | `--group-size` CLI flag | `8` | Number of attacks per group (for checkpoint-based resumption) |
| `--db` | CLI flag | `runs.db` | SQLite telemetry file path; written by `RunRecorder` in `src/telemetry.py` |

---

## Secrets

The application does not require any cloud API keys. Armor is reached over a local Unix socket (no key), and agent LLM calls route through `BackendProtocol` to a locally-running Ollama or llama-cpp process (also keyless).

**Rule:** Secrets are never pasted into chat, never logged, and never written into the repo. The `protect-secrets` hook blocks writes to common credential filenames, and the `make fitness-no-secrets` check fails the build on `sk-`, `ARMOR_API_KEY=`, or `ANTHROPIC_API_KEY=` literals appearing in `src/` or `tests/`.

---

## Defaults policy

Defaults are safe — Armor is disabled by default when `armor_client=None`, and no destructive or exfiltration-capable behavior is enabled unless explicitly constructed. Agent instantiation never reads secrets from disk; the framework has no concept of a cloud API credential.
