"""DOI cache system for storing CrossRef API responses."""

import json
import logging
import time
from pathlib import Path
from typing import Any

from .cache_utils import get_cache_dir, get_legacy_cache_dir, migrate_cache_file

logger = logging.getLogger(__name__)


class DOICache:
    """Cache system for DOI metadata from CrossRef API."""

    def __init__(
        self,
        cache_dir: str | None = None,
        cache_filename: str | None = None,
        manuscript_name: str | None = None,
    ):
        """Initialize DOI cache.

        Args:
            cache_dir: Directory to store cache files (if None, uses platform-standard location)
            cache_filename: Name of the cache file (if None, uses manuscript-specific naming)
            manuscript_name: Name of the manuscript (used for manuscript-specific caching)
        """
        self.manuscript_name = manuscript_name

        # Use standardized cache directory if not specified
        if cache_dir is None:
            self.cache_dir = get_cache_dir("doi")
        else:
            self.cache_dir = Path(cache_dir)

        # Determine cache filename
        if cache_filename is not None:
            # Use provided filename (backward compatibility)
            self.cache_file = self.cache_dir / cache_filename
        elif manuscript_name is not None:
            # Use manuscript-specific filename
            self.cache_file = self.cache_dir / f"doi_cache_{manuscript_name}.json"
        else:
            # Default filename
            self.cache_file = self.cache_dir / "doi_cache.json"

        self.cache_expiry_days = 30

        # Handle migration from legacy cache location
        self._migrate_legacy_cache()

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load existing cache
        self._cache = self._load_cache()

        # Performance tracking
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "expires": 0, "total_size": 0}

    def _migrate_legacy_cache(self) -> None:
        """Migrate cache file from legacy location if it exists."""
        if self.cache_dir == get_cache_dir("doi"):
            # Only migrate if using new standardized location
            legacy_dir = get_legacy_cache_dir()

            if self.manuscript_name is not None:
                legacy_file = legacy_dir / f"doi_cache_{self.manuscript_name}.json"
            else:
                legacy_file = legacy_dir / "doi_cache.json"

            if legacy_file.exists():
                try:
                    migrate_cache_file(legacy_file, self.cache_file)
                    logger.info(f"Migrated DOI cache from {legacy_file} to {self.cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to migrate DOI cache: {e}")

    def _load_cache(self) -> dict[str, Any]:
        """Load cache from file."""
        if not self.cache_file.exists():
            return {}

        try:
            with open(self.cache_file, encoding="utf-8") as f:
                cache_data = json.load(f)

            # Clean expired entries
            current_time = time.time()
            cleaned_cache = {}

            for doi, entry in cache_data.items():
                if "timestamp" in entry:
                    # Check if entry is still valid
                    entry_time = entry["timestamp"]
                    if (current_time - entry_time) < (self.cache_expiry_days * 24 * 3600):
                        cleaned_cache[doi] = entry
                    else:
                        logger.debug(f"Expired cache entry for DOI: {doi}")
                else:
                    # Legacy entries without timestamp - remove them
                    logger.debug(f"Removing legacy cache entry for DOI: {doi}")

            return cleaned_cache

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Error loading cache file: {e}. Starting with empty cache.")
            return {}

    def _save_cache(self) -> None:
        """Save cache to file."""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving cache file: {e}")

    def get(self, doi: str) -> dict[str, Any] | None:
        """Get cached metadata for a DOI.

        Args:
            doi: DOI to look up

        Returns:
            Cached metadata if available and not expired, None otherwise
        """
        normalized_doi = doi.lower().strip()

        if normalized_doi in self._cache:
            entry = self._cache[normalized_doi]

            # Check if entry is still valid
            if "timestamp" in entry:
                current_time = time.time()
                entry_time = entry["timestamp"]

                if (current_time - entry_time) < (self.cache_expiry_days * 24 * 3600):
                    logger.debug(f"Cache hit for DOI: {doi}")
                    self._stats["hits"] += 1
                    return entry.get("metadata")
                else:
                    # Entry expired, remove it
                    logger.debug(f"Cache entry expired for DOI: {doi}")
                    self._stats["expires"] += 1
                    del self._cache[normalized_doi]
                    self._save_cache()

        logger.debug(f"Cache miss for DOI: {doi}")
        self._stats["misses"] += 1
        return None

    def set(self, doi: str, metadata: dict[str, Any]) -> None:
        """Cache metadata for a DOI.

        Args:
            doi: DOI to cache
            metadata: Metadata to cache
        """
        normalized_doi = doi.lower().strip()

        self._cache[normalized_doi] = {"metadata": metadata, "timestamp": time.time()}
        self._stats["sets"] += 1
        self._stats["total_size"] = len(self._cache)

        self._save_cache()
        logger.debug(f"Cached metadata for DOI: {doi}")

    def set_resolution_status(self, doi: str, resolves: bool, error_message: str | None = None) -> None:
        """Cache DOI resolution status.

        Args:
            doi: DOI to cache status for
            resolves: Whether the DOI resolves
            error_message: Optional error message if resolution failed
        """
        normalized_doi = doi.lower().strip()

        resolution_data = {
            "resolves": resolves,
            "error_message": error_message,
            "timestamp": time.time(),
        }

        # If we already have cached data, update it, otherwise create new entry
        if normalized_doi in self._cache:
            self._cache[normalized_doi]["resolution"] = resolution_data
        else:
            self._cache[normalized_doi] = {
                "metadata": None,
                "resolution": resolution_data,
                "timestamp": time.time(),
            }

        self._save_cache()
        logger.debug(f"Cached resolution status for DOI {doi}: {resolves}")

    def get_resolution_status(self, doi: str) -> dict[str, Any] | None:
        """Get cached resolution status for a DOI.

        Args:
            doi: DOI to look up

        Returns:
            Resolution status if available and not expired, None otherwise
        """
        normalized_doi = doi.lower().strip()

        if normalized_doi in self._cache:
            entry = self._cache[normalized_doi]

            # Check if resolution status exists and is not expired
            if "resolution" in entry:
                resolution_data = entry["resolution"]
                if "timestamp" in resolution_data:
                    current_time = time.time()
                    entry_time = resolution_data["timestamp"]

                    if (current_time - entry_time) < (self.cache_expiry_days * 24 * 3600):
                        logger.debug(f"Cache hit for DOI resolution: {doi}")
                        return resolution_data
                    else:
                        # Resolution data expired, remove it
                        logger.debug(f"Cache entry expired for DOI resolution: {doi}")
                        del entry["resolution"]
                        self._save_cache()

        logger.debug(f"Cache miss for DOI resolution: {doi}")
        return None

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "expires": 0, "total_size": 0}
        self._save_cache()
        logger.info("Cleared DOI cache")

    def cleanup_expired(self) -> int:
        """Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_dois = []

        for doi, entry in self._cache.items():
            if "timestamp" in entry:
                entry_time = entry["timestamp"]
                if (current_time - entry_time) >= (self.cache_expiry_days * 24 * 3600):
                    expired_dois.append(doi)

        for doi in expired_dois:
            del self._cache[doi]

        if expired_dois:
            self._save_cache()
            logger.info(f"Removed {len(expired_dois)} expired cache entries")

        return len(expired_dois)

    def stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0

        for entry in self._cache.values():
            if "timestamp" in entry:
                entry_time = entry["timestamp"]
                if (current_time - entry_time) < (self.cache_expiry_days * 24 * 3600):
                    valid_entries += 1
                else:
                    expired_entries += 1

        return {
            "manuscript_name": self.manuscript_name,
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "cache_file": str(self.cache_file),
            "cache_size_bytes": self.cache_file.stat().st_size if self.cache_file.exists() else 0,
            # Performance statistics
            "performance": self._stats.copy(),
            "hit_rate": self._stats["hits"] / (self._stats["hits"] + self._stats["misses"])
            if (self._stats["hits"] + self._stats["misses"]) > 0
            else 0.0,
        }

    def get_performance_stats(self) -> dict[str, Any]:
        """Get detailed performance statistics.

        Returns:
            Dictionary with performance metrics
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        return {
            "cache_hits": self._stats["hits"],
            "cache_misses": self._stats["misses"],
            "total_requests": total_requests,
            "hit_rate": self._stats["hits"] / total_requests if total_requests > 0 else 0.0,
            "cache_sets": self._stats["sets"],
            "expired_entries": self._stats["expires"],
            "current_size": self._stats["total_size"],
        }

    def batch_get(self, dois: list[str]) -> dict[str, Any]:
        """Batch retrieve multiple DOIs from cache.

        Args:
            dois: List of DOIs to retrieve

        Returns:
            Dictionary mapping DOIs to their cached metadata (if available)
        """
        results = {}
        for doi in dois:
            metadata = self.get(doi)
            if metadata is not None:
                results[doi] = metadata
        return results

    def batch_set(self, doi_metadata_pairs: list[tuple[str, dict[str, Any]]]) -> None:
        """Batch cache multiple DOI metadata pairs.

        Args:
            doi_metadata_pairs: List of (doi, metadata) tuples to cache
        """
        for doi, metadata in doi_metadata_pairs:
            normalized_doi = doi.lower().strip()
            self._cache[normalized_doi] = {"metadata": metadata, "timestamp": time.time()}
            self._stats["sets"] += 1

        self._stats["total_size"] = len(self._cache)
        self._save_cache()
        logger.debug(f"Batch cached {len(doi_metadata_pairs)} DOI entries")
