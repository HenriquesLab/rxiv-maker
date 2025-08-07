"""Table processing for markdown to LaTeX conversion.

This module handles conversion of markdown tables to LaTeX table environments,
including table formatting, rotation, and special syntax handling.
"""

import re

from .citation_processor import convert_citations_to_latex
from .types import (
    LatexContent,
    MarkdownContent,
    ProtectedContent,
    TableData,
    TableHeaders,
)


def convert_tables_to_latex(
    text: MarkdownContent,
    protected_backtick_content: ProtectedContent | None = None,
    is_supplementary: bool = False,
) -> LatexContent:
    r"""Convert markdown tables to LaTeX table environments.

    Args:
        text: The text containing markdown tables
        protected_backtick_content: Dict of protected backtick content
        is_supplementary: If True, enables supplementary content processing

    Returns:
        Text with tables converted to LaTeX format
    """
    if protected_backtick_content is None:
        protected_backtick_content = {}

    lines = text.split("\n")
    result_lines: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for table caption before the table
        table_caption = None
        table_width = "single"  # default to single column

        # Look for a caption line before the table (allowing for blank line between)
        # (format: "Table 1: Caption text", "Table* 1: Caption text", etc.)
        caption_line_index = None
        if i > 0:
            # Check line immediately before
            if re.match(r"^Table\*?\s+\d+[\s:.]\s*", lines[i - 1].strip(), re.IGNORECASE):
                caption_line_index = i - 1
            # Check line two positions back (in case of blank line)
            elif (
                i > 1
                and lines[i - 1].strip() == ""
                and re.match(r"^Table\*?\s+\d+[\s:.]\s*", lines[i - 2].strip(), re.IGNORECASE)
            ):
                caption_line_index = i - 2

        if caption_line_index is not None:
            caption_line = lines[caption_line_index].strip()
            # Check if it's a two-column table (Table* format)
            if caption_line.lower().startswith("table*"):
                table_width = "double"
            # Extract caption text after "Table X:" or "Table* X:" etc.
            caption_match = re.match(r"^Table\*?\s+\d+[\s:.]?\s*(.*)$", caption_line, re.IGNORECASE)
            if caption_match:
                table_caption = caption_match.group(1).strip()

        # Check if current line starts a table (contains pipe symbols)
        if _is_table_start(line, lines, i):
            # Found a table! Extract it
            header_line = line.strip()

            # Parse header
            headers = _split_table_row_respecting_backticks(header_line)
            num_cols = len(headers)

            # Skip header and separator
            i += 2

            # Collect data rows
            data_rows: TableData = []
            while i < len(lines) and lines[i].strip():
                current_line = lines[i].strip()
                if _is_table_row(current_line):
                    cells = _split_table_row_respecting_backticks(current_line)
                    # Pad cells if needed
                    while len(cells) < num_cols:
                        cells.append("")
                    data_rows.append(cells[:num_cols])  # Truncate if too many
                    i += 1
                else:
                    break

            # Remove the caption line from result_lines if it was added
            if table_caption and caption_line_index is not None:
                # Calculate how many lines to remove based on caption position
                lines_back = i - caption_line_index
                # Remove the appropriate number of lines from result_lines
                if lines_back == 1:  # Caption was immediately before table
                    if result_lines and result_lines[-1].strip().lower().startswith("table"):
                        result_lines.pop()
                elif (
                    lines_back == 2
                    and len(result_lines) >= 2
                    and result_lines[-1].strip() == ""
                    and result_lines[-2].strip().lower().startswith("table")
                ):
                    # Remove blank line and caption line
                    result_lines.pop()  # Remove blank line
                    result_lines.pop()  # Remove caption line

            # Check for new format table caption after the table
            new_format_caption, table_id, rotation_angle = _parse_table_caption(lines, i)
            if new_format_caption:
                i += 2  # Skip blank line and caption line

            # Generate LaTeX table with the processed caption
            latex_table = generate_latex_table(
                headers,
                data_rows,
                new_format_caption or table_caption,
                table_width,
                table_id,
                protected_backtick_content,
                rotation_angle,
                is_supplementary,
            )
            result_lines.extend(latex_table.split("\n"))

            # Continue with next line (i is already incremented)
            continue

        # Not a table, add line as-is
        result_lines.append(line)
        i += 1

    return "\n".join(result_lines)


def generate_latex_table(
    headers: TableHeaders,
    data_rows: TableData,
    caption: str | None = None,
    width: str = "single",
    table_id: str | None = None,
    protected_backtick_content: ProtectedContent | None = None,
    rotation_angle: int | None = None,
    is_supplementary: bool = False,
) -> LatexContent:
    """Generate LaTeX table from headers and data rows.

    Uses sidewaystable for rotation.

    Args:
        headers: List of table header strings
        data_rows: List of table rows (each row is a list of cell strings)
        caption: Optional table caption
        width: Table width ("single" or "double")
        table_id: Optional table ID for labeling
        protected_backtick_content: Protected backtick content dictionary
        rotation_angle: Optional rotation angle for table
        is_supplementary: Whether this is a supplementary table

    Returns:
        Complete LaTeX table environment as string
    """
    if protected_backtick_content is None:
        protected_backtick_content = {}

    num_cols = len(headers)

    # Check if this is a Markdown Syntax Overview table to preserve literal
    # syntax in the first column
    # Remove markdown formatting from header for comparison
    first_header_clean = headers[0].lower().strip() if headers else ""
    first_header_clean = re.sub(r"\*\*(.*?)\*\*", r"\1", first_header_clean)  # Remove **bold**
    first_header_clean = re.sub(r"\*(.*?)\*", r"\1", first_header_clean)  # Remove *italic*
    is_markdown_syntax_table = first_header_clean == "markdown element"

    # Determine if we should use tabularx for better width handling
    # Use tabularx for:
    # 1. Markdown syntax table (special case)
    # 2. Tables with many columns (5 or more)
    # 3. Tables that would benefit from flexible column width
    use_tabularx = (
        (is_markdown_syntax_table and rotation_angle)  # Original condition
        or (num_cols >= 5)  # Wide tables with many columns
        or (any(len(header) > 15 for header in headers))  # Tables with long headers
    )

    # Create column specification
    if use_tabularx:
        if is_markdown_syntax_table:
            # Special case for markdown syntax table
            col_spec = "|l|l|X|"  # Markdown Element | LaTeX Equivalent | Description
        elif num_cols >= 6:
            # For very wide tables (6+ columns), use mix of fixed and flexible columns
            # First two columns fixed, rest flexible
            col_spec = "|l|l|" + "X|" * (num_cols - 2) + ""
        elif num_cols == 5:
            # For 5-column tables, use one flexible column in the middle or end
            col_spec = "|l|l|X|l|l|"
        else:
            # For tables with long headers, use flexible columns
            col_spec = "|" + "X|" * num_cols
    else:
        # Use regular column specification (all left-aligned with borders)
        col_spec = "|" + "l|" * num_cols

    # Format headers
    formatted_headers: list[str] = []
    for i, header in enumerate(headers):
        # For markdown syntax table, treat first two columns as literal code examples
        is_code_example_column = i < 2 and is_markdown_syntax_table
        formatted_headers.append(
            _format_table_cell(
                header,
                is_code_example_column,
                is_header=True,
                protected_backtick_content=protected_backtick_content,
            )
        )

    # Format data rows
    formatted_data_rows: list[list[str]] = []
    for row in data_rows:
        formatted_row: list[str] = []
        for i, cell in enumerate(row):
            # For markdown syntax table, treat first two columns as literal code
            is_code_example_column = i < 2 and is_markdown_syntax_table
            formatted_row.append(
                _format_table_cell(
                    cell,
                    is_code_example_column,
                    is_header=False,
                    protected_backtick_content=protected_backtick_content,
                )
            )
        formatted_data_rows.append(formatted_row)

    # Determine table environment
    if use_tabularx:
        if is_markdown_syntax_table:
            # Override rotation for markdown syntax table - use portrait with tabularx
            table_env, position = _determine_table_environment(
                "double",
                None,
                is_supplementary,  # Force double-column, no rotation
            )
        else:
            # For other wide tables, use double column layout for better fit
            table_env, position = _determine_table_environment("double", rotation_angle, is_supplementary)
    else:
        table_env, position = _determine_table_environment(width, rotation_angle, is_supplementary)

    # Build LaTeX table environment
    latex_lines = [
        f"\\begin{{{table_env}}}{position}",
        "\\centering",
    ]

    # Add rotation if specified and not already using sidewaystable
    # Skip rotation for markdown syntax tables (they use tabularx instead)
    use_rotatebox = (
        rotation_angle and not table_env.startswith("sideways") and not (is_markdown_syntax_table and use_tabularx)
    )
    if use_rotatebox:
        latex_lines.append(f"\\rotatebox{{{rotation_angle}}}{{%")

    # Add tabular environment
    if use_tabularx:
        # Use smaller font for wide tables to improve fit
        if num_cols >= 5:
            latex_lines.append("\\footnotesize")  # Smaller font for wide tables
        else:
            latex_lines.append("\\small")  # Standard small font
        latex_lines.append(f"\\begin{{tabularx}}{{\\textwidth}}{{{col_spec}}}")
    else:
        latex_lines.append(f"\\begin{{tabular}}{{{col_spec}}}")
    latex_lines.append("\\hline")

    # Add header row
    header_row = " & ".join(formatted_headers) + " \\\\"
    latex_lines.append(header_row)
    latex_lines.append("\\hline")

    # Add data rows
    for row in formatted_data_rows:
        data_row = " & ".join(row) + " \\\\"
        latex_lines.append(data_row)
        latex_lines.append("\\hline")

    # Close tabular environment
    if use_tabularx:
        latex_lines.append("\\end{tabularx}")
    else:
        latex_lines.append("\\end{tabular}")

    # Close rotatebox if used
    if use_rotatebox:
        latex_lines.append("}%")

    # Add caption
    if caption:
        latex_lines.append("\\raggedright")
        latex_lines.append(f"\\caption{{{caption}}}")
        label = table_id if table_id else "tab:comparison"
        latex_lines.append(f"\\label{{{label}}}")

    # Close environment
    latex_lines.append(f"\\end{{{table_env}}}")

    return "\n".join(latex_lines)


def _format_table_cell(
    cell: str,
    is_markdown_example_column: bool = False,
    is_header: bool = False,
    protected_backtick_content: ProtectedContent | None = None,
) -> str:
    """Format a table cell for LaTeX output.

    Args:
        cell: Cell content to format
        is_markdown_example_column: Whether this is a markdown syntax example column
        is_header: Whether this is a header cell
        protected_backtick_content: Protected backtick content dictionary

    Returns:
        Formatted cell content for LaTeX
    """
    if protected_backtick_content is None:
        protected_backtick_content = {}

    # First restore any protected backtick content
    for placeholder, original in protected_backtick_content.items():
        cell = cell.replace(placeholder, original)

    # If this is the "Markdown Element" column, preserve literal syntax
    if is_markdown_example_column:
        return _format_markdown_syntax_cell(cell)

    # Regular cell formatting (including headers)
    return _format_regular_table_cell(cell)


def _format_markdown_syntax_cell(cell: str) -> str:
    """Format a cell in markdown syntax overview table to preserve literal syntax."""

    # First, process backticks to preserve literal syntax
    def process_code_only(match: re.Match[str]) -> str:
        code_content = match.group(1)

        # Check if this looks like LaTeX syntax (starts with backslash)
        if code_content.startswith("\\"):
            # This is LaTeX syntax - use special LaTeX escaping
            code_content = _escape_latex_syntax_for_texttt(code_content)
        else:
            # This is markdown syntax - use regular literal escaping
            code_content = _escape_literal_markdown_for_texttt(code_content)

        return f"\\texttt{{{code_content}}}"

    # Process backticks first to protect literal syntax
    cell = re.sub(r"`([^`]+)`", process_code_only, cell)

    # Now apply markdown formatting only to text outside of \texttt{} blocks
    # Convert **bold** to \textbf{...} and *italic* to \textit{...} if not in \texttt
    def apply_markdown_formatting(text: str) -> str:
        # Don't apply formatting inside \texttt{} blocks
        if "\\texttt{" in text:
            return text
        text = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", text)
        text = re.sub(r"\*([^*]+)\*", r"\\textit{\1}", text)
        return text

    # Split by \texttt blocks and apply formatting only to the non-texttt parts
    parts = re.split(r"(\\texttt\{[^}]*\})", cell)
    for i in range(len(parts)):
        if not parts[i].startswith("\\texttt{"):
            parts[i] = apply_markdown_formatting(parts[i])

    return "".join(parts)


def _format_regular_table_cell(cell: str) -> str:
    """Format a regular table cell with markdown processing."""

    # First, process code blocks to protect them from markdown formatting
    def process_code_in_table(match: re.Match[str]) -> str:
        code_content = match.group(1)
        # Replace problematic characters that break tables
        # Order matters - do backslashes first, then other characters
        code_content = _escape_for_texttt(code_content)
        # For multiline code in tables, replace newlines with spaces
        code_content = code_content.replace("\n", " ")
        # Remove multiple spaces
        code_content = re.sub(r"\s+", " ", code_content).strip()
        return f"\\texttt{{{code_content}}}"

    # Process code blocks - use simple approach that handles all cases
    # First handle the specific case of `` `code` `` (double backticks with
    # inner backticks)
    cell = re.sub(
        r"``\s*`([^`]+)`\s*``",
        lambda m: f"\\texttt{{{_escape_for_texttt(m.group(1))}}}",
        cell,
    )
    # Then handle regular double backticks
    cell = re.sub(r"``([^`]+)``", process_code_in_table, cell)
    # Finally handle single backticks
    cell = re.sub(r"`([^`]+)`", process_code_in_table, cell)

    # Apply formatting outside texttt blocks
    cell = _apply_formatting_outside_texttt(cell)

    # Process citations after formatting but before escaping
    cell = convert_citations_to_latex(cell)

    # Escape remaining special characters outside LaTeX commands
    cell = _escape_outside_latex_commands(cell)

    return cell


def _escape_latex_special_chars(text: str) -> str:
    """Escape LaTeX special characters in text."""
    text = text.replace("\\", "\\textbackslash{}")
    text = text.replace("{", "\\{")
    text = text.replace("}", "\\}")
    text = text.replace("&", "\\&")
    text = text.replace("%", "\\%")
    text = text.replace("$", "\\$")
    text = text.replace("#", "\\#")
    text = text.replace("^", "\\textasciicircum{}")
    text = text.replace("~", "\\textasciitilde{}")
    text = text.replace("_", "\\_")
    text = text.replace("[", "\\lbrack{}")
    text = text.replace("]", "\\rbrack{}")
    text = text.replace("@", "\\@")
    return text


def _escape_latex_syntax_for_texttt(text: str) -> str:
    r"""Escape LaTeX syntax examples for display in texttt without double-escaping.

    This function is specifically for LaTeX command examples (like \textbf{bold})
    that should be displayed literally in tables without breaking LaTeX parsing.
    """
    # For LaTeX syntax examples, we want to show the command as-is
    # The key insight: \textbackslash{} renders as a single backslash in LaTeX
    # So \textbackslash{}textbf\{bold\} should render as \textbf{bold}

    # Replace backslashes with \textbackslash (no {})
    text = text.replace("\\", "\\textbackslash ")

    # Escape curly braces so they display as literal braces
    text = text.replace("{", "\\{")
    text = text.replace("}", "\\}")

    # Escape other special characters that could break table parsing
    text = text.replace("&", "\\&")
    text = text.replace("%", "\\%")
    text = text.replace("$", "\\$")
    text = text.replace("#", "\\#")
    text = text.replace("^", "\\textasciicircum{}")
    text = text.replace("~", "\\textasciitilde{}")
    text = text.replace("_", "\\_")

    return text


def _escape_literal_markdown_for_texttt(text: str) -> str:
    """Escape literal markdown syntax for display in texttt without breaking LaTeX.

    This function is specifically for markdown syntax examples that should be displayed
    literally in tables (e.g., showing `**bold**` instead of converting to LaTeX).
    """
    # For literal markdown syntax, we want minimal escaping to preserve readability
    # Only escape characters that would break LaTeX parsing

    # Handle backslashes carefully - don't add extra spaces for literal syntax
    text = text.replace("\\", "\\textbackslash{}")

    # Escape curly braces
    text = text.replace("{", "\\{")
    text = text.replace("}", "\\}")

    # Escape other LaTeX special characters
    text = text.replace("&", "\\&")
    text = text.replace("%", "\\%")
    text = text.replace("$", "\\$")
    text = text.replace("#", "\\#")
    text = text.replace("^", "\\textasciicircum{}")
    text = text.replace("~", "\\textasciitilde{}")
    text = text.replace("_", "\\_")

    return text


def _escape_latex_for_texttt_safe(text: str) -> str:
    """Escape LaTeX special characters safely for use in texttt environments.

    This function uses a more robust approach to prevent LaTeX from interpreting
    escaped characters as commands when they appear inside texttt environments.
    """
    # For texttt content, use a simpler approach that doesn't break LaTeX parsing
    # Only escape the minimal set of characters that actually cause problems

    # Replace backslashes with a safer representation
    # Remove the extra space that was causing LaTeX parsing issues
    text = text.replace("\\", "\\textbackslash{}")

    # Use simpler curly brace escaping that doesn't break parsing
    text = text.replace("{", "\\{")
    text = text.replace("}", "\\}")

    # Handle other special characters
    text = text.replace("&", "\\&")
    text = text.replace("%", "\\%")
    text = text.replace("$", "\\$")
    text = text.replace("#", "\\#")
    text = text.replace("^", "\\textasciicircum{}")
    text = text.replace("~", "\\textasciitilde{}")
    text = text.replace("_", "\\_")
    text = text.replace("@", "\\@")

    return text


def _escape_for_texttt(text: str) -> str:
    r"""Escape special characters for use inside \\texttt{} environment.

    In texttt, most characters are literal, but we need to escape:
    - Special unicode characters like arrows
    - ASCII arrow sequences that can trigger math mode
    """
    # Handle special characters that don't work well in texttt
    # Replace unicode arrows with text equivalents for texttt environment
    text = text.replace("→", " to ")
    text = text.replace("←", " from ")
    text = text.replace("↑", " up ")
    text = text.replace("↓", " down ")
    # Replace ASCII arrow sequences that can cause math mode issues
    text = text.replace("->", " to ")
    text = text.replace("<-", " from ")
    text = text.replace("=>", " implies ")

    # For texttt, only escape characters that really need it
    # Most characters are literal in texttt, so avoid over-escaping

    return text


def _apply_formatting_outside_texttt(text: str) -> str:
    """Apply markdown formatting outside texttt blocks."""

    # Handle bold first (double asterisks) - but only outside \texttt{}
    def replace_bold_outside_texttt(text: str) -> str:
        parts = re.split(r"(\\texttt\{[^}]*\})", text)
        result: list[str] = []
        for _i, part in enumerate(parts):
            if part.startswith("\\texttt{"):
                result.append(part)
            else:
                part = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", part)
                result.append(part)
        return "".join(result)

    # Handle italic (single asterisks) - but only outside \texttt{}
    def replace_italic_outside_texttt(text: str) -> str:
        parts = re.split(r"(\\texttt\{[^}]*\})", text)
        result: list[str] = []
        for _i, part in enumerate(parts):
            if part.startswith("\\texttt{"):
                result.append(part)
            else:
                part = re.sub(
                    r"(?<!\*)\*([^*\s][^*]*[^*\s]|\w)\*(?!\*)",
                    r"\\textit{\1}",
                    part,
                )
                result.append(part)
        return "".join(result)

    text = replace_bold_outside_texttt(text)
    text = replace_italic_outside_texttt(text)
    return text


def _escape_underscores_outside_cite(text: str) -> str:
    r"""Escape underscores but not inside \cite{} commands."""
    # Split text on cite commands to preserve them
    parts = re.split(r"(\\cite\{[^}]*\})", text)
    result: list[str] = []
    for part in parts:
        if part.startswith("\\cite{"):
            # Don't escape underscores inside cite commands
            result.append(part)
        else:
            # Escape underscores in regular text
            part = part.replace("_", "\\_")
            result.append(part)
    return "".join(result)


def _escape_outside_latex_commands(text: str) -> str:
    """Escape special characters outside LaTeX formatting commands."""
    # Split on all LaTeX formatting commands to protect them
    parts = re.split(r"(\\texttt\{[^}]*\}|\\textbf\{[^}]*\}|\\textit\{[^}]*\})", text)
    result: list[str] = []
    for _i, part in enumerate(parts):
        if part.startswith(("\\texttt{", "\\textbf{", "\\textit{")):
            result.append(part)
        else:
            part = part.replace("&", "\\&")
            part = part.replace("%", "\\%")
            part = part.replace("$", "\\$")
            part = part.replace("#", "\\#")
            part = part.replace("^", "\\^{}")
            part = part.replace("~", "\\~{}")
            # Escape underscores but not inside \cite{} commands
            part = _escape_underscores_outside_cite(part)
            # Handle Unicode arrows that can cause LaTeX math mode issues
            part = part.replace("→", "$\\rightarrow$")
            part = part.replace("←", "$\\leftarrow$")
            part = part.replace("↑", "$\\uparrow$")
            part = part.replace("↓", "$\\downarrow$")
            # Escape problematic hyphens in compound words (but not all hyphens)
            # Only escape hyphens in specific problematic contexts
            part = part.replace("cross-references", "cross\\-references")
            part = part.replace("self-contained", "self\\-contained")
            part = part.replace("user-friendly", "user\\-friendly")
            part = part.replace("pre-configured", "pre\\-configured")
            part = part.replace("zero-setup", "zero\\-setup")
            part = part.replace("fully-resolved", "fully\\-resolved")
            result.append(part)
    return "".join(result)


def _is_table_start(line: str, lines: list[str], i: int) -> bool:
    """Check if a line starts a markdown table."""
    return (
        "|" in line
        and line.strip().startswith("|")
        and line.strip().endswith("|")
        and i + 1 < len(lines)
        and "|" in lines[i + 1]
        and "-" in lines[i + 1]
    )


def _is_table_row(line: str) -> bool:
    """Check if a line is a valid table row."""
    return "|" in line and line.startswith("|") and line.endswith("|")


def _parse_table_caption(lines: list[str], i: int) -> tuple[str | None, str | None, int | None]:
    """Parse table caption in new format after table."""
    new_format_caption = None
    table_id = None
    rotation_angle = None

    if (
        i < len(lines)
        and lines[i].strip() == ""
        and i + 1 < len(lines)
        and re.match(r"^\{#[a-zA-Z0-9_:-]+.*\}\s*\*\*.*\*\*", lines[i + 1].strip())
    ):
        # Found new format caption, parse it
        caption_line = lines[i + 1].strip()

        # Parse caption with optional attributes like rotate=90
        caption_match = re.match(r"^\{#([a-zA-Z0-9_:-]+)([^}]*)\}\s*(.+)$", caption_line)
        if caption_match:
            table_id = caption_match.group(1)
            attributes_str = caption_match.group(2).strip()
            caption_text = caption_match.group(3)

            # Extract rotation attribute if present
            if attributes_str:
                rotation_match = re.search(r"rotate=(\d+)", attributes_str)
                if rotation_match:
                    rotation_angle = int(rotation_match.group(1))

            # Process caption text to handle markdown formatting
            new_format_caption = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", caption_text)
            new_format_caption = re.sub(r"\*([^*]+)\*", r"\\textit{\1}", new_format_caption)

    return new_format_caption, table_id, rotation_angle


def _split_table_row_respecting_backticks(row: str) -> list[str]:
    """Split a table row on pipe characters while respecting backticks.

    Args:
        row: The table row string to split

    Returns:
        List of cell contents
    """
    # Find all backtick-protected regions
    backtick_ranges = []
    in_backtick = False
    start_pos = 0

    for i, char in enumerate(row):
        if char == "`":
            if not in_backtick:
                start_pos = i
                in_backtick = True
            else:
                backtick_ranges.append((start_pos, i))
                in_backtick = False

    # Split on pipes that are not inside backticks
    cells = []
    current_cell = ""

    for i, char in enumerate(row):
        if char == "|":
            # Check if this pipe is inside backticks
            inside_backticks = any(start <= i <= end for start, end in backtick_ranges)
            if not inside_backticks:
                cells.append(current_cell.strip())
                current_cell = ""
            else:
                current_cell += char
        else:
            current_cell += char

    # Add the last cell
    if current_cell:
        cells.append(current_cell.strip())

    # Remove empty cells at the beginning and end (markdown table format)
    while cells and not cells[0]:
        cells.pop(0)
    while cells and not cells[-1]:
        cells.pop()

    return cells


def convert_table_references_to_latex(text: MarkdownContent) -> LatexContent:
    r"""Convert table references from @table:id and @stable:id to LaTeX.

    Converts @table:id to Table \\ref{table:id} and @stable:id to
    Table \\ref{stable:id}.

    Args:
        text: Text containing table references

    Returns:
        Text with table references converted to LaTeX format with "Table" prefix
    """
    # Convert @table:id to Table \ref{table:id} (regular tables)
    text = re.sub(r"@table:([a-zA-Z0-9_-]+)", r"Table \\ref{table:\1}", text)

    # Convert @stable:id to Table \ref{stable:id} (supplementary tables)
    text = re.sub(r"@stable:([a-zA-Z0-9_-]+)", r"Table \\ref{stable:\1}", text)

    return text


def _determine_table_environment(width: str, rotation_angle: int | None, is_supplementary: bool) -> tuple[str, str]:
    """Determine the appropriate table environment and position."""
    if rotation_angle and is_supplementary:
        # Use unified sideways table for rotated supplementary tables
        table_env = "ssidewaystable"
        position = ""  # ssidewaystable handles positioning internally
    elif is_supplementary:
        table_env = "table*" if width == "double" else "table"
        position = "[ht]"
    else:
        table_env = "table*" if width == "double" else "table"
        position = width == "double" and "[!ht]" or "[ht]"

    return table_env, position
