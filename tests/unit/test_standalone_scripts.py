"""Test that standalone scripts can be executed without import errors.

This test ensures that all command scripts that may be executed directly
have proper import handling to avoid relative import errors.
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestStandaloneScripts:
    """Test standalone script execution."""

    @pytest.fixture
    def src_path(self):
        """Get the path to the src directory."""
        return Path(__file__).parent.parent.parent / "src"

    def run_script_import_test(self, script_path: Path) -> tuple[bool, str]:
        """Test if a script can be imported without errors.

        Args:
            script_path: Path to the script to test

        Returns:
            Tuple of (success, error_message)
        """
        # Run the script with Python in a way that tests imports
        cmd = [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, '{script_path.parent.parent.parent}'); exec(open('{script_path}').read())",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

            # Check for import errors in stderr
            if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
                return False, result.stderr

            # Also check stdout for import errors (some scripts print to stdout)
            if "ImportError" in result.stdout or "ModuleNotFoundError" in result.stdout:
                return False, result.stdout

            return True, ""

        except subprocess.TimeoutExpired:
            # Timeout is OK - it means the script started but may be waiting for input
            return True, ""
        except Exception as e:
            return False, str(e)

    @pytest.mark.parametrize(
        "script_name",
        [
            "copy_pdf.py",
            "analyze_word_count.py",
            "validate_pdf.py",
            "generate_preprint.py",
            "generate_figures.py",
            "fix_bibliography.py",
            "add_bibliography.py",
            "track_changes.py",
            "prepare_arxiv.py",
            "setup_environment.py",
        ],
    )
    @pytest.mark.fast
    def test_command_scripts_imports(self, src_path, script_name):
        """Test that command scripts can be executed without import errors."""
        script_path = src_path / "rxiv_maker" / "commands" / script_name

        if not script_path.exists():
            pytest.skip(f"Script {script_name} not found")

        success, error = self.run_script_import_test(script_path)

        assert success, f"Script {script_name} has import errors: {error}"

    @pytest.mark.fast
    def test_pdf_validator_imports(self, src_path):
        """Test that pdf_validator.py can be imported."""
        script_path = src_path / "rxiv_maker" / "validators" / "pdf_validator.py"

        if not script_path.exists():
            pytest.skip("pdf_validator.py not found")

        # For validators, we need to check if they're being run as scripts
        with open(script_path) as f:
            content = f.read()

        # Check if the file has __main__ section
        if "__main__" in content:
            success, error = self.run_script_import_test(script_path)
            assert success, (
                f"pdf_validator.py has import errors when run as script: {error}"
            )

    @pytest.mark.parametrize(
        "script_path,expected_imports",
        [
            (
                "commands/copy_pdf.py",
                ["yaml_processor", "copy_pdf_to_manuscript_folder"],
            ),
            ("commands/analyze_word_count.py", ["extract_content_sections"]),
            ("validators/pdf_validator.py", ["base_validator"]),
        ],
    )
    def test_script_has_proper_imports(self, src_path, script_path, expected_imports):
        """Test that scripts have proper import handling for standalone execution."""
        full_path = src_path / "rxiv_maker" / script_path

        if not full_path.exists():
            pytest.skip(f"Script {script_path} not found")

        with open(full_path) as f:
            content = f.read()

        # Check if script has __main__ section
        has_main = "__main__" in content

        # Check if script has sys.path manipulation for imports
        has_sys_path = "sys.path" in content

        # Check if script uses relative imports
        has_relative_imports = any(imp in content for imp in ["from ..", "from ."])

        if has_main and has_relative_imports:
            assert has_sys_path, (
                f"Script {script_path} has __main__ and relative imports but no sys.path manipulation"
            )
