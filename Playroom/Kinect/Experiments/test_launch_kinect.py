"""Offline tests for the Kinect launcher; never access the camera."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from Playroom.Kinect.Experiments import launch_kinect


class KinectLauncherTests(unittest.TestCase):
    def test_usb_ids_from_sysfs(self):
        with tempfile.TemporaryDirectory() as folder:
            camera = Path(folder) / "1-1"
            camera.mkdir()
            (camera / "idVendor").write_text("045e\n")
            (camera / "idProduct").write_text("02bf\n")
            other = Path(folder) / "1-2"
            other.mkdir()
            (other / "idVendor").write_text("ffff\n")
            (other / "idProduct").write_text("0001\n")
            with patch.object(launch_kinect, "Path") as mocked:
                # Exercise device parsing via a concrete base path.
                original = Path
                mocked.side_effect = lambda arg: original(folder) if arg == "/sys/bus/usb/devices" else original(arg)
                self.assertEqual(launch_kinect.usb_devices(), [("02bf", "Kinect camera")])

    def test_missing_interpreter_is_not_working(self):
        self.assertFalse(launch_kinect.supports_kinect("/definitely/not/here/kinect-python"))

    def test_preflight_does_not_launch(self):
        with patch.object(launch_kinect, "usb_devices", return_value=[]), \
             patch.object(launch_kinect, "candidate_interpreters", return_value=iter([])), \
             patch.object(launch_kinect, "NATIVE", Path("/definitely/not/here/native")):
            self.assertEqual(launch_kinect.main(["--check"]), 2)


if __name__ == "__main__":
    unittest.main()
