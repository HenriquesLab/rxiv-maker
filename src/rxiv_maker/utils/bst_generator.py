"""BibTeX style file generator for custom author name formatting.

This module generates custom .bst files with different author name format strings
to support lastname_initials, lastname_firstname, and firstname_lastname formats.
"""

import re
from pathlib import Path
from typing import Dict

from ..core.logging_config import get_logger

logger = get_logger()

# BibTeX format string mapping
# BibTeX format codes:
# ff = full first name, f = first initial
# vv = von part, ll = last name, jj = junior part
BST_FORMAT_MAP: Dict[str, str] = {
    "lastname_initials": "{vv~}{ll}{, f.}",  # Smith, J.A.
    "lastname_firstname": "{ff~}{vv~}{ll}{, jj}",  # Smith, John A. (current default)
    "firstname_lastname": "{ff~}{vv~}{ll}",  # John A. Smith
}


def generate_bst_file(format_type: str, output_dir: Path) -> Path:
    """Generate a custom .bst file with the specified author name format.

    Args:
        format_type: One of "lastname_initials", "lastname_firstname", "firstname_lastname"
        output_dir: Directory where the generated .bst file should be written

    Returns:
        Path to the generated .bst file

    Raises:
        ValueError: If format_type is not recognized
        FileNotFoundError: If template .bst file cannot be found
        IOError: If .bst file cannot be written

    Example:
        >>> output_path = generate_bst_file("lastname_initials", Path("./output"))
        >>> # Creates ./output/rxiv_maker_style.bst with lastname, initials format
    """
    if format_type not in BST_FORMAT_MAP:
        valid_formats = ", ".join(BST_FORMAT_MAP.keys())
        raise ValueError(f"Invalid format_type '{format_type}'. Must be one of: {valid_formats}")

    # Get the format string for this format type
    format_string = BST_FORMAT_MAP[format_type]

    # Find the template .bst file in the package
    # Try multiple locations for development and installed configurations
    possible_template_paths = [
        # Installed package location (site-packages/rxiv_maker/tex/style/)
        Path(__file__).parent.parent / "tex" / "style" / "rxiv_maker_style.bst",
        # Development location (src/tex/style/)
        Path(__file__).parent.parent.parent / "tex" / "style" / "rxiv_maker_style.bst",
        # Alternative development location
        Path(__file__).parent.parent.parent.parent / "src" / "tex" / "style" / "rxiv_maker_style.bst",
    ]

    template_path = None
    for path in possible_template_paths:
        if path.exists():
            template_path = path
            break

    if template_path is None:
        searched_paths = "\n".join(f"  - {p}" for p in possible_template_paths)
        raise FileNotFoundError(
            f"Template .bst file not found.\n"
            f"Searched locations:\n{searched_paths}\n"
            f"This may indicate a corrupted installation."
        )

    # Read the template file
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            bst_content = f.read()
    except IOError as e:
        raise IOError(f"Failed to read template .bst file: {e}") from e

    # Replace the format string in the format.names function (line ~222)
    # The line looks like: s nameptr "{ff~}{vv~}{ll}{, jj}" format.name$ 't :=
    # We need to replace ONLY in format.names, NOT in format.full.names
    #
    # Strategy: Match the FUNCTION {format.names} block specifically
    # This ensures we don't modify format.full.names which is used for citation labels
    #
    # Pattern explanation:
    # 1. Match "FUNCTION {format.names}" to find the start of the function
    # 2. Use non-greedy match (.*?) to capture until we find our target line
    # 3. Match and capture the format string in quotes
    # 4. This avoids matching format.full.names which appears later in the file
    pattern = r'(FUNCTION\s+\{format\.names\}.*?s\s+nameptr\s+")([^"]+)("\s+format\.name\$)'
    replacement = rf"\1{format_string}\3"

    modified_content, num_subs = re.subn(pattern, replacement, bst_content, flags=re.DOTALL)

    if num_subs == 0:
        logger.warning(
            "No format string pattern found in format.names function. "
            "The .bst file structure may have changed. "
            "Citation formatting may not work as expected."
        )
        # Still write the file but log a warning
    elif num_subs > 1:
        # This should never happen with the new pattern, but keep the check
        logger.error(
            f"Found {num_subs} matches in .bst file. Expected exactly 1. "
            "This indicates an unexpected .bst file structure. "
            "Please report this issue."
        )
        raise ValueError(f"Unexpected .bst file structure: found {num_subs} matches for format.names, expected 1")
    else:
        # Success - exactly one match
        logger.debug(f"Successfully updated format.names function with format '{format_type}'")

    # Create output directory if it doesn't exist
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write the generated .bst file
    output_path = output_dir / "rxiv_maker_style.bst"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(modified_content)
    except IOError as e:
        raise IOError(f"Failed to write generated .bst file: {e}") from e

    logger.debug(f"Generated .bst file with format '{format_type}' at: {output_path}")

    return output_path


def get_bst_format_string(format_type: str) -> str:
    """Get the BibTeX format string for a given format type.

    Args:
        format_type: One of "lastname_initials", "lastname_firstname", "firstname_lastname"

    Returns:
        BibTeX format string

    Raises:
        ValueError: If format_type is not recognized

    Example:
        >>> get_bst_format_string("lastname_initials")
        '{vv~}{ll}{, f.}'
    """
    if format_type not in BST_FORMAT_MAP:
        valid_formats = ", ".join(BST_FORMAT_MAP.keys())
        raise ValueError(f"Invalid format_type '{format_type}'. Must be one of: {valid_formats}")
    return BST_FORMAT_MAP[format_type]
