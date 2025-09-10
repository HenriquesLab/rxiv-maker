"""Integration tests for the complete comment system functionality.

This module tests the end-to-end functionality of the comment filtering system
across all three types of comments: HTML, Python, and LaTeX. It ensures that
the security fixes work correctly in the full processing pipeline.
"""

from rxiv_maker.converters.custom_command_processor import process_custom_commands
from rxiv_maker.converters.md2tex import convert_markdown_to_latex


class TestCommentSystemIntegration:
    """Test end-to-end comment system integration."""

    def test_html_comment_filtering_in_full_pipeline(self):
        """Test that HTML comments are filtered out in the complete processing pipeline."""
        # Create markdown with HTML comments containing dangerous content
        markdown_content = """
# Document Title

Regular content here.

<!--
| Dangerous | Table | Should Not Appear |
|-----------|-------|-------------------|
| Row 1     | @malicious_citation | Data |

{{py:exec
import os
os.system("rm -rf /")
}}

{{tex: \\dangerouscommand{malicious}}}
-->

More regular content after the comment.
"""

        # Process through the full pipeline
        result = convert_markdown_to_latex(markdown_content)

        # Should preserve safe content
        assert "Document Title" in result
        assert "Regular content here." in result
        assert "More regular content after the comment." in result

        # Should remove ALL dangerous commented content
        assert "Dangerous" not in result
        assert "Table" not in result
        assert "Should Not Appear" not in result
        assert "@malicious_citation" not in result
        assert "py:exec" not in result
        assert "os.system" not in result
        assert "rm -rf" not in result
        assert "dangerouscommand" not in result
        assert "malicious" not in result

    def test_python_comment_filtering_in_executable_blocks(self):
        """Test that Python comments are filtered in executable blocks."""
        markdown_content = """
{{py:exec
# This is a dangerous comment that should not execute
import math
x = 5  # This comment should also be filtered
# y = dangerous_function()
result = math.sqrt(x)
}}

The result is: {{py:get result}}
"""

        # Process the custom commands
        result = process_custom_commands(markdown_content)

        # Should execute the valid Python code
        assert "2.236" in result or "2.23606" in result  # sqrt(5) ≈ 2.236

        # Should not contain any comments in the output or processing
        # Note: We can't easily test that comments weren't executed since they're filtered,
        # but we can verify the result is mathematically correct

    def test_latex_comment_filtering_in_tex_blocks(self):
        """Test that LaTeX comments are filtered in TeX injection blocks."""
        markdown_content = """
{{tex:
% This comment should be filtered
\\textbf{Bold Text} % Another comment
% \\dangerouscommand{should not appear}
\\textit{Italic Text}
}}
"""

        # Process the custom commands
        result = process_custom_commands(markdown_content)

        # Should preserve LaTeX commands
        assert "\\textbf{Bold Text}" in result
        assert "\\textit{Italic Text}" in result

        # Should filter out comments
        assert "% This comment should be filtered" not in result
        assert "% Another comment" not in result
        assert "dangerouscommand" not in result

    def test_mixed_comment_types_in_same_document(self):
        """Test handling of all three comment types in the same document."""
        markdown_content = """
# Test Document

Regular content.

<!-- HTML comment with table:
| Should | Not | Appear |
|--------|-----|--------|
| Row    | @bad_cite | Data |
-->

{{py:exec
# Python comment: should not execute
import random
# seed = 12345  # This should not set seed
random.seed(42)
value = random.randint(1, 100)
}}

Result: {{py:get value}}

{{tex:
% LaTeX comment: should be filtered
\\textbf{Bold} % Inline comment
% \\badcommand{dangerous}
\\textit{Italic}
}}

Final content.
"""

        # Process through the full pipeline
        result = convert_markdown_to_latex(markdown_content)

        # Should preserve good content
        assert "Test Document" in result
        assert "Regular content." in result
        assert "Final content." in result
        assert "\\textbf{Bold}" in result
        assert "\\textit{Italic}" in result

        # Should remove HTML commented content
        assert "Should" not in result or "Should" in "Test Document"  # Avoid false positive
        assert "@bad_cite" not in result

        # Should execute Python (comments filtered)
        assert "Result:" in result
        # Should have deterministic result due to seed(42)

        # Should filter LaTeX comments
        assert "% LaTeX comment" not in result
        assert "badcommand" not in result

    def test_comment_security_edge_cases(self):
        """Test edge cases for comment security."""
        markdown_content = """
<!-- Tricky case: HTML comment with nested content
{{py:exec
import subprocess
subprocess.run(["rm", "-rf", "/"], check=True)
}}

And a table:
| Evil | Table | Here |
|------|-------|------|
| @dangerous | {{py:get malicious}} | Bad |

{{tex: \\evilcommand{destroy everything}}}
-->

This should remain: {{py:exec
result = "safe"
}}

Safe result: {{py:get result}}
"""

        result = convert_markdown_to_latex(markdown_content)

        # Should preserve safe content
        assert "This should remain:" in result
        assert "safe" in result

        # Should remove ALL dangerous commented content
        assert "subprocess" not in result
        assert "rm -rf" not in result
        assert "Evil" not in result
        assert "@dangerous" not in result
        assert "evilcommand" not in result
        assert "destroy everything" not in result

    def test_comment_system_preserves_functionality(self):
        """Test that comment filtering doesn't break normal functionality."""
        markdown_content = """
# Normal Document

This is regular markdown content.

{{py:exec
import math
pi_value = math.pi
squared = 2 ** 2
}}

Mathematical constants:
- Pi: {{py:get pi_value}}
- Two squared: {{py:get squared}}

{{tex: \\textbf{Bold text} and \\textit{italic text}}}

| Normal | Table | Works |
|--------|-------|-------|
| Row 1  | Data  | Here  |

Citations still work: @example2023

Final paragraph.
"""

        result = convert_markdown_to_latex(markdown_content)

        # Should preserve all normal functionality
        assert "Normal Document" in result
        assert "regular markdown content" in result
        assert "Mathematical constants" in result
        assert "3.14159" in result  # Pi value
        assert "4" in result  # 2^2 = 4
        assert "\\textbf{Bold text}" in result
        assert "\\textit{italic text}" in result
        assert "Normal" in result and "Table" in result  # Table processing
        assert "\\cite{example2023}" in result  # Citations
        assert "Final paragraph" in result

    def test_malformed_html_comments_handled_safely(self):
        """Test that malformed HTML comments don't break processing."""
        markdown_content = """
Regular content.

<!-- Unclosed comment with dangerous content
{{py:exec
dangerous_code = "should not execute"
}}

More content that might be affected.
"""

        # Should process without crashing
        result = convert_markdown_to_latex(markdown_content)

        # Should preserve safe content
        assert "Regular content." in result
        assert "More content that might be affected." in result

        # The malformed comment content should remain (as it's not properly closed)
        # This is acceptable behavior - perfect parsing is complex

    def test_nested_content_in_comments_filtered(self):
        """Test that complex nested content inside comments is filtered."""
        markdown_content = """
Before comment.

<!--
## Commented Section

This section contains:

- Lists with @malicious_citations
- Complex tables:

| Name | Code | Danger Level |
|------|------|--------------|
| Test | {{py:exec malicious=True}} | {{py:get malicious}} |

### Subsection

More dangerous content: {{tex: \\input{/etc/passwd}}}

And some math: $E = mc^2$
-->

After comment.
"""

        result = convert_markdown_to_latex(markdown_content)

        # Should only have safe content
        assert "Before comment." in result
        assert "After comment." in result

        # Should remove all nested dangerous content
        assert "Commented Section" not in result
        assert "@malicious_citations" not in result
        assert "malicious=True" not in result
        assert "Danger Level" not in result
        assert "\\input{/etc/passwd}" not in result
        # Note: $E = mc^2$ might be tricky to test as it could appear elsewhere


class TestCommentSystemPerformance:
    """Test that comment filtering doesn't significantly impact performance."""

    def test_large_document_with_comments(self):
        """Test processing of large document with many comments."""
        # Create a moderately large document with various comment types
        sections = []
        for i in range(50):
            section = f"""
## Section {i}

Content for section {i}.

<!-- Comment {i} with table:
| Col1 | Col2 | Col3 |
|------|------|------|
| Data | @cite{i} | More |
-->

{{py:exec
# Comment in Python block {i}
section_num = {i}
}}

Section number: {{py:get section_num}}

{{tex: \\textbf{{Section {i}}} % Comment in LaTeX}}
"""
            sections.append(section)

        large_content = "\n".join(sections)

        # Should process without timeout or excessive memory usage
        result = convert_markdown_to_latex(large_content)

        # Should preserve good content
        assert "Section 0" in result
        assert "Section 49" in result

        # Should remove commented content (spot check)
        assert "@cite" not in result
        assert "Comment 25 with table" not in result


class TestCommentSystemRegression:
    """Test that comment system fixes don't break existing functionality."""

    def test_existing_markdown_features_still_work(self):
        """Test that standard markdown features continue to work."""
        markdown_content = """
# Main Title

## Subsection

**Bold text** and *italic text*.

- List item 1
- List item 2
  - Nested item

1. Numbered item
2. Another numbered item

`inline code` and:

```python
code_block = "should not be processed as command"
print(code_block)
```

[Link text](http://example.com)

![Figure caption](figure.png){#fig:example}

| Table | Headers |
|-------|---------|
| Data  | More    |

Mathematical formula: $E = mc^2$

> Block quote text

Final paragraph with @citation2023.
"""

        result = convert_markdown_to_latex(markdown_content)

        # Should process all standard markdown correctly
        assert "Main Title" in result
        assert "Subsection" in result
        assert "textbf{Bold text}" in result
        assert "textit{italic text}" in result
        assert "\\item List item 1" in result
        assert "\\item Numbered item" in result
        assert "texttt{inline code}" in result
        assert "begin{lstlisting}" in result or "begin{verbatim}" in result  # Code blocks
        assert "href{http://example.com}" in result
        assert "includegraphics" in result  # Figures
        assert "begin{table}" in result or "begin{tabular}" in result  # Tables
        assert "$E = mc^2$" in result  # Math
        assert "\\cite{citation2023}" in result  # Citations
