"""Test fixture optimizations and performance improvements."""

import os
import shutil
import tempfile
import time
from pathlib import Path

import pytest

# Mark all tests in this file as CI excluded due to performance sensitivity
pytestmark = [pytest.mark.performance, pytest.mark.ci_exclude]


class OptimizedManuscriptFixtures:
    """Optimized fixtures for manuscript testing."""

    @staticmethod
    def copy_tree_optimized(src: Path, dst: Path, use_hardlinks: bool = True):
        """Optimized tree copying using hardlinks where possible."""
        dst.mkdir(parents=True, exist_ok=True)

        for item in src.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(src)
                dst_item = dst / rel_path
                dst_item.parent.mkdir(parents=True, exist_ok=True)

                # Use hardlinks for static files, copy for modifiable files
                if use_hardlinks and item.suffix in {".png", ".jpg", ".pdf", ".svg"}:
                    try:
                        os.link(item, dst_item)
                        continue
                    except (OSError, AttributeError):
                        pass

                # Fallback to copy
                shutil.copy2(item, dst_item)

    @staticmethod
    def create_minimal_manuscript(base_dir: Path, name: str = "test_manuscript"):
        """Create a minimal manuscript with optimized file operations."""
        manuscript_dir = base_dir / name
        manuscript_dir.mkdir(exist_ok=True)

        # Create FIGURES directory
        figures_dir = manuscript_dir / "FIGURES"
        figures_dir.mkdir(exist_ok=True)

        # Write files efficiently
        files_to_create = {
            "00_CONFIG.yml": """title: "Test Manuscript"
authors:
  - name: "Test Author"
    affiliation: "Test University"
    email: "test@example.com"
abstract: "Test abstract for performance testing."
keywords: ["test", "performance"]
""",
            "01_MAIN.md": """# Test Manuscript

## Introduction

This is a test manuscript for performance benchmarking.

## Methods

Standard testing methodology.

## Results

All tests completed successfully.

## Conclusion

Performance optimization is effective.
""",
            "03_REFERENCES.bib": """@article{test2023,
    title = {Test Article for Performance},
    author = {Test Author},
    journal = {Test Journal},
    year = {2023},
    volume = {1},
    pages = {1--10}
}
""",
        }

        for filename, content in files_to_create.items():
            (manuscript_dir / filename).write_text(content)

        return manuscript_dir


@pytest.mark.performance
class TestFixtureOptimizations:
    """Test performance improvements in fixtures."""

    def test_optimized_manuscript_creation(self, benchmark):
        """Benchmark optimized manuscript creation."""
        optimizer = OptimizedManuscriptFixtures()

        def create_optimized_manuscript():
            with tempfile.TemporaryDirectory() as tmpdir:
                base_dir = Path(tmpdir)
                manuscript = optimizer.create_minimal_manuscript(base_dir)
                return manuscript.exists()

        result = benchmark(create_optimized_manuscript)
        assert result is True

    def test_hardlink_optimization(self, benchmark):
        """Benchmark hardlink vs copy optimization."""

        def test_hardlink_performance():
            with tempfile.TemporaryDirectory() as tmpdir:
                source_dir = Path(tmpdir) / "source"
                source_dir.mkdir()

                # Create test files (simulate images)
                for i in range(10):
                    (source_dir / f"image_{i}.png").write_bytes(b"fake_png_data" * 100)

                dest_dir = Path(tmpdir) / "dest"

                optimizer = OptimizedManuscriptFixtures()
                optimizer.copy_tree_optimized(source_dir, dest_dir, use_hardlinks=True)

                return dest_dir.exists() and len(list(dest_dir.glob("*.png"))) == 10

        result = benchmark(test_hardlink_performance)
        assert result is True

    def test_bulk_file_operations(self, benchmark):
        """Benchmark bulk file operations."""

        def bulk_operations():
            with tempfile.TemporaryDirectory() as tmpdir:
                base_dir = Path(tmpdir)

                # Create multiple manuscripts efficiently
                manuscripts = []
                for i in range(5):
                    manuscript = OptimizedManuscriptFixtures.create_minimal_manuscript(
                        base_dir, f"manuscript_{i}"
                    )
                    manuscripts.append(manuscript)

                return all(m.exists() for m in manuscripts)

        result = benchmark(bulk_operations)
        assert result is True


@pytest.mark.performance
class TestCachingStrategies:
    """Test caching strategies for performance improvement."""

    @pytest.fixture(scope="class")
    def cached_manuscript_template(self):
        """Class-scoped cached manuscript template."""
        return {
            "config_content": """title: "Cached Test Manuscript"
authors:
  - name: "Cached Author"
    affiliation: "Cache University"
    email: "cache@test.com"
abstract: "Cached abstract for performance testing."
keywords: ["cache", "performance", "test"]
""",
            "main_content": """# Cached Test Manuscript

## Introduction

This manuscript uses cached template data.

## Methods

Caching methodology for improved performance.

## Results

Cached results show improved performance.

## Conclusion

Caching is effective for test performance.
""",
            "bib_content": """@article{cached2023,
    title = {Cached Article for Performance},
    author = {Cached Author},
    journal = {Cache Journal},
    year = {2023},
    volume = {1},
    pages = {1--10}
}
""",
        }

    def test_cached_template_performance(self, benchmark, cached_manuscript_template):
        """Benchmark using cached templates."""

        def use_cached_template():
            with tempfile.TemporaryDirectory() as tmpdir:
                manuscript_dir = Path(tmpdir) / "cached_manuscript"
                manuscript_dir.mkdir()

                figures_dir = manuscript_dir / "FIGURES"
                figures_dir.mkdir()

                # Use cached template data
                (manuscript_dir / "00_CONFIG.yml").write_text(
                    cached_manuscript_template["config_content"]
                )
                (manuscript_dir / "01_MAIN.md").write_text(
                    cached_manuscript_template["main_content"]
                )
                (manuscript_dir / "03_REFERENCES.bib").write_text(
                    cached_manuscript_template["bib_content"]
                )

                return manuscript_dir.exists()

        result = benchmark(use_cached_template)
        assert result is True

    def test_session_vs_class_vs_function_scoped(self, benchmark):
        """Compare different fixture scopes performance impact."""

        # Simulate the overhead of different scoping strategies
        def scope_simulation():
            # Function-scoped (highest overhead)
            function_time = 0
            for _ in range(3):
                start = time.perf_counter()
                with tempfile.TemporaryDirectory() as tmpdir:
                    Path(tmpdir, "test.txt").write_text("test")
                function_time += time.perf_counter() - start

            # Class-scoped simulation (medium overhead)
            start = time.perf_counter()
            with tempfile.TemporaryDirectory() as tmpdir:
                for j in range(3):
                    Path(tmpdir, f"test_{j}.txt").write_text("test")
            class_time = time.perf_counter() - start

            # Session-scoped simulation (lowest overhead)
            start = time.perf_counter()
            with tempfile.TemporaryDirectory() as tmpdir:
                files = [Path(tmpdir, f"test_{i}.txt") for i in range(3)]
                for file_path in files:
                    file_path.write_text("test")
            session_time = time.perf_counter() - start

            return {
                "function": function_time,
                "class": class_time,
                "session": session_time,
            }

        result = benchmark(scope_simulation)
        assert isinstance(result, dict)
        assert all(isinstance(v, float) for v in result.values())


@pytest.mark.performance
class TestContainerOptimizations:
    """Test container-related performance optimizations."""

    def test_container_reuse_simulation(self, benchmark):
        """Simulate container reuse vs recreation performance."""

        def container_lifecycle_simulation():
            # Simulate container startup/shutdown overhead
            startup_times = []

            # Scenario 1: Container per test (high overhead)
            for _i in range(3):
                start = time.perf_counter()
                # Simulate container startup
                time.sleep(0.05)  # 50ms startup time
                # Simulate test work
                time.sleep(0.01)  # 10ms test work
                # Simulate container shutdown
                time.sleep(0.02)  # 20ms shutdown time
                startup_times.append(time.perf_counter() - start)

            # Scenario 2: Reused container (low overhead)
            start = time.perf_counter()
            # Simulate single container startup
            time.sleep(0.05)  # 50ms startup time
            for _i in range(3):
                # Simulate test work only
                time.sleep(0.01)  # 10ms test work per test
            # Simulate single container shutdown
            time.sleep(0.02)  # 20ms shutdown time
            reuse_time = time.perf_counter() - start

            return {
                "per_test_total": sum(startup_times),
                "reused_total": reuse_time,
                "improvement_ratio": sum(startup_times) / reuse_time,
            }

        result = benchmark(container_lifecycle_simulation)
        assert result["improvement_ratio"] > 1.0  # Reuse should be faster

    def test_workspace_mounting_optimization(self, benchmark):
        """Test workspace mounting strategy performance."""

        def workspace_setup():
            with tempfile.TemporaryDirectory() as tmpdir:
                workspace_dir = Path(tmpdir) / "workspace"
                workspace_dir.mkdir()

                # Simulate mounting workspace with many files
                for i in range(20):
                    file_path = workspace_dir / f"file_{i}.txt"
                    file_path.write_text(f"content {i}")

                # Simulate checking mounted files
                mounted_files = list(workspace_dir.glob("*.txt"))

                return len(mounted_files) == 20

        result = benchmark(workspace_setup)
        assert result is True


# Performance test configuration
pytest_benchmark_config = {
    "min_rounds": 3,
    "max_time": 5.0,
    "warmup": True,
    "warmup_iterations": 1,
    "timer": time.perf_counter,
    "group_by": "group",
}


@pytest.fixture(scope="session")
def performance_baseline():
    """Session-scoped performance baseline for regression testing."""
    return {
        "manuscript_creation_max_time": 0.1,  # 100ms max
        "file_copy_max_time": 0.05,  # 50ms max for small files
        "fixture_setup_max_time": 0.02,  # 20ms max
    }
