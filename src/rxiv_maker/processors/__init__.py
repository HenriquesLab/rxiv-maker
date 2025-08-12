"""Processing modules for Rxiv-Maker.

This package contains core processing modules for YAML metadata,
templates, and author information.
"""

from .author_processor import (
    generate_authors_and_affiliations,
    generate_corresponding_authors,
    generate_extended_author_info,
)
from .template_processor import (
    generate_supplementary_tex,
    get_template_path,
    process_template_replacements,
)
from .yaml_processor import extract_yaml_metadata

__all__ = [
    "extract_yaml_metadata",
    "get_template_path",
    "process_template_replacements",
    "generate_supplementary_tex",
    "generate_authors_and_affiliations",
    "generate_corresponding_authors",
    "generate_extended_author_info",
]
