"""Citation processing for markdown to LaTeX conversion.

This module handles conversion of markdown citations to LaTeX format,
including single citations, multiple bracketed citations, and citation
key validation.
"""

import re

from .types import CitationKey, LatexContent, MarkdownContent, ProtectedContent


def convert_citations_to_latex(text: MarkdownContent) -> LatexContent:
    """Convert markdown citations to LaTeX format.

    Args:
        text: Text containing markdown citations

    Returns:
        Text with citations converted to LaTeX format
    """

    # Handle bracketed multiple citations like [@citation1;@citation2]
    def process_multiple_citations(match: re.Match[str]) -> str:
        citations_text = match.group(1)
        # Split by semicolon and clean up each citation
        citations: list[CitationKey] = []
        for cite in citations_text.split(";"):
            # Remove @ symbol and whitespace
            clean_cite = cite.strip().lstrip("@").strip()
            if clean_cite:
                citations.append(clean_cite)
        return "\\cite{" + ",".join(citations) + "}"

    text = re.sub(r"\[(@[^]]+)\]", process_multiple_citations, text)

    # First, protect email addresses and domain-like patterns by temporarily replacing them
    email_patterns = []

    def protect_email(match):
        email_patterns.append(match.group(0))
        return f"__EMAIL_PATTERN_{len(email_patterns) - 1}__"

    # Match email-like patterns: word@word.word or @word.word (domain patterns)
    text = re.sub(r"(\w+@[\w.-]+\.\w+|@[\w.-]+\.\w+)", protect_email, text)

    # Handle single citations like @citation_key (but not figure/equation references)
    # Allow alphanumeric, underscore, and hyphen in citation keys
    # Exclude figure and equation references by not matching @fig: or @eq: patterns
    text = re.sub(r"@(?!fig:|eq:)([a-zA-Z0-9_-]+)", r"\\cite{\1}", text)

    # Restore protected email patterns
    for i, pattern in enumerate(email_patterns):
        text = text.replace(f"__EMAIL_PATTERN_{i}__", pattern)

    return text


def process_citations_outside_tables(
    content: MarkdownContent, protected_markdown_tables: ProtectedContent
) -> LatexContent:
    """Process citations only outside of protected markdown table blocks.

    Args:
        content: Content to process
        protected_markdown_tables: Dictionary of protected table content

    Returns:
        Content with citations processed outside tables
    """
    # Find all protected markdown table placeholders
    table_placeholders = list(protected_markdown_tables)

    if not table_placeholders:
        # No protected tables, process normally
        return process_citations_in_text(content)

    # Split content by table placeholders and only process non-protected parts
    parts = [content]
    for placeholder in table_placeholders:
        new_parts: list[str] = []
        for part in parts:
            if placeholder in part:
                split_parts = part.split(placeholder)
                for i, split_part in enumerate(split_parts):
                    new_parts.append(split_part)
                    if i < len(split_parts) - 1:  # Don't add placeholder after last part
                        new_parts.append(placeholder)
            else:
                new_parts.append(part)
        parts = new_parts

    # Process citations only in non-placeholder parts
    processed_parts: list[str] = []
    for part in parts:
        if part in table_placeholders:
            # This is a protected table placeholder - don't process citations
            processed_parts.append(part)
        else:
            # This is regular text - process citations
            processed_parts.append(process_citations_in_text(part))

    return "".join(processed_parts)


def process_citations_in_text(text: MarkdownContent) -> LatexContent:
    """Process citations in regular text content.

    Args:
        text: Text content to process

    Returns:
        Text with citations converted to LaTeX
    """

    # First handle bracketed multiple citations like [@citation1;@citation2]
    def process_multiple_citations(match: re.Match[str]) -> str:
        citations_text = match.group(1)
        # Split by semicolon and clean up each citation
        citations: list[CitationKey] = []
        for cite in citations_text.split(";"):
            # Remove @ symbol and whitespace
            clean_cite = cite.strip().lstrip("@").strip()
            if clean_cite:
                citations.append(clean_cite)
        return "\\cite{" + ",".join(citations) + "}"

    text = re.sub(r"\[(@[^]]+)\]", process_multiple_citations, text)

    # First, protect email addresses and domain-like patterns by temporarily replacing them
    email_patterns = []

    def protect_email(match):
        email_patterns.append(match.group(0))
        return f"__EMAIL_PATTERN_{len(email_patterns) - 1}__"

    # Match email-like patterns: word@word.word or @word.word (domain patterns)
    text = re.sub(r"(\w+@[\w.-]+\.\w+|@[\w.-]+\.\w+)", protect_email, text)

    # Handle single citations like @citation_key (but not figure/equation references)
    # Allow alphanumeric, underscore, and hyphen in citation keys
    # Exclude figure and equation references by not matching @fig: or @eq: patterns
    text = re.sub(r"@(?!fig:|eq:)([a-zA-Z0-9_-]+)", r"\\cite{\1}", text)

    # Restore protected email patterns
    for i, pattern in enumerate(email_patterns):
        text = text.replace(f"__EMAIL_PATTERN_{i}__", pattern)
    return text


def validate_citation_key(citation_key: CitationKey) -> bool:
    """Validate that a citation key follows proper format.

    Args:
        citation_key: The citation key to validate

    Returns:
        True if the citation key is valid, False otherwise
    """
    # Citation keys should contain only alphanumeric characters,
    # underscores, and hyphens
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", citation_key))


def extract_citations_from_text(text: MarkdownContent) -> list[CitationKey]:
    """Extract all citation keys from markdown text.

    Args:
        text: Text to extract citations from

    Returns:
        List of unique citation keys found in the text
    """
    citations: list[CitationKey] = []

    # Find bracketed multiple citations
    bracketed_matches = re.findall(r"\[(@[^]]+)\]", text)
    for match in bracketed_matches:
        for cite in match.split(";"):
            clean_cite = cite.strip().lstrip("@").strip()
            if clean_cite and clean_cite not in citations:
                citations.append(clean_cite)

    # Find single citations (excluding figure and equation references)
    single_matches = re.findall(r"@(?!fig:|eq:)([a-zA-Z0-9_-]+)", text)
    for cite in single_matches:
        if cite not in citations:
            citations.append(cite)

    return citations
