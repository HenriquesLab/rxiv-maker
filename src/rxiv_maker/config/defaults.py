"""Default configuration values for rxiv-maker.

This module provides sensible defaults for all optional configuration settings,
allowing users to maintain minimal 00_CONFIG.yml files with only essential fields.
"""

from typing import Any, Dict

# Default configuration values
DEFAULT_CONFIG: Dict[str, Any] = {
    # Citation configuration
    "citation_style": "numbered",  # or "author-date"
    # Bibliography author name format
    "bibliography_author_format": "lastname_firstname",  # Options: lastname_initials, lastname_firstname, firstname_lastname
    # Figures configuration
    "figures": {
        "directory": "FIGURES",
        "generate": True,
        "formats": ["png", "svg"],
    },
    # Validation configuration
    "validation": {
        "enabled": True,
        "strict": False,
        "skip_doi_check": False,
    },
    # Cache configuration
    "cache": {
        "enabled": True,
        "ttl_hours": 24,
    },
    # Methods section placement
    # Options: "inline" (or 1), "after_results" (or 2), "after_bibliography" (or 3)
    "methods_placement": "after_bibliography",
    # Acknowledgment
    "acknowledge_rxiv_maker": True,
}


def get_config_with_defaults(user_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge user configuration with default values.

    Args:
        user_config: User-provided configuration dictionary

    Returns:
        Complete configuration with defaults applied for missing fields

    Example:
        >>> user_cfg = {"title": "My Paper", "authors": [...]}
        >>> full_cfg = get_config_with_defaults(user_cfg)
        >>> full_cfg["citation_style"]  # Returns "numbered" (default)
        'numbered'
        >>> full_cfg["cache"]["enabled"]  # Returns True (default)
        True
    """
    import copy

    # Start with a deep copy of defaults
    config = copy.deepcopy(DEFAULT_CONFIG)

    # Deep merge user config - user values override defaults
    for key, value in user_config.items():
        if isinstance(value, dict) and key in config and isinstance(config[key], dict):
            # For nested dictionaries, merge individual keys
            config[key].update(value)
        else:
            # For simple values, override directly
            config[key] = value

    return config


def get_default_value(key: str) -> Any:
    """Get a specific default configuration value.

    Args:
        key: Configuration key (supports dot notation for nested keys)

    Returns:
        Default value for the specified key, or None if not found

    Example:
        >>> get_default_value("citation_style")
        'numbered'
        >>> get_default_value("figures.directory")
        'FIGURES'
    """
    if "." in key:
        # Handle nested keys with dot notation
        parts = key.split(".")
        value = DEFAULT_CONFIG
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value
    else:
        return DEFAULT_CONFIG.get(key)
