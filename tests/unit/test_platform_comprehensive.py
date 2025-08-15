"""Comprehensive test coverage for platform.py utilities."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rxiv_maker.utils.platform import PlatformDetector, platform_detector


class TestPlatformDetectorCore(unittest.TestCase):
    """Test core PlatformDetector functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = PlatformDetector()

    def test_platform_detection_returns_valid_platform(self):
        """Test that platform detection returns a valid platform string."""
        platform_name = self.detector._detect_platform()
        self.assertIn(platform_name, ["Windows", "macOS", "Linux", "Unknown"])

    def test_get_platform_normalized_consistency(self):
        """Test platform normalization is consistent."""
        normalized = self.detector.get_platform_normalized()
        self.assertIn(normalized, ["windows", "macos", "linux"])

    @patch("os.name", "nt")
    def test_platform_detection_windows(self):
        """Test Windows platform detection."""
        detector = PlatformDetector()
        self.assertEqual(detector._detect_platform(), "Windows")
        self.assertTrue(detector.is_windows())
        self.assertFalse(detector.is_macos())
        self.assertFalse(detector.is_linux())

    @patch("platform.system")
    def test_platform_detection_macos(self, mock_system):
        """Test macOS platform detection."""
        mock_system.return_value = "Darwin"
        detector = PlatformDetector()
        self.assertEqual(detector._detect_platform(), "macOS")
        self.assertFalse(detector.is_windows())
        self.assertTrue(detector.is_macos())
        self.assertFalse(detector.is_linux())

    @patch("platform.system")
    def test_platform_detection_linux(self, mock_system):
        """Test Linux platform detection."""
        mock_system.return_value = "Linux"
        detector = PlatformDetector()
        self.assertEqual(detector._detect_platform(), "Linux")
        self.assertFalse(detector.is_windows())
        self.assertFalse(detector.is_macos())
        self.assertTrue(detector.is_linux())

    def test_unix_like_detection(self):
        """Test Unix-like platform detection."""
        with patch.object(self.detector, "is_macos", return_value=True):
            self.assertTrue(self.detector.is_unix_like())

        with patch.object(self.detector, "is_linux", return_value=True):
            self.assertTrue(self.detector.is_unix_like())

        with patch.object(self.detector, "is_windows", return_value=True):
            with patch.object(self.detector, "is_macos", return_value=False):
                with patch.object(self.detector, "is_linux", return_value=False):
                    self.assertFalse(self.detector.is_unix_like())

    @patch("shutil.which")
    @patch.dict(os.environ, {}, clear=True)
    @patch("pathlib.Path.exists")
    def test_python_command_detection_system_python3(self, mock_exists, mock_which):
        """Test Python command detection fallback to system python3."""
        mock_which.return_value = None  # No uv
        mock_exists.return_value = False  # No conda/venv python
        with patch.object(PlatformDetector, "is_windows", return_value=False):
            detector = PlatformDetector()
            self.assertEqual(detector._detect_python_command(), "python3")

    @patch("shutil.which")
    @patch.dict(os.environ, {}, clear=True)
    @patch("pathlib.Path.exists")
    def test_python_command_detection_system_python_windows(self, mock_exists, mock_which):
        """Test Python command detection fallback to system python on Windows."""
        mock_which.return_value = None  # No uv
        mock_exists.return_value = False  # No conda/venv python
        with patch.object(PlatformDetector, "is_windows", return_value=True):
            detector = PlatformDetector()
            self.assertEqual(detector._detect_python_command(), "python")

    @patch("shutil.which")
    def test_python_command_detection_fallback(self, mock_which):
        """Test Python command detection fallback."""
        mock_which.return_value = None
        with patch("sys.executable", "/usr/bin/python"):
            detector = PlatformDetector()
            # Should return sys.executable if which fails
            result = detector._detect_python_command()
            self.assertIn("python", result)


class TestPlatformDetectorEnvironment(unittest.TestCase):
    """Test environment detection methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = PlatformDetector()

    def test_is_conda_env_with_conda_default_env(self):
        """Test conda environment detection with CONDA_DEFAULT_ENV."""
        with patch.dict(os.environ, {"CONDA_DEFAULT_ENV": "myenv"}):
            self.assertTrue(self.detector.is_in_conda_env())

    def test_is_conda_env_with_conda_prefix(self):
        """Test conda environment detection with CONDA_PREFIX."""
        with patch.dict(os.environ, {"CONDA_PREFIX": "/opt/conda"}):
            self.assertTrue(self.detector.is_in_conda_env())

    def test_is_conda_env_false(self):
        """Test conda environment detection when not in conda."""
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(self.detector.is_in_conda_env())

    def test_get_conda_env_name_from_default_env(self):
        """Test getting conda environment name from CONDA_DEFAULT_ENV."""
        with patch.dict(os.environ, {"CONDA_DEFAULT_ENV": "test-env"}):
            self.assertEqual(self.detector.get_conda_env_name(), "test-env")

    def test_get_conda_env_name_from_mamba_default_env(self):
        """Test getting conda environment name from MAMBA_DEFAULT_ENV."""
        with patch.dict(os.environ, {"MAMBA_DEFAULT_ENV": "myenv"}):
            self.assertEqual(self.detector.get_conda_env_name(), "myenv")

    def test_get_conda_env_name_none(self):
        """Test getting conda environment name when not in conda."""
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(self.detector.get_conda_env_name())

    def test_get_conda_prefix(self):
        """Test getting conda prefix."""
        with patch.dict(os.environ, {"CONDA_PREFIX": "/opt/conda/envs/test"}):
            result = self.detector.get_conda_prefix()
            self.assertEqual(str(result), "/opt/conda/envs/test")

    def test_get_conda_prefix_none(self):
        """Test getting conda prefix when not set."""
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(self.detector.get_conda_prefix())

    @patch("shutil.which")
    def test_get_conda_executable_conda_available(self, mock_which):
        """Test getting conda executable when conda is available."""
        mock_which.side_effect = lambda cmd: "conda" if cmd == "conda" else None
        self.assertEqual(self.detector.get_conda_executable(), "conda")

    @patch("shutil.which")
    def test_get_conda_executable_mamba_fallback(self, mock_which):
        """Test getting conda executable with mamba fallback."""
        mock_which.side_effect = lambda cmd: "mamba" if cmd == "mamba" else None
        self.assertEqual(self.detector.get_conda_executable(), "mamba")

    @patch("shutil.which")
    def test_get_conda_executable_none(self, mock_which):
        """Test getting conda executable when none available."""
        mock_which.return_value = None
        self.assertIsNone(self.detector.get_conda_executable())


class TestPlatformDetectorVirtualEnv(unittest.TestCase):
    """Test virtual environment detection methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = PlatformDetector()

    def test_is_in_venv_with_virtual_env(self):
        """Test virtual environment detection with VIRTUAL_ENV."""
        with patch.dict(os.environ, {"VIRTUAL_ENV": "/path/to/venv"}):
            self.assertTrue(self.detector.is_in_venv())

    def test_is_in_venv_false(self):
        """Test virtual environment detection when not in venv."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("rxiv_maker.utils.platform.sys") as mock_sys:
                # Mock sys to simulate non-venv environment
                mock_sys.prefix = "/usr/local"
                mock_sys.base_prefix = "/usr/local"
                # Ensure real_prefix doesn't exist (no hasattr for old virtualenv)
                del mock_sys.real_prefix
                self.assertFalse(self.detector.is_in_venv())

    def test_get_virtual_env_path(self):
        """Test getting virtual environment path when .venv exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock .venv directory with python executable
            venv_dir = Path(temp_dir) / ".venv"
            venv_bin = venv_dir / "bin"
            venv_bin.mkdir(parents=True)
            python_exe = venv_bin / "python"
            python_exe.touch()

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                result = self.detector.get_venv_python_path()
                self.assertIsNotNone(result)
                self.assertTrue(result.endswith("python"))
            finally:
                os.chdir(original_cwd)

    @patch.dict(os.environ, {}, clear=True)  # Clear all environment variables including VIRTUAL_ENV
    def test_get_virtual_env_path_none(self):
        """Test getting virtual environment path when .venv doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory where .venv doesn't exist
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                # Create a fresh detector instance to avoid cached environment
                detector = PlatformDetector()
                result = detector.get_venv_python_path()
                self.assertIsNone(result)
            finally:
                os.chdir(original_cwd)

    @patch("os.name", "nt")  # Mock os.name for Windows detection
    def test_venv_python_path_windows(self):
        """Test virtual environment Python path on Windows."""
        detector = PlatformDetector()
        with patch.dict(os.environ, {"VIRTUAL_ENV": "C:\\venv"}):
            with patch("rxiv_maker.utils.platform.Path") as mock_path:
                # Mock Path constructor and path operations
                mock_venv_dir = mock_path.return_value
                mock_scripts_dir = mock_venv_dir.__truediv__.return_value
                mock_python_path = mock_scripts_dir.__truediv__.return_value
                mock_python_path.__str__.return_value = "C:\\venv\\Scripts\\python.exe"
                mock_python_path.exists.return_value = True

                expected = "C:\\venv\\Scripts\\python.exe"
                self.assertEqual(detector.get_venv_python_path(), expected)

    @patch("platform.system", return_value="Linux")
    @patch("os.name", "posix")  # Mock os.name for Unix detection
    def test_venv_python_path_unix(self, mock_system):
        """Test virtual environment Python path on Unix."""
        detector = PlatformDetector()
        with patch.dict(os.environ, {"VIRTUAL_ENV": "/opt/venv"}):
            with patch("pathlib.Path.exists", return_value=True):
                expected = "/opt/venv/bin/python"
                self.assertEqual(detector.get_venv_python_path(), expected)

    def test_venv_python_path_no_venv(self):
        """Test virtual environment Python path when not in venv."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("pathlib.Path.exists", return_value=False):
                self.assertIsNone(self.detector.get_venv_python_path())

    @patch("os.name", "nt")  # Mock os.name for Windows detection
    def test_venv_activate_path_windows(self):
        """Test virtual environment activate path on Windows."""
        detector = PlatformDetector()
        with patch.dict(os.environ, {"VIRTUAL_ENV": "C:\\venv"}):
            with patch("rxiv_maker.utils.platform.Path") as mock_path:
                # Mock Path constructor and path operations
                mock_venv_dir = mock_path.return_value
                mock_scripts_dir = mock_venv_dir.__truediv__.return_value
                mock_activate_path = mock_scripts_dir.__truediv__.return_value
                mock_activate_path.__str__.return_value = "C:\\venv\\Scripts\\activate"
                mock_activate_path.exists.return_value = True

                expected = "C:\\venv\\Scripts\\activate"
                self.assertEqual(detector.get_venv_activate_path(), expected)

    @patch("platform.system", return_value="Linux")
    @patch("os.name", "posix")  # Mock os.name for Unix detection
    def test_venv_activate_path_unix(self, mock_system):
        """Test virtual environment activate path on Unix."""
        detector = PlatformDetector()
        with patch.dict(os.environ, {"VIRTUAL_ENV": "/opt/venv"}):
            with patch("pathlib.Path.exists", return_value=True):
                expected = "/opt/venv/bin/activate"
                self.assertEqual(detector.get_venv_activate_path(), expected)


# NOTE: The following test class tests methods that don't exist in the actual PlatformDetector implementation
# These tests should be reviewed and either removed or the methods should be implemented
#
# class TestPlatformDetectorFileOperations(unittest.TestCase):
#     """Test file operation utilities."""
#     # These tests are for methods not implemented in platform.py:
#     # - ensure_directory()
#     # - safe_file_operation()
#     # - read_conda_environment_file()
#
#     def setUp(self):
#         """Set up test fixtures."""
#         self.detector = PlatformDetector()
#         self.test_dir = tempfile.mkdtemp()
#
#     def tearDown(self):
#         """Clean up test fixtures."""
#         shutil.rmtree(self.test_dir, ignore_errors=True)
#
#     @unittest.skip("Method ensure_directory not implemented in PlatformDetector")
#     def test_ensure_directory_creates_directory(self):
#         """Test directory creation with ensure_directory."""
#         test_path = Path(self.test_dir) / "new_dir"
#         self.detector.ensure_directory(test_path)
#         self.assertTrue(test_path.exists())
#         self.assertTrue(test_path.is_dir())
#
#     @unittest.skip("Method ensure_directory not implemented in PlatformDetector")
#     def test_ensure_directory_existing_directory(self):
#         """Test ensure_directory with existing directory."""
#         test_path = Path(self.test_dir) / "existing"
#         test_path.mkdir()
#
#         # Should not raise an error
#         self.detector.ensure_directory(test_path)
#         self.assertTrue(test_path.exists())
#
#     @unittest.skip("Method ensure_directory not implemented in PlatformDetector")
#     def test_ensure_directory_with_permissions(self):
#         """Test directory creation with specific permissions."""
#         test_path = Path(self.test_dir) / "perm_dir"
#         self.detector.ensure_directory(test_path, permissions=0o755)
#         self.assertTrue(test_path.exists())
#
#     @unittest.skip("Method safe_file_operation not implemented in PlatformDetector")
#     def test_safe_file_operation_success(self):
#         """Test successful safe file operation."""
#         test_file = Path(self.test_dir) / "test.txt"
#
#         def write_operation():
#             test_file.write_text("test content")
#             return True
#
#         result = self.detector.safe_file_operation(write_operation, "write test file")
#         self.assertTrue(result)
#         self.assertTrue(test_file.exists())
#
#     @unittest.skip("Method safe_file_operation not implemented in PlatformDetector")
#     def test_safe_file_operation_failure(self):
#         """Test safe file operation with failure."""
#
#         def failing_operation():
#             raise PermissionError("Access denied")
#
#         result = self.detector.safe_file_operation(failing_operation, "failing operation")
#         self.assertFalse(result)
#
#     @unittest.skip("Method read_conda_environment_file not implemented in PlatformDetector")
#     def test_read_conda_environment_file_success(self):
#         """Test reading conda environment file successfully."""
#         env_file = Path(self.test_dir) / "environment.yml"
#         env_file.write_text("VAR1=value1\nVAR2=value2\n# Comment\n")
#
#         result = self.detector.read_conda_environment_file(str(env_file))
#         expected = {"VAR1": "value1", "VAR2": "value2"}
#         self.assertEqual(result, expected)
#
#     @unittest.skip("Method read_conda_environment_file not implemented in PlatformDetector")
#     def test_read_conda_environment_file_missing(self):
#         """Test reading non-existent conda environment file."""
#         result = self.detector.read_conda_environment_file("/nonexistent/file.yml")
#         self.assertEqual(result, {})


class TestPlatformDetectorPackageManager(unittest.TestCase):
    """Test package manager detection and operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = PlatformDetector()

    @unittest.skip("Complex mocking required - install_uv has multi-step subprocess calls")
    @patch("subprocess.run")
    def test_install_uv_success_windows(self, mock_run):
        """Test successful UV installation on Windows."""
        with patch.object(self.detector, "is_windows", return_value=True):
            mock_run.return_value.returncode = 0

            result = self.detector.install_uv()
            self.assertTrue(result)
            mock_run.assert_called()

    @unittest.skip("Complex mocking required - install_uv has multi-step subprocess calls")
    @patch("subprocess.run")
    def test_install_uv_success_unix(self, mock_run):
        """Test successful UV installation on Unix."""
        with patch.object(self.detector, "is_windows", return_value=False):
            mock_run.return_value.returncode = 0

            result = self.detector.install_uv()
            self.assertTrue(result)
            mock_run.assert_called()

    @patch("subprocess.run")
    def test_install_uv_failure(self, mock_run):
        """Test UV installation failure."""
        mock_run.return_value.returncode = 1

        result = self.detector.install_uv()
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_install_uv_exception(self, mock_run):
        """Test UV installation with exception."""
        mock_run.side_effect = Exception("Network error")

        result = self.detector.install_uv()
        self.assertFalse(result)

    @unittest.skip("Method check_package_manager_availability not implemented in PlatformDetector")
    @patch("shutil.which")
    def test_check_package_manager_availability_uv(self, mock_which):
        """Test package manager availability check for UV."""
        mock_which.side_effect = lambda cmd: "/usr/bin/uv" if cmd == "uv" else None

        available = self.detector.check_package_manager_availability()
        self.assertIn("uv", available)

    @unittest.skip("Method check_package_manager_availability not implemented in PlatformDetector")
    @patch("shutil.which")
    def test_check_package_manager_availability_pip(self, mock_which):
        """Test package manager availability check for pip."""
        mock_which.side_effect = lambda cmd: "/usr/bin/pip" if cmd == "pip" else None

        available = self.detector.check_package_manager_availability()
        self.assertIn("pip", available)

    @unittest.skip("Method check_package_manager_availability not implemented in PlatformDetector")
    @patch("shutil.which")
    def test_check_package_manager_availability_none(self, mock_which):
        """Test package manager availability when none available."""
        mock_which.return_value = None

        available = self.detector.check_package_manager_availability()
        self.assertEqual(available, [])


class TestPlatformDetectorSystemInfo(unittest.TestCase):
    """Test system information gathering methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = PlatformDetector()

    @unittest.skip("Method get_platform_info not implemented in PlatformDetector")
    def test_get_platform_info_structure(self):
        """Test platform info returns expected structure."""
        info = self.detector.get_platform_info()

        required_keys = ["platform", "python_version", "python_executable"]
        for key in required_keys:
            self.assertIn(key, info)

    @unittest.skip("Method get_platform_info not implemented in PlatformDetector")
    def test_get_platform_info_types(self):
        """Test platform info returns correct types."""
        info = self.detector.get_platform_info()

        self.assertIsInstance(info["platform"], str)
        self.assertIsInstance(info["python_version"], str)
        self.assertIsInstance(info["python_executable"], str)

    @unittest.skip("Method get_platform_info not implemented in PlatformDetector")
    @patch("sys.executable")
    @patch("platform.python_version")
    def test_get_platform_info_values(self, mock_py_version, mock_executable):
        """Test platform info returns correct values."""
        mock_py_version.return_value = "3.11.5"
        mock_executable.__str__ = lambda: "/usr/bin/python3"

        info = self.detector.get_platform_info()
        self.assertEqual(info["python_version"], "3.11.5")

    def test_platform_detector_singleton(self):
        """Test that platform_detector is a singleton instance."""
        self.assertIsInstance(platform_detector, PlatformDetector)

        # Should return the same instance
        from rxiv_maker.utils.platform import platform_detector as pd2

        self.assertIs(platform_detector, pd2)


class TestPlatformDetectorEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = PlatformDetector()

    @patch("platform.system")
    def test_unknown_platform_handling(self, mock_system):
        """Test handling of unknown platform."""
        mock_system.return_value = "UnknownOS"
        detector = PlatformDetector()

        # Should return "Unknown" for unknown platforms
        self.assertEqual(detector._detect_platform(), "Unknown")

    def test_venv_path_with_missing_executable(self):
        """Test venv path when Python executable doesn't exist."""
        with patch.dict(os.environ, {"VIRTUAL_ENV": "/nonexistent/venv"}):
            path = self.detector.get_venv_python_path()
            # Should return None when the executable doesn't exist
            self.assertIsNone(path)

    def test_conda_env_name_with_complex_path(self):
        """Test conda environment name with complex environment variable."""
        complex_env_name = "my-complex-env-name"
        with patch.dict(os.environ, {"CONDA_DEFAULT_ENV": complex_env_name}):
            name = self.detector.get_conda_env_name()
            self.assertEqual(name, "my-complex-env-name")

    @unittest.skip("Method safe_file_operation not implemented in PlatformDetector")
    def test_file_operations_with_readonly_filesystem(self):
        """Test file operations on read-only filesystem."""
        # Create a temporary directory and make it read-only
        test_dir = tempfile.mkdtemp()
        try:
            os.chmod(test_dir, 0o444)  # Read-only

            def failing_write():
                (Path(test_dir) / "test.txt").write_text("test")

            result = self.detector.safe_file_operation(failing_write, "write to readonly")
            self.assertFalse(result)
        finally:
            os.chmod(test_dir, 0o755)  # Restore permissions for cleanup
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
