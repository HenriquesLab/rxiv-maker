"""Unified cache package for rxiv-maker.

This package consolidates all caching functionality including:
- Advanced caching with TTL and persistence
- Bibliography and DOI-specific caches
- Cache utilities and directory management
- Secure cache handling with encryption
"""

# Core cache utilities
# Advanced caching functionality
from .advanced_cache import AdvancedCache

# Domain-specific caches
from .bibliography_cache import BibliographyCache
from .cache_utils import get_cache_dir
from .doi_cache import DOICache

# Security utilities
from .secure_cache_utils import (
    get_secure_cache_dir,
    secure_migrate_cache_directory,
    secure_migrate_cache_file,
    validate_cache_security,
)

__all__ = [
    # Core utilities
    "get_cache_dir",
    # Advanced caching
    "AdvancedCache",
    # Domain-specific
    "BibliographyCache",
    "DOICache",
    # Security utilities
    "get_secure_cache_dir",
    "secure_migrate_cache_file",
    "secure_migrate_cache_directory",
    "validate_cache_security",
]
