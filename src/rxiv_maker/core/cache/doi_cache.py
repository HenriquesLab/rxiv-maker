"""DOI cache system for storing CrossRef API responses."""

import json
import logging
import os
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
        self.cache_expiry_days_extended = 90  # Extended cache during API outages
        self.negative_cache_hours = 1  # Cache API failures temporarily

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
            # Ensure cache directory exists
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            # Verify directory is writable
            if not os.access(self.cache_dir, os.W_OK):
                logger.warning(f"Cache directory {self.cache_dir} is not writable, skipping cache save")
                return

            # Use atomic write for better reliability
            temp_file = self.cache_file.with_suffix(".tmp")
            try:
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(self._cache, f, indent=2, ensure_ascii=False)

                # Atomic move (works on most filesystems)
                temp_file.replace(self.cache_file)
                logger.debug(f"Successfully saved cache to {self.cache_file}")

            except Exception as write_error:
                # Clean up temp file if something went wrong
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except Exception:
                        pass
                raise write_error

        except PermissionError as e:
            logger.warning(f"Permission denied saving cache file {self.cache_file}: {e}")
        except OSError as e:
            logger.warning(f"OS error saving cache file {self.cache_file}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving cache file {self.cache_file}: {e}")

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

    def set_api_failure(self, doi: str, api_name: str, error_message: str) -> None:
        """Cache API failure for temporary negative caching.

        Args:
            doi: DOI that failed to validate
            api_name: Name of the API that failed
            error_message: Error message from the API
        """
        normalized_doi = doi.lower().strip()

        failure_data = {
            "api_name": api_name,
            "error_message": error_message,
            "failed": True,
            "timestamp": time.time(),
        }

        # If we already have cached data, add failure info, otherwise create new entry
        if normalized_doi in self._cache:
            if "failures" not in self._cache[normalized_doi]:
                self._cache[normalized_doi]["failures"] = {}
            self._cache[normalized_doi]["failures"][api_name] = failure_data
        else:
            self._cache[normalized_doi] = {
                "metadata": None,
                "failures": {api_name: failure_data},
                "timestamp": time.time(),
            }

        self._save_cache()
        logger.debug(f"Cached API failure for {api_name} on DOI {doi}")

    def get_api_failure(self, doi: str, api_name: str) -> dict[str, Any] | None:
        """Get cached API failure information.

        Args:
            doi: DOI to check
            api_name: Name of the API to check

        Returns:
            Failure information if cached and not expired, None otherwise
        """
        normalized_doi = doi.lower().strip()

        if normalized_doi in self._cache:
            entry = self._cache[normalized_doi]
            failures = entry.get("failures", {})

            if api_name in failures:
                failure_data = failures[api_name]
                if "timestamp" in failure_data:
                    current_time = time.time()
                    failure_time = failure_data["timestamp"]

                    # Check if failure is still within negative cache period
                    if (current_time - failure_time) < (self.negative_cache_hours * 3600):
                        logger.debug(f"Found cached failure for {api_name} on DOI {doi}")
                        return failure_data
                    else:
                        # Failure cache expired, remove it
                        logger.debug(f"Failure cache expired for {api_name} on DOI {doi}")
                        del failures[api_name]
                        if not failures:
                            del entry["failures"]
                        self._save_cache()

        return None

    def is_extended_cache_period(self) -> bool:
        """Check if we should use extended cache period due to API outages.

        Returns:
            True if multiple APIs are failing and we should extend cache period
        """
        current_time = time.time()
        recent_failures: dict[str, int] = {}
        total_dois_checked = 0

        # Count recent failures by API across all DOI entries
        for entry in self._cache.values():
            failures = entry.get("failures", {})
            if failures:  # Only count entries that have had validation attempts
                total_dois_checked += 1

            for api_name, failure_data in failures.items():
                if "timestamp" in failure_data:
                    failure_time = failure_data["timestamp"]
                    # Count failures in the last 2 hours (more generous for detection)
                    if (current_time - failure_time) < 7200:
                        recent_failures[api_name] = recent_failures.get(api_name, 0) + 1

        # If we have at least some DOIs checked and multiple APIs are failing
        if total_dois_checked == 0:
            return False  # No validation attempts yet

        # Calculate failure rates for primary APIs
        primary_apis = ["CrossRef", "DataCite", "JOSS"]
        failing_primary_apis = 0

        for api in primary_apis:
            failure_count = recent_failures.get(api, 0)
            # Consider API as failing if it has failures for >50% of recent attempts
            if failure_count >= max(1, total_dois_checked * 0.5):
                failing_primary_apis += 1

        # Also check fallback APIs
        fallback_apis = ["OpenAlex", "SemanticScholar", "HandleSystem"]
        failing_fallback_apis = sum(1 for api in fallback_apis if recent_failures.get(api, 0) >= 1)

        # Trigger extended cache if:
        # 1. At least 2 primary APIs are failing, OR
        # 2. At least 1 primary API + 2 fallback APIs are failing
        is_extended = failing_primary_apis >= 2 or (failing_primary_apis >= 1 and failing_fallback_apis >= 2)

        if is_extended:
            logger.debug(
                f"Extended cache period active: {failing_primary_apis} primary APIs failing, "
                f"{failing_fallback_apis} fallback APIs failing (checked {total_dois_checked} DOIs)"
            )

        return is_extended

    def get_with_extended_cache(self, doi: str) -> dict[str, Any] | None:
        """Get cached metadata with extended cache period during API outages.

        Args:
            doi: DOI to look up

        Returns:
            Cached metadata if available (with extended expiry during outages)
        """
        normalized_doi = doi.lower().strip()

        if normalized_doi in self._cache:
            entry = self._cache[normalized_doi]

            if "timestamp" in entry and entry.get("metadata"):
                current_time = time.time()
                entry_time = entry["timestamp"]

                # Use extended cache period if we're in an outage scenario
                cache_period_days = (
                    self.cache_expiry_days_extended if self.is_extended_cache_period() else self.cache_expiry_days
                )

                if (current_time - entry_time) < (cache_period_days * 24 * 3600):
                    logger.debug(f"Cache hit for DOI (extended: {cache_period_days} days): {doi}")
                    self._stats["hits"] += 1
                    return entry.get("metadata")
                else:
                    logger.debug(f"Cache entry expired for DOI: {doi}")
                    self._stats["expires"] += 1

        logger.debug(f"Cache miss for DOI: {doi}")
        self._stats["misses"] += 1
        return None
