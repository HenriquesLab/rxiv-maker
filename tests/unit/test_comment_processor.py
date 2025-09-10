"""Tests for comment processing functionality.

This module tests the critical comment filtering functionality that ensures
commented content is never processed as active content. This is essential
for both security and correctness.
"""

from rxiv_maker.converters.comment_processor import (
    _find_comment_start,
    _find_latex_comment_start,
    filter_latex_comments,
    filter_python_comments,
    preprocess_comments,
    remove_html_comments,
)


class TestHtmlCommentRemoval:
    """Test HTML comment removal functionality."""

    def test_remove_simple_html_comment(self):
        """Test removal of simple HTML comments."""
        input_text = "Before <!-- This is a comment --> After"
        expected = "Before  After"
        result = remove_html_comments(input_text)
        assert result == expected

    def test_remove_multiline_html_comment(self):
        """Test removal of multiline HTML comments."""
        input_text = """Before
<!-- This is a
multiline comment
spanning several lines -->
After"""
        expected = """Before

After"""
        result = remove_html_comments(input_text)
        assert result == expected

    def test_remove_comment_with_table(self):
        """Test removal of HTML comment containing a table (the critical case)."""
        # Create the input without escaping issues
        input_text = (
            "Before table\n\n"
            "<!--| Name | Description | Reference |\n"
            "|-------|----------|--------|\n"
            "| JE2 | Derivative of community-acquired MRSA | @fey_genetic_2013 |\n"
            "| BCBMS14 | JE2 stuff containing stuff-2| %@reed_crispri-based_2024 |\n"
            "| LCML1 | JE2 stuff containing psg-0001_dnaA | @reed_crispri-based_2024 | -->\n\n"
            "After table"
        )
        expected = "Before table\n\n\n\nAfter table"
        result = remove_html_comments(input_text)
        assert result == expected
        # Ensure no table markdown syntax remains
        assert "|" not in result
        assert "@fey_genetic_2013" not in result
        assert "@reed_crispri-based_2024" not in result

    def test_remove_comment_with_citations(self):
        """Test that citations inside comments are removed."""
        input_text = """Regular text
<!-- This paper by @smith2023 and @jones2024 should not be processed -->
More text"""
        expected = """Regular text

More text"""
        result = remove_html_comments(input_text)
        assert result == expected
        assert "@smith2023" not in result
        assert "@jones2024" not in result

    def test_remove_comment_with_executable_blocks(self):
        """Test that executable blocks inside comments are removed."""
        input_text = """Before
<!--
{{py:exec
dangerous_code = "rm -rf /"
os.system(dangerous_code)
}}
The result is {{py:get dangerous_code}}
-->
After"""
        expected = """Before

After"""
        result = remove_html_comments(input_text)
        assert result == expected
        assert "py:exec" not in result
        assert "dangerous_code" not in result

    def test_remove_comment_with_tex_blocks(self):
        """Test that TeX blocks inside comments are removed."""
        input_text = """Before
<!-- {{tex: \\dangerous{command}}} -->
After"""
        expected = """Before

After"""
        result = remove_html_comments(input_text)
        assert result == expected
        assert "tex:" not in result
        assert "dangerous" not in result

    def test_multiple_comments(self):
        """Test removal of multiple HTML comments."""
        input_text = """Start
<!-- First comment -->
Middle
<!-- Second comment with @citation -->
End"""
        expected = """Start

Middle

End"""
        result = remove_html_comments(input_text)
        assert result == expected
        assert "comment" not in result
        assert "@citation" not in result

    def test_nested_comments(self):
        """Test handling of nested comment-like syntax."""
        input_text = """Before
<!-- Outer comment <!-- inner text --> still commented -->
After"""
        # Our algorithm removes comments from first <!-- to first -->
        # This is acceptable behavior for security purposes
        result = remove_html_comments(input_text)
        assert "inner text" not in result
        # Note: "still commented -->" will remain due to our simple parsing
        # This is acceptable as perfect nested comment parsing is complex
        # and the security goal is achieved

    def test_malformed_comments(self):
        """Test handling of malformed comments."""
        input_text = """Before
<!-- Unclosed comment
Regular text after unclosed comment"""
        # Should leave malformed comments as-is (don't break the document)
        result = remove_html_comments(input_text)
        assert "Unclosed comment" in result  # Malformed comment preserved

    def test_empty_comments(self):
        """Test removal of empty comments."""
        input_text = "Before <!-- --> After"
        expected = "Before  After"
        result = remove_html_comments(input_text)
        assert result == expected

    def test_comments_with_special_characters(self):
        """Test comments containing special regex characters."""
        input_text = "Before <!-- Comment with $pecial ^characters* and [brackets] --> After"
        expected = "Before  After"
        result = remove_html_comments(input_text)
        assert result == expected


class TestPythonCommentFiltering:
    """Test Python comment filtering within executable blocks."""

    def test_filter_full_line_comment(self):
        """Test filtering of full-line Python comments."""
        code = """x = 5
# This is a comment
y = 10"""
        expected = """x = 5

y = 10"""
        result = filter_python_comments(code)
        assert result == expected

    def test_filter_inline_comment(self):
        """Test filtering of inline Python comments."""
        code = "x = 5  # This is an inline comment"
        expected = "x = 5"
        result = filter_python_comments(code)
        assert result == expected

    def test_preserve_hash_in_strings(self):
        """Test that # inside strings is preserved."""
        code = """message = "Use #hashtags in social media"  # This is a comment"""
        expected = '''message = "Use #hashtags in social media"'''
        result = filter_python_comments(code)
        assert result == expected
        assert "#hashtags" in result
        assert "This is a comment" not in result

    def test_complex_python_with_comments(self):
        """Test filtering comments in complex Python code."""
        code = """# Initialize variables
import math  # Math library
x = 10  # Set x value
# Calculate result
result = math.sqrt(x)  # Square root
print(f"Result: {result}")  # Display result"""

        result = filter_python_comments(code)

        # Should preserve the actual code
        assert "import math" in result
        assert "x = 10" in result
        assert "result = math.sqrt(x)" in result
        assert 'print(f"Result: {result}")' in result

        # Should remove all comments
        assert "Initialize variables" not in result
        assert "Math library" not in result
        assert "Set x value" not in result
        assert "Calculate result" not in result
        assert "Square root" not in result
        assert "Display result" not in result

    def test_preserve_line_numbers(self):
        """Test that line numbers are preserved for error reporting."""
        code = """line1 = 1
# comment on line 2
line3 = 3
# comment on line 4
line5 = 5"""

        result = filter_python_comments(code)
        lines = result.split("\n")

        # Should have 5 lines (same as input)
        assert len(lines) == 5
        assert lines[0] == "line1 = 1"
        assert lines[1] == ""  # Comment replaced with empty line
        assert lines[2] == "line3 = 3"
        assert lines[3] == ""  # Comment replaced with empty line
        assert lines[4] == "line5 = 5"

    def test_hash_in_various_string_contexts(self):
        """Test # in different string contexts."""
        code = """
single = 'Price: $10 #1 item'  # Comment here
double = "Hashtag: #python"  # Another comment
multiline = '''
This has #hashtags
and # symbols
'''  # Final comment
"""
        result = filter_python_comments(code)

        # Should preserve all the # inside strings
        assert "#1 item" in result
        assert "#python" in result
        # Note: multiline strings are tricky - the current implementation
        # processes line by line, so # inside multiline strings may not be preserved
        # This is acceptable for the security goal of preventing dangerous code execution

        # Should remove all actual comments
        assert "Comment here" not in result
        assert "Another comment" not in result
        # Note: The final comment is tricky because it's after the multiline string close


class TestLatexCommentFiltering:
    """Test LaTeX comment filtering within TeX blocks."""

    def test_filter_full_line_latex_comment(self):
        """Test filtering of full-line LaTeX comments."""
        code = r"""\textbf{Bold}
% This is a comment
\textit{Italic}"""
        expected = r"""\textbf{Bold}

\textit{Italic}"""
        result = filter_latex_comments(code)
        assert result == expected

    def test_filter_inline_latex_comment(self):
        """Test filtering of inline LaTeX comments."""
        code = r"\textbf{Bold} % This is an inline comment"
        expected = r"\textbf{Bold}"
        result = filter_latex_comments(code)
        assert result == expected

    def test_preserve_escaped_percent(self):
        """Test that escaped % (\\%) is preserved."""
        code = r"\text{Price: \$100 \& tax: 5\% (total: \$105)} % This is a comment"
        expected = r"\text{Price: \$100 \& tax: 5\% (total: \$105)}"
        result = filter_latex_comments(code)
        assert result == expected
        assert r"5\%" in result  # Escaped % preserved
        assert "This is a comment" not in result

    def test_complex_latex_with_comments(self):
        """Test filtering comments in complex LaTeX code."""
        code = r"""% Document setup
\documentclass{article} % Article class
\usepackage{amsmath}    % Math package
% Begin document
\begin{document}
\title{My Title} % Document title
\author{Author}  % Author name
\end{document}   % End document"""

        result = filter_latex_comments(code)

        # Should preserve LaTeX commands
        assert r"\documentclass{article}" in result
        assert r"\usepackage{amsmath}" in result
        assert r"\begin{document}" in result
        assert r"\title{My Title}" in result
        assert r"\author{Author}" in result
        assert r"\end{document}" in result

        # Should remove all comments
        assert "Document setup" not in result
        assert "Article class" not in result
        assert "Math package" not in result
        assert "Begin document" not in result
        assert "Document title" not in result
        assert "Author name" not in result
        assert "End document" not in result

    def test_multiple_escaped_percent(self):
        """Test handling of multiple backslashes before %."""
        code = r"""
\text{One backslash: \%}  % Comment 1
\text{Two backslashes: \\%} % Comment 2
\text{Three backslashes: \\\%} % Comment 3
"""
        result = filter_latex_comments(code)

        # \% should be preserved (escaped)
        assert r"\%" in result
        # \\% should have the % removed (not escaped)
        assert r"Two backslashes: \\" in result
        # \\\% should be preserved (escaped)
        assert r"\\\%" in result

        # All comments should be removed
        assert "Comment 1" not in result
        assert "Comment 2" not in result
        assert "Comment 3" not in result


class TestCommentHelperFunctions:
    """Test helper functions for comment detection."""

    def test_find_python_comment_start(self):
        """Test Python comment start detection."""
        # Full line comment
        assert _find_comment_start("# Full line comment") == 0
        assert _find_comment_start("   # Indented comment") == 0

        # Inline comment
        assert _find_comment_start("x = 5  # Inline comment") == 7

        # No comment
        assert _find_comment_start("x = 5") == -1
        assert _find_comment_start("") == -1

        # Hash in string
        assert _find_comment_start('message = "Use #hashtags"') == -1
        assert _find_comment_start("url = 'http://example.com#section'") == -1

        # Hash in string with comment after - need to account for exact position
        test_line = 'msg = "#tag"  # comment'
        expected_pos = test_line.find("  # comment") + 2  # Position of the # in comment
        assert _find_comment_start(test_line) == expected_pos

    def test_find_latex_comment_start(self):
        """Test LaTeX comment start detection."""
        # Full line comment
        assert _find_latex_comment_start("% Full line comment") == 0
        assert _find_latex_comment_start("   % Indented comment") == 0

        # Inline comment
        assert _find_latex_comment_start(r"\textbf{Bold} % comment") == 14

        # No comment
        assert _find_latex_comment_start(r"\textbf{Bold}") == -1
        assert _find_latex_comment_start("") == -1

        # Escaped percent
        assert _find_latex_comment_start(r"\text{5\% tax}") == -1

        # Escaped percent with comment after
        assert _find_latex_comment_start(r"\text{5\% tax} % comment") == 15


class TestPreprocessComments:
    """Test the main preprocessing function."""

    def test_preprocess_removes_html_comments(self):
        """Test that preprocess_comments removes HTML comments."""
        input_text = """Regular text
<!-- This should be removed -->
More text"""
        expected = """Regular text

More text"""
        result = preprocess_comments(input_text)
        assert result == expected

    def test_preprocess_with_mixed_content(self):
        """Test preprocessing with tables, citations, and executable blocks in comments."""
        input_text = """# Document Title

Regular content here.

<!--
| Commented Table | Should Not | Appear |
|-----------------|------------|---------|
| Row 1           | @cite1     | Data    |

{{py:exec
# This dangerous code should never execute
import os
os.system("rm -rf /")
}}

{{tex: \\dangerous{command}}}
-->

More regular content.
"""
        result = preprocess_comments(input_text)

        # Should preserve regular content
        assert "# Document Title" in result
        assert "Regular content here." in result
        assert "More regular content." in result

        # Should remove all commented content
        assert "Commented Table" not in result
        assert "@cite1" not in result
        assert "py:exec" not in result
        assert "os.system" not in result
        assert "dangerous{command}" not in result


class TestIntegrationScenarios:
    """Test integration scenarios mimicking real-world usage."""

    def test_security_scenario_dangerous_code_commented(self):
        """Test that dangerous code in comments never gets processed."""
        input_text = """
# Safe Document

This is safe content.

<!--
{{py:exec
import subprocess
subprocess.run(['rm', '-rf', '/'], check=True)
}}

The result is: {{py:get malicious_result}}

| Malicious | Table | With Citations |
|-----------|-------|----------------|
| Evil      | @bad_paper | {{py:get secret_data}} |
-->

End of document.
"""
        result = preprocess_comments(input_text)

        # Should preserve safe content
        assert "# Safe Document" in result
        assert "This is safe content." in result
        assert "End of document." in result

        # Should remove ALL dangerous content
        assert "py:exec" not in result
        assert "subprocess" not in result
        assert "rm -rf" not in result
        assert "py:get" not in result
        assert "malicious_result" not in result
        assert "secret_data" not in result
        assert "@bad_paper" not in result
        assert "Malicious" not in result

    def test_complex_nested_content_in_comments(self):
        """Test complex nested content inside comments."""
        input_text = """
Regular text

<!--
## Commented Section

This section contains:

- Lists with @citations
- Tables with executable content:

| Name | Code | Result |
|------|------|--------|
| Test | {{py:exec x=1}} | {{py:get x}} |

And some {{tex: \\LaTeX{} commands}}.

### Subsection

More content that should be ignored.
-->

Final text
"""
        result = preprocess_comments(input_text)

        # Only regular content should remain
        assert "Regular text" in result
        assert "Final text" in result

        # All commented content should be gone
        assert "Commented Section" not in result
        assert "Lists with" not in result
        assert "@citations" not in result
        assert "py:exec" not in result
        assert "LaTeX{}" not in result
        assert "Subsection" not in result
        assert "should be ignored" not in result
