"""Citation range formatting utilities for manuscript processing.

This module provides utilities to format consecutive citation numbers as ranges
(e.g., [1, 2, 3] → [1-3]). Used by DOCX export and potentially LaTeX processing
to create compact, readable citation references.

Examples:
    >>> format_number_list([1, 2, 3, 5, 6, 8])
    '[1-3, 5-6, 8]'
    >>> format_citation_ranges("text [1][2][3] more")
    'text [1-3] more'
"""

import re
from typing import List


def format_number_list(numbers: List[int]) -> str:
    """Format a list of citation numbers as ranges.

    Consecutive numbers are combined into ranges with hyphens.
    Single numbers and non-consecutive numbers are separated by commas.

    Args:
        numbers: List of citation numbers

    Returns:
        Formatted string with ranges

    Examples:
        >>> format_number_list([1, 2, 3, 5, 6, 8])
        '[1-3, 5-6, 8]'
        >>> format_number_list([15, 16])
        '[15-16]'
        >>> format_number_list([1, 3, 5])
        '[1, 3, 5]'
        >>> format_number_list([])
        '[]'
    """
    if not numbers:
        return "[]"

    # Sort and deduplicate numbers
    sorted_nums = sorted(set(numbers))

    # Build ranges
    ranges = []
    start = sorted_nums[0]
    end = sorted_nums[0]

    for num in sorted_nums[1:]:
        if num == end + 1:
            # Continue current range
            end = num
        else:
            # End current range and start new one
            if start == end:
                # Single number
                ranges.append(str(start))
            else:
                # Range (including 2 consecutive numbers like 15-16)
                ranges.append(f"{start}-{end}")
            start = num
            end = num

    # Add final range
    if start == end:
        # Single number
        ranges.append(str(start))
    else:
        # Range (including 2 consecutive numbers like 15-16)
        ranges.append(f"{start}-{end}")

    return f"[{', '.join(ranges)}]"


def format_citation_ranges(text: str) -> str:
    """Format consecutive citations as ranges.

    Converts patterns like [1][2][3] to [1-3], [15][16] to [15-16], etc.
    Also formats comma-separated lists like [1, 2, 3] to [1-3].

    Args:
        text: Text with numbered citations

    Returns:
        Text with consecutive citations formatted as ranges

    Examples:
        >>> format_citation_ranges("text [1][2][3] more")
        'text [1-3] more'
        >>> format_citation_ranges("text [1, 2, 3] more")
        'text [1-3] more'
        >>> format_citation_ranges("text [1][3][4] more")
        'text [1][3-4] more'
        >>> format_citation_ranges("text [1] [2] [3] more")
        'text [1-3] more'
    """

    # Pattern 1: Handle adjacent bracketed citations [1][2][3] or [1] [2] [3]
    def combine_adjacent(match_obj):
        # Extract all numbers from consecutive brackets (allowing spaces between)
        numbers = [int(n) for n in re.findall(r"\[(\d+)\]", match_obj.group(0))]
        return format_number_list(numbers)

    # Find sequences of adjacent bracketed numbers (with optional spaces between)
    text = re.sub(r"(?:\[\d+\]\s*){2,}", combine_adjacent, text)

    # Pattern 2: Handle comma-separated citations within single brackets [1, 2, 3]
    def combine_comma_separated(match_obj):
        # Extract all numbers from comma-separated list
        numbers_str = match_obj.group(1)
        numbers = [int(n.strip()) for n in numbers_str.split(",")]
        return format_number_list(numbers)

    text = re.sub(r"\[([\d,\s]+)\]", combine_comma_separated, text)

    return text
