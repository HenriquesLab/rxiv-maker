"""Tests for the backtick validation script."""

from pathlib import Path
from unittest.mock import patch

from scripts.validate_backticks import (
    BacktickItem,
    extract_backticks_from_file,
    get_expected_pdf_text,
    normalize_text_for_comparison,
    validate_backtick_item,
)


class TestBacktickExtraction:
    """Test backtick extraction from markdown files."""

    def test_extract_single_backticks(self, tmp_path):
        """Test extraction of single backticks."""
        content = "This is `code` and `more code` here."
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        result = extract_backticks_from_file(test_file)

        assert len(result) == 2
        assert result[0].content == "code"
        assert result[1].content == "more code"
        assert all(item.backtick_type == "single" for item in result)

    def test_extract_double_backticks(self, tmp_path):
        """Test extraction of double backticks."""
        content = "This is ``double code`` and ``more double`` here."
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        result = extract_backticks_from_file(test_file)

        assert len(result) == 2
        assert result[0].content == "double code"
        assert result[1].content == "more double"
        assert all(item.backtick_type == "double" for item in result)

    def test_extract_mixed_backticks(self, tmp_path):
        """Test extraction of mixed single and double backticks."""
        content = "Single `code` and double ``code block`` here."
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        result = extract_backticks_from_file(test_file)

        assert len(result) == 2
        assert result[0].content == "code block"  # Double backticks processed first
        assert result[0].backtick_type == "double"
        assert result[1].content == "code"
        assert result[1].backtick_type == "single"

    def test_extract_with_line_numbers(self, tmp_path):
        """Test that line numbers are correctly captured."""
        content = "Line 1\nThis is `code` on line 2\nLine 3 with ``double``"
        test_file = tmp_path / "test.md"
        test_file.write_text(content)

        result = extract_backticks_from_file(test_file)

        assert len(result) == 2
        # Find the items by content to check line numbers
        double_item = next(item for item in result if item.content == "double")
        single_item = next(item for item in result if item.content == "code")

        assert double_item.line_number == 3
        assert single_item.line_number == 2

    def test_file_read_error(self, tmp_path):
        """Test handling of file read errors."""
        non_existent_file = tmp_path / "nonexistent.md"

        result = extract_backticks_from_file(non_existent_file)

        assert result == []


class TestTextNormalization:
    """Test text normalization for PDF comparison."""

    def test_whitespace_normalization(self):
        """Test that extra whitespace is normalized."""
        text = "  This   has    extra   spaces  "
        result = normalize_text_for_comparison(text)
        assert result == "This has extra spaces"

    def test_brace_normalization(self):
        """Test that braces are normalized (spaces removed)."""
        text = "Text with { spaced } braces"
        result = normalize_text_for_comparison(text)
        assert result == "Text with{spaced}braces"

    def test_backslash_normalization(self):
        """Test that backslash spacing is normalized."""
        text = "LaTeX \\ command with spaces"
        result = normalize_text_for_comparison(text)
        assert result == "LaTeX \\command with spaces"


class TestExpectedPdfText:
    """Test generation of expected PDF text."""

    def test_latex_command_expected(self):
        """Test that LaTeX commands are expected as-is."""
        content = "\\textbf{bold text}"
        result = get_expected_pdf_text(content)
        assert result == content

    def test_citation_expected(self):
        """Test that citations are expected as-is."""
        content = "@fig:test"
        result = get_expected_pdf_text(content)
        assert result == content

    def test_url_expected(self):
        """Test that URLs are expected as-is."""
        content = "https://example.com"
        result = get_expected_pdf_text(content)
        assert result == content

    def test_file_extension_expected(self):
        """Test that file extensions are expected as-is."""
        content = ".py"
        result = get_expected_pdf_text(content)
        assert result == content

    def test_regular_code_expected(self):
        """Test that regular code is expected as-is."""
        content = "variable_name"
        result = get_expected_pdf_text(content)
        assert result == content


class TestBacktickValidation:
    """Test backtick validation against PDF text."""

    def test_successful_validation(self):
        """Test successful validation when content is found."""
        item = BacktickItem(
            content="test_code",
            file_path="test.md",
            line_number=1,
            context="This is `test_code` here",
            backtick_type="single",
        )
        pdf_text = "Some text with test_code in the middle."

        result = validate_backtick_item(item, pdf_text)

        assert result.found_in_pdf is True
        assert len(result.actual_matches) == 1
        assert len(result.issues) == 0

    def test_failed_validation_with_issues(self):
        """Test validation failure with issue detection."""
        item = BacktickItem(
            content="\\textbf{test}",
            file_path="test.md",
            line_number=1,
            context="This is `\\textbf{test}` here",
            backtick_type="single",
        )
        # The normalization will turn \\textbf{test} into \\textbf{test} (no spaces around braces)
        # And will turn "textbftest" into "textbftest"
        # So we need the PDF text to have the content without braces
        pdf_text = "Some text with \\textbftest but missing braces."

        result = validate_backtick_item(item, pdf_text)

        assert result.found_in_pdf is False
        assert "Content found but missing braces" in result.issues

    def test_missing_backslashes_issue(self):
        """Test detection of missing backslashes issue."""
        item = BacktickItem(
            content="\\command",
            file_path="test.md",
            line_number=1,
            context="This is `\\command` here",
            backtick_type="single",
        )
        pdf_text = "Some text with command but missing backslash."

        result = validate_backtick_item(item, pdf_text)

        assert result.found_in_pdf is False
        assert "Content found but missing backslashes" in result.issues


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_content_validation(self):
        """Test validation with empty content."""
        item = BacktickItem(
            content="", file_path="test.md", line_number=1, context="Empty backticks ``", backtick_type="double"
        )
        pdf_text = "Some PDF text"

        result = validate_backtick_item(item, pdf_text)

        # Empty content is technically found (empty string is in any string)
        # but this is expected behavior
        assert result.found_in_pdf is True

    def test_special_characters_in_content(self):
        """Test handling of special regex characters."""
        item = BacktickItem(
            content="test[.*]+()?",
            file_path="test.md",
            line_number=1,
            context="Regex `test[.*]+()?` chars",
            backtick_type="single",
        )
        pdf_text = "Content with test[.*]+()? special chars"

        result = validate_backtick_item(item, pdf_text)

        assert result.found_in_pdf is True

    @patch("scripts.validate_backticks.subprocess.run")
    def test_pdf_build_timeout(self, mock_run):
        """Test PDF build timeout handling."""
        import subprocess

        from scripts.validate_backticks import build_pdf

        mock_run.side_effect = subprocess.TimeoutExpired("rxiv", 300)

        result = build_pdf(Path("/test/path"))

        assert result is False

    @patch("scripts.validate_backticks.subprocess.run")
    def test_pdf_build_error(self, mock_run):
        """Test PDF build error handling."""
        from scripts.validate_backticks import build_pdf

        mock_run.side_effect = Exception("Build failed")

        result = build_pdf(Path("/test/path"))

        assert result is False
