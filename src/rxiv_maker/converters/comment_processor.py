"""Comment processing for markdown to LaTeX conversion.

This module handles removal of all types of comments from markdown content
BEFORE any other processing occurs. This is critical for security and correctness
as comments should never be processed as active content.

Supported comment types:
- HTML/Markdown comments: <!-- content -->
- Python comments: # comment (within {{py:exec}} blocks)
- LaTeX comments: % comment (within {{tex:...}} blocks)
"""

from .types import MarkdownContent


def remove_html_comments(text: MarkdownContent) -> MarkdownContent:
    """Remove HTML/Markdown comments entirely from text.

    This function completely removes HTML comments and their content,
    preventing any processing of commented-out tables, citations,
    executable blocks, or other markdown elements.

    Args:
        text: Text containing HTML comments to remove

    Returns:
        Text with all HTML comments and their content completely removed
    """
    # Remove HTML comments entirely (not convert to LaTeX comments)
    # This must happen BEFORE any other processing to prevent
    # tables, citations, executable blocks, etc. inside comments from being processed

    # Use a more robust approach that handles nested comments better
    result = []
    i = 0
    while i < len(text):
        # Look for <!--
        if text[i : i + 4] == "<!--":
            # Find the closing -->
            j = i + 4
            while j < len(text) - 2:
                if text[j : j + 3] == "-->":
                    # Found closing, skip the entire comment
                    i = j + 3
                    break
                j += 1
            else:
                # No closing found, keep the malformed comment
                result.append(text[i])
                i += 1
        else:
            result.append(text[i])
            i += 1

    return "".join(result)


def filter_python_comments(code: str) -> str:
    """Filter Python comments from code within {{py:exec}} blocks.

    Removes both full-line comments and inline comments while preserving
    line numbers for accurate error reporting.

    Args:
        code: Python code that may contain comments

    Returns:
        Python code with comments filtered out
    """
    lines = code.split("\n")
    filtered_lines = []

    for line in lines:
        # Handle inline comments - everything after # is a comment
        # But we need to be careful about # inside strings
        comment_pos = _find_comment_start(line)

        if comment_pos == 0:
            # Entire line is a comment, replace with empty line to preserve line numbers
            filtered_lines.append("")
        elif comment_pos > 0:
            # Inline comment, keep code before #
            filtered_lines.append(line[:comment_pos].rstrip())
        else:
            # No comment found, keep entire line
            filtered_lines.append(line)

    return "\n".join(filtered_lines)


def filter_latex_comments(code: str) -> str:
    """Filter LaTeX comments from code within {{tex:...}} blocks.

    Removes both full-line comments and inline comments while preserving
    the structure for proper LaTeX processing.

    Args:
        code: LaTeX code that may contain comments

    Returns:
        LaTeX code with comments filtered out
    """
    lines = code.split("\n")
    filtered_lines = []

    for line in lines:
        # In LaTeX, everything after % is a comment (unless % is escaped as \%)
        comment_pos = _find_latex_comment_start(line)

        if comment_pos == 0:
            # Entire line is a comment, replace with empty line
            filtered_lines.append("")
        elif comment_pos > 0:
            # Inline comment, keep content before %
            filtered_lines.append(line[:comment_pos].rstrip())
        else:
            # No comment found, keep entire line
            filtered_lines.append(line)

    return "\n".join(filtered_lines)


def _find_comment_start(line: str) -> int:
    """Find the position where a Python comment starts.

    Handles # inside strings correctly by parsing string literals.
    Note: This function handles single-line cases. Multiline strings
    should be handled at a higher level.

    Args:
        line: Line of Python code

    Returns:
        Position of # comment start, -1 if no comment, 0 if entire line is comment
    """
    # Skip lines that are entirely whitespace
    if not line.strip():
        return -1

    # Check if line starts with # (full line comment)
    if line.lstrip().startswith("#"):
        return 0

    # Look for # outside of strings
    in_single_quote = False
    in_double_quote = False
    in_triple_single = False
    in_triple_double = False
    escaped = False
    i = 0

    while i < len(line):
        char = line[i]

        if escaped:
            escaped = False
            i += 1
            continue

        if char == "\\":
            escaped = True
            i += 1
            continue

        # Check for triple quotes first
        if i <= len(line) - 3:
            if line[i : i + 3] == "'''" and not in_double_quote and not in_triple_double:
                in_triple_single = not in_triple_single
                i += 3
                continue
            elif line[i : i + 3] == '"""' and not in_single_quote and not in_triple_single:
                in_triple_double = not in_triple_double
                i += 3
                continue

        # If we're in a triple-quoted string, skip everything except looking for the closing triple quote
        if in_triple_single or in_triple_double:
            i += 1
            continue

        # Handle single/double quotes
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif char == "#" and not in_single_quote and not in_double_quote:
            return i

        i += 1

    return -1


def _find_latex_comment_start(line: str) -> int:
    r"""Find the position where a LaTeX comment starts.

    Handles escaped % (\\%) correctly.

    Args:
        line: Line of LaTeX code

    Returns:
        Position of % comment start, -1 if no comment, 0 if entire line is comment
    """
    # Skip lines that are entirely whitespace
    if not line.strip():
        return -1

    # Check if line starts with % (full line comment)
    if line.lstrip().startswith("%"):
        return 0

    # Look for unescaped %
    i = 0
    while i < len(line):
        if line[i] == "%":
            # Check if it's escaped (preceded by odd number of backslashes)
            backslash_count = 0
            j = i - 1
            while j >= 0 and line[j] == "\\":
                backslash_count += 1
                j -= 1

            # If even number of backslashes (including 0), % is not escaped
            if backslash_count % 2 == 0:
                return i
        i += 1

    return -1


def preprocess_comments(text: MarkdownContent) -> MarkdownContent:
    """Remove all HTML comments from markdown content as first preprocessing step.

    This function should be called at the very beginning of the conversion pipeline
    to ensure that no commented content gets processed by any subsequent processors.

    Args:
        text: Raw markdown content that may contain HTML comments

    Returns:
        Markdown content with all HTML comments completely removed
    """
    # Remove HTML comments first and foremost
    text = remove_html_comments(text)

    # Note: Python and LaTeX comment filtering happens within their respective
    # processors (python_executor.py and custom_command_processor.py) since
    # they need to process the executable blocks first before filtering comments
    # within those blocks.

    return text
