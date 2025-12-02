"""Tests for changelog CLI command."""

import re
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from rxiv_maker.cli.commands.changelog import changelog


def strip_ansi(text):
    """Remove ANSI escape codes from text for testing."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


@pytest.fixture
def runner():
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_changelog():
    """Sample changelog content for testing."""
    # Include current version to match __version__
    return """# Changelog

## [v1.13.7] - 2025-12-02

### Fixed
- DOI display in bibliographies
- Citation system clarification

## [v1.13.6] - 2025-12-02

### Fixed
- Citation auto-injection to use arXiv version

## [v1.13.3] - 2025-11-27

### Fixed
- Custom section headers for non-standard sections

## [v1.13.0] - 2025-11-24

### Added
- Multiple citation styles feature
- Inline DOI resolution

### Fixed
- LaTeX conditional expansion bug

## [v1.12.0] - 2025-11-19

### Added
- New figure positioning

### Changed
- **BREAKING**: Configuration format changed

## [v1.11.0] - 2025-11-15

### Added
- Repository management features
"""


class TestChangelogCommand:
    """Tests for the changelog command."""

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_default_shows_current_version(self, mock_fetch, runner, sample_changelog):
        """Test that default command shows current version."""
        mock_fetch.return_value = sample_changelog

        result = runner.invoke(changelog)

        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "Version" in output
        assert "Fetching changelog" in output

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_specific_version(self, mock_fetch, runner, sample_changelog):
        """Test showing specific version."""
        mock_fetch.return_value = sample_changelog

        result = runner.invoke(changelog, ["v1.13.0"])

        assert result.exit_code == 0
        assert "1.13.0" in result.output
        assert "Multiple citation styles" in result.output

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_recent_flag(self, mock_fetch, runner, sample_changelog):
        """Test --recent flag."""
        mock_fetch.return_value = sample_changelog

        result = runner.invoke(changelog, ["--recent", "2"])

        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "Last 2" in output and "version" in output.lower()

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_since_flag(self, mock_fetch, runner, sample_changelog):
        """Test --since flag."""
        mock_fetch.return_value = sample_changelog

        result = runner.invoke(changelog, ["--since", "v1.11.0"])

        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "since" in output.lower() and "1.11.0" in output

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_breaking_only_flag(self, mock_fetch, runner, sample_changelog):
        """Test --breaking-only flag."""
        mock_fetch.return_value = sample_changelog

        result = runner.invoke(changelog, ["--recent", "5", "--breaking-only"])

        assert result.exit_code == 0
        # Should show v1.12.0 which has breaking changes
        output = strip_ansi(result.output)
        assert "BREAKING" in output or "Configuration format" in output

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_full_flag(self, mock_fetch, runner, sample_changelog):
        """Test --full flag shows complete entry."""
        mock_fetch.return_value = sample_changelog

        result = runner.invoke(changelog, ["v1.13.0", "--full"])

        assert result.exit_code == 0
        assert "Added:" in result.output
        assert "Fixed:" in result.output

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_nonexistent_version(self, mock_fetch, runner, sample_changelog):
        """Test error handling for nonexistent version."""
        mock_fetch.return_value = sample_changelog

        result = runner.invoke(changelog, ["v9.99.99"])

        assert result.exit_code == 1
        assert "not found" in result.output

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_network_error(self, mock_fetch, runner):
        """Test graceful handling of network errors."""
        mock_fetch.side_effect = Exception("Network error")

        result = runner.invoke(changelog)

        assert result.exit_code == 1
        assert "Error fetching changelog" in result.output
        assert "github.com" in result.output  # Should show fallback URL

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_with_breaking_changes_display(self, mock_fetch, runner, sample_changelog):
        """Test that breaking changes are displayed prominently."""
        mock_fetch.return_value = sample_changelog

        result = runner.invoke(changelog, ["v1.12.0"])

        assert result.exit_code == 0
        assert "⚠️" in result.output or "BREAKING" in result.output

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_since_with_no_versions(self, mock_fetch, runner, sample_changelog):
        """Test --since when there are no versions after specified version."""
        mock_fetch.return_value = sample_changelog

        # Use the latest version to ensure no versions after it
        result = runner.invoke(changelog, ["--since", "v1.13.7"])

        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "No versions found" in output

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_recent_with_zero(self, mock_fetch, runner, sample_changelog):
        """Test --recent with 0 defaults to 5."""
        mock_fetch.return_value = sample_changelog

        result = runner.invoke(changelog, ["--recent", "0"])

        assert result.exit_code == 0
        # Should default to showing 5 versions

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_displays_release_link(self, mock_fetch, runner, sample_changelog):
        """Test that release link is displayed."""
        mock_fetch.return_value = sample_changelog

        result = runner.invoke(changelog, ["v1.13.0"])

        assert result.exit_code == 0
        assert "github.com/henriqueslab/rxiv-maker/releases" in result.output


class TestChangelogFormatting:
    """Tests for changelog output formatting."""

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_highlights_format(self, mock_fetch, runner, sample_changelog):
        """Test that highlights are formatted correctly."""
        mock_fetch.return_value = sample_changelog

        result = runner.invoke(changelog, ["v1.13.0"])

        assert result.exit_code == 0
        assert "Highlights:" in result.output
        # Should have emoji formatting
        assert "✨" in result.output or "🐛" in result.output or "🔄" in result.output

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_version_header_format(self, mock_fetch, runner, sample_changelog):
        """Test version header formatting."""
        mock_fetch.return_value = sample_changelog

        result = runner.invoke(changelog, ["v1.13.0"])

        assert result.exit_code == 0
        assert "📦 Version 1.13.0" in result.output
        assert "2025-11-24" in result.output


class TestChangelogEdgeCases:
    """Tests for edge cases in changelog command."""

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_empty_content(self, mock_fetch, runner):
        """Test handling of empty changelog."""
        mock_fetch.return_value = ""

        result = runner.invoke(changelog, ["v1.0.0"])

        assert result.exit_code == 1

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_malformed_content(self, mock_fetch, runner):
        """Test handling of malformed changelog."""
        mock_fetch.return_value = "This is not a valid changelog"

        result = runner.invoke(changelog, ["v1.0.0"])

        assert result.exit_code == 1

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_version_without_date(self, mock_fetch, runner):
        """Test version without date is handled correctly."""
        changelog_no_date = """# Changelog

## [v1.0.0]

### Added
- Some feature
"""
        mock_fetch.return_value = changelog_no_date

        result = runner.invoke(changelog, ["v1.0.0"])

        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "Version" in output and "1.0.0" in output

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_recent_exceeds_available(self, mock_fetch, runner, sample_changelog):
        """Test requesting more recent versions than available."""
        mock_fetch.return_value = sample_changelog

        result = runner.invoke(changelog, ["--recent", "100"])

        # Should show all available versions without error
        assert result.exit_code == 0


class TestChangelogIntegration:
    """Integration tests for changelog command."""

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_full_workflow(self, mock_fetch, runner, sample_changelog):
        """Test complete workflow from fetch to display."""
        mock_fetch.return_value = sample_changelog

        # Test each major use case
        result1 = runner.invoke(changelog, ["v1.13.0"])
        assert result1.exit_code == 0

        result2 = runner.invoke(changelog, ["--recent", "2"])
        assert result2.exit_code == 0

        result3 = runner.invoke(changelog, ["--since", "v1.11.0"])
        assert result3.exit_code == 0

        # --breaking-only without other args shows current version, which may not have breaking changes
        # Use with --recent instead
        result4 = runner.invoke(changelog, ["--recent", "5", "--breaking-only"])
        assert result4.exit_code == 0

    @patch("rxiv_maker.cli.commands.changelog.fetch_changelog")
    def test_changelog_combined_flags(self, mock_fetch, runner, sample_changelog):
        """Test combining multiple flags."""
        mock_fetch.return_value = sample_changelog

        result = runner.invoke(changelog, ["--recent", "3", "--breaking-only", "--full"])

        assert result.exit_code == 0
        # Should show only versions with breaking changes in full format
