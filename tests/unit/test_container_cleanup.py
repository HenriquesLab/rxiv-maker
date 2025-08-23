"""Unit tests for container cleanup functionality."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest


@pytest.mark.unit
class TestContainerSessionCleanup(unittest.TestCase):
    """Test container session cleanup functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.workspace_dir = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_abstract_cleanup_all_sessions(self):
        """Test abstract engine cleanup_all_sessions method."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.abstract import ContainerSession
            from rxiv_maker.engines.docker_engine import DockerEngine

            # Create engine with mocked sessions
            engine = DockerEngine(workspace_dir=self.workspace_dir)

            # Create mock sessions
            mock_session1 = Mock(spec=ContainerSession)
            mock_session2 = Mock(spec=ContainerSession)

            engine._active_sessions = {
                "session1": mock_session1,
                "session2": mock_session2,
            }

            # Test cleanup_all_sessions
            engine.cleanup_all_sessions()

            # Verify all sessions were cleaned up
            mock_session1.cleanup.assert_called_once()
            mock_session2.cleanup.assert_called_once()

            # Verify sessions were removed
            self.assertEqual(len(engine._active_sessions), 0)

        except ImportError:
            self.skipTest("Container engine imports not available")

    @patch("time.time")
    @patch("subprocess.run")
    def test_docker_cleanup_expired_sessions(self, mock_run, mock_time):
        """Test Docker engine expired session cleanup."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.docker_engine import DockerEngine, DockerSession

            # Set up time mocks
            current_time = 1000.0
            old_session_time = current_time - 700  # Expired (older than 600s timeout)
            fresh_session_time = current_time - 300  # Fresh (within timeout)
            mock_time.return_value = current_time

            # Create engine
            engine = DockerEngine(workspace_dir=self.workspace_dir)
            engine._last_cleanup = 0  # Force cleanup to run

            # Create mock sessions with different ages
            old_session = Mock(spec=DockerSession)
            old_session.created_at = old_session_time
            old_session.is_active.return_value = True
            old_session.cleanup.return_value = True

            fresh_session = Mock(spec=DockerSession)
            fresh_session.created_at = fresh_session_time
            fresh_session.is_active.return_value = True

            inactive_session = Mock(spec=DockerSession)
            inactive_session.created_at = fresh_session_time
            inactive_session.is_active.return_value = False
            inactive_session.cleanup.return_value = True

            engine._active_sessions = {
                "old": old_session,
                "fresh": fresh_session,
                "inactive": inactive_session,
            }

            # Run cleanup
            engine._cleanup_expired_sessions(force=True)

            # Verify expired and inactive sessions were cleaned up
            old_session.cleanup.assert_called_once()
            inactive_session.cleanup.assert_called_once()
            fresh_session.cleanup.assert_not_called()

            # Verify only fresh session remains
            self.assertEqual(len(engine._active_sessions), 1)
            self.assertIn("fresh", engine._active_sessions)

        except ImportError:
            self.skipTest("Docker engine imports not available")

    @patch("time.time")
    @patch("subprocess.run")
    def test_podman_cleanup_expired_sessions(self, mock_run, mock_time):
        """Test Podman engine expired session cleanup."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.podman_engine import PodmanEngine, PodmanSession

            # Set up time mocks
            current_time = 1000.0
            old_session_time = current_time - 700  # Expired
            mock_time.return_value = current_time

            # Create engine
            engine = PodmanEngine(workspace_dir=self.workspace_dir)
            engine._last_cleanup = 0  # Force cleanup to run

            # Create mock expired session
            expired_session = Mock(spec=PodmanSession)
            expired_session.created_at = old_session_time
            expired_session.is_active.return_value = True
            expired_session.cleanup.return_value = True

            engine._active_sessions = {"expired": expired_session}

            # Run cleanup
            engine._cleanup_expired_sessions(force=True)

            # Verify expired session was cleaned up
            expired_session.cleanup.assert_called_once()
            self.assertEqual(len(engine._active_sessions), 0)

        except ImportError:
            self.skipTest("Podman engine imports not available")

    @patch("time.time")
    @patch("subprocess.run")
    def test_session_cleanup_max_sessions_limit(self, mock_run, mock_time):
        """Test that cleanup removes oldest sessions when max limit exceeded."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.docker_engine import DockerEngine, DockerSession

            current_time = 1000.0
            mock_time.return_value = current_time

            # Create engine with low max sessions for testing
            engine = DockerEngine(workspace_dir=self.workspace_dir)
            engine._max_sessions = 2
            engine._last_cleanup = 0

            # Create multiple sessions with different ages
            oldest_session = Mock(spec=DockerSession)
            oldest_session.created_at = current_time - 300
            oldest_session.is_active.return_value = True
            oldest_session.cleanup.return_value = True

            middle_session = Mock(spec=DockerSession)
            middle_session.created_at = current_time - 200
            middle_session.is_active.return_value = True
            middle_session.cleanup.return_value = True

            newest_session = Mock(spec=DockerSession)
            newest_session.created_at = current_time - 100
            newest_session.is_active.return_value = True

            engine._active_sessions = {
                "oldest": oldest_session,
                "middle": middle_session,
                "newest": newest_session,
            }

            # Run cleanup - should remove oldest session to stay within limit
            engine._cleanup_expired_sessions(force=True)

            # Verify oldest session was cleaned up to maintain max limit
            oldest_session.cleanup.assert_called_once()
            middle_session.cleanup.assert_not_called()
            newest_session.cleanup.assert_not_called()

            # Should have 2 sessions remaining (max limit)
            self.assertEqual(len(engine._active_sessions), 2)
            self.assertNotIn("oldest", engine._active_sessions)

        except ImportError:
            self.skipTest("Docker engine imports not available")

    @patch("subprocess.run")
    def test_session_cleanup_failure_handling(self, mock_run):
        """Test handling of session cleanup failures."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.docker_engine import DockerEngine, DockerSession

            # Create engine
            engine = DockerEngine(workspace_dir=self.workspace_dir)

            # Create session that fails to cleanup
            failing_session = Mock(spec=DockerSession)
            failing_session.cleanup.side_effect = Exception("Cleanup failed")

            working_session = Mock(spec=DockerSession)
            working_session.cleanup.return_value = True

            engine._active_sessions = {"failing": failing_session, "working": working_session}

            # Cleanup should continue despite individual failures
            engine.cleanup_all_sessions()

            # Verify both sessions had cleanup attempted
            failing_session.cleanup.assert_called_once()
            working_session.cleanup.assert_called_once()

            # Sessions should still be removed from active list
            self.assertEqual(len(engine._active_sessions), 0)

        except ImportError:
            self.skipTest("Docker engine imports not available")

    def test_cleanup_throttling(self):
        """Test that cleanup is throttled to avoid frequent executions."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.docker_engine import DockerEngine

            current_time = 1000.0

            # Create engine
            engine = DockerEngine(workspace_dir=self.workspace_dir)
            engine._last_cleanup = current_time - 20  # Recent cleanup (within 30s throttle)

            with patch("time.time", return_value=current_time):
                # Add a mock expired session (old enough to be cleaned)
                mock_session = Mock()
                mock_session.created_at = current_time - 700  # Older than 600s timeout
                mock_session.is_active.return_value = True
                mock_session.cleanup.return_value = True
                engine._active_sessions = {"test": mock_session}

                # Run cleanup - should be throttled
                engine._cleanup_expired_sessions()

                # Session should not be cleaned up due to throttling
                mock_session.cleanup.assert_not_called()
                self.assertEqual(len(engine._active_sessions), 1)

                # Force cleanup should work regardless of throttling
                engine._cleanup_expired_sessions(force=True)
                mock_session.cleanup.assert_called_once()

        except ImportError:
            self.skipTest("Docker engine imports not available")


@pytest.mark.unit
class TestContainerEngineFactory(unittest.TestCase):
    """Test container engine factory cleanup functionality."""

    def test_factory_cleanup_all_engines(self):
        """Test factory-level cleanup of all engines."""
        try:
            import sys

            sys.path.insert(0, "src")
            import weakref

            from rxiv_maker.engines.factory import ContainerEngineFactory

            # Create mock engines
            mock_docker = Mock()
            mock_docker.engine_name = "docker"
            mock_docker.cleanup_all_sessions.return_value = None

            mock_podman = Mock()
            mock_podman.engine_name = "podman"
            mock_podman.cleanup_all_sessions.return_value = None

            # Create weak references as the factory expects
            docker_ref = weakref.ref(mock_docker)
            podman_ref = weakref.ref(mock_podman)

            # Test cleanup with mocked active engines
            with patch.object(ContainerEngineFactory, "_active_engines", {docker_ref, podman_ref}):
                cleanup_count = ContainerEngineFactory.cleanup_all_engines()

                # Verify all engines were cleaned up
                mock_docker.cleanup_all_sessions.assert_called_once()
                mock_podman.cleanup_all_sessions.assert_called_once()
                self.assertEqual(cleanup_count, 2)

        except ImportError:
            self.skipTest("Container engine factory imports not available")

    def test_factory_cleanup_with_failures(self):
        """Test factory cleanup handles individual engine failures gracefully."""
        try:
            import sys

            sys.path.insert(0, "src")
            import weakref

            from rxiv_maker.engines.factory import ContainerEngineFactory

            # Create mock engines - one fails, one succeeds
            failing_engine = Mock()
            failing_engine.engine_name = "failing"
            failing_engine.cleanup_all_sessions.side_effect = Exception("Cleanup failed")

            working_engine = Mock()
            working_engine.engine_name = "working"
            working_engine.cleanup_all_sessions.return_value = None

            # Create weak references as the factory expects
            failing_ref = weakref.ref(failing_engine)
            working_ref = weakref.ref(working_engine)

            # Test cleanup continues despite failures
            with patch.object(ContainerEngineFactory, "_active_engines", {failing_ref, working_ref}):
                cleanup_count = ContainerEngineFactory.cleanup_all_engines()

                # Verify both engines were attempted
                failing_engine.cleanup_all_sessions.assert_called_once()
                working_engine.cleanup_all_sessions.assert_called_once()

                # Only working engine should be counted as successful
                self.assertEqual(cleanup_count, 1)

        except ImportError:
            self.skipTest("Container engine factory imports not available")


@pytest.mark.unit
class TestContainerSessionLifecycle(unittest.TestCase):
    """Test individual container session lifecycle."""

    @patch("subprocess.run")
    def test_docker_session_cleanup(self, mock_run):
        """Test Docker session cleanup operations."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.docker_engine import DockerSession

            # Create session
            session = DockerSession("test_container_id", "test:latest", Path("/tmp"))

            # Mock successful cleanup
            mock_run.return_value = Mock(returncode=0)

            # Test cleanup
            result = session.cleanup()
            self.assertTrue(result)
            self.assertFalse(session._active)

            # Verify Docker stop and rm commands were called
            expected_calls = [
                call(
                    ["docker", "stop", "test_container_id"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=10,
                ),
                call(
                    ["docker", "rm", "test_container_id"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=10,
                ),
            ]
            mock_run.assert_has_calls(expected_calls, any_order=False)

        except ImportError:
            self.skipTest("Docker session imports not available")

    @patch("subprocess.run")
    def test_podman_session_cleanup(self, mock_run):
        """Test Podman session cleanup operations."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.podman_engine import PodmanSession

            # Create session
            session = PodmanSession("test_container_id", "test:latest", Path("/tmp"))

            # Mock successful cleanup
            mock_run.return_value = Mock(returncode=0)

            # Test cleanup
            result = session.cleanup()
            self.assertTrue(result)
            self.assertFalse(session._active)

            # Verify Podman stop and rm commands were called
            expected_calls = [
                call(
                    ["podman", "stop", "test_container_id"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=10,
                ),
                call(
                    ["podman", "rm", "test_container_id"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=10,
                ),
            ]
            mock_run.assert_has_calls(expected_calls, any_order=False)

        except ImportError:
            self.skipTest("Podman session imports not available")

    @patch("subprocess.run")
    def test_session_cleanup_already_inactive(self, mock_run):
        """Test cleanup of already inactive session."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.docker_engine import DockerSession

            # Create inactive session
            session = DockerSession("test_container_id", "test:latest", Path("/tmp"))
            session._active = False

            # Test cleanup - should return True immediately
            result = session.cleanup()
            self.assertTrue(result)

            # No subprocess calls should be made
            mock_run.assert_not_called()

        except ImportError:
            self.skipTest("Docker session imports not available")


if __name__ == "__main__":
    unittest.main()
