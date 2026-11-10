from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class CommandResult:
    """Successful OpenClaw command output."""

    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class OpenClawCommandError(RuntimeError):
    """Safe typed failure from the OpenClaw executable."""

    def __init__(
        self,
        code: str,
        *,
        returncode: int | None = None,
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        super().__init__(code)
        self.code = code
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class OpenClawClient:
    """Run OpenClaw with an argv boundary and a bounded execution time."""

    def __init__(self, binary: str = "openclaw", timeout_seconds: float = 30.0) -> None:
        if not binary.strip():
            raise ValueError("OpenClaw binary must not be empty")
        if timeout_seconds <= 0:
            raise ValueError("OpenClaw timeout must be positive")
        self.binary = binary
        self.timeout_seconds = timeout_seconds

    def run(self, arguments: Sequence[str], *, stdin: str | None = None) -> CommandResult:
        argv = (self.binary, *tuple(arguments))
        try:
            completed = subprocess.run(
                list(argv),
                input=stdin,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                shell=False,
            )
        except FileNotFoundError as exc:
            raise OpenClawCommandError("openclaw_not_found") from exc
        except subprocess.TimeoutExpired as exc:
            raise OpenClawCommandError("openclaw_timeout") from exc

        if completed.returncode != 0:
            raise OpenClawCommandError(
                "openclaw_command_failed",
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        return CommandResult(
            argv=argv,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    def run_json(self, arguments: Sequence[str], *, stdin: str | None = None) -> Any:
        result = self.run(arguments, stdin=stdin)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise OpenClawCommandError("openclaw_invalid_json") from exc
