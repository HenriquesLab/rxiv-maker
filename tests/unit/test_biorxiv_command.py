"""Unit tests for bioRxiv CLI command."""

from click.testing import CliRunner

from rxiv_maker.cli.commands.biorxiv import biorxiv


class TestBioRxivCommand:
    """Test the bioRxiv CLI command."""

    def test_biorxiv_command_help(self):
        """Test that help message displays correctly."""
        runner = CliRunner()
        result = runner.invoke(biorxiv, ["--help"])
        assert result.exit_code == 0
        assert "bioRxiv submission package" in result.output
        assert "author template" in result.output or "TSV file" in result.output
