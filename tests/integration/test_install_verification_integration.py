"""Integration tests for installation verification workflow."""

import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

from rxiv_maker.install.dependency_handlers.system_libs import SystemLibsHandler
from rxiv_maker.install.utils.logging import InstallLogger
from rxiv_maker.install.utils.verification import (
    check_system_dependencies,
    diagnose_installation,
    verify_installation,
)


@pytest.mark.integration
class TestInstallationVerificationWorkflow:
    """Test complete installation verification workflow."""

    def test_full_verification_workflow_success(self):
        """Test complete verification workflow when all components are available."""
        # Mock all components as available
        with (
            patch("rxiv_maker.install.utils.verification._check_python", return_value=True),
            patch("rxiv_maker.install.utils.verification._check_latex", return_value=True),
            patch("rxiv_maker.install.utils.verification._check_nodejs", return_value=True),
            patch("rxiv_maker.install.utils.verification._check_r", return_value=True),
            patch("rxiv_maker.install.utils.verification._check_system_libraries", return_value=True),
            patch("rxiv_maker.install.utils.verification._check_rxiv_maker", return_value=True),
        ):
            # Run verification
            results = verify_installation(verbose=False)
            missing = check_system_dependencies()
            diagnosis = diagnose_installation()

            # Verify results structure
            expected_components = ["python", "latex", "nodejs", "r", "system_libs", "rxiv_maker"]
            assert all(component in results for component in expected_components)
            assert all(results[component] for component in expected_components)

            # No missing dependencies
            assert missing == []

            # Diagnosis should show core components (diagnosis doesn't include rxiv_maker)
            diagnosis_components = ["python", "latex", "nodejs", "r", "system_libs"]
            assert all(component in diagnosis for component in diagnosis_components)

    def test_verification_workflow_with_missing_components(self):
        """Test verification workflow when some components are missing."""
        # Mock some components as missing
        with (
            patch("rxiv_maker.install.utils.verification._check_python", return_value=True),
            patch("rxiv_maker.install.utils.verification._check_latex", return_value=False),
            patch("rxiv_maker.install.utils.verification._check_nodejs", return_value=False),
            patch("rxiv_maker.install.utils.verification._check_r", return_value=True),
            patch("rxiv_maker.install.utils.verification._check_system_libraries", return_value=True),
            patch("rxiv_maker.install.utils.verification._check_rxiv_maker", return_value=True),
        ):
            # Run verification
            results = verify_installation(verbose=False)
            missing = check_system_dependencies()

            # Verify missing components are identified
            assert results["latex"] is False
            assert results["nodejs"] is False
            assert results["python"] is True
            assert results["r"] is True  # R is optional

            # Missing should exclude R (optional component)
            expected_missing = ["latex", "nodejs"]
            assert sorted(missing) == sorted(expected_missing)
            assert "r" not in missing

    def test_system_libs_handler_integration(self):
        """Test SystemLibsHandler integration with verification system."""
        mock_logger = MagicMock(spec=InstallLogger)
        handler = SystemLibsHandler(mock_logger)

        # Test importlib.util.find_spec integration
        with patch("importlib.util.find_spec") as mock_find_spec:
            # Mock some packages as available, some as missing
            def side_effect(package):
                if package in ["matplotlib", "numpy"]:
                    return MagicMock()  # Available
                return None  # Missing

            mock_find_spec.side_effect = side_effect

            # Test verification
            verification_result = handler.verify_installation()
            handler.get_missing_packages()  # Just call it for side effects

            assert verification_result is False  # Should fail due to missing packages

            # Test that get_missing_packages uses __import__ (different from verify_installation)
            with patch("builtins.__import__") as mock_import:

                def import_side_effect(package):
                    if package in ["PIL", "scipy"]:
                        raise ImportError(f"No module named '{package}'")
                    return MagicMock()

                mock_import.side_effect = import_side_effect
                missing = handler.get_missing_packages()
                expected_missing = ["PIL", "scipy"]
                assert sorted(missing) == sorted(expected_missing)

    def test_python_version_compatibility_integration(self):
        """Test Python version compatibility across different verification points."""
        mock_logger = MagicMock(spec=InstallLogger)
        handler = SystemLibsHandler(mock_logger)

        # Test with different Python versions
        test_versions = [
            ((3, 11, 0), True),
            ((3, 11, 5), True),
            ((3, 12, 0), True),
            ((3, 10, 9), False),
        ]

        for (major, minor, micro), expected in test_versions:
            with patch("sys.version_info") as mock_version:
                mock_version.major = major
                mock_version.minor = minor
                mock_version.micro = micro

                # Test handler method
                handler_result = handler.check_python_compatibility()

                # Test verification module function
                with patch("rxiv_maker.install.utils.verification._check_python") as mock_check:
                    mock_check.return_value = expected
                    verification_results = verify_installation()

                    assert handler_result == expected
                    assert verification_results["python"] == expected

    @pytest.mark.parametrize(
        "subprocess_exception",
        [
            subprocess.TimeoutExpired("cmd", 10),
            FileNotFoundError("Command not found"),
            PermissionError("Access denied"),
            OSError("System error"),
        ],
    )
    def test_subprocess_error_handling_integration(self, subprocess_exception):
        """Test integration of subprocess error handling across components."""
        with patch("subprocess.run", side_effect=subprocess_exception):
            # All subprocess-based checks should handle errors gracefully
            results = verify_installation(verbose=False)
            diagnosis = diagnose_installation()

            # LaTeX, Node.js, and R checks should all fail gracefully
            assert results["latex"] is False
            assert results["nodejs"] is False
            assert results["r"] is False

            # Diagnosis should capture error information
            assert "issues" in diagnosis["latex"]
            assert "issues" in diagnosis["nodejs"]
            assert "issues" in diagnosis["r"]

    def test_cross_platform_path_handling_integration(self):
        """Test cross-platform path handling in verification and diagnosis."""
        test_paths = [
            "/usr/local/bin/pdflatex",  # Unix-style
            "C:\\Program Files\\LaTeX\\pdflatex.exe",  # Windows-style
            "/opt/homebrew/bin/pdflatex",  # macOS Homebrew
        ]

        for test_path in test_paths:
            with (
                patch("shutil.which", return_value=test_path),
                patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="pdfTeX 3.141592653")),
            ):
                diagnosis = diagnose_installation()

                # Should handle all path styles correctly
                assert diagnosis["latex"]["path"] == test_path
                assert diagnosis["latex"]["installed"] is True

    def test_importlib_find_spec_vs_import_consistency(self):
        """Test consistency between importlib.util.find_spec and __import__ approaches."""
        # Test packages that exist vs don't exist
        real_packages = ["sys", "os", "pathlib"]  # These should always exist
        fake_packages = ["nonexistent_package_12345", "fake_module_xyz"]

        for package in real_packages:
            # Test find_spec approach
            import importlib.util

            find_spec_result = importlib.util.find_spec(package)

            # Test import approach
            try:
                __import__(package)
                import_success = True
            except ImportError:
                import_success = False

            # Results should be consistent
            assert (find_spec_result is not None) == import_success

        for package in fake_packages:
            # Test find_spec approach
            import importlib.util

            find_spec_result = importlib.util.find_spec(package)

            # Test import approach
            try:
                __import__(package)
                import_success = True
            except ImportError:
                import_success = False

            # Results should be consistent (both should fail)
            assert (find_spec_result is not None) == import_success
            assert find_spec_result is None
            assert import_success is False

    def test_verification_with_real_python_environment(self):
        """Test verification using the real Python environment."""
        # This test runs with the actual environment
        results = verify_installation(verbose=False)

        # Python should always be available (we're running it)
        assert results["python"] is True

        # rxiv_maker should be available (we're testing it)
        assert results["rxiv_maker"] is True

        # Get detailed diagnosis
        diagnosis = diagnose_installation()

        # Python diagnosis should be complete
        python_info = diagnosis["python"]
        assert python_info["installed"] is True
        assert python_info["version"] is not None
        assert python_info["path"] == sys.executable
        assert len(python_info["issues"]) == 0  # Current Python should have no issues

    def test_missing_components_error_reporting(self):
        """Test error reporting for missing components."""
        # Mock specific failure scenarios
        with patch("subprocess.run") as mock_run:
            # Mock different failure types
            def run_side_effect(cmd, **kwargs):
                if "pdflatex" in cmd:
                    raise FileNotFoundError("pdflatex not found")
                elif "node" in cmd:
                    return MagicMock(returncode=1, stderr="node: command not found")
                elif "R" in cmd:
                    raise PermissionError("Access denied")
                return MagicMock(returncode=0)

            mock_run.side_effect = run_side_effect

            diagnosis = diagnose_installation()

            # Each component should report specific issues (accept both error formats)
            latex_error = diagnosis["latex"]["issues"][0]
            assert "Error checking LaTeX" in latex_error or "pdflatex not found in PATH" in latex_error
            assert diagnosis["nodejs"]["installed"] is False
            assert "Error checking R" in diagnosis["r"]["issues"][0]

    def test_packaging_library_fallback_integration(self):
        """Test packaging library fallback behavior integration."""
        mock_logger = MagicMock(spec=InstallLogger)
        handler = SystemLibsHandler(mock_logger)

        # Test with packaging library available
        with (
            patch("rxiv_maker.install.dependency_handlers.system_libs.HAS_PACKAGING", True),
            patch("rxiv_maker.install.dependency_handlers.system_libs.version") as mock_version,
        ):
            # Mock successful version comparison
            mock_version.parse.return_value.__ge__ = MagicMock(return_value=True)

            result = handler.check_python_compatibility()
            assert result is True

            details = handler.get_python_version_details()
            assert details["version_parser"] == "packaging"

        # Test with packaging library causing exception (fallback)
        with (
            patch("rxiv_maker.install.dependency_handlers.system_libs.HAS_PACKAGING", True),
            patch("rxiv_maker.install.dependency_handlers.system_libs.version") as mock_version,
        ):
            mock_version.parse.side_effect = Exception("Parsing error")

            result = handler.check_python_compatibility()
            # Should still work using fallback
            assert result is True  # Current Python should pass

            # Should log the fallback
            handler.logger.debug.assert_called_with("Error parsing version with packaging library: Parsing error")


@pytest.mark.integration
class TestInstallationVerificationPerformance:
    """Test performance aspects of installation verification."""

    def test_verification_performance_reasonable_time(self):
        """Test that verification completes in reasonable time."""
        import time

        start_time = time.time()

        # Run full verification
        results = verify_installation(verbose=False)
        diagnosis = diagnose_installation()

        end_time = time.time()
        elapsed = end_time - start_time

        # Should complete within 10 seconds even with real subprocess calls
        assert elapsed < 10.0, f"Verification took too long: {elapsed:.2f} seconds"

        # Should have checked all expected components
        assert len(results) >= 6
        assert len(diagnosis) >= 5

    def test_system_libraries_check_performance(self):
        """Test that system libraries check is performant."""
        import time

        mock_logger = MagicMock(spec=InstallLogger)
        handler = SystemLibsHandler(mock_logger)

        start_time = time.time()

        # Run multiple checks
        for _ in range(10):
            handler.verify_installation()
            handler.get_missing_packages()
            handler.check_python_compatibility()

        end_time = time.time()
        elapsed = end_time - start_time

        # 10 iterations should complete quickly
        assert elapsed < 1.0, f"System libraries checks too slow: {elapsed:.2f} seconds"

    def test_diagnosis_caching_behavior(self):
        """Test that diagnosis doesn't perform unnecessary repeated work."""
        # Mock expensive operations
        expensive_call_count = 0

        def mock_expensive_subprocess(*args, **kwargs):
            nonlocal expensive_call_count
            expensive_call_count += 1
            import time

            time.sleep(0.01)  # Simulate slow call
            return MagicMock(returncode=0, stdout="version info")

        with (
            patch("subprocess.run", side_effect=mock_expensive_subprocess),
            patch("shutil.which", return_value="/usr/bin/tool"),
        ):
            # Run diagnosis multiple times
            for _ in range(3):
                diagnose_installation()  # Just call for side effects

            # Each run should make fresh calls (no caching expected in current implementation)
            # But the number should be predictable
            assert expensive_call_count > 0
            assert expensive_call_count <= 21  # 3 runs * 7 potential subprocess calls per run


@pytest.mark.integration
class TestInstallationVerificationEdgeCases:
    """Test edge cases in installation verification integration."""

    def test_partial_installation_scenarios(self):
        """Test scenarios where only some components are partially installed."""
        # Scenario: LaTeX installed but some packages missing
        with patch("subprocess.run") as mock_run, patch("shutil.which") as mock_which:

            def run_side_effect(cmd, **kwargs):
                if "pdflatex" in cmd and "--version" in cmd:
                    return MagicMock(returncode=0, stdout="pdfTeX version")
                elif "tlmgr" in cmd or "miktex" in cmd:
                    return MagicMock(returncode=1, stderr="Package not found")
                else:
                    return MagicMock(returncode=0)

            mock_run.side_effect = run_side_effect

            # Mock shutil.which to return valid paths for tools we want to simulate as installed
            def which_side_effect(cmd):
                if cmd == "pdflatex":
                    return "/usr/bin/pdflatex"  # Simulate pdflatex is available
                return None  # Other commands not found

            mock_which.side_effect = which_side_effect

            results = verify_installation()
            diagnosis = diagnose_installation()

            # LaTeX should be detected as installed
            assert results["latex"] is True
            assert diagnosis["latex"]["installed"] is True

    def test_environment_variable_interaction(self):
        """Test verification behavior with different environment variables."""
        import os

        # Test with modified PATH
        original_path = os.environ.get("PATH", "")

        try:
            # Add fake path
            os.environ["PATH"] = "/fake/path:" + original_path

            # Verification should still work
            results = verify_installation()

            # Python should still be found (we're running it)
            assert results["python"] is True

        finally:
            os.environ["PATH"] = original_path

    def test_unicode_and_special_characters_handling(self):
        """Test handling of unicode and special characters in paths and output."""
        # Test with paths containing special characters
        special_paths = [
            "/Users/Jürgen/bin/pdflatex",  # Unicode
            "/Program Files (x86)/LaTeX/pdflatex.exe",  # Spaces and parentheses
            "/opt/texlive/2023/bin/x86_64-linux/pdflatex",  # Long path
        ]

        for special_path in special_paths:
            with patch("shutil.which", return_value=special_path), patch("subprocess.run") as mock_run:
                # Mock command output with unicode
                mock_run.return_value = MagicMock(returncode=0, stdout="pdfTeX 3.14159265 (TeX Live 2023/Arch Linüx)")

                diagnosis = diagnose_installation()

                # Should handle special characters correctly
                assert diagnosis["latex"]["path"] == special_path
                assert diagnosis["latex"]["installed"] is True

    def test_concurrent_verification_safety(self):
        """Test that concurrent verification calls are safe."""
        import threading

        results = []
        errors = []

        def run_verification():
            try:
                result = verify_installation(verbose=False)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Run multiple verifications concurrently
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=run_verification)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)

        # All should complete without errors
        assert len(errors) == 0, f"Concurrent verification errors: {errors}"
        assert len(results) == 5

        # All results should be consistent
        first_result = results[0]
        for result in results[1:]:
            # Core components should be consistent across runs
            assert result["python"] == first_result["python"]
            assert result["rxiv_maker"] == first_result["rxiv_maker"]
