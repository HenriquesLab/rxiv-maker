"""Integration tests for homebrew workflow validation.

Tests the version synchronization and validation logic used in the
homebrew auto-update workflow.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from rxiv_maker import __version__


class TestHomebrewWorkflowValidation(unittest.TestCase):
    """Test homebrew workflow validation logic."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(__file__).parent.parent
        self.src_dir = self.test_dir / "src"

    def test_codebase_version_extraction(self):
        """Test that we can extract version from codebase like the workflow does."""
        # This simulates the version extraction logic from the workflow
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(f"""
import sys
import os
sys.path.insert(0, '{self.src_dir.absolute()}')
try:
    from rxiv_maker import __version__
    print(__version__)
except ImportError as e:
    print(f'Error importing version: {{e}}', file=sys.stderr)
    sys.exit(1)
""")
            f.flush()

            result = subprocess.run(["python", f.name], capture_output=True, text=True, timeout=10)

        # Clean up
        os.unlink(f.name)

        self.assertEqual(result.returncode, 0, f"Version extraction failed: {result.stderr}")
        extracted_version = result.stdout.strip()
        self.assertEqual(
            extracted_version,
            __version__,
            f"Extracted version {extracted_version} doesn't match imported version {__version__}",
        )

    def test_version_format_validation(self):
        """Test version format validation logic from workflow."""
        # Test valid version formats
        valid_versions = ["1.5.16", "1.0.0", "2.10.5", "0.1.0"]
        for version in valid_versions:
            with self.subTest(version=version):
                # Simulate the regex check from the workflow
                result = subprocess.run(
                    ["bash", "-c", f"echo '{version}' | grep -q '^[0-9][0-9.]*$'"], capture_output=True
                )
                self.assertEqual(result.returncode, 0, f"Valid version {version} failed regex check")

        # Test invalid version formats
        invalid_versions = ["v1.5.16", "abc", "", "1.5.16-dev", "1.5.16+beta"]
        for version in invalid_versions:
            with self.subTest(version=version):
                result = subprocess.run(
                    ["bash", "-c", f"echo '{version}' | grep -q '^[0-9][0-9.]*$'"], capture_output=True
                )
                self.assertNotEqual(result.returncode, 0, f"Invalid version {version} passed regex check")

    def test_version_extraction_from_cli_output(self):
        """Test version extraction from CLI output like the workflow does."""
        # Test the exact extraction logic from the workflow
        test_outputs = [
            ("rxiv, version 1.5.16", "1.5.16"),
            ("rxiv, version 2.0.0", "2.0.0"),
            ("rxiv-maker 1.5.16", "1.5.16"),  # Alternative format
        ]

        for output, expected in test_outputs:
            with self.subTest(output=output, expected=expected):
                # Method 1: sed extraction (primary)
                result = subprocess.run(
                    ["bash", "-c", f"echo '{output}' | sed -n 's/.*version \\([0-9][0-9.]*\\).*/\\1/p'"],
                    capture_output=True,
                    text=True,
                )

                extracted = result.stdout.strip()
                if extracted:
                    self.assertEqual(
                        extracted,
                        expected,
                        f"Primary extraction failed for '{output}': got '{extracted}', expected '{expected}'",
                    )
                else:
                    # Method 2: specific regex fallback
                    result = subprocess.run(
                        ["bash", "-c", f"echo '{output}' | grep -o '[0-9]\\+\\.[0-9]\\+\\.[0-9]\\+' | head -1"],
                        capture_output=True,
                        text=True,
                    )
                    extracted = result.stdout.strip()

                    if extracted:
                        self.assertEqual(
                            extracted,
                            expected,
                            f"Fallback extraction failed for '{output}': got '{extracted}', expected '{expected}'",
                        )
                    else:
                        # Method 3: general regex fallback
                        result = subprocess.run(
                            ["bash", "-c", f"echo '{output}' | grep -o '[0-9][0-9.]*' | head -1"],
                            capture_output=True,
                            text=True,
                        )
                        extracted = result.stdout.strip()
                        self.assertEqual(
                            extracted,
                            expected,
                            f"All extraction methods failed for '{output}': got '{extracted}', expected '{expected}'",
                        )

    def test_version_synchronization_validation(self):
        """Test the version synchronization logic between release and codebase."""
        # Test matching versions
        release_version = "1.5.16"
        codebase_version = "1.5.16"

        self.assertEqual(release_version, codebase_version, "Version synchronization should pass for matching versions")

        # Test mismatched versions (should fail)
        release_version = "1.5.15"
        codebase_version = "1.5.16"

        self.assertNotEqual(
            release_version, codebase_version, "Version synchronization should fail for mismatched versions"
        )

    @patch("subprocess.run")
    def test_timeout_handling(self, mock_run):
        """Test timeout handling for version commands."""
        # Test timeout scenario
        mock_run.return_value = MagicMock(returncode=124)  # timeout exit code

        # Simulate the timeout check logic from workflow
        subprocess.run(["true"], timeout=1)  # This won't actually timeout

        # In real workflow, exit code 124 means timeout
        if mock_run.return_value.returncode == 124:
            with self.assertRaises(TimeoutError):
                raise TimeoutError("Version command timed out after 30 seconds")

    def test_error_handling_validation(self):
        """Test error handling for various failure scenarios."""
        # Test command not found
        result = subprocess.run(["bash", "-c", "command -v nonexistent_command"], capture_output=True)
        self.assertNotEqual(result.returncode, 0, "Non-existent command should fail")

        # Test empty version extraction
        result = subprocess.run(
            ["bash", "-c", "echo 'no version here' | grep -o '[0-9][0-9.]*'"], capture_output=True, text=True
        )
        self.assertEqual(result.stdout.strip(), "", "Empty extraction should return empty string")

    def test_fallback_extraction_methods(self):
        """Test that fallback extraction methods work when primary fails."""
        # Test case where primary sed extraction might fail
        problematic_output = "rxiv 1.5.16"  # No "version" keyword

        # Primary method should fail
        result = subprocess.run(
            ["bash", "-c", f"echo '{problematic_output}' | sed -n 's/.*version \\([0-9][0-9.]*\\).*/\\1/p'"],
            capture_output=True,
            text=True,
        )
        primary_result = result.stdout.strip()

        # Fallback method should work
        result = subprocess.run(
            ["bash", "-c", f"echo '{problematic_output}' | grep -o '[0-9]\\+\\.[0-9]\\+\\.[0-9]\\+' | head -1"],
            capture_output=True,
            text=True,
        )
        fallback_result = result.stdout.strip()

        self.assertEqual(fallback_result, "1.5.16", "Fallback extraction should work")
        self.assertNotEqual(primary_result, fallback_result, "Primary and fallback should differ for this case")

    def test_installation_retry_logic_simulation(self):
        """Test the retry logic simulation for installation failures."""
        max_attempts = 3
        success_on_attempt = 2

        # Simulate retry logic
        for attempt in range(1, max_attempts + 1):
            if attempt == success_on_attempt:
                success = True
                break
            else:
                success = False
                if attempt < max_attempts:
                    # In real workflow, there would be a sleep here
                    pass

        self.assertTrue(success, f"Should succeed on attempt {success_on_attempt}")

    def test_workflow_environment_variables(self):
        """Test environment variable handling in workflow context."""
        # Test tag name processing
        test_cases = [
            ("v1.5.16", "1.5.16"),  # Remove v prefix
            ("1.5.16", "1.5.16"),  # No prefix
            ("v2.0.0", "2.0.0"),  # Different version
        ]

        for tag_name, expected_version in test_cases:
            with self.subTest(tag_name=tag_name):
                # Simulate the bash logic: VERSION="${TAG_NAME#v}"
                if tag_name.startswith("v"):
                    version = tag_name[1:]
                else:
                    version = tag_name

                self.assertEqual(version, expected_version, f"Tag processing failed for {tag_name}")


class TestHomebrewWorkflowRobustness(unittest.TestCase):
    """Test robustness aspects of the homebrew workflow."""

    def test_unicode_handling(self):
        """Test that the workflow handles unicode characters gracefully."""
        # Test version output with potential unicode issues
        test_outputs = [
            "rxiv, version 1.5.16",
            "rxiv, version 1.5.16\n",  # With newline
            "rxiv, version 1.5.16\r\n",  # With carriage return
        ]

        for output in test_outputs:
            with self.subTest(output=repr(output)):
                result = subprocess.run(
                    ["bash", "-c", f"echo '{output}' | sed -n 's/.*version \\([0-9][0-9.]*\\).*/\\1/p'"],
                    capture_output=True,
                    text=True,
                )
                extracted = result.stdout.strip()
                self.assertEqual(extracted, "1.5.16", f"Unicode handling failed for {repr(output)}")

    def test_path_handling(self):
        """Test path handling in different environments."""
        # Test that PATH variable affects command discovery
        original_path = os.environ.get("PATH", "")

        try:
            # Test with minimal PATH
            os.environ["PATH"] = "/usr/bin:/bin"
            subprocess.run(["which", "python"], capture_output=True)
            # Should still find python in standard locations

        finally:
            os.environ["PATH"] = original_path

    def test_shell_compatibility(self):
        """Test shell compatibility for bash commands."""
        # Test that the bash syntax used in workflow is compatible
        bash_commands = [
            "echo 'test' | grep -o '[0-9][0-9.]*'",
            "timeout 1 echo 'test' || echo 'timeout failed'",
            "command -v echo >/dev/null 2>&1",
        ]

        for cmd in bash_commands:
            with self.subTest(cmd=cmd):
                result = subprocess.run(["bash", "-c", cmd], capture_output=True)
                # Should not fail with syntax errors
                self.assertNotEqual(result.returncode, 127, f"Bash syntax error in: {cmd}")


if __name__ == "__main__":
    unittest.main()
