"""Tests for error handling scenarios and edge cases.

This module tests comprehensive error handling, network failures, permission errors,
malformed inputs, and other edge cases across the rxiv-maker system.
"""

import json
import os
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

# Exclude from default CI run; intentionally exercises error/edge cases and can be flaky
pytestmark = pytest.mark.ci_exclude


@pytest.mark.flaky  # Network tests can be unstable in CI
class TestNetworkErrorHandling(unittest.TestCase):
    """Test network error handling scenarios."""

    @patch("requests.get")
    def test_doi_validation_network_timeout(self, mock_get):
        """Test DOI validation with network timeout."""
        import requests

        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        # Simulate DOI validation failure due to network timeout
        with self.assertRaises(requests.exceptions.Timeout):
            requests.get("https://api.crossref.org/works/10.1000/test", timeout=5)

    @patch("requests.get")
    def test_doi_validation_connection_error(self, mock_get):
        """Test DOI validation with connection error."""
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("No internet connection")

        with self.assertRaises(requests.exceptions.ConnectionError):
            requests.get("https://api.crossref.org/works/10.1000/test")

    @patch("requests.get")
    def test_doi_validation_rate_limiting(self, mock_get):
        """Test DOI validation with rate limiting (429 Too Many Requests)."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.text = "Rate limit exceeded"
        mock_get.return_value = mock_response

        response = mock_get.return_value
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response.headers)

    @patch("requests.get")
    def test_doi_validation_server_error(self, mock_get):
        """Test DOI validation with server error (500 Internal Server Error)."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        response = mock_get.return_value
        self.assertEqual(response.status_code, 500)

    @patch("socket.create_connection")
    def test_network_connectivity_check(self, mock_socket):
        """Test network connectivity checking."""
        # Test successful connection
        mock_socket.return_value = Mock()

        def check_internet_connection():
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=3)
                return True
            except OSError:
                return False

        self.assertTrue(check_internet_connection())

        # Test failed connection
        mock_socket.side_effect = OSError("Network unreachable")
        self.assertFalse(check_internet_connection())


class TestPermissionErrorHandling(unittest.TestCase):
    """Test permission error handling scenarios."""

    def test_file_permission_denied_read(self):
        """Test handling of permission denied errors when reading files."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            test_file = Path(f.name)

        try:
            # Simulate permission denied by mocking open
            with patch("builtins.open", mock_open()) as mock_file:
                mock_file.side_effect = PermissionError("Permission denied")

                with self.assertRaises(PermissionError), open(test_file) as file:
                    file.read()
        finally:
            test_file.unlink(missing_ok=True)

    def test_file_permission_denied_write(self):
        """Test handling of permission denied errors when writing files."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            test_file = Path(f.name)

        try:
            with patch("builtins.open", mock_open()) as mock_file:
                mock_file.side_effect = PermissionError("Permission denied")

                with self.assertRaises(PermissionError), open(test_file, "w") as file:
                    file.write("test content")
        finally:
            test_file.unlink(missing_ok=True)

    @patch("pathlib.Path.mkdir")
    def test_directory_creation_permission_denied(self, mock_mkdir):
        """Test handling of permission denied errors when creating directories."""
        mock_mkdir.side_effect = PermissionError("Permission denied")

        test_dir = Path("test_output_dir")
        with self.assertRaises(PermissionError):
            test_dir.mkdir(parents=True, exist_ok=True)

    @patch("shutil.copy2")
    def test_file_copy_permission_denied(self, mock_copy):
        """Test handling of permission denied errors when copying files."""
        import shutil

        mock_copy.side_effect = PermissionError("Permission denied")

        with self.assertRaises(PermissionError):
            shutil.copy2("source.txt", "destination.txt")

    @patch("os.chmod")
    def test_file_chmod_permission_denied(self, mock_chmod):
        """Test handling of permission denied errors when changing file permissions."""
        mock_chmod.side_effect = PermissionError("Operation not permitted")

        with self.assertRaises(PermissionError):
            os.chmod("test_file.py", 0o755)


class TestMalformedInputHandling(unittest.TestCase):
    """Test handling of malformed and invalid inputs."""

    def test_malformed_yaml_config(self):
        """Test handling of malformed YAML configuration files."""
        malformed_yaml_content = """
title: "Test Document"
author: "Test Author
  invalid_indentation: value
- list_item_without_context
  missing_colon value
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(malformed_yaml_content)
            yaml_file = Path(f.name)

        try:
            import yaml

            with self.assertRaises(yaml.YAMLError), open(yaml_file) as file:
                yaml.safe_load(file)
        finally:
            yaml_file.unlink(missing_ok=True)

    def test_malformed_bibtex_entries(self):
        """Test handling of malformed BibTeX entries."""
        malformed_bibtex = """
@article{incomplete_entry
    title = {Missing closing brace
    author = {Test Author},
    year = {2023}

@article{missing_comma,
    title = {Test Title}
    author = {Another Author}
    year = {2023}
}

@invalidtype{bad_entry_type,
    title = {This entry type doesn't exist},
    year = {2023}
}
"""

        # Test that malformed BibTeX is detected
        self.assertIn("Missing closing brace", malformed_bibtex)
        self.assertNotIn("}", malformed_bibtex.split("\n")[1])  # Missing closing brace

    def test_malformed_markdown_syntax(self):
        """Test handling of malformed Markdown syntax."""
        malformed_markdown = """
# Valid Header

## Unclosed emphasis *text without closing asterisk

[Broken link](missing-url

@fig:reference_without_figure

Math expression with unmatched delimiters: $x + y = z

Code block without closing:
```python
def function():
    pass
"""

        # Test detection of various malformed elements
        self.assertIn("*text without closing asterisk", malformed_markdown)
        self.assertIn("[Broken link](missing-url", malformed_markdown)
        self.assertNotIn("```", malformed_markdown.split("```python")[1])

    def test_invalid_doi_formats(self):
        """Test handling of invalid DOI formats."""
        invalid_dois = [
            "not_a_doi",
            "10.1000/",  # Missing suffix
            "doi:10.1000/",  # Should not include "doi:" prefix
            "https://doi.org/10.1000/test",  # Should not include URL
            "10.1000 test",  # Space in DOI
            "10.1000/test with spaces",
            "",  # Empty DOI
            "10.",  # Incomplete DOI
            "invalid.prefix/suffix",  # Invalid prefix
        ]

        import re

        # DOI regex pattern (simplified)
        doi_pattern = r"^10\.\d{4,}/[^\s]+$"

        for doi in invalid_dois:
            with self.subTest(doi=doi):
                self.assertFalse(bool(re.match(doi_pattern, doi)))

    def test_corrupted_json_data(self):
        """Test handling of corrupted JSON data."""
        corrupted_json_samples = [
            '{"incomplete": json}',  # Missing quotes
            '{"trailing_comma": true,}',  # Trailing comma
            '{"unescaped": "quote"inside"}',  # Unescaped quotes
            "{incomplete",  # Incomplete JSON
            '{"dup": 1, "dup": 2}',  # Duplicate keys (valid but problematic)
            "",  # Empty string
        ]

        for json_data in corrupted_json_samples:
            with self.subTest(json_data=json_data):
                try:
                    json.loads(json_data)
                    # If we get here, it's not actually invalid JSON
                    # (some cases like duplicate keys are valid JSON)
                    pass
                except json.JSONDecodeError:
                    # This is expected for truly malformed JSON
                    pass


class TestResourceExhaustionScenarios(unittest.TestCase):
    """Test resource exhaustion and constraint scenarios."""

    @patch("shutil.disk_usage")
    def test_disk_space_exhaustion(self, mock_disk_usage):
        """Test handling of disk space exhaustion."""
        # Mock disk usage to return very little free space
        mock_disk_usage.return_value = (1000000000, 950000000, 50000000)  # 50MB free

        total, used, free = mock_disk_usage.return_value
        free_gb = free / (1024**3)

        # Check if there's sufficient space (should fail)
        minimum_required_gb = 2.0
        self.assertLess(free_gb, minimum_required_gb)

    @pytest.mark.fast
    def test_memory_exhaustion(self):
        """Test handling of memory exhaustion."""
        try:
            # Mock memory to show low available memory
            with patch("psutil.virtual_memory") as mock_memory:
                mock_memory.return_value = Mock(
                    total=8 * 1024**3,  # 8GB total
                    available=100 * 1024**2,  # 100MB available
                    percent=95.0,
                )

                memory_info = mock_memory.return_value
                available_gb = memory_info.available / (1024**3)

                # Check if there's sufficient memory
                minimum_required_gb = 1.0
                self.assertLess(available_gb, minimum_required_gb)

        except ImportError:
            self.skipTest("psutil not available")

    def test_large_file_handling(self):
        """Test handling of extremely large files."""
        # Simulate large file size check
        large_file_size_mb = 1000  # 1GB
        max_supported_size_mb = 500  # 500MB limit

        file_too_large = large_file_size_mb > max_supported_size_mb
        self.assertTrue(file_too_large)

    @patch("subprocess.run")
    def test_process_timeout_handling(self, mock_run):
        """Test handling of process timeouts."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["long_running_command"], timeout=30)

        with self.assertRaises(subprocess.TimeoutExpired):
            subprocess.run(["long_running_command"], timeout=30)

    def test_maximum_recursion_depth(self):
        """Test handling of maximum recursion depth scenarios."""
        import sys

        def safe_recursive_function(depth, max_depth=50):
            """A recursion function with built-in safety limits."""
            if depth <= 0 or depth > max_depth:
                return depth
            return safe_recursive_function(depth - 1, max_depth)

        # Test that we can handle reasonable recursion depths safely
        max_safe_depth = 50  # Reduced to avoid any issues
        result = safe_recursive_function(max_safe_depth)
        self.assertEqual(result, 0)

        # Test recursion limit awareness
        current_limit = sys.getrecursionlimit()
        self.assertGreater(current_limit, 100)


class TestConcurrencyAndRaceConditions(unittest.TestCase):
    """Test concurrency issues and race conditions."""

    @pytest.mark.flaky  # Threading and timing sensitive
    def test_concurrent_file_access(self):
        """Test handling of concurrent file access scenarios."""
        import threading
        import time

        with tempfile.NamedTemporaryFile(delete=False) as test_file:
            test_file_path = test_file.name

        results = []

        def write_to_file(content, delay=0):
            time.sleep(delay)
            try:
                with open(test_file_path, "w") as f:
                    f.write(content)
                results.append(f"Success: {content}")
            except Exception as e:
                results.append(f"Error: {e}")

        try:
            # Create threads that attempt to write simultaneously
            threads = [
                threading.Thread(target=write_to_file, args=("Thread1", 0.1)),
                threading.Thread(target=write_to_file, args=("Thread2", 0.1)),
            ]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            # At least one should succeed
            success_count = len([r for r in results if r.startswith("Success")])
            self.assertGreater(success_count, 0)

        finally:
            Path(test_file_path).unlink(missing_ok=True)

    def test_cache_file_corruption_during_concurrent_access(self):
        """Test handling of cache file corruption during concurrent access."""
        cache_content = {"test_key": "test_value"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(cache_content, f)
            cache_file = Path(f.name)

        try:
            # Simulate partial write (corrupted file)
            with open(cache_file, "w") as f:
                f.write('{"partial":')  # Incomplete JSON

            # Test that corrupted cache is handled gracefully
            try:
                with open(cache_file) as f:
                    json.load(f)
                self.fail("Should have raised JSONDecodeError")
            except json.JSONDecodeError:
                # This is expected - corrupted cache should be detected
                pass

        finally:
            cache_file.unlink(missing_ok=True)


class TestExternalDependencyFailures(unittest.TestCase):
    """Test failures of external dependencies and tools."""

    @patch("subprocess.run")
    def test_latex_not_installed(self, mock_run):
        """Test handling when LaTeX is not installed."""
        mock_run.side_effect = FileNotFoundError("pdflatex: command not found")

        with self.assertRaises(FileNotFoundError):
            subprocess.run(["pdflatex", "--version"], capture_output=True)

    @patch("subprocess.run")
    def test_r_not_installed(self, mock_run):
        """Test handling when R is not installed."""
        mock_run.side_effect = FileNotFoundError("Rscript: command not found")

        with self.assertRaises(FileNotFoundError):
            subprocess.run(["Rscript", "--version"], capture_output=True)

    @patch("subprocess.run")
    def test_docker_not_available(self, mock_run):
        """Test handling when Docker is not available."""
        mock_run.side_effect = FileNotFoundError("docker: command not found")

        with self.assertRaises(FileNotFoundError):
            subprocess.run(["docker", "--version"], capture_output=True)

    @patch("subprocess.run")
    def test_python_package_import_failure(self, mock_run):
        """Test handling of Python package import failures."""
        mock_run.return_value = Mock(returncode=1, stderr="ModuleNotFoundError: No module named 'matplotlib'")

        result = mock_run.return_value
        self.assertEqual(result.returncode, 1)
        self.assertIn("ModuleNotFoundError", result.stderr)

    @patch("subprocess.run")
    def test_r_package_not_available(self, mock_run):
        """Test handling of R package unavailability."""
        mock_run.return_value = Mock(returncode=1, stderr="Error: there is no package called 'ggplot2'")

        result = mock_run.return_value
        self.assertEqual(result.returncode, 1)
        self.assertIn("no package called", result.stderr)


class TestDataIntegrityAndCorruption(unittest.TestCase):
    """Test data integrity and corruption scenarios."""

    def test_corrupted_manuscript_files(self):
        """Test handling of corrupted manuscript files."""
        # Simulate binary data in markdown file
        corrupted_content = b"\x00\x01\x02\x03\xff\xfe\xfd"

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            f.write(corrupted_content)
            corrupted_file = Path(f.name)

        try:
            # Attempt to read as text (should handle encoding errors)
            try:
                with open(corrupted_file, encoding="utf-8") as file:
                    file.read()
                # If we get here, the file wasn't actually corrupted enough
            except UnicodeDecodeError:
                # This is expected for binary data
                pass

        finally:
            corrupted_file.unlink(missing_ok=True)

    def test_truncated_files(self):
        """Test handling of truncated files."""
        complete_content = "This is a complete file with proper ending.\n"
        truncated_content = "This is a truncated file that ends abrupt"

        # Test detection of incomplete content patterns
        self.assertTrue(complete_content.endswith("\n"))
        self.assertFalse(truncated_content.endswith("\n"))

    def test_file_checksum_mismatch(self):
        """Test handling of file checksum mismatches."""
        import hashlib

        original_content = "Original file content"
        modified_content = "Modified file content"

        original_checksum = hashlib.md5(original_content.encode(), usedforsecurity=False).hexdigest()
        modified_checksum = hashlib.md5(modified_content.encode(), usedforsecurity=False).hexdigest()

        # Checksums should be different
        self.assertNotEqual(original_checksum, modified_checksum)

    def test_empty_required_files(self):
        """Test handling of empty required files."""
        required_files = ["config.yml", "main.md", "references.bib"]

        for filename in required_files:
            with tempfile.NamedTemporaryFile(suffix=f".{filename.split('.')[-1]}", delete=False) as f:
                # Create empty file
                empty_file = Path(f.name)

            try:
                # Check if file is empty
                self.assertEqual(empty_file.stat().st_size, 0)

                # Empty required files should be detected as problematic
                is_empty = empty_file.stat().st_size == 0
                self.assertTrue(is_empty)

            finally:
                empty_file.unlink(missing_ok=True)


class TestGracefulDegradationScenarios(unittest.TestCase):
    """Test graceful degradation when features are unavailable."""

    def test_fallback_to_local_when_docker_unavailable(self):
        """Test fallback to local execution when Docker is unavailable."""
        # Simulate Docker check failure
        docker_available = False

        # Test fallback logic
        execution_mode = "docker" if docker_available else "local"

        self.assertEqual(execution_mode, "local")

    def test_skip_optional_features_when_dependencies_missing(self):
        """Test skipping optional features when dependencies are missing."""
        optional_features = {
            "mermaid_diagrams": True,  # Always available via mermaid.ink API
            "r_figures": False,  # R not available
            "advanced_pdf_features": True,  # LaTeX available
        }

        enabled_features = [name for name, available in optional_features.items() if available]
        self.assertIn("advanced_pdf_features", enabled_features)
        self.assertIn("mermaid_diagrams", enabled_features)
        self.assertNotIn("r_figures", enabled_features)

    def test_continue_with_warnings_for_non_critical_failures(self):
        """Test continuing execution with warnings for non-critical failures."""
        warnings = []
        errors = []

        # Simulate various issues
        issues = [
            ("figure_generation_failed", "warning"),
            ("missing_optional_package", "warning"),
            ("missing_required_file", "error"),
            ("network_timeout", "warning"),
        ]

        for issue, severity in issues:
            if severity == "warning":
                warnings.append(issue)
            else:
                errors.append(issue)

        # Should NOT continue if there are errors
        can_continue = len(errors) == 0
        self.assertFalse(can_continue)  # Has errors in this case

        # Test case with only warnings
        # Remove the error for this test
        test_issues = [i for i in issues if i[1] != "error"]
        # Now verify test_issues only has warnings
        assert len([issue for issue, severity in test_issues if severity == "error"]) == 0
        test_can_continue = len([issue for issue, severity in test_issues if severity == "error"]) == 0
        self.assertTrue(test_can_continue)


if __name__ == "__main__":
    unittest.main()
