import json
import stat
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "manager.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False)


class ManagerTests(unittest.TestCase):
    def test_delete_requires_confirmation(self):
        result = run("delete", "agent-a")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--confirm", result.stderr)


    def test_dry_run_is_json_and_does_not_need_openclaw(self):
        result = run("create", "agent-a", "--workspace", "/tmp/ws", "--dry-run", "--openclaw-bin", "does-not-exist")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["results"][0]["status"], "planned")
        self.assertIn("agents add agent-a", payload["results"][0]["command"])


    def test_create_delegates_to_cli(self):
        result = run("create", "agent-a", "--workspace", "/tmp/ws", "--bind", "telegram:demo", "--openclaw-bin", "/bin/echo")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        command = payload["results"][0]["stdout"]
        self.assertIn("agents", command)
        self.assertIn("--non-interactive", command)
        self.assertIn("telegram:demo", command)


if __name__ == "__main__":
    unittest.main()
