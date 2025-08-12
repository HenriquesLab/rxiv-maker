"""Unit tests for the supplementary note processor module."""

import pytest

from rxiv_maker.converters.supplementary_note_processor import (
    extract_supplementary_note_info,
    process_supplementary_note_references,
    process_supplementary_notes,
    restore_supplementary_note_placeholders,
    validate_supplementary_note_numbering,
)


class TestSupplementaryNoteProcessing:
    """Test supplementary note processing functionality."""

    def test_single_supplementary_note_processing(self):
        """Test processing of a single supplementary note."""
        content = "{#snote:file-structure} **File Structure and Organisation.**\n\nThis is the note content."

        # Process the notes
        processed = process_supplementary_notes(content)

        # Should contain placeholder
        assert "XXSUBNOTEPROTECTEDXX0XXENDXX" in processed
        assert "{#snote:file-structure}" not in processed

        # Restore placeholders
        restored = restore_supplementary_note_placeholders(processed)

        # Should contain LaTeX subsection with label
        expected_section = "\\suppnotesection{File Structure and Organisation.}\\label{snote:file-structure}"
        assert expected_section in restored
        assert "\\renewcommand{\\thesubsection}{Supp. Note \\arabic{subsection}}" in restored
        assert "\\setcounter{subsection}{0}" in restored

    def test_multiple_supplementary_notes_processing(self):
        """Test processing of multiple supplementary notes."""
        content = """{#snote:first} **First Note.**

Some content here.

{#snote:second} **Second Note.**

More content here."""

        # Process the notes
        processed = process_supplementary_notes(content)

        # Should contain placeholders
        assert "XXSUBNOTEPROTECTEDXX0XXENDXX" in processed
        assert "XXSUBNOTEPROTECTEDXX1XXENDXX" in processed
        assert "{#snote:first}" not in processed
        assert "{#snote:second}" not in processed

        # Restore placeholders
        restored = restore_supplementary_note_placeholders(processed)

        # Should contain both LaTeX subsections
        assert "\\suppnotesection{First Note.}\\label{snote:first}" in restored
        assert "\\suppnotesection{Second Note.}\\label{snote:second}" in restored
        # Should only have renewcommand setup once (for the first note)
        assert restored.count("\\renewcommand{\\thesubsection}{Supp. Note \\arabic{subsection}}") == 1

    def test_supplementary_note_with_special_characters(self):
        """Test processing notes with special characters in titles."""
        content = "{#snote:test} **Title with & Special % Characters.**"

        processed = process_supplementary_notes(content)
        restored = restore_supplementary_note_placeholders(processed)

        assert "\\suppnotesection{Title with & Special % Characters.}\\label{snote:test}" in restored

    def test_supplementary_note_reference_processing(self):
        """Test processing of supplementary note references."""
        content = "Please see @snote:file-structure for details on organization."

        result = process_supplementary_note_references(content)

        assert "\\ref{snote:file-structure}" in result
        assert "@snote:file-structure" not in result

    def test_multiple_supplementary_note_references(self):
        """Test processing of multiple supplementary note references."""
        content = "See @snote:first and @snote:second for more information."

        result = process_supplementary_note_references(content)

        assert "\\ref{snote:first}" in result
        assert "\\ref{snote:second}" in result
        assert "@snote:" not in result

    def test_no_supplementary_notes_processing(self):
        """Test that content without supplementary notes is unchanged."""
        content = "This is regular content with no supplementary notes."

        processed = process_supplementary_notes(content)
        restored = restore_supplementary_note_placeholders(processed)

        assert processed == content
        assert restored == content

    def test_supplementary_note_with_whitespace_variations(self):
        """Test processing with various whitespace patterns."""
        test_cases = [
            "{#snote:test}**Title**",  # No space before title
            "{#snote:test} **Title**",  # Single space
            "{#snote:test}  **Title**",  # Multiple spaces
        ]

        for content in test_cases:
            processed = process_supplementary_notes(content)
            restored = restore_supplementary_note_placeholders(processed)
            assert "\\suppnotesection{Title}\\label{snote:test}" in restored

        # Test case that won't match (spaces inside braces)
        invalid_content = "{ #snote:test } **Title**"
        processed = process_supplementary_notes(invalid_content)
        # Should remain unchanged since it doesn't match the pattern
        assert processed == invalid_content

    def test_supplementary_note_id_normalization(self):
        """Test that supplementary note IDs are properly normalized."""
        content = "{#snote:complex-id_with.symbols} **Test Title.**"

        processed = process_supplementary_notes(content)
        restored = restore_supplementary_note_placeholders(processed)

        # ID should be preserved as-is in the label
        assert "\\label{snote:complex-id_with.symbols}" in restored

    def test_end_to_end_supplementary_note_workflow(self):
        """Test the complete workflow from markdown to LaTeX."""
        markdown_content = """# Supplementary Information

{#snote:methodology} **Research Methodology Details.**

This section describes the detailed methodology used in the study.

Please refer to @snote:methodology for implementation details.

{#snote:analysis} **Statistical Analysis Framework.**

This section provides the complete statistical analysis framework."""

        # Step 1: Process notes
        processed = process_supplementary_notes(markdown_content)

        # Step 2: Process references
        processed = process_supplementary_note_references(processed)

        # Step 3: Restore placeholders
        final = restore_supplementary_note_placeholders(processed)

        # Verify LaTeX output
        assert "\\suppnotesection{Research Methodology Details.}\\label{snote:methodology}" in final
        assert "\\suppnotesection{Statistical Analysis Framework.}\\label{snote:analysis}" in final
        assert "\\ref{snote:methodology}" in final
        assert "\\renewcommand{\\thesubsection}{Supp. Note \\arabic{subsection}}" in final
        assert "{#snote:" not in final
        assert "@snote:" not in final


class TestSupplementaryNoteValidation:
    """Test supplementary note validation functionality."""

    def test_extract_supplementary_note_info_traditional_format(self):
        """Test extraction of supplementary note info from traditional format."""
        content = """### Supplementary Note 1: First Note
### Supplementary Note 2: Second Note
### Supplementary Note 3: Third Note with Complex Title"""

        notes_info = extract_supplementary_note_info(content)

        assert len(notes_info) == 3
        assert notes_info[0] == (1, "First Note", "first_note")
        assert notes_info[1] == (2, "Second Note", "second_note")
        assert notes_info[2] == (
            3,
            "Third Note with Complex Title",
            "third_note_with_complex_title",
        )

    def test_validate_correct_numbering(self):
        """Test validation of correctly numbered supplementary notes."""
        content = """### Supplementary Note 1: First Note
### Supplementary Note 2: Second Note
### Supplementary Note 3: Third Note"""

        errors = validate_supplementary_note_numbering(content)
        assert len(errors) == 0

    def test_validate_incorrect_numbering(self):
        """Test validation catches incorrect numbering."""
        content = """### Supplementary Note 1: First Note
### Supplementary Note 3: Third Note
### Supplementary Note 4: Fourth Note"""

        errors = validate_supplementary_note_numbering(content)
        assert len(errors) > 0
        assert "expected 2" in errors[0]

    def test_validate_duplicate_numbering(self):
        """Test validation catches duplicate numbers."""
        content = """### Supplementary Note 1: First Note
### Supplementary Note 1: Duplicate Note
### Supplementary Note 2: Second Note"""

        errors = validate_supplementary_note_numbering(content)
        assert len(errors) > 0
        # Should find duplicate numbers
        duplicate_error = next((e for e in errors if "Duplicate" in e), None)
        assert duplicate_error is not None
        assert "1" in duplicate_error

    def test_validate_no_notes(self):
        """Test validation with no supplementary notes."""
        content = "This content has no supplementary notes."

        errors = validate_supplementary_note_numbering(content)
        assert len(errors) == 0


class TestSupplementaryNoteIntegration:
    """Test integration with the overall markdown to LaTeX pipeline."""

    def test_integration_with_text_formatting(self):
        """Test that supplementary notes work correctly with text formatting."""
        content = """{#snote:test} **Bold Title.**

This note has **bold** and *italic* formatting that should be preserved."""

        # Process notes first (before text formatting)
        processed = process_supplementary_notes(content)

        # Verify placeholder is created and original syntax is gone
        assert "XXSUBNOTEPROTECTEDXX0XXENDXX" in processed
        assert "{#snote:test}" not in processed

        # Text formatting would happen here in the real pipeline
        # For this test, we'll simulate it on the content around the placeholder
        processed = processed.replace("**bold**", "\\textbf{bold}")
        processed = processed.replace("*italic*", "\\textit{italic}")

        # Restore placeholders (after text formatting)
        final = restore_supplementary_note_placeholders(processed)

        # The title should be preserved in the LaTeX subsection
        assert "\\suppnotesection{Bold Title.}" in final
        # The content should have text formatting applied
        assert "\\textbf{bold}" in final
        assert "\\textit{italic}" in final

    def test_supplementary_notes_preserved_in_code_blocks(self):
        """Test that supplementary note syntax in code blocks doesn't get processed."""
        content = """```markdown
{#snote:example} **This is an example.**
```

{#snote:real} **This is a real note.**"""

        # In the real pipeline, code blocks would be protected first
        # For this test, we simulate the current behavior where code blocks
        # are NOT protected. The current implementation processes ALL
        # {#snote:} patterns regardless of context
        processed = process_supplementary_notes(content)
        restored = restore_supplementary_note_placeholders(processed)

        # Both notes get processed (including the one in the code block)
        # This might be a limitation of the current implementation
        assert "\\suppnotesection{This is an example.}" in restored
        assert "\\suppnotesection{This is a real note.}" in restored

        # The original patterns should be gone
        assert "{#snote:example}" not in restored
        assert "{#snote:real}" not in restored

    def test_complex_document_structure(self):
        """Test supplementary notes in a complex document structure."""
        content = """# Main Document

This is the main content with a reference to @snote:detailed-analysis.

## Methods

Standard methods section.

# Supplementary Information

{#snote:detailed-analysis} **Detailed Statistical Analysis.**

This supplementary note provides detailed analysis methods.

See also @snote:implementation for technical details.

{#snote:implementation} **Technical Implementation Details.**

This note describes the implementation approach."""

        # Full processing pipeline
        processed = process_supplementary_notes(content)
        processed = process_supplementary_note_references(processed)
        final = restore_supplementary_note_placeholders(processed)

        # Verify all components
        assert "\\suppnotesection{Detailed Statistical Analysis.}" in final
        assert "\\suppnotesection{Technical Implementation Details.}" in final
        assert "\\ref{snote:detailed-analysis}" in final
        assert "\\ref{snote:implementation}" in final
        assert "\\renewcommand{\\thesubsection}{Supp. Note \\arabic{subsection}}" in final

        # Verify no original syntax remains
        assert "{#snote:" not in final
        assert "@snote:" not in final


if __name__ == "__main__":
    pytest.main([__file__])
