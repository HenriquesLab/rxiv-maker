"""URL and link processing for markdown to LaTeX conversion.

This module handles conversion of markdown links and URLs to LaTeX format,
including proper escaping of special characters in URLs.
"""

import re

from .types import LatexContent, MarkdownContent


def convert_links_to_latex(text: MarkdownContent) -> LatexContent:
    """Convert markdown links to LaTeX URLs.

    Args:
        text: Text containing markdown links

    Returns:
        Text with links converted to LaTeX format
    """

    # Handle markdown links [text](url)
    def process_link(match: re.Match[str]) -> str:
        link_text = match.group(1)
        url = match.group(2)

        # Escape special LaTeX characters in URL
        url_escaped = escape_url_for_latex(url)

        # If link text is the same as URL, use \url{}
        if link_text.strip() == url.strip():
            return f"\\url{{{url_escaped}}}"
        else:
            # Use \href{url}{text} for links with different text
            return f"\\href{{{url_escaped}}}{{{link_text}}}"

    # Convert [text](url) format
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", process_link, text)

    # Handle bare URLs (convert standalone URLs to \url{})
    text = _convert_bare_urls(text)

    return text


def escape_url_for_latex(url: str) -> str:
    """Escape special characters in URLs for LaTeX.

    Args:
        url: URL to escape

    Returns:
        URL with LaTeX special characters escaped
    """
    # Characters that need escaping in LaTeX URLs
    # Most URLs work fine in \url{} and \href{} without escaping
    # but we should handle common problematic characters
    url = url.replace("#", "\\#")  # Hash symbols need escaping
    url = url.replace("%", "\\%")  # Percent symbols need escaping

    # Note: underscores usually don't need escaping in \url{} but can be
    # handled if needed
    # url = url.replace('_', '\\_')

    return url


def _convert_bare_urls(text: MarkdownContent) -> LatexContent:
    """Convert bare URLs to LaTeX format."""

    def process_bare_url(match: re.Match[str]) -> str:
        url = match.group(0)
        url_escaped = escape_url_for_latex(url)
        return f"\\url{{{url_escaped}}}"

    # First pass: protect existing LaTeX commands by temporarily replacing them
    latex_url_pattern = r"\\url\{[^}]+\}"
    latex_href_pattern = r"\\href\{[^}]+\}\{[^}]+\}"

    # Store existing LaTeX commands to avoid double-processing
    protected_commands: list[str] = []

    def protect_latex_command(match: re.Match[str]) -> str:
        protected_commands.append(match.group(0))
        return f"__PROTECTED_LATEX_CMD_{len(protected_commands) - 1}__"

    # Protect existing LaTeX URL commands
    text = re.sub(latex_url_pattern, protect_latex_command, text)
    text = re.sub(latex_href_pattern, protect_latex_command, text)

    # Now convert bare URLs
    text = re.sub(r"https?://[^\s\}>\]]+", process_bare_url, text)

    # Restore protected LaTeX commands
    for i, cmd in enumerate(protected_commands):
        text = text.replace(f"__PROTECTED_LATEX_CMD_{i}__", cmd)

    return text


def validate_url_format(url: str) -> bool:
    """Validate that a URL has proper format.

    Args:
        url: URL to validate

    Returns:
        True if URL format is valid, False otherwise
    """
    # Basic URL validation pattern
    url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(url_pattern, url, re.IGNORECASE))


def extract_urls_from_text(text: MarkdownContent) -> list[tuple[str, str]]:
    """Extract all URLs from markdown text.

    Args:
        text: Text to extract URLs from

    Returns:
        List of tuples (link_text, url) for each link found
    """
    urls: list[tuple[str, str]] = []

    # Find markdown-style links [text](url)
    markdown_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text)
    for link_text, url in markdown_links:
        urls.append((link_text.strip(), url.strip()))

    # Find bare URLs
    bare_urls = re.findall(r"https?://[^\s\}>\]]+", text)
    for url in bare_urls:
        # For bare URLs, use the URL as both text and link
        urls.append((url, url))

    return urls


def normalize_urls(text: MarkdownContent) -> MarkdownContent:
    """Normalize URLs to a consistent format.

    Args:
        text: Text containing URLs to normalize

    Returns:
        Text with normalized URLs
    """

    def normalize_url(match: re.Match[str]) -> str:
        link_text = match.group(1)
        url = match.group(2).strip()

        # Ensure URL has protocol
        if not url.startswith(("http://", "https://")) and (
            url.startswith("www.") or "." in url and not url.startswith(("mailto:", "ftp:"))
        ):
            url = "https://" + url

        return f"[{link_text}]({url})"

    # Normalize markdown links
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", normalize_url, text)

    return text


def convert_email_links_to_latex(text: MarkdownContent) -> LatexContent:
    """Convert email addresses to LaTeX format.

    Args:
        text: Text containing email addresses

    Returns:
        Text with email addresses converted to LaTeX
    """

    # Convert plain email addresses
    def process_email(match: re.Match[str]) -> str:
        email = match.group(0)
        return f"\\href{{mailto:{email}}}{{{email}}}"

    # Email pattern
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

    # Only convert emails not already in links
    # First protect existing links
    protected_links: list[str] = []

    def protect_link(match: re.Match[str]) -> str:
        protected_links.append(match.group(0))
        return f"__PROTECTED_LINK_{len(protected_links) - 1}__"

    # Protect markdown links and LaTeX commands
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", protect_link, text)
    text = re.sub(r"\\href\{[^}]+\}\{[^}]+\}", protect_link, text)

    # Convert unprotected emails
    text = re.sub(email_pattern, process_email, text)

    # Restore protected links
    for i, link in enumerate(protected_links):
        text = text.replace(f"__PROTECTED_LINK_{i}__", link)

    return text


def sanitize_url_for_latex(url: str) -> str:
    """Sanitize a URL for safe use in LaTeX.

    Args:
        url: URL to sanitize

    Returns:
        Sanitized URL safe for LaTeX
    """
    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", '"', "'", "`"]
    for char in dangerous_chars:
        url = url.replace(char, "")

    # Escape LaTeX special characters
    url = escape_url_for_latex(url)

    return url
