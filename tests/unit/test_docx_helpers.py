"""Tests for DOCX helper utilities."""

from rxiv_maker.utils.bibliography_parser import BibEntry
from rxiv_maker.utils.docx_helpers import (
    clean_latex_commands,
    format_authors_list,
    format_bibliography_entry,
    normalize_whitespace,
    remove_yaml_header,
    truncate_text,
)


class TestRemoveYamlHeader:
    """Test YAML header removal."""

    def test_removes_yaml_header(self):
        """Test removing YAML frontmatter."""
        content = "---\ntitle: Test\nauthor: Smith\n---\n\nActual content"
        result = remove_yaml_header(content)
        assert result == "Actual content"

    def test_no_yaml_header(self):
        """Test content without YAML header."""
        content = "Just regular content"
        result = remove_yaml_header(content)
        assert result == content

    def test_yaml_header_not_closed(self):
        """Test content with unclosed YAML header."""
        content = "---\ntitle: Test\n\nNo closing delimiter"
        result = remove_yaml_header(content)
        assert result == content  # Returns original if not properly closed

    def test_preserves_content_after_header(self):
        """Test that all content after header is preserved."""
        content = "---\ntitle: Test\n---\n\n# Heading\n\nParagraph with text."
        result = remove_yaml_header(content)
        assert result == "# Heading\n\nParagraph with text."


class TestFormatBibliographyEntry:
    """Test bibliography entry formatting."""

    def test_format_complete_entry(self):
        """Test formatting a complete bibliography entry."""
        entry = BibEntry(
            key="smith2021",
            entry_type="article",
            fields={"author": "Smith, J.", "year": "2021", "title": "Test Article", "journal": "Nature"},
            raw="",
        )
        result = format_bibliography_entry(entry)
        assert "Smith, J." in result
        assert "(2021)" in result
        assert "Test Article" in result
        assert "Nature" in result

    def test_format_entry_with_doi(self):
        """Test formatting entry with DOI."""
        entry = BibEntry(
            key="smith2021",
            entry_type="article",
            fields={"author": "Smith, J.", "year": "2021", "title": "Test Article"},
            raw="",
        )
        result = format_bibliography_entry(entry, doi="10.1234/example")
        assert "DOI: https://doi.org/10.1234/example" in result

    def test_format_entry_missing_fields(self):
        """Test formatting entry with missing fields."""
        entry = BibEntry(key="incomplete", entry_type="article", fields={}, raw="")
        result = format_bibliography_entry(entry)
        # Author formatting converts "Unknown Author" to "Author, Unknown"
        assert "Author, Unknown" in result or "Unknown Author" in result
        assert "(n.d.)" in result
        assert "Untitled" in result

    def test_format_entry_no_journal(self):
        """Test formatting entry without journal."""
        entry = BibEntry(
            key="book2021",
            entry_type="book",
            fields={"author": "Author, A.", "year": "2021", "title": "Book Title"},
            raw="",
        )
        result = format_bibliography_entry(entry)
        assert "Book Title." in result
        # Should end with title period since no journal
        assert result.rstrip() == "Author, A. (2021). Book Title."


class TestFormatAuthorsList:
    """Test authors list formatting."""

    def test_format_single_author(self):
        """Test formatting single author."""
        result = format_authors_list("Smith, J.")
        assert result == "Smith, J."

    def test_format_two_authors(self):
        """Test formatting two authors."""
        result = format_authors_list("Smith, J. and Jones, A.")
        assert result == "Smith, J., Jones, A."

    def test_format_many_authors_truncated(self):
        """Test truncating long author list."""
        authors = "Smith, J. and Jones, A. and Brown, B. and White, C."
        result = format_authors_list(authors, max_authors=2)
        assert "Smith, J., Jones, A., et al." == result

    def test_format_exactly_max_authors(self):
        """Test with exactly max_authors."""
        authors = "Smith, J. and Jones, A. and Brown, B."
        result = format_authors_list(authors, max_authors=3)
        assert result == "Smith, J., Jones, A., Brown, B."

    def test_format_empty_authors(self):
        """Test with empty authors string."""
        result = format_authors_list("")
        assert result == "Unknown Author"


class TestCleanLatexCommands:
    """Test LaTeX command cleaning."""

    def test_clean_textbf(self):
        """Test removing textbf command."""
        text = "This is \\textbf{bold} text"
        result = clean_latex_commands(text)
        assert result == "This is bold text"

    def test_clean_textit(self):
        """Test removing textit command."""
        text = "This is \\textit{italic} text"
        result = clean_latex_commands(text)
        assert result == "This is italic text"

    def test_clean_cite(self):
        """Test removing cite command."""
        text = "Reference \\cite{smith2021} here"
        result = clean_latex_commands(text)
        assert "\\cite" not in result
        assert "Reference  here" in result

    def test_clean_multiple_commands(self):
        """Test removing multiple commands."""
        text = "Text with \\textbf{bold} and \\textit{italic} and \\cite{ref}"
        result = clean_latex_commands(text)
        assert result == "Text with bold and italic and "


class TestTruncateText:
    """Test text truncation."""

    def test_no_truncation_needed(self):
        """Test text shorter than max length."""
        text = "Short text"
        result = truncate_text(text, max_length=50)
        assert result == text

    def test_truncates_long_text(self):
        """Test truncating long text."""
        text = "This is a very long text that needs to be truncated"
        result = truncate_text(text, max_length=20)
        assert len(result) == 20
        assert result.endswith("...")

    def test_custom_suffix(self):
        """Test custom truncation suffix."""
        text = "Long text here"
        result = truncate_text(text, max_length=10, suffix=">>")
        assert result.endswith(">>")
        assert len(result) == 10


class TestNormalizeWhitespace:
    """Test whitespace normalization."""

    def test_multiple_spaces(self):
        """Test collapsing multiple spaces."""
        text = "Text  with   many    spaces"
        result = normalize_whitespace(text)
        assert result == "Text with many spaces"

    def test_newlines(self):
        """Test collapsing newlines."""
        text = "Line 1\n\nLine 2\nLine 3"
        result = normalize_whitespace(text)
        assert result == "Line 1 Line 2 Line 3"

    def test_tabs(self):
        """Test collapsing tabs."""
        text = "Text\twith\t\ttabs"
        result = normalize_whitespace(text)
        assert result == "Text with tabs"

    def test_mixed_whitespace(self):
        """Test mixed whitespace types."""
        text = "  Text  \n\n  with   \t mixed  \n spaces  "
        result = normalize_whitespace(text)
        assert result == "Text with mixed spaces"
