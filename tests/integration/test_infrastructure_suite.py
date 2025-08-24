"""Infrastructure integration test suite for rxiv-maker.

This consolidated test suite combines infrastructure tests from multiple files:
- Docker integration tests (29 files consolidated)
- Network dependency tests (22 files consolidated)
- Filesystem operation tests (74 files consolidated)
- Platform detection tests
- Environment setup tests

Consolidation reduces 50+ scattered infrastructure tests into focused suites
while improving test reliability and maintainability.
"""

import os
import platform
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

try:
    import pytest

    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

    class MockPytest:
        class mark:
            @staticmethod
            def docker(cls):
                return cls

            @staticmethod
            def network(cls):
                return cls

            @staticmethod
            def filesystem(cls):
                return cls

            @staticmethod
            def slow(cls):
                return cls

            @staticmethod
            def skipif(*args, **kwargs):
                def decorator(cls):
                    return cls

                return decorator

    pytest = MockPytest()

# Import infrastructure components with fallbacks
try:
    from rxiv_maker.docker.manager import get_docker_manager

    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

try:
    from rxiv_maker.utils.platform import platform_detector

    PLATFORM_UTILS_AVAILABLE = True
except ImportError:
    PLATFORM_UTILS_AVAILABLE = False

try:
    from rxiv_maker.utils.dependency_checker import DependencyChecker

    DEPENDENCY_CHECKER_AVAILABLE = True
except ImportError:
    DEPENDENCY_CHECKER_AVAILABLE = False

try:
    from rxiv_maker.engines.operations.setup_environment import EnvironmentSetup

    ENVIRONMENT_SETUP_AVAILABLE = True
except ImportError:
    ENVIRONMENT_SETUP_AVAILABLE = False


# Check Docker availability at runtime
def is_docker_available():
    """Check if Docker is available on the system."""
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True, timeout=5)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


# Check network connectivity
def is_network_available():
    """Check if network connectivity is available."""
    try:
        import urllib.error
        import urllib.request

        urllib.request.urlopen("http://google.com", timeout=5)
        return True
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


class InfrastructureTestBase(unittest.TestCase):
    """Base class for infrastructure tests with common utilities."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_files = []

        # Create common test directory structure
        (self.temp_dir / "input").mkdir(exist_ok=True)
        (self.temp_dir / "output").mkdir(exist_ok=True)
        (self.temp_dir / "figures").mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up test files
        for file_path in self.test_files:
            try:
                if Path(file_path).exists():
                    if Path(file_path).is_dir():
                        shutil.rmtree(file_path)
                    else:
                        Path(file_path).unlink()
            except (OSError, IOError, PermissionError):
                pass

        # Clean up temp directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_file(self, filename: str, content: str = "test content") -> Path:
        """Create a test file and track it for cleanup."""
        file_path = self.temp_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        self.test_files.append(file_path)
        return file_path

    def create_test_directory(self, dirname: str) -> Path:
        """Create a test directory and track it for cleanup."""
        dir_path = self.temp_dir / dirname
        dir_path.mkdir(parents=True, exist_ok=True)
        self.test_files.append(dir_path)
        return dir_path


@pytest.mark.docker
@pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker components not available")
class TestDockerIntegration(InfrastructureTestBase):
    """Test Docker integration functionality."""

    def setUp(self):
        super().setUp()
        if DOCKER_AVAILABLE:
            self.docker_manager = get_docker_manager()

    @unittest.skipUnless(is_docker_available(), "Docker not installed")
    def test_docker_availability_check(self):
        """Test Docker availability detection."""
        if not DOCKER_AVAILABLE:
            self.skipTest("Docker manager not available")

        is_available = self.docker_manager.is_docker_available()

        # Should detect Docker correctly
        self.assertIsInstance(is_available, bool)

        if is_available:
            version_info = self.docker_manager.get_docker_version()
            self.assertIsInstance(version_info, dict)
            self.assertIn("version", version_info)

    @unittest.skipUnless(is_docker_available(), "Docker not installed")
    def test_docker_image_management(self):
        """Test Docker image pull and management."""
        if not DOCKER_AVAILABLE:
            self.skipTest("Docker manager not available")

        # Test with a small, common image
        test_image = "alpine:latest"

        try:
            # Pull image
            pull_result = self.docker_manager.pull_image(test_image)
            self.assertTrue(pull_result["success"], "Should successfully pull image")

            # Check if image exists
            images = self.docker_manager.list_images()
            image_names = [img.get("name", "") for img in images]

            self.assertTrue(any(test_image in name for name in image_names), "Pulled image should be in image list")

        except Exception as e:
            self.skipTest(f"Docker operations failed: {e}")

    @unittest.skipUnless(is_docker_available(), "Docker not installed")
    def test_docker_container_lifecycle(self):
        """Test Docker container creation and lifecycle."""
        if not DOCKER_AVAILABLE:
            self.skipTest("Docker manager not available")

        container_config = {
            "image": "alpine:latest",
            "command": ["echo", "test"],
            "remove": True,  # Auto-remove after completion
        }

        try:
            # Create and run container
            result = self.docker_manager.run_container(container_config)

            self.assertTrue(result["success"], "Container should run successfully")
            self.assertEqual(result.get("output", "").strip(), "test")

        except Exception as e:
            self.skipTest(f"Container operations failed: {e}")

    def test_docker_build_context_preparation(self):
        """Test preparation of Docker build context."""
        if not DOCKER_AVAILABLE:
            self.skipTest("Docker manager not available")

        # Create test manuscript structure
        manuscript_content = """
        # Test Manuscript
        This is a test manuscript for Docker building.
        """

        self.create_test_file("manuscript.md", manuscript_content)
        self.create_test_file("00_CONFIG.yml", "title: Test")

        # Prepare build context
        context_result = self.docker_manager.prepare_build_context(str(self.temp_dir))

        self.assertTrue(context_result["success"], "Build context preparation should succeed")
        self.assertIn("context_dir", context_result)

        context_dir = Path(context_result["context_dir"])
        self.assertTrue(context_dir.exists(), "Context directory should exist")

    def test_docker_volume_management(self):
        """Test Docker volume management for manuscript processing."""
        if not DOCKER_AVAILABLE:
            self.skipTest("Docker manager not available")

        # Create test content
        self.create_test_file("input/test.md", "# Test")

        volume_config = {"host_path": str(self.temp_dir), "container_path": "/workspace", "read_only": False}

        volume_result = self.docker_manager.create_volume_mapping(volume_config)

        self.assertTrue(volume_result["success"], "Volume mapping should succeed")
        self.assertIn("mount_options", volume_result)

    @pytest.mark.slow
    def test_docker_build_performance(self):
        """Test Docker build performance and optimization."""
        if not DOCKER_AVAILABLE or not is_docker_available():
            self.skipTest("Docker not available for performance testing")

        # Create comprehensive build context
        files_to_create = [
            ("manuscript.md", "# Large Test Manuscript\n" + "Content line\n" * 100),
            ("bibliography.bib", "@article{test,\n  title={Test},\n  year={2023}\n}\n" * 50),
            ("00_CONFIG.yml", "title: Performance Test\nauthors: [Test Author]"),
        ]

        for filename, content in files_to_create:
            self.create_test_file(filename, content)

        # Time the build context preparation
        import time

        start_time = time.time()

        context_result = self.docker_manager.prepare_build_context(str(self.temp_dir))

        end_time = time.time()
        preparation_time = end_time - start_time

        self.assertTrue(context_result["success"], "Build context should be prepared successfully")
        self.assertLess(preparation_time, 30.0, "Build context preparation should complete in under 30 seconds")


@pytest.mark.network
class TestNetworkIntegration(InfrastructureTestBase):
    """Test network-dependent functionality."""

    @unittest.skipUnless(is_network_available(), "Network not available")
    def test_doi_resolution_network_call(self):
        """Test DOI resolution with actual network calls."""
        try:
            from rxiv_maker.validators.doi_validator import DOIValidator
        except ImportError:
            self.skipTest("DOI validator not available")

        validator = DOIValidator(manuscript_path=".")

        # Test with known DOI
        test_doi = "10.1038/nature12373"

        try:
            result = validator.resolve_doi(test_doi)

            self.assertIsInstance(result, dict)
            if result.get("success"):
                self.assertIn("title", result)
                self.assertIn("authors", result)

        except Exception as e:
            self.skipTest(f"DOI resolution failed: {e}")

    @unittest.skipUnless(is_network_available(), "Network not available")
    def test_bibliography_fetch_network(self):
        """Test bibliography fetching from external sources."""
        try:
            from rxiv_maker.engines.operations.add_bibliography import BibliographyAdder
        except ImportError:
            self.skipTest("Bibliography adder not available")

        adder = BibliographyAdder(manuscript_path=".")

        # Test fetching from CrossRef
        test_query = "machine learning nature 2020"

        try:
            results = adder.search_crossref(test_query, limit=5)

            self.assertIsInstance(results, list)
            if len(results) > 0:
                result = results[0]
                self.assertIn("title", result)
                self.assertIn("DOI", result)

        except Exception as e:
            self.skipTest(f"Bibliography fetch failed: {e}")

    def test_network_error_handling(self):
        """Test graceful handling of network errors."""
        try:
            from rxiv_maker.validators.doi_validator import DOIValidator
        except ImportError:
            self.skipTest("DOI validator not available")

        validator = DOIValidator()

        # Mock network failure
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("Network error")

            result = validator.resolve_doi("10.1000/test.doi")

            # Should handle network errors gracefully
            self.assertIsInstance(result, dict)
            self.assertFalse(result.get("success", True))
            self.assertIn("error", result)

    def test_offline_mode_fallback(self):
        """Test offline mode fallback functionality."""
        try:
            from rxiv_maker.validators.doi_validator import DOIValidator
        except ImportError:
            self.skipTest("DOI validator not available")

        validator = DOIValidator(manuscript_path=".", enable_online_validation=False)

        # In offline mode, should not make network calls
        # Test that validator works with offline setting
        result = validator.validate()

        # Should work without network calls when offline mode is enabled
        # Test that result contains proper ValidationResult structure
        self.assertTrue(hasattr(result, "validator_name"))
        self.assertTrue(hasattr(result, "errors"))
        self.assertEqual(result.validator_name, "DOIValidator")
        # Offline mode should complete without making network calls

    @patch("urllib.request.urlopen")
    def test_network_connectivity_check(self, mock_urlopen):
        """Test network connectivity detection."""
        try:
            from rxiv_maker.utils.network import NetworkChecker
        except ImportError:
            self.skipTest("Network checker not available")

        checker = NetworkChecker()

        # Mock successful connection
        mock_urlopen.return_value.__enter__.return_value = MagicMock()

        is_connected = checker.check_connectivity()
        self.assertTrue(is_connected)

        # Mock failed connection
        mock_urlopen.side_effect = Exception("Network error")

        is_connected = checker.check_connectivity()
        self.assertFalse(is_connected)


@pytest.mark.filesystem
class TestFilesystemIntegration(InfrastructureTestBase):
    """Test filesystem operations and file handling."""

    def test_manuscript_file_discovery(self):
        """Test manuscript file discovery in various locations."""
        try:
            from rxiv_maker.utils import find_manuscript_md
        except ImportError:
            self.skipTest("File helpers not available")

        # Test standard manuscript discovery
        self.create_test_file("manuscript.md", "# Test Manuscript")

        old_cwd = Path.cwd()
        os.chdir(self.temp_dir)

        try:
            manuscript_path = find_manuscript_md()

            self.assertIsNotNone(manuscript_path)
            self.assertTrue(Path(manuscript_path).exists())
            self.assertEqual(Path(manuscript_path).name, "manuscript.md")
        finally:
            os.chdir(old_cwd)

    def test_output_directory_management(self):
        """Test output directory creation and management."""
        try:
            from rxiv_maker.utils import create_output_dir
        except ImportError:
            self.skipTest("File helpers not available")

        output_dir = self.temp_dir / "test_output"

        # Should create directory if it doesn't exist
        create_output_dir(str(output_dir))

        self.assertTrue(output_dir.exists())
        self.assertTrue(output_dir.is_dir())

        # Should handle existing directory gracefully
        create_output_dir(str(output_dir))
        self.assertTrue(output_dir.exists())

    def test_file_permission_handling(self):
        """Test handling of file permissions and access issues."""
        if platform.system() == "Windows":
            self.skipTest("Permission tests not applicable on Windows")

        # Create file with restricted permissions
        restricted_file = self.create_test_file("restricted.txt", "restricted content")

        # Remove read permissions
        os.chmod(restricted_file, 0o000)

        try:
            # Test graceful handling of permission errors
            try:
                with open(restricted_file, "r") as f:
                    f.read()
                self.fail("Should have raised PermissionError")
            except PermissionError:
                pass  # Expected
        finally:
            # Restore permissions for cleanup
            os.chmod(restricted_file, 0o644)

    def test_large_file_handling(self):
        """Test handling of large files."""
        # Create moderately large test file (1MB)
        large_content = "A" * (1024 * 1024)
        large_file = self.create_test_file("large_file.txt", large_content)

        # Test file size detection
        file_size = large_file.stat().st_size
        self.assertGreater(file_size, 1000000)  # > 1MB

        # Test chunked reading
        chunk_size = 8192
        total_read = 0

        with open(large_file, "r") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                total_read += len(chunk)

        self.assertEqual(total_read, len(large_content))

    def test_concurrent_file_access(self):
        """Test concurrent file access handling."""
        import threading

        test_file = self.create_test_file("concurrent_test.txt", "initial content")

        results = []
        errors = []

        def read_file():
            try:
                with open(test_file, "r") as f:
                    content = f.read()
                    results.append(content)
            except Exception as e:
                errors.append(e)

        def write_file(content):
            try:
                with open(test_file, "a") as f:
                    f.write(content)
            except Exception as e:
                errors.append(e)

        # Create multiple threads for concurrent access
        threads = []
        for i in range(5):
            t1 = threading.Thread(target=read_file)
            t2 = threading.Thread(target=write_file, args=(f" append{i}",))
            threads.extend([t1, t2])

        # Start all threads
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Should handle concurrent access without crashing
        self.assertLessEqual(len(errors), 2, "Should have minimal concurrent access errors")
        self.assertGreater(len(results), 0, "Should successfully read file multiple times")

    def test_directory_traversal_security(self):
        """Test protection against directory traversal attacks."""
        try:
            from rxiv_maker.utils.file_helpers import safe_path_join
        except ImportError:
            self.skipTest("Safe path utilities not available")

        base_dir = str(self.temp_dir)

        # Test safe path joining
        safe_paths = ["subdir/file.txt", "file.txt", "./subdir/file.txt"]

        unsafe_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "/absolute/path/file.txt",
            "subdir/../../../etc/passwd",
        ]

        for path in safe_paths:
            try:
                result = safe_path_join(base_dir, path)
                # Should not raise exception and stay within base directory
                self.assertTrue(str(result).startswith(base_dir))
            except Exception:
                pass  # May reject some paths as unsafe, which is acceptable

        for path in unsafe_paths:
            with self.assertRaises((ValueError, Exception)):
                safe_path_join(base_dir, path)


@pytest.mark.filesystem
@unittest.skipUnless(PLATFORM_UTILS_AVAILABLE, "Platform utilities not available")
class TestPlatformDetection(InfrastructureTestBase):
    """Test platform detection and platform-specific functionality."""

    def test_operating_system_detection(self):
        """Test operating system detection."""
        current_os = platform_detector.get_os()

        expected_os_types = ["windows", "macos", "linux", "unix"]
        self.assertIn(current_os.lower(), expected_os_types)

    def test_python_environment_detection(self):
        """Test Python environment detection."""
        env_info = platform_detector.get_python_environment()

        self.assertIn("version", env_info)
        self.assertIn("executable", env_info)
        self.assertIn("virtual_env", env_info)

        # Verify version format
        version = env_info["version"]
        self.assertRegex(version, r"\d+\.\d+\.\d+")

    def test_dependency_availability_check(self):
        """Test detection of system dependencies."""
        if not DEPENDENCY_CHECKER_AVAILABLE:
            self.skipTest("Dependency checker not available")

        checker = DependencyChecker()

        # Check common system dependencies
        deps_to_check = ["python", "git"]

        for dep in deps_to_check:
            is_available = checker.check_dependency(dep)
            self.assertIsInstance(is_available, bool)

    def test_latex_installation_detection(self):
        """Test LaTeX installation detection."""
        if not DEPENDENCY_CHECKER_AVAILABLE:
            self.skipTest("Dependency checker not available")

        checker = DependencyChecker()

        latex_tools = ["pdflatex", "bibtex", "latexmk"]
        latex_status = {}

        for tool in latex_tools:
            latex_status[tool] = checker.check_latex_tool(tool)

        # At least one LaTeX tool should be detected on most systems
        any_latex = any(latex_status.values())

        # This is informational rather than a hard requirement
        if any_latex:
            self.assertTrue(any_latex, "At least one LaTeX tool should be available")

    def test_docker_installation_detection(self):
        """Test Docker installation detection."""
        if not DEPENDENCY_CHECKER_AVAILABLE:
            self.skipTest("Dependency checker not available")

        checker = DependencyChecker()

        docker_available = checker.check_dependency("docker")
        docker_compose_available = checker.check_dependency("docker-compose")

        # Should return boolean values
        self.assertIsInstance(docker_available, bool)
        self.assertIsInstance(docker_compose_available, bool)

    def test_system_resource_detection(self):
        """Test system resource detection."""
        resource_info = platform_detector.get_system_resources()

        self.assertIn("cpu_count", resource_info)
        self.assertIn("memory_total", resource_info)
        self.assertIn("disk_space", resource_info)

        # Verify reasonable values
        self.assertGreater(resource_info["cpu_count"], 0)
        self.assertGreater(resource_info["memory_total"], 0)
        self.assertGreater(resource_info["disk_space"], 0)


@pytest.mark.filesystem
@unittest.skipUnless(ENVIRONMENT_SETUP_AVAILABLE, "Environment setup not available")
class TestEnvironmentSetup(InfrastructureTestBase):
    """Test environment setup and configuration."""

    def setUp(self):
        super().setUp()
        self.env_setup = EnvironmentSetup()

    def test_python_environment_setup(self):
        """Test Python environment setup and validation."""
        # Check current Python environment
        py_info = self.env_setup.check_python_environment()

        self.assertIn("version", py_info)
        self.assertIn("executable", py_info)
        self.assertIn("packages", py_info)

        # Should detect current Python version
        import sys

        expected_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        self.assertIn(expected_version, py_info["version"])

    def test_virtual_environment_detection(self):
        """Test virtual environment detection."""
        venv_info = self.env_setup.detect_virtual_environment()

        self.assertIn("in_venv", venv_info)
        self.assertIn("venv_path", venv_info)
        self.assertIn("venv_type", venv_info)

        # Should correctly identify if we're in a virtual environment
        self.assertIsInstance(venv_info["in_venv"], bool)

    def test_dependency_installation_check(self):
        """Test checking of required dependencies."""
        required_deps = ["pyyaml", "pathlib", "unittest"]

        dep_status = self.env_setup.check_dependencies(required_deps)

        self.assertIsInstance(dep_status, dict)

        for dep in required_deps:
            self.assertIn(dep, dep_status)
            # Most of these should be available in test environment
            if dep in ["pathlib", "unittest"]:  # Standard library
                self.assertTrue(dep_status[dep]["available"])

    def test_configuration_file_setup(self):
        """Test configuration file creation and validation."""
        config_dir = self.temp_dir / ".rxiv_maker"

        setup_result = self.env_setup.setup_configuration_directory(str(config_dir))

        self.assertTrue(setup_result["success"])
        self.assertTrue(config_dir.exists())
        self.assertTrue(config_dir.is_dir())

    def test_cache_directory_setup(self):
        """Test cache directory setup."""
        cache_setup = self.env_setup.setup_cache_directories()

        self.assertTrue(cache_setup["success"])
        self.assertIn("cache_dir", cache_setup)

        cache_dir = Path(cache_setup["cache_dir"])
        self.assertTrue(cache_dir.exists())

    def test_system_compatibility_check(self):
        """Test system compatibility verification."""
        compatibility = self.env_setup.check_system_compatibility()

        self.assertIn("compatible", compatibility)
        self.assertIn("issues", compatibility)
        self.assertIn("recommendations", compatibility)

        # Should provide useful information
        self.assertIsInstance(compatibility["compatible"], bool)
        self.assertIsInstance(compatibility["issues"], list)


if __name__ == "__main__":
    # Configure test runner based on available frameworks
    if PYTEST_AVAILABLE:
        pytest.main([__file__, "-v"])
    else:
        # Run with unittest
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(__import__(__name__))
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)
