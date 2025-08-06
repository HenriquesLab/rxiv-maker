"""Code block processing for markdown to LaTeX conversion.

This module handles conversion of markdown code blocks (both fenced and indented)
to LaTeX listings or verbatim environments with proper syntax highlighting.
"""

import re

from .types import LatexContent, MarkdownContent


def convert_code_blocks_to_latex(text: MarkdownContent) -> LatexContent:
    """Convert markdown code blocks to LaTeX listings environments.

    Args:
        text: Text containing markdown code blocks

    Returns:
        Text with code blocks converted to LaTeX environments
    """
    # Handle fenced code blocks first (``` ... ```)
    text = _process_fenced_code_blocks(text)

    # Handle indented code blocks (4+ spaces at start of line)
    text = _process_indented_code_blocks(text)

    return text


def _process_fenced_code_blocks(text: MarkdownContent) -> LatexContent:
    """Process fenced code blocks (``` ... ```)."""

    def process_fenced_code_block(match: re.Match[str]) -> str:
        # Check if language is specified
        language_match = re.search(r"^```(\w+)", match.group(0))
        language = ""

        if language_match:
            language = language_match.group(1).lower()
            # Map common language names to listings-compatible ones
            language_map = {
                "yml": "yaml",
                "sh": "bash",
                "shell": "bash",
                "js": "javascript",
                "ts": "typescript",
                "py": "python",
                "md": "markdown",
                "tex": "latex",
                "bib": "bibtex",
            }
            language = language_map.get(language, language)

        # Extract content between the triple backticks
        full_match = match.group(0)
        if language_match:
            # Remove the language specification line
            content_start = full_match.find("\n") + 1
            content_end = full_match.rfind("\n```")
            code_content = full_match[content_start:content_end]
        else:
            # No language specified
            code_content = match.group(1)

        # Use listings if language is specified and supported, otherwise use verbatim
        if language and language in _get_supported_languages():
            return (
                f"{{\\footnotesize\n"
                f"\\begin{{lstlisting}}[style=arxivstyle,language={language}]\n"
                f"{code_content}\n"
                f"\\end{{lstlisting}}\n}}"
            )
        else:
            # Fallback to verbatim for unknown languages or no language specified
            return f"{{\\footnotesize\n\\begin{{verbatim}}\n{code_content}\n\\end{{verbatim}}\n}}"

    # Convert fenced code blocks first to protect them from further processing
    return re.sub(
        r"^```(?:\w+)?\n(.*?)\n```$",
        process_fenced_code_block,
        text,
        flags=re.MULTILINE | re.DOTALL,
    )


def _process_indented_code_blocks(text: MarkdownContent) -> LatexContent:
    """Process indented code blocks (4+ spaces at start of line)."""
    lines = text.split("\n")
    result_lines: list[str] = []
    i = 0
    in_code_env = False

    while i < len(lines):
        line = lines[i]

        # Track code environment state (verbatim or listings)
        if "\\begin{verbatim}" in line or re.search(r"\\begin\{lstlisting\}", line):
            in_code_env = True
            result_lines.append(line)
            i += 1
            continue
        elif "\\end{verbatim}" in line or "\\end{lstlisting}" in line:
            in_code_env = False
            result_lines.append(line)
            i += 1
            continue
        elif in_code_env:
            # We're inside a code environment, don't process as indented code
            result_lines.append(line)
            i += 1
            continue

        # Check if line is indented with 4+ spaces (code block) and not in code
        # environment
        if re.match(r"^    ", line) and line.strip() and not in_code_env:
            # Start of indented code block
            code_lines: list[str] = []

            # Collect all consecutive indented lines
            while i < len(lines):
                current_line = lines[i]
                if re.match(r"^    ", current_line) or current_line.strip() == "":
                    # Remove 4 spaces of indentation
                    if current_line.startswith("    "):
                        code_lines.append(current_line[4:])
                    else:
                        code_lines.append(current_line)
                    i += 1
                else:
                    break

            # Remove trailing empty lines
            while code_lines and code_lines[-1].strip() == "":
                code_lines.pop()

            if code_lines:
                result_lines.append("{\\footnotesize")
                result_lines.append("\\begin{verbatim}")
                result_lines.extend(code_lines)
                result_lines.append("\\end{verbatim}")
                result_lines.append("}")
        else:
            result_lines.append(line)
            i += 1

    return "\n".join(result_lines)


def _get_supported_languages() -> list[str]:
    """Get list of languages supported by listings."""
    return [
        "yaml",
        "markdown",
        "python",
        "bash",
        "javascript",
        "typescript",
        "latex",
        "json",
        "xml",
        "html",
        "css",
        "bibtex",
    ]


def protect_code_content(text: MarkdownContent) -> tuple[LatexContent, dict[str, str]]:
    """Protect code content from further markdown processing.

    Args:
        text: Text that may contain code blocks

    Returns:
        Tuple of (processed_text, protected_content_dict)
    """
    protected_content: dict[str, str] = {}

    def protect_verbatim_content(match: re.Match[str]) -> str:
        verbatim_content = match.group(0)
        placeholder = f"XXPROTECTEDVERBATIMXX{len(protected_content)}XXPROTECTEDVERBATIMXX"
        protected_content[placeholder] = verbatim_content
        return placeholder

    # Protect all verbatim environments from further markdown processing
    text = re.sub(
        r"\\begin\{verbatim\}.*?\\end\{verbatim\}",
        protect_verbatim_content,
        text,
        flags=re.DOTALL,
    )

    # Protect all listings environments from further markdown processing
    text = re.sub(
        r"\\begin\{lstlisting\}\[.*?\].*?\\end\{lstlisting\}",
        protect_verbatim_content,
        text,
        flags=re.DOTALL,
    )

    return text, protected_content


def restore_protected_code(text: LatexContent, protected_content: dict[str, str]) -> LatexContent:
    """Restore protected code content.

    Args:
        text: Text with protected placeholders
        protected_content: Dictionary mapping placeholders to original content

    Returns:
        Text with code content restored
    """
    for placeholder, original_content in protected_content.items():
        text = text.replace(placeholder, original_content)
    return text


def validate_code_block_syntax(code_block: str, language: str = "") -> bool:
    """Validate that a code block has proper syntax.

    Args:
        code_block: The code block content
        language: Optional language identifier

    Returns:
        True if syntax appears valid, False otherwise
    """
    # Basic validation - check for balanced quotes and brackets
    if language.lower() in ["json", "yaml"]:
        # For structured data, check basic balance
        open_braces = code_block.count("{")
        close_braces = code_block.count("}")
        open_brackets = code_block.count("[")
        close_brackets = code_block.count("]")

        return open_braces == close_braces and open_brackets == close_brackets

    # For other languages, just check it's not empty
    return bool(code_block.strip())


def extract_code_blocks_from_text(text: MarkdownContent) -> list[tuple[str, str]]:
    """Extract all code blocks from markdown text.

    Args:
        text: Text to extract code blocks from

    Returns:
        List of tuples (language, code_content) for each code block found
    """
    code_blocks: list[tuple[str, str]] = []

    # Find fenced code blocks
    fenced_pattern = r"^```(\w+)?\n(.*?)\n```$"
    for match in re.finditer(fenced_pattern, text, re.MULTILINE | re.DOTALL):
        language = match.group(1) or ""
        content = match.group(2)
        code_blocks.append((language, content))

    # Find indented code blocks
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        if re.match(r"^    ", lines[i]) and lines[i].strip():
            # Start of indented code block
            code_lines: list[str] = []
            while i < len(lines) and (re.match(r"^    ", lines[i]) or not lines[i].strip()):
                if lines[i].startswith("    "):
                    code_lines.append(lines[i][4:])
                else:
                    code_lines.append(lines[i])
                i += 1

            # Remove trailing empty lines
            while code_lines and not code_lines[-1].strip():
                code_lines.pop()

            if code_lines:
                code_blocks.append(("", "\n".join(code_lines)))
        else:
            i += 1

    return code_blocks
