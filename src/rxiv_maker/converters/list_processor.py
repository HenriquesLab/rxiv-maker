"""List processing for markdown to LaTeX conversion.

This module handles conversion of markdown lists (both ordered and unordered)
to LaTeX list environments (itemize and enumerate).
"""

import re

from .types import LatexContent, MarkdownContent


def convert_lists_to_latex(text: MarkdownContent) -> LatexContent:
    """Convert markdown lists to LaTeX list environments.

    Args:
        text: Text containing markdown lists

    Returns:
        Text with lists converted to LaTeX environments
    """
    lines = text.split("\n")
    result_lines: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for unordered list (- or * at start of line)
        if re.match(r"^\s*[-*]\s+", line):
            i = _process_unordered_list(lines, i, result_lines)
        # Check for ordered list (number followed by . or ))
        elif re.match(r"^\s*\d+[.)]\s+", line):
            i = _process_ordered_list(lines, i, result_lines)
        else:
            # Regular line, not a list
            result_lines.append(line)
            i += 1

    return "\n".join(result_lines)


def _process_unordered_list(lines: list[str], start_index: int, result_lines: list[str]) -> int:
    """Process an unordered list starting at the given index.

    Args:
        lines: All lines of text
        start_index: Index where the list starts
        result_lines: List to append results to

    Returns:
        Index of the next line to process
    """
    list_lines: list[str] = []
    indent_level = len(lines[start_index]) - len(lines[start_index].lstrip())
    i = start_index

    # Collect all consecutive list items at the same indent level
    while i < len(lines):
        current_line = lines[i]
        if re.match(rf"^\s{{0,{indent_level + 2}}}[-*]\s+", current_line):
            # Extract the list item content (remove the bullet)
            item_content = re.sub(r"^\s*[-*]\s+", "", current_line)
            list_lines.append(f"  \\item {item_content}")
            i += 1
        elif current_line.strip() == "":
            # Empty line, might continue list
            i += 1
            if i < len(lines) and re.match(rf"^\s{{0,{indent_level + 2}}}[-*]\s+", lines[i]):
                continue
            else:
                break
        else:
            # Not a list item, end of list
            break

    # Add the complete itemize environment
    result_lines.append("\\begin{itemize}")
    result_lines.extend(list_lines)
    result_lines.append("\\end{itemize}")

    return i


def _process_ordered_list(lines: list[str], start_index: int, result_lines: list[str]) -> int:
    """Process an ordered list starting at the given index.

    Args:
        lines: All lines of text
        start_index: Index where the list starts
        result_lines: List to append results to

    Returns:
        Index of the next line to process
    """
    list_lines: list[str] = []
    indent_level = len(lines[start_index]) - len(lines[start_index].lstrip())
    i = start_index

    # Collect all consecutive list items at the same indent level
    while i < len(lines):
        current_line = lines[i]
        if re.match(rf"^\s{{0,{indent_level + 2}}}\d+[.)]\s+", current_line):
            # Extract the list item content (remove the number)
            item_content = re.sub(r"^\s*\d+[.)]\s+", "", current_line)
            list_lines.append(f"  \\item {item_content}")
            i += 1
        elif current_line.strip() == "":
            # Empty line, might continue list
            i += 1
            if i < len(lines) and re.match(rf"^\s{{0,{indent_level + 2}}}\d+[.)]\s+", lines[i]):
                continue
            else:
                break
        else:
            # Not a list item, end of list
            break

    # Add the complete enumerate environment
    result_lines.append("\\begin{enumerate}")
    result_lines.extend(list_lines)
    result_lines.append("\\end{enumerate}")

    return i


def extract_list_items_from_text(text: MarkdownContent) -> tuple[list[str], list[str]]:
    """Extract all list items from markdown text.

    Args:
        text: Text to extract list items from

    Returns:
        Tuple of (unordered_items, ordered_items)
    """
    unordered_items: list[str] = []
    ordered_items: list[str] = []

    lines = text.split("\n")

    for line in lines:
        # Check for unordered list items
        unordered_match = re.match(r"^\s*[-*]\s+(.+)$", line)
        if unordered_match:
            unordered_items.append(unordered_match.group(1).strip())

        # Check for ordered list items
        ordered_match = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if ordered_match:
            ordered_items.append(ordered_match.group(1).strip())

    return unordered_items, ordered_items


def validate_list_structure(text: MarkdownContent) -> bool:
    """Validate that list structure is properly formatted.

    Args:
        text: Text containing lists to validate

    Returns:
        True if list structure is valid, False otherwise
    """
    lines = text.split("\n")

    for _i, line in enumerate(lines):
        # Check for proper list item formatting
        if re.match(r"^\s*[-*]\s", line):
            # Unordered list item should have content after marker
            if not re.match(r"^\s*[-*]\s+.+", line):
                return False
        elif re.match(r"^\s*\d+[.)]\s", line) and not re.match(r"^\s*\d+[.)]\s+.+", line):
            # Ordered list item should have content after marker
            return False

    return True


def normalize_list_markers(text: MarkdownContent) -> MarkdownContent:
    """Normalize list markers to consistent format.

    Args:
        text: Text with potentially inconsistent list markers

    Returns:
        Text with normalized list markers
    """
    lines = text.split("\n")
    result_lines: list[str] = []

    for line in lines:
        # Normalize unordered list markers to use dashes
        if re.match(r"^\s*\*\s+", line):
            normalized = re.sub(r"^(\s*)\*(\s+)", r"\1-\2", line)
            result_lines.append(normalized)
        # Normalize ordered list markers to use periods
        elif re.match(r"^\s*\d+\)\s+", line):
            normalized = re.sub(r"^(\s*\d+)\)(\s+)", r"\1.\2", line)
            result_lines.append(normalized)
        else:
            result_lines.append(line)

    return "\n".join(result_lines)
