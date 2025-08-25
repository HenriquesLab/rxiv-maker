"""Global container manager for singleton container engine instances.

This module provides a centralized way to manage container engines across
the entire CLI session, minimizing container creation and maximizing reuse.
"""

import atexit
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from ..engines.core.abstract import AbstractContainerEngine
from ..engines.core.factory import get_container_engine

logger = logging.getLogger(__name__)


class GlobalContainerManager:
    """Singleton manager for container engines across CLI session."""

    _instance = None
    _lock = threading.Lock()
    _engines: Dict[str, AbstractContainerEngine] = {}
    _initialized = False

    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the global container manager."""
        if not self._initialized:
            self._session_config = self._load_session_config()
            self._warmed_up = False
            GlobalContainerManager._initialized = True

    def _load_session_config(self) -> Dict[str, Any]:
        """Load container session configuration from environment."""
        return {
            # Container behavior mode: reuse (default), minimal, isolated
            "mode": os.environ.get("RXIV_CONTAINER_MODE", "reuse").lower(),
            # Session timeout in seconds (default: 20 minutes for better reuse)
            "session_timeout": int(os.environ.get("RXIV_SESSION_TIMEOUT", "1200")),
            # Maximum concurrent sessions (default: 3, most operations are sequential)
            "max_sessions": int(os.environ.get("RXIV_MAX_SESSIONS", "3")),
            # Memory limit per container
            "memory_limit": os.environ.get("RXIV_DOCKER_MEMORY", "2g"),
            # CPU limit per container
            "cpu_limit": os.environ.get("RXIV_DOCKER_CPU", "2.0"),
            # Whether to enable container warmup
            "enable_warmup": os.environ.get("RXIV_ENABLE_WARMUP", "true").lower() == "true",
        }

    def get_container_engine(
        self,
        engine_type: Optional[str] = None,
        workspace_dir: Optional[Path] = None,
        force_new: bool = False,
    ) -> AbstractContainerEngine:
        """Get or create a container engine instance.

        Args:
            engine_type: Type of engine ('docker', 'podman', or None for auto-detect)
            workspace_dir: Workspace directory (defaults to current working directory)
            force_new: Force creation of new engine instance

        Returns:
            Container engine instance
        """
        workspace_dir = workspace_dir or Path.cwd().resolve()

        # Create cache key based on engine type and workspace
        cache_key = f"{engine_type or 'auto'}:{workspace_dir}"

        # Return existing engine if available and not forcing new
        if not force_new and cache_key in self._engines:
            existing_engine = self._engines[cache_key]
            # Verify engine is still healthy
            try:
                if existing_engine.check_available():
                    logger.debug(f"Reusing existing container engine: {existing_engine.engine_name}")
                    return existing_engine
                else:
                    logger.debug("Existing engine unhealthy, creating new one")
                    # Remove unhealthy engine
                    del self._engines[cache_key]
            except Exception as e:
                logger.debug(f"Engine health check failed: {e}")
                del self._engines[cache_key]

        # Apply session configuration based on mode
        session_config = self._get_session_config_for_mode()

        # Create new engine instance
        logger.debug(f"Creating new container engine: {engine_type or 'auto'}")
        engine = get_container_engine(engine_type=engine_type, workspace_dir=workspace_dir, **session_config)

        # Apply our optimized session settings
        self._configure_engine_for_optimization(engine)

        # Cache the engine
        self._engines[cache_key] = engine

        # Warmup if enabled and this is the first engine
        if self._session_config["enable_warmup"] and not self._warmed_up:
            self._warmup_engine(engine)
            self._warmed_up = True

        logger.debug(f"Container engine ready: {engine.engine_name}")
        return engine

    def _get_session_config_for_mode(self) -> Dict[str, Any]:
        """Get session configuration based on container mode."""
        mode = self._session_config["mode"]

        if mode == "minimal":
            # Minimal mode: aggressive cleanup, no session reuse
            return {
                "enable_session_reuse": False,
                "memory_limit": "1g",
                "cpu_limit": "1.0",
            }
        elif mode == "isolated":
            # Isolated mode: each operation gets fresh container
            return {
                "enable_session_reuse": False,
                "memory_limit": self._session_config["memory_limit"],
                "cpu_limit": self._session_config["cpu_limit"],
            }
        else:  # reuse mode (default)
            # Reuse mode: maximize container reuse
            return {
                "enable_session_reuse": True,
                "memory_limit": self._session_config["memory_limit"],
                "cpu_limit": self._session_config["cpu_limit"],
            }

    def _configure_engine_for_optimization(self, engine: AbstractContainerEngine) -> None:
        """Configure engine with optimized session settings."""
        # Apply optimized timeouts and limits
        engine._session_timeout = self._session_config["session_timeout"]
        engine._max_sessions = self._session_config["max_sessions"]

        # Optimize cleanup frequency (check every 60 seconds instead of 30)
        engine._last_cleanup = time.time()

    def _warmup_engine(self, engine: AbstractContainerEngine) -> None:
        """Warmup container engine with a lightweight operation."""
        try:
            logger.debug("Warming up container engine...")
            start_time = time.time()

            # Use a lightweight warmup command
            result = engine.run_command(command=["echo", "container_warmup_ready"], session_key="general", timeout=30)

            if result.returncode == 0:
                warmup_time = time.time() - start_time
                logger.debug(f"Container engine warmed up in {warmup_time:.2f}s")
            else:
                logger.debug("Container warmup failed, but engine is available")

        except Exception as e:
            logger.debug(f"Container warmup failed: {e}")

    def cleanup_all_engines(self) -> int:
        """Clean up all cached container engines.

        Returns:
            Number of engines successfully cleaned up
        """
        logger.debug("Cleaning up all cached container engines...")
        cleanup_count = 0

        for cache_key, engine in list(self._engines.items()):
            try:
                engine.cleanup_all_sessions()
                cleanup_count += 1
                logger.debug(f"Cleaned up engine: {engine.engine_name}")
            except Exception as e:
                logger.debug(f"Failed to cleanup engine {engine.engine_name}: {e}")
            finally:
                # Remove from cache regardless of cleanup success
                del self._engines[cache_key]

        self._warmed_up = False
        logger.debug(f"Cleaned up {cleanup_count} container engines")
        return cleanup_count

    def get_engine_stats(self) -> Dict[str, Any]:
        """Get statistics about cached engines and their sessions.

        Returns:
            Dictionary with engine statistics
        """
        stats = {"cached_engines": len(self._engines), "session_config": self._session_config, "engines": []}

        for cache_key, engine in self._engines.items():
            try:
                engine_stats = engine.get_session_stats()
                stats["engines"].append(
                    {"cache_key": cache_key, "engine_name": engine.engine_name, "sessions": engine_stats}
                )
            except Exception as e:
                stats["engines"].append(
                    {"cache_key": cache_key, "engine_name": getattr(engine, "engine_name", "unknown"), "error": str(e)}
                )

        return stats

    def force_cleanup_sessions(self, engine_type: Optional[str] = None) -> int:
        """Force cleanup of sessions for specific engine type or all engines.

        Args:
            engine_type: Engine type to cleanup (None for all)

        Returns:
            Number of sessions cleaned up
        """
        cleanup_count = 0

        for _cache_key, engine in self._engines.items():
            if engine_type is None or engine.engine_name == engine_type:
                try:
                    engine.cleanup_all_sessions()
                    cleanup_count += 1
                except Exception as e:
                    logger.debug(f"Failed to cleanup sessions for {engine.engine_name}: {e}")

        return cleanup_count

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (useful for testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.cleanup_all_engines()
            cls._instance = None
            cls._engines.clear()
            cls._initialized = False


# Global instance
_global_manager = None


def get_global_container_manager() -> GlobalContainerManager:
    """Get the global container manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = GlobalContainerManager()
    return _global_manager


def cleanup_global_containers():
    """Cleanup all global container engines (called on exit)."""
    global _global_manager
    if _global_manager is not None:
        return _global_manager.cleanup_all_engines()
    return 0


# Register cleanup on module exit
atexit.register(cleanup_global_containers)
