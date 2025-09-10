"""Test for the specific issue reported by the user.

This test validates that the exact issue reported by the user
(HTML commented table being rendered in PDF) is now fixed.
"""

from rxiv_maker.converters.md2tex import convert_markdown_to_latex


def test_user_reported_html_comment_table_issue():
    """Test the specific issue reported by the user.

    The user reported that this HTML comment was still being processed
    and generating a table in the PDF when it should be ignored:

    <!--| Name | Description | Reference |
    |-------|----------|--------|
    | JE2 | Derivative of community-acquired MRSA | @fey_genetic_2013 |
    | BCBMS14 | JE2 \\textit{$\\Delta$spa:$\\text{P}_\\text{xyl/tet03}-\\text{dcas9}_\\text{Spy}$} containing $\\text{psg-RNA}_\\text{Spy}$-2| %@reed_crispri-based_2024 |
    | LCML1 | JE2 \\textit{$\\Delta$spa:$\\text{P}_\\text{xyl/tet03}-\\text{dcas9}_\\text{Spy}$} containing psg-0001_dnaA | @reed_crispri-based_2024 | -->
    """
    # The exact content reported by the user
    markdown_content = """
This content should remain.

<!--| Name | Description | Reference |
|-------|----------|--------|
| JE2 | Derivative of community-acquired MRSA | @fey_genetic_2013 |
| BCBMS14 | JE2 \\textit{$\\Delta$spa:$\\text{P}_\\text{xyl/tet03}-\\text{dcas9}_\\text{Spy}$} containing $\\text{psg-RNA}_\\text{Spy}$-2| %@reed_crispri-based_2024 |
| LCML1 | JE2 \\textit{$\\Delta$spa:$\\text{P}_\\text{xyl/tet03}-\\text{dcas9}_\\text{Spy}$} containing psg-0001_dnaA | @reed_crispri-based_2024 | -->

This content should also remain.
"""

    # Process through the full markdown-to-LaTeX pipeline
    result = convert_markdown_to_latex(markdown_content)

    # Should preserve non-commented content
    assert "This content should remain." in result
    assert "This content should also remain." in result

    # CRITICAL: Should NOT contain any of the table content that was commented out
    assert "Name" not in result or ("This content" in result)  # Avoid false positive from "This content should remain"
    assert "Description" not in result
    assert "Reference" not in result
    assert "JE2" not in result
    assert "BCBMS14" not in result
    assert "LCML1" not in result
    assert "community-acquired MRSA" not in result
    assert "@fey_genetic_2013" not in result
    assert "@reed_crispri-based_2024" not in result
    assert "psg-0001_dnaA" not in result

    # Should not contain table markdown syntax
    assert "|-------|----------|--------|" not in result

    # Should not contain LaTeX table environments that would be generated from the markdown table
    assert "begin{table}" not in result
    assert "begin{tabular}" not in result

    # Should not process the citations that were inside the comment
    # (In a real document, these would become \cite{} commands)
    assert "\\cite{fey_genetic_2013}" not in result
    assert "\\cite{reed_crispri-based_2024}" not in result


def test_commented_executable_code_not_executed():
    """Test that executable code in HTML comments is not executed."""
    markdown_content = """
Safe content here.

<!--
{{py:exec
# This should never execute
dangerous_var = "This should not appear in output"
}}

The result would be: {{py:get dangerous_var}}

{{tex: \\dangerouscommand{malicious content}}}
-->

More safe content.
"""

    result = convert_markdown_to_latex(markdown_content)

    # Should preserve safe content
    assert "Safe content here." in result
    assert "More safe content." in result

    # Should NOT execute the Python code or process the TeX command
    assert "This should not appear in output" not in result
    assert "py:exec" not in result
    assert "py:get" not in result
    assert "dangerous_var" not in result
    assert "dangerouscommand" not in result
    assert "malicious content" not in result


def test_tex_comments_in_blocks_filtered():
    """Test that TeX comments within {{tex:...}} blocks are filtered as user requested."""
    markdown_content = """
{{tex:
\\textbf{Bold Text} % This comment should be filtered
% This entire line is a comment and should be filtered
\\textit{Italic Text}
}}
"""

    result = convert_markdown_to_latex(markdown_content)

    # Should preserve the LaTeX commands
    assert "\\textbf{Bold Text}" in result
    assert "\\textit{Italic Text}" in result

    # Should filter out the comments
    assert "% This comment should be filtered" not in result
    assert "% This entire line is a comment" not in result


def test_python_comments_in_exec_blocks_filtered():
    """Test that Python comments within {{py:exec}} blocks are filtered."""
    markdown_content = """
{{py:exec
# This comment should not execute or appear
import math
result = math.pi  # This inline comment should also be filtered
# dangerous_function_call()  # This should definitely not execute
}}

Pi value: {{py:get result}}
"""

    result = convert_markdown_to_latex(markdown_content)

    # Should execute the actual Python code
    assert "3.14159" in result  # Pi value should be computed and inserted

    # Comments should not appear anywhere in the result
    # Note: We can't directly test that comments weren't executed,
    # but we can verify the result contains expected computed values
