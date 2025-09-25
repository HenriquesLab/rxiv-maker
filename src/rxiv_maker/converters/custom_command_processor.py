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

    # Protect tex block placeholders from being processed
    def protect_tex_placeholder(match: re.Match[str]) -> str:
        protected_blocks.append(match.group(0))
        return f"__CUSTOM_CODE_BLOCK_{len(protected_blocks) - 1}__"

    text = re.sub(r"XXPROTECTEDTEXBLOCKXX\d+XXPROTECTEDTEXBLOCKXX", protect_tex_placeholder, text)

    # Process custom commands with new 3-step Python execution model
    # Store original text for accurate line number calculation
    original_text_for_line_numbers = text
    text = _process_blindtext_commands(text)
    text = _process_tex_commands(text)
    text = _process_python_commands_three_step(text, original_text_for_line_numbers)
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


def _filter_latex_comments(tex_code: str) -> str:
    """Filter LaTeX comments from TeX code before processing.

    Removes both full-line comments and inline comments while preserving
    the structure for proper LaTeX processing.

    Args:
        tex_code: LaTeX code that may contain comments

    Returns:
        LaTeX code with comments filtered out
    """
    lines = tex_code.split("\n")
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
            # Check if this tex command is inside a texttt/detokenize block (should be left as literal)
            context_start = max(0, i - 30)  # Look back for context
            context = text[context_start:i]

            # If we're inside \texttt{\detokenize{, don't process this as a tex command
            if r"\texttt{\detokenize{" in context and context.count("{") > context.count("}"):
                # This is inside a detokenize block - treat as literal text
                result.append(text[i])
                i += 1
                continue

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

                # CRITICAL: Filter out LaTeX comments before processing
                # Comments should never be processed as active TeX content
                tex_code = _filter_latex_comments(tex_code)

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


def _process_python_commands_three_step(text: MarkdownContent, original_text: MarkdownContent = None) -> LatexContent:
    """Process Python execution commands using enhanced 3-step execution model.

    Step 0: Process {{py:}} blocks - execute and display output
    Step 1: Execute all {{py:exec code}} blocks in order to initialize context
    Step 2: Process all {{py:get variable}} blocks using initialized context
    Step 3: Continue with LaTeX conversion (Python code already resolved)

    Args:
        text: Markdown content with Python commands (potentially preprocessed)
        original_text: Original markdown content before preprocessing (for accurate line numbers)

    Returns:
        LaTeX content with Python commands processed
    """
    try:
        from .python_executor import get_python_executor

        executor = get_python_executor()
    except ImportError:
        # If python_executor is not available, return text unchanged
        return text

    # STEP 0: Process simple {{py:}} blocks that execute and display output
    text = _process_python_block_commands(text, executor)

    # STEP 1: Find and execute all {{py:exec}} blocks in order
    # Use original text for accurate line numbers if available
    exec_blocks = _find_python_exec_blocks(text, original_text)

    for exec_block in exec_blocks:
        try:
            # Execute the initialization block with manuscript context
            executor.execute_initialization_block(
                exec_block["code"],
                manuscript_file="manuscript",  # Could be enhanced to pass actual filename
                line_number=exec_block["line_number"],
            )
        except Exception as e:
            # Python execution errors should halt the entire build process
            from ..core.logging_config import get_logger

            logger = get_logger()

            # Create more informative error message
            error_lines = str(e).split("\n")
            main_error = error_lines[0] if error_lines else str(e)

            # Show a preview of the code block for context
            code_preview = exec_block["code"].strip()
            lines = code_preview.split("\n")
            preview_lines = lines[:3]  # Show first 3 lines
            if len(lines) > 3:
                preview_lines.append("...")
            code_snippet = "\n    ".join(preview_lines)

            error_msg = f"""Python execution error in exec block starting at line {exec_block["line_number"]}:

Error: {main_error}

Code block preview:
    {code_snippet}

This error occurred while executing the {{{{py:exec}}}} block in the manuscript."""

            # Import here to avoid circular imports
            from .python_executor import PythonExecutionError

            # Log the detailed error message once, then raise a simpler version to avoid repetition
            logger.error(error_msg)

            # Re-raise with a simpler message to avoid duplication in higher-level error handling
            simple_msg = (
                f"Python execution error in exec block starting at line {exec_block['line_number']}: {main_error}"
            )

            if isinstance(e, PythonExecutionError):
                # Preserve the original exception but ensure it halts the build
                raise PythonExecutionError(simple_msg) from e
            else:
                # Convert other exceptions to PythonExecutionError
                raise PythonExecutionError(simple_msg) from e

    # Remove all {{py:exec}} blocks from text (they were initialization only)
    text = _remove_python_exec_blocks(text)

    # STEP 1.5: Process inline {py: expression} commands (after exec blocks are executed)
    text = _process_python_inline_commands(text, executor)

    # STEP 2: Process all {{py:get}} blocks using initialized context
    text = _process_python_get_blocks(text, executor)

    return text


def _find_python_exec_blocks(text: MarkdownContent, original_text: MarkdownContent = None) -> list[dict]:
    """Find all {{py:exec}} blocks in text and return their details.

    Args:
        text: Text to search for Python blocks (potentially preprocessed)
        original_text: Original text for accurate line number calculation

    Returns:
        List of dictionaries with block details including accurate line numbers
    """
    exec_blocks = []

    # Use original text for line number calculation if available
    line_number_text = original_text if original_text is not None else text

    # Split text into lines to calculate line numbers
    lines = line_number_text.split("\n")
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
                if original_text is not None:
                    # Find the position of this block in the original text
                    # Look for the same {{py:exec block content in original text
                    original_pos = original_text.find(full_match)
                    if original_pos >= 0:
                        # Create character-to-line mapping for original text
                        orig_lines = original_text.split("\n")
                        orig_char_to_line = {}
                        orig_char_pos = 0
                        for orig_line_num, orig_line in enumerate(orig_lines, 1):
                            for _ in range(len(orig_line) + 1):  # +1 for newline
                                orig_char_to_line[orig_char_pos] = orig_line_num
                                orig_char_pos += 1
                        line_number = orig_char_to_line.get(original_pos, 1)
                    else:
                        line_number = 1  # Fallback
                else:
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


def _process_python_block_commands(text: MarkdownContent, executor) -> LatexContent:
    """Process simple {{py:}} blocks that execute code and display output."""
    result = []
    i = 0
    while i < len(text):
        # Look for {{py: but not {{py:exec or {{py:get
        if text[i : i + 5] == "{{py:":
            # Check if it's not followed by "exec" or "get"
            remaining = text[i + 5 :]
            if not (remaining.startswith("exec") or remaining.startswith("get")):
                # Find the matching closing }}
                brace_count = 2  # Start with {{
                start = i + 5  # After "{{py:"
                j = start
                while j < len(text) and brace_count > 0:
                    if text[j] == "{":
                        brace_count += 1
                    elif text[j] == "}":
                        brace_count -= 1
                    j += 1

                if brace_count == 0:
                    # Found matching braces, extract and execute the code
                    code = text[start : j - 2].strip()  # Exclude the }}

                    try:
                        # Execute the code and get formatted output
                        output = executor.execute_block(code)
                        result.append(output)
                        i = j
                    except (ValueError, KeyError, AttributeError, TypeError) as e:
                        # Handle specific execution errors with logging
                        from ..core.logging_config import get_logger

                        logger = get_logger()
                        logger.warning(f"Python execution error in py:get command: {str(e)}")
                        error_msg = f"```\nPython execution error: {str(e)}\n```"
                        result.append(error_msg)
                        i = j
                else:
                    # No matching braces found, keep the original text
                    result.append(text[i])
                    i += 1
            else:
                # This is {{py:exec or {{py:get, skip it for now
                result.append(text[i])
                i += 1
        else:
            result.append(text[i])
            i += 1

    return "".join(result)


def _process_python_inline_commands(text: MarkdownContent, executor) -> LatexContent:
    """Process inline {py: expression} commands."""
    # Split text into lines to calculate line numbers for tracking
    lines = text.split("\n")

    def process_inline_command(match: re.Match[str]) -> str:
        expression = match.group(1).strip()

        # Calculate line number for this match
        line_number = None
        match_start = match.start()
        char_count = 0
        for line_idx, line in enumerate(lines):
            if char_count + len(line) >= match_start:
                line_number = line_idx + 1
                break
            char_count += len(line) + 1  # +1 for newline

        try:
            # Execute the expression as inline code
            result = executor.execute_inline(expression, line_number=line_number, file_path="manuscript")
            return result
        except (ValueError, KeyError, AttributeError, TypeError, NameError, SyntaxError) as e:
            # Handle specific Python execution errors with logging
            from ..core.logging_config import get_logger

            logger = get_logger()
            logger.warning(f"Python inline execution error for '{expression}' at line {line_number}: {str(e)}")
            return f"[Error: {str(e)}]"

    # Process {py: expression} patterns (single braces, not double braces)
    # Use negative lookbehind to avoid matching {{py: patterns
    text = re.sub(r"(?<!\{)\{py:\s*([^}]+)\}(?!\})", process_inline_command, text)

    return text


def _process_python_get_blocks(text: MarkdownContent, executor) -> LatexContent:
    """Process all {{py:get}} blocks using the initialized Python context."""
    # Split text into lines to calculate line numbers for tracking
    lines = text.split("\n")

    def process_get_command(match: re.Match[str]) -> str:
        variable_name = match.group(1).strip()

        # Calculate line number for this match
        line_number = None
        match_start = match.start()
        char_count = 0
        for line_idx, line in enumerate(lines):
            if char_count + len(line) >= match_start:
                line_number = line_idx + 1
                break
            char_count += len(line) + 1  # +1 for newline

        try:
            result = executor.get_variable_value(variable_name, line_number=line_number, file_path="manuscript")
            return str(result) if result is not None else ""
        except (ValueError, KeyError, AttributeError, NameError) as e:
            # Handle specific variable retrieval errors with logging
            from ..core.logging_config import get_logger

            logger = get_logger()
            logger.warning(f"Error retrieving variable '{variable_name}' at line {line_number}: {str(e)}")
            return f"[Error retrieving {variable_name}: {str(e)}]"
        except Exception as e:
            # Handle PythonExecutionError and other execution-related errors
            from ..core.logging_config import get_logger

            logger = get_logger()
            logger.warning(
                f"Python execution error retrieving variable '{variable_name}' at line {line_number}: {str(e)}"
            )
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
