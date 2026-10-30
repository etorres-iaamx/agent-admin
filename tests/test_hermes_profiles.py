import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "tools" / "hermes_profiles" / "manager.py"


class HermesProfileManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / ".hermes"
        self.home.mkdir()
        self.fake_bin = Path(self.tmp.name) / "hermes"
        self.fake_bin.write_text("""#!/usr/bin/env python3
import json, os, sys
log = os.environ.get('HERMES_TEST_LOG')
if log:
    with open(log, 'a', encoding='utf-8') as f:
        f.write(json.dumps(sys.argv[1:]) + '\\n')
print('ok: ' + ' '.join(sys.argv[1:]))
""")
        self.fake_bin.chmod(self.fake_bin.stat().st_mode | stat.S_IXUSR)
        self.env = os.environ.copy()
        self.env["HERMES_HOME"] = str(self.home)
        self.env["HERMES_TEST_LOG"] = str(Path(self.tmp.name) / "commands.log")

    def tearDown(self):
        self.tmp.cleanup()

    def run_manager(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_create_delegates_to_hermes_without_clone(self):
        result = self.run_manager(
            "create", "cliente-001", "--description", "Atencion Comercial",
            "--hermes-bin", str(self.fake_bin), "--no-alias",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["result"]["command"][1:4], ["profile", "create", "cliente-001"])
        self.assertIn("--no-alias", payload["result"]["command"])
        self.assertNotIn("--clone", payload["result"]["command"])

    def test_default_is_protected_from_delete(self):
        result = self.run_manager(
            "delete", "default", "--confirm", "--hermes-bin", str(self.fake_bin)
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("default", result.stderr)

    def test_context_update_writes_only_named_profile_files(self):
        profile_dir = self.home / "profiles" / "cliente-001" / "memories"
        profile_dir.mkdir(parents=True)
        soul = Path(self.tmp.name) / "SOUL.md"
        user = Path(self.tmp.name) / "USER.md"
        agents = Path(self.tmp.name) / "AGENTS.md"
        soul.write_text("Yolotl")
        user.write_text("Estudio Prisma")
        agents.write_text("Solo cliente-003")
        result = self.run_manager(
            "context-update", "cliente-001",
            "--soul-file", str(soul), "--user-file", str(user), "--agents-file", str(agents),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / "profiles/cliente-001/SOUL.md").read_text(), "Yolotl")
        self.assertEqual((self.home / "profiles/cliente-001/memories/USER.md").read_text(), "Estudio Prisma")
        self.assertEqual((self.home / "profiles/cliente-001/AGENTS.md").read_text(), "Solo cliente-003")

    def test_validate_reports_missing_context_files(self):
        result = self.run_manager("validate", "cliente-002")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["result"]["valid"])
        self.assertIn("SOUL.md", payload["result"]["missing"])

    def test_dry_run_does_not_write_or_execute(self):
        result = self.run_manager(
            "context-update", "cliente-003", "--dry-run", "--soul-file", str(Path(self.tmp.name) / "missing")
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["result"]["status"], "planned")
        self.assertFalse((self.home / "profiles/cliente-003/SOUL.md").exists())


if __name__ == "__main__":
    unittest.main()
