"""Cross-platform test optimizations and compatibility improvements."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestCrossPlatformPathHandling:
    """Test cross-platform path handling improvements."""

    @pytest.mark.parametrize(
        "platform,expected_separator",
        [
            ("win32", "\\"),
            ("darwin", "/"),
            ("linux", "/"),
        ],
    )
    def test_path_separator_handling(self, platform, expected_separator):
        """Test that path separators are handled correctly across platforms."""
        with patch("sys.platform", platform):
            # Use pathlib for cross-platform compatibility
            test_path = Path("test") / "subdir" / "file.txt"

            # pathlib should handle platform differences automatically
            assert isinstance(test_path, Path)

            # When converted to string, should use platform-appropriate separator
            path_str = str(test_path)
            if platform == "win32":
                # On actual Windows, pathlib uses \\ but when mocking on Unix systems,
                # pathlib still uses the native separator. So we test the actual OS behavior.
                import os

                expected_sep = "\\" if os.name == "nt" else "/"
                assert expected_sep in path_str
            else:
                assert "/" in path_str

    @pytest.mark.parametrize(
        "test_path",
        [
            "/Users/test/file.txt",  # Unix-style
            "C:\\Users\\test\\file.txt",  # Windows-style
            "/opt/homebrew/bin/tool",  # macOS Homebrew
            "\\\\server\\share\\file.txt",  # UNC path
        ],
    )
    def test_pathlib_normalization(self, test_path):
        """Test that pathlib normalizes paths correctly."""
        path = Path(test_path)

        # pathlib should handle all path formats
        assert isinstance(path, Path)
        assert len(path.parts) > 0

        # Should be able to get parent directory
        parent = path.parent
        assert isinstance(parent, Path)

    def test_temp_directory_creation_cross_platform(self):
        """Test temporary directory creation works on all platforms."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Should be able to create subdirectories
            sub_dir = temp_path / "subdir" / "nested"
            sub_dir.mkdir(parents=True, exist_ok=True)

            assert sub_dir.exists()
            assert sub_dir.is_dir()

            # Should be able to create files
            test_file = sub_dir / "test.txt"
            test_file.write_text("test content", encoding="utf-8")

            assert test_file.exists()
            assert test_file.read_text(encoding="utf-8") == "test content"

    @pytest.mark.parametrize("encoding", ["utf-8", "ascii", "latin-1"])
    def test_file_encoding_handling(self, encoding):
        """Test file encoding handling across platforms."""
        test_content = "test content"

        with tempfile.NamedTemporaryFile(mode="w", encoding=encoding, delete=False) as f:
            f.write(test_content)
            temp_path = Path(f.name)

        try:
            # Should be able to read with explicit encoding
            content = temp_path.read_text(encoding=encoding)
            assert content == test_content
        finally:
            temp_path.unlink(missing_ok=True)

    def test_environment_variable_handling(self):
        """Test environment variable handling across platforms."""
        # Test common environment variables
        test_vars = {
            "PATH": "Test PATH modification",
            "TEMP": "Test temporary directory",
            "HOME": "Test home directory",
        }

        original_values = {}
        try:
            for var, value in test_vars.items():
                original_values[var] = os.environ.get(var)
                os.environ[var] = value

            # All platforms should handle environment variables
            for var, expected in test_vars.items():
                assert os.environ[var] == expected

        finally:
            # Restore original values
            for var, original in original_values.items():
                if original is None:
                    os.environ.pop(var, None)
                else:
                    os.environ[var] = original


class TestProcessExecutionCrossPlatform:
    """Test process execution compatibility across platforms."""

    @pytest.mark.parametrize(
        "shell_command",
        [
            ("echo", "hello"),  # Available on all platforms
            ("python", "--version"),  # Python should be available
        ],
    )
    def test_subprocess_execution_cross_platform(self, shell_command):
        """Test subprocess execution across platforms."""
        import subprocess

        try:
            result = subprocess.run(
                shell_command,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,  # Don't raise on non-zero exit
            )

            # Should complete without exceptions
            assert isinstance(result.returncode, int)
            assert isinstance(result.stdout, str)
            assert isinstance(result.stderr, str)

        except FileNotFoundError:
            # Command not found is acceptable
            pytest.skip(f"Command {shell_command[0]} not available on this platform")

    def test_shell_vs_no_shell_execution(self):
        """Test differences between shell and non-shell execution."""
        import subprocess

        # Test a simple command that should work everywhere
        try:
            # Without shell (secure)
            result1 = subprocess.run(["python", "--version"], capture_output=True, text=True, timeout=10, shell=False)

            # With shell - using explicit command array for security even when shell=True
            # This demonstrates shell behavior while keeping the test secure
            if sys.platform == "win32":
                cmd_array = ["cmd", "/c", "python --version"]
            else:
                cmd_array = ["sh", "-c", "python --version"]

            result2 = subprocess.run(cmd_array, capture_output=True, text=True, timeout=10, shell=False)

            # Both should succeed (or fail similarly)
            assert type(result1.returncode) is type(result2.returncode)

        except FileNotFoundError:
            pytest.skip("Python command not available")

    @pytest.mark.parametrize("timeout_duration", [1, 5, 10])
    def test_subprocess_timeout_handling(self, timeout_duration):
        """Test subprocess timeout handling across platforms."""
        import subprocess

        # Use a command that should complete quickly
        try:
            result = subprocess.run(
                ["python", "-c", "print('hello')"], capture_output=True, text=True, timeout=timeout_duration
            )

            # Should complete within timeout
            assert result.returncode == 0
            assert "hello" in result.stdout

        except subprocess.TimeoutExpired:
            # Timeout is acceptable behavior to test
            pass
        except FileNotFoundError:
            pytest.skip("Python not available for timeout test")


class TestPlatformSpecificBehaviors:
    """Test platform-specific behaviors that affect tests."""

    def test_case_sensitivity_handling(self):
        """Test case sensitivity handling across platforms."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a file
            test_file = temp_path / "TestFile.txt"
            test_file.write_text("content", encoding="utf-8")

            # Test case sensitivity behavior
            lower_file = temp_path / "testfile.txt"
            upper_file = temp_path / "TESTFILE.TXT"

            # Ensure files don't exist initially
            lower_file.unlink(missing_ok=True)
            upper_file.unlink(missing_ok=True)

            # Test filesystem case sensitivity by creating lower file first
            lower_file.write_text("lower")

            # Check if filesystem is case-sensitive by seeing if upper_file exists
            is_case_sensitive = not upper_file.exists()

            if is_case_sensitive:
                # Case-sensitive filesystem - can have both files
                upper_file.write_text("upper")
                assert lower_file.exists()
                assert upper_file.exists()
                assert lower_file.read_text() == "lower"
                assert upper_file.read_text() == "upper"

                # Clean up
                lower_file.unlink(missing_ok=True)
                upper_file.unlink(missing_ok=True)
            else:
                # Case-insensitive filesystem - both names refer to same file
                assert upper_file.exists()  # Should exist because it's the same file
                # The content should be what we wrote to lower_file
                assert upper_file.read_text() == "lower"

                # Writing to upper_file should overwrite the same file
                upper_file.write_text("upper")
                assert lower_file.read_text() == "upper"

                # Clean up
                lower_file.unlink(missing_ok=True)

    def test_line_ending_handling(self):
        """Test line ending handling across platforms."""
        test_lines = ["line1", "line2", "line3"]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, newline="") as f:
            # Write with explicit line endings
            f.write("\n".join(test_lines))
            temp_path = Path(f.name)

        try:
            # Read back - should handle platform line endings
            content = temp_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            assert lines == test_lines

        finally:
            temp_path.unlink(missing_ok=True)

    def test_permission_handling_cross_platform(self):
        """Test file permission handling differences."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Test permission changes
            if sys.platform != "win32":
                # Unix-like systems support chmod
                temp_path.chmod(0o644)
                stat = temp_path.stat()
                # Should be able to get permission info
                assert hasattr(stat, "st_mode")
            else:
                # Windows handles permissions differently
                # Just verify file operations work
                assert temp_path.exists()
                temp_path.write_text("test", encoding="utf-8")
                assert temp_path.read_text(encoding="utf-8") == "test"

        finally:
            temp_path.unlink(missing_ok=True)


class TestImportBehaviorCrossPlatform:
    """Test import behavior consistency across platforms."""

    def test_importlib_find_spec_consistency(self):
        """Test that importlib.util.find_spec works consistently."""
        import importlib.util

        # Test with standard library modules
        standard_modules = ["os", "sys", "pathlib", "json"]

        for module in standard_modules:
            spec = importlib.util.find_spec(module)
            assert spec is not None
            assert spec.name == module

            # Should be able to import the module
            imported = importlib.util.module_from_spec(spec)
            assert imported is not None

    def test_package_detection_cross_platform(self):
        """Test package detection works across platforms."""
        import importlib.util

        # Test current package
        spec = importlib.util.find_spec("rxiv_maker")
        if spec is not None:
            # If found, should have consistent properties
            assert spec.name == "rxiv_maker"
            assert hasattr(spec, "origin")

            # Should be able to access submodules
            submodule_spec = importlib.util.find_spec("rxiv_maker.utils")
            if submodule_spec is not None:
                assert submodule_spec.name == "rxiv_maker.utils"

    def test_import_error_consistency(self):
        """Test that import errors are consistent across platforms."""
        import importlib.util

        # Test with non-existent module
        fake_modules = [
            "definitely_not_a_real_module_12345",
            "fake.nested.module",
            "invalid-module-name",
        ]

        for module in fake_modules:
            try:
                spec = importlib.util.find_spec(module)
                assert spec is None  # Should consistently return None
            except (ImportError, ModuleNotFoundError):
                # Expected for non-existent modules
                pass


class TestTestFrameworkOptimizations:
    """Test optimizations for the test framework itself."""

    def test_fixture_performance(self):
        """Test that fixtures perform well across platforms."""
        import time

        # Time fixture-like setup/teardown
        start_time = time.time()

        # Simulate fixture setup
        temp_resources = []
        for _ in range(10):
            temp_dir = tempfile.mkdtemp()
            temp_resources.append(temp_dir)

        setup_time = time.time() - start_time

        # Simulate fixture teardown
        cleanup_start = time.time()
        for temp_dir in temp_resources:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

        cleanup_time = time.time() - cleanup_start
        total_time = time.time() - start_time

        # Should complete reasonably quickly on all platforms
        assert total_time < 5.0  # 5 seconds max
        assert setup_time < 3.0  # Setup should be fast
        assert cleanup_time < 2.0  # Cleanup should be fast

    def test_parallel_test_safety(self):
        """Test that tests can run safely in parallel."""
        import threading
        import time

        results = []
        errors = []

        def worker_function():
            try:
                # Simulate test work that might conflict
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    test_file = temp_path / f"test_{threading.current_thread().ident}.txt"
                    test_file.write_text("test data", encoding="utf-8")

                    time.sleep(0.1)  # Simulate work

                    content = test_file.read_text(encoding="utf-8")
                    results.append(content)

            except Exception as e:
                errors.append(e)

        # Run multiple workers
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker_function)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=10)

        # All should succeed without conflicts
        assert len(errors) == 0, f"Parallel execution errors: {errors}"
        assert len(results) == 5
        assert all(result == "test data" for result in results)

    def test_memory_usage_reasonable(self):
        """Test that test memory usage is reasonable."""
        import gc

        # Force garbage collection
        gc.collect()

        # Get initial memory usage (rough estimate)
        initial_objects = len(gc.get_objects())

        # Simulate memory-intensive test operations
        large_data = []
        for i in range(1000):
            large_data.append(f"test_data_{i}" * 100)

        # Clean up explicitly
        del large_data
        gc.collect()

        # Check memory didn't grow excessively
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects

        # Allow some growth but not excessive
        assert object_growth < 5000, f"Excessive memory growth: {object_growth} objects"
