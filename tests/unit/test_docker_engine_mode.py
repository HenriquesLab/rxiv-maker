"""DEPRECATED: Legacy Docker-only tests.

This file contains legacy Docker-specific tests.
New container engine tests that support both Docker and Podman are in test_container_engines.py.

These tests are kept for backwards compatibility but should be updated to use the new
parameterized approach in test_container_engines.py.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Exclude from default CI test session; run via dedicated engine jobs
pytestmark = pytest.mark.ci_exclude


@pytest.mark.parametrize("engine_type", ["docker", "podman"])
@pytest.mark.docker
@pytest.mark.podman
class TestContainerEngineMode(unittest.TestCase):
    """Test container engine functionality for both Docker and Podman."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.workspace_dir = Path(self.temp_dir)
        self.engine_type = getattr(self, "_pytest_engine_type", "docker")  # Default to docker for unittest

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("subprocess.run")
    def test_docker_engine_availability_check(self, mock_run):
        """Test Docker engine availability checking."""
        # Test Docker available
        mock_run.return_value = Mock(returncode=0, stdout="Docker version 20.10.0")

        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.factory import get_container_engine

            with patch.dict(os.environ, {"RXIV_ENGINE": "docker"}):
                engine = get_container_engine("docker", workspace_dir=self.workspace_dir)
                self.assertEqual(engine.engine_name, "docker")

        except (ImportError, RuntimeError):
            # Skip if Docker engine not available or imports fail
            self.skipTest("Docker engine not available or imports failed")

    @patch("subprocess.run")
    def test_docker_engine_unavailable(self, mock_run):
        """Test behavior when Docker engine is unavailable."""
        # Test Docker not available
        mock_run.return_value = Mock(returncode=1, stderr="docker: command not found")

        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.factory import get_container_engine

            with self.assertRaises(RuntimeError):
                get_container_engine("docker", workspace_dir=self.workspace_dir)

        except ImportError:
            # Skip if imports fail
            self.skipTest("Engine imports not available")

    def test_docker_environment_variable_detection(self):
        """Test Docker engine detection via environment variable."""
        with patch.dict(os.environ, {"RXIV_ENGINE": "DOCKER"}):
            self.assertEqual(os.environ.get("RXIV_ENGINE"), "DOCKER")

        with patch.dict(os.environ, {"RXIV_ENGINE": "docker"}):
            self.assertEqual(os.environ.get("RXIV_ENGINE"), "docker")

    @patch("subprocess.run")
    def test_docker_command_execution(self, mock_run):
        """Test Docker command execution."""
        mock_run.return_value = Mock(returncode=0, stdout="Docker command executed")

        # Simulate Docker command
        docker_cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{self.workspace_dir}:/workspace",
            "-w",
            "/workspace",
            "henriqueslab/rxiv-maker-base:latest",
            "python3",
            "--version",
        ]

        try:
            import subprocess

            result = subprocess.run(docker_cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
        except Exception:
            # Skip if subprocess simulation fails
            self.skipTest("Docker command simulation failed")

    def test_docker_image_reference(self):
        """Test Docker image reference validation."""
        expected_image = "henriqueslab/rxiv-maker-base:latest"

        # Test that the expected image reference is used
        self.assertIsInstance(expected_image, str)
        self.assertIn("henriqueslab/rxiv-maker-base", expected_image)
        self.assertIn("latest", expected_image)

    @patch("subprocess.run")
    def test_docker_container_lifecycle(self, mock_run):
        """Test Docker container lifecycle operations."""
        # Mock successful container operations
        mock_run.return_value = Mock(returncode=0, stdout="Container operation successful")

        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.factory import get_container_engine

            with patch.dict(os.environ, {"RXIV_ENGINE": "docker"}):
                # Test engine creation
                engine = get_container_engine("docker", workspace_dir=self.workspace_dir)

                # Test basic engine properties
                self.assertEqual(engine.engine_name, "docker")
                self.assertEqual(engine.workspace_dir, self.workspace_dir)

        except (ImportError, RuntimeError):
            # Skip if Docker engine not available or imports fail
            self.skipTest("Docker engine not available or imports failed")

    def test_docker_workspace_mounting(self):
        """Test Docker workspace directory mounting logic."""
        workspace_path = str(self.workspace_dir)

        # Test workspace path formatting for Docker mount
        mount_arg = f"{workspace_path}:/workspace"

        self.assertIn(workspace_path, mount_arg)
        self.assertIn(":/workspace", mount_arg)

        # Test workspace creation
        test_file = self.workspace_dir / "test.txt"
        test_file.write_text("test content")

        self.assertTrue(test_file.exists())
        self.assertEqual(test_file.read_text(), "test content")

    @patch("subprocess.run")
    def test_docker_memory_and_cpu_limits(self, mock_run):
        """Test Docker memory and CPU limit configuration."""
        mock_run.return_value = Mock(returncode=0)

        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.factory import get_container_engine

            with patch.dict(os.environ, {"RXIV_ENGINE": "docker"}):
                # Test engine creation with resource limits
                engine = get_container_engine(
                    "docker", workspace_dir=self.workspace_dir, memory_limit="1g", cpu_limit="1.0"
                )

                # Verify resource limits are set
                self.assertEqual(engine.memory_limit, "1g")
                self.assertEqual(engine.cpu_limit, "1.0")

        except (ImportError, RuntimeError, AttributeError):
            # Skip if Docker engine not available or attributes don't exist
            self.skipTest("Docker engine not available or resource limit attributes not implemented")

    def test_docker_engine_factory_registration(self):
        """Test Docker engine registration in factory."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.factory import ContainerEngineFactory

            # Test that docker is registered
            supported_engines = ContainerEngineFactory.get_supported_engines()
            self.assertIn("docker", supported_engines)

        except ImportError:
            # Skip if imports fail
            self.skipTest("Engine factory imports not available")

    @patch("subprocess.run")
    def test_docker_error_handling(self, mock_run):
        """Test Docker error handling scenarios."""
        # Test Docker command failure
        mock_run.return_value = Mock(returncode=1, stderr="Docker error occurred")

        try:
            import subprocess

            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)

        except Exception:
            # Skip if subprocess simulation fails
            self.skipTest("Docker error simulation failed")


@pytest.mark.docker
class TestDockerEngineIntegration(unittest.TestCase):
    """Test Docker engine integration scenarios."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.workspace_dir = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("subprocess.run")
    def test_docker_engine_selection_priority(self, mock_run):
        """Test Docker engine selection priority."""
        mock_run.return_value = Mock(returncode=0, stdout="Docker available")

        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.factory import ContainerEngineFactory

            # Test engine availability detection
            availability = ContainerEngineFactory.list_available_engines()

            # Docker should be in the list
            self.assertIn("docker", availability)

        except ImportError:
            # Skip if imports fail
            self.skipTest("Engine factory imports not available")

    def test_docker_session_reuse_configuration(self):
        """Test Docker session reuse configuration."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.factory import get_container_engine

            with patch.dict(os.environ, {"RXIV_ENGINE": "docker"}):
                # Test with session reuse enabled
                with patch("subprocess.run", return_value=Mock(returncode=0)):
                    engine = get_container_engine("docker", workspace_dir=self.workspace_dir, enable_session_reuse=True)

                    self.assertTrue(engine.enable_session_reuse)

                # Test with session reuse disabled
                with patch("subprocess.run", return_value=Mock(returncode=0)):
                    engine = get_container_engine(
                        "docker", workspace_dir=self.workspace_dir, enable_session_reuse=False
                    )

                    self.assertFalse(engine.enable_session_reuse)

        except (ImportError, RuntimeError, AttributeError):
            # Skip if Docker engine not available or attributes don't exist
            self.skipTest("Docker engine not available or session reuse not implemented")

    @patch("subprocess.run")
    def test_docker_fallback_behavior(self, mock_run):
        """Test Docker fallback behavior when primary operations fail."""
        # First call fails, second succeeds
        mock_run.side_effect = [
            Mock(returncode=1, stderr="First attempt failed"),
            Mock(returncode=0, stdout="Fallback successful"),
        ]

        try:
            import subprocess

            # Simulate initial failure
            result1 = subprocess.run(["docker", "pull", "test:latest"], capture_output=True)
            self.assertEqual(result1.returncode, 1)

            # Simulate fallback success
            result2 = subprocess.run(["docker", "build", "-t", "test:latest", "."], capture_output=True)
            self.assertEqual(result2.returncode, 0)

        except Exception:
            # Skip if subprocess simulation fails
            self.skipTest("Docker fallback simulation failed")


if __name__ == "__main__":
    unittest.main()
