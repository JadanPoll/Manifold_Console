"""No devices, network calls, installations or GUI required."""
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from Applications.CameraLab import camera_env


class CameraEnvironmentTests(unittest.TestCase):
    def test_reuse_existing_opencv_environment(self):
        with patch.object(camera_env, "candidates", return_value=iter([
            "/not/a/python", sys.executable
        ])), patch.object(camera_env.subprocess, "run",
                         return_value=SimpleNamespace(returncode=0)) as run:
            path, count = camera_env.working_python()
            self.assertEqual(path, sys.executable)
            self.assertEqual(count, 1)
            self.assertEqual(run.call_args.args[0][0], sys.executable)

    def test_failed_environment_remains_optional(self):
        with patch.object(camera_env, "candidates", return_value=iter([sys.executable])), \
             patch.object(camera_env.subprocess, "run",
                          return_value=SimpleNamespace(returncode=1)):
            self.assertEqual(camera_env.working_python(), (None, 1))

    def test_explicit_setup_only_uses_private_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "manifold-camera"
            calls = []
            def fake_run(argv, **_kwargs):
                calls.append(argv)
                return SimpleNamespace(returncode=0, stdout="ok", stderr="")
            with patch.object(camera_env, "CAMERA_VENV", target), \
                 patch.object(camera_env.subprocess, "run", side_effect=fake_run), \
                 patch.object(camera_env, "working_python", return_value=(
                     str(target / "bin/python"), 1)):
                ok, _text, _log = camera_env.install_camera_tools()
            self.assertTrue(ok)
            self.assertEqual(calls[0][:3], [sys.executable, "-m", "venv"])
            self.assertEqual(calls[1][0], str(target / "bin/python"))
            self.assertIn("--only-binary=:all:", calls[1])
            self.assertNotIn("sudo", " ".join(" ".join(a) for a in calls))


if __name__ == "__main__":
    unittest.main()
