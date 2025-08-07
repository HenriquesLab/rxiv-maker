"""Supplementary note processing for markdown to LaTeX conversion.

This module handles the conversion of supplementary note headers and creates
a reference system for citing supplementary notes from the main text.
"""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from .types import LatexContent, MarkdownContent


def process_supplementary_notes(content: LatexContent) -> LatexContent:
    """Process supplementary note headers and create reference labels.

    Converts {#snote:id} **Title** format to LaTeX format with automatic
    "Supplementary Note X:" numbering and reference labels. Processes all snote
    patterns throughout the document.

    Args:
        content: The markdown content to process (before LaTeX conversion)

    Returns:
        Processed content with supplementary notes formatted, protected from
        text formatting
    """
    # Handle markdown format {#snote:id} **Title**
    # This runs before text formatting, so we expect markdown format
    pattern = r"\{#snote:([^}]+)\}\s*\*\*([^*]+)\*\*"

    # Find all matches first and store them
    matches = re.findall(pattern, content, flags=re.MULTILINE)

    if not matches:
        return content

    # Create protected replacements that won't be affected by text formatting
    # Use placeholders that completely isolate the LaTeX commands
    replacements = {}
    first_note_processed = False

    for i, (snote_id, title) in enumerate(matches):
        snote_id = snote_id.strip()
        title = title.strip()

        # Use the provided snote_id as the reference label
        ref_label = f"snote:{snote_id}"

        # For the first note, add the renewcommand before the subsection
        prefix = ""
        if not first_note_processed:
            prefix = (
                "% Setup subsection numbering for supplementary notes\n"
                "\\renewcommand{\\thesubsection}{Supp. Note \\arabic{subsection}}\n"
                "\\setcounter{subsection}{0}\n\n"
            )
            first_note_processed = True

        # Create the LaTeX subsection with proper counter increment
        # Use custom command to ensure counter is incremented for cross-references
        latex_replacement = f"{prefix}\\suppnotesection{{{title}}}\\label{{{ref_label}}}"

        # Create a unique placeholder that completely replaces the markdown pattern
        # This placeholder won't contain any asterisks or other markdown syntax
        placeholder = f"XXSUBNOTEPROTECTEDXX{i}XXENDXX"
        replacements[placeholder] = latex_replacement

    # Replace each match with its placeholder
    def replace_with_placeholder(match):
        # Find which match this is
        snote_id = match.group(1).strip()
        title = match.group(2).strip()

        for i, (stored_id, stored_title) in enumerate(matches):
            if stored_id.strip() == snote_id and stored_title.strip() == title:
                return f"XXSUBNOTEPROTECTEDXX{i}XXENDXX"

        # Fallback (shouldn't happen)
        return match.group(0)

    # Replace patterns with placeholders
    processed_content = re.sub(pattern, replace_with_placeholder, content, flags=re.MULTILINE)

    # Store the replacements for later restoration after text formatting
    # We use a global variable since strings don't have attributes
    global _snote_replacements
    _snote_replacements = replacements

    return processed_content


# Global variable to store replacements
_snote_replacements: dict[str, str] = {}


def restore_supplementary_note_placeholders(content: LatexContent) -> LatexContent:
    """Restore supplementary note placeholders after text formatting.

    This should be called after all text formatting is complete.

    Args:
        content: Content with supplementary note placeholders

    Returns:
        Content with placeholders replaced by LaTeX commands
    """
    global _snote_replacements

    # Replace placeholders with final LaTeX
    for placeholder, latex_replacement in _snote_replacements.items():
        content = content.replace(placeholder, latex_replacement)

    # Clear the replacements after use
    _snote_replacements = {}

    return content


def process_supplementary_note_references(content: LatexContent) -> LatexContent:
    r"""Process supplementary note references in the content.

    Converts references like @snote:title to LaTeX Supplementary Note \\ref{}.

    Args:
        content: The LaTeX content to process

    Returns:
        Processed content with supplementary note references converted with prefix
    """
    # Pattern to match supplementary note references
    # Matches: @snote:label
    pattern = r"@snote:([a-zA-Z0-9_-]+)"

    def replace_reference(match):
        label = match.group(1)
        return f"\\ref{{snote:{label}}}"

    # Replace supplementary note references
    content = re.sub(pattern, replace_reference, content)

    return content


def extract_supplementary_note_info(
    content: MarkdownContent,
) -> list[tuple[int, str, str]]:
    """Extract information about supplementary notes from markdown content.

    Args:
        content: The markdown content to analyze

    Returns:
        List of tuples containing (note_number, title, reference_label)
    """
    pattern = r"^### Supplementary Note (\d+):?\s*(.+)$"
    notes_info = []

    for match in re.finditer(pattern, content, re.MULTILINE):
        note_num = int(match.group(1))
        title = match.group(2).strip()

        # Create reference label
        label = re.sub(r"[^\w\s-]", "", title.lower())
        label = re.sub(r"[-\s]+", "_", label).strip("_")

        notes_info.append((note_num, title, label))

    return notes_info


def validate_supplementary_note_numbering(content: MarkdownContent) -> list[str]:
    """Validate that supplementary notes are numbered correctly.

    Args:
        content: The markdown content to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    notes_info = extract_supplementary_note_info(content)
    errors: list[str] = []

    if not notes_info:
        return errors

    # Check for sequential numbering starting from 1
    expected_num = 1
    for note_num, _title, _ in sorted(notes_info, key=lambda x: x[0]):
        if note_num != expected_num:
            errors.append(f"Supplementary Note {note_num} found, expected {expected_num}")
        expected_num += 1

    # Check for duplicate numbers
    numbers = [num for num, _, _ in notes_info]
    duplicates = {num for num in numbers if numbers.count(num) > 1}
    if duplicates:
        errors.append(f"Duplicate supplementary note numbers: {sorted(duplicates)}")

    return errors
