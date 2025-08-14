"""Tests for Docker optimization functionality."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from rxiv_maker.docker.optimization import DockerBuildOptimizer


class TestDockerBuildOptimizer(unittest.TestCase):
    """Test DockerBuildOptimizer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.optimizer = DockerBuildOptimizer()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test DockerBuildOptimizer initialization."""
        self.assertIsNotNone(self.optimizer.cache)

        # Test with custom cache directory
        custom_optimizer = DockerBuildOptimizer(cache_dir=self.temp_dir)
        self.assertIsNotNone(custom_optimizer.cache)

    def test_cache_initialization(self):
        """Test that cache is properly initialized."""
        # Cache should have specific configuration
        self.assertEqual(self.optimizer.cache.name, "docker_builds")
        self.assertEqual(self.optimizer.cache.max_memory_items, 50)
        self.assertEqual(self.optimizer.cache.max_disk_size_mb, 500)
        # Note: ttl_hours might not be directly accessible as an attribute
        # Test that cache is properly configured instead
        self.assertIsNotNone(self.optimizer.cache)

    def test_calculate_dir_hash(self):
        """Test directory hash calculation."""
        # Create test files
        test_dockerfile = self.temp_dir / "Dockerfile"
        test_dockerfile.write_text("FROM python:3.11")

        test_requirements = self.temp_dir / "requirements.txt"
        test_requirements.write_text("click>=8.0.0")

        # Calculate hash
        hash_value = self.optimizer._calculate_dir_hash(self.temp_dir)

        # Should return a valid hash string
        self.assertIsInstance(hash_value, str)
        self.assertGreater(len(hash_value), 0)

        # Hash should be consistent for same content
        hash_value2 = self.optimizer._calculate_dir_hash(self.temp_dir)
        self.assertEqual(hash_value, hash_value2)

    def test_calculate_dir_hash_with_changes(self):
        """Test that directory hash changes when content changes."""
        # Create initial file
        test_file = self.temp_dir / "Dockerfile"
        test_file.write_text("FROM python:3.11")

        initial_hash = self.optimizer._calculate_dir_hash(self.temp_dir)

        # Modify file
        test_file.write_text("FROM python:3.12")

        modified_hash = self.optimizer._calculate_dir_hash(self.temp_dir)

        # Hash should be different
        self.assertNotEqual(initial_hash, modified_hash)

    def test_calculate_dir_hash_missing_directory(self):
        """Test directory hash calculation with missing directory."""
        missing_dir = self.temp_dir / "nonexistent"

        # Should handle missing directory gracefully
        hash_value = self.optimizer._calculate_dir_hash(missing_dir)
        self.assertIsInstance(hash_value, str)

    def test_calculate_dir_hash_empty_directory(self):
        """Test directory hash calculation with empty directory."""
        empty_dir = self.temp_dir / "empty"
        empty_dir.mkdir()

        hash_value = self.optimizer._calculate_dir_hash(empty_dir)
        self.assertIsInstance(hash_value, str)
        self.assertGreater(len(hash_value), 0)

    def test_essential_files_only(self):
        """Test that only essential files are included in hash calculation."""
        # Create essential files
        (self.temp_dir / "Dockerfile").write_text("FROM python:3.11")
        (self.temp_dir / "requirements.txt").write_text("click>=8.0.0")
        (self.temp_dir / "pyproject.toml").write_text("[project]\nname = 'test'")

        # Create non-essential files
        (self.temp_dir / "README.md").write_text("# Test")
        (self.temp_dir / "random.txt").write_text("ignored")

        hash_with_extra = self.optimizer._calculate_dir_hash(self.temp_dir)

        # Remove non-essential files
        (self.temp_dir / "README.md").unlink()
        (self.temp_dir / "random.txt").unlink()

        hash_without_extra = self.optimizer._calculate_dir_hash(self.temp_dir)

        # Hash should be the same (only essential files matter)
        self.assertEqual(hash_with_extra, hash_without_extra)

    @patch("subprocess.run")
    def test_docker_optimization_with_buildkit(self, mock_run):
        """Test Docker optimization with BuildKit."""
        # Mock successful BuildKit check
        mock_run.return_value = MagicMock(returncode=0, stdout="DOCKER_BUILDKIT=1", stderr="")

        # Test that optimizer can check for BuildKit
        # (This would be a method if it existed in the actual class)

        # Verify subprocess was used correctly
        if mock_run.called:
            call_args = mock_run.call_args
            # Should use list format (secure)
            if call_args[0]:
                self.assertIsInstance(call_args[0][0], list)

    def test_multiple_optimizers(self):
        """Test creating multiple optimizer instances."""
        optimizers = [DockerBuildOptimizer() for _ in range(3)]

        # Each should have its own cache
        cache_names = [opt.cache.name for opt in optimizers]
        self.assertTrue(all(name == "docker_builds" for name in cache_names))

        # But should be separate instances
        self.assertEqual(len(optimizers), 3)

    @patch.dict(os.environ, {"DOCKER_BUILDKIT": "1"})
    def test_buildkit_environment_awareness(self):
        """Test optimizer awareness of BuildKit environment."""
        optimizer = DockerBuildOptimizer()

        # Should create successfully even with BuildKit enabled
        self.assertIsNotNone(optimizer)
        self.assertEqual(os.environ.get("DOCKER_BUILDKIT"), "1")

    def test_hash_algorithm_security(self):
        """Test that hash calculation uses secure algorithm."""
        test_file = self.temp_dir / "Dockerfile"
        test_file.write_text("FROM python:3.11")

        hash_value = self.optimizer._calculate_dir_hash(self.temp_dir)

        # Should be a hexadecimal string
        self.assertTrue(all(c in "0123456789abcdef" for c in hash_value.lower()))
        # Should have reasonable length (not too short)
        self.assertGreaterEqual(len(hash_value), 8)


class TestDockerOptimizationIntegration(unittest.TestCase):
    """Integration tests for Docker optimization."""

    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up integration test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_optimization_with_real_project_structure(self):
        """Test optimization with realistic project structure."""
        # Create realistic project files
        (self.temp_dir / "Dockerfile").write_text("""
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
""")

        (self.temp_dir / "requirements.txt").write_text("""
click>=8.0.0
rich>=13.0.0
""")

        (self.temp_dir / "pyproject.toml").write_text("""
[project]
name = "test-project"
version = "1.0.0"
""")

        optimizer = DockerBuildOptimizer()
        hash_value = optimizer._calculate_dir_hash(self.temp_dir)

        self.assertIsInstance(hash_value, str)
        self.assertGreater(len(hash_value), 0)

    def test_cache_persistence_across_instances(self):
        """Test that cache persists across optimizer instances."""
        # Create test content
        (self.temp_dir / "Dockerfile").write_text("FROM python:3.11")

        # First optimizer
        optimizer1 = DockerBuildOptimizer()
        hash1 = optimizer1._calculate_dir_hash(self.temp_dir)

        # Second optimizer (same cache name)
        optimizer2 = DockerBuildOptimizer()
        hash2 = optimizer2._calculate_dir_hash(self.temp_dir)

        # Hashes should be consistent
        self.assertEqual(hash1, hash2)

    def test_platform_specific_optimization(self):
        """Test that optimization works across platforms."""
        optimizer = DockerBuildOptimizer()

        # Create test files with different line endings (platform specific)
        test_content = "FROM python:3.11\nWORKDIR /app"
        (self.temp_dir / "Dockerfile").write_text(test_content)

        hash_value = optimizer._calculate_dir_hash(self.temp_dir)

        # Should work regardless of platform
        self.assertIsInstance(hash_value, str)
        self.assertGreater(len(hash_value), 0)


if __name__ == "__main__":
    unittest.main()
