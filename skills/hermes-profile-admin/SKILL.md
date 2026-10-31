---
name: hermes-profile-admin
description: "Administer Hermes Profiles and their context files."
version: 0.1.0
author: Emilio David Torres Ramos (etorres-iaamx), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Hermes, Profiles, lifecycle, context, isolation]
    related_skills: []
---

# Hermes Profile administration

Use `skills/hermes-profile-admin/scripts/manager.py` to administer real Hermes Profiles and
their context files. The adapter delegates lifecycle changes to the official
`hermes profile` CLI and writes only the named Profile's `SOUL.md`,
`memories/USER.md`, and `AGENTS.md` files.

## When to Use

- Create, list, inspect, validate, update, or delete a Hermes Profile.
- Prepare isolated client context for a Profile.
- Verify that a Profile has all required context files.

Do not use this skill to modify `default` unless the user explicitly authorizes
that exact target. Do not use it to copy credentials, channels, sessions, or
memory between Profiles.

## Prerequisites

- Hermes is installed and the selected `hermes` executable is available.
- The operator has authorized the target Profile and context content.
- Context source files contain no secrets unless the user explicitly authorized
  their local use.

The Profile root is resolved from `HERMES_HOME` or `~/.hermes`. Override the
CLI with `--hermes-bin` and the root with `--hermes-home` when testing.

## Quick Reference

```bash
python3 skills/hermes-profile-admin/scripts/manager.py list
python3 skills/hermes-profile-admin/scripts/manager.py show cliente-001
python3 skills/hermes-profile-admin/scripts/manager.py create cliente-001 --description "Atencion Comercial"
python3 skills/hermes-profile-admin/scripts/manager.py update cliente-001 \
  --description "Atencion Comercial y soporte" \
  --alias soporte
python3 skills/hermes-profile-admin/scripts/manager.py update cliente-001 \
  --rename cliente-soporte
python3 skills/hermes-profile-admin/scripts/manager.py validate cliente-001
python3 skills/hermes-profile-admin/scripts/manager.py context-update cliente-001 \
  --soul-file ./SOUL.md \
  --user-file ./USER.md \
  --agents-file ./AGENTS.md
python3 skills/hermes-profile-admin/scripts/manager.py delete cliente-001 --confirm
```

Use `--dry-run` before mutations when reviewing the target or command. The
adapter returns JSON with `ok` and `result` or `error`.

## Procedure

1. Confirm the exact Profile name. Completion criterion: it matches the
   authorized target and is not `default` for a client operation.
2. Run `list` or `show` before a mutation. Completion criterion: the target's
   current state is recorded.
3. Use `create` without cloning another Profile. Completion criterion: the
   official CLI reports successful creation.
4. Use `update` for Profile configuration such as description, rename, or
   wrapper alias. Completion criterion: each requested official CLI operation
   reports success.
5. Use `context-update` with explicit source files. Completion criterion: every
   requested file exists only under the target Profile directory.
6. Run `validate`. Completion criterion: `valid` is `true` and all three files
   are present when the Profile is intended to be complete.
7. For deletion, require `--confirm` and never target `default`. Completion
   criterion: Hermes reports successful deletion and a subsequent `list` no
   longer shows the named Profile.

## Context boundaries

- `SOUL.md` defines identity and response style.
- `memories/USER.md` defines the client and fictitious contact context.
- `AGENTS.md` defines operational limits and rejected cross-client requests.
- The adapter never copies a source Profile's files automatically.
- `update --description` delegates to `hermes profile describe --text`.
- `update --rename` delegates to `hermes profile rename`.
- `update --alias` and `--remove-alias` delegate to `hermes profile alias`.
- `context-update` uses atomic per-file replacement only at the resolved target
  paths; it does not edit Hermes databases or provider credentials.

## Pitfalls

- Hermes uses one host Gateway for multiplexed Profiles; creating a Profile does
  not require starting a separate Gateway.
- `API_SERVER_PORT` is not a per-Profile listener in the multiplexed setup;
  validate API routes separately from Profile lifecycle operations.
- `delete --confirm` is physical deletion. It is not a reversible disable.
- A successful file write does not prove isolation; run a cross-Profile test.
- Never place API keys, passwords, OAuth tokens, or real customer data in
  committed source files, command arguments, or logs.

## Verification

```bash
python3 -m unittest discover -s tests -p 'test_hermes_profiles.py' -v
python3 -m unittest discover -s skills/openclaw-agent-admin/tests -v
```

For a live operation, verify the exact Profile with `show`, run `validate`, and
check the resulting files under that Profile's resolved home.
