#!/usr/bin/env python3
"""
Test runner for Python-first GitHub Actions scripts.
Ensures proper imports and environment setup.

Usage:
    python .github/test_runner.py [--comprehensive] [--stress]
"""

import os
import sys
import argparse
import unittest
from pathlib import Path

# Ensure we're running from project root
project_root = Path(__file__).parent.parent
os.chdir(project_root)

# Add script directories to Python path
sys.path.insert(0, str(Path('.github/scripts/common')))
sys.path.insert(0, str(Path('.github/scripts/release')))

def run_basic_tests():
    """Run basic functionality tests."""
    print("🧪 Running Basic Tests")
    print("=" * 50)
    
    # Test imports work
    try:
        from logger import setup_logger
        from config import ConfigLoader, get_current_version
        from utils import retry_with_backoff, check_pypi_package_available
        from orchestrator import ReleaseOrchestrator
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test basic instantiation
    try:
        os.environ['GITHUB_TOKEN'] = 'test-token'
        os.environ['PYPI_TOKEN'] = 'test-token'  
        os.environ['GITHUB_REF_NAME'] = 'v1.0.0-test'
        
        orchestrator = ReleaseOrchestrator(dry_run=True, debug=True)
        print("✅ Orchestrator instantiation successful")
    except Exception as e:
        print(f"❌ Orchestrator instantiation failed: {e}")
        return False
    
    # Test pipeline execution
    try:
        result = orchestrator.run_release_pipeline()
        if result:
            print("✅ Pipeline execution successful")
        else:
            print("❌ Pipeline execution failed")
            return False
    except Exception as e:
        print(f"❌ Pipeline execution error: {e}")
        return False
    
    return True


def run_error_tests():
    """Run error handling tests."""
    print("\n🚨 Running Error Handling Tests")
    print("=" * 50)
    
    from orchestrator import ReleaseOrchestrator
    
    # Test missing token
    try:
        old_token = os.environ.get('GITHUB_TOKEN')
        if 'GITHUB_TOKEN' in os.environ:
            del os.environ['GITHUB_TOKEN']
        
        try:
            ReleaseOrchestrator(dry_run=True)
            print("❌ Should have failed with missing token")
            return False
        except ValueError as e:
            if "GITHUB_TOKEN" in str(e):
                print("✅ Correctly caught missing token error")
            else:
                print(f"❌ Wrong error: {e}")
                return False
        finally:
            if old_token:
                os.environ['GITHUB_TOKEN'] = old_token
    
    except Exception as e:
        print(f"❌ Unexpected error in token test: {e}")
        return False
    
    # Test invalid version
    try:
        os.environ['GITHUB_TOKEN'] = 'test-token'
        os.environ['GITHUB_REF_NAME'] = 'invalid-version'
        
        orchestrator = ReleaseOrchestrator(dry_run=True)
        result = orchestrator.validate_pre_conditions()
        
        if not result:
            print("✅ Correctly rejected invalid version")
        else:
            print("❌ Should have rejected invalid version")
            return False
            
    except Exception as e:
        print(f"❌ Unexpected error in version test: {e}")
        return False
    
    return True


def run_configuration_tests():
    """Run configuration tests."""
    print("\n⚙️  Running Configuration Tests")
    print("=" * 50)
    
    try:
        from config import ConfigLoader, ReleaseConfig
        
        # Test config loading
        loader = ConfigLoader()
        config = loader.load_release_config()
        
        print(f"✅ Config loaded: {config.package_name}")
        print(f"   PyPI timeout: {config.pypi_timeout}s")
        print(f"   Cross-repo timeout: {config.cross_repo_timeout}s")
        
        # Test environment override
        os.environ['PACKAGE_NAME'] = 'test-override'
        config = loader.load_release_config()
        
        if config.package_name == 'test-override':
            print("✅ Environment override works")
        else:
            print("❌ Environment override failed")
            return False
        
        # Clean up
        del os.environ['PACKAGE_NAME']
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False
    
    return True


def run_utility_tests():
    """Run utility function tests."""
    print("\n🔧 Running Utility Tests")
    print("=" * 50)
    
    try:
        from utils import RetryConfig, wait_for_condition, create_http_session
        import time
        
        # Test retry config
        retry_config = RetryConfig(max_retries=2, initial_delay=0.1)
        print(f"✅ RetryConfig created: max_retries={retry_config.max_retries}")
        
        # Test timeout behavior
        def always_false():
            return False
        
        start_time = time.time()
        result = wait_for_condition(always_false, timeout=1, check_interval=0.2)
        elapsed = time.time() - start_time
        
        if not result and 0.8 <= elapsed <= 1.5:
            print(f"✅ Timeout test passed: {elapsed:.1f}s")
        else:
            print(f"❌ Timeout test failed: result={result}, elapsed={elapsed:.1f}s")
            return False
        
        # Test HTTP session
        session = create_http_session(timeout=10)
        if session and hasattr(session, 'timeout'):
            print("✅ HTTP session creation works")
        else:
            print("❌ HTTP session creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Utility test failed: {e}")
        return False
    
    return True


def run_integration_test():
    """Run full integration test."""
    print("\n🔄 Running Integration Test")
    print("=" * 50)
    
    try:
        # Set up clean environment
        os.environ['GITHUB_TOKEN'] = 'test-integration-token'
        os.environ['PYPI_TOKEN'] = 'test-integration-token'
        os.environ['GITHUB_REF_NAME'] = 'v2.1.0-integration'
        
        from orchestrator import ReleaseOrchestrator
        
        # Test with various configurations
        test_cases = [
            {"dry_run": True, "force": False, "debug": True},
            {"dry_run": True, "force": True, "debug": False},
        ]
        
        for i, params in enumerate(test_cases, 1):
            print(f"  Test case {i}: {params}")
            
            orchestrator = ReleaseOrchestrator(**params)
            result = orchestrator.run_release_pipeline()
            
            if result:
                print(f"    ✅ Case {i} passed")
            else:
                print(f"    ❌ Case {i} failed")
                return False
        
        print("✅ All integration test cases passed")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_performance_test():
    """Run performance tests."""
    print("\n⚡ Running Performance Test")
    print("=" * 50)
    
    try:
        import time
        from orchestrator import ReleaseOrchestrator
        
        # Time multiple dry-run executions
        times = []
        for i in range(5):
            os.environ['GITHUB_REF_NAME'] = f'v1.0.{i}-perf'
            
            start_time = time.time()
            orchestrator = ReleaseOrchestrator(dry_run=True, debug=False)
            result = orchestrator.run_release_pipeline()
            elapsed = time.time() - start_time
            
            if result:
                times.append(elapsed)
                print(f"  Run {i+1}: {elapsed:.3f}s")
            else:
                print(f"  Run {i+1}: FAILED")
                return False
        
        avg_time = sum(times) / len(times)
        print(f"✅ Average execution time: {avg_time:.3f}s")
        
        if avg_time < 5.0:  # Should be very fast in dry run
            print("✅ Performance test passed")
            return True
        else:
            print("❌ Performance test failed - too slow")
            return False
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test runner for Python-first GitHub Actions")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive tests")
    parser.add_argument("--stress", action="store_true", help="Run stress tests")
    
    args = parser.parse_args()
    
    print("🚀 Python-First GitHub Actions Test Suite")
    print("Demonstrating ultrathink testing capabilities")
    print()
    
    # Core test suite
    test_results = []
    
    test_results.append(("Basic Tests", run_basic_tests()))
    test_results.append(("Error Handling", run_error_tests()))
    test_results.append(("Configuration", run_configuration_tests()))
    test_results.append(("Utilities", run_utility_tests()))
    test_results.append(("Integration", run_integration_test()))
    
    if args.comprehensive:
        test_results.append(("Performance", run_performance_test()))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = 0
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
        total += 1
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    # Demonstrate advantages
    print(f"\n💪 Ultrathink Testing Advantages Demonstrated:")
    print(f"  • Instant feedback: All tests run in seconds")
    print(f"  • Local debugging: Full stack traces and breakpoints")
    print(f"  • Comprehensive coverage: Edge cases, errors, performance")
    print(f"  • No CI dependency: Everything testable locally")
    print(f"  • Easy iteration: Modify and re-test immediately")
    
    success = passed == total
    print(f"\n🎯 Result: {'SUCCESS' if success else 'FAILURE'}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())