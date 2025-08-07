"""Text formatting processors for markdown to LaTeX conversion.

This module handles basic text formatting including bold, italic, code,
headers, and special character escaping.
"""

import re

from .types import LatexContent, MarkdownContent


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
    # Convert bold and italic
    text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"\*(.+?)\*", r"\\textit{\1}", text)

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
    text = re.sub(r"^## (.+)$", r"\\section{\1}", text, flags=re.MULTILINE)
    text = re.sub(r"^### (.+)$", r"\\subsection{\1}", text, flags=re.MULTILINE)
    text = re.sub(r"^#### (.+)$", r"\\subsubsection{\1}", text, flags=re.MULTILINE)

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

        # Check if this code span contains mathematical expressions
        # Mathematical expressions should be protected from seqsplit processing
        has_math_delimiters = "$" in code_content
        has_dollar_paren = "$(" in code_content or "$)" in code_content

        if has_dollar_paren or has_math_delimiters:
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

            # For long code spans (>20 characters), use seqsplit inside texttt
            # to allow line breaks while maintaining monospace formatting
            # BUT only if no LaTeX commands (indicated by backslashes)
            if len(code_content) > 20 and "\\" not in code_content:
                # Use protected placeholder to prevent escaping of \seqsplit command
                return f"PROTECTED_TEXTTT_SEQSPLIT_START{{{escaped_content}}}PROTECTED_TEXTTT_SEQSPLIT_END"
            else:
                return f"\\texttt{{{escaped_content}}}"

    # Process both double and single backticks
    text = re.sub(r"``([^`]+)``", process_code_blocks, text)  # Double backticks first
    text = re.sub(r"`([^`]+)`", process_code_blocks, text)  # Then single backticks

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
    parts = re.split(r"(\\[a-zA-Z]+\{[^}]*\})", text)
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
    # Split by \texttt{} blocks and process only non-texttt parts
    parts = re.split(r"(\\texttt\{[^}]*\})", text)
    result: list[str] = []

    for _i, part in enumerate(parts):
        if part.startswith("\\texttt{"):
            # This is a texttt block, don't process it
            result.append(part)
        else:
            # This is regular text, apply bold formatting
            part = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", part)
            result.append(part)
    return "".join(result)


def protect_italic_outside_texttt(text: MarkdownContent) -> LatexContent:
    """Apply italic formatting only outside texttt blocks and LaTeX environments.

    Args:
        text: Text to process

    Returns:
        Text with italic formatting applied outside code blocks and LaTeX environments
    """
    # Split by both \texttt{} blocks and LaTeX environments
    # This regex captures \texttt{} and LaTeX environments (\begin{...}...\end{...})
    pattern = r"(\\texttt\{[^}]*\}|\\begin\{[^}]*\*?\}.*?\\end\{[^}]*\*?\})"
    parts = re.split(pattern, text, flags=re.DOTALL)
    result: list[str] = []

    for _i, part in enumerate(parts):
        if part.startswith("\\texttt{") or part.startswith("\\begin{"):
            # This is a texttt block or LaTeX environment, don't process it
            result.append(part)
        else:
            # This is regular text, apply italic formatting
            # Process italic markers - handle various contexts including list items
            part = re.sub(
                r"(?<!\*)\*([^*]+?)\*(?!\*)",
                r"\\textit{\1}",
                part,
            )
            result.append(part)
    return "".join(result)


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

        # Debug output
        if "\\texttt{" in text and "\\begin{lstlisting}" in text:
            print("DEBUG: escape_special_characters found texttt with listings in text")

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
                print(f"DEBUG: Converting texttt with listings to verb: {full_content[:50]}...")
                return f"\\verb{delimiter}{full_content}{delimiter}"
            else:
                # Return unchanged
                return f"\\texttt{{{full_content}}}"

        # Use re.DOTALL to match across newlines, and handle nested braces properly
        # This pattern handles one level of nested braces
        pattern = r"\\texttt\{((?:[^{}]*(?:\{[^}]*\})*[^{}]*)*)\}"
        text = re.sub(pattern, process_texttt_block, text, flags=re.DOTALL)

        return text
        text = re.sub(pattern, process_texttt_block, text, flags=re.DOTALL)

        return text

    text = replace_listings_texttt(text)

    # Then apply the general function for other cases
    # Escape special characters in texttt commands
    def escape_specials_in_texttt_content(content: str) -> str:
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
        else:
            # For other backslashes, use textbackslash
            content = content.replace("\\", "\\textbackslash{}")

        # Escape # characters
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

    text = re.sub(r"\(([^)]+)\)", escape_file_paths_in_parens, text)

    # Protect LaTeX commands (like \includegraphics{}) from underscore escaping
    protected_latex_commands: dict[str, str] = {}

    def protect_latex_command(match: re.Match[str]) -> str:
        """Replace LaTeX command with placeholder."""
        command = match.group(0)
        placeholder = f"XXPROTECTEDLATEXCOMMANDXX{len(protected_latex_commands)}XXPROTECTEDLATEXCOMMANDXX"
        protected_latex_commands[placeholder] = command
        return placeholder

    # Protect \includegraphics{} commands
    text = re.sub(r"\\includegraphics\[[^\]]*\]\{[^}]*\}", protect_latex_command, text)

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
    text = re.sub(r"\b\d+_[A-Z_]+\b", escape_filenames, text)

    # Final step: replace all placeholders with properly escaped underscores
    text = text.replace("XUNDERSCOREX", "\\_")

    # Restore protected LaTeX commands after escaping
    for placeholder, original_command in protected_latex_commands.items():
        text = text.replace(placeholder, original_command)

    # Handle Unicode arrows that can cause LaTeX math mode issues
    # These need to be converted to proper LaTeX math commands
    text = text.replace("→", "$\\rightarrow$")
    text = text.replace("←", "$\\leftarrow$")
    text = text.replace("↑", "$\\uparrow$")
    text = text.replace("↓", "$\\downarrow$")

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
