"""Tests for changelog parser module."""

from rxiv_maker.utils.changelog_parser import (
    ChangelogEntry,
    detect_breaking_changes,
    extract_highlights,
    fetch_and_format_changelog,
    format_summary,
    get_versions_between,
    parse_sections,
    parse_version_entry,
)

# Sample changelog content for testing
SAMPLE_CHANGELOG = """# Changelog

All notable changes to this project will be documented in this file.

## [v1.13.0] - 2025-11-24

### Added
- **Multiple citation styles**: Choose between numbered citations `[1, 2]` and author-date format `(Smith, 2024)` via `citation_style` config option
  - Numbered style (default): Traditional academic format
  - Author-date style: Parenthetical citations like `(Smith, 2024)`
- **Inline DOI resolution**: Automatically convert DOIs in text to proper BibTeX citations
  - Enable via `enable_inline_doi_resolution: true` in config
  - Fetches metadata from CrossRef/DataCite APIs

### Changed
- Updated documentation with new citation examples

### Fixed
- Fixed LaTeX conditional expansion for citation style switching
- Fixed DOI regex to handle trailing punctuation correctly

## [v1.12.1] - 2025-11-20

### Fixed
- Fixed competing interests placement in template
- Fixed DOI hyperlinks in references

## [v1.12.0] - 2025-11-19

### Added
- New figure positioning options

### Changed
- **BREAKING**: Changed configuration format for figures
  - Old format no longer supported
  - See migration guide for upgrading

### Removed
- Removed inline methods placement option

## [v1.11.0] - 2025-11-15

### Added
- Repository management features
- GitHub integration

### Security
- ⚠️ Fixed potential command injection vulnerability
"""


class TestParseVersionEntry:
    """Tests for parse_version_entry function."""

    def test_parse_existing_version(self):
        """Test parsing an existing version."""
        entry = parse_version_entry(SAMPLE_CHANGELOG, "1.13.0")

        assert entry is not None
        assert entry.version == "1.13.0"
        assert entry.date == "2025-11-24"
        assert "Added" in entry.sections
        assert "Changed" in entry.sections
        assert "Fixed" in entry.sections

    def test_parse_version_with_v_prefix(self):
        """Test parsing version with v prefix."""
        entry = parse_version_entry(SAMPLE_CHANGELOG, "v1.13.0")

        assert entry is not None
        assert entry.version == "1.13.0"

    def test_parse_nonexistent_version(self):
        """Test parsing a version that doesn't exist."""
        entry = parse_version_entry(SAMPLE_CHANGELOG, "9.99.99")

        assert entry is None

    def test_parse_version_without_date(self):
        """Test parsing version header without date."""
        changelog = "## [v1.0.0]\n\n### Added\n- Some feature\n"
        entry = parse_version_entry(changelog, "1.0.0")

        assert entry is not None
        assert entry.version == "1.0.0"
        assert entry.date is None


class TestParseSections:
    """Tests for parse_sections function."""

    def test_parse_basic_sections(self):
        """Test parsing basic Added/Changed/Fixed sections."""
        content = """
### Added
- Feature one
- Feature two

### Fixed
- Bug fix one
"""
        sections = parse_sections(content)

        assert "Added" in sections
        assert len(sections["Added"]) == 2
        assert sections["Added"][0] == "Feature one"
        assert "Fixed" in sections
        assert len(sections["Fixed"]) == 1

    def test_parse_with_nested_bullets(self):
        """Test parsing items with nested bullets."""
        content = """
### Added
- **Main feature**: Description
  - Sub-detail one
  - Sub-detail two
- Another feature
"""
        sections = parse_sections(content)

        assert "Added" in sections
        # Parser treats indented items as separate bullets (4 total)
        assert len(sections["Added"]) == 4
        # First item is the main feature
        assert "Main feature" in sections["Added"][0]
        # Nested items are captured
        assert "Sub-detail one" in sections["Added"][1]
        assert "Another feature" in sections["Added"][3]

    def test_parse_empty_section(self):
        """Test parsing section with no items."""
        content = """
### Added

### Fixed
- Bug fix
"""
        sections = parse_sections(content)

        assert "Added" in sections
        assert len(sections["Added"]) == 0
        assert "Fixed" in sections
        assert len(sections["Fixed"]) == 1

    def test_parse_all_section_types(self):
        """Test parsing all supported section types."""
        content = """
### Added
- Added item

### Changed
- Changed item

### Fixed
- Fixed item

### Removed
- Removed item

### Documentation
- Doc item

### Deprecated
- Deprecated item

### Security
- Security item
"""
        sections = parse_sections(content)

        assert len(sections) == 7
        assert all(
            section in sections
            for section in [
                "Added",
                "Changed",
                "Fixed",
                "Removed",
                "Documentation",
                "Deprecated",
                "Security",
            ]
        )


class TestExtractHighlights:
    """Tests for extract_highlights function."""

    def test_extract_with_limit(self):
        """Test extracting limited number of highlights."""
        entry = parse_version_entry(SAMPLE_CHANGELOG, "1.13.0")
        highlights = extract_highlights(entry, limit=2)

        assert len(highlights) == 2
        # Should prioritize Added section
        assert highlights[0][0] == "✨"  # Added emoji

    def test_extract_all_highlights(self):
        """Test extracting all highlights."""
        entry = parse_version_entry(SAMPLE_CHANGELOG, "1.13.0")
        highlights = extract_highlights(entry, limit=10)

        # Should get items from multiple sections
        emojis = [h[0] for h in highlights]
        assert "✨" in emojis  # Added
        assert "🔄" in emojis  # Changed
        assert "🐛" in emojis  # Fixed

    def test_extract_prioritizes_added(self):
        """Test that Added items are prioritized."""
        entry = parse_version_entry(SAMPLE_CHANGELOG, "1.13.0")
        highlights = extract_highlights(entry, limit=3)

        # First items should be from Added section
        assert highlights[0][0] == "✨"
        assert highlights[1][0] == "✨"

    def test_extract_truncates_long_descriptions(self):
        """Test that long descriptions are truncated."""
        content = """
## [v1.0.0] - 2025-01-01

### Added
- This is a very long feature description that should be truncated because it exceeds the maximum length allowed for highlights and we don't want to display too much text in the terminal
"""
        entry = parse_version_entry(content, "1.0.0")
        highlights = extract_highlights(entry, limit=1)

        assert len(highlights) == 1
        description = highlights[0][1]
        assert len(description) <= 80
        assert description.endswith("...")

    def test_extract_from_empty_entry(self):
        """Test extracting from entry with no items."""
        content = """
## [v1.0.0] - 2025-01-01

### Added
"""
        entry = parse_version_entry(content, "1.0.0")
        highlights = extract_highlights(entry, limit=3)

        assert len(highlights) == 0


class TestDetectBreakingChanges:
    """Tests for detect_breaking_changes function."""

    def test_detect_breaking_keyword(self):
        """Test detecting BREAKING keyword."""
        entry = parse_version_entry(SAMPLE_CHANGELOG, "1.12.0")
        breaking = detect_breaking_changes(entry)

        assert len(breaking) > 0
        assert any("configuration format" in b.lower() for b in breaking)

    def test_detect_warning_emoji(self):
        """Test detecting ⚠️ emoji."""
        entry = parse_version_entry(SAMPLE_CHANGELOG, "1.11.0")
        breaking = detect_breaking_changes(entry)

        assert len(breaking) > 0
        assert any("command injection" in b.lower() for b in breaking)

    def test_no_breaking_changes(self):
        """Test entry with no breaking changes."""
        entry = parse_version_entry(SAMPLE_CHANGELOG, "1.12.1")
        breaking = detect_breaking_changes(entry)

        assert len(breaking) == 0

    def test_detect_multiple_breaking_changes(self):
        """Test detecting multiple breaking changes."""
        content = """
## [v1.0.0] - 2025-01-01

### Changed
- **BREAKING**: API change one
- **BREAKING**: API change two
- Regular change
"""
        entry = parse_version_entry(content, "1.0.0")
        breaking = detect_breaking_changes(entry)

        assert len(breaking) == 2


class TestGetVersionsBetween:
    """Tests for get_versions_between function."""

    def test_get_consecutive_versions(self):
        """Test getting versions between consecutive releases."""
        versions = get_versions_between(SAMPLE_CHANGELOG, "1.12.1", "1.13.0")

        assert versions == ["1.13.0"]

    def test_get_multiple_versions(self):
        """Test getting multiple versions."""
        versions = get_versions_between(SAMPLE_CHANGELOG, "1.11.0", "1.13.0")

        # Should return in chronological order (oldest to newest)
        assert len(versions) == 3
        assert versions == ["1.12.0", "1.12.1", "1.13.0"]

    def test_get_with_v_prefix(self):
        """Test with v prefix in versions."""
        versions = get_versions_between(SAMPLE_CHANGELOG, "v1.12.1", "v1.13.0")

        assert versions == ["1.13.0"]

    def test_get_invalid_range(self):
        """Test with invalid version range."""
        versions = get_versions_between(SAMPLE_CHANGELOG, "9.99.99", "1.13.0")

        assert versions == []

    def test_get_same_versions(self):
        """Test with same current and latest version."""
        versions = get_versions_between(SAMPLE_CHANGELOG, "1.13.0", "1.13.0")

        assert versions == []

    def test_get_reverse_order(self):
        """Test with newer current than latest (should return empty)."""
        versions = get_versions_between(SAMPLE_CHANGELOG, "1.13.0", "1.12.0")

        assert versions == []


class TestFormatSummary:
    """Tests for format_summary function."""

    def test_format_single_version(self):
        """Test formatting single version."""
        entry = parse_version_entry(SAMPLE_CHANGELOG, "1.13.0")
        summary = format_summary([entry], show_breaking=False, highlights_per_version=2)

        assert "v1.13.0" in summary
        assert "2025-11-24" in summary
        assert "What's New:" in summary
        # Should contain emojis
        assert "✨" in summary

    def test_format_multiple_versions(self):
        """Test formatting multiple versions."""
        entry1 = parse_version_entry(SAMPLE_CHANGELOG, "1.13.0")
        entry2 = parse_version_entry(SAMPLE_CHANGELOG, "1.12.1")
        summary = format_summary([entry1, entry2], show_breaking=False)

        assert "v1.13.0" in summary
        assert "v1.12.1" in summary
        assert summary.index("v1.13.0") < summary.index("v1.12.1")  # Order preserved

    def test_format_with_breaking_changes(self):
        """Test formatting with breaking changes highlighted."""
        entry = parse_version_entry(SAMPLE_CHANGELOG, "1.12.0")
        summary = format_summary([entry], show_breaking=True)

        assert "⚠️  BREAKING CHANGES:" in summary
        assert "configuration format" in summary.lower()

    def test_format_without_breaking_section(self):
        """Test that breaking section is omitted when no breaking changes."""
        entry = parse_version_entry(SAMPLE_CHANGELOG, "1.13.0")
        summary = format_summary([entry], show_breaking=True)

        assert "BREAKING CHANGES:" not in summary

    def test_format_respects_highlights_limit(self):
        """Test that highlights limit is respected."""
        entry = parse_version_entry(SAMPLE_CHANGELOG, "1.13.0")
        summary = format_summary([entry], show_breaking=False, highlights_per_version=1)

        # Split by "What's New:" header to only count highlights (not the header emoji)
        if "What's New:" in summary:
            highlights_section = summary.split("What's New:", 1)[1]
        else:
            highlights_section = summary

        # Count number of emoji highlights in the highlights section
        emoji_count = highlights_section.count("✨") + highlights_section.count("🔄") + highlights_section.count("🐛")
        assert emoji_count == 1


class TestFetchAndFormatChangelog:
    """Tests for fetch_and_format_changelog function (integration)."""

    def test_invalid_url_returns_error(self):
        """Test that invalid URL returns error message."""
        summary, error = fetch_and_format_changelog(
            "1.12.0",
            "1.13.0",
            changelog_url="https://invalid.url.that.does.not.exist/changelog.md",
        )

        assert summary is None
        assert error is not None
        assert "Failed to fetch changelog" in error

    def test_invalid_version_range_returns_error(self):
        """Test that invalid version range returns error."""
        # Using a mock changelog that won't have these versions
        summary, error = fetch_and_format_changelog(
            "9.99.98",
            "9.99.99",
            changelog_url="https://raw.githubusercontent.com/HenriquesLab/rxiv-maker/main/CHANGELOG.md",
        )

        assert summary is None
        assert error is not None
        assert "No changelog entries found" in error or "Could not parse" in error


class TestChangelogEntry:
    """Tests for ChangelogEntry dataclass."""

    def test_changelog_entry_creation(self):
        """Test creating a ChangelogEntry."""
        entry = ChangelogEntry(
            version="1.0.0",
            date="2025-01-01",
            sections={"Added": ["Feature one"]},
            raw_content="### Added\n- Feature one",
        )

        assert entry.version == "1.0.0"
        assert entry.date == "2025-01-01"
        assert "Added" in entry.sections
        assert entry.raw_content != ""


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_malformed_changelog(self):
        """Test parsing malformed changelog."""
        malformed = "This is not a valid changelog format\nJust some random text\n"
        entry = parse_version_entry(malformed, "1.0.0")

        assert entry is None

    def test_empty_changelog(self):
        """Test parsing empty changelog."""
        entry = parse_version_entry("", "1.0.0")

        assert entry is None

    def test_version_without_sections(self):
        """Test parsing version entry without any sections."""
        changelog = "## [v1.0.0] - 2025-01-01\n\nSome text but no sections\n"
        entry = parse_version_entry(changelog, "1.0.0")

        assert entry is not None
        assert entry.version == "1.0.0"
        assert len(entry.sections) == 0

    def test_unicode_in_changelog(self):
        """Test handling Unicode characters in changelog."""
        changelog = """
## [v1.0.0] - 2025-01-01

### Added
- Feature with émojis 🎉 and ünicode
- 中文 support
"""
        entry = parse_version_entry(changelog, "1.0.0")

        assert entry is not None
        highlights = extract_highlights(entry)
        assert len(highlights) > 0
