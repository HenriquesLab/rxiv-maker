"""Helper utilities for DOCX export.

This module provides utility functions for DOCX generation including:
- YAML header removal
- Bibliography entry formatting
- Text processing utilities
- PDF to image conversion
"""

import io
import re
from pathlib import Path
from typing import Optional

from PIL import Image

from rxiv_maker.utils.author_name_formatter import format_author_list

from ..utils.bibliography_parser import BibEntry


def remove_yaml_header(content: str) -> str:
    r"""Remove YAML frontmatter from markdown content.

    Args:
        content: Markdown content that may contain YAML frontmatter

    Returns:
        Content with YAML header removed

    Example:
        >>> content = "---\ntitle: Test\n---\n\nActual content"
        >>> remove_yaml_header(content)
        'Actual content'
    """
    if content.startswith("---"):
        # Find second --- delimiter
        end = content.find("\n---\n", 3)
        if end != -1:
            return content[end + 5 :].lstrip()
    return content


def format_bibliography_entry(
    entry: BibEntry,
    doi: Optional[str] = None,
    slim: bool = False,
    author_format: str = "lastname_firstname",
) -> str:
    """Format a bibliography entry for display.

    Full format: Author (Year). Title. Journal Volume(Number): Pages. DOI (if provided)
    Slim format: LastName, Year
    DOI is appended as a new line and rendered as a hyperlink in DOCX writer.

    Args:
        entry: Bibliography entry to format
        doi: DOI string (optional)
        slim: If True, use slim format (LastName, Year)
        author_format: Format for author names - "lastname_initials", "lastname_firstname", "firstname_lastname"

    Returns:
        Formatted bibliography string

    Example:
        >>> entry = BibEntry(
        ...     key="smith2021",
        ...     entry_type="article",
        ...     fields={"author": "Smith, J.", "year": "2021",
        ...             "title": "Test Article", "journal": "Nature"},
        ...     raw=""
        ... )
        >>> format_bibliography_entry(entry, "10.1234/example", slim=True)
        'Smith, 2021'
    """
    # Extract fields with defaults
    author = entry.fields.get("author", "Unknown Author")
    year = entry.fields.get("year", "n.d.")

    # Clean LaTeX commands from author names and format according to specified style
    author = clean_latex_commands(author)
    author = format_author_list(author, author_format)

    if slim:
        # Slim format: First author last name, Year
        first_author = author.split(" and ")[0].strip()
        # Get last name (last word before any comma)
        if "," in first_author:
            # Format: "LastName, FirstName" - take first part
            last_name = first_author.split(",")[0].strip()
        else:
            # Format: "FirstName LastName" - take last word
            author_parts = first_author.split()
            last_name = author_parts[-1] if author_parts else "Unknown"
        return f"{last_name}, {year}"

    # Full format
    title = entry.fields.get("title", "Untitled")
    title = clean_latex_commands(title)

    # Build formatted string starting with authors and year
    formatted = f"{author} ({year}). {title}."

    # Add journal/publisher information based on entry type
    entry_type = entry.entry_type.lower()

    if entry_type == "article":
        journal = entry.fields.get("journal", "")
        if journal:
            journal = clean_latex_commands(journal)
            formatted += f" {journal}"

            # Add volume
            volume = entry.fields.get("volume", "")
            if volume:
                formatted += f" {volume}"

            # Add issue/number in parentheses
            number = entry.fields.get("number", "")
            if number:
                formatted += f"({number})"

            # Add pages
            pages = entry.fields.get("pages", "")
            if pages:
                # Replace double dashes with en dash
                pages = pages.replace("--", "–")
                formatted += f": {pages}"

            formatted += "."

    elif entry_type in ["book", "inbook", "incollection"]:
        publisher = entry.fields.get("publisher", "")
        if publisher:
            publisher = clean_latex_commands(publisher)
            formatted += f" {publisher}."

    elif entry_type == "inproceedings":
        booktitle = entry.fields.get("booktitle", "")
        if booktitle:
            booktitle = clean_latex_commands(booktitle)
            formatted += f" In: {booktitle}"

            # Add pages if available
            pages = entry.fields.get("pages", "")
            if pages:
                pages = pages.replace("--", "–")
                formatted += f", pp. {pages}"

            formatted += "."

    # Add DOI if available (will be rendered as hyperlink in DOCX writer)
    if doi:
        formatted += f"\nDOI: https://doi.org/{doi}"

    return formatted


def format_authors_list(authors_string: str, max_authors: int = 3) -> str:
    """Format authors string for display, truncating if too many.

    Args:
        authors_string: Authors string from BibTeX (e.g., "Smith, J. and Jones, A.")
        max_authors: Maximum number of authors to show before truncating

    Returns:
        Formatted authors string (e.g., "Smith, J., et al.")

    Example:
        >>> format_authors_list("Smith, J. and Jones, A. and Brown, B. and White, C.")
        'Smith, J., et al.'
    """
    if not authors_string:
        return "Unknown Author"

    # Split by "and"
    authors = [a.strip() for a in authors_string.split(" and ")]

    if len(authors) <= max_authors:
        return ", ".join(authors)

    # Truncate and add "et al."
    return f"{', '.join(authors[:max_authors])}, et al."


def clean_latex_commands(text: str) -> str:
    r"""Remove or convert common LaTeX commands to plain text.

    Args:
        text: Text potentially containing LaTeX commands

    Returns:
        Text with LaTeX commands removed or converted

    Example:
        >>> clean_latex_commands("Text with \\\\textbf{bold} and \\\\cite{ref}")
        'Text with bold and ref'
        >>> clean_latex_commands("Griffi{\\'e}")
        'Griffié'
    """
    # Convert LaTeX accent commands to Unicode
    # Handle both with and without backslashes (BibTeX parser may strip them)
    # Also handle variant forms where backslash is replaced with the literal character
    accent_map = {
        # Acute accents (é, á, í, ó, ú) - use non-raw strings for single backslash
        "\\'e": "é",
        "{\\'e}": "é",
        "{'e}": "é",
        "{'é}": "é",
        "\\'a": "á",
        "{\\'a}": "á",
        "{'a}": "á",
        "{'á}": "á",
        "\\'i": "í",
        "{\\'i}": "í",
        "{'i}": "í",
        "{'í}": "í",
        "'{\\i}": "í",  # Acute on dotless i
        "\\'o": "ó",
        "{\\'o}": "ó",
        "{'o}": "ó",
        "{'ó}": "ó",
        "'{o}": "ó",  # Acute o (variant without backslash)
        "\\'u": "ú",
        "{\\'u}": "ú",
        "{'u}": "ú",
        "{'ú}": "ú",
        # Uppercase acute accents
        "\\'E": "É",
        "{\\'E}": "É",
        "{'E}": "É",
        "\\'A": "Á",
        "{\\'A}": "Á",
        "{'A}": "Á",
        "\\'I": "Í",
        "{\\'I}": "Í",
        "{'I}": "Í",
        "'{\\I}": "Í",  # Acute on uppercase dotless I
        "\\'O": "Ó",
        "{\\'O}": "Ó",
        "{'O}": "Ó",
        "'{O}": "Ó",
        "\\'U": "Ú",
        "{\\'U}": "Ú",
        "{'U}": "Ú",
        # Umlaut/diaeresis (ë, ä, ï, ö, ü)
        '\\"e': "ë",
        '{\\"e}': "ë",
        '{"e}': "ë",
        '{"ë}': "ë",
        '\\"a': "ä",
        '{\\"a}': "ä",
        '{"a}': "ä",
        '{"ä}': "ä",
        '\\"i': "ï",
        '{\\"i}': "ï",
        '{"i}': "ï",
        '{"ï}': "ï",
        '\\"o': "ö",
        '{\\"o}': "ö",
        '{"o}': "ö",
        '{"ö}': "ö",
        '\\"u': "ü",
        '{\\"u}': "ü",
        '{"u}': "ü",
        '{"ü}': "ü",
        # Grave accents (è, à)
        "\\`e": "è",
        "{\\`e}": "è",
        "{`e}": "è",
        "{`è}": "è",
        "\\`a": "à",
        "{\\`a}": "à",
        "{`a}": "à",
        "{`à}": "à",
        # Circumflex (ê, â)
        "\\^e": "ê",
        "{\\^e}": "ê",
        "{^e}": "ê",
        "{^ê}": "ê",
        "\\^a": "â",
        "{\\^a}": "â",
        "{^a}": "â",
        "{^â}": "â",
        # Tilde (ñ, ã, õ)
        "\\~n": "ñ",
        "{\\~n}": "ñ",
        "{~n}": "ñ",
        "{~ñ}": "ñ",
        "~{n}": "ñ",
        "\\~a": "ã",
        "{\\~a}": "ã",
        "{~a}": "ã",
        "~{a}": "ã",  # Tilde on a (variant)
        "{~ã}": "ã",
        "\\~o": "õ",
        "{\\~o}": "õ",
        "{~o}": "õ",
        "~{o}": "õ",  # Tilde on o (variant)
        "{~õ}": "õ",
        # Uppercase tilde
        "\\~N": "Ñ",
        "{\\~N}": "Ñ",
        "~{N}": "Ñ",
        "\\~A": "Ã",
        "{\\~A}": "Ã",
        "~{A}": "Ã",
        "\\~O": "Õ",
        "{\\~O}": "Õ",
        "~{O}": "Õ",
        # Cedilla (ç)
        "\\c{c}": "ç",
        "{\\c{c}}": "ç",
        "{\\c{ç}}": "ç",
    }

    for latex_cmd, unicode_char in accent_map.items():
        text = text.replace(latex_cmd, unicode_char)

    # Remove common formatting commands but keep their content
    text = re.sub(r"\\textbf\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\textit\{([^}]+)\}", r"\1", text)
    text = re.sub(r"\\emph\{([^}]+)\}", r"\1", text)

    # Remove citations (they'll be handled separately)
    text = re.sub(r"\\cite[pt]?\{[^}]+\}", "", text)

    # Remove braces around single accented characters (leftover from LaTeX accents)
    # Matches: {ü}, {é}, {ë}, {Ó}, {Í}, etc.
    text = re.sub(r"\{([áéíóúàèìòùâêîôûäëïöüñçãõÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÄËÏÖÜÑÇÃÕ])\}", r"\1", text)

    # Remove other common commands
    text = re.sub(r"\\[a-zA-Z]+\{([^}]+)\}", r"\1", text)

    # Remove lone backslashes
    text = re.sub(r"\\(?![a-zA-Z])", "", text)

    return text


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to append if truncated

    Returns:
        Truncated text

    Example:
        >>> truncate_text("This is a very long text that needs truncation", 20)
        'This is a very lo...'
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def normalize_whitespace(text: str) -> str:
    r"""Normalize whitespace in text (multiple spaces to single, strip).

    Args:
        text: Text to normalize

    Returns:
        Normalized text

    Example:
        >>> normalize_whitespace("Text  with   extra\\n\\nspaces")
        'Text with extra spaces'
    """
    # Replace all whitespace (including newlines) with single spaces
    text = " ".join(text.split())
    return text.strip()


def convert_pdf_to_image(pdf_path: Path, dpi: int = 150, max_width: int = 6) -> Optional[io.BytesIO]:
    """Convert first page of PDF to PNG image for embedding in DOCX.

    Args:
        pdf_path: Path to PDF file
        dpi: DPI for conversion (default: 150 for good quality)
        max_width: Maximum width in inches for Word document (default: 6)

    Returns:
        BytesIO object containing PNG image data, or None if conversion fails

    Example:
        >>> img_bytes = convert_pdf_to_image(Path("figure.pdf"))
        >>> if img_bytes:
        ...     doc.add_picture(img_bytes, width=Inches(6))
    """
    try:
        from pdf2image import convert_from_path

        # Convert first page of PDF to image
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            first_page=1,
            last_page=1,
            fmt="png",
        )

        if not images:
            return None

        img = images[0]

        # Resize if too large (maintain aspect ratio)
        # Max width in pixels at given DPI
        max_width_px = int(max_width * dpi)

        if img.width > max_width_px:
            aspect_ratio = img.height / img.width
            new_width = max_width_px
            new_height = int(new_width * aspect_ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Convert to BytesIO
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return img_bytes

    except Exception as e:
        # Log error but don't crash - return None to indicate failure
        print(f"Warning: Failed to convert PDF to image: {e}")
        return None
