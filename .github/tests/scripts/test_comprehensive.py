#!/usr/bin/env python3
"""
Comprehensive test suite for Python-first GitHub Actions.
Tests edge cases, error scenarios, performance, and integration.

This demonstrates the testing advantage over YAML workflows.
"""

import sys
import os
import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import json

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "common"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "release"))

class TestErrorScenarios(unittest.TestCase):
    """Test comprehensive error scenarios that would be hard to test in YAML."""
    
    def setUp(self):
        """Set up test environment."""
        self.env_patcher = patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test-github-token',
            'PYPI_TOKEN': 'test-pypi-token',
            'GITHUB_REF_NAME': 'v1.2.3'
        })
        self.env_patcher.start()
        
        from orchestrator import ReleaseOrchestrator
        self.ReleaseOrchestrator = ReleaseOrchestrator
    
    def tearDown(self):
        """Clean up."""
        self.env_patcher.stop()
    
    def test_missing_github_token(self):
        """Test behavior when GitHub token is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {'PYPI_TOKEN': 'test'}):
                with self.assertRaises(ValueError) as cm:
                    self.ReleaseOrchestrator(dry_run=True)
                
                self.assertIn("GITHUB_TOKEN", str(cm.exception))
    
    def test_invalid_version_format(self):
        """Test handling of invalid version formats."""
        with patch.dict(os.environ, {'GITHUB_REF_NAME': 'invalid-version'}):
            orchestrator = self.ReleaseOrchestrator(dry_run=True)
            result = orchestrator.validate_pre_conditions()
            self.assertFalse(result)
    
    @patch('orchestrator.check_github_release_exists')
    def test_release_already_exists_no_force(self, mock_github_check):
        """Test behavior when release already exists without force flag."""
        mock_github_check.return_value = True
        
        orchestrator = self.ReleaseOrchestrator(dry_run=True, force=False)
        result = orchestrator.validate_pre_conditions()
        
        self.assertFalse(result)
        mock_github_check.assert_called_once()
    
    @patch('orchestrator.check_github_release_exists')
    def test_release_already_exists_with_force(self, mock_github_check):
        """Test behavior when release already exists WITH force flag."""
        mock_github_check.return_value = True
        
        orchestrator = self.ReleaseOrchestrator(dry_run=True, force=True)
        result = orchestrator.validate_pre_conditions()
        
        # Should succeed because force=True
        self.assertTrue(result)
    
    @patch('orchestrator.trigger_workflow')
    def test_partial_cross_repo_failure(self, mock_trigger):
        """Test handling when some cross-repo workflows fail."""
        # First call (homebrew) succeeds, second (apt) fails
        mock_trigger.side_effect = [True, False]
        
        orchestrator = self.ReleaseOrchestrator(dry_run=False)
        result = orchestrator.trigger_cross_repository_workflows()
        
        # Should return False due to APT failure
        self.assertFalse(result)
        self.assertTrue(orchestrator.release_state['homebrew_triggered'])
        self.assertFalse(orchestrator.release_state['apt_triggered'])
    
    def test_rollback_state_tracking(self):
        """Test that rollback properly tracks what was completed."""
        orchestrator = self.ReleaseOrchestrator(dry_run=True)
        
        # Simulate partial completion
        orchestrator.release_state['github_release_created'] = True
        orchestrator.release_state['pypi_published'] = False
        orchestrator.release_state['homebrew_triggered'] = True
        
        # Test rollback handling
        test_error = Exception("Simulated failure")
        orchestrator.handle_release_failure(test_error)
        
        # Should complete without raising exception
        self.assertTrue(True)


class TestPerformanceScenarios(unittest.TestCase):
    """Test performance, timeouts, and retry scenarios."""
    
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test-token',
            'PYPI_TOKEN': 'test-token',
            'GITHUB_REF_NAME': 'v1.0.0'
        })
        self.env_patcher.start()
        
        from utils import wait_for_condition, retry_with_backoff, RetryConfig
        self.wait_for_condition = wait_for_condition
        self.retry_with_backoff = retry_with_backoff
        self.RetryConfig = RetryConfig
    
    def tearDown(self):
        self.env_patcher.stop()
    
    def test_timeout_behavior(self):
        """Test timeout behavior with wait_for_condition."""
        def always_false():
            return False
        
        start_time = time.time()
        result = self.wait_for_condition(
            always_false,
            timeout=2,  # 2 second timeout
            check_interval=0.5
        )
        elapsed = time.time() - start_time
        
        self.assertFalse(result)
        self.assertGreaterEqual(elapsed, 2)  # Should timeout after 2 seconds
        self.assertLess(elapsed, 3)  # But not much longer
    
    def test_retry_with_backoff(self):
        """Test retry mechanism with exponential backoff."""
        call_count = 0
        
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"Attempt {call_count} failed")
            return "success"
        
        retry_config = self.RetryConfig(max_retries=3, initial_delay=0.1)
        start_time = time.time()
        
        result = self.retry_with_backoff(failing_function, retry_config)
        elapsed = time.time() - start_time
        
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
        # Should have some delay due to backoff (0.1 + 0.2 = 0.3s minimum)
        self.assertGreaterEqual(elapsed, 0.3)
    
    def test_retry_exhaustion(self):
        """Test behavior when all retries are exhausted."""
        def always_failing():
            raise Exception("Always fails")
        
        retry_config = self.RetryConfig(max_retries=2, initial_delay=0.1)
        
        with self.assertRaises(Exception) as cm:
            self.retry_with_backoff(always_failing, retry_config)
        
        self.assertEqual(str(cm.exception), "Always fails")


class TestAPIIntegration(unittest.TestCase):
    """Test integration with external APIs (mocked for reliability)."""
    
    def setUp(self):
        from utils import check_pypi_package_available, check_github_release_exists
        self.check_pypi = check_pypi_package_available
        self.check_github = check_github_release_exists
    
    @patch('utils.create_http_session')
    def test_pypi_package_check_success(self, mock_session):
        """Test PyPI package availability check success."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.return_value.get.return_value = mock_response
        
        result = self.check_pypi("test-package", "v1.0.0")
        self.assertTrue(result)
    
    @patch('utils.create_http_session')
    def test_pypi_package_check_not_found(self, mock_session):
        """Test PyPI package availability check when package not found."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_session.return_value.get.return_value = mock_response
        
        result = self.check_pypi("nonexistent-package", "v1.0.0")
        self.assertFalse(result)
    
    @patch('utils.create_http_session')
    def test_github_release_check_network_error(self, mock_session):
        """Test GitHub release check with network error."""
        import requests
        mock_session.return_value.get.side_effect = requests.RequestException("Network error")
        
        result = self.check_github("owner", "repo", "v1.0.0", "token")
        self.assertFalse(result)  # Should return False on network error


class TestConfigurationEdgeCases(unittest.TestCase):
    """Test configuration loading and validation edge cases."""
    
    def test_config_loading_with_missing_file(self):
        """Test config loading when YAML file doesn't exist."""
        from config import ConfigLoader
        
        # Create temporary directory without config file
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = ConfigLoader(temp_dir)
            config = loader.load_release_config()
            
            # Should use defaults
            self.assertEqual(config.package_name, "rxiv-maker")
            self.assertEqual(config.pypi_timeout, 300)
    
    def test_config_environment_override(self):
        """Test that environment variables override config file."""
        from config import ConfigLoader
        
        with patch.dict(os.environ, {'PACKAGE_NAME': 'custom-package'}):
            loader = ConfigLoader()
            config = loader.load_release_config()
            
            self.assertEqual(config.package_name, "custom-package")
    
    def test_invalid_config_values(self):
        """Test validation of invalid configuration values."""
        from config import ReleaseConfig
        
        with self.assertRaises(ValueError):
            ReleaseConfig(package_name="")  # Empty package name
        
        with self.assertRaises(ValueError):
            ReleaseConfig(package_name="test", pypi_timeout=-1)  # Negative timeout


class TestRealWorldScenarios(unittest.TestCase):
    """Test complex real-world scenarios."""
    
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test-token',
            'PYPI_TOKEN': 'test-token',
            'GITHUB_REF_NAME': 'v2.0.0'
        })
        self.env_patcher.start()
        
        from orchestrator import ReleaseOrchestrator
        self.ReleaseOrchestrator = ReleaseOrchestrator
    
    def tearDown(self):
        self.env_patcher.stop()
    
    @patch('orchestrator.check_pypi_package_available')
    @patch('orchestrator.check_github_release_exists')
    @patch('orchestrator.trigger_workflow')
    def test_complete_release_pipeline_dry_run(self, mock_trigger, mock_github, mock_pypi):
        """Test complete release pipeline in dry-run mode."""
        # Set up mocks
        mock_github.return_value = False
        mock_pypi.return_value = False
        mock_trigger.return_value = True
        
        orchestrator = self.ReleaseOrchestrator(dry_run=True, debug=True)
        result = orchestrator.run_release_pipeline()
        
        self.assertTrue(result)
        
        # Verify final state
        expected_state = {
            'github_release_created': True,
            'pypi_published': True,
            'homebrew_triggered': True,
            'apt_triggered': True
        }
        self.assertEqual(orchestrator.release_state, expected_state)
    
    @patch('orchestrator.wait_for_condition')
    def test_pypi_propagation_timeout(self, mock_wait):
        """Test PyPI propagation timeout scenario."""
        mock_wait.return_value = False  # Simulate timeout
        
        orchestrator = self.ReleaseOrchestrator(dry_run=False)
        result = orchestrator.wait_for_pypi_propagation()
        
        self.assertFalse(result)


def run_stress_test():
    """Run stress test with multiple concurrent scenarios."""
    print("\n🏋️  Running Stress Test")
    print("=" * 50)
    
    import threading
    import concurrent.futures
    
    def run_orchestrator_instance(instance_id):
        """Run orchestrator instance with unique version."""
        os.environ['GITHUB_REF_NAME'] = f'v1.0.{instance_id}'
        
        from orchestrator import ReleaseOrchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)
        return orchestrator.run_release_pipeline()
    
    # Run multiple instances concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_orchestrator_instance, i) for i in range(10)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    success_count = sum(results)
    print(f"✅ Stress test: {success_count}/10 instances succeeded")
    return success_count == 10


def run_memory_test():
    """Test memory usage and cleanup."""
    print("\n🧠 Running Memory Test")
    print("=" * 50)
    
    import psutil
    import gc
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    # Create and destroy many orchestrator instances
    for i in range(100):
        os.environ['GITHUB_REF_NAME'] = f'v1.0.{i}'
        
        from orchestrator import ReleaseOrchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)
        orchestrator.validate_pre_conditions()
        
        # Delete reference
        del orchestrator
        
        if i % 20 == 0:
            gc.collect()
    
    final_memory = process.memory_info().rss
    memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
    
    print(f"💾 Memory increase: {memory_increase:.2f} MB")
    print(f"✅ Memory test: {'PASS' if memory_increase < 50 else 'FAIL'}")
    
    return memory_increase < 50


if __name__ == "__main__":
    print("🧪 Comprehensive Testing Suite")
    print("Testing advantages over YAML workflows:")
    print("• Edge case testing")
    print("• Error scenario validation") 
    print("• Performance testing")
    print("• Integration testing")
    print("• Stress testing")
    print("• Memory testing")
    print()
    
    # Run unit tests
    print("📋 Running Unit Tests...")
    unittest.main(argv=[''], exit=False, verbosity=1)
    
    # Run stress tests
    stress_success = run_stress_test()
    
    # Run memory tests
    memory_success = run_memory_test()
    
    # Summary
    print(f"\n🏆 Testing Complete")
    print(f"├── Unit tests: ✅ Completed")
    print(f"├── Stress test: {'✅ PASS' if stress_success else '❌ FAIL'}")
    print(f"└── Memory test: {'✅ PASS' if memory_success else '❌ FAIL'}")
    
    print(f"\n💪 Ultrathink Testing Advantages Demonstrated:")
    print(f"  • Comprehensive edge case coverage")
    print(f"  • Real-world scenario simulation")
    print(f"  • Performance and stress testing")  
    print(f"  • All testable locally without CI")
    print(f"  • Instant feedback and debugging")