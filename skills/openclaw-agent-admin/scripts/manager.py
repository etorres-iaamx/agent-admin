#!/usr/bin/env python3
"""Safe, JSON-oriented adapter around ``openclaw agents``.

The adapter intentionally delegates state changes to the official CLI instead
of modifying OpenClaw's configuration or databases itself.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from typing import Any, Sequence


class ManagerError(RuntimeError):
    """An expected adapter or OpenClaw CLI failure."""


def run_openclaw(binary: str, args: Sequence[str], dry_run: bool = False) -> dict[str, Any]:
    command = [binary, "agents", *args]
    result: dict[str, Any] = {"command": shlex.join(command), "dry_run": dry_run}
    if dry_run:
        result["status"] = "planned"
        return result

    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    result["returncode"] = completed.returncode
    if completed.stdout.strip():
        result["stdout"] = completed.stdout.strip()
        try:
            result["data"] = json.loads(completed.stdout)
        except json.JSONDecodeError:
            pass
    if completed.stderr.strip():
        result["stderr"] = completed.stderr.strip()
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip() or "OpenClaw CLI failed"
        raise ManagerError(f"{detail} (exit {completed.returncode})")
    result["status"] = "ok"
    return result


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--openclaw-bin", default=os.environ.get("OPENCLAW_BIN", "openclaw"), help=argparse.SUPPRESS)
    parser.add_argument("--dry-run", action="store_true", help="Show the command without executing it")
    parser.add_argument("--json", action="store_true", help="Retained for compatibility; output is JSON by default")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)

    for name in ("list",):
        command = sub.add_parser(name, help="List configured agents")
        add_common(command)
        command.add_argument("--bindings", action="store_true")
        command.add_argument("--tree", action="store_true")

    command = sub.add_parser("get", help="Get one configured agent")
    add_common(command)
    command.add_argument("agent_id")

    command = sub.add_parser("create", help="Add an isolated agent")
    add_common(command)
    command.add_argument("agent_id")
    command.add_argument("--workspace", required=True)
    command.add_argument("--agent-dir")
    command.add_argument("--model")
    command.add_argument("--bind", action="append", default=[])

    command = sub.add_parser("update", help="Update identity and/or bindings")
    add_common(command)
    command.add_argument("agent_id")
    command.add_argument("--name")
    command.add_argument("--theme")
    command.add_argument("--emoji")
    command.add_argument("--avatar")
    command.add_argument("--bind", action="append", default=[])
    command.add_argument("--unbind", action="append", default=[])

    command = sub.add_parser("delete", help="Delete an agent")
    add_common(command)
    command.add_argument("agent_id")
    command.add_argument("--confirm", action="store_true", help="Required confirmation for physical deletion")
    return parser


def execute(args: argparse.Namespace) -> list[dict[str, Any]]:
    binary = args.openclaw_bin
    if args.operation == "list":
        cli_args = ["list", "--json"]
        if args.bindings:
            cli_args.append("--bindings")
        if args.tree:
            cli_args.append("--tree")
        return [run_openclaw(binary, cli_args, args.dry_run)]

    if args.operation == "get":
        listed = run_openclaw(binary, ["list", "--json", "--bindings"], args.dry_run)
        if args.dry_run:
            listed["select"] = args.agent_id
            return [listed]
        data = listed.get("data")
        if data is None:
            raise ManagerError("openclaw agents list did not return JSON")
        agents = data if isinstance(data, list) else data.get("agents", [])
        matches = [agent for agent in agents if agent.get("id") == args.agent_id]
        if not matches:
            raise ManagerError(f"agent not found: {args.agent_id}")
        return [{"status": "ok", "agent": matches[0]}]

    if args.operation == "create":
        cli_args = ["add", args.agent_id, "--workspace", args.workspace, "--non-interactive", "--json"]
        for option, value in (("--agent-dir", args.agent_dir), ("--model", args.model)):
            if value:
                cli_args.extend([option, value])
        for binding in args.bind:
            cli_args.extend(["--bind", binding])
        return [run_openclaw(binary, cli_args, args.dry_run)]

    if args.operation == "update":
        results: list[dict[str, Any]] = []
        identity = [("--name", args.name), ("--theme", args.theme), ("--emoji", args.emoji), ("--avatar", args.avatar)]
        identity_args = ["set-identity", "--agent", args.agent_id, "--json"]
        has_identity_change = False
        for option, value in identity:
            if value is not None:
                has_identity_change = True
                identity_args.extend([option, value])
        if has_identity_change:
            results.append(run_openclaw(binary, identity_args, args.dry_run))
        for binding in args.bind:
            results.append(run_openclaw(binary, ["bind", "--agent", args.agent_id, "--bind", binding, "--json"], args.dry_run))
        for binding in args.unbind:
            results.append(run_openclaw(binary, ["unbind", "--agent", args.agent_id, "--bind", binding, "--json"], args.dry_run))
        if not results:
            raise ManagerError("update requires at least one identity, --bind, or --unbind value")
        return results

    if args.operation == "delete":
        if not args.confirm:
            raise ManagerError("delete is physical; repeat with --confirm")
        return [run_openclaw(binary, ["delete", args.agent_id, "--force", "--json"], args.dry_run)]

    raise ManagerError(f"unsupported operation: {args.operation}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        results = execute(parser.parse_args(argv))
        print(json.dumps({"ok": True, "results": results}, ensure_ascii=False))
        return 0
    except ManagerError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except OSError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 127


if __name__ == "__main__":
    raise SystemExit(main())
