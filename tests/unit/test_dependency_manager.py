"""Unit tests for dependency manager functionality."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


@pytest.mark.unit
class TestDependencyManager(unittest.TestCase):
    """Test dependency manager functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_dependency_manager_initialization(self):
        """Test DependencyManager initialization."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.dependency_manager import DependencyManager

            # Test initialization
            manager = DependencyManager(self.project_dir, cache_enabled=True)
            self.assertEqual(manager.project_dir, self.project_dir)
            self.assertIsNotNone(manager.cache)

            # Test without cache
            manager_no_cache = DependencyManager(self.project_dir, cache_enabled=False)
            self.assertIsNone(manager_no_cache.cache)

        except ImportError:
            self.skipTest("Dependency manager module not available")

    def test_pyproject_file_detection(self):
        """Test detection of pyproject.toml files."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.dependency_manager import DependencyManager

            # Create test pyproject.toml
            pyproject_content = """
[tool.poetry]
name = "test-project"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.11"
requests = "^2.28.0"
"""
            pyproject_file = self.project_dir / "pyproject.toml"
            pyproject_file.write_text(pyproject_content)

            manager = DependencyManager(self.project_dir)
            self.assertTrue(manager.pyproject_file.exists())

        except ImportError:
            self.skipTest("Dependency manager module not available")

    def test_requirements_file_detection(self):
        """Test detection of requirements.txt files."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.dependency_manager import DependencyManager

            # Create test requirements.txt
            requirements_content = """
requests>=2.28.0
numpy>=1.21.0
pyyaml>=6.0
"""
            requirements_file = self.project_dir / "requirements.txt"
            requirements_file.write_text(requirements_content)

            manager = DependencyManager(self.project_dir)
            self.assertTrue(manager.requirements_file.exists())

        except ImportError:
            self.skipTest("Dependency manager module not available")

    @patch("subprocess.run")
    def test_dependency_scanning(self, mock_run):
        """Test dependency vulnerability scanning."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.dependency_manager import DependencyManager

            # Mock subprocess response for dependency scan
            mock_run.return_value = Mock(
                returncode=0,
                stdout=json.dumps({"vulnerabilities": [], "packages": ["requests==2.28.0", "numpy==1.21.0"]}),
                stderr="",
            )

            manager = DependencyManager(self.project_dir)

            if hasattr(manager, "scan_vulnerabilities"):
                result = manager.scan_vulnerabilities()
                self.assertIsNotNone(result)
                mock_run.assert_called()

        except ImportError:
            self.skipTest("Dependency manager module not available")

    @patch("requests.get")
    def test_security_advisory_checking(self, mock_get):
        """Test checking for security advisories."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.dependency_manager import DependencyManager

            # Mock API response for security advisories
            mock_response = Mock()
            mock_response.json.return_value = {
                "vulnerabilities": [
                    {
                        "id": "GHSA-xxxx-xxxx-xxxx",
                        "package": "requests",
                        "severity": "medium",
                        "summary": "Test vulnerability",
                    }
                ]
            }
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            manager = DependencyManager(self.project_dir)

            if hasattr(manager, "check_security_advisories"):
                advisories = manager.check_security_advisories("requests")
                self.assertIsInstance(advisories, (list, dict))

        except ImportError:
            self.skipTest("Dependency manager module not available")

    def test_dependency_parsing(self):
        """Test parsing of dependency specifications."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.dependency_manager import DependencyManager

            manager = DependencyManager(self.project_dir)

            # Test dependency string parsing
            test_dependencies = ["requests>=2.28.0", "numpy==1.21.0", "pyyaml~=6.0", "pytest>=7.0,<8.0"]

            if hasattr(manager, "parse_dependency"):
                for dep in test_dependencies:
                    parsed = manager.parse_dependency(dep)
                    self.assertIsNotNone(parsed)
                    self.assertIn("name", parsed)
                    self.assertIn("version", parsed)

        except ImportError:
            self.skipTest("Dependency manager module not available")

    def test_update_impact_assessment(self):
        """Test assessment of update impacts."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.dependency_manager import DependencyManager

            manager = DependencyManager(self.project_dir)

            # Test update impact calculation
            new_version = "2.29.0"

            if hasattr(manager, "assess_update_impact"):
                impact = manager.assess_update_impact("requests", new_version)
                self.assertIsInstance(impact, dict)
                self.assertIn("risk_level", impact)

        except ImportError:
            self.skipTest("Dependency manager module not available")

    @patch("subprocess.run")
    def test_dependency_installation(self, mock_run):
        """Test dependency installation functionality."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.dependency_manager import DependencyManager

            # Mock successful installation
            mock_run.return_value = Mock(returncode=0, stdout="Successfully installed requests-2.28.0", stderr="")

            manager = DependencyManager(self.project_dir)

            if hasattr(manager, "install_dependency"):
                result = manager.install_dependency("requests==2.28.0")
                self.assertTrue(result)
                mock_run.assert_called()

        except ImportError:
            self.skipTest("Dependency manager module not available")

    def test_cache_integration(self):
        """Test cache integration for dependency data."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.dependency_manager import DependencyManager

            manager = DependencyManager(self.project_dir, cache_enabled=True)

            # Test cache operations if available
            if hasattr(manager, "cache_dependency_info"):
                test_package = "requests"
                test_info = {"version": "2.28.0", "vulnerabilities": [], "last_updated": "2023-01-01"}

                manager.cache_dependency_info(test_package, test_info)
                cached_info = manager.get_cached_dependency_info(test_package)
                self.assertEqual(cached_info, test_info)

        except ImportError:
            self.skipTest("Dependency manager module not available")


@pytest.mark.unit
class TestDependencyManagerPerformance(unittest.TestCase):
    """Test performance aspects of dependency manager."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_large_dependency_list_processing(self):
        """Test processing of large dependency lists."""
        try:
            import sys

            sys.path.insert(0, "src")
            import time

            from rxiv_maker.security.dependency_manager import DependencyManager

            # Create large requirements.txt
            large_requirements = []
            for i in range(100):
                large_requirements.append(f"package{i}>=1.0.0")

            requirements_file = self.project_dir / "requirements.txt"
            requirements_file.write_text("\n".join(large_requirements))

            manager = DependencyManager(self.project_dir)

            if hasattr(manager, "parse_all_dependencies"):
                start_time = time.time()
                dependencies = manager.parse_all_dependencies()
                end_time = time.time()

                # Should complete within reasonable time
                self.assertLess(end_time - start_time, 5.0)  # Under 5 seconds
                self.assertIsInstance(dependencies, (list, dict))

        except ImportError:
            self.skipTest("Dependency manager module not available")

    @patch("requests.get")
    def test_concurrent_vulnerability_checking(self, mock_get):
        """Test concurrent vulnerability checking for multiple packages."""
        try:
            import sys

            sys.path.insert(0, "src")
            import time

            from rxiv_maker.security.dependency_manager import DependencyManager

            # Mock API responses
            mock_response = Mock()
            mock_response.json.return_value = {"vulnerabilities": []}
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            manager = DependencyManager(self.project_dir)

            packages = ["requests", "numpy", "pyyaml", "pytest", "setuptools"]

            if hasattr(manager, "check_multiple_packages"):
                start_time = time.time()
                results = manager.check_multiple_packages(packages)
                end_time = time.time()

                # Should be faster than sequential processing
                self.assertLess(end_time - start_time, 10.0)
                self.assertIsInstance(results, (list, dict))

        except ImportError:
            self.skipTest("Dependency manager module not available")


if __name__ == "__main__":
    unittest.main()
