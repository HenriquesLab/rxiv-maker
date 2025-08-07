"""Integration tests for supplementary information formatting fixes.

These tests validate the fixes implemented for the technical audit:
1. Correct cross-reference resolution for supplementary notes
2. Sequential float numbering without duplicates
3. Absence of forced page breaks
4. Float barrier functionality
"""

import pytest

from rxiv_maker.converters.md2tex import convert_markdown_to_latex
from rxiv_maker.converters.supplementary_note_processor import (
    process_supplementary_note_references,
    process_supplementary_notes,
    restore_supplementary_note_placeholders,
)
from rxiv_maker.converters.table_processor import (
    convert_tables_to_latex,
    generate_latex_table,
)


class TestSupplementaryNoteReferences:
    """Test supplementary note cross-referencing functionality."""

    def test_supplementary_note_command_generation(self):
        """Test that supplementary notes generate proper LaTeX commands."""
        content = "{#snote:test-id} **Test Title**"

        # Process notes
        processed = process_supplementary_notes(content)
        restored = restore_supplementary_note_placeholders(processed)

        # Should use custom command that increments counter and includes numbering setup
        assert "\\suppnotesection{Test Title}" in restored
        assert "\\label{snote:test-id}" in restored
        assert "\\renewcommand{\\thesubsection}{Supp. Note \\arabic{subsection}}" in restored
        assert "\\subsection*{" not in restored  # Should not use starred subsection

    def test_supplementary_note_reference_conversion(self):
        """Test that supplementary note references are converted correctly."""
        content = "See @snote:test-id for details."

        processed = process_supplementary_note_references(content)

        assert "\\ref{snote:test-id}" in processed
        assert "@snote:test-id" not in processed

    def test_counter_setup_included_once(self):
        """Test that counter setup is only included for the first note."""
        content = "{#snote:first} **First Note**\n\nSome content\n\n{#snote:second} **Second Note**"

        processed = process_supplementary_notes(content)
        restored = restore_supplementary_note_placeholders(processed)

        # Counter setup should appear only once
        counter_setups = restored.count("\\renewcommand{\\thesubsection}")
        assert counter_setups == 1

        # Both notes should be present
        assert "\\suppnotesection{First Note}" in restored
        assert "\\suppnotesection{Second Note}" in restored


class TestSupplementaryFloatNumbering:
    """Test unified supplementary float environment numbering."""

    def test_table_environment_selection(self):
        """Test that correct table environments are selected."""
        from rxiv_maker.converters.table_processor import _determine_table_environment

        # Regular table
        env, pos = _determine_table_environment("single", None, False)
        assert env == "table"

        # Supplementary table
        env, pos = _determine_table_environment("single", None, True)
        assert env == "table"

        # Double-column supplementary table
        env, pos = _determine_table_environment("double", None, True)
        assert env == "table*"

        # Rotated supplementary table
        env, pos = _determine_table_environment("single", 90, True)
        assert env == "ssidewaystable"

    def test_no_table_counter_reset(self):
        """Test that supplementary table environments don't reset main counter."""
        # This test ensures the unified environments don't contain \setcounter{table}{0}
        # The actual LaTeX class definition should be checked manually, but we can
        # verify the Python code doesn't generate problematic LaTeX

        table_content = """
| Header 1 | Header 2 |
|----------|----------|
| Data 1   | Data 2   |

{#stable:test-table} **Test Table**
"""

        result = convert_tables_to_latex(table_content, is_supplementary=True)

        # Should not contain counter reset commands
        assert "\\setcounter{table}{0}" not in result
        # Should use standard table environment
        assert "\\begin{table}" in result


class TestFloatBarrierSupport:
    """Test float barrier directive functionality."""

    def test_float_barrier_conversion(self):
        """Test that <float-barrier> is converted to \\FloatBarrier."""
        content = "Some text before\n\n<float-barrier>\n\nSome text after"

        result = convert_markdown_to_latex(content)

        assert "\\FloatBarrier" in result
        assert "<float-barrier>" not in result

    def test_float_barrier_with_whitespace(self):
        """Test float barrier conversion with surrounding whitespace."""
        content = "  <float-barrier>  \n"

        result = convert_markdown_to_latex(content)

        assert "\\FloatBarrier" in result
        assert "<float-barrier>" not in result


class TestNoForcedPageBreaks:
    """Test absence of hardcoded page breaks."""

    def test_tables_no_auto_newpage(self):
        """Test that tables don't automatically add \\newpage."""
        table_content = """
| Header 1 | Header 2 |
|----------|----------|
| Data 1   | Data 2   |
"""

        result = convert_tables_to_latex(table_content, is_supplementary=True)

        # Should not contain automatic newpage after table
        lines = result.split("\n")
        table_end_indices = [i for i, line in enumerate(lines) if "\\end{" in line and "table" in line]

        for idx in table_end_indices:
            if idx + 1 < len(lines):
                next_line = lines[idx + 1].strip()
                assert next_line != "\\newpage", "Tables should not automatically add \\newpage"

    def test_supplementary_content_no_forced_breaks(self):
        """Test that supplementary content processing doesn't force page breaks."""
        content = """
# Supplementary Information

{#snote:test} **Test Note**

Some content here.

| Col1 | Col2 |
|------|------|
| A    | B    |

More content.
"""

        result = convert_markdown_to_latex(content, is_supplementary=True)

        # Count newpage commands - should only be explicit ones, not automatic
        newpage_count = result.count("\\newpage")

        # There should be no automatic newpage insertions
        # (any newpage commands should be from explicit <newpage> markers)
        assert "<newpage>" not in content  # Ensure test content has no explicit markers
        assert newpage_count == 0, "No automatic \\newpage should be inserted"


class TestTabularxForWideTable:
    """Test tabularx usage for wide tables instead of rotation."""

    def test_markdown_syntax_table_uses_tabularx(self):
        """Test that markdown syntax tables use tabularx instead of rotation."""
        # Simulate a markdown syntax overview table
        headers = ["Markdown Element", "LaTeX Equivalent", "Description"]
        data_rows = [
            ["`code`", "\\texttt{code}", "Inline code formatting"],
            ["**bold**", "\\textbf{bold}", "Bold text formatting"],
        ]

        result = generate_latex_table(
            headers=headers,
            data_rows=data_rows,
            caption="Markdown Syntax Overview",
            width="single",
            rotation_angle=90,  # Would normally cause rotation
            is_supplementary=True,
        )

        # For markdown syntax table, should use tabularx instead of rotation
        if "markdown element" in headers[0].lower():
            assert "\\begin{tabularx}" in result
            assert "\\rotatebox" not in result
            assert "\\small" in result  # Should use smaller font


class TestIntegrationScenario:
    """End-to-end integration test scenario."""

    def test_complete_supplementary_document(self):
        """Test processing a complete supplementary document."""
        content = """
# Supplementary Information

{#snote:methods} **Additional Methods**

Details about the experimental setup are provided here.
See @snote:analysis for analysis details.

| Parameter | Value | Description |
|-----------|-------|-------------|
| Temperature | 25°C | Room temperature |
| pH | 7.4 | Physiological pH |

<float-barrier>

{#snote:analysis} **Statistical Analysis**

The analysis was performed using standard methods.

**Markdown Element** | **LaTeX Equivalent** | **Description**
`*italic*` | `\\textit{italic}` | Italic text formatting
`**bold**` | `\\textbf{bold}` | Bold text formatting

{#stable:syntax-table rotate=90} **Markdown Syntax Overview**
"""

        result = convert_markdown_to_latex(content, is_supplementary=True)

        # Check supplementary note processing
        assert "\\suppnotesection{Additional Methods}" in result
        assert "\\suppnotesection{Statistical Analysis}" in result
        assert "\\ref{snote:analysis}" in result

        # Check float barrier
        assert "\\FloatBarrier" in result

        # Check no automatic newpage
        forced_newpages = result.count("\\newpage")
        assert forced_newpages == 0, "Should not contain forced page breaks"

        # Check table environments
        assert "\\begin{table}" in result or "\\begin{ssidewaystable}" in result

        # Should not contain problematic patterns
        assert "\\subsection*{" not in result  # Should use \\suppnotesection instead
        assert "\\setcounter{table}{0}" not in result  # Should not reset counter


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
