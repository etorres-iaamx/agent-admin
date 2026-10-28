---
name: openclaw-agent-admin
description: Administer persistent OpenClaw agents through the official CLI, including create, inspect, identity updates, bindings, and confirmed deletion. Use for roster lifecycle automation; do not use for editing agent workspace content or provider credentials.
metadata:
  short-description: Manage OpenClaw agent lifecycle
---

# OpenClaw agent administration

Use `scripts/manager.py` as the stable adapter for lifecycle operations. It
delegates to `openclaw agents`; it does not edit `openclaw.json`, SQLite, agent
directories, or workspaces directly.

## Operations

```bash
python scripts/manager.py list
python scripts/manager.py get <agent-id>
python scripts/manager.py create <agent-id> --workspace <path> --agent-dir <path> [--model <id>] [--bind <channel[:account]>]
python scripts/manager.py update <agent-id> [--name <name>] [--theme <theme>] [--emoji <emoji>] [--avatar <value>] [--bind <channel[:account]>] [--unbind <channel[:account]>]
python scripts/manager.py delete <agent-id> --confirm
```

Use `--dry-run` before a mutation when the requested values or target are
ambiguous. Use `--json` for machine-readable output (the adapter emits JSON by
default). Treat a non-zero exit code as failure and inspect the returned error.

`delete --confirm` is a physical deletion: the OpenClaw CLI prunes the agent's
workspace/state. Do not infer that it is a reversible or logical deactivation.
Do not use it for the `main` agent unless the user explicitly requests that
exact target.

The adapter can be pointed at a test or alternate executable with
`--openclaw-bin PATH` or `OPENCLAW_BIN`. Never put tokens, passwords, or API
keys in command arguments, skill files, logs, or generated profiles.

Creating an agent only creates its OpenClaw lifecycle entry. If the agent needs
`AGENTS.md`, `SOUL.md`, `USER.md`, or `IDENTITY.md`, create those separately in
the target workspace after verifying the selected paths and authorized
content.
