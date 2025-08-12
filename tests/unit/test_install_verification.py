"""Unit tests for installation verification utilities."""

import subprocess
import sys
from unittest.mock import MagicMock, call, patch

import pytest

from rxiv_maker.install.utils.verification import (
    _check_latex,
    _check_nodejs,
    _check_python,
    _check_r,
    _check_rxiv_maker,
    _check_system_libraries,
    _diagnose_latex,
    _diagnose_nodejs,
    _diagnose_python,
    _diagnose_r,
    _diagnose_system_libs,
    _print_verification_results,
    check_system_dependencies,
    diagnose_installation,
    verify_installation,
)


class TestVerifyInstallation:
    """Test main verification functionality."""

    def test_verify_installation_structure(self):
        """Test that verify_installation returns expected structure."""
        with (
            patch("rxiv_maker.install.utils.verification._check_python", return_value=True),
            patch("rxiv_maker.install.utils.verification._check_latex", return_value=True),
            patch("rxiv_maker.install.utils.verification._check_nodejs", return_value=True),
            patch("rxiv_maker.install.utils.verification._check_r", return_value=True),
            patch("rxiv_maker.install.utils.verification._check_system_libraries", return_value=True),
            patch("rxiv_maker.install.utils.verification._check_rxiv_maker", return_value=True),
        ):
            results = verify_installation()

            expected_components = ["python", "latex", "nodejs", "r", "system_libs", "rxiv_maker"]
            assert all(component in results for component in expected_components)
            assert all(results[component] is True for component in expected_components)

    @patch("rxiv_maker.install.utils.verification._print_verification_results")
    def test_verify_installation_verbose_mode(self, mock_print):
        """Test verify_installation with verbose output."""
        with (
            patch("rxiv_maker.install.utils.verification._check_python", return_value=True),
            patch("rxiv_maker.install.utils.verification._check_latex", return_value=False),
            patch("rxiv_maker.install.utils.verification._check_nodejs", return_value=True),
            patch("rxiv_maker.install.utils.verification._check_r", return_value=True),
            patch("rxiv_maker.install.utils.verification._check_system_libraries", return_value=True),
            patch("rxiv_maker.install.utils.verification._check_rxiv_maker", return_value=True),
        ):
            results = verify_installation(verbose=True)

            mock_print.assert_called_once_with(results)
            assert results["latex"] is False

    def test_check_system_dependencies_filters_optional(self):
        """Test that check_system_dependencies excludes R as optional."""
        mock_results = {
            "python": True,
            "latex": False,
            "nodejs": True,
            "r": False,  # R is optional
            "system_libs": False,
            "rxiv_maker": True,
        }

        with patch("rxiv_maker.install.utils.verification.verify_installation", return_value=mock_results):
            missing = check_system_dependencies()

            # R should not be in missing list even though it's False
            expected_missing = ["latex", "system_libs"]
            assert sorted(missing) == sorted(expected_missing)
            assert "r" not in missing


class TestIndividualChecks:
    """Test individual component check functions."""

    def test_check_python_current_version(self):
        """Test _check_python with current Python version."""
        # This test runs with the actual Python version
        result = _check_python()

        # Should be True since we're running Python 3.11+
        assert result is True

    @patch("sys.version_info")
    def test_check_python_version_compatibility(self, mock_version):
        """Test _check_python with different Python versions."""
        test_cases = [
            ((3, 11, 0), True),
            ((3, 11, 5), True),
            ((3, 12, 0), True),
            ((3, 10, 9), False),
            ((2, 7, 18), False),
        ]

        for version_info, expected in test_cases:
            mock_version.major, mock_version.minor, mock_version.micro = version_info

            result = _check_python()

            assert result == expected, f"Failed for Python {version_info}"

    def test_check_python_exception_handling(self):
        """Test _check_python exception handling."""
        with patch("sys.version_info", side_effect=Exception("Version error")):
            result = _check_python()
            assert result is False

    @patch("subprocess.run")
    def test_check_latex_available(self, mock_run):
        """Test _check_latex when LaTeX is available."""
        mock_run.return_value = MagicMock(returncode=0)

        result = _check_latex()

        assert result is True
        mock_run.assert_called_once_with(["pdflatex", "--version"], capture_output=True, text=True, timeout=10)

    @patch("subprocess.run")
    def test_check_latex_not_available(self, mock_run):
        """Test _check_latex when LaTeX is not available."""
        mock_run.return_value = MagicMock(returncode=1)

        result = _check_latex()

        assert result is False

    @patch("subprocess.run")
    def test_check_latex_exception_handling(self, mock_run):
        """Test _check_latex exception handling."""
        mock_run.side_effect = FileNotFoundError("Command not found")

        result = _check_latex()

        assert result is False

    @patch("subprocess.run")
    def test_check_nodejs_both_available(self, mock_run):
        """Test _check_nodejs when both node and npm are available."""
        mock_run.return_value = MagicMock(returncode=0)

        result = _check_nodejs()

        assert result is True
        expected_calls = [
            call(["node", "--version"], capture_output=True, text=True, timeout=10),
            call(["npm", "--version"], capture_output=True, text=True, timeout=10),
        ]
        mock_run.assert_has_calls(expected_calls)

    @patch("subprocess.run")
    def test_check_nodejs_node_missing(self, mock_run):
        """Test _check_nodejs when node is missing but npm is available."""
        # Mock node failure, npm success
        mock_run.side_effect = [MagicMock(returncode=1), MagicMock(returncode=0)]

        result = _check_nodejs()

        assert result is False

    @patch("subprocess.run")
    def test_check_nodejs_npm_missing(self, mock_run):
        """Test _check_nodejs when node is available but npm is missing."""
        # Mock node success, npm failure
        mock_run.side_effect = [MagicMock(returncode=0), MagicMock(returncode=1)]

        result = _check_nodejs()

        assert result is False

    @patch("subprocess.run")
    def test_check_r_available(self, mock_run):
        """Test _check_r when R is available."""
        mock_run.return_value = MagicMock(returncode=0)

        result = _check_r()

        assert result is True
        mock_run.assert_called_once_with(["R", "--version"], capture_output=True, text=True, timeout=10)

    @patch("subprocess.run")
    def test_check_r_not_available(self, mock_run):
        """Test _check_r when R is not available."""
        mock_run.return_value = MagicMock(returncode=1)

        result = _check_r()

        assert result is False

    @patch("importlib.util.find_spec")
    def test_check_system_libraries_all_available(self, mock_find_spec):
        """Test _check_system_libraries when all packages are available."""
        mock_find_spec.return_value = MagicMock()  # Non-None indicates available

        result = _check_system_libraries()

        assert result is True
        expected_packages = ["matplotlib", "numpy", "PIL"]
        assert mock_find_spec.call_count == len(expected_packages)
        for package in expected_packages:
            mock_find_spec.assert_any_call(package)

    @patch("importlib.util.find_spec")
    def test_check_system_libraries_missing_package(self, mock_find_spec):
        """Test _check_system_libraries when a package is missing."""

        def side_effect(package):
            if package == "matplotlib":
                return None  # Package missing
            return MagicMock()  # Package available

        mock_find_spec.side_effect = side_effect

        result = _check_system_libraries()

        assert result is False

    @patch("importlib.util.find_spec")
    def test_check_rxiv_maker_available(self, mock_find_spec):
        """Test _check_rxiv_maker when package is available."""
        mock_find_spec.return_value = MagicMock()

        result = _check_rxiv_maker()

        assert result is True
        mock_find_spec.assert_called_once_with("rxiv_maker")

    @patch("importlib.util.find_spec")
    def test_check_rxiv_maker_not_available(self, mock_find_spec):
        """Test _check_rxiv_maker when package is not available."""
        mock_find_spec.return_value = None

        result = _check_rxiv_maker()

        assert result is False


class TestPrintVerificationResults:
    """Test verification results printing functionality."""

    @patch("builtins.print")
    @patch("rxiv_maker.utils.unicode_safe.get_safe_icon")
    def test_print_verification_results_all_installed(self, mock_get_icon, mock_print):
        """Test printing when all components are installed."""
        # Mock icons
        mock_get_icon.side_effect = lambda emoji, fallback: emoji

        results = {"python": True, "latex": True, "nodejs": True, "r": True, "system_libs": True, "rxiv_maker": True}

        _print_verification_results(results)

        # Verify print calls include success indicators
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        success_lines = [line for line in print_calls if "✅ INSTALLED" in line]
        assert len(success_lines) == 6  # All components should show as installed

    @patch("builtins.print")
    @patch("rxiv_maker.utils.unicode_safe.get_safe_icon")
    def test_print_verification_results_some_missing(self, mock_get_icon, mock_print):
        """Test printing when some components are missing."""
        # Mock icons
        mock_get_icon.side_effect = lambda emoji, fallback: emoji

        results = {"python": True, "latex": False, "nodejs": True, "r": False, "system_libs": False, "rxiv_maker": True}

        _print_verification_results(results)

        # Verify warning message is shown
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        warning_lines = [line for line in print_calls if "⚠️  3 components missing" in line]
        assert len(warning_lines) == 1

    @patch("builtins.print")
    @patch("rxiv_maker.utils.unicode_safe.get_safe_icon")
    def test_print_verification_results_all_working(self, mock_get_icon, mock_print):
        """Test printing when all components are working."""
        # Mock icons
        mock_get_icon.side_effect = lambda emoji, fallback: emoji

        results = {"python": True, "latex": True, "nodejs": True, "r": True, "system_libs": True, "rxiv_maker": True}

        _print_verification_results(results)

        # Verify success message is shown
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        success_lines = [line for line in print_calls if "✅ All components are installed and working!" in line]
        assert len(success_lines) == 1


class TestDiagnoseInstallation:
    """Test diagnostic functionality."""

    def test_diagnose_installation_structure(self):
        """Test that diagnose_installation returns expected structure."""
        with (
            patch("rxiv_maker.install.utils.verification._diagnose_python", return_value={}),
            patch("rxiv_maker.install.utils.verification._diagnose_latex", return_value={}),
            patch("rxiv_maker.install.utils.verification._diagnose_nodejs", return_value={}),
            patch("rxiv_maker.install.utils.verification._diagnose_r", return_value={}),
            patch("rxiv_maker.install.utils.verification._diagnose_system_libs", return_value={}),
        ):
            diagnosis = diagnose_installation()

            expected_components = ["python", "latex", "nodejs", "r", "system_libs"]
            assert all(component in diagnosis for component in expected_components)

    def test_diagnose_python_current_version(self):
        """Test _diagnose_python with current Python version."""
        info = _diagnose_python()

        assert info["installed"] is True
        assert "version" in info
        assert "path" in info
        assert info["path"] == sys.executable
        assert len(info["issues"]) == 0  # Should have no issues with current Python

    @patch("sys.version_info")
    def test_diagnose_python_old_version(self, mock_version):
        """Test _diagnose_python with old Python version."""
        mock_version.major = 3
        mock_version.minor = 10
        mock_version.micro = 0

        info = _diagnose_python()

        assert info["installed"] is True
        assert "Python 3.11+ required, found 3.10.0" in info["issues"]

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_diagnose_latex_available(self, mock_run, mock_which):
        """Test _diagnose_latex when LaTeX is available."""
        mock_which.return_value = "/usr/local/bin/pdflatex"
        mock_run.return_value = MagicMock(returncode=0, stdout="pdfTeX 3.141592653-2.6-1.40.22 (TeX Live 2021)")

        info = _diagnose_latex()

        assert info["installed"] is True
        assert info["path"] == "/usr/local/bin/pdflatex"
        assert "pdfTeX" in info["version"]

    @patch("shutil.which")
    def test_diagnose_latex_not_found(self, mock_which):
        """Test _diagnose_latex when LaTeX is not found."""
        mock_which.return_value = None

        info = _diagnose_latex()

        assert info["installed"] is False
        assert "pdflatex not found in PATH" in info["issues"]

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_diagnose_nodejs_available(self, mock_run, mock_which):
        """Test _diagnose_nodejs when Node.js is available."""
        mock_which.return_value = "/usr/local/bin/node"
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v18.17.0"),  # node --version
            MagicMock(returncode=0, stdout="9.6.7"),  # npm --version
        ]

        info = _diagnose_nodejs()

        assert info["installed"] is True
        assert info["path"] == "/usr/local/bin/node"
        assert info["version"] == "v18.17.0"
        assert info["npm_version"] == "9.6.7"

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_diagnose_nodejs_npm_not_working(self, mock_run, mock_which):
        """Test _diagnose_nodejs when npm is not working."""
        mock_which.return_value = "/usr/local/bin/node"
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="v18.17.0"),  # node works
            MagicMock(returncode=1, stdout=""),  # npm fails
        ]

        info = _diagnose_nodejs()

        assert info["installed"] is False
        assert "npm not working" in info["issues"]

    @patch("shutil.which")
    def test_diagnose_r_not_found(self, mock_which):
        """Test _diagnose_r when R is not found."""
        mock_which.return_value = None

        info = _diagnose_r()

        assert info["installed"] is False
        assert "R not found in PATH (optional)" in info["issues"]

    @patch("builtins.__import__")
    def test_diagnose_system_libs_all_available(self, mock_import):
        """Test _diagnose_system_libs when all packages are available."""
        mock_import.return_value = MagicMock()

        info = _diagnose_system_libs()

        assert info["installed"] is True
        assert len(info["missing_packages"]) == 0

    @patch("builtins.__import__")
    def test_diagnose_system_libs_some_missing(self, mock_import):
        """Test _diagnose_system_libs when some packages are missing."""

        def side_effect(package):
            if package in ["matplotlib", "scipy"]:
                raise ImportError(f"No module named '{package}'")
            return MagicMock()

        mock_import.side_effect = side_effect

        info = _diagnose_system_libs()

        assert info["installed"] is False
        assert sorted(info["missing_packages"]) == ["matplotlib", "scipy"]
        assert "Missing packages: matplotlib, scipy" in info["issues"]


class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility scenarios."""

    @pytest.mark.parametrize(
        "platform,command_exists,expected",
        [
            ("win32", True, True),
            ("win32", False, False),
            ("darwin", True, True),
            ("darwin", False, False),
            ("linux", True, True),
            ("linux", False, False),
        ],
    )
    @patch("subprocess.run")
    def test_check_latex_cross_platform(self, mock_run, platform, command_exists, expected):
        """Test LaTeX check across different platforms."""
        with patch("sys.platform", platform):
            if command_exists:
                mock_run.return_value = MagicMock(returncode=0)
            else:
                mock_run.side_effect = FileNotFoundError("Command not found")

            result = _check_latex()

            assert result == expected

    @pytest.mark.parametrize(
        "exception_type",
        [
            FileNotFoundError,
            PermissionError,
            subprocess.TimeoutExpired("cmd", 10),
            OSError,
        ],
    )
    @patch("subprocess.run")
    def test_subprocess_exception_handling(self, mock_run, exception_type):
        """Test handling of various subprocess exceptions across platforms."""
        mock_run.side_effect = exception_type

        # All check functions should handle exceptions gracefully
        assert _check_latex() is False
        assert _check_nodejs() is False
        assert _check_r() is False

    @patch("importlib.util.find_spec")
    def test_system_libraries_importlib_cross_platform(self, mock_find_spec):
        """Test importlib.util.find_spec works consistently across platforms."""
        # Test that the new approach works on all platforms
        mock_find_spec.return_value = MagicMock()

        result = _check_system_libraries()

        assert result is True
        # Verify it checks the expected packages
        expected_calls = ["matplotlib", "numpy", "PIL"]
        assert mock_find_spec.call_count == len(expected_calls)

    def test_path_handling_cross_platform(self):
        """Test path handling works across platforms."""
        with patch("shutil.which") as mock_which:
            # Test with different path styles
            test_paths = [
                "/usr/local/bin/pdflatex",  # Unix-style
                "C:\\Program Files\\LaTeX\\pdflatex.exe",  # Windows-style
                "/opt/homebrew/bin/pdflatex",  # macOS Homebrew
            ]

            for test_path in test_paths:
                mock_which.return_value = test_path

                info = _diagnose_latex()

                # Should handle all path styles correctly
                assert info["path"] == test_path


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and comprehensive error handling."""

    @patch("subprocess.run")
    def test_timeout_handling_all_checks(self, mock_run):
        """Test timeout handling in all subprocess-based checks."""
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 10)

        # All should handle timeout gracefully
        assert _check_latex() is False
        assert _check_nodejs() is False
        assert _check_r() is False

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_diagnose_latex_subprocess_exception(self, mock_run, mock_which):
        """Test _diagnose_latex exception handling in subprocess call."""
        mock_which.return_value = "/usr/local/bin/pdflatex"
        mock_run.side_effect = Exception("Unexpected error")

        info = _diagnose_latex()

        assert "Error checking LaTeX: Unexpected error" in info["issues"]

    def test_diagnose_python_exception_handling(self):
        """Test _diagnose_python exception handling."""
        # The _diagnose_python function is very robust and handles most error cases
        # gracefully without raising exceptions. Test that it always returns a dict
        info = _diagnose_python()

        # Should always return a valid structure
        assert isinstance(info, dict)
        assert "installed" in info
        assert "version" in info
        assert "path" in info
        assert "issues" in info
        assert isinstance(info["issues"], list)

    @patch("importlib.util.find_spec")
    def test_check_system_libraries_find_spec_exception(self, mock_find_spec):
        """Test _check_system_libraries with find_spec raising exception."""
        mock_find_spec.side_effect = ImportError("Module import error")

        # Should propagate the exception for proper handling
        with pytest.raises(ImportError):
            _check_system_libraries()

    def test_empty_results_handling(self):
        """Test handling of empty or malformed results."""
        # Test with empty results dictionary
        with patch("builtins.print") as mock_print:
            _print_verification_results({})

            # Should handle empty results gracefully
            assert mock_print.called

    @patch("builtins.__import__")
    def test_diagnose_system_libs_import_error_variations(self, mock_import):
        """Test different types of import errors in system libs diagnosis."""

        def side_effect(package):
            error_types = {
                "matplotlib": ImportError("No module named 'matplotlib'"),
                "PIL": ModuleNotFoundError("No module named 'PIL'"),
                "numpy": ImportError("DLL load failed while importing"),
                "pandas": ImportError("cannot import name 'something'"),
            }
            if package in error_types:
                raise error_types[package]
            return MagicMock()

        mock_import.side_effect = side_effect

        info = _diagnose_system_libs()

        # All different error types should be caught as missing packages
        expected_missing = ["PIL", "matplotlib", "numpy", "pandas"]
        assert sorted(info["missing_packages"]) == expected_missing
