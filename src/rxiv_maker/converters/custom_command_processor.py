r"""Custom markdown command processor for rxiv-maker.

This module handles custom markdown commands that get converted to LaTeX.
It provides an extensible framework for adding new commands while maintaining
the same patterns as other processors in the converters package.

Currently supported commands:
- {{blindtext}} → \blindtext
- {{Blindtext}} → \\Blindtext

Future planned commands:
- {{py: code}} → Execute Python code and insert output
- {py: code} → Execute Python code inline
"""

import re
from typing import Callable, Dict

from .types import LatexContent, MarkdownContent


def process_custom_commands(text: MarkdownContent) -> LatexContent:
    """Process all custom markdown commands and convert them to LaTeX.

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

    # Process custom commands
    text = _process_blindtext_commands(text)
    text = _process_python_commands(text)
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


def _process_python_commands(text: MarkdownContent) -> LatexContent:
    """Process Python execution commands.

    Converts:
    - {{py: code}} → Execute code and insert output as code block
    - {py: code} → Execute code inline and insert result

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

    # Process block Python commands {{py: code}}
    def process_block_python(match: re.Match[str]) -> str:
        code = match.group(1).strip()
        try:
            result = executor.execute_block(code)
            return result
        except Exception as e:
            return f"```\nPython execution error: {str(e)}\n```"

    # Process inline Python commands {py: code}
    def process_inline_python(match: re.Match[str]) -> str:
        code = match.group(1).strip()
        try:
            result = executor.execute_inline(code)
            return result
        except Exception as e:
            return f"[Error: {str(e)}]"

    # Apply block command processing first
    # Use non-greedy matching and handle nested braces properly
    def find_and_replace_block_python(text):
        result = []
        i = 0
        while i < len(text):
            # Look for {{py:
            start_marker = "{{py:"
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
                    code = text[start : j - 2]  # Exclude the }}

                    # Create a mock match object with captured code
                    captured_code = code.strip()

                    class MockMatch:
                        def __init__(self, captured_code_param):
                            self.captured_code = captured_code_param

                        def group(self, n):
                            return self.captured_code

                    replacement = process_block_python(MockMatch(captured_code))
                    result.append(replacement)
                    i = j
                else:
                    # No matching braces found
                    result.append(text[i])
                    i += 1
            else:
                result.append(text[i])
                i += 1
        return "".join(result)

    text = find_and_replace_block_python(text)

    # Apply inline command processing (simpler, single line)
    text = re.sub(r"\{py:\s*([^}]+)\}", process_inline_python, text)

    return text


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
