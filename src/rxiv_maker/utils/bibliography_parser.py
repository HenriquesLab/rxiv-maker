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

    # Helper function to extract braced field values with proper nesting
    def extract_braced_value(text: str, start_pos: int) -> tuple[str, int]:
        """Extract value from braced field, handling nested braces.

        Returns: (value, end_position)
        """
        if start_pos >= len(text) or text[start_pos] != "{":
            return ("", start_pos)

        brace_count = 0
        value_start = start_pos + 1
        i = start_pos

        while i < len(text):
            if text[i] == "{":
                brace_count += 1
            elif text[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    return (text[value_start:i], i + 1)
            i += 1

        return (text[value_start:], len(text))

    # Simpler pattern that finds field names and equals signs
    field_start_pattern = re.compile(
        r'(\w+)\s*=\s*(["{])',  # Field name, =, and opening delimiter
        re.MULTILINE,
    )

    for field_match in field_start_pattern.finditer(fields_content):
        field_name = field_match.group(1).strip().lower()
        delimiter = field_match.group(2)
        value_start = field_match.end() - 1  # Back up to the delimiter

        if delimiter == "{":
            # Extract braced value with proper nesting
            field_value, _end_pos = extract_braced_value(fields_content, value_start)
        elif delimiter == '"':
            # Extract quoted value
            quote_end = fields_content.find('"', value_start + 1)
            if quote_end != -1:
                field_value = fields_content[value_start + 1 : quote_end]
            else:
                field_value = fields_content[value_start + 1 :]
        else:
            continue

        # Clean up the value
        field_value = field_value.strip()
        field_value = " ".join(field_value.split())

        if field_value:
            fields[field_name] = field_value

    # Also handle bare values (numbers, etc.) not already processed
    bare_pattern = re.compile(r'(\w+)\s*=\s*([^,}\s"{][^,}]*)', re.MULTILINE)

    for field_match in bare_pattern.finditer(fields_content):
        field_name = field_match.group(1).strip().lower()

        # Skip if already processed
        if field_name in fields:
            continue

        field_value = field_match.group(2).strip().rstrip(",").strip()
        field_value = " ".join(field_value.split())

        if field_value:
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
