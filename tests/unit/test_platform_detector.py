"""Tests for cross-platform compatibility utilities.

This module tests the PlatformDetector class and related functionality
for handling Windows, macOS, and Linux platform differences.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from rxiv_maker.utils.platform import (
    PlatformDetector,
    _convert_to_ascii,
    get_platform,
    get_python_command,
    # Conda-related imports
    is_unix_like,
    is_windows,
    run_platform_command,
    safe_console_print,
    safe_print,
)

# Exclude from default CI run due to platform-specific branching and flakiness
pytestmark = pytest.mark.ci_exclude


class TestPlatformDetector(unittest.TestCase):
    """Test PlatformDetector class functionality."""

    def setUp(self):
        """Set up test environment."""
        self.detector = PlatformDetector()

    def test_detect_windows_platform(self):
        """Test Windows platform detection."""
        with patch("os.name", "nt"), patch("platform.system", return_value="Windows"):
            detector = PlatformDetector()
            self.assertEqual(detector.platform, "Windows")
            self.assertTrue(detector.is_windows())
            self.assertFalse(detector.is_macos())
            self.assertFalse(detector.is_linux())
            self.assertFalse(detector.is_unix_like())

    def test_detect_macos_platform(self):
        """Test macOS platform detection."""
        with patch("os.name", "posix"), patch("platform.system", return_value="Darwin"):
            detector = PlatformDetector()
            self.assertEqual(detector.platform, "macOS")
            self.assertFalse(detector.is_windows())
            self.assertTrue(detector.is_macos())
            self.assertFalse(detector.is_linux())
            self.assertTrue(detector.is_unix_like())

    def test_detect_linux_platform(self):
        """Test Linux platform detection."""
        with patch("os.name", "posix"), patch("platform.system", return_value="Linux"):
            detector = PlatformDetector()
            self.assertEqual(detector.platform, "Linux")
            self.assertFalse(detector.is_windows())
            self.assertFalse(detector.is_macos())
            self.assertTrue(detector.is_linux())
            self.assertTrue(detector.is_unix_like())

    def test_detect_unknown_platform(self):
        """Test unknown platform detection fallback."""
        with (
            patch("os.name", "unknown"),
            patch("platform.system", return_value="Unknown"),
        ):
            detector = PlatformDetector()
            self.assertEqual(detector.platform, "Unknown")

    def test_path_separator_windows(self):
        """Test path separator for Windows."""
        with patch.object(self.detector, "is_windows", return_value=True):
            self.assertEqual(self.detector.get_path_separator(), "\\")

    def test_path_separator_unix(self):
        """Test path separator for Unix-like systems."""
        with patch.object(self.detector, "is_windows", return_value=False):
            self.assertEqual(self.detector.get_path_separator(), "/")

    def test_null_device_windows(self):
        """Test null device for Windows."""
        with patch.object(self.detector, "is_windows", return_value=True):
            self.assertEqual(self.detector.get_null_device(), "nul")

    def test_null_device_unix(self):
        """Test null device for Unix-like systems."""
        with patch.object(self.detector, "is_windows", return_value=False):
            self.assertEqual(self.detector.get_null_device(), "/dev/null")

    @patch("shutil.which")
    def test_python_command_detection_with_uv(self, mock_which):
        """Test Python command detection when uv is available."""
        mock_which.return_value = "/usr/local/bin/uv"

        detector = PlatformDetector()
        self.assertEqual(detector.python_cmd, "uv run python")

    @patch("shutil.which", return_value=None)
    @patch("pathlib.Path.exists")
    def test_python_command_detection_with_venv_windows(self, mock_exists, mock_which):
        """Test Python command detection with venv on Windows."""
        mock_exists.return_value = True

        with patch.object(PlatformDetector, "is_windows", return_value=True):
            with patch.object(
                PlatformDetector,
                "get_venv_python_path",
                return_value=".venv\\Scripts\\python.exe",
            ):
                detector = PlatformDetector()
                self.assertEqual(detector.python_cmd, ".venv\\Scripts\\python.exe")

    @patch("shutil.which", return_value=None)
    @patch("pathlib.Path.exists")
    def test_python_command_detection_with_venv_unix(self, mock_exists, mock_which):
        """Test Python command detection with venv on Unix."""
        mock_exists.return_value = True

        with patch.object(PlatformDetector, "is_windows", return_value=False):
            with patch.object(
                PlatformDetector,
                "get_venv_python_path",
                return_value=".venv/bin/python",
            ):
                detector = PlatformDetector()
                self.assertEqual(detector.python_cmd, ".venv/bin/python")

    @patch("shutil.which", return_value=None)
    def test_python_command_fallback_windows(self, mock_which):
        """Test Python command fallback on Windows."""
        with patch.object(PlatformDetector, "is_windows", return_value=True):
            with patch.object(PlatformDetector, "get_venv_python_path", return_value=None):
                detector = PlatformDetector()
                self.assertEqual(detector.python_cmd, "python")

    @patch("shutil.which", return_value=None)
    def test_python_command_fallback_unix(self, mock_which):
        """Test Python command fallback on Unix."""
        with patch.object(PlatformDetector, "is_windows", return_value=False):
            with patch.object(PlatformDetector, "get_venv_python_path", return_value=None):
                detector = PlatformDetector()
                self.assertEqual(detector.python_cmd, "python3")

    def test_venv_python_path_windows(self):
        """Test virtual environment Python path on Windows."""
        with patch.object(self.detector, "is_windows", return_value=True):
            # Mock both venv_dir.exists() and python_path.exists() calls
            with (
                patch("pathlib.Path.exists", return_value=True),
                patch.dict("os.environ", {"VIRTUAL_ENV": ""}, clear=False),  # Clear VIRTUAL_ENV to test .venv path
            ):
                result = self.detector.get_venv_python_path()
                # The actual implementation returns string representation which uses OS path separators
                expected = str(Path(".venv") / "Scripts" / "python.exe")
                self.assertEqual(result, expected)

    def test_venv_python_path_unix(self):
        """Test virtual environment Python path on Unix."""
        with patch.object(self.detector, "is_windows", return_value=False):
            # Mock both venv_dir.exists() and python_path.exists() calls
            with (
                patch("pathlib.Path.exists", return_value=True),
                patch.dict("os.environ", {"VIRTUAL_ENV": ""}, clear=False),  # Clear VIRTUAL_ENV to test .venv path
            ):
                result = self.detector.get_venv_python_path()
                # The actual implementation returns string representation which uses OS path separators
                expected = str(Path(".venv") / "bin" / "python")
                self.assertEqual(result, expected)

    @patch("pathlib.Path.exists", return_value=False)
    def test_venv_python_path_not_exists(self, mock_exists):
        """Test virtual environment Python path when .venv doesn't exist."""
        result = self.detector.get_venv_python_path()
        self.assertIsNone(result)

    def test_venv_activate_path_windows(self):
        """Test virtual environment activate path on Windows."""
        with (
            patch.object(self.detector, "is_windows", return_value=True),
            patch("pathlib.Path.exists", return_value=True),
            patch.dict("os.environ", {"VIRTUAL_ENV": ""}, clear=False),  # Clear VIRTUAL_ENV to test .venv path
        ):
            result = self.detector.get_venv_activate_path()
            # The actual implementation returns string representation which uses OS path separators
            expected = str(Path(".venv") / "Scripts" / "activate")
            self.assertEqual(result, expected)

    def test_venv_activate_path_unix(self):
        """Test virtual environment activate path on Unix."""
        with (
            patch.object(self.detector, "is_windows", return_value=False),
            patch("pathlib.Path.exists", return_value=True),
            patch.dict("os.environ", {"VIRTUAL_ENV": ""}, clear=False),  # Clear VIRTUAL_ENV to test .venv path
        ):
            result = self.detector.get_venv_activate_path()
            # The actual implementation returns string representation which uses OS path separators
            expected = str(Path(".venv") / "bin" / "activate")
            self.assertEqual(result, expected)

    @patch("subprocess.run")
    def test_run_command_windows(self, mock_run):
        """Test secure command execution on Windows (default shell=False)."""
        mock_run.return_value = Mock(returncode=0, stdout="output")

        with patch.object(self.detector, "is_windows", return_value=True):
            result = self.detector.run_command("echo test")

        mock_run.assert_called_once_with("echo test", shell=False)
        self.assertEqual(result.returncode, 0)

    @patch("subprocess.run")
    def test_run_command_unix(self, mock_run):
        """Test secure command execution on Unix (default shell=False)."""
        mock_run.return_value = Mock(returncode=0, stdout="output")

        with patch.object(self.detector, "is_windows", return_value=False):
            result = self.detector.run_command("echo test")

        mock_run.assert_called_once_with("echo test", shell=False)
        self.assertEqual(result.returncode, 0)

    @patch("subprocess.run")
    def test_run_command_with_shell_explicit(self, mock_run):
        """Test command execution with explicit shell=True (legacy mode)."""
        mock_run.return_value = Mock(returncode=0, stdout="output")

        # Test that shell=True still works when explicitly requested
        result = self.detector.run_command("echo test", shell=True)
        mock_run.assert_called_once_with("echo test", shell=True)
        self.assertEqual(result.returncode, 0)

    @patch("subprocess.run")
    def test_run_command_with_list_args(self, mock_run):
        """Test secure command execution with list arguments."""
        mock_run.return_value = Mock(returncode=0, stdout="output")

        # Test the secure way with list arguments
        result = self.detector.run_command(["echo", "test"])
        mock_run.assert_called_once_with(["echo", "test"], shell=False)
        self.assertEqual(result.returncode, 0)

    @patch("shutil.which")
    def test_check_command_exists_true(self, mock_which):
        """Test command existence check when command exists."""
        mock_which.return_value = "/usr/bin/python"

        result = self.detector.check_command_exists("python")
        self.assertTrue(result)

    @patch("shutil.which")
    def test_check_command_exists_false(self, mock_which):
        """Test command existence check when command doesn't exist."""
        mock_which.return_value = None

        result = self.detector.check_command_exists("nonexistent")
        self.assertFalse(result)

    def test_env_file_content_not_exists(self):
        """Test reading environment file when it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / "nonexistent.env"
            result = self.detector.get_env_file_content(env_file)
            self.assertEqual(result, {})

    def test_env_file_content_exists(self):
        """Test reading environment file content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("VAR1=value1\n")
            f.write("VAR2=value2\n")
            f.write("# Comment line\n")
            f.write("VAR3=value3=with=equals\n")
            f.write("INVALID_LINE\n")
            f.write("\n")
            env_file = Path(f.name)

        try:
            result = self.detector.get_env_file_content(env_file)
            expected = {
                "VAR1": "value1",
                "VAR2": "value2",
                "VAR3": "value3=with=equals",
            }
            self.assertEqual(result, expected)
        finally:
            env_file.unlink(missing_ok=True)

    @patch("subprocess.run")
    def test_install_uv_windows(self, mock_run):
        """Test uv installation on Windows."""
        # Mock successful responses for both PowerShell calls
        mock_run.side_effect = [
            Mock(returncode=0, stdout="$install_script_content"),  # Download script
            Mock(returncode=0, stdout="Installation complete"),  # Execute script
        ]

        with patch.object(self.detector, "is_windows", return_value=True):
            result = self.detector.install_uv()

        self.assertTrue(result)
        self.assertEqual(mock_run.call_count, 2)

        # Check first call (download script)
        first_call_args = mock_run.call_args_list[0][0][0]
        self.assertIn("powershell", first_call_args)
        self.assertIn("Invoke-RestMethod https://astral.sh/uv/install.ps1", first_call_args)

        # Check second call (execute script)
        second_call_args = mock_run.call_args_list[1][0][0]
        self.assertIn("powershell", second_call_args)
        self.assertIn("-ExecutionPolicy", second_call_args)

    @patch("subprocess.run")
    def test_install_uv_unix(self, mock_run):
        """Test uv installation on Unix."""
        # Mock successful responses for both curl and sh calls
        mock_run.side_effect = [
            Mock(returncode=0, stdout="#!/bin/sh\necho 'install script'"),  # curl download
            Mock(returncode=0, stdout="Installation complete"),  # sh execution
        ]

        with patch.object(self.detector, "is_windows", return_value=False):
            result = self.detector.install_uv()

        self.assertTrue(result)
        self.assertEqual(mock_run.call_count, 2)

        # Check first call (curl download)
        first_call_args = mock_run.call_args_list[0][0][0]
        self.assertEqual(first_call_args[0], "curl")
        self.assertIn("https://astral.sh/uv/install.sh", first_call_args)

        # Check second call (sh execution)
        second_call_args = mock_run.call_args_list[1][0][0]
        self.assertEqual(second_call_args[0], "sh")

    @patch("subprocess.run")
    def test_install_uv_failure(self, mock_run):
        """Test uv installation failure."""
        mock_run.return_value = Mock(returncode=1)

        result = self.detector.install_uv()
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_install_uv_exception(self, mock_run):
        """Test uv installation with exception."""
        mock_run.side_effect = Exception("Network error")

        result = self.detector.install_uv()
        self.assertFalse(result)

    @patch("shutil.rmtree")
    @patch("pathlib.Path.exists")
    def test_remove_directory_success(self, mock_exists, mock_rmtree):
        """Test successful directory removal."""
        mock_exists.return_value = True

        test_path = Path("test_dir")
        result = self.detector.remove_directory(test_path)

        self.assertTrue(result)
        mock_rmtree.assert_called_once_with(test_path)

    @patch("pathlib.Path.exists")
    def test_remove_directory_not_exists(self, mock_exists):
        """Test directory removal when directory doesn't exist."""
        mock_exists.return_value = False

        test_path = Path("nonexistent_dir")
        result = self.detector.remove_directory(test_path)

        self.assertFalse(result)

    @patch("shutil.rmtree")
    @patch("pathlib.Path.exists")
    def test_remove_directory_exception(self, mock_exists, mock_rmtree):
        """Test directory removal with exception."""
        mock_exists.return_value = True
        mock_rmtree.side_effect = Exception("Permission denied")

        test_path = Path("test_dir")
        result = self.detector.remove_directory(test_path)

        self.assertFalse(result)

    @patch("shutil.copy2")
    @patch("pathlib.Path.mkdir")
    def test_copy_file_success(self, mock_mkdir, mock_copy):
        """Test successful file copying."""
        src = Path("src.txt")
        dst = Path("dst/dst.txt")

        result = self.detector.copy_file(src, dst)

        self.assertTrue(result)
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_copy.assert_called_once_with(src, dst)

    @patch("shutil.copy2")
    @patch("pathlib.Path.mkdir")
    def test_copy_file_exception(self, mock_mkdir, mock_copy):
        """Test file copying with exception."""
        mock_copy.side_effect = Exception("Permission denied")

        src = Path("src.txt")
        dst = Path("dst.txt")

        result = self.detector.copy_file(src, dst)
        self.assertFalse(result)

    def test_make_executable_windows(self):
        """Test making file executable on Windows."""
        with patch.object(self.detector, "is_windows", return_value=True):
            result = self.detector.make_executable(Path("test.py"))
            self.assertTrue(result)  # Windows always returns True

    @patch("pathlib.Path.stat")
    @patch("pathlib.Path.chmod")
    def test_make_executable_unix_success(self, mock_chmod, mock_stat):
        """Test making file executable on Unix."""
        import stat

        mock_stat.return_value = Mock(st_mode=0o644)

        with patch.object(self.detector, "is_windows", return_value=False):
            result = self.detector.make_executable(Path("test.py"))

        self.assertTrue(result)
        mock_chmod.assert_called_once_with(0o644 | stat.S_IEXEC)

    @patch("pathlib.Path.chmod")
    def test_make_executable_unix_exception(self, mock_chmod):
        """Test making file executable on Unix with exception."""
        mock_chmod.side_effect = Exception("Permission denied")

        with patch.object(self.detector, "is_windows", return_value=False):
            result = self.detector.make_executable(Path("test.py"))

        self.assertFalse(result)


class TestPlatformUtilityFunctions(unittest.TestCase):
    """Test utility functions that use the global platform detector."""

    def test_get_platform(self):
        """Test get_platform function."""
        result = get_platform()
        self.assertIn(result, ["Windows", "macOS", "Linux", "Unknown"])

    def test_get_python_command(self):
        """Test get_python_command function."""
        result = get_python_command()
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_is_windows(self):
        """Test is_windows function."""
        result = is_windows()
        self.assertIsInstance(result, bool)

    def test_is_unix_like(self):
        """Test is_unix_like function."""
        result = is_unix_like()
        self.assertIsInstance(result, bool)

    @patch("rxiv_maker.utils.platform.subprocess.run")
    def test_run_platform_command(self, mock_run_command):
        """Test run_platform_command function."""
        mock_run_command.return_value = Mock(returncode=0)

        result = run_platform_command("echo test")

        mock_run_command.assert_called_once_with("echo test", shell=False)
        self.assertEqual(result.returncode, 0)


class TestPlatformDetectorEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for PlatformDetector."""

    def test_env_file_reading_with_malformed_content(self):
        """Test environment file reading with malformed content."""
        detector = PlatformDetector()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("VALID=value\n")
            f.write("NO_EQUALS_SIGN\n")
            f.write("=EMPTY_KEY\n")
            f.write("SPACE_IN_KEY =value\n")
            f.write("KEY= VALUE_WITH_SPACES \n")
            env_file = Path(f.name)

        try:
            result = detector.get_env_file_content(env_file)

            # Should handle malformed lines gracefully
            self.assertIn("VALID", result)
            self.assertEqual(result["VALID"], "value")
            self.assertIn("KEY", result)
            self.assertEqual(result["KEY"], "VALUE_WITH_SPACES")

        finally:
            env_file.unlink(missing_ok=True)

    def test_env_file_reading_exception_handling(self):
        """Test environment file reading with I/O exception."""
        detector = PlatformDetector()

        # Create a file that will cause an exception when read
        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = OSError("Permission denied")

            result = detector.get_env_file_content(Path("test.env"))
            self.assertEqual(result, {})

    @patch("shutil.which")
    def test_python_command_detection_edge_case(self, mock_which):
        """Test Python command detection with edge cases."""
        # Test when uv exists but venv python doesn't
        mock_which.return_value = None

        with patch.object(PlatformDetector, "get_venv_python_path", return_value=None):
            with patch.object(PlatformDetector, "is_windows", return_value=False):
                detector = PlatformDetector()
                self.assertEqual(detector.python_cmd, "python3")

    def test_venv_path_with_missing_executable(self):
        """Test venv path detection when directory exists but executable is missing."""
        detector = PlatformDetector()

        # Mock .venv directory exists but python executable doesn't
        with patch("pathlib.Path.exists", side_effect=lambda: False):
            result = detector.get_venv_python_path()
            self.assertIsNone(result)

    def test_concurrent_platform_detection(self):
        """Test that multiple PlatformDetector instances work correctly."""
        detector1 = PlatformDetector()
        detector2 = PlatformDetector()

        # Both should detect the same platform
        self.assertEqual(detector1.platform, detector2.platform)
        self.assertEqual(detector1.is_windows(), detector2.is_windows())

    @patch("subprocess.run")
    def test_command_execution_with_custom_kwargs(self, mock_run):
        """Test command execution with custom keyword arguments."""
        mock_run.return_value = Mock(returncode=0)
        detector = PlatformDetector()

        detector.run_command("test command", capture_output=True, text=True, timeout=30)

        mock_run.assert_called_once_with("test command", shell=False, capture_output=True, text=True, timeout=30)


class TestUnicodeEncoding(unittest.TestCase):
    """Test Unicode encoding handling for cross-platform compatibility."""

    def test_safe_print_with_unicode_support(self):
        """Test safe_print when terminal supports Unicode."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.encoding = "utf-8"

            with patch("builtins.print") as mock_print:
                safe_print("Test message")

                # Should print with Unicode emoji
                mock_print.assert_called_once_with("✅ Test message")

    def test_safe_print_without_unicode_support(self):
        """Test safe_print when terminal doesn't support Unicode."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.encoding = None  # No encoding support

            with patch("builtins.print") as mock_print:
                safe_print("Test message")

                # Should print with ASCII fallback when no encoding
                mock_print.assert_called_once_with("[OK] Test message")

    def test_safe_print_no_encoding(self):
        """Test safe_print when stdout has no encoding."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.encoding = None

            with patch("builtins.print") as mock_print:
                safe_print("Test message")

                # Should use ASCII fallback
                mock_print.assert_called_once_with("[OK] Test message")

    def test_safe_print_custom_symbols(self):
        """Test safe_print with custom symbols."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.encoding = "utf-8"

            with patch("builtins.print") as mock_print:
                safe_print("Test message", success_symbol="🎉", fallback_symbol="[SUCCESS]")

                # Should print with custom Unicode symbol
                mock_print.assert_called_once_with("🎉 Test message")

    def test_safe_console_print_unicode_success(self):
        """Test safe_console_print when Unicode works."""
        mock_console = Mock()

        safe_console_print(mock_console, "✅ Test message", style="green")

        mock_console.print.assert_called_once_with("✅ Test message", style="green")

    def test_safe_console_print_unicode_fallback(self):
        """Test safe_console_print when Unicode fails."""
        mock_console = Mock()
        mock_console.print.side_effect = [
            UnicodeEncodeError("charmap", "✅", 0, 1, "undefined"),
            None,
        ]

        with patch("builtins.print"):
            safe_console_print(mock_console, "✅ Test message", style="green")

            # Should try Rich console with ASCII first
            self.assertEqual(mock_console.print.call_count, 2)
            second_call = mock_console.print.call_args_list[1]
            self.assertEqual(second_call[0][0], "[OK] Test message")

    def test_safe_console_print_double_fallback(self):
        """Test safe_console_print when both Rich attempts fail."""
        mock_console = Mock()
        mock_console.print.side_effect = UnicodeEncodeError("charmap", "✅", 0, 1, "undefined")

        with patch("builtins.print") as mock_print:
            safe_console_print(mock_console, "✅ Test message", style="green")

            # Should fall back to plain print
            mock_print.assert_called_once_with("[OK] Test message")

    def test_convert_to_ascii_basic_emojis(self):
        """Test ASCII conversion of basic emojis."""
        test_cases = [
            ("✅ Success", "[OK] Success"),
            ("❌ Error", "[ERROR] Error"),
            ("🔍 Searching", "[SEARCH] Searching"),
            ("📦 Package", "[PACKAGE] Package"),
            ("⚠️ Warning", "[WARNING] Warning"),
            ("🐍 Python", "[PYTHON] Python"),
            ("🐳 Docker", "[DOCKER] Docker"),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = _convert_to_ascii(input_text)
                self.assertEqual(result, expected)

    def test_convert_to_ascii_arrows(self):
        """Test ASCII conversion of arrow symbols."""
        test_cases = [
            ("A → B", "A -> B"),
            ("B ← A", "B <- A"),
            ("Up ↑", "Up ^"),
            ("Down ↓", "Down v"),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = _convert_to_ascii(input_text)
                self.assertEqual(result, expected)

    def test_convert_to_ascii_mixed_content(self):
        """Test ASCII conversion with mixed Unicode and ASCII content."""
        input_text = "🔍 Searching for 📦 package → version 1.0.0 ✅"
        expected = "[SEARCH] Searching for [PACKAGE] package -> version 1.0.0 [OK]"

        result = _convert_to_ascii(input_text)
        self.assertEqual(result, expected)

    def test_convert_to_ascii_no_unicode(self):
        """Test ASCII conversion with no Unicode content."""
        input_text = "Regular ASCII text with no emojis"
        expected = input_text  # Should remain unchanged

        result = _convert_to_ascii(input_text)
        self.assertEqual(result, expected)

    def test_convert_to_ascii_unknown_emoji(self):
        """Test ASCII conversion with unknown emoji."""
        # Use an emoji that's not in our replacement dict
        input_text = "Unknown emoji: 🦄"
        expected = input_text  # Should remain unchanged if not in replacement dict

        result = _convert_to_ascii(input_text)
        self.assertEqual(result, expected)

    def test_safe_print_ascii_encoding(self):
        """Test safe_print with ASCII encoding."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.encoding = "ascii"

            with patch("builtins.print") as mock_print:
                # Test with ASCII-only content - should work normally
                safe_print("Test message", success_symbol="[OK]", fallback_symbol="[OK]")

                # Should use the success symbol since it's ASCII
                mock_print.assert_called_once_with("[OK] Test message")

    def test_safe_console_print_with_table_object(self):
        """Test safe_console_print with Rich table objects."""
        mock_console = Mock()
        mock_table = Mock()
        mock_table.__str__ = Mock(return_value="Table content")

        safe_console_print(mock_console, mock_table, style="blue")

        mock_console.print.assert_called_once_with(mock_table, style="blue")

    def test_safe_console_print_with_kwargs(self):
        """Test safe_console_print with additional keyword arguments."""
        mock_console = Mock()

        safe_console_print(mock_console, "Test message", style="green", highlight=True, markup=False)

        mock_console.print.assert_called_once_with("Test message", style="green", highlight=True, markup=False)


if __name__ == "__main__":
    unittest.main()
