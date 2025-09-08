r"""Custom markdown command processor for rxiv-maker.

This module handles custom markdown commands that get converted to LaTeX.
It provides an extensible framework for adding new commands while maintaining
the same patterns as other processors in the converters package.

Currently supported commands:
- {{blindtext}} → \blindtext
- {{Blindtext}} → \\Blindtext
- {{tex: LaTeX code}} → Direct LaTeX code injection
- {{py:exec code}} → Execute Python code (initialization)
- {{py:get variable}} → Insert Python variable values

Future planned commands:
- {{r: code}} → Execute R code and insert output
"""

import re
from typing import Callable, Dict

from .types import LatexContent, MarkdownContent


def process_custom_commands(text: MarkdownContent) -> LatexContent:
    """Process all custom markdown commands and convert them to LaTeX.

    Now implements 3-step execution model for Python commands:
    1. Execute all {{py:exec}} blocks in order
    2. Process all {{py:get}} blocks using initialized context
    3. Continue with other command processing

    Args:
        text: The markdown content containing custom commands

    Returns:
        LaTeX content with custom commands converted
    """
    # First protect code blocks from command processing
    protected_blocks: list[str] = []

    # Protect fenced code blocks
    def protect_fenced_code(match: re.Match[str]) -> str:
        protected_blocks.append(match.group(0))
        return f"__CUSTOM_CODE_BLOCK_{len(protected_blocks) - 1}__"

    text = re.sub(r"```.*?```", protect_fenced_code, text, flags=re.DOTALL)

    # Protect inline code (backticks)
    def protect_inline_code(match: re.Match[str]) -> str:
        protected_blocks.append(match.group(0))
        return f"__CUSTOM_CODE_BLOCK_{len(protected_blocks) - 1}__"

    text = re.sub(r"`[^`]+`", protect_inline_code, text)

    # Process custom commands with new 3-step Python execution model
    text = _process_blindtext_commands(text)
    text = _process_tex_commands(text)
    text = _process_python_commands_three_step(text)
    # Future: text = _process_r_commands(text)

    # Restore protected code blocks
    for i, block in enumerate(protected_blocks):
        text = text.replace(f"__CUSTOM_CODE_BLOCK_{i}__", block)

    return text


def _process_blindtext_commands(text: MarkdownContent) -> LatexContent:
    r"""Process blindtext commands converting {{blindtext}} → \\blindtext and {{Blindtext}} → \\Blindtext.

    Args:
        text: Markdown content with blindtext commands

    Returns:
        LaTeX content with blindtext commands converted
    """
    # Define the command mappings
    command_mappings = {
        "blindtext": r"\\blindtext",
        "Blindtext": r"\\Blindtext",
    }

    # Process each command type
    for markdown_cmd, latex_cmd in command_mappings.items():
        # Pattern matches {{command}} with optional whitespace
        pattern = rf"\{{\{{\s*{re.escape(markdown_cmd)}\s*\}}\}}"
        text = re.sub(pattern, latex_cmd, text)

    return text


def _process_tex_commands(text: MarkdownContent) -> LatexContent:
    r"""Process TeX injection commands converting {{tex: LaTeX code}} → LaTeX code.

    Args:
        text: Markdown content with TeX commands

    Returns:
        LaTeX content with TeX commands processed and raw LaTeX inserted
    """
    # Use a more robust approach to handle nested braces properly
    result = []
    i = 0

    while i < len(text):
        # Look for {{tex:
        start_marker = "{{tex:"
        if text[i : i + len(start_marker)] == start_marker:
            # Found the start of a TeX command
            # Find the matching closing }}
            brace_count = 2  # Start with {{
            start = i + len(start_marker)
            j = start
            while j < len(text) and brace_count > 0:
                if text[j] == "{":
                    brace_count += 1
                elif text[j] == "}":
                    brace_count -= 1
                j += 1

            if brace_count == 0:
                # Found matching braces, extract and process the TeX code
                tex_code = text[start : j - 2].strip()  # Exclude the }}

                # Fix encoding issues for common Unicode characters in TeX code
                # Replace degree symbol with LaTeX command for better compatibility
                tex_code = tex_code.replace("º", "\\degree")
                tex_code = tex_code.replace("°", "\\degree")

                result.append(tex_code)
                i = j
            else:
                # No matching braces found, keep the original text
                result.append(text[i])
                i += 1
        else:
            result.append(text[i])
            i += 1

    return "".join(result)


def _process_python_commands_three_step(text: MarkdownContent) -> LatexContent:
    """Process Python execution commands using 3-step execution model.

    Step 1: Execute all {{py:exec code}} blocks in order to initialize context
    Step 2: Process all {{py:get variable}} blocks using initialized context
    Step 3: Continue with LaTeX conversion (Python code already resolved)

    Args:
        text: Markdown content with Python commands

    Returns:
        LaTeX content with Python commands processed
    """
    try:
        from .python_executor import get_python_executor

        executor = get_python_executor()
    except ImportError:
        # If python_executor is not available, return text unchanged
        return text

    # STEP 1: Find and execute all {{py:exec}} blocks in order
    exec_blocks = _find_python_exec_blocks(text)

    for exec_block in exec_blocks:
        try:
            # Execute the initialization block with manuscript context
            executor.execute_initialization_block(
                exec_block["code"],
                manuscript_file="manuscript",  # Could be enhanced to pass actual filename
                line_number=exec_block["line_number"],
            )
        except Exception as e:
            # Replace the exec block with error message
            error_msg = f"```\nPython execution error in exec block: {str(e)}\n```"
            text = text.replace(exec_block["full_match"], error_msg)

    # Remove all {{py:exec}} blocks from text (they were initialization only)
    text = _remove_python_exec_blocks(text)

    # STEP 2: Process all {{py:get}} blocks using initialized context
    text = _process_python_get_blocks(text, executor)

    return text


def _find_python_exec_blocks(text: MarkdownContent) -> list[dict]:
    """Find all {{py:exec}} blocks in text and return their details."""
    exec_blocks = []

    # Split text into lines to calculate line numbers
    lines = text.split("\n")
    char_to_line = {}
    char_pos = 0
    for line_num, line in enumerate(lines, 1):
        for _char_idx in range(len(line) + 1):  # +1 for newline
            char_to_line[char_pos] = line_num
            char_pos += 1

    i = 0
    while i < len(text):
        # Look for {{py:exec
        start_marker = "{{py:exec"
        if text[i : i + len(start_marker)] == start_marker:
            # Find the matching closing }}
            brace_count = 2  # Start with {{
            start = i + len(start_marker)
            j = start
            while j < len(text) and brace_count > 0:
                if text[j] == "{":
                    brace_count += 1
                elif text[j] == "}":
                    brace_count -= 1
                j += 1

            if brace_count == 0:
                # Found matching braces
                full_match = text[i:j]
                code = text[start : j - 2].strip()  # Exclude the }}

                # Calculate line number where this block starts
                line_number = char_to_line.get(i, 1)

                exec_blocks.append(
                    {"full_match": full_match, "code": code, "start_pos": i, "end_pos": j, "line_number": line_number}
                )
                i = j
            else:
                i += 1
        else:
            i += 1

    return exec_blocks


def _remove_python_exec_blocks(text: MarkdownContent) -> LatexContent:
    """Remove all {{py:exec}} blocks from text."""
    result = []
    i = 0
    while i < len(text):
        # Look for {{py:exec
        start_marker = "{{py:exec"
        if text[i : i + len(start_marker)] == start_marker:
            # Find the matching closing }}
            brace_count = 2  # Start with {{
            start = i + len(start_marker)
            j = start
            while j < len(text) and brace_count > 0:
                if text[j] == "{":
                    brace_count += 1
                elif text[j] == "}":
                    brace_count -= 1
                j += 1

            if brace_count == 0:
                # Skip this entire exec block (remove it)
                i = j
            else:
                # No matching braces found, keep the text
                result.append(text[i])
                i += 1
        else:
            result.append(text[i])
            i += 1

    return "".join(result)


def _process_python_get_blocks(text: MarkdownContent, executor) -> LatexContent:
    """Process all {{py:get}} blocks using the initialized Python context."""

    def process_get_command(match: re.Match[str]) -> str:
        variable_name = match.group(1).strip()
        try:
            result = executor.get_variable_value(variable_name)
            return str(result) if result is not None else ""
        except Exception as e:
            return f"[Error retrieving {variable_name}: {str(e)}]"

    # Process {{py:get variable}} blocks
    text = re.sub(r"\{\{py:get\s+([^}]+)\}\}", process_get_command, text)

    return text


# Keep old function for backward compatibility (deprecated)
def _process_python_commands(text: MarkdownContent) -> LatexContent:
    """Process Python execution commands (deprecated - use _process_python_commands_three_step).

    This function is kept for backward compatibility but is no longer used by default.
    The new 3-step execution model is preferred.
    """
    # For now, redirect to new implementation
    return _process_python_commands_three_step(text)


def _process_r_commands(text: MarkdownContent) -> LatexContent:
    """Process R execution commands (future implementation).

    Will convert:
    - {{r: code}} → Execute R code and insert output
    - {r: code} → Execute R code inline

    Args:
        text: Markdown content with R commands

    Returns:
        LaTeX content with R commands processed
    """
    # Future implementation for R command execution
    return text


# Registry for extensibility
COMMAND_PROCESSORS: Dict[str, Callable[[MarkdownContent], LatexContent]] = {
    "blindtext": _process_blindtext_commands,
    "tex": _process_tex_commands,
    "python": _process_python_commands,
    # Future: 'r': _process_r_commands,
}


def register_command_processor(name: str, processor: Callable[[MarkdownContent], LatexContent]) -> None:
    """Register a new custom command processor.

    This allows for plugin-style extension of the custom command system.

    Args:
        name: Name of the command processor
        processor: Function that processes the commands
    """
    COMMAND_PROCESSORS[name] = processor


def get_supported_commands() -> list[str]:
    """Get list of currently supported custom commands.

    Returns:
        List of supported command names
    """
    return list(COMMAND_PROCESSORS.keys())
