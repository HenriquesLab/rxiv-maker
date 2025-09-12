"""Tests for error message quality and helpfulness regression issues.

This module contains regression tests for error message quality problems
identified by Guillaume, focusing on helpful debugging information and
clear validation messages.

Key issues tested:
- Path not found error message clarity
- CLI help message usefulness
- Validation error actionability
- Debugging information quality
"""

import tempfile
from pathlib import Path

import pytest


class TestErrorMessageQuality:
    """Test that error messages are helpful for debugging Guillaume's issues."""

    def test_path_not_found_error_messages(self):
        """Test that path not found errors provide helpful information."""
        from rxiv_maker.utils import find_manuscript_md

        with tempfile.TemporaryDirectory() as temp_dir:
            empty_dir = Path(temp_dir) / "empty"
            empty_dir.mkdir()

            # Should raise a helpful error message when file not found
            with pytest.raises(FileNotFoundError) as exc_info:
                find_manuscript_md(empty_dir)

            # Error message should be helpful and mention the directory
            error_msg = str(exc_info.value)
            assert "01_MAIN.md not found" in error_msg
            assert str(empty_dir) in error_msg

    def test_cli_help_messages(self):
        """Test that CLI help messages are clear and helpful."""
        from click.testing import CliRunner

        from rxiv_maker.cli.main import main

        runner = CliRunner()

        # Test main help
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "manuscript" in result.output.lower()

        # Test clean command help
        result = runner.invoke(main, ["clean", "--help"])
        assert result.exit_code == 0
        assert "clean" in result.output.lower()

    def test_validation_error_clarity(self):
        """Test that validation errors are clear and actionable."""
        from click.testing import CliRunner

        from rxiv_maker.cli.main import main

        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create incomplete manuscript
            manuscript_dir = Path(temp_dir) / "incomplete"
            manuscript_dir.mkdir()
            # Missing 01_MAIN.md file

            result = runner.invoke(main, ["validate", str(manuscript_dir)], catch_exceptions=True)

            # Should provide clear error about missing file
            assert "01_MAIN.md" in result.output or "main" in result.output.lower()


if __name__ == "__main__":
    pytest.main([__file__])
