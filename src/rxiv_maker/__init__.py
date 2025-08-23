"""Rxiv-Maker Python Package.

A comprehensive toolkit for automated scientific article generation and building.

This package provides a comprehensive toolkit for preparing academic manuscripts
with LaTeX-quality output, integrated bibliography management, figure generation,
and validation systems.

Main Components:
- Services: High-level business logic and orchestration
- Core: Central managers, cache, and configuration
- Engines: Document processing and build operations
- CLI: Command-line interface and user interactions
- Utils: Common utilities and platform helpers
- Validators: Comprehensive manuscript validation

Quick Start:
    from rxiv_maker import ManuscriptService, ValidationService

    # Discover and process manuscript
    ms = ManuscriptService()
    result = ms.discover_manuscript()

    # Validate manuscript
    vs = ValidationService()
    validation = vs.validate_manuscript_comprehensive()
"""

from .__version__ import __version__

# Service Layer Facade - Most commonly needed for external use
try:
    from .services import (  # noqa: F401
        BuildService,
        ConfigurationService,
        ManuscriptService,
        PublicationService,
        ValidationService,
    )

    # Essential exceptions for error handling
    from .services.base import ProcessingError, ServiceError, ServiceResult, ValidationError  # noqa: F401

    SERVICES_AVAILABLE = True
except ImportError:
    # Services may not be available in all environments
    SERVICES_AVAILABLE = False

# Core Utilities Facade - Commonly used across modules
try:
    from .utils.platform import platform_detector  # noqa: F401
    from .utils.unicode_safe import get_safe_icon, safe_console_print, safe_print  # noqa: F401

    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False

# Cache Facade - Frequently accessed
try:
    from .core.cache import AdvancedCache, BibliographyCache, DOICache, get_cache_dir  # noqa: F401

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False


# Maintain backward compatibility
def get_version():
    """Get version information."""
    return __version__


def get_versions():
    """Get version information in versioneer-compatible format."""
    return {"version": __version__}


__author__ = "Rxiv-Maker Contributors"
__description__ = "Academic manuscript preparation toolkit"

# Dynamic __all__ based on available components
__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__description__",
    "get_version",
    "get_versions",
]

if SERVICES_AVAILABLE:
    __all__.extend(
        [
            "ManuscriptService",
            "ValidationService",
            "BuildService",
            "PublicationService",
            "ConfigurationService",
            "ServiceError",
            "ValidationError",
            "ProcessingError",
            "ServiceResult",
        ]
    )

if UTILS_AVAILABLE:
    __all__.extend(
        [
            "safe_print",
            "safe_console_print",
            "get_safe_icon",
            "platform_detector",
        ]
    )

if CACHE_AVAILABLE:
    __all__.extend(
        [
            "get_cache_dir",
            "AdvancedCache",
            "BibliographyCache",
            "DOICache",
        ]
    )
