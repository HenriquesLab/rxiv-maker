"""Text formatting processors for markdown to LaTeX conversion.

This module handles basic text formatting including bold, italic, code,
headers, and special character escaping.
"""

import re

from .types import LatexContent, MarkdownContent

# Pre-compiled regex patterns for performance optimization
# Text formatting patterns
BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*")
ITALIC_PATTERN = re.compile(r"\*(.+?)\*")
UNDERLINE_PATTERN = re.compile(r"__([^_\n]*(?:_[^_\n]*)*?)__")

# Bold/italic patterns with constraints
BOLD_CONSTRAINED_PATTERN = re.compile(r"\*\*([^*]+)\*\*")
ITALIC_CONSTRAINED_PATTERN = re.compile(r"(?<!\*)\*([^*]+?)\*(?!\*)")

# Header patterns
H2_PATTERN = re.compile(r"^## (.+)$", re.MULTILINE)
H3_PATTERN = re.compile(r"^### (.+)$", re.MULTILINE)
H4_PATTERN = re.compile(r"^#### (.+)$", re.MULTILINE)

# Code block patterns
DOUBLE_BACKTICK_PATTERN = re.compile(r"``([^`]+)``")
SINGLE_BACKTICK_PATTERN = re.compile(r"`([^`]+)`")

# LaTeX command patterns
LATEX_COMMAND_PATTERN = re.compile(r"(\\[a-zA-Z]+\{[^}]*\})")
TEXTTT_PATTERN = re.compile(r"(\\texttt\{[^}]*\})")

# Special character patterns
PERCENT_PATTERN = re.compile(r"(?<!\\)(?<!^)%", re.MULTILINE)
CARET_PATTERN = re.compile(r"(?<!\$)(?<!\\\$)\^(?!\^)(?![^$]*\$)")

# File path patterns
PARENS_PATTERN = re.compile(r"\(([^)]+)\)")
UNDERSCORE_ID_PATTERN = re.compile(r"\b\d+_[A-Z_]+\b")

# LaTeX cleanup patterns
DOUBLE_BACKSLASH_SPACED_PATTERN = re.compile(r"\\textbackslash textbackslash\s+")
DOUBLE_BACKSLASH_PATTERN = re.compile(r"\\textbackslash textbackslash")

# Protected environment patterns (will be built dynamically)
_PROTECTED_ENV_PATTERN = None


def _get_protected_env_pattern():
    """Get or create the protected environment pattern."""
    global _PROTECTED_ENV_PATTERN
    if _PROTECTED_ENV_PATTERN is None:
        # Separate non-starred and starred environments for proper backreference matching
        base_environments = [
            "equation",
            "align",
            "gather",
            "multiline",
            "split",
            "verbatim",
            "lstlisting",
            "tabular",
            "tabularx",
            "longtable",
            "array",
            "minipage",
            "figure",
            "sfigure",
            "sidewaysfigure",
        ]

        # Create patterns for both non-starred and starred versions
        patterns = []
        patterns.append("\\\\texttt\\{[^}]*\\}")  # texttt blocks

        for env in base_environments:
            # Non-starred version
            patterns.append(f"\\\\begin\\{{{re.escape(env)}\\}}.*?\\\\end\\{{{re.escape(env)}\\}}")
            # Starred version
            patterns.append(f"\\\\begin\\{{{re.escape(env)}\\*\\}}.*?\\\\end\\{{{re.escape(env)}\\*\\}}")

        # Combine all patterns into one with proper grouping
        pattern = f"({'|'.join(patterns)})"
        _PROTECTED_ENV_PATTERN = re.compile(pattern, re.DOTALL)
    return _PROTECTED_ENV_PATTERN


def _apply_formatting_outside_protected_environments(
    text: MarkdownContent, formatting_pattern: re.Pattern[str], replacement: str, use_full_protection: bool = True
) -> LatexContent:
    r"""Generic function to apply text formatting outside protected environments.

    Args:
        text: Text to process
        formatting_pattern: Pre-compiled regex pattern for the formatting
        replacement: Replacement string (e.g., r"\\textbf{\1}")
        use_full_protection: Whether to use full environment protection (True) or just texttt (False)

    Returns:
        Text with formatting applied outside protected environments
    """
    if use_full_protection:
        # Split by both \texttt{} blocks and LaTeX environments
        protection_pattern = _get_protected_env_pattern()
        parts = protection_pattern.split(text)

        result: list[str] = []
        for part in parts:
            if part is None:
                continue
            if part.startswith("\\texttt{") or part.startswith("\\begin{"):
                # This is a protected block, don't process it
                result.append(part)
            else:
                # This is regular text, apply formatting
                part = formatting_pattern.sub(replacement, part)
                result.append(part)
        return "".join(result)
    else:
        # Split by \texttt{} blocks only
        parts = TEXTTT_PATTERN.split(text)
        result: list[str] = []

        for part in parts:
            if part.startswith("\\texttt{"):
                # This is a texttt block, don't process it
                result.append(part)
            else:
                # This is regular text, apply formatting
                part = formatting_pattern.sub(replacement, part)
                result.append(part)
        return "".join(result)


def convert_subscript_superscript_to_latex(text: LatexContent) -> LatexContent:
    r"""Convert subscript and superscript markdown syntax to LaTeX.

    Avoids converting inside LaTeX commands like \\texttt{}.

    Args:
        text: Text content that may contain subscript and superscript

    Returns:
        LaTeX formatted text with subscript/superscript converted
    """

    # Helper function to avoid replacing inside LaTeX commands
    def replace_outside_commands(pattern, replacement, text):
        """Replace pattern with replacement, but not inside LaTeX commands or math mode."""
        # Combine all protection patterns into a single regex to avoid
        # sequential processing issues where one pattern affects another
        combined_pattern = (
            r"(\\texttt\{[^}]*\})|"  # \texttt{...}
            r"(\\text\{[^}]*\})|"  # \text{...}
            r"(\$[^$]*\$)|"  # Inline math $...$
            r"(\$\$.*?\$\$)|"  # Display math $$...$$
            r"(\\begin\{equation\}.*?\\end\{equation\})"  # equation environments
        )

        # Split by the combined pattern - protected parts will be in groups
        parts = re.split(combined_pattern, text, flags=re.DOTALL)
        result = []

        for part in parts:
            if part is None or part == "":
                continue

            # Check if this part matches any of our protection patterns
            is_protected = (
                part.startswith("\\texttt{")
                or part.startswith("\\text{")
                or (part.startswith("$") and not part.startswith("$$"))
                or part.startswith("$$")
                or part.startswith("\\begin{equation}")
            )

            if not is_protected:
                # Only apply replacement to unprotected parts
                part = re.sub(pattern, replacement, part)

            result.append(part)

        return "".join(result)

    # Convert simple subscript and superscript using markdown-style syntax
    # H~2~O becomes H\textsubscript{2}O
    text = replace_outside_commands(r"~([^~\s]+)~", r"\\textsubscript{\1}", text)
    # E=mc^2^ becomes E=mc\textsuperscript{2}
    text = replace_outside_commands(r"\^([^\^\s]+)\^", r"\\textsuperscript{\1}", text)

    return text


def convert_text_formatting_to_latex(text: MarkdownContent) -> LatexContent:
    """Convert markdown text formatting to LaTeX.

    Args:
        text: Markdown text with formatting

    Returns:
        LaTeX formatted text
    """
    # Convert bold and italic using pre-compiled patterns
    text = BOLD_PATTERN.sub(r"\\textbf{\1}", text)
    text = ITALIC_PATTERN.sub(r"\\textit{\1}", text)

    # Convert underlined text (single line only, don't match across line breaks)
    text = UNDERLINE_PATTERN.sub(r"\\underline{\1}", text)

    # Convert subscript and superscript
    text = convert_subscript_superscript_to_latex(text)

    # Note: Code conversion is handled by process_code_spans function
    # to properly support line breaking for long code spans

    return text


def convert_headers_to_latex(text: MarkdownContent) -> LatexContent:
    """Convert markdown headers to LaTeX sections.

    Args:
        text: Markdown text with headers

    Returns:
        LaTeX text with section commands
    """
    text = H2_PATTERN.sub(r"\\section{\1}", text)
    text = H3_PATTERN.sub(r"\\subsection{\1}", text)
    text = H4_PATTERN.sub(r"\\subsubsection{\1}", text)

    return text


def process_code_spans(text: MarkdownContent) -> LatexContent:
    """Process inline code spans with proper escaping.

    Args:
        text: Text containing inline code spans

    Returns:
        Text with code spans converted to LaTeX
    """

    def process_code_blocks(match: re.Match[str]) -> str:
        code_content = match.group(1)

        # Check if this is a URL - if so, handle it specially
        is_url = (
            code_content.startswith("http://")
            or code_content.startswith("https://")
            or code_content.startswith("ftp://")
        )

        if is_url:
            # For URLs, use the \url command which handles underscores automatically
            return f"\\url{{{code_content}}}"

        # Check if this code span contains mathematical expressions
        # Mathematical expressions should be protected from seqsplit processing
        has_math_delimiters = "$" in code_content
        has_dollar_paren = "$(" in code_content or "$)" in code_content
        # Also check for protected math placeholders (from earlier math protection step)
        has_protected_math = "XXPROTECTEDMATHXX" in code_content

        # Check if this code span contains LaTeX commands that need special protection
        has_latex_commands = "\\" in code_content and any(
            latex_cmd in code_content
            for latex_cmd in [
                "\\textbf",
                "\\textit",
                "\\emph",
                "\\textsubscript",
                "\\textsuperscript",
                "\\section",
                "\\subsection",
                "\\subsubsection",
                "\\cite",
                "\\ref",
                "\\begin",
                "\\end",
                "\\item",
                "\\href",
                "\\url",
                "\\eqref",
                "\\sidenote",
            ]
        )

        # Check if this is a {{tex:...}} or {{py:...}} reference that should be displayed literally
        # Also handle protected tex block placeholders
        is_block_reference = (
            code_content.startswith("{{")
            and code_content.endswith("}}")
            and ("tex:" in code_content or "py:" in code_content)
        ) or code_content.startswith("XXPROTECTEDTEXBLOCKXX")

        # Check if this code span contains Markdown syntax or special characters that need verbatim display
        # Exclude {{tex:...}} and {{py:...}} references from markdown syntax treatment
        has_markdown_syntax = not is_block_reference and any(
            syntax in code_content
            for syntax in [
                "**",  # Bold markdown
                "*",  # Italic markdown (but not if it's just a single asterisk in regular text)
                "~~",  # Strikethrough markdown
                "`",  # Nested backticks
                "~",  # Subscript syntax (when standalone)
                "^",  # Superscript syntax (when standalone)
                "#",  # Header syntax (single hash)
                "##",  # Header syntax
                "###",  # Header syntax
                "@",  # Citation references
                "<!--",  # HTML comments
                "<",  # HTML tags or special syntax
                ">",  # HTML tags or special syntax
                "[",  # Link syntax
                "]",  # Link syntax
            ]
        )

        if is_block_reference:
            # For {{tex:...}} and {{py:...}} references, use detokenize for robust handling
            # This avoids all the brace escaping issues by treating content literally
            return f"\\texttt{{\\detokenize{{{code_content}}}}}"
        elif has_latex_commands or has_markdown_syntax:
            # For code spans with LaTeX commands or Markdown syntax, use \detokenize for true verbatim display
            # This ensures that \textbf{bold text} or **bold text** appears literally in the PDF
            return f"PROTECTED_DETOKENIZE_START{{{code_content}}}PROTECTED_DETOKENIZE_END"
        elif has_dollar_paren or has_math_delimiters or has_protected_math:
            # For code spans with mathematical content, use \detokenize for robust
            # protection. This prevents LaTeX from interpreting $ as math delimiters
            return f"PROTECTED_DETOKENIZE_START{{{code_content}}}PROTECTED_DETOKENIZE_END"
        else:
            # Handle special LaTeX characters inside code spans using standard escaping
            escaped_content = code_content
            # Hash needs to be escaped in LaTeX as it's used for macro params
            escaped_content = escaped_content.replace("#", "\\#")
            # In texttt, underscores need escaping - use placeholder for safety
            escaped_content = escaped_content.replace("_", "XUNDERSCOREX")

            # For Python inline commands containing mathematical operators, handle quotes first
            if (code_content.startswith("{py:") or "py:" in code_content) and any(
                op in code_content for op in ["*", "//", "^", "+", "-", "%"]
            ):
                # Replace single quotes with double quotes for LaTeX compatibility BEFORE escaping braces
                escaped_content = escaped_content.replace("'", '"')

            # For ALL Python inline commands, use consistent handling
            if code_content.startswith("{py:") or "py:" in code_content:
                # For Python commands, keep braces as-is and only escape other special characters
                py_escaped_content = code_content
                py_escaped_content = py_escaped_content.replace("#", "\\#")
                py_escaped_content = py_escaped_content.replace("_", "XUNDERSCOREX")
                # For Python commands with math operators, also replace quotes
                if any(op in code_content for op in ["*", "//", "^", "+", "-", "%"]):
                    py_escaped_content = py_escaped_content.replace("'", '"')
                # Don't escape braces - let them be literal in texttt
                # Use a protected placeholder to avoid further processing
                return f"PROTECTED_PYTHON_COLOR_START{{{py_escaped_content}}}PROTECTED_PYTHON_COLOR_END"

            # For non-Python commands, handle braces normally
            escaped_content = escaped_content.replace("{", "\\{")
            escaped_content = escaped_content.replace("}", "\\}")

            # For very long code spans (>60 characters), use seqsplit inside texttt
            # to allow line breaks while maintaining monospace formatting
            # BUT only if no LaTeX commands (indicated by backslashes)
            # AND not for Python inline commands which should stay readable
            is_python_command = code_content.startswith("{py:") or code_content.startswith("py:")
            if len(code_content) > 60 and "\\" not in code_content and not is_python_command:
                # Use protected placeholder to prevent escaping of \seqsplit command
                return f"PROTECTED_TEXTTT_SEQSPLIT_START{{{escaped_content}}}PROTECTED_TEXTTT_SEQSPLIT_END"
            else:
                return f"\\texttt{{{escaped_content}}}"

    # Process both double and single backticks
    text = DOUBLE_BACKTICK_PATTERN.sub(process_code_blocks, text)  # Double backticks first
    text = SINGLE_BACKTICK_PATTERN.sub(process_code_blocks, text)  # Then single backticks

    # Convert protected detokenize placeholders to actual LaTeX
    def replace_protected_detokenize(match: re.Match[str]) -> str:
        content = match.group(1)
        return f"\\texttt{{\\detokenize{{{content}}}}}"

    # Use a more robust pattern that handles nested braces
    def find_and_replace_detokenize(text: str) -> str:
        result = []
        i = 0
        while i < len(text):
            # Look for PROTECTED_DETOKENIZE_START{
            start_marker = "PROTECTED_DETOKENIZE_START{"
            if text[i : i + len(start_marker)] == start_marker:
                # Find the matching closing brace
                brace_count = 0
                start = i + len(start_marker)
                j = start
                while j < len(text):
                    if text[j] == "{":
                        brace_count += 1
                    elif text[j] == "}":
                        if brace_count == 0:
                            # Found the matching closing brace
                            content = text[start:j]
                            # Check if this is followed by the end marker
                            end_marker = "}PROTECTED_DETOKENIZE_END"
                            if text[j : j + len(end_marker)] == end_marker:
                                # Handle LaTeX commands with braces specially to avoid \detokenize spacing issues
                                if (
                                    content.startswith("\\")
                                    and "{" in content
                                    and "}" in content
                                    and content.count("\\") == 1
                                ):
                                    # For simple LaTeX commands like \textbf{bold text}, use manual approach
                                    # to avoid the space that \detokenize introduces after \textbf
                                    escaped_content = (
                                        content.replace("\\", "\\textbackslash ")
                                        .replace("{", "\\{")
                                        .replace("}", "\\}")
                                    )
                                    replacement = f"\\texttt{{{escaped_content}}}"
                                else:
                                    # For everything else (markdown syntax, simple text), use \detokenize
                                    # This will handle special characters like #, ~, ^ correctly
                                    # Note: \detokenize may double hash characters in PDF but this is better than backslashes
                                    replacement = f"\\texttt{{\\detokenize{{{content}}}}}"
                                result.append(replacement)
                                i = j + len(end_marker)
                                break
                            else:
                                # No matching end marker, treat as regular content
                                result.append(text[i])
                                i += 1
                                break
                        else:
                            brace_count -= 1
                    j += 1
                else:
                    # No matching brace found, just add the original text
                    result.append(text[i])
                    i += 1
            else:
                result.append(text[i])
                i += 1
        return "".join(result)

    text = find_and_replace_detokenize(text)

    # Convert protected Python color placeholders to actual LaTeX
    text = find_and_replace_python_color(text)

    return text


def apply_bold_italic_formatting(text: MarkdownContent) -> LatexContent:
    """Apply bold and italic formatting while protecting LaTeX commands.

    Args:
        text: Text to format

    Returns:
        Formatted text with LaTeX commands protected
    """

    def safe_bold_replace(match: re.Match[str]) -> str:
        bold_content = match.group(1)
        return f"\\textbf{{{bold_content}}}"

    def safe_italic_replace(match: re.Match[str]) -> str:
        italic_content = match.group(1)
        return f"\\textit{{{italic_content}}}"

    # Replace bold/italic but skip if inside LaTeX commands
    # Split by LaTeX commands and only process text parts
    parts = LATEX_COMMAND_PATTERN.split(text)
    processed_parts: list[str] = []

    for i, part in enumerate(parts):
        if i % 2 == 0:  # This is regular text, not a LaTeX command
            # Apply bold/italic formatting
            part = re.sub(r"\*\*(.+?)\*\*", safe_bold_replace, part)
            part = re.sub(r"\*(.+?)\*", safe_italic_replace, part)
        # If i % 2 == 1, it's a LaTeX command - leave it unchanged
        processed_parts.append(part)

    return "".join(processed_parts)


def protect_bold_outside_texttt(text: MarkdownContent) -> LatexContent:
    """Apply bold formatting only outside texttt blocks.

    Args:
        text: Text to process

    Returns:
        Text with bold formatting applied outside code blocks
    """
    return _apply_formatting_outside_protected_environments(
        text, BOLD_CONSTRAINED_PATTERN, r"\\textbf{\1}", use_full_protection=False
    )


def protect_italic_outside_texttt(text: MarkdownContent) -> LatexContent:
    """Apply italic formatting only outside texttt blocks and LaTeX environments.

    Args:
        text: Text to process

    Returns:
        Text with italic formatting applied outside code blocks and LaTeX environments
    """
    return _apply_formatting_outside_protected_environments(
        text, ITALIC_CONSTRAINED_PATTERN, r"\\textit{\1}", use_full_protection=True
    )


def protect_underline_outside_texttt(text: MarkdownContent) -> LatexContent:
    """Apply underline formatting only outside texttt blocks and specific LaTeX environments.

    Args:
        text: Text to process

    Returns:
        Text with underline formatting applied outside code blocks and protected LaTeX environments
    """
    return _apply_formatting_outside_protected_environments(
        text, UNDERLINE_PATTERN, r"\\underline{\1}", use_full_protection=True
    )


def escape_special_characters(text: MarkdownContent) -> LatexContent:
    """Escape special LaTeX characters in text.

    Args:
        text: Text to escape

    Returns:
        Text with LaTeX special characters escaped
    """
    # First, handle all specific cases that contain listings environments
    # This handles the nested brace issue where regex fails

    # Find all texttt environments that contain listings
    def replace_listings_texttt(text: str) -> str:
        # Simple approach: find texttt blocks with listings and replace with verb
        import re

        # Find all \texttt{...} blocks
        def process_texttt_block(match):
            full_content = match.group(1)

            # If this texttt block contains listings, replace with verb
            if "\\begin{lstlisting}" in full_content:
                # Use verb with a delimiter that's not in the content
                delimiters = [
                    "|",
                    "!",
                    "@",
                    "#",
                    "$",
                    "%",
                    "^",
                    "&",
                    "*",
                    "+",
                    "=",
                    "~",
                ]
                delimiter = "|"
                for d in delimiters:
                    if d not in full_content:
                        delimiter = d
                        break
                return f"\\verb{delimiter}{full_content}{delimiter}"
            else:
                # Return unchanged
                return f"\\texttt{{{full_content}}}"

        # Use re.DOTALL to match across newlines, and handle nested braces properly
        # This pattern handles one level of nested braces without ReDoS vulnerability
        pattern = r"\\texttt\{([^{}]*(?:\{[^}]*\}[^{}]*)*)\}"
        text = re.sub(pattern, process_texttt_block, text, flags=re.DOTALL)

        return text

    text = replace_listings_texttt(text)

    # IMPORTANT: Protect LaTeX commands FIRST before any underscore escaping
    # Protect LaTeX reference commands that should not have underscores escaped
    # These commands use identifiers that often contain underscores (like fig:name_with_underscores)
    protected_latex_commands: dict[str, str] = {}

    def protect_latex_command(match: re.Match[str]) -> str:
        """Replace LaTeX command with placeholder."""
        command = match.group(0)
        placeholder = f"XXPROTECTEDLATEXCOMMANDXX{len(protected_latex_commands)}XXPROTECTEDLATEXCOMMANDXX"
        protected_latex_commands[placeholder] = command
        return placeholder

    # CRITICAL: Protect content that's already been processed by table_processor
    # The table processor uses \detokenize{} for complex cases - don't touch these
    # Protect \texttt{\detokenize{...}} commands (from table processor)
    # Use a more robust pattern that handles nested braces, including triple braces like {{{tex:...}}}
    text = re.sub(
        r"\\texttt\{\\detokenize\{[^{}]*(?:\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}[^{}]*)*\}\}", protect_latex_command, text
    )

    # Protect standalone \detokenize{...} commands
    text = re.sub(r"\\detokenize\{[^}]*\}", protect_latex_command, text)

    # Protect \includegraphics{} commands
    text = re.sub(r"\\includegraphics\[[^\]]*\]\{[^}]*\}", protect_latex_command, text)

    latex_ref_commands = [
        r"\\ref\{[^}]*\}",  # \ref{fig:name_with_underscores}
        r"\\eqref\{[^}]*\}",  # \eqref{eq:name_with_underscores}
        r"\\label\{[^}]*\}",  # \label{fig:name_with_underscores}
        r"\\pageref\{[^}]*\}",  # \pageref{sec:name_with_underscores}
        r"\\cite\{[^}]*\}",  # \cite{author_2024}
        r"\\citep\{[^}]*\}",  # \citep{author_2024}
        r"\\citet\{[^}]*\}",  # \citet{author_2024}
        r"\\citealt\{[^}]*\}",  # \citealt{author_2024}
        r"\\cref\{[^}]*\}",  # \cref{fig:name_with_underscores} (cleveref)
        r"\\Cref\{[^}]*\}",  # \Cref{fig:name_with_underscores} (cleveref)
    ]

    for pattern in latex_ref_commands:
        text = re.sub(pattern, protect_latex_command, text)

    # Then apply the general function for other cases
    # Escape special characters in texttt commands
    def escape_specials_in_texttt_content(content: str) -> str:
        # Special handling for URL commands - they should not be wrapped in texttt
        if content.startswith("\\url{") and content.endswith("}"):
            # This is already a URL command, return it as-is
            return content

        # Special handling for content that contains URL commands
        if "\\url{" in content:
            # Don't wrap content containing URL commands in texttt to avoid nesting
            # Just return the content as-is since URLs are already properly formatted
            return content

        # Special handling for listings environments - they interfere with texttt
        if "\\begin{lstlisting}" in content or "\\end{lstlisting}" in content:
            # Use verb instead of texttt for listings content
            # Find a delimiter that's not in the content
            delimiters = ["|", "!", "@", "#", "$", "%", "^", "&", "*", "+", "=", "~"]
            delimiter = "|"
            for d in delimiters:
                if d not in content:
                    delimiter = d
                    break
            return f"\\verb{delimiter}{content}{delimiter}"
        # Special handling for detokenize commands - don't escape the backslashes
        elif "\\detokenize{" in content:
            # This content already has detokenize, just return it wrapped in texttt
            return f"\\texttt{{{content}}}"
        # Special handling for LaTeX command protected content - don't escape backslashes
        elif "LATEXCMD_PROTECTED_START{" in content and "}LATEXCMD_PROTECTED_END" in content:
            # Extract the protected content and return it as-is
            start_marker = "LATEXCMD_PROTECTED_START{"
            end_marker = "}LATEXCMD_PROTECTED_END"
            start_idx = content.find(start_marker)
            end_idx = content.find(end_marker)
            if start_idx != -1 and end_idx != -1:
                protected_content = content[start_idx + len(start_marker) : end_idx]
                return f"\\texttt{{{protected_content}}}"
            # Fallback if markers are malformed
            return f"\\texttt{{{content}}}"
        else:
            # For other backslashes, use textbackslash
            # Skip processing if text already contains any form of textbackslash (already escaped)
            if "textbackslash" not in content:
                content = content.replace("\\", "\\textbackslash ")

        # Escape # characters only if not already escaped
        if "\\#" not in content:
            content = content.replace("#", "\\#")
        return f"\\texttt{{{content}}}"

    # Use a more sophisticated approach to handle nested braces
    def find_and_replace_texttt(text: str) -> str:
        result = []
        i = 0
        while i < len(text):
            # Look for \texttt{
            if text[i : i + 8] == "\\texttt{":
                # Find the matching closing brace
                brace_count = 0
                start = i + 8
                j = start
                while j < len(text):
                    if text[j] == "{":
                        brace_count += 1
                    elif text[j] == "}":
                        if brace_count == 0:
                            # Found the matching closing brace
                            content = text[start:j]
                            replacement = escape_specials_in_texttt_content(content)
                            result.append(replacement)
                            i = j + 1
                            break
                        else:
                            brace_count -= 1
                    j += 1
                else:
                    # No matching brace found, just add the original text
                    result.append(text[i])
                    i += 1
            else:
                result.append(text[i])
                i += 1
        return "".join(result)

    text = find_and_replace_texttt(text)

    # Handle underscores carefully - LaTeX is very picky about this
    # We need to escape underscores in text mode but NOT double-escape them

    # Handle remaining underscores in file paths within parentheses
    def escape_file_paths_in_parens(match: re.Match[str]) -> str:
        paren_content = match.group(1)
        # Only escape if it looks like a file path (has extension or
        # is all caps directory)
        if ("." in paren_content and "_" in paren_content) or (
            paren_content.endswith(".md")
            or paren_content.endswith(".bib")
            or paren_content.endswith(".tex")
            or paren_content.endswith(".py")
            or paren_content.endswith(".csv")
        ):
            return f"({paren_content.replace('_', 'XUNDERSCOREX')})"
        return match.group(0)

    text = PARENS_PATTERN.sub(escape_file_paths_in_parens, text)

    # Handle remaining underscores in file names and paths
    # Match common filename patterns: WORD_WORD.ext, word_word.ext, etc.
    def escape_filenames(match: re.Match[str]) -> str:
        filename = match.group(0)
        # Escape underscores in anything that looks like a filename
        return filename.replace("_", "XUNDERSCOREX")

    # Match filenames with extensions
    text = re.sub(
        r"\b[\w]+_[\w._]*\.(md|yml|yaml|bib|tex|py|csv|pdf|png|svg|jpg)\b",
        escape_filenames,
        text,
    )

    # Also match numbered files like 00_CONFIG, 01_MAIN, etc.
    text = UNDERSCORE_ID_PATTERN.sub(escape_filenames, text)

    # Escape percent signs in text (but not in comments that start with %)
    # Use a regex to avoid escaping percent signs at the start of lines (which are comments)
    text = PERCENT_PATTERN.sub(r"\\%", text)

    # Final step: replace all placeholders with properly escaped underscores
    text = text.replace("XUNDERSCOREX", "\\_")

    # Restore protected LaTeX commands after escaping
    for placeholder, original_command in protected_latex_commands.items():
        text = text.replace(placeholder, original_command)

    # Handle special characters that can cause LaTeX issues
    # Escape caret character outside of math mode and texttt blocks
    def escape_carets_outside_protected_contexts(text):
        """Escape carets but not inside LaTeX commands or math mode."""
        # Combine all protection patterns into a single regex
        combined_pattern = (
            r"(\\texttt\{[^}]*\})|"  # \texttt{...}
            r"(\\text\{[^}]*\})|"  # \text{...}
            r"(\$[^$]*\$)|"  # Inline math $...$
            r"(\$\$.*?\$\$)|"  # Display math $$...$$
            r"(\\begin\{equation\}.*?\\end\{equation\})"  # equation environments
        )

        # Split by the combined pattern - protected parts will be in groups
        parts = re.split(combined_pattern, text, flags=re.DOTALL)
        result = []

        for part in parts:
            if part is None or part == "":
                continue

            # Check if this part matches any of our protection patterns
            is_protected = (
                part.startswith("\\texttt{")
                or part.startswith("\\text{")
                or (part.startswith("$") and not part.startswith("$$"))
                or part.startswith("$$")
                or part.startswith("\\begin{equation}")
            )

            if not is_protected:
                # Only escape carets in unprotected parts
                # Only escape isolated carets that aren't already in math mode
                part = CARET_PATTERN.sub(r"\\textasciicircum{}", part)

            result.append(part)

        return "".join(result)

    text = escape_carets_outside_protected_contexts(text)

    # Handle Unicode arrows that can cause LaTeX math mode issues
    # Use safe text replacements that work in all contexts
    text = text.replace("→", " to ")  # Simple text replacement
    text = text.replace("←", " from ")
    text = text.replace("↑", " up ")
    text = text.replace("↓", " down ")

    # Clean up double escaping that may have occurred during table processing
    text = _cleanup_double_escaping_textformatters(text)

    return text


def _cleanup_double_escaping_textformatters(text: str) -> str:
    r"""Clean up double-escaped backslashes in texttt environments.

    Fixes patterns like \\textbackslash{}textbackslash that break LaTeX parsing.
    """
    # Fix the specific pattern of double-escaped backslashes
    # Replace \\textbackslash textbackslash (with space) with just \\textbackslash using pre-compiled patterns
    text = DOUBLE_BACKSLASH_SPACED_PATTERN.sub(r"\\textbackslash ", text)

    # Also try without requiring space after
    text = DOUBLE_BACKSLASH_PATTERN.sub(r"\\textbackslash ", text)

    return text


def restore_protected_seqsplit(text: LatexContent) -> LatexContent:
    """Restore protected seqsplit commands after special character escaping.

    Args:
        text: LaTeX content with protected seqsplit placeholders

    Returns:
        LaTeX content with seqsplit commands restored
    """
    # Handle both escaped and non-escaped versions of the placeholders
    for start_marker, end_marker in [
        ("PROTECTED_TEXTTT_SEQSPLIT_START{", "PROTECTED_TEXTTT_SEQSPLIT_END"),
        (
            "PROTECTED\\_TEXTTT\\_SEQSPLIT\\_START{",
            "PROTECTED\\_TEXTTT\\_SEQSPLIT\\_END",
        ),
    ]:
        while start_marker in text:
            start_pos = text.find(start_marker)
            if start_pos == -1:
                break

            # Find the matching end marker
            content_start = start_pos + len(start_marker)
            brace_count = 1
            pos = content_start

            while pos < len(text) and brace_count > 0:
                if text[pos] == "{":
                    brace_count += 1
                elif text[pos] == "}":
                    brace_count -= 1
                pos += 1

            if brace_count == 0:
                content_end = pos - 1
                content = text[content_start:content_end]

                # Check if this is followed by the end marker
                remaining = text[pos:]
                if remaining.startswith(end_marker):
                    end_marker_end = pos + len(end_marker)

                    # Replace XUNDERSCOREX back to actual underscores
                    content = content.replace("XUNDERSCOREX", "\\_")

                    # Replace with seqsplit
                    replacement = f"\\texttt{{\\seqsplit{{{content}}}}}"
                    text = text[:start_pos] + replacement + text[end_marker_end:]
                else:
                    # If no matching end marker, break to avoid infinite loop
                    break
            else:
                # If braces don't match, break to avoid infinite loop
                break

    return text


def identify_long_technical_identifiers(text: LatexContent, min_length: int = 15) -> LatexContent:
    """Wrap long technical identifiers with seqsplit for better line breaking.

    This function identifies long alphanumeric identifiers (gene names, protein names,
    method names, etc.) and wraps them with LaTeX's seqsplit command to allow
    proper line breaking in scientific documents.

    Args:
        text: Input text that may contain long technical identifiers
        min_length: Minimum length for identifiers to be wrapped (default: 15)

    Returns:
        Text with long identifiers wrapped in seqsplit commands
    """
    # Avoid processing inside LaTeX commands, math mode, or existing seqsplit
    # Pattern to match areas to protect from modification
    protect_pattern = (
        r"(\\[a-zA-Z]+\{[^}]*\})|"  # LaTeX commands like \cite{...}, \texttt{...}
        r"(\$[^$]*\$)|"  # Math mode $...$
        r"(\\seqsplit\{[^}]*\})"  # Existing seqsplit commands
    )

    protected_areas = []
    for match in re.finditer(protect_pattern, text):
        protected_areas.append((match.start(), match.end()))

    def is_protected(start, end):
        """Check if a position range is within a protected area."""
        for pstart, pend in protected_areas:
            if start >= pstart and end <= pend:
                return True
        return False

    # Pattern for long technical identifiers
    # Matches alphanumeric strings with underscores, dots, or mixed case
    identifier_pattern = r"\b[A-Za-z][A-Za-z0-9_.]*[A-Za-z0-9][A-Za-z0-9_.]*\b"

    def replace_identifier(match):
        identifier = match.group()
        start, end = match.span()

        # Skip if in protected area
        if is_protected(start, end):
            return identifier

        # Skip if already wrapped or too short
        if len(identifier) < min_length:
            return identifier

        return f"\\seqsplit{{{identifier}}}"

    result = re.sub(identifier_pattern, replace_identifier, text)
    return result


def wrap_long_strings_in_context(text: LatexContent, min_length: int = 20) -> LatexContent:
    """Wrap long strings that appear after contextual keywords.

    This function looks for long strings that appear after certain contextual
    keywords (like "algorithm", "method", "protocol") and wraps them with seqsplit.

    Args:
        text: Input text to process
        min_length: Minimum length for strings to be wrapped (default: 20)

    Returns:
        Text with contextual long strings wrapped in seqsplit
    """
    # Keywords that often precede technical identifiers
    context_keywords = [
        r"\balgorithm\s+",
        r"\bmethod\s+",
        r"\bprotocol\s+",
        r"\btool\s+",
        r"\bsoftware\s+",
        r"\bpackage\s+",
        r"\blibrary\s+",
    ]

    # Protect same areas as the identifier function
    protect_pattern = (
        r"(\\[a-zA-Z]+\{[^}]*\})|"  # LaTeX commands
        r"(\$[^$]*\$)|"  # Math mode
        r"(\\seqsplit\{[^}]*\})"  # Existing seqsplit
    )

    protected_areas = []
    for match in re.finditer(protect_pattern, text):
        protected_areas.append((match.start(), match.end()))

    def is_protected(start, end):
        """Check if a position range is within a protected area."""
        for pstart, pend in protected_areas:
            if start >= pstart and end <= pend:
                return True
        return False

    result = text
    for keyword in context_keywords:
        # Pattern to match keyword followed by a long identifier
        pattern = f"({keyword})([A-Za-z][A-Za-z0-9_.]*)"

        def replace_contextual(match):
            keyword_part = match.group(1)
            identifier = match.group(2)
            start, end = match.span()

            # Skip if in protected area
            if is_protected(start, end):
                return match.group()

            # Only wrap if identifier is long enough
            if len(identifier) >= min_length:
                return f"{keyword_part}\\seqsplit{{{identifier}}}"
            else:
                return match.group()

        result = re.sub(pattern, replace_contextual, result, flags=re.IGNORECASE)

    return result


def find_and_replace_python_color(text: str) -> str:
    """Convert protected Python color placeholders to actual LaTeX."""
    result = []
    i = 0
    while i < len(text):
        # Look for PROTECTED_PYTHON_COLOR_START{
        start_marker = "PROTECTED_PYTHON_COLOR_START{"
        if text[i : i + len(start_marker)] == start_marker:
            # Find the matching closing brace
            brace_count = 0
            start = i + len(start_marker)
            j = start
            while j < len(text):
                if text[j] == "{":
                    brace_count += 1
                elif text[j] == "}":
                    if brace_count == 0:
                        # Found the matching closing brace
                        content = text[start:j]
                        # Look for the end marker
                        end_marker = "}PROTECTED_PYTHON_COLOR_END"
                        if text[j : j + len(end_marker)] == end_marker:
                            # Replace XUNDERSCOREX back to actual underscores
                            content = content.replace("XUNDERSCOREX", "\\_")
                            # Create Python code with literal braces (no color for now)
                            result.append(f"\\texttt{{{content}}}")
                            i = j + len(end_marker)
                            break
                    else:
                        brace_count -= 1
                j += 1
            else:
                # No matching end found, append character and continue
                result.append(text[i])
                i += 1
        else:
            result.append(text[i])
            i += 1
    return "".join(result)
