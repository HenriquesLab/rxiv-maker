"""Advanced caching system with performance optimizations.

This module provides enhanced caching capabilities including:
- Multi-level caching (memory + disk)
- Content-based expiration
- Compressed storage
- Performance metrics
- Automatic cleanup
"""

import gzip
import hashlib
import json
import logging
import pickle
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from .cache_utils import get_cache_dir

logger = logging.getLogger(__name__)


class AdvancedCache:
    """Multi-level cache with memory and disk storage."""

    def __init__(
        self,
        name: str,
        max_memory_items: int = 1000,
        max_disk_size_mb: int = 100,
        compression: bool = True,
        ttl_hours: int = 24,
    ):
        """Initialize advanced cache.

        Args:
            name: Cache name (used for directory)
            max_memory_items: Maximum items in memory cache
            max_disk_size_mb: Maximum disk cache size in MB
            compression: Whether to compress disk storage
            ttl_hours: Time-to-live in hours
        """
        self.name = name
        self.max_memory_items = max_memory_items
        self.max_disk_size_mb = max_disk_size_mb
        self.compression = compression
        self.ttl_seconds = ttl_hours * 3600

        # In-memory cache (LRU-style with access tracking)
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._access_order: Dict[str, float] = {}

        # Disk cache
        self.cache_dir = get_cache_dir("advanced") / name
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Performance metrics
        self.stats = {"memory_hits": 0, "disk_hits": 0, "misses": 0, "evictions": 0, "compressions": 0}

        # Initialize with cleanup
        self._cleanup_expired()

    def _generate_key(self, key: str, content_hash: str = None) -> str:
        """Generate cache key with optional content-based component."""
        if content_hash:
            return f"{key}_{content_hash}"
        return key

    def _calculate_content_hash(self, data: Any) -> str:
        """Calculate hash of data for content-based caching."""
        if isinstance(data, (dict, list)):
            serialized = json.dumps(data, sort_keys=True)
        elif isinstance(data, str):
            serialized = data
        else:
            serialized = str(data)

        return hashlib.md5(serialized.encode(), usedforsecurity=False).hexdigest()[:12]

    def _evict_memory_lru(self) -> None:
        """Evict least recently used items from memory cache."""
        if len(self._memory_cache) < self.max_memory_items:
            return

        # Sort by access time and remove oldest
        sorted_keys = sorted(self._access_order.items(), key=lambda x: x[1])
        to_remove = len(sorted_keys) - self.max_memory_items + 1

        for key, _ in sorted_keys[:to_remove]:
            if key in self._memory_cache:
                del self._memory_cache[key]
                del self._access_order[key]
                self.stats["evictions"] += 1

    def _get_disk_path(self, key: str) -> Path:
        """Get disk cache file path."""
        safe_key = key.replace("/", "_").replace("\\", "_")
        extension = ".gz" if self.compression else ".pickle"
        return self.cache_dir / f"{safe_key}{extension}"

    def _save_to_disk(self, key: str, data: Any, metadata: Dict[str, Any]) -> None:
        """Save data to disk with optional compression."""
        disk_path = self._get_disk_path(key)

        cache_entry = {"data": data, "metadata": metadata, "timestamp": time.time()}

        try:
            if self.compression:
                with gzip.open(disk_path, "wb") as f:
                    pickle.dump(cache_entry, f)
                self.stats["compressions"] += 1
            else:
                with open(disk_path, "wb") as f:
                    pickle.dump(cache_entry, f)

            logger.debug(f"Saved to disk cache: {key}")
        except Exception as e:
            logger.warning(f"Failed to save to disk cache: {e}")

    def _load_from_disk(self, key: str) -> Optional[Tuple[Any, Dict[str, Any]]]:
        """Load data from disk with optional decompression."""
        disk_path = self._get_disk_path(key)

        if not disk_path.exists():
            return None

        try:
            if self.compression:
                with gzip.open(disk_path, "rb") as f:
                    cache_entry = pickle.load(f)
            else:
                with open(disk_path, "rb") as f:
                    cache_entry = pickle.load(f)

            # Check expiration
            if time.time() - cache_entry["timestamp"] > self.ttl_seconds:
                disk_path.unlink()  # Remove expired file
                return None

            logger.debug(f"Loaded from disk cache: {key}")
            return cache_entry["data"], cache_entry["metadata"]

        except Exception as e:
            logger.warning(f"Failed to load from disk cache: {e}")
            return None

    def set(self, key: str, data: Any, metadata: Optional[Dict[str, Any]] = None, content_based: bool = False) -> str:
        """Set cache entry with optional content-based key generation.

        Args:
            key: Base cache key
            data: Data to cache
            metadata: Optional metadata
            content_based: Whether to include content hash in key

        Returns:
            Final cache key used
        """
        metadata = metadata or {}

        # Generate final key
        if content_based:
            content_hash = self._calculate_content_hash(data)
            final_key = self._generate_key(key, content_hash)
            metadata["content_hash"] = content_hash
        else:
            final_key = key

        # Store in memory cache
        self._memory_cache[final_key] = {"data": data, "metadata": metadata, "timestamp": time.time()}
        self._access_order[final_key] = time.time()

        # Evict if necessary
        self._evict_memory_lru()

        # Store on disk asynchronously (non-blocking)
        try:
            self._save_to_disk(final_key, data, metadata)
        except Exception as e:
            logger.debug(f"Disk save failed for {final_key}: {e}")

        return final_key

    def get(self, key: str) -> Optional[Tuple[Any, Dict[str, Any]]]:
        """Get cache entry with metadata.

        Args:
            key: Cache key to lookup

        Returns:
            Tuple of (data, metadata) if found, None otherwise
        """
        current_time = time.time()

        # Check memory cache first
        if key in self._memory_cache:
            entry = self._memory_cache[key]

            # Check expiration
            if current_time - entry["timestamp"] > self.ttl_seconds:
                del self._memory_cache[key]
                del self._access_order[key]
            else:
                # Update access time
                self._access_order[key] = current_time
                self.stats["memory_hits"] += 1
                return entry["data"], entry["metadata"]

        # Check disk cache
        disk_result = self._load_from_disk(key)
        if disk_result:
            data, metadata = disk_result

            # Promote to memory cache
            self._memory_cache[key] = {"data": data, "metadata": metadata, "timestamp": current_time}
            self._access_order[key] = current_time
            self._evict_memory_lru()

            self.stats["disk_hits"] += 1
            return data, metadata

        self.stats["misses"] += 1
        return None

    def get_data(self, key: str) -> Optional[Any]:
        """Get only data from cache (convenience method)."""
        result = self.get(key)
        return result[0] if result else None

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self.get(key) is not None

    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        deleted = False

        # Remove from memory
        if key in self._memory_cache:
            del self._memory_cache[key]
            del self._access_order[key]
            deleted = True

        # Remove from disk
        disk_path = self._get_disk_path(key)
        if disk_path.exists():
            disk_path.unlink()
            deleted = True

        return deleted

    def clear(self) -> None:
        """Clear all cache entries."""
        self._memory_cache.clear()
        self._access_order.clear()

        # Clear disk cache
        for file_path in self.cache_dir.glob("*"):
            if file_path.is_file():
                file_path.unlink()

        # Reset stats
        for key in self.stats:
            self.stats[key] = 0

    def _cleanup_expired(self) -> int:
        """Clean up expired disk cache entries."""
        current_time = time.time()
        removed = 0

        for file_path in self.cache_dir.glob("*"):
            if not file_path.is_file():
                continue

            try:
                # Check file modification time as fallback
                if current_time - file_path.stat().st_mtime > self.ttl_seconds:
                    file_path.unlink()
                    removed += 1
                    continue

                # Try to load and check internal timestamp
                try:
                    if file_path.suffix == ".gz":
                        with gzip.open(file_path, "rb") as f:
                            entry = pickle.load(f)
                    else:
                        with open(file_path, "rb") as f:
                            entry = pickle.load(f)

                    if current_time - entry["timestamp"] > self.ttl_seconds:
                        file_path.unlink()
                        removed += 1

                except Exception:
                    # If we can't load it, remove it
                    file_path.unlink()
                    removed += 1

            except Exception as e:
                logger.debug(f"Error during cleanup of {file_path}: {e}")

        if removed > 0:
            logger.info(f"Cleaned up {removed} expired cache entries")

        return removed

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = sum([self.stats["memory_hits"], self.stats["disk_hits"], self.stats["misses"]])

        if total_requests > 0:
            hit_rate = (self.stats["memory_hits"] + self.stats["disk_hits"]) / total_requests
        else:
            hit_rate = 0.0

        # Calculate disk usage
        disk_size = sum(f.stat().st_size for f in self.cache_dir.glob("*") if f.is_file())

        return {
            **self.stats,
            "hit_rate": hit_rate,
            "memory_entries": len(self._memory_cache),
            "disk_size_bytes": disk_size,
            "disk_size_mb": disk_size / (1024 * 1024),
            "cache_dir": str(self.cache_dir),
        }


def cached_function(
    cache_name: str, ttl_hours: int = 24, content_based: bool = True, compression: bool = True
) -> Callable:
    """Decorator for caching function results.

    Args:
        cache_name: Name for the cache
        ttl_hours: Time-to-live in hours
        content_based: Whether to use content-based caching
        compression: Whether to compress cached data
    """

    def decorator(func: Callable) -> Callable:
        cache = AdvancedCache(name=f"function_{cache_name}", ttl_hours=ttl_hours, compression=compression)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_data = {"function": func.__name__, "args": args, "kwargs": kwargs}
            base_key = hashlib.md5(
                json.dumps(key_data, default=str, sort_keys=True).encode(), usedforsecurity=False
            ).hexdigest()

            # Check cache
            result = cache.get_data(base_key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result

            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}, executing...")
            result = func(*args, **kwargs)

            cache.set(base_key, result, metadata={"function": func.__name__}, content_based=content_based)

            return result

        # Add cache management methods
        wrapper.cache = cache
        wrapper.clear_cache = cache.clear
        wrapper.cache_stats = cache.get_stats

        return wrapper

    return decorator


# Global cache instances for common operations
_global_caches = {}


def get_global_cache(name: str, **kwargs) -> AdvancedCache:
    """Get or create a global cache instance."""
    if name not in _global_caches:
        _global_caches[name] = AdvancedCache(name=name, **kwargs)
    return _global_caches[name]


def clear_all_caches() -> None:
    """Clear all global cache instances."""
    for cache in _global_caches.values():
        cache.clear()
    _global_caches.clear()


def get_cache_statistics() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all global caches."""
    return {name: cache.get_stats() for name, cache in _global_caches.items()}
