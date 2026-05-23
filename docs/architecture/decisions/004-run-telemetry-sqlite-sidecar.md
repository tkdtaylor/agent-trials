# ADR 004 — Run telemetry as a CLI-layer SQLite sidecar

**Status:** Accepted
**Date:** 2026-05-23

## Context

After the initial benchmark runs it became useful to persist per-run metadata (model, corpus hash, Armor version, wall-clock time, VRAM usage) and per-attack outcomes for later analysis — without querying `results.json` ad-hoc. The question was where to place this persistence.

Two options were considered:

1. **Inside `ArmorEvalRunner`** — wire `RunRecorder` into `run_benchmark()` so every call automatically records to SQLite.
2. **In the CLI layer (`src/__main__.py`)** — the CLI calls `run_benchmark()`, receives the results dict, and then records it.

## Decision

Telemetry is a CLI-layer concern. `RunRecorder` is instantiated and called in `src/__main__.py`, never inside `ArmorEvalRunner`.

## Consequences

- `ArmorEvalRunner` remains a pure in-process library with no side-effectful writes. Callers that use the Python API directly (e.g. tests, notebooks, custom scripts) get no implicit SQLite writes.
- The `--db` flag is a CLI flag, not a constructor parameter on `ArmorEvalRunner`. Changing the telemetry store (e.g. switching to a different database) requires only CLI-layer changes.
- The layering fitness function F-002 (runner must not import from concrete agent modules) is unaffected; telemetry is not in the runner at all.
- VRAM sampling (`GET /api/ps`) is best-effort and happens after `run_benchmark()` returns. It is not available when using the Python API directly.
