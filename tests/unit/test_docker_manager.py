"""Tests for Docker manager functionality."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from rxiv_maker.docker.manager import DockerSession


class TestDockerSession(unittest.TestCase):
    """Test DockerSession class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.container_id = "test_container_123"
        self.image = "test_image:latest"
        self.session = DockerSession(container_id=self.container_id, image=self.image, workspace_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test DockerSession initialization."""
        self.assertEqual(self.session.container_id, self.container_id)
        self.assertEqual(self.session.image, self.image)
        self.assertEqual(self.session.workspace_dir, self.temp_dir)

    @patch("subprocess.run")
    def test_cleanup_success(self, mock_run):
        """Test successful container cleanup."""
        # Mock successful subprocess calls
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # Test cleanup
        self.session.cleanup()

        # Verify correct commands were called
        self.assertEqual(mock_run.call_count, 2)

        # Check stop command
        stop_call = mock_run.call_args_list[0]
        self.assertIn("docker", stop_call[0][0])
        self.assertIn("stop", stop_call[0][0])
        self.assertIn(self.container_id, stop_call[0][0])

        # Check remove command
        rm_call = mock_run.call_args_list[1]
        self.assertIn("docker", rm_call[0][0])
        self.assertIn("rm", rm_call[0][0])
        self.assertIn(self.container_id, rm_call[0][0])

    @patch("subprocess.run")
    def test_cleanup_with_timeout(self, mock_run):
        """Test container cleanup handles timeouts gracefully."""
        # Mock timeout exception
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["docker"], timeout=10)

        # Test cleanup doesn't raise exception
        try:
            self.session.cleanup()
        except Exception as e:
            self.fail(f"cleanup() raised an exception: {e}")

    @patch("subprocess.run")
    def test_cleanup_with_error(self, mock_run):
        """Test container cleanup handles errors gracefully."""
        # Mock subprocess error for first call, success for second
        mock_run.side_effect = [subprocess.CalledProcessError(1, "docker"), MagicMock(returncode=0)]

        # Test cleanup handles errors gracefully
        # The cleanup method should catch exceptions internally
        self.session.cleanup()  # Should not raise exception

    def test_session_properties(self):
        """Test session property access."""
        self.assertTrue(hasattr(self.session, "container_id"))
        self.assertTrue(hasattr(self.session, "image"))
        self.assertTrue(hasattr(self.session, "workspace_dir"))
        self.assertIsInstance(self.session.workspace_dir, Path)

    @patch("rxiv_maker.utils.platform.platform_detector")
    def test_session_with_platform_detection(self, mock_detector):
        """Test session works with platform detection utilities."""
        mock_detector.is_windows.return_value = False
        mock_detector.is_macos.return_value = True

        # Create session and verify it doesn't break with platform detection
        session = DockerSession(container_id="test_mac", image="test:mac", workspace_dir=self.temp_dir)

        self.assertEqual(session.container_id, "test_mac")

    def test_workspace_dir_handling(self):
        """Test workspace directory handling."""
        # Test with string path
        str_path = str(self.temp_dir)
        session = DockerSession(container_id="test_str", image="test:str", workspace_dir=Path(str_path))

        self.assertIsInstance(session.workspace_dir, Path)
        self.assertEqual(session.workspace_dir, self.temp_dir)

    @patch("subprocess.run")
    def test_docker_command_construction(self, mock_run):
        """Test that Docker commands are constructed securely."""
        mock_run.return_value = MagicMock(returncode=0)

        # Test cleanup to see command construction
        self.session.cleanup()

        # Verify commands use list format (not shell=True)
        for call in mock_run.call_args_list:
            args, kwargs = call
            # Command should be a list (secure)
            self.assertIsInstance(args[0], list)
            # Should not use shell=True
            self.assertFalse(kwargs.get("shell", False))


class TestDockerManagerIntegration(unittest.TestCase):
    """Integration tests for Docker manager functionality."""

    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up integration test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("subprocess.run")
    def test_docker_session_lifecycle(self, mock_run):
        """Test complete Docker session lifecycle."""
        # Mock docker command responses
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # Create and cleanup session
        session = DockerSession(container_id="lifecycle_test", image="test:lifecycle", workspace_dir=self.temp_dir)

        # Test that session can be created and cleaned up
        session.cleanup()

        # Verify subprocess was called
        self.assertTrue(mock_run.called)

    def test_multiple_sessions(self):
        """Test handling multiple Docker sessions."""
        sessions = []
        for i in range(3):
            session = DockerSession(
                container_id=f"multi_test_{i}", image=f"test:multi_{i}", workspace_dir=self.temp_dir
            )
            sessions.append(session)

        # Verify all sessions have unique container IDs
        container_ids = [s.container_id for s in sessions]
        self.assertEqual(len(set(container_ids)), 3)
        self.assertEqual(len(container_ids), 3)

    @patch.dict(os.environ, {"DOCKER_HOST": "tcp://test:2376"})
    def test_docker_environment_variables(self):
        """Test Docker session with environment variables."""
        session = DockerSession(container_id="env_test", image="test:env", workspace_dir=self.temp_dir)

        # Session should be created successfully even with Docker env vars
        self.assertEqual(session.container_id, "env_test")
        self.assertEqual(os.environ.get("DOCKER_HOST"), "tcp://test:2376")


if __name__ == "__main__":
    unittest.main()
