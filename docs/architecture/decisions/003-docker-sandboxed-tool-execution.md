# ADR 003 — Docker-sandboxed tool execution

**Date:** 2026-05-16
**Status:** Accepted

## Context

`ToolUseAgent` executes tools as part of responding to attack vectors. In a demo scenario — particularly one where we want to show a *successful* attack getting through — this is dangerous: a tool-abuse attack that succeeds could execute arbitrary code on the host.

Two concerns:
1. **Blast radius**: A successful tool-abuse attack in a demo should not be able to touch the host filesystem, network, or processes.
2. **Demo integrity**: We need to be able to *demonstrate* a successful attack safely — one that would normally cause real harm — without actually causing it. This is the whole point of the benchmark: show the damage Armor prevents.

The default tool executor is `simulated_execute_tool()`, which returns canned strings and never runs code. This is safe but not realistic — it cannot demonstrate a successful attack that actually does something.

## Decision

Add `SandboxedToolExecutor` (`src/backends/sandbox.py`) as an optional tool executor that runs tool code inside Docker containers with:
- `--network none` — no outbound network access from the container.
- `--read-only` — no writes to the container filesystem.
- `--rm` — container is removed immediately after execution.

Tool implementations are passed as a `dict[str, str]` mapping tool name to a Python snippet. The executor injects the call arguments as JSON into the script header so snippets can access them via an `args` variable.

`SandboxedToolExecutor` is activated via the `--sandbox` CLI flag. The default remains `simulated_execute_tool()` — Docker is not a hard dependency.

## Consequences

**Positive:**
- Successful tool-abuse attacks can be demonstrated without any real risk to the host.
- The demo case ("attack succeeds, here's what would have happened") is now visually concrete.
- Blast radius for any escape is bounded to what Docker's isolation provides.

**Negative:**
- Requires Docker running locally; adds an optional runtime dependency.
- The `python:3.12-slim` image must be pulled before first use (~50 MB).
- Snippets run with Python stdlib only — tool implementations that need third-party packages require a custom image (not supported yet).

## Alternatives considered

- **subprocess with restricted env:** Easier but no filesystem isolation and harder to constrain network access portably.
- **Always use Docker (no simulated fallback):** Rejected — Docker is not available in all CI environments and is heavyweight for simple offline testing.
