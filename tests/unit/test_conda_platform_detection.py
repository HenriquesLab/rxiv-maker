"""Tests for conda/mamba environment detection in PlatformDetector.

This module specifically tests conda and mamba environment detection
to ensure rxiv-maker works correctly in anaconda/miniconda environments.
"""

import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from rxiv_maker.utils.platform import (
    PlatformDetector,
    get_conda_env_name,
    get_conda_executable,
    get_conda_python_path,
    is_in_conda_env,
)


class TestCondaPlatformDetection(unittest.TestCase):
    """Test conda environment detection functionality."""

    def setUp(self):
        """Set up test environment."""
        self.detector = PlatformDetector()

        # Store original environment
        self.original_env = {
            key: os.environ.get(key)
            for key in ["CONDA_DEFAULT_ENV", "CONDA_PREFIX", "MAMBA_DEFAULT_ENV", "MAMBA_PREFIX"]
        }

    def tearDown(self):
        """Restore original environment."""
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

    def test_conda_environment_detection_conda_default_env(self):
        """Test conda environment detection using CONDA_DEFAULT_ENV."""
        # Set up conda environment
        os.environ["CONDA_DEFAULT_ENV"] = "test_env"
        os.environ["CONDA_PREFIX"] = "/path/to/conda/envs/test_env"

        # Clear mamba vars to test conda specifically
        for key in ["MAMBA_DEFAULT_ENV", "MAMBA_PREFIX"]:
            if key in os.environ:
                del os.environ[key]

        detector = PlatformDetector()

        self.assertTrue(detector.is_in_conda_env())
        self.assertEqual(detector.get_conda_env_name(), "test_env")
        self.assertEqual(detector.get_conda_prefix(), Path("/path/to/conda/envs/test_env"))

    def test_conda_environment_detection_mamba(self):
        """Test mamba environment detection."""
        # Set up mamba environment
        os.environ["MAMBA_DEFAULT_ENV"] = "mamba_env"
        os.environ["MAMBA_PREFIX"] = "/path/to/mamba/envs/mamba_env"

        # Clear conda vars to test mamba specifically
        for key in ["CONDA_DEFAULT_ENV", "CONDA_PREFIX"]:
            if key in os.environ:
                del os.environ[key]

        detector = PlatformDetector()

        self.assertTrue(detector.is_in_conda_env())
        self.assertEqual(detector.get_conda_env_name(), "mamba_env")
        self.assertEqual(detector.get_conda_prefix(), Path("/path/to/mamba/envs/mamba_env"))

    def test_conda_environment_detection_base_environment(self):
        """Test conda base environment detection (should return None for env name)."""
        os.environ["CONDA_DEFAULT_ENV"] = "base"
        os.environ["CONDA_PREFIX"] = "/path/to/conda"

        detector = PlatformDetector()

        self.assertTrue(detector.is_in_conda_env())
        self.assertIsNone(detector.get_conda_env_name())  # base env should return None
        self.assertEqual(detector.get_conda_prefix(), Path("/path/to/conda"))

    def test_no_conda_environment(self):
        """Test behavior when not in conda environment."""
        # Clear all conda/mamba environment variables
        for key in ["CONDA_DEFAULT_ENV", "CONDA_PREFIX", "MAMBA_DEFAULT_ENV", "MAMBA_PREFIX"]:
            if key in os.environ:
                del os.environ[key]

        detector = PlatformDetector()

        self.assertFalse(detector.is_in_conda_env())
        self.assertIsNone(detector.get_conda_env_name())
        self.assertIsNone(detector.get_conda_prefix())
        self.assertIsNone(detector.get_conda_python_path())

    def test_conda_python_path_windows(self):
        """Test conda python path detection on Windows."""
        with patch.object(self.detector, "is_windows", return_value=True):
            with patch.object(self.detector, "is_in_conda_env", return_value=True):
                with patch.object(self.detector, "get_conda_prefix", return_value=Path("/conda/envs/test")):
                    with patch("pathlib.Path.exists", return_value=True):
                        result = self.detector.get_conda_python_path()
                        expected = str(Path("/conda/envs/test") / "python.exe")
                        self.assertEqual(result, expected)

    def test_conda_python_path_unix(self):
        """Test conda python path detection on Unix."""
        with patch.object(self.detector, "is_windows", return_value=False):
            with patch.object(self.detector, "is_in_conda_env", return_value=True):
                with patch.object(self.detector, "get_conda_prefix", return_value=Path("/conda/envs/test")):
                    with patch("pathlib.Path.exists", return_value=True):
                        result = self.detector.get_conda_python_path()
                        expected = str(Path("/conda/envs/test") / "bin" / "python")
                        self.assertEqual(result, expected)

    def test_conda_python_path_not_exists(self):
        """Test conda python path when python executable doesn't exist."""
        with patch.object(self.detector, "is_in_conda_env", return_value=True):
            with patch.object(self.detector, "get_conda_prefix", return_value=Path("/conda/envs/test")):
                with patch("pathlib.Path.exists", return_value=False):
                    result = self.detector.get_conda_python_path()
                    self.assertIsNone(result)

    @patch("shutil.which")
    def test_conda_executable_detection_mamba_preferred(self, mock_which):
        """Test that mamba is preferred over conda when both are available."""

        # Mock both mamba and conda being available
        def which_side_effect(cmd):
            if cmd == "mamba":
                return "/usr/bin/mamba"
            elif cmd == "conda":
                return "/usr/bin/conda"
            return None

        mock_which.side_effect = which_side_effect

        detector = PlatformDetector()
        result = detector.get_conda_executable()
        self.assertEqual(result, "mamba")

    @patch("shutil.which")
    def test_conda_executable_detection_conda_fallback(self, mock_which):
        """Test conda fallback when mamba is not available."""

        # Mock only conda being available
        def which_side_effect(cmd):
            if cmd == "conda":
                return "/usr/bin/conda"
            return None

        mock_which.side_effect = which_side_effect

        detector = PlatformDetector()
        result = detector.get_conda_executable()
        self.assertEqual(result, "conda")

    @patch("shutil.which")
    def test_conda_executable_detection_none(self, mock_which):
        """Test when neither conda nor mamba are available."""
        mock_which.return_value = None

        detector = PlatformDetector()
        result = detector.get_conda_executable()
        self.assertIsNone(result)

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_conda_forge_availability_true(self, mock_which, mock_run):
        """Test conda-forge channel availability detection."""
        mock_which.return_value = "/usr/bin/conda"
        mock_run.return_value = Mock(returncode=0, stdout="channels:\n  - conda-forge\n  - defaults")

        detector = PlatformDetector()
        result = detector.is_conda_forge_available()
        self.assertTrue(result)

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_conda_forge_availability_false(self, mock_which, mock_run):
        """Test conda-forge channel not available."""
        mock_which.return_value = "/usr/bin/conda"
        mock_run.return_value = Mock(returncode=0, stdout="channels:\n  - defaults")

        detector = PlatformDetector()
        result = detector.is_conda_forge_available()
        self.assertFalse(result)

    @patch("shutil.which")
    def test_conda_forge_availability_no_conda(self, mock_which):
        """Test conda-forge availability when conda is not available."""
        mock_which.return_value = None

        detector = PlatformDetector()
        result = detector.is_conda_forge_available()
        self.assertFalse(result)

    def test_python_command_detection_with_conda(self):
        """Test Python command detection in conda environment."""
        with patch("shutil.which", return_value=None):  # No uv
            with patch.object(PlatformDetector, "get_conda_python_path", return_value="/conda/envs/test/bin/python"):
                with patch.object(
                    PlatformDetector,
                    "get_venv_python_path",
                    return_value=None,  # No venv
                ):
                    with patch("pathlib.Path.exists", return_value=True):
                        detector = PlatformDetector()
                        self.assertEqual(detector.python_cmd, "/conda/envs/test/bin/python")

    def test_python_command_detection_priority(self):
        """Test Python command detection priority: uv > conda > venv > system."""
        # Test that conda is used when uv is not available but conda is
        with patch("shutil.which", return_value=None):  # No uv
            with patch.object(PlatformDetector, "get_conda_python_path", return_value="/conda/bin/python"):
                with patch("pathlib.Path.exists", return_value=True):
                    with patch.object(PlatformDetector, "get_venv_python_path", return_value=None):
                        detector = PlatformDetector()
                        self.assertEqual(detector.python_cmd, "/conda/bin/python")


class TestCondaGlobalFunctions(unittest.TestCase):
    """Test global conda utility functions."""

    def setUp(self):
        """Set up test environment."""
        # Store original environment
        self.original_env = {
            key: os.environ.get(key)
            for key in ["CONDA_DEFAULT_ENV", "CONDA_PREFIX", "MAMBA_DEFAULT_ENV", "MAMBA_PREFIX"]
        }

    def tearDown(self):
        """Restore original environment."""
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

    def test_is_in_conda_env_global(self):
        """Test global is_in_conda_env function."""
        # Clear environment first
        for key in ["CONDA_DEFAULT_ENV", "CONDA_PREFIX", "MAMBA_DEFAULT_ENV", "MAMBA_PREFIX"]:
            if key in os.environ:
                del os.environ[key]

        self.assertFalse(is_in_conda_env())

        # Set conda environment
        os.environ["CONDA_DEFAULT_ENV"] = "test"
        self.assertTrue(is_in_conda_env())

    def test_get_conda_env_name_global(self):
        """Test global get_conda_env_name function."""
        os.environ["CONDA_DEFAULT_ENV"] = "test_env"
        self.assertEqual(get_conda_env_name(), "test_env")

    def test_get_conda_python_path_global(self):
        """Test global get_conda_python_path function."""
        with patch("rxiv_maker.utils.platform.platform_detector") as mock_detector:
            mock_detector.get_conda_python_path.return_value = "/conda/bin/python"
            result = get_conda_python_path()
            self.assertEqual(result, "/conda/bin/python")

    @patch("shutil.which")
    def test_get_conda_executable_global(self, mock_which):
        """Test global get_conda_executable function."""
        mock_which.side_effect = lambda cmd: "/usr/bin/conda" if cmd == "conda" else None
        result = get_conda_executable()
        self.assertEqual(result, "conda")


class TestCondaIntegrationWithExistingCode(unittest.TestCase):
    """Test that conda functionality integrates well with existing code."""

    def test_conda_environment_affects_platform_detector(self):
        """Test that conda environment detection affects overall platform behavior."""
        with patch.dict(os.environ, {"CONDA_DEFAULT_ENV": "test_env", "CONDA_PREFIX": "/conda/envs/test_env"}):
            detector = PlatformDetector()

            # Should detect conda environment
            self.assertTrue(detector.is_in_conda_env())

            # Python command should include conda path if available
            with patch.object(detector, "get_conda_python_path", return_value="/conda/envs/test_env/bin/python"):
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("shutil.which", return_value=None):  # No uv
                        detector_new = PlatformDetector()
                        self.assertEqual(detector_new.python_cmd, "/conda/envs/test_env/bin/python")


if __name__ == "__main__":
    unittest.main()
