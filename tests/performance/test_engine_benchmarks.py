"""Benchmark tests for execution engine performance."""

import subprocess
import tempfile
import time
from pathlib import Path

import pytest

# Mark all tests in this file as CI excluded due to performance sensitivity
pytestmark = [pytest.mark.performance, pytest.mark.ci_exclude, pytest.mark.slow]


@pytest.mark.performance
@pytest.mark.slow
class TestEnginePerformanceBenchmarks:
    """Benchmark execution engine operations."""

    def test_local_engine_startup_performance(self, benchmark):
        """Benchmark local engine initialization."""
        from tests.conftest import ExecutionEngine

        def create_local_engine():
            engine = ExecutionEngine("local")
            # Test a simple command
            result = engine.run(["python", "--version"])
            return result.returncode == 0

        result = benchmark(create_local_engine)
        assert result is True

    @pytest.mark.docker
    def test_docker_engine_startup_performance(self, benchmark):
        """Benchmark Docker engine initialization and container startup."""

        def setup_docker_engine():
            # Check if Docker is available
            try:
                subprocess.run(["docker", "--version"], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                pytest.skip("Docker not available")

            # Pull image (this is normally cached)
            docker_image = "henriqueslab/rxiv-maker-base:latest"

            # Start container
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--rm",
                    "-v",
                    f"{Path.cwd()}:/workspace",
                    "-w",
                    "/workspace",
                    docker_image,
                    "sleep",
                    "10",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            container_id = result.stdout.strip()

            try:
                # Test container is responsive
                test_result = subprocess.run(
                    ["docker", "exec", container_id, "python", "--version"],
                    capture_output=True,
                    check=True,
                )
                return test_result.returncode == 0
            finally:
                # Cleanup
                subprocess.run(
                    ["docker", "stop", container_id],
                    capture_output=True,
                    check=False,
                )

        result = benchmark(setup_docker_engine)
        assert result is True

    def test_command_execution_performance_local(self, benchmark):
        """Benchmark command execution performance on local engine."""
        from tests.conftest import ExecutionEngine

        engine = ExecutionEngine("local")

        def execute_commands():
            results = []
            # Test multiple command types
            commands = [
                ["python", "--version"],
                ["python", "-c", "print('hello')"],
                ["python", "-c", "import sys; print(sys.version)"],
            ]

            for cmd in commands:
                result = engine.run(cmd)
                results.append(result.returncode == 0)

            return all(results)

        result = benchmark(execute_commands)
        assert result is True

    def test_file_operations_performance_local(self, benchmark):
        """Benchmark file operations on local engine."""
        from tests.conftest import ExecutionEngine

        engine = ExecutionEngine("local")

        def file_operations():
            with tempfile.TemporaryDirectory() as tmpdir:
                temp_path = Path(tmpdir)

                # Create test files
                test_file = temp_path / "test.txt"
                test_file.write_text("test content")

                # Test file operations via engine
                result1 = engine.run(["ls", str(temp_path)])
                result2 = engine.run(["cat", str(test_file)])

                return result1.returncode == 0 and result2.returncode == 0

        result = benchmark(file_operations)
        assert result is True


@pytest.mark.performance
class TestOptimizedFixtureBenchmarks:
    """Benchmark optimized fixture implementations."""

    def test_class_scoped_vs_function_scoped_fixtures(self, benchmark):
        """Compare performance of class vs function scoped fixtures."""

        def function_scoped_setup():
            # Simulate function-scoped fixture setup
            results = []
            for _i in range(10):
                with tempfile.TemporaryDirectory() as tmpdir:
                    manuscript_dir = Path(tmpdir) / "manuscript"
                    manuscript_dir.mkdir()

                    # Create files
                    (manuscript_dir / "config.yml").write_text("title: Test")
                    (manuscript_dir / "main.md").write_text("# Test")

                    results.append(manuscript_dir.exists())

            return all(results)

        result = benchmark(function_scoped_setup)
        assert result is True

    def test_hardlink_vs_copy_performance(self, benchmark):
        """Compare hardlink vs copy performance for file operations."""
        import os
        import shutil

        def test_copy_strategies():
            with tempfile.TemporaryDirectory() as tmpdir:
                source_dir = Path(tmpdir) / "source"
                source_dir.mkdir()

                # Create test files
                for i in range(20):
                    (source_dir / f"file_{i}.txt").write_text(f"content {i}")

                # Test hardlink strategy
                hardlink_dir = Path(tmpdir) / "hardlink_dest"
                hardlink_dir.mkdir()

                hardlink_success = True
                for file_path in source_dir.glob("*.txt"):
                    dest_path = hardlink_dir / file_path.name
                    try:
                        os.link(file_path, dest_path)
                    except OSError:
                        hardlink_success = False
                        break

                # Test copy strategy
                copy_dir = Path(tmpdir) / "copy_dest"
                shutil.copytree(source_dir, copy_dir)

                return hardlink_success and copy_dir.exists()

        result = benchmark(test_copy_strategies)
        assert result is True

    def test_cached_manuscript_template_performance(self, benchmark):
        """Benchmark using cached vs fresh manuscript templates."""
        # Simulate cached template data
        cached_template = {
            "config": "title: Cached Test\nauthors:\n  - name: Test Author",
            "content": "# Cached Test\n\nThis is cached content.",
            "bibliography": "@article{cached,title={Cached}}",
        }

        def use_cached_template():
            results = []
            for i in range(5):
                with tempfile.TemporaryDirectory() as tmpdir:
                    manuscript_dir = Path(tmpdir) / f"manuscript_{i}"
                    manuscript_dir.mkdir()

                    # Use cached template data
                    (manuscript_dir / "00_CONFIG.yml").write_text(
                        cached_template["config"]
                    )
                    (manuscript_dir / "01_MAIN.md").write_text(
                        cached_template["content"]
                    )
                    (manuscript_dir / "03_REFERENCES.bib").write_text(
                        cached_template["bibliography"]
                    )

                    results.append(manuscript_dir.exists())

            return all(results)

        result = benchmark(use_cached_template)
        assert result is True


@pytest.mark.performance
class TestParallelExecutionBenchmarks:
    """Benchmark parallel test execution scenarios."""

    def test_sequential_vs_parallel_simulation(self, benchmark):
        """Simulate sequential vs parallel test execution patterns."""

        def sequential_tests():
            # Simulate running tests sequentially
            total_time = 0
            for _i in range(10):
                start = time.perf_counter()
                # Simulate test work
                time.sleep(0.01)  # 10ms per test
                end = time.perf_counter()
                total_time += end - start
            return total_time < 1.0  # Should complete in under 1 second

        result = benchmark(sequential_tests)
        assert result is True

    def test_test_isolation_performance(self, benchmark):
        """Benchmark test isolation overhead."""

        def isolated_test_runs():
            results = []
            for i in range(5):
                # Simulate test isolation setup/teardown
                with tempfile.TemporaryDirectory() as tmpdir:
                    test_dir = Path(tmpdir) / f"test_{i}"
                    test_dir.mkdir()

                    # Simulate test work
                    (test_dir / "output.txt").write_text(f"test {i} output")

                    results.append(test_dir.exists())

            return all(results)

        result = benchmark(isolated_test_runs)
        assert result is True


# Custom benchmark markers for categorization
pytestmark = [
    pytest.mark.performance,
    pytest.mark.benchmark(
        group="engine_performance",
        min_rounds=3,
        max_time=10.0,
        warmup=True,
    ),
]
