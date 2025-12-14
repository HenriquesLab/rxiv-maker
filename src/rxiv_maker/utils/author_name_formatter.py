"""Author name parsing and formatting utilities.

This module provides functionality to parse, format, and transform author names
between different bibliographic citation formats.

Supported formats:
- lastname_initials: "Smith, J.A."
- lastname_firstname: "Smith, John A."
- firstname_lastname: "John A. Smith"
"""

import re
from typing import Dict


def extract_initials(given_name: str) -> str:
    """Extract initials from a given name.

    Args:
        given_name: Given name(s), which may include first and middle names

    Returns:
        Formatted initials with periods

    Examples:
        >>> extract_initials("John Alan")
        'J.A.'
        >>> extract_initials("J. A.")
        'J.A.'
        >>> extract_initials("Jean-Paul")
        'J.-P.'
        >>> extract_initials("John")
        'J.'
    """
    if not given_name or not given_name.strip():
        return ""

    given_name = given_name.strip()

    # Handle hyphenated names specially (e.g., "Jean-Paul" → "J.-P.")
    if "-" in given_name:
        # Remove periods first, then split on hyphen
        cleaned = given_name.replace(".", "").strip()
        parts = cleaned.split("-")
        initials = "-".join(part[0].upper() + "." for part in parts if part and part.strip())
        return initials

    # Remove periods and split on whitespace to handle multi-word names
    cleaned = given_name.replace(".", "").strip()
    words = cleaned.split()

    if not words:
        return ""

    # Handle concatenated initials like "JA" → "J.A."
    # If we have a single "word" with multiple uppercase letters, treat each as an initial
    if len(words) == 1 and len(words[0]) > 1:
        word = words[0]
        # Check if it looks like concatenated initials (all or mostly uppercase)
        uppercase_count = sum(1 for c in word if c.isupper())
        if uppercase_count >= len(word) * 0.8:  # 80% or more uppercase
            # Treat each uppercase letter as an initial
            initials = [c.upper() + "." for c in word if c.isupper()]
            return "".join(initials) if initials else ""

    # Extract first letter from each word
    initials = []
    for word in words:
        if word and word[0].isalpha():
            initials.append(word[0].upper() + ".")

    return "".join(initials) if initials else ""


def parse_author_name(name_str: str) -> Dict[str, str]:
    """Parse an author name into components.

    Handles both "LastName, FirstName MiddleName" and "FirstName MiddleName LastName" formats.

    Args:
        name_str: Author name string to parse

    Returns:
        Dictionary with keys: first, middle, last, suffix, von
        Empty strings for missing components

    Examples:
        >>> parse_author_name("Smith, John A.")
        {'first': 'John', 'middle': 'A.', 'last': 'Smith', 'suffix': '', 'von': ''}
        >>> parse_author_name("von Neumann, John")
        {'first': 'John', 'middle': '', 'last': 'von Neumann', 'suffix': '', 'von': 'von'}
        >>> parse_author_name("Martin, James Jr.")
        {'first': 'James', 'middle': '', 'last': 'Martin', 'suffix': 'Jr.', 'von': ''}
        >>> parse_author_name("John A. Smith")
        {'first': 'John', 'middle': 'A.', 'last': 'Smith', 'suffix': '', 'von': ''}
    """
    if not name_str or not name_str.strip():
        return {"first": "", "middle": "", "last": "", "suffix": "", "von": ""}

    name_str = name_str.strip()

    # Common suffixes to detect
    suffixes = ["Jr.", "Jr", "Sr.", "Sr", "II", "III", "IV", "V"]

    # Check for "LastName, FirstName" format (comma indicates this format)
    if "," in name_str:
        # Split by comma
        parts = [p.strip() for p in name_str.split(",", 1)]
        last_part = parts[0]
        given_part = parts[1] if len(parts) > 1 else ""

        # Check if last part of given_part is a suffix
        suffix = ""
        if given_part:
            given_words = given_part.split()
            if given_words and given_words[-1] in suffixes:
                suffix = given_words[-1]
                given_part = " ".join(given_words[:-1])

        # Parse given names (first + middle)
        given_words = given_part.split() if given_part else []
        first = given_words[0] if given_words else ""
        middle = " ".join(given_words[1:]) if len(given_words) > 1 else ""

        # Check for von/van prefix in last name
        von = ""
        last_words = last_part.split()
        if last_words and last_words[0].lower() in ["von", "van", "de", "del", "della", "di"]:
            von = last_words[0]
            # Keep von as part of last name
            last = last_part
        else:
            last = last_part

        return {
            "first": first,
            "middle": middle,
            "last": last,
            "suffix": suffix,
            "von": von,
        }
    else:
        # "FirstName MiddleName LastName" format
        words = name_str.split()

        if not words:
            return {"first": "", "middle": "", "last": "", "suffix": "", "von": ""}

        # Check if last word is a suffix
        suffix = ""
        if words[-1] in suffixes:
            suffix = words[-1]
            words = words[:-1]

        if not words:
            return {"first": "", "middle": "", "last": "", "suffix": suffix, "von": ""}

        # Single name (e.g., "Plato")
        if len(words) == 1:
            return {
                "first": "",
                "middle": "",
                "last": words[0],
                "suffix": suffix,
                "von": "",
            }

        # Check for von/van prefix
        von = ""
        von_idx = None
        for i, word in enumerate(words[:-1]):  # Don't check last word
            if word.lower() in ["von", "van", "de", "del", "della", "di"]:
                von = word
                von_idx = i
                break

        if von_idx is not None:
            # Everything before von is first/middle, von + rest is last
            first = words[0] if von_idx > 0 else ""
            middle = " ".join(words[1:von_idx]) if von_idx > 1 else ""
            last = " ".join(words[von_idx:])
        else:
            # Standard: First [Middle...] Last
            first = words[0]
            middle = " ".join(words[1:-1]) if len(words) > 2 else ""
            last = words[-1]

        return {
            "first": first,
            "middle": middle,
            "last": last,
            "suffix": suffix,
            "von": von,
        }


def format_author_name(author_parts: Dict[str, str], format_type: str) -> str:
    """Format an author name according to the specified format.

    Args:
        author_parts: Dictionary with author name components (from parse_author_name)
        format_type: One of "lastname_initials", "lastname_firstname", "firstname_lastname"

    Returns:
        Formatted author name string

    Examples:
        >>> parts = {'first': 'John', 'middle': 'A.', 'last': 'Smith', 'suffix': '', 'von': ''}
        >>> format_author_name(parts, "lastname_initials")
        'Smith, J.A.'
        >>> format_author_name(parts, "lastname_firstname")
        'Smith, John A.'
        >>> format_author_name(parts, "firstname_lastname")
        'John A. Smith'
    """
    first = author_parts.get("first", "").strip()
    middle = author_parts.get("middle", "").strip()
    last = author_parts.get("last", "").strip()
    suffix = author_parts.get("suffix", "").strip()

    # Build given name (first + middle)
    given_parts = []
    if first:
        given_parts.append(first)
    if middle:
        given_parts.append(middle)
    given_name = " ".join(given_parts)

    # Handle single-name authors (e.g., "Plato")
    if not given_name and last:
        return last

    if not last:
        return given_name  # Fallback if no last name

    # Format based on type
    if format_type == "lastname_initials":
        # Extract initials from given name
        initials = extract_initials(given_name)
        if initials:
            result = f"{last}, {initials}"
        else:
            result = last
    elif format_type == "lastname_firstname":
        if given_name:
            result = f"{last}, {given_name}"
        else:
            result = last
    elif format_type == "firstname_lastname":
        if given_name:
            result = f"{given_name} {last}"
        else:
            result = last
    else:
        # Default to lastname_firstname
        if given_name:
            result = f"{last}, {given_name}"
        else:
            result = last

    # Add suffix if present
    if suffix:
        if format_type in ["lastname_initials", "lastname_firstname"]:
            result = f"{result}, {suffix}"
        else:
            result = f"{result} {suffix}"

    return result


def format_author_list(authors_str: str, format_type: str) -> str:
    """Format a list of authors separated by 'and'.

    Note: Caller should clean LaTeX commands from authors_str before calling this function.

    Args:
        authors_str: String of authors separated by " and " (should be LaTeX-cleaned)
        format_type: One of "lastname_initials", "lastname_firstname", "firstname_lastname"

    Returns:
        Formatted author list joined by " and "

    Examples:
        >>> format_author_list("Smith, John and Jones, Mary A.", "lastname_initials")
        'Smith, J. and Jones, M.A.'
        >>> format_author_list("Smith, John A. and Jones, Mary", "firstname_lastname")
        'John A. Smith and Mary Jones'
    """
    if not authors_str or not authors_str.strip():
        return ""

    # Split by " and " (BibTeX standard separator)
    # Handle potential variations: "and", " and ", " and  "
    author_list = re.split(r"\s+and\s+", authors_str)

    # Parse and format each author
    formatted_authors = []
    for author in author_list:
        author = author.strip()
        if not author:
            continue

        # Parse the name
        author_parts = parse_author_name(author)

        # Format according to specified type
        formatted = format_author_name(author_parts, format_type)
        formatted_authors.append(formatted)

    # Join with " and "
    return " and ".join(formatted_authors)
