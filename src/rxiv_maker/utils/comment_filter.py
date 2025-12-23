"""Comment filtering utilities for manuscript processing.

This module provides utilities to identify and filter metadata comments
from manuscript content. Used by both DOCX export and potentially LaTeX
processing to handle comment blocks consistently.

Examples:
    >>> is_metadata_comment("Note: this is a metadata comment")
    True
    >>> is_metadata_comment("TODO: fix this")
    False
"""


def is_metadata_comment(comment_text: str) -> bool:
    """Check if a comment is metadata/informational and should be skipped.

    Metadata comments are those that start with common prefixes like
    "Note:", "Comment:", etc. These are typically informational and
    should be filtered out during processing.

    Args:
        comment_text: The comment text to check

    Returns:
        True if comment should be skipped (is metadata), False if it should be included

    Examples:
        >>> is_metadata_comment("Note: remember to update this")
        True
        >>> is_metadata_comment("comment this section is WIP")
        True
        >>> is_metadata_comment("TODO: fix the bug")
        False
        >>> is_metadata_comment("")
        True
    """
    if not comment_text:
        return True

    # Normalize to lowercase for case-insensitive matching
    normalized = comment_text.lower().strip()

    # Skip comments that start with common metadata keywords
    metadata_prefixes = ["note:", "note ", "comment:", "comment "]
    return any(normalized.startswith(prefix) for prefix in metadata_prefixes)
