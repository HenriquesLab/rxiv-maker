"""Unit tests for text_utils module."""

from rxiv_maker.utils.text_utils import clean_text_for_analysis, count_words_in_text


class TestCountWordsInText:
    """Test cases for count_words_in_text function."""

    def test_simple_text(self):
        """Test counting words in simple text."""
        assert count_words_in_text("Hello world") == 2
        assert count_words_in_text("This is a test") == 4

    def test_empty_and_none_input(self):
        """Test handling of empty and None input."""
        assert count_words_in_text("") == 0
        assert count_words_in_text("   ") == 0
        assert count_words_in_text(None) == 0

    def test_code_blocks_removal(self):
        """Test that code blocks are properly removed from word count."""
        text_with_code = "Hello ```python\nprint('test')\n``` world"
        assert count_words_in_text(text_with_code) == 2

        # Multiple code blocks
        text_multi_code = "Start ```code1``` middle ```code2``` end"
        assert count_words_in_text(text_multi_code) == 3

    def test_inline_code_removal(self):
        """Test that inline code is properly removed from word count."""
        text_with_inline = "Hello `inline_code` world"
        assert count_words_in_text(text_with_inline) == 2

        # Multiple inline code
        text_multi_inline = "Start `code1` middle `code2` end"
        assert count_words_in_text(text_multi_inline) == 3

    def test_latex_commands_removal(self):
        """Test that LaTeX commands are properly removed from word count."""
        # LaTeX commands with braces
        text_with_latex = "Hello \\textbf{bold} world"
        assert count_words_in_text(text_with_latex) == 2

        # Standalone LaTeX commands
        text_with_standalone = "Hello \\newline world"
        assert count_words_in_text(text_with_standalone) == 2

        # Multiple LaTeX commands
        text_multi_latex = "\\section{Title} Hello \\textit{italic} and \\textbf{bold} text"
        # Expected: Hello, and, text (3 words, LaTeX commands removed)
        assert count_words_in_text(text_multi_latex) == 3

    def test_combined_formatting(self):
        """Test word counting with combined code blocks, inline code, and LaTeX."""
        complex_text = """
        # Introduction

        This is a \\textbf{bold} statement with `inline_code` and a code block:

        ```python
        def hello():
            print("Hello world")
        ```

        The \\textit{result} is amazing.
        """
        # Expected words: #, Introduction, This, is, a, statement, with, and, a, code, block:, The, is, amazing.
        # (14 words after removing LaTeX commands and code)
        result = count_words_in_text(complex_text)
        assert result == 14

    def test_whitespace_handling(self):
        """Test that extra whitespace doesn't affect word count."""
        assert count_words_in_text("  hello    world  ") == 2
        assert count_words_in_text("word1\n\nword2\t\tword3") == 3

    def test_special_characters(self):
        """Test word counting with special characters."""
        assert count_words_in_text("hello-world test_case") == 2
        assert count_words_in_text("user@example.com is an email") == 4


class TestCleanTextForAnalysis:
    """Test cases for clean_text_for_analysis function."""

    def test_empty_and_none_input(self):
        """Test handling of empty and None input."""
        assert clean_text_for_analysis("") == ""
        assert clean_text_for_analysis(None) == ""

    def test_simple_text_unchanged(self):
        """Test that simple text remains unchanged."""
        text = "This is a simple sentence."
        assert clean_text_for_analysis(text) == text

    def test_code_blocks_removed(self):
        """Test that code blocks are removed but other text remains."""
        text = "Before ```python\ncode here\n``` after"
        expected = "Before  after"
        assert clean_text_for_analysis(text) == expected

    def test_inline_code_removed(self):
        """Test that inline code is removed but other text remains."""
        text = "Before `inline code` after"
        expected = "Before  after"
        assert clean_text_for_analysis(text) == expected

    def test_latex_commands_removed(self):
        """Test that LaTeX commands are removed but other text remains."""
        text = "Before \\textbf{bold text} and \\newline after"
        expected = "Before  and  after"
        assert clean_text_for_analysis(text) == expected

    def test_combined_cleaning(self):
        """Test cleaning with all types of formatting."""
        text = "Start \\section{Title} with `code` and ```block\ncode``` end"
        # Should remove LaTeX commands, inline code, and code blocks
        result = clean_text_for_analysis(text)
        assert "section" not in result.lower()
        assert "title" not in result.lower()
        assert "code" not in result.lower()
        assert "block" not in result.lower()
        # Should keep the main words
        assert "Start" in result
        assert "with" in result
        assert "and" in result
        assert "end" in result

    def test_whitespace_normalized(self):
        """Test that the result is properly stripped."""
        text = "   \\textbf{title} content   "
        result = clean_text_for_analysis(text)
        assert result == "content"
        assert not result.startswith(" ")
        assert not result.endswith(" ")
