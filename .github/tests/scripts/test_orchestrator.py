#!/usr/bin/env python3
"""
Test script for the release orchestrator.

Demonstrates local testing capabilities that replace slow CI debugging.

Usage:
    python .github/tests/scripts/test_orchestrator.py
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "common"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "release"))


class TestReleaseOrchestrator(unittest.TestCase):
    """Test cases for release orchestrator."""

    def setUp(self):
        """Set up test environment."""
        # Mock environment variables
        self.env_patcher = patch.dict(
            os.environ,
            {"GITHUB_TOKEN": "test-github-token", "PYPI_TOKEN": "test-pypi-token", "GITHUB_REF_NAME": "v1.2.3"},
        )
        self.env_patcher.start()

        # Import after environment is set up
        from orchestrator import ReleaseOrchestrator

        self.ReleaseOrchestrator = ReleaseOrchestrator

    def tearDown(self):
        """Clean up test environment."""
        self.env_patcher.stop()

    @patch("orchestrator.check_pypi_package_available")
    @patch("orchestrator.check_github_release_exists")
    def test_validate_pre_conditions_success(self, mock_github_check, mock_pypi_check):
        """Test successful pre-condition validation."""
        # Mock external checks to return False (package doesn't exist yet)
        mock_github_check.return_value = False
        mock_pypi_check.return_value = False

        orchestrator = self.ReleaseOrchestrator(dry_run=True, debug=True)
        result = orchestrator.validate_pre_conditions()

        self.assertTrue(result)
        mock_github_check.assert_called_once()
        mock_pypi_check.assert_called_once()

    @patch("orchestrator.check_pypi_package_available")
    @patch("orchestrator.check_github_release_exists")
    def test_validate_pre_conditions_release_exists(self, mock_github_check, mock_pypi_check):
        """Test pre-condition validation when release already exists."""
        # Mock to return True (release already exists)
        mock_github_check.return_value = True

        orchestrator = self.ReleaseOrchestrator(dry_run=True)
        result = orchestrator.validate_pre_conditions()

        self.assertFalse(result)

    def test_dry_run_mode(self):
        """Test that dry run mode skips actual operations."""
        orchestrator = self.ReleaseOrchestrator(dry_run=True, debug=True)

        # These should all return True in dry run mode
        self.assertTrue(orchestrator.create_github_release())
        self.assertTrue(orchestrator.publish_to_pypi())
        self.assertTrue(orchestrator.wait_for_pypi_propagation())

    @patch("orchestrator.trigger_workflow")
    def test_trigger_cross_repository_workflows(self, mock_trigger):
        """Test cross-repository workflow triggering."""
        mock_trigger.return_value = True

        orchestrator = self.ReleaseOrchestrator(dry_run=False)
        result = orchestrator.trigger_cross_repository_workflows()

        self.assertTrue(result)
        self.assertTrue(orchestrator.release_state["homebrew_triggered"])
        self.assertTrue(orchestrator.release_state["apt_triggered"])

        # Should be called twice (homebrew and apt)
        self.assertEqual(mock_trigger.call_count, 2)

    def test_error_handling(self):
        """Test error handling and state tracking."""
        orchestrator = self.ReleaseOrchestrator(dry_run=True)

        # Simulate an error
        test_error = Exception("Test error")
        orchestrator.handle_release_failure(test_error)

        # Should not raise an exception
        self.assertTrue(True)  # If we get here, error handling worked


class TestLocalDebugging(unittest.TestCase):
    """Demonstrate local debugging capabilities."""

    def test_local_config_loading(self):
        """Test that configuration can be loaded locally."""
        from config import ConfigLoader

        loader = ConfigLoader()

        # This should work locally without GitHub Actions environment
        try:
            config = loader.load_release_config()
            self.assertEqual(config.package_name, "rxiv-maker")
            self.assertGreater(config.pypi_timeout, 0)
        except Exception as e:
            self.fail(f"Config loading failed: {e}")

    def test_local_utilities(self):
        """Test utility functions locally."""
        from utils import RetryConfig, create_http_session

        # Test retry config
        retry_config = RetryConfig(max_retries=2, backoff_factor=1.5)
        self.assertEqual(retry_config.max_retries, 2)
        self.assertEqual(retry_config.backoff_factor, 1.5)

        # Test HTTP session creation
        session = create_http_session(timeout=10)
        self.assertIsNotNone(session)
        self.assertEqual(session.timeout, 10)


def run_integration_test():
    """Run a full integration test in dry-run mode."""
    print("\n🧪 Running Integration Test (Dry Run)")
    print("=" * 50)

    # Set up environment for testing
    os.environ["GITHUB_TOKEN"] = "test-token"
    os.environ["PYPI_TOKEN"] = "test-token"
    os.environ["GITHUB_REF_NAME"] = "v1.2.3-test"

    try:
        from orchestrator import ReleaseOrchestrator

        orchestrator = ReleaseOrchestrator(dry_run=True, debug=True)
        success = orchestrator.run_release_pipeline()

        print(f"\n🎯 Integration test result: {'SUCCESS' if success else 'FAILURE'}")
        return success

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Testing Release Orchestrator Locally")
    print("This demonstrates the debuggability advantage over YAML workflows!")
    print()

    # Run unit tests
    unittest.main(argv=[""], exit=False, verbosity=2)

    # Run integration test
    integration_success = run_integration_test()

    print("\n📊 Summary:")
    print("  • Unit tests: Completed")
    print(f"  • Integration test: {'PASSED' if integration_success else 'FAILED'}")
    print("  • Local debugging: ✅ Available")
    print("  • No CI required: ✅ True")

    print("\n💡 Key Benefits Demonstrated:")
    print("  • Instant feedback (no waiting for CI)")
    print("  • Breakpoints and debugging possible")
    print("  • Unit testable components")
    print("  • Easy to modify and test changes")
    print("  • Clear error messages and logging")
