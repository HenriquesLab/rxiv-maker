"""Tests for CLI argument parsing regression issues.

This module contains regression tests for CLI argument parsing problems identified
by Guillaume in Issue #97, specifically related to Google Colab compatibility and
unexpected argument handling.

Key issues tested:
- Issue #97: Google Colab argument parsing issues
- CLI command argument validation and error handling
- Compatibility with Google Colab environment
"""

import tempfile
from pathlib import Path

import pytest


class TestCLIArgumentParsing:
    """Test CLI argument parsing issues (Issue #97)."""

    def test_clean_command_with_unexpected_argument(self):
        """Test that clean command properly handles unexpected arguments.

        This tests the specific error from Issue #97:
        'Error: Got unexpected extra argument (paper)'
        """
        from click.testing import CliRunner

        from rxiv_maker.cli.main import main

        runner = CliRunner()

        # Test the problematic command that was failing in Google Colab
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a proper manuscript structure
            manuscript_dir = Path(temp_dir) / "manuscript"
            manuscript_dir.mkdir(parents=True)
            (manuscript_dir / "01_MAIN.md").write_text("# Test")

            # This should not cause "unexpected extra argument" error
            result = runner.invoke(main, ["clean", str(manuscript_dir)], catch_exceptions=False)

            # Should succeed or fail with a different error (not argument parsing)
            assert "Got unexpected extra argument" not in result.output

    def test_clean_command_argument_validation(self):
        """Test clean command argument validation."""
        from click.testing import CliRunner

        from rxiv_maker.cli.main import main

        runner = CliRunner()

        # Test with invalid argument that should be caught properly
        result = runner.invoke(main, ["clean", "--invalid-option"], catch_exceptions=True)

        # Should give a helpful error message, not crash
        assert result.exit_code != 0
        assert "invalid-option" in result.output.lower() or "unknown option" in result.output.lower()

    def test_pdf_command_argument_parsing(self):
        """Test PDF command argument parsing for Google Colab compatibility."""
        from click.testing import CliRunner

        from rxiv_maker.cli.main import main

        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            manuscript_dir = Path(temp_dir) / "manuscript"
            manuscript_dir.mkdir(parents=True)
            (manuscript_dir / "01_MAIN.md").write_text("# Test")

            # Test the command that was run in Google Colab
            result = runner.invoke(main, ["pdf", str(manuscript_dir)], catch_exceptions=True)

            # Should not fail due to argument parsing
            assert "Got unexpected extra argument" not in result.output


if __name__ == "__main__":
    pytest.main([__file__])
