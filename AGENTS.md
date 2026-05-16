# Codex Project Instructions

`CLAUDE.md` is the canonical agent guide for this repository. Read it first and
follow it unless a higher-priority Codex/system instruction conflicts.

## Startup

- Read `CLAUDE.md`, then `docs/architecture/agent-rules.md`.
- For implementation tasks, read the task file, its paired test spec under
  `docs/tasks/test-specs/`, and `docs/architecture/overview.md` before editing.
- Treat `docs/spec/` as the current source of truth. When behavior, data model,
  interfaces, configuration, component boundaries, or runtime flow change, update
  the matching spec or diagram in the same change.

## Reusing Claude Hooks

Codex does not automatically run `.claude/settings.json` hooks, so reuse the same
scripts manually when they apply. Set `CLAUDE_PROJECT_DIR=$PWD` when invoking
them from this repo.

Before writing or editing a file, the Claude safety hooks are:

```bash
printf '%s' '{"tool_input":{"file_path":"<path>"}}' | CLAUDE_PROJECT_DIR=$PWD python3 .claude/scripts/protect-secrets.py
printf '%s' '{"tool_input":{"file_path":"<path>"}}' | CLAUDE_PROJECT_DIR=$PWD python3 .claude/scripts/config-protection.py
```

Before running risky Bash/git commands, check the command through the Bash hooks:

```bash
printf '%s' '{"tool_name":"Bash","tool_input":{"command":"<command>"}}' | CLAUDE_PROJECT_DIR=$PWD python3 .claude/scripts/block-no-verify.py
printf '%s' '{"tool_name":"Bash","tool_input":{"command":"<command>"}}' | CLAUDE_PROJECT_DIR=$PWD python3 .claude/scripts/protect-checkout.py
printf '%s' '{"tool_name":"Bash","tool_input":{"command":"<command>"}}' | CLAUDE_PROJECT_DIR=$PWD python3 .claude/scripts/spec-coverage-check.py
```

Use the hook profile controls from `CLAUDE.md`:

```bash
export CLAUDE_HOOK_PROFILE=minimal
export CLAUDE_DISABLED_HOOKS=desktop-notify,batch-format-typecheck
```

## Work Rules

- Follow the "Always", "Ask first", and "Never" boundaries in `CLAUDE.md`.
- Do not create implementation files under `src/` without a task and test spec.
- Write or complete the test spec before implementation.
- Keep tasks small and composable; avoid unrelated refactors.
- Use `git mv` for task state moves and verify with `scripts/check-task-state.sh`.
- Do not use `git checkout -- <path>` over a dirty worktree. Use `git diff`,
  `git show`, `git stash`, or an isolated worktree instead.
- Do not bypass hooks with `--no-verify` or weaken lint/format configuration to
  make checks pass.

## Verification

For ordinary code changes, run:

```bash
make check
make fitness
scripts/check-task-state.sh
```

For task completion, also verify every `TC-*` marker in the paired test spec is
referenced by a real assertion in tests, then move the task to
`docs/tasks/completed/`, update `coverage-tracker.md`, and follow the milestone
commit/push rule in `CLAUDE.md`.

## Claude Agent Specs

The files in `.claude/agents/` are reusable role guides. When using Codex
sub-agents, adapt those instructions to the available Codex tools and keep the
same scope discipline. If multiple code-modifying agents run in parallel, use
isolated worktrees where available and then run:

```bash
scripts/verify-worktree-isolation.sh <agent-id> [<agent-id> ...]
```
