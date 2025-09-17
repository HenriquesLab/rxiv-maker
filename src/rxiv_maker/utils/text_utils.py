"""Text processing utilities for rxiv-maker."""

import re
from typing import Union


def count_words_in_text(text: Union[str, None]) -> int:
    r"""Count words in text, excluding code blocks and LaTeX commands.

    This function provides robust word counting for academic manuscripts
    by filtering out code blocks, inline code, and LaTeX commands.

    Args:
        text: The text to count words in. Can be None.

    Returns:
        int: Number of words found in the text.

    Examples:
        >>> count_words_in_text("Hello world")
        2
        >>> count_words_in_text("Hello `code` world")
        2
        >>> count_words_in_text("Hello \\textbf{bold} world")
        2
    """
    if not text or not text.strip():
        return 0

    # Remove code blocks (```...```)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    # Remove inline code (`...`)
    text = re.sub(r"`[^`]+`", "", text)

    # Remove LaTeX commands with braces (e.g., \textbf{text})
    text = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", "", text)

    # Remove standalone LaTeX commands (e.g., \newline)
    text = re.sub(r"\\[a-zA-Z]+", "", text)

    # Split by whitespace and count non-empty words
    words = [word for word in text.split() if word.strip()]
    return len(words)


def clean_text_for_analysis(text: Union[str, None]) -> str:
    """Clean text by removing code blocks and LaTeX commands for analysis.

    Args:
        text: The text to clean. Can be None.

    Returns:
        str: Cleaned text with code and LaTeX removed.
    """
    if not text:
        return ""

    # Apply same cleaning as word count but return the cleaned text
    cleaned = text

    # Remove code blocks
    cleaned = re.sub(r"```.*?```", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"`[^`]+`", "", cleaned)

    # Remove LaTeX commands
    cleaned = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", "", cleaned)
    cleaned = re.sub(r"\\[a-zA-Z]+", "", cleaned)

    return cleaned.strip()
