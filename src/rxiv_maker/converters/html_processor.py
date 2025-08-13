"""HTML processing for markdown to LaTeX conversion.

This module handles conversion of HTML elements to LaTeX equivalents,
including comments, tags, and special HTML constructs.
"""

import re

from .types import LatexContent, MarkdownContent


def convert_html_comments_to_latex(text: MarkdownContent) -> LatexContent:
    """Convert HTML comments to LaTeX comments.

    Args:
        text: Text containing HTML comments

    Returns:
        Text with HTML comments converted to LaTeX format
    """

    def replace_comment(match: re.Match[str]) -> str:
        comment_content = match.group(1)
        # Convert to LaTeX comment - each line needs to start with %
        lines = comment_content.split("\n")
        latex_comment_lines: list[str] = []
        for line in lines:
            line = line.strip()
            if line:
                latex_comment_lines.append("% " + line)
            else:
                latex_comment_lines.append("%")
        return "\n".join(latex_comment_lines)

    return re.sub(r"<!--(.*?)-->", replace_comment, text, flags=re.DOTALL)


def convert_html_tags_to_latex(text: MarkdownContent) -> LatexContent:
    """Convert common HTML tags to LaTeX equivalents.

    Args:
        text: Text containing HTML tags

    Returns:
        Text with HTML tags converted to LaTeX
    """
    # Convert line breaks
    text = re.sub(r"<br\s*/?>", r"\\\\", text, flags=re.IGNORECASE)

    # Convert bold tags
    text = re.sub(r"<b>(.*?)</b>", r"\\textbf{\1}", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(
        r"<strong>(.*?)</strong>",
        r"\\textbf{\1}",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Convert italic tags
    text = re.sub(r"<i>(.*?)</i>", r"\\textit{\1}", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<em>(.*?)</em>", r"\\textit{\1}", text, flags=re.IGNORECASE | re.DOTALL)

    # Convert code tags
    text = re.sub(r"<code>(.*?)</code>", r"\\texttt{\1}", text, flags=re.IGNORECASE | re.DOTALL)

    return text


def convert_html_entities_to_latex(text: MarkdownContent) -> LatexContent:
    """Convert HTML entities to LaTeX equivalents.

    Args:
        text: Text containing HTML entities

    Returns:
        Text with HTML entities converted to LaTeX
    """
    # Common HTML entities and their LaTeX equivalents
    entity_map = {
        "&amp;": "\\&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&apos;": "'",
        "&nbsp;": "~",  # Non-breaking space
        "&copy;": "\\copyright",
        "&reg;": "\\textregistered",
        "&trade;": "\\texttrademark",
        "&mdash;": "---",  # Em dash
        "&ndash;": "--",  # En dash
        "&hellip;": "\\ldots",  # Ellipsis
    }

    for entity, latex_equiv in entity_map.items():
        text = text.replace(entity, latex_equiv)

    return text


def strip_html_tags(text: MarkdownContent) -> MarkdownContent:
    """Remove all HTML tags from text, keeping only the content.

    Args:
        text: Text that may contain HTML tags

    Returns:
        Text with HTML tags removed
    """
    # Remove all HTML tags but keep their content
    return re.sub(r"<[^>]+>", "", text)


def validate_html_structure(text: MarkdownContent) -> bool:
    """Validate that HTML tags are properly closed.

    Args:
        text: Text containing HTML to validate

    Returns:
        True if HTML structure is valid, False otherwise
    """
    # Stack to track open tags
    stack: list[str] = []

    # Find all HTML tags
    tags = re.findall(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)[^>]*>", text)

    for is_closing, tag_name in tags:
        tag_name = tag_name.lower()

        # Self-closing tags don't need to be tracked
        if tag_name in ["br", "hr", "img", "input", "meta", "link"]:
            continue

        if is_closing:
            # Closing tag
            if not stack or stack[-1] != tag_name:
                return False
            stack.pop()
        else:
            # Opening tag
            stack.append(tag_name)

    # All tags should be closed
    return len(stack) == 0


def extract_html_tags_from_text(text: MarkdownContent) -> list[tuple[str, str, bool]]:
    """Extract all HTML tags from text.

    Args:
        text: Text to extract HTML tags from

    Returns:
        List of tuples (tag_name, full_tag, is_self_closing)
    """
    tags: list[tuple[str, str, bool]] = []

    # Find all HTML tags
    tag_pattern = r"<(/?)([a-zA-Z][a-zA-Z0-9]*)[^>]*(/?)>"

    for match in re.finditer(tag_pattern, text):
        bool(match.group(1))
        tag_name = match.group(2).lower()
        is_self_closing = bool(match.group(3)) or tag_name in [
            "br",
            "hr",
            "img",
            "input",
            "meta",
            "link",
        ]
        full_tag = match.group(0)

        tags.append((tag_name, full_tag, is_self_closing))

    return tags


def clean_html_for_latex(text: MarkdownContent) -> LatexContent:
    """Clean HTML content for LaTeX conversion.

    This function performs a comprehensive cleanup of HTML content,
    converting supported elements and removing unsupported ones.

    Args:
        text: Text containing HTML content

    Returns:
        Cleaned text suitable for LaTeX conversion
    """
    # First convert supported HTML elements
    text = convert_html_tags_to_latex(text)
    text = convert_html_entities_to_latex(text)
    text = convert_html_comments_to_latex(text)

    # Remove any remaining unsupported HTML tags
    # List of tags to completely remove (including content)
    remove_tags = ["script", "style", "head", "meta", "link"]
    for tag in remove_tags:
        text = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", text, flags=re.IGNORECASE | re.DOTALL)

    # Remove remaining HTML tags but keep content
    text = strip_html_tags(text)

    return text
