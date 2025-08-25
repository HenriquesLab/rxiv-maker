"""Cache facade for simplified rxiv-maker cache access.

This module provides simplified access to the comprehensive cache system
without requiring deep knowledge of the internal cache structure.

Usage:
    from rxiv_maker.cache import get_cache, clear_cache, cache_statistics

    # Get cache instance
    cache = get_cache('bibliography')

    # Clear all caches
    clear_cache('all')

    # Get cache statistics
    stats = cache_statistics()
"""

import logging
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

# Import cache components with fallbacks
try:
    from .core.cache import (
        AdvancedCache,
        BibliographyCache,
        DOICache,
        get_cache_dir,
        get_secure_cache_dir,
        validate_cache_security,
    )

    CACHE_AVAILABLE = True
except ImportError:
    logger.debug("Cache components not available")
    CACHE_AVAILABLE = False


def get_cache(
    cache_type: str = "advanced", name: Optional[str] = None
) -> Optional[Union[AdvancedCache, BibliographyCache, DOICache]]:
    """Get a cache instance by type.

    Args:
        cache_type: Type of cache ('advanced', 'bibliography', 'doi')
        name: Name for advanced cache (required for AdvancedCache)

    Returns:
        Cache instance or None if not available

    Examples:
        >>> cache = get_cache('bibliography')
        >>> doi_cache = get_cache('doi')
        >>> my_cache = get_cache('advanced', 'my_data')
    """
    if not CACHE_AVAILABLE:
        logger.warning("Cache system not available")
        return None

    try:
        if cache_type == "advanced":
            if name is None:
                raise ValueError("AdvancedCache requires a name parameter")
            return AdvancedCache(name)

        elif cache_type == "bibliography":
            return BibliographyCache()

        elif cache_type == "doi":
            return DOICache()

        else:
            raise ValueError(f"Unknown cache type: {cache_type}. Use 'advanced', 'bibliography', or 'doi'")

    except Exception as e:
        logger.error(f"Failed to create {cache_type} cache: {e}")
        return None


def clear_cache(cache_type: str = "all") -> bool:
    """Clear cache by type.

    Args:
        cache_type: Type of cache to clear ('all', 'advanced', 'bibliography', 'doi')

    Returns:
        True if successful, False otherwise

    Examples:
        >>> clear_cache('all')  # Clear all caches
        >>> clear_cache('bibliography')  # Clear only bibliography cache
    """
    if not CACHE_AVAILABLE:
        logger.warning("Cache system not available")
        return False

    try:
        if cache_type == "all":
            # Clear all cache types
            success = True
            for ct in ["bibliography", "doi"]:
                success &= clear_cache(ct)
            return success

        elif cache_type == "bibliography":
            bib_cache = BibliographyCache()
            if hasattr(bib_cache, "clear"):
                bib_cache.clear()
            return True

        elif cache_type == "doi":
            doi_cache = DOICache()
            if hasattr(doi_cache, "clear"):
                doi_cache.clear()
            return True

        else:
            logger.warning(f"Unknown cache type for clearing: {cache_type}")
            return False

    except Exception as e:
        logger.error(f"Failed to clear {cache_type} cache: {e}")
        return False


def cache_statistics() -> Dict[str, Any]:
    """Get comprehensive cache statistics.

    Returns:
        Dictionary containing cache statistics and health information

    Examples:
        >>> stats = cache_statistics()
        >>> print(f"Cache directory: {stats['cache_directory']}")
        >>> print(f"Security status: {stats['security_status']['secure']}")
    """
    if not CACHE_AVAILABLE:
        return {"cache_available": False, "error": "Cache system not available"}

    stats = {
        "cache_available": True,
        "cache_directory": None,
        "secure_cache_directory": None,
        "security_status": {},
        "errors": [],
    }

    try:
        # Get cache directories
        stats["cache_directory"] = str(get_cache_dir())
        stats["secure_cache_directory"] = str(get_secure_cache_dir())

        # Get security validation
        stats["security_status"] = validate_cache_security()

    except Exception as e:
        logger.error(f"Failed to get cache statistics: {e}")
        stats["errors"].append(str(e))

    return stats


def cache_health_check() -> Dict[str, Any]:
    """Perform comprehensive cache health check.

    Returns:
        Dictionary containing health check results

    Examples:
        >>> health = cache_health_check()
        >>> if health['healthy']:
        ...     print("Cache system is healthy")
        >>> else:
        ...     print(f"Issues found: {health['issues']}")
    """
    health = {"healthy": True, "cache_available": CACHE_AVAILABLE, "issues": [], "warnings": [], "statistics": {}}

    if not CACHE_AVAILABLE:
        health["healthy"] = False
        health["issues"].append("Cache system not available")
        return health

    try:
        # Get cache statistics
        stats = cache_statistics()
        health["statistics"] = stats

        if stats.get("errors"):
            health["healthy"] = False
            health["issues"].extend(stats["errors"])

        # Check security status
        security = stats.get("security_status", {})
        if not security.get("secure", True):
            health["healthy"] = False
            health["issues"].extend(security.get("issues", []))

        if security.get("warnings"):
            health["warnings"].extend(security["warnings"])

        # Test cache instances
        for cache_type in ["bibliography", "doi"]:
            cache_instance = get_cache(cache_type)
            if cache_instance is None:
                health["warnings"].append(f"{cache_type} cache could not be instantiated")

    except Exception as e:
        health["healthy"] = False
        health["issues"].append(f"Health check failed: {str(e)}")

    return health


# Convenience aliases for backward compatibility
def get_bibliography_cache():
    """Get the bibliography cache instance."""
    return get_cache("bibliography")


def get_doi_cache():
    """Get the DOI cache instance."""
    return get_cache("doi")


def clear_all_caches():
    """Clear all caches."""
    return clear_cache("all")


__all__ = [
    "get_cache",
    "clear_cache",
    "cache_statistics",
    "cache_health_check",
    # Convenience functions
    "get_bibliography_cache",
    "get_doi_cache",
    "clear_all_caches",
]
