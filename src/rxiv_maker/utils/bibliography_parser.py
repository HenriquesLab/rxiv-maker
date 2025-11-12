"""Bibliography file parsing utilities.

This module provides utilities for parsing BibTeX files and extracting entry information.
Used by CLI commands to provide structured bibliography data.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class BibEntry:
    """Represents a parsed bibliography entry."""

    key: str  # Citation key (e.g., "smith2020")
    entry_type: str  # Entry type (e.g., "article", "book")
    fields: dict[str, str]  # Entry fields (title, author, year, etc.)
    raw: str  # Raw BibTeX entry


def parse_bib_file(bib_path: Path) -> list[BibEntry]:
    """Parse a BibTeX file and extract all entries.

    Args:
        bib_path: Path to the .bib file

    Returns:
        List of parsed bibliography entries

    Raises:
        FileNotFoundError: If the bibliography file doesn't exist
        ValueError: If the file cannot be parsed
    """
    if not bib_path.exists():
        raise FileNotFoundError(f"Bibliography file not found: {bib_path}")

    try:
        content = bib_path.read_text(encoding="utf-8")
    except Exception as e:
        raise ValueError(f"Could not read bibliography file: {e}") from e

    return parse_bib_content(content)


def parse_bib_content(content: str) -> list[BibEntry]:
    """Parse BibTeX content and extract all entries.

    Args:
        content: BibTeX file content

    Returns:
        List of parsed bibliography entries
    """
    entries = []

    # Pattern to match complete bib entries: @type{key, ...fields...}
    # We need to manually track braces since BibTeX entries can contain nested braces
    entry_start_pattern = re.compile(r"@(\w+)\s*\{\s*([^,\s}]+)\s*,", re.MULTILINE)

    for match in entry_start_pattern.finditer(content):
        entry_type = match.group(1).lower()
        key = match.group(2).strip()

        # Find the matching closing brace for this entry
        start_pos = match.end()
        brace_count = 1  # We've seen the opening brace
        end_pos = start_pos

        for i, char in enumerate(content[start_pos:], start=start_pos):
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i
                    break

        # Extract fields content (between comma after key and closing brace)
        fields_content = content[start_pos:end_pos].strip()

        # Parse individual fields
        fields = _parse_fields(fields_content)

        # Extract raw entry (from @ to closing brace)
        raw_text = content[match.start() : end_pos + 1]

        entry = BibEntry(key=key, entry_type=entry_type, fields=fields, raw=raw_text)
        entries.append(entry)

    return entries


def _parse_fields(fields_content: str) -> dict[str, str]:
    """Parse fields from a bibliography entry.

    Args:
        fields_content: The content between the comma after the key and the closing brace

    Returns:
        Dictionary of field names to values
    """
    fields = {}

    # Pattern to match:
    # - field = {value}  (braced values)
    # - field = "value"  (quoted values)
    # - field = value    (bare values - numbers, single words)
    # Handles multi-line values and nested braces
    field_pattern = re.compile(
        r"""
        (\w+)                           # Field name
        \s*=\s*                         # Equals sign with optional whitespace
        (?:
            \{((?:[^\}]|\{[^\}]*\})*?)\}  # Braced value (group 2)
            |"((?:[^"]|\\")*?)"           # Quoted value (group 3)
            |([^,}\s][^,}]*)              # Bare value (group 4) - anything until comma or }
        )
        """,
        re.DOTALL | re.MULTILINE | re.VERBOSE,
    )

    for field_match in field_pattern.finditer(fields_content):
        field_name = field_match.group(1).strip().lower()

        # Get value from whichever group matched (braced, quoted, or bare)
        field_value = field_match.group(2) or field_match.group(3) or field_match.group(4) or ""

        # Clean up the value:
        # 1. Strip leading/trailing whitespace
        field_value = field_value.strip()
        # 2. Remove trailing comma (from bare values)
        field_value = field_value.rstrip(",").strip()
        # 3. Replace all whitespace (including newlines, tabs) with single spaces
        field_value = " ".join(field_value.split())

        if field_value:  # Only add non-empty values
            fields[field_name] = field_value

    return fields


def entry_to_dict(entry: BibEntry, include_raw: bool = False) -> dict[str, Any]:
    """Convert a BibEntry to a dictionary for JSON serialization.

    Args:
        entry: The bibliography entry
        include_raw: Whether to include the raw BibTeX entry

    Returns:
        Dictionary representation of the entry
    """
    result = {"key": entry.key, "type": entry.entry_type, **entry.fields}

    if include_raw:
        result["raw"] = entry.raw

    return result


def format_author_list(author_string: str) -> list[str]:
    """Format author string into a list of individual authors.

    Args:
        author_string: The author field from a BibTeX entry (e.g., "Smith, J. and Doe, J.")

    Returns:
        List of author names
    """
    if not author_string:
        return []

    # Split on 'and' (case-insensitive, with word boundaries)
    authors = re.split(r"\s+and\s+", author_string, flags=re.IGNORECASE)

    # Clean up each author name
    return [author.strip() for author in authors if author.strip()]
