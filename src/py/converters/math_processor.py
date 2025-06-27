"""Math processing for markdown to LaTeX conversion.

This module handles mathematical expressions in markdown, preserving LaTeX math
notation while converting surrounding content.
"""

import re

from .types import LatexContent, MarkdownContent


def protect_math_expressions(
    content: MarkdownContent,
) -> tuple[LatexContent, dict[str, str]]:
    """Protect mathematical expressions from other markdown processing.

    Args:
        content: Markdown content containing math expressions

    Returns:
        Tuple of (content with math protected, dict of protected math)
    """
    protected_math: dict[str, str] = {}

    def protect_math(match: re.Match[str]) -> str:
        """Replace math expression with placeholder."""
        math_expr = match.group(0)
        placeholder = f"XXPROTECTEDMATHXX{len(protected_math)}XXPROTECTEDMATHXX"
        protected_math[placeholder] = math_expr
        return placeholder

    # Protect display math ($$...$$) first - must be done before inline math
    content = re.sub(r"\$\$.*?\$\$", protect_math, content, flags=re.DOTALL)

    # Protect inline math ($...$)
    # Use negative lookbehind/lookahead to avoid matching display math delimiters
    content = re.sub(r"(?<!\$)\$(?!\$)([^$\n]+?)(?<!\$)\$(?!\$)", protect_math, content)

    return content, protected_math


def restore_math_expressions(
    content: LatexContent, protected_math: dict[str, str]
) -> LatexContent:
    """Restore protected mathematical expressions.

    Args:
        content: Content with math placeholders
        protected_math: Dictionary mapping placeholders to original math

    Returns:
        Content with math expressions restored
    """
    import re

    for placeholder, math_expr in protected_math.items():
        # Check if this placeholder is inside a texttt context
        # Find all occurrences of the placeholder
        start = 0
        while True:
            pos = content.find(placeholder, start)
            if pos == -1:
                break

            # Check if this occurrence is inside \texttt{...} or \seqsplit{...}
            # Look backward to find if we're inside texttt or seqsplit
            before = content[:pos]

            # Find most recent \texttt{, \seqsplit{, or \detokenize{ before position
            texttt_match = None
            seqsplit_match = None
            detokenize_match = None

            for match in re.finditer(r"\\texttt\{", before):
                texttt_match = match
            for match in re.finditer(r"\\seqsplit\{", before):
                seqsplit_match = match
            for match in re.finditer(r"\\detokenize\{", before):
                detokenize_match = match

            # Check if we're inside a texttt, seqsplit, or detokenize context
            in_seqsplit_context = False
            in_detokenize_context = False

            if texttt_match or seqsplit_match or detokenize_match:
                # Find the most recent opening brace and determine context type
                last_brace_pos = -1
                context_type = None

                if texttt_match:
                    last_brace_pos = max(last_brace_pos, texttt_match.end() - 1)
                    context_type = "texttt"
                if seqsplit_match and seqsplit_match.end() - 1 > last_brace_pos:
                    last_brace_pos = seqsplit_match.end() - 1
                    context_type = "seqsplit"
                if detokenize_match and detokenize_match.end() - 1 > last_brace_pos:
                    last_brace_pos = detokenize_match.end() - 1
                    context_type = "detokenize"

                if last_brace_pos != -1:
                    # Count braces to see if we're still inside
                    brace_count = 0
                    for i in range(last_brace_pos, pos):
                        if content[i] == "{":
                            brace_count += 1
                        elif content[i] == "}":
                            brace_count -= 1

                    if brace_count > 0:
                        if context_type == "seqsplit":
                            in_seqsplit_context = True
                        elif context_type == "detokenize":
                            in_detokenize_context = True

            # Replace with appropriate content
            if in_seqsplit_context:
                # Escape dollar signs for seqsplit context
                escaped_math = math_expr.replace("$", "\\$")
                content = (
                    content[:pos] + escaped_math + content[pos + len(placeholder) :]
                )
                start = pos + len(escaped_math)
            elif in_detokenize_context:
                # Don't escape for detokenize context - it handles literal display
                content = content[:pos] + math_expr + content[pos + len(placeholder) :]
                start = pos + len(math_expr)
            else:
                # Normal replacement
                content = content[:pos] + math_expr + content[pos + len(placeholder) :]
                start = pos + len(math_expr)

    return content


def process_latex_math_blocks(content: MarkdownContent) -> LatexContent:
    """Process LaTeX math blocks in markdown content.

    This function handles LaTeX math environments that might be embedded
    in markdown content, ensuring they are properly preserved.

    Args:
        content: Markdown content potentially containing LaTeX math blocks

    Returns:
        Content with LaTeX math blocks processed
    """
    # LaTeX math environments to preserve
    math_environments = [
        "align",
        "align*",
        "equation",
        "equation*",
        "gather",
        "gather*",
        "multiline",
        "multiline*",
        "split",
        "array",
        "matrix",
        "pmatrix",
        "bmatrix",
        "vmatrix",
        "Vmatrix",
    ]

    # Protect LaTeX math environments from markdown processing
    protected_envs: dict[str, str] = {}

    def protect_env(match: re.Match[str]) -> str:
        """Replace LaTeX environment with placeholder."""
        env_content = match.group(0)
        placeholder = (
            f"XXPROTECTEDLATEXMATHXX{len(protected_envs)}XXPROTECTEDLATEXMATHXX"
        )
        protected_envs[placeholder] = env_content
        return placeholder

    # Protect each math environment
    for env in math_environments:
        pattern = rf"\\begin\{{{env}\*?\}}.*?\\end\{{{env}\*?\}}"
        content = re.sub(pattern, protect_env, content, flags=re.DOTALL)

    # Process the content (this would be where other markdown processing happens)
    # For now, we just restore the environments

    # Restore protected environments
    for placeholder, env_content in protected_envs.items():
        content = content.replace(placeholder, env_content)

    return content


def convert_math_markdown_to_latex(content: MarkdownContent) -> LatexContent:
    """Convert markdown content with math expressions to LaTeX.

    This is the main entry point for math processing. It handles enhanced
    markdown-like math syntax and protects math expressions during conversion.

    Args:
        content: Markdown content with potential math expressions

    Returns:
        LaTeX content with math expressions preserved and converted
    """
    # First process enhanced math blocks ($$...$$ {#eq:id})
    content = process_enhanced_math_blocks(content)

    # Then protect inline and display math
    content, protected_math = protect_math_expressions(content)

    # At this point, other markdown processors would run
    # Math expressions are protected from interference

    # Finally restore all math expressions
    content = restore_math_expressions(content, protected_math)

    return content


def parse_math_block_attributes(attr_string: str) -> dict[str, str]:
    """Parse math block attributes like {#eq:id .align}.

    Args:
        attr_string: String containing math block attributes

    Returns:
        Dictionary of parsed attributes including 'id' and 'environment'
    """
    attributes = {}

    # Extract ID (starts with #)
    id_match = re.search(r"#([a-zA-Z0-9_:-]+)", attr_string)
    if id_match:
        attributes["id"] = id_match.group(1)

    # Extract environment/class (starts with .)
    env_match = re.search(r"\.([a-zA-Z]+)", attr_string)
    if env_match:
        attributes["environment"] = env_match.group(1)
    else:
        # Default to equation if ID is provided but no environment specified
        if "id" in attributes:
            attributes["environment"] = "equation"

    return attributes


def convert_attributed_math_blocks(content: MarkdownContent) -> LatexContent:
    r"""Convert markdown-style attributed math blocks to LaTeX environments.

    Converts patterns like:
    $$F = ma$$ {#eq:newton} → \begin{equation}\label{eq:newton}F = ma\end{equation}
    $$....$$ {#eq:id .align} → \begin{align}\label{eq:id}....\end{align}

    Args:
        content: Markdown content containing attributed math blocks

    Returns:
        Content with attributed math blocks converted to LaTeX
    """

    def convert_math_block(match: re.Match[str]) -> str:
        """Convert a single attributed math block."""
        math_content = match.group(1).strip()
        attr_string = match.group(2)

        attributes = parse_math_block_attributes(attr_string)

        if "id" not in attributes:
            # No ID specified, return as regular display math
            return f"$${math_content}$$"

        equation_id = attributes["id"]
        environment = attributes.get("environment", "equation")

        # Handle special cases for environment names
        if environment == "unnumbered":
            # Use equation* for unnumbered equations
            return f"\\begin{{equation*}}\n{math_content}\n\\end{{equation*}}"
        elif environment in ["equation", "align", "gather", "multiline"]:
            # Standard numbered environments
            return (
                f"\\begin{{{environment}}}\n{math_content}\n"
                f"\\label{{{equation_id}}}\n\\end{{{environment}}}"
            )
        else:
            # Default to equation for unknown environments
            return (
                f"\\begin{{equation}}\n{math_content}\n"
                f"\\label{{{equation_id}}}\n\\end{{equation}}"
            )

    # Pattern to match ONLY $$...$$ followed by attributes containing #
    # This ensures we only process attributed math blocks, not regular ones
    # The \s* allows for optional whitespace between $$ and {
    pattern = r"\$\$(.*?)\$\$\s*\{([^}]*#[^}]*)\}"

    content = re.sub(pattern, convert_math_block, content, flags=re.DOTALL)

    return content


def process_enhanced_math_blocks(content: MarkdownContent) -> LatexContent:
    """Process both attributed math blocks and standard LaTeX math environments.

    This function handles the enhanced markdown-like math syntax while preserving
    existing LaTeX math environments for backward compatibility.

    Args:
        content: Markdown content with potential enhanced math syntax

    Returns:
        Content with enhanced math blocks processed
    """
    # First convert attributed math blocks to LaTeX environments
    content = convert_attributed_math_blocks(content)

    # Then protect all LaTeX math environments (including newly created ones)
    content = process_latex_math_blocks(content)

    return content


# Export the main functions
__all__ = [
    "protect_math_expressions",
    "restore_math_expressions",
    "process_latex_math_blocks",
    "convert_math_markdown_to_latex",
    "parse_math_block_attributes",
    "convert_attributed_math_blocks",
    "process_enhanced_math_blocks",
]
