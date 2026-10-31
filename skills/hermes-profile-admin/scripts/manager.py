#!/usr/bin/env python3
"""Safe adapter for Hermes Profile lifecycle and context files."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable


PROFILE_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
CONTEXT_FILES = {
    "soul": Path("SOUL.md"),
    "user": Path("memories") / "USER.md",
    "agents": Path("AGENTS.md"),
}


class ManagerError(RuntimeError):
    """Expected user-facing manager error."""


def validate_profile_name(name: str) -> str:
    if not PROFILE_RE.fullmatch(name):
        raise ManagerError("profile must use lowercase letters, numbers, and hyphens")
    return name


def hermes_home(value: str | None) -> Path:
    return Path(value or os.environ.get("HERMES_HOME", "~/.hermes")).expanduser().resolve()


def profile_dir(home: Path, name: str) -> Path:
    validate_profile_name(name)
    target = (home / "profiles" / name).resolve()
    profiles_root = (home / "profiles").resolve()
    if target.parent != profiles_root:
        raise ManagerError("profile path escaped the Profiles directory")
    return target


def run_hermes(binary: str, args: list[str], dry_run: bool = False) -> dict[str, Any]:
    command = [binary, *args]
    result: dict[str, Any] = {"command": command, "dry_run": dry_run}
    if dry_run:
        result["status"] = "planned"
        return result
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise ManagerError(str(exc)) from exc
    result["returncode"] = completed.returncode
    result["stdout"] = completed.stdout.strip()
    result["stderr"] = completed.stderr.strip()
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip() or "Hermes CLI failed"
        raise ManagerError(f"{detail} (exit {completed.returncode})")
    result["status"] = "ok"
    return result


def context_paths(home: Path, name: str) -> dict[str, Path]:
    root = profile_dir(home, name)
    return {key: root / relative for key, relative in CONTEXT_FILES.items()}


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def update_context(args: argparse.Namespace) -> dict[str, Any]:
    home = hermes_home(args.hermes_home)
    paths = context_paths(home, args.profile)
    sources = {"soul": args.soul_file, "user": args.user_file, "agents": args.agents_file}
    selected = {key: Path(value).expanduser().resolve() for key, value in sources.items() if value}
    if not selected:
        raise ManagerError("context-update requires at least one context file")
    if args.dry_run:
        return {
            "status": "planned",
            "profile": args.profile,
            "writes": {key: str(paths[key]) for key in selected},
        }
    content = {}
    for key, source in selected.items():
        if not source.is_file():
            raise ManagerError(f"context source not found: {source}")
        content[key] = source.read_text(encoding="utf-8")
    for key, text in content.items():
        atomic_write(paths[key], text)
    return {
        "status": "updated",
        "profile": args.profile,
        "written": {key: str(paths[key]) for key in content},
    }


def validate_context(args: argparse.Namespace) -> dict[str, Any]:
    paths = context_paths(hermes_home(args.hermes_home), args.profile)
    present = {key: path.is_file() for key, path in paths.items()}
    root = profile_dir(hermes_home(args.hermes_home), args.profile)
    labels = {key: str(path.relative_to(root)) for key, path in paths.items()}
    return {
        "profile": args.profile,
        "valid": all(present.values()),
        "present": [labels[key] for key, ok in present.items() if ok],
        "missing": [labels[key] for key, ok in present.items() if not ok],
        "paths": {key: str(path) for key, path in paths.items()},
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Hermes Profiles and context files")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("list",):
        command = sub.add_parser(name, help="list Profiles")
        command.add_argument("--hermes-bin", default=os.environ.get("HERMES_BIN", "hermes"))
        command.add_argument("--dry-run", action="store_true")

    show = sub.add_parser("show", help="show one Profile")
    show.add_argument("profile")
    show.add_argument("--hermes-bin", default=os.environ.get("HERMES_BIN", "hermes"))
    show.add_argument("--dry-run", action="store_true")

    create = sub.add_parser("create", help="create a Profile without cloning another Profile")
    create.add_argument("profile")
    create.add_argument("--description")
    create.add_argument("--no-alias", action="store_true", default=True)
    create.add_argument("--hermes-bin", default=os.environ.get("HERMES_BIN", "hermes"))
    create.add_argument("--dry-run", action="store_true")

    update = sub.add_parser("update", help="update Profile configuration")
    update.add_argument("profile")
    update.add_argument("--description", help="replace the Profile description")
    update.add_argument("--rename", help="rename the Profile")
    alias = update.add_mutually_exclusive_group()
    alias.add_argument("--alias", help="create or replace the Profile wrapper alias")
    alias.add_argument("--remove-alias", action="store_true", help="remove the Profile wrapper alias")
    update.add_argument("--hermes-bin", default=os.environ.get("HERMES_BIN", "hermes"))
    update.add_argument("--dry-run", action="store_true")

    delete = sub.add_parser("delete", help="physically delete a Profile")
    delete.add_argument("profile")
    delete.add_argument("--confirm", action="store_true")
    delete.add_argument("--hermes-bin", default=os.environ.get("HERMES_BIN", "hermes"))
    delete.add_argument("--dry-run", action="store_true")

    for name in ("context-update", "validate"):
        command = sub.add_parser(name, help=f"{name} Profile context")
        command.add_argument("profile")
        command.add_argument("--hermes-home")
        command.add_argument("--dry-run", action="store_true")
        if name == "context-update":
            command.add_argument("--soul-file")
            command.add_argument("--user-file")
            command.add_argument("--agents-file")
    return parser


def execute(args: argparse.Namespace) -> Any:
    if args.command == "list":
        return run_hermes(args.hermes_bin, ["profile", "list"], args.dry_run)
    if args.command == "show":
        validate_profile_name(args.profile)
        return run_hermes(args.hermes_bin, ["profile", "show", args.profile], args.dry_run)
    if args.command == "create":
        validate_profile_name(args.profile)
        command = ["profile", "create", args.profile, "--no-alias"]
        if args.description:
            command.extend(["--description", args.description])
        return run_hermes(args.hermes_bin, command, args.dry_run)
    if args.command == "update":
        validate_profile_name(args.profile)
        if args.rename:
            validate_profile_name(args.rename)
        if not any((args.description is not None, args.rename, args.alias, args.remove_alias)):
            raise ManagerError("update requires --description, --rename, --alias, or --remove-alias")
        results = []
        target = args.profile
        if args.description is not None:
            results.append(run_hermes(
                args.hermes_bin,
                ["profile", "describe", target, "--text", args.description],
                args.dry_run,
            ))
        if args.rename:
            results.append(run_hermes(
                args.hermes_bin,
                ["profile", "rename", target, args.rename],
                args.dry_run,
            ))
            target = args.rename
        if args.alias:
            results.append(run_hermes(
                args.hermes_bin,
                ["profile", "alias", target, "--name", args.alias],
                args.dry_run,
            ))
        elif args.remove_alias:
            results.append(run_hermes(
                args.hermes_bin,
                ["profile", "alias", target, "--remove"],
                args.dry_run,
            ))
        return results
    if args.command == "delete":
        validate_profile_name(args.profile)
        if args.profile == "default":
            raise ManagerError("refusing to delete protected Profile: default")
        if not args.confirm:
            raise ManagerError("delete is physical; repeat with --confirm")
        return run_hermes(args.hermes_bin, ["profile", "delete", "-y", args.profile], args.dry_run)
    if args.command == "context-update":
        return update_context(args)
    if args.command == "validate":
        return validate_context(args)
    raise ManagerError(f"unsupported command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    try:
        result = execute(build_parser().parse_args(argv))
        print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))
        return 0
    except ManagerError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
