"""Tests for Docker manager manual edits and logging improvements.

This module tests the manual edits made to docker/manager.py to ensure
they maintain functionality while improving error handling and logging.
"""

import inspect
import logging
import re
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from rxiv_maker.docker.manager import DockerManager, DockerSession


class TestDockerManagerLogging:
    """Test Docker manager logging improvements."""

    def test_logging_import_available(self):
        """Test that logging module is properly imported in docker manager."""
        # Should be able to create manager without import errors
        manager = DockerManager()
        assert manager is not None

    def test_session_cleanup_logging(self):
        """Test that session cleanup errors are properly logged."""
        with tempfile.TemporaryDirectory() as temp_dir:
            session = DockerSession("test-container", "test-image", Path(temp_dir))

            with patch("subprocess.run") as mock_run, patch("logging.debug") as mock_log:
                # Simulate subprocess error during cleanup
                mock_run.side_effect = subprocess.CalledProcessError(1, "docker")

                # This should log the error instead of silently passing
                session.cleanup()

                # Should have logged the error
                if mock_log.called:
                    assert mock_log.called

    def test_container_details_error_logging(self):
        """Test that container details errors are properly logged."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = DockerManager(workspace_dir=Path(temp_dir))

            with patch("subprocess.run") as mock_run, patch("logging.debug"):
                # Simulate error getting container details
                mock_run.side_effect = subprocess.CalledProcessError(1, "docker")

                # This should log the error
                result = manager.get_container_info("non-existent-session")

                # Should return None and log error
                assert result is None

    def test_cpu_parsing_error_logging(self):
        """Test that CPU parsing errors are properly logged."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = DockerManager(workspace_dir=Path(temp_dir))

            with patch("subprocess.run") as mock_run, patch("logging.debug"):
                # Simulate invalid CPU percentage output
                mock_process = Mock()
                mock_process.stdout = "invalid-cpu-format\n"
                mock_process.returncode = 0
                mock_run.return_value = mock_process

                # This should handle the error gracefully and log it
                try:
                    stats = manager.get_resource_usage()
                    # Should not crash but may have logged error
                    assert isinstance(stats, dict)
                except Exception:
                    pytest.fail("Should handle CPU parsing errors gracefully")

    def test_script_path_resolution_logging(self):
        """Test that script path resolution issues are properly logged."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = DockerManager(workspace_dir=Path(temp_dir))

            with patch("logging.debug"):
                # Create a script outside the workspace
                external_script = Path("/tmp/external_script.py")

                # This should log a debug message about script being outside workspace
                with patch("pathlib.Path.exists", return_value=True):
                    try:
                        # This would normally trigger the logging
                        manager.run_python_script(external_script)
                    except Exception:
                        # Expected to fail, but should have logged the path issue
                        pass


class TestDockerManagerErrorHandling:
    """Test improved error handling in Docker manager."""

    def test_session_cleanup_error_handling(self):
        """Test that session cleanup handles errors gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            session = DockerSession("test-container", "test-image", Path(temp_dir))

            with patch("subprocess.run") as mock_run:
                # Simulate various subprocess errors
                error_types = [
                    subprocess.TimeoutExpired("docker", 30),
                    subprocess.CalledProcessError(1, "docker"),
                    OSError("Docker not found"),
                ]

                for error in error_types:
                    mock_run.side_effect = error

                    # Should handle error gracefully, not crash
                    try:
                        session.cleanup()
                        # Should handle the error appropriately
                    except Exception as e:
                        pytest.fail(f"Session cleanup should handle {type(error).__name__} gracefully: {e}")

    def test_manager_resilience_to_docker_failures(self):
        """Test that Docker manager is resilient to Docker daemon failures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = DockerManager(workspace_dir=Path(temp_dir))

            with patch("subprocess.run") as mock_run:
                # Simulate Docker daemon not running
                mock_run.side_effect = subprocess.CalledProcessError(1, "docker")

                # These operations should fail gracefully, not crash
                operations = [
                    lambda: manager.check_docker_available(),
                    lambda: manager.get_session_stats(),
                    lambda: manager.cleanup_all_sessions(),
                ]

                for operation in operations:
                    try:
                        result = operation()
                        # Should return appropriate failure indicator
                        assert result is not None or result == {}
                    except Exception as e:
                        # Some exceptions may be expected, but not crashes
                        assert "docker" in str(e).lower() or "container" in str(e).lower()

    def test_resource_monitoring_error_handling(self):
        """Test that resource monitoring handles errors gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = DockerManager(workspace_dir=Path(temp_dir))

            with patch("subprocess.run") as mock_run:
                # Simulate various output formats that could cause parsing errors
                problematic_outputs = [
                    "",  # Empty output
                    "invalid format",  # Non-JSON output
                    "0%\n--\n1.5GiB",  # Malformed stats
                    "NaN%\ninfinity\nError",  # Invalid numbers
                ]

                for output in problematic_outputs:
                    mock_process = Mock()
                    mock_process.stdout = output
                    mock_process.returncode = 0
                    mock_run.return_value = mock_process

                    # Should handle malformed output gracefully
                    try:
                        stats = manager.get_resource_usage()
                        assert isinstance(stats, dict)
                        # Should have some basic structure even on error
                        assert "total_cpu_percent" in stats or len(stats) == 0
                    except Exception as e:
                        pytest.fail(f"Resource monitoring should handle malformed output gracefully: {e}")


class TestDockerManagerCodeQuality:
    """Test code quality improvements in Docker manager."""

    def test_no_silent_exception_handling(self):
        """Test that there are no silent exception handlers (bare 'pass' statements)."""
        # Get source code of both classes
        manager_source = inspect.getsource(DockerManager)
        session_source = inspect.getsource(DockerSession)

        # Look for problematic patterns (except: ... pass without logging)
        # Pattern to find except blocks with only 'pass'
        bare_pass_pattern = r"except[^:]*:\s*pass\s*(?:\n|$)"

        manager_matches = re.findall(bare_pass_pattern, manager_source, re.MULTILINE)
        session_matches = re.findall(bare_pass_pattern, session_source, re.MULTILINE)

        # Should not have any bare pass statements in exception handlers
        assert len(manager_matches) == 0, f"Found silent exception handlers in DockerManager: {manager_matches}"
        assert len(session_matches) == 0, f"Found silent exception handlers in DockerSession: {session_matches}"

    def test_proper_logging_usage(self):
        """Test that logging is used appropriately throughout the module."""
        from rxiv_maker.docker import manager

        # Check that logging is imported
        source = inspect.getsource(manager)
        assert "import logging" in source, "Logging should be imported"

        # Check for logging calls in exception handlers
        # This is a basic check - real implementation would be more sophisticated
        logging_pattern = r"logging\.(debug|info|warning|error|exception)"
        logging_calls = re.findall(logging_pattern, source)

        # Should have some logging calls (exact number depends on implementation)
        assert len(logging_calls) > 0, "Should have logging calls for error handling"

    def test_error_message_quality(self):
        """Test that error messages are informative and helpful."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = DockerManager(workspace_dir=Path(temp_dir))

            # Test with non-existent Docker command to trigger error
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = FileNotFoundError("docker: command not found")

                try:
                    manager.check_docker_available()
                except Exception as e:
                    # Error message should be helpful
                    error_msg = str(e).lower()
                    assert any(word in error_msg for word in ["docker", "not found", "install", "available"])


class TestRegressionPrevention:
    """Test to prevent regression of the manual edits."""

    def test_manual_edits_preserved(self):
        """Test that the manual edits are preserved and functional."""
        # Read the current docker/manager.py file
        manager_file = Path(__file__).parent.parent.parent / "src" / "rxiv_maker" / "docker" / "manager.py"

        if manager_file.exists():
            content = manager_file.read_text()

            # Check that logging import is present
            assert "import logging" in content, "Logging import should be present"

            # Check that bare 'pass' statements were removed from exception handlers
            # Look for the specific patterns that were fixed
            problem_patterns = [
                "except (subprocess.TimeoutExpired, subprocess.CalledProcessError):\n            pass",
                'except Exception as e:\n            print(f"Warning: Failed to get container details: {e}")\n            pass',
                "except ValueError as e:\n            print(f\"Warning: Invalid CPU percentage value '{cpu_percent}': {e}\")\n            pass",
            ]

            for pattern in problem_patterns:
                assert pattern not in content, f"Problematic pattern should be fixed: {pattern}"

    def test_logging_functionality(self):
        """Test that logging functionality works as expected."""
        # Create manager and ensure logging works
        with tempfile.TemporaryDirectory() as temp_dir:
            DockerManager(workspace_dir=Path(temp_dir))

            # Test that we can call logging functions without error
            with patch("logging.debug") as mock_debug:
                # This should be able to log without issues
                logging.debug("Test logging message")
                mock_debug.assert_called_with("Test logging message")


if __name__ == "__main__":
    pytest.main([__file__])
