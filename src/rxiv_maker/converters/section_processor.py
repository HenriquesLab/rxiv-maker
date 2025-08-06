"""Section processing for markdown to LaTeX conversion.

This module handles extraction of content sections from markdown files
and mapping of section titles to standardized keys.
"""

import re

from .types import MarkdownContent, SectionDict, SectionKey, SectionTitle


def extract_content_sections(article_md: MarkdownContent) -> SectionDict:
    """Extract content sections from markdown file and convert to LaTeX.

    Args:
        article_md: Either markdown content as string or path to markdown file

    Returns:
        Dictionary mapping section keys to LaTeX content

    Raises:
        FileNotFoundError: If article_md is a file path that doesn't exist
    """
    # Import here to avoid circular imports
    from .md2tex import convert_markdown_to_latex

    # Check if article_md is a file path or content
    if article_md.startswith("#") or article_md.startswith("---") or "\n" in article_md:
        # It's content, not a file path
        content = article_md
    else:
        # It's a file path
        with open(article_md, encoding="utf-8") as file:
            content = file.read()

    # Remove YAML front matter
    content = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL)

    # Dictionary to store extracted sections
    sections: SectionDict = {}

    # Split content by ## headers to find sections
    section_pattern = r"^## (.+?)$"
    section_matches = list(re.finditer(section_pattern, content, re.MULTILINE))

    # If no sections found, treat entire content as main
    if not section_matches:
        # Check if entire content is supplementary
        is_supplementary = "supplementary" in content.lower()
        sections["main"] = convert_markdown_to_latex(content, is_supplementary)
        return sections

    # Extract main content (everything before first ## header)
    first_section_start = section_matches[0].start()
    main_content = content[:first_section_start].strip()
    if main_content:
        # Check if main content is supplementary
        is_main_supplementary = "supplementary" in main_content.lower()
        sections["main"] = convert_markdown_to_latex(main_content, is_main_supplementary)

    # Extract each section
    for i, match in enumerate(section_matches):
        section_title = match.group(1).strip()
        section_start = match.end()

        # Find end of section (next ## header or end of document)
        if i + 1 < len(section_matches):
            section_end = section_matches[i + 1].start()
        else:
            section_end = len(content)

        section_content = content[section_start:section_end].strip()

        # Check if this is supplementary content (check both title and content)
        is_supplementary = "supplementary" in section_title.lower() or "supplementary" in section_content.lower()

        section_content_latex = convert_markdown_to_latex(section_content, is_supplementary)

        # Map section titles to our standard keys
        section_key = map_section_title_to_key(section_title)
        if section_key:
            sections[section_key] = section_content_latex

    return sections


def map_section_title_to_key(title: SectionTitle) -> SectionKey:
    """Map section title to standardized key.

    Args:
        title: The section title from markdown

    Returns:
        Standardized section key, or custom key if no match found
    """
    title_lower = title.lower()

    if "abstract" in title_lower:
        return "abstract"
    elif "introduction" in title_lower:
        return "main"
    elif "method" in title_lower:
        return "methods"
    elif "result" in title_lower and "discussion" in title_lower:
        return "results_and_discussion"
    elif "result" in title_lower:
        return "results"
    elif "discussion" in title_lower:
        return "discussion"
    elif "conclusion" in title_lower:
        return "conclusion"
    elif "data availability" in title_lower or "data access" in title_lower:
        return "data_availability"
    elif "code availability" in title_lower or "code access" in title_lower:
        return "code_availability"
    elif "manuscript preparation" in title_lower or "manuscript prep" in title_lower:
        return "manuscript_preparation"
    elif "author contribution" in title_lower or "contribution" in title_lower:
        return "author_contributions"
    elif "acknowledgement" in title_lower or "acknowledge" in title_lower:
        return "acknowledgements"
    elif "funding" in title_lower or "financial support" in title_lower or "grant" in title_lower:
        return "funding"
    else:
        # For other sections, return as lowercase with spaces replaced by underscores
        return title_lower.replace(" ", "_").replace("-", "_")
