r"""LaTeX accent character to Unicode conversion map.

This module provides centralized mapping of LaTeX accent commands to their
Unicode equivalents. Used by both DOCX export and LaTeX processing to ensure
consistent character handling across formats.

Examples:
    >>> clean_latex_accents("\\'e")
    'é'
    >>> clean_latex_accents("Calf{\\'e}")
    'Café'
"""

from typing import Dict

# LaTeX accent commands to Unicode character mapping
# Handles both with and without backslashes (BibTeX parser may strip them)
# Also handles variant forms where backslash is replaced with the literal character
ACCENT_MAP: Dict[str, str] = {
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


def clean_latex_accents(text: str) -> str:
    r"""Convert LaTeX accent commands to Unicode characters.

    Args:
        text: Text containing LaTeX accent commands

    Returns:
        Text with accent commands converted to Unicode

    Examples:
        >>> clean_latex_accents("Calf{\\'e}")
        'Café'
        >>> clean_latex_accents("Se\\~nor")
        'Señor'
    """
    for latex_cmd, unicode_char in ACCENT_MAP.items():
        text = text.replace(latex_cmd, unicode_char)
    return text
