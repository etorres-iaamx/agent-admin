import subprocess
import unittest
from unittest.mock import patch

from openclaw_agent_core import OpenClawClient, OpenClawCommandError


class ClientTests(unittest.TestCase):
    def test_uses_bounded_argv_execution(self) -> None:
        completed = subprocess.CompletedProcess(
            ["openclaw", "agents", "list", "--json"],
            0,
            stdout='[{"id":"main"}]',
            stderr="",
        )
        with patch("openclaw_agent_core.client.subprocess.run", return_value=completed) as run:
            result = OpenClawClient(timeout_seconds=7).run(["agents", "list", "--json"])

        self.assertEqual(result.stdout, '[{"id":"main"}]')
        run.assert_called_once_with(
            ["openclaw", "agents", "list", "--json"],
            input=None,
            capture_output=True,
            text=True,
            timeout=7,
            check=False,
            shell=False,
        )

    def test_redacts_failure_from_exception_text(self) -> None:
        completed = subprocess.CompletedProcess(
            ["openclaw", "agents", "list", "--json"],
            2,
            stdout="secret stdout",
            stderr="secret stderr",
        )
        with patch("openclaw_agent_core.client.subprocess.run", return_value=completed):
            with self.assertRaisesRegex(OpenClawCommandError, "openclaw_command_failed") as error:
                OpenClawClient().run(["agents", "list", "--json"])

        self.assertEqual(error.exception.stdout, "secret stdout")
        self.assertEqual(error.exception.stderr, "secret stderr")
        self.assertEqual(str(error.exception), "openclaw_command_failed")
