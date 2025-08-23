"""Unified cache management system for rxiv-maker.

This module provides a centralized interface for all caching operations across
rxiv-maker, unifying DOI caches, figure checksums, validation results, and
other caching needs into a single, consistent API.
"""

import hashlib
import json
import pickle
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, TypeVar

from ..cache.cache_utils import get_cache_dir
from ..error_recovery import RecoveryEnhancedMixin
from ..logging_config import get_logger

logger = get_logger()

T = TypeVar("T")


class CacheType(Enum):
    """Types of cache storage."""

    MEMORY = "memory"  # In-memory cache (lost on restart)
    DISK = "disk"  # Persistent disk cache
    HYBRID = "hybrid"  # Memory + disk with configurable eviction


class SerializationFormat(Enum):
    """Cache serialization formats."""

    JSON = "json"  # JSON format (human readable)
    PICKLE = "pickle"  # Python pickle (supports complex objects)
    RAW = "raw"  # Raw bytes/string (for binary data)


@dataclass
class CacheEntry:
    """A single cache entry with metadata."""

    key: str
    value: Any
    timestamp: float = field(default_factory=time.time)
    ttl: Optional[float] = None  # Time to live in seconds
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl

    def touch(self) -> None:
        """Update access statistics."""
        self.access_count += 1
        self.last_accessed = time.time()


@dataclass
class CacheConfig:
    """Configuration for cache instances."""

    name: str
    cache_type: CacheType = CacheType.DISK
    serialization: SerializationFormat = SerializationFormat.JSON
    ttl_seconds: Optional[float] = None  # Default TTL for entries
    max_size_mb: Optional[float] = None  # Maximum cache size
    max_entries: Optional[int] = None  # Maximum number of entries
    eviction_policy: str = "lru"  # lru, lfu, fifo
    auto_cleanup: bool = True  # Automatic cleanup of expired entries
    compression: bool = False  # Compress stored data
    backup_enabled: bool = True  # Create backup files

    def __post_init__(self):
        """Validate configuration."""
        if self.max_size_mb is not None and self.max_size_mb <= 0:
            raise ValueError("max_size_mb must be positive")
        if self.max_entries is not None and self.max_entries <= 0:
            raise ValueError("max_entries must be positive")


class CacheInterface(ABC, Generic[T]):
    """Abstract interface for cache implementations."""

    @abstractmethod
    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """Get value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: T, ttl: Optional[float] = None) -> None:
        """Set value in cache."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass

    @abstractmethod
    def keys(self) -> List[str]:
        """Get all cache keys."""
        pass

    @abstractmethod
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass


class MemoryCache(CacheInterface[T]):
    """In-memory cache implementation."""

    def __init__(self, config: CacheConfig):
        self.config = config
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0, "evictions": 0, "size_bytes": 0}

    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """Get value from memory cache."""
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return default

            entry = self._cache[key]

            if entry.is_expired():
                del self._cache[key]
                self._stats["misses"] += 1
                return default

            entry.touch()
            self._stats["hits"] += 1
            return entry.value

    def set(self, key: str, value: T, ttl: Optional[float] = None) -> None:
        """Set value in memory cache."""
        with self._lock:
            ttl = ttl or self.config.ttl_seconds

            # Create entry
            entry = CacheEntry(key=key, value=value, ttl=ttl, size_bytes=self._estimate_size(value))

            # Check if we need to evict entries
            if self._should_evict():
                self._evict_entries()

            self._cache[key] = entry
            self._stats["sets"] += 1
            self._update_size_stats()

    def delete(self, key: str) -> bool:
        """Delete value from memory cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats["deletes"] += 1
                self._update_size_stats()
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._update_size_stats()

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        with self._lock:
            if key not in self._cache:
                return False
            return not self._cache[key].is_expired()

    def keys(self) -> List[str]:
        """Get all valid cache keys."""
        with self._lock:
            return [k for k, v in self._cache.items() if not v.is_expired()]

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {**self._stats, "entries": len(self._cache), "config": self.config}

    def _estimate_size(self, value: Any) -> int:
        """Estimate size of value in bytes."""
        try:
            if hasattr(value, "__sizeof__"):
                return value.__sizeof__()
            return len(str(value))
        except Exception:
            return 100  # Default estimate

    def _should_evict(self) -> bool:
        """Check if eviction is needed."""
        if self.config.max_entries and len(self._cache) >= self.config.max_entries:
            return True

        if self.config.max_size_mb:
            current_mb = self._stats["size_bytes"] / (1024 * 1024)
            if current_mb >= self.config.max_size_mb:
                return True

        return False

    def _evict_entries(self) -> None:
        """Evict entries based on policy."""
        if not self._cache:
            return

        # Remove expired entries first
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired_keys:
            del self._cache[key]

        # If still need to evict, use policy
        if self._should_evict():
            if self.config.eviction_policy == "lru":
                # Remove least recently used
                key_to_remove = min(self._cache.keys(), key=lambda k: self._cache[k].last_accessed)
            elif self.config.eviction_policy == "lfu":
                # Remove least frequently used
                key_to_remove = min(self._cache.keys(), key=lambda k: self._cache[k].access_count)
            else:  # fifo
                # Remove oldest
                key_to_remove = min(self._cache.keys(), key=lambda k: self._cache[k].timestamp)

            del self._cache[key_to_remove]
            self._stats["evictions"] += 1

    def _update_size_stats(self) -> None:
        """Update size statistics."""
        self._stats["size_bytes"] = sum(entry.size_bytes for entry in self._cache.values())


class DiskCache(CacheInterface[T]):
    """Disk-based cache implementation."""

    def __init__(self, config: CacheConfig, cache_dir: Optional[Path] = None):
        self.config = config
        self.cache_dir = cache_dir or get_cache_dir(config.name)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.index_file = self.cache_dir / "cache_index.json"
        self._index: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

        self._load_index()

        if config.auto_cleanup:
            self._cleanup_expired()

    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """Get value from disk cache."""
        with self._lock:
            if key not in self._index:
                return default

            entry_info = self._index[key]

            # Check expiry
            if entry_info.get("ttl") and time.time() - entry_info["timestamp"] > entry_info["ttl"]:
                self._remove_entry(key)
                return default

            # Load from disk
            try:
                file_path = self.cache_dir / f"{self._hash_key(key)}.cache"

                if not file_path.exists():
                    self._remove_entry(key)
                    return default

                value = self._deserialize(file_path)

                # Update access stats
                entry_info["access_count"] = entry_info.get("access_count", 0) + 1
                entry_info["last_accessed"] = time.time()
                self._save_index()

                return value

            except Exception as e:
                logger.warning(f"Failed to load cache entry {key}: {e}")
                self._remove_entry(key)
                return default

    def set(self, key: str, value: T, ttl: Optional[float] = None) -> None:
        """Set value in disk cache."""
        with self._lock:
            try:
                ttl = ttl or self.config.ttl_seconds
                file_path = self.cache_dir / f"{self._hash_key(key)}.cache"

                # Serialize to disk
                self._serialize(file_path, value)

                # Update index
                self._index[key] = {
                    "timestamp": time.time(),
                    "ttl": ttl,
                    "file_path": str(file_path),
                    "access_count": 0,
                    "last_accessed": time.time(),
                    "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
                }

                self._save_index()

            except Exception as e:
                logger.error(f"Failed to save cache entry {key}: {e}")

    def delete(self, key: str) -> bool:
        """Delete value from disk cache."""
        with self._lock:
            if key in self._index:
                self._remove_entry(key)
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            for key in list(self._index.keys()):
                self._remove_entry(key)

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        with self._lock:
            return key in self._index and not self._is_expired(key)

    def keys(self) -> List[str]:
        """Get all valid cache keys."""
        with self._lock:
            return [k for k in self._index.keys() if not self._is_expired(k)]

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_size = sum(info.get("size_bytes", 0) for info in self._index.values())

            return {
                "entries": len(self._index),
                "total_size_bytes": total_size,
                "cache_dir": str(self.cache_dir),
                "config": self.config,
            }

    def _load_index(self) -> None:
        """Load cache index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r") as f:
                    self._index = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache index: {e}")
                self._index = {}

    def _save_index(self) -> None:
        """Save cache index to disk."""
        try:
            with open(self.index_file, "w") as f:
                json.dump(self._index, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")

    def _serialize(self, file_path: Path, value: T) -> None:
        """Serialize value to disk."""
        if self.config.serialization == SerializationFormat.JSON:
            with open(file_path, "w") as f:
                json.dump(value, f)
        elif self.config.serialization == SerializationFormat.PICKLE:
            with open(file_path, "wb") as f:
                pickle.dump(value, f)
        else:  # RAW
            if isinstance(value, bytes):
                with open(file_path, "wb") as f:
                    f.write(value)
            else:
                with open(file_path, "w") as f:
                    f.write(str(value))

    def _deserialize(self, file_path: Path) -> T:
        """Deserialize value from disk."""
        if self.config.serialization == SerializationFormat.JSON:
            with open(file_path, "r") as f:
                return json.load(f)
        elif self.config.serialization == SerializationFormat.PICKLE:
            with open(file_path, "rb") as f:
                return pickle.load(f)
        else:  # RAW
            try:
                with open(file_path, "rb") as f:
                    return f.read()
            except Exception:
                with open(file_path, "r") as f:
                    return f.read()

    def _hash_key(self, key: str) -> str:
        """Hash key to safe filename."""
        return hashlib.md5(key.encode()).hexdigest()

    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired."""
        if key not in self._index:
            return True

        entry_info = self._index[key]
        ttl = entry_info.get("ttl")

        if ttl is None:
            return False

        return time.time() - entry_info["timestamp"] > ttl

    def _remove_entry(self, key: str) -> None:
        """Remove cache entry from disk and index."""
        if key in self._index:
            entry_info = self._index[key]
            file_path = Path(entry_info["file_path"])

            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete cache file {file_path}: {e}")

            del self._index[key]
            self._save_index()

    def _cleanup_expired(self) -> None:
        """Clean up expired entries."""
        expired_keys = [k for k in self._index.keys() if self._is_expired(k)]
        for key in expired_keys:
            self._remove_entry(key)


class CacheManager(RecoveryEnhancedMixin):
    """Unified cache management system for rxiv-maker.

    Features:
    - Multiple cache instances with different configurations
    - Memory, disk, and hybrid caching strategies
    - Automatic cleanup and eviction policies
    - Thread-safe operations
    - Performance monitoring and statistics
    - Migration from legacy cache systems
    """

    def __init__(self):
        """Initialize cache manager."""
        super().__init__()
        self._caches: Dict[str, CacheInterface] = {}
        self._configs: Dict[str, CacheConfig] = {}
        self._lock = threading.RLock()

        # Register built-in cache instances
        self._register_builtin_caches()

        logger.debug("CacheManager initialized")

    def _register_builtin_caches(self) -> None:
        """Register built-in cache instances."""
        # DOI metadata cache
        self.create_cache(
            CacheConfig(
                name="doi",
                cache_type=CacheType.DISK,
                serialization=SerializationFormat.JSON,
                ttl_seconds=30 * 24 * 3600,  # 30 days
                max_size_mb=10,
                eviction_policy="lru",
            )
        )

        # Figure checksum cache
        self.create_cache(
            CacheConfig(
                name="figures",
                cache_type=CacheType.DISK,
                serialization=SerializationFormat.JSON,
                ttl_seconds=None,  # No expiry for checksums
                max_entries=1000,
                eviction_policy="lru",
            )
        )

        # Validation results cache
        self.create_cache(
            CacheConfig(
                name="validation",
                cache_type=CacheType.MEMORY,
                serialization=SerializationFormat.PICKLE,
                ttl_seconds=3600,  # 1 hour
                max_entries=100,
                eviction_policy="lru",
            )
        )

        # Build artifacts cache
        self.create_cache(
            CacheConfig(
                name="build",
                cache_type=CacheType.DISK,
                serialization=SerializationFormat.PICKLE,
                ttl_seconds=7 * 24 * 3600,  # 7 days
                max_size_mb=50,
                eviction_policy="lru",
            )
        )

        # Session cache (temporary data)
        self.create_cache(
            CacheConfig(
                name="session",
                cache_type=CacheType.MEMORY,
                serialization=SerializationFormat.PICKLE,
                ttl_seconds=1800,  # 30 minutes
                max_entries=50,
                eviction_policy="lru",
            )
        )

    def create_cache(self, config: CacheConfig) -> CacheInterface:
        """Create a new cache instance.

        Args:
            config: Cache configuration

        Returns:
            Created cache instance
        """
        with self._lock:
            if config.cache_type == CacheType.MEMORY:
                cache = MemoryCache(config)
            elif config.cache_type == CacheType.DISK:
                cache = DiskCache(config)
            else:  # HYBRID
                # TODO: Implement hybrid cache (memory + disk)
                cache = DiskCache(config)

            self._caches[config.name] = cache
            self._configs[config.name] = config

            logger.debug(f"Created cache: {config.name} ({config.cache_type.value})")
            return cache

    def get_cache(self, name: str) -> Optional[CacheInterface]:
        """Get cache instance by name.

        Args:
            name: Cache name

        Returns:
            Cache instance or None if not found
        """
        return self._caches.get(name)

    def list_caches(self) -> List[str]:
        """List all cache names.

        Returns:
            List of cache names
        """
        return list(self._caches.keys())

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all caches.

        Returns:
            Dictionary mapping cache names to statistics
        """
        return {name: cache.stats() for name, cache in self._caches.items()}

    def clear_all(self) -> None:
        """Clear all caches."""
        with self._lock:
            for cache in self._caches.values():
                cache.clear()

        logger.info("Cleared all caches")

    def cleanup_expired(self) -> None:
        """Clean up expired entries across all caches."""
        # Memory caches handle this automatically
        # Disk caches need explicit cleanup
        for _name, cache in self._caches.items():
            if isinstance(cache, DiskCache):
                cache._cleanup_expired()

        logger.debug("Cleaned up expired cache entries")


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance.

    Returns:
        Global cache manager
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


# Convenience functions for common cache operations
def cache_doi(doi: str, metadata: Dict[str, Any], ttl: Optional[float] = None) -> None:
    """Cache DOI metadata.

    Args:
        doi: DOI identifier
        metadata: DOI metadata
        ttl: Time to live override
    """
    cache = get_cache_manager().get_cache("doi")
    if cache:
        cache.set(doi, metadata, ttl)


def get_cached_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Get cached DOI metadata.

    Args:
        doi: DOI identifier

    Returns:
        Cached metadata or None
    """
    cache = get_cache_manager().get_cache("doi")
    if cache:
        return cache.get(doi)
    return None


def cache_figure_checksum(figure_path: str, checksum: str) -> None:
    """Cache figure checksum.

    Args:
        figure_path: Path to figure
        checksum: Figure checksum
    """
    cache = get_cache_manager().get_cache("figures")
    if cache:
        cache.set(figure_path, checksum)


def get_cached_figure_checksum(figure_path: str) -> Optional[str]:
    """Get cached figure checksum.

    Args:
        figure_path: Path to figure

    Returns:
        Cached checksum or None
    """
    cache = get_cache_manager().get_cache("figures")
    if cache:
        return cache.get(figure_path)
    return None


# Export public API
__all__ = [
    "CacheManager",
    "CacheType",
    "SerializationFormat",
    "CacheConfig",
    "CacheInterface",
    "get_cache_manager",
    "cache_doi",
    "get_cached_doi",
    "cache_figure_checksum",
    "get_cached_figure_checksum",
]
