# Agent Trials — Claude Code layer

The canonical, harness-neutral briefing for this repo is **`AGENTS.md`**. It carries
project orientation, structure, commands, design principles, conventions, the task
workflow, commit rules, boundaries, and the load-bearing process rules. Read it first.

@AGENTS.md

Everything below is the **Claude Code-specific layer** — mechanics only Claude Code
understands. The shared rules live in `AGENTS.md` (imported above) and must not be
duplicated here.

## Subagents

The role prompts in `.claude/agents/` are first-class Claude Code subagents. Dispatch
them with the Task tool:

- **task-executor** — implement a single task end to end (runs `scripts/start-task.sh`
  as Step 0, writes code, commits at 🟡 on the task branch, reports back).
- **spec-verifier** — assertion-by-assertion gate; returns APPROVE or BLOCK. Run on
  every task before promoting to ✅.
- **code-reviewer** — review the diff before merge (`/code-review`).
- **architect** — design review and drift audit between code, diagrams, and the spec.
- **security-auditor** — security pass over the attack surface and Armor integration.

```
use task-executor — task: docs/tasks/backlog/NNN-name.md, spec: docs/tasks/test-specs/NNN-name-test-spec.md
```

Each agent call is ephemeral — it reads the task file, does the work, commits, and
reports back without bloating the main conversation.

When dispatching parallel agents in one message, set `isolation: "worktree"` and run
`scripts/verify-worktree-isolation.sh <agent-id> [<agent-id> ...]` after they complete
to confirm none bypassed the worktree flag.

## Hook profiles

Hooks run automatically and are gated by profile level. Control via environment
variables:

```bash
export CLAUDE_HOOK_PROFILE=minimal    # Safety hooks only (secret protection, block-no-verify, config-protection, protect-checkout)
export CLAUDE_HOOK_PROFILE=standard   # + workflow hooks (plan restructuring, compaction, checkpoints) — default
export CLAUDE_HOOK_PROFILE=strict     # + formatting, notifications (batch-format-typecheck, desktop-notify)
export CLAUDE_DISABLED_HOOKS=desktop-notify,batch-format-typecheck  # Disable specific hooks
```

Already wired via `.claude/settings.json` (standard profile): `no-commit-on-main`,
`protect-secrets`, `block-no-verify`, plan→tasks restructuring, compaction guards,
spec-coverage-check.

## Plan mode

When you exit plan mode, a hook automatically restructures the plan:
- Each step becomes a task file in `docs/tasks/backlog/`
- Test spec stubs are created for each task
- The plan is replaced with a lightweight skeleton to save context tokens
- The full plan is backed up to `docs/plans/`

### End handoffs with a resume command

When a response completes a logical milestone that leaves follow-on work, end the
response with a **fenced code block** containing the exact resume command — not inline
backticks, not prose. A fenced code block is what renders the copy button in the
VSCode chat UI.

**Verify the path exists before writing the resume block.** Glob
`docs/tasks/backlog/NNN-*.md` (and the matching
`docs/tasks/test-specs/NNN-*-test-spec.md`) and copy the real filenames into the block.
Do NOT infer filenames — the plan-mode hook may rename task files as it writes them
out. If there is genuinely nothing to resume, skip the block.

## Retro injection (inject-retros)

The `inject-retros.py` SessionStart hook parses the retro log
(`docs/agent-rules.md`) plus this file at session start and surfaces the entries that
match the active task's spec. Adding an entry to `docs/agent-rules.md` is how a
one-time mistake becomes a permanent guard. The *essentials* of those rules are inlined
into `AGENTS.md` so every harness gets them even without the hook.

## Recommended skills

- **code-scanner** — scan before installing new packages or before shipping. Trigger:
  "scan this for vulnerabilities" or "is this safe to install?"
- **simplify** — review changed code after heavy implementation sprints. Trigger:
  "simplify this module"
- **claude-api** — if a new backend wraps the Anthropic SDK behind `BackendProtocol`.
  Trigger: code imports `anthropic`
- **security-review** — full security review of the attack surface and Armor
  integration before any public demo. Trigger: "security review"

### Note on MCP

Not needed — `gh` covers repo ops, WebSearch/WebFetch cover research, and the provider
CLIs are driven as subprocesses.
