"""Factory for creating container engine instances."""

import atexit
import logging
import os
import weakref
from pathlib import Path
from typing import Dict, Optional, Set, Type

from .abstract import AbstractContainerEngine
from .docker_engine import DockerEngine
from .exceptions import ContainerEngineError
from .podman_engine import PodmanEngine

logger = logging.getLogger(__name__)


class ContainerEngineFactory:
    """Factory class for creating container engine instances."""

    # Registry of available engines
    _engines: Dict[str, Type[AbstractContainerEngine]] = {
        "docker": DockerEngine,
        "podman": PodmanEngine,
    }

    # Registry to track active engine instances for cleanup
    _active_engines: Set[weakref.ReferenceType] = set()
    _cleanup_registered = False

    @classmethod
    def create_engine(
        cls,
        engine_type: str,
        default_image: str = "henriqueslab/rxiv-maker-base:latest",
        workspace_dir: Optional[Path] = None,
        enable_session_reuse: bool = True,
        memory_limit: str = "2g",
        cpu_limit: str = "2.0",
        **kwargs,
    ) -> AbstractContainerEngine:
        """Create a container engine instance.

        Args:
            engine_type: Type of engine to create ('docker' or 'podman')
            default_image: Default container image to use
            workspace_dir: Workspace directory (defaults to current working directory)
            enable_session_reuse: Whether to reuse containers across operations
            memory_limit: Memory limit for containers (e.g., "2g", "512m")
            cpu_limit: CPU limit for containers (e.g., "2.0" for 2 cores)
            **kwargs: Additional arguments passed to the engine constructor

        Returns:
            Container engine instance

        Raises:
            ValueError: If engine_type is not supported
            RuntimeError: If the requested engine is not available
        """
        engine_type_lower = engine_type.lower()

        if engine_type_lower not in cls._engines:
            available_engines = list(cls._engines.keys())
            raise ValueError(f"Unsupported engine type: {engine_type}. Available engines: {available_engines}")

        engine_class = cls._engines[engine_type_lower]

        # Create engine instance
        engine = engine_class(
            default_image=default_image,
            workspace_dir=workspace_dir,
            enable_session_reuse=enable_session_reuse,
            memory_limit=memory_limit,
            cpu_limit=cpu_limit,
            **kwargs,
        )

        # Check if engine is available with detailed error handling
        try:
            if not engine.check_available():
                raise RuntimeError(
                    f"{engine_type.title()} is not available. Please ensure {engine_type} is installed and running."
                )
        except ContainerEngineError:
            # Re-raise our custom exceptions with their helpful error messages
            raise
        except Exception as e:
            # Catch any other unexpected errors
            logger.debug(f"Unexpected error checking {engine_type} availability: {e}")
            raise RuntimeError(f"Failed to check {engine_type.title()} availability: {e}") from e

        # Register engine for cleanup
        cls._register_engine_instance(engine)

        return engine

    @classmethod
    def get_default_engine(
        cls,
        workspace_dir: Optional[Path] = None,
        **kwargs,
    ) -> AbstractContainerEngine:
        """Get the default container engine based on environment and availability.

        Priority order:
        1. RXIV_ENGINE environment variable
        2. Docker if available
        3. Podman if available
        4. Raise error if no container engine is available

        Args:
            workspace_dir: Workspace directory (defaults to current working directory)
            **kwargs: Additional arguments passed to the engine constructor

        Returns:
            Container engine instance

        Raises:
            RuntimeError: If no container engines are available
        """
        # Check environment variable first
        env_engine = os.environ.get("RXIV_ENGINE", "").lower()
        if env_engine in cls._engines:
            try:
                return cls.create_engine(env_engine, workspace_dir=workspace_dir, **kwargs)
            except RuntimeError as e:
                # Engine specified in env var is not available, continue to auto-detect
                logging.warning(f"Engine '{env_engine}' specified in environment variable is not available: {e}")

        # Auto-detect available engines in priority order
        priority_engines = ["docker", "podman"]

        for engine_type in priority_engines:
            if engine_type in cls._engines:
                engine_class = cls._engines[engine_type]
                # Create a minimal instance just for availability check
                temp_engine = engine_class(workspace_dir=workspace_dir or Path.cwd())
                if temp_engine.check_available():
                    return cls.create_engine(engine_type, workspace_dir=workspace_dir, **kwargs)

        # No engines available
        available_engines = list(cls._engines.keys())
        raise RuntimeError(f"No container engines are available. Please install one of: {available_engines}")

    @classmethod
    def list_available_engines(cls) -> Dict[str, bool]:
        """List all available engines and their availability status.

        Returns:
            Dictionary mapping engine names to their availability status
        """
        availability = {}

        for engine_name, engine_class in cls._engines.items():
            try:
                # Create a minimal instance just for availability check
                temp_engine = engine_class()
                availability[engine_name] = temp_engine.check_available()
            except Exception:
                availability[engine_name] = False

        return availability

    @classmethod
    def register_engine(
        cls,
        engine_name: str,
        engine_class: Type[AbstractContainerEngine],
    ) -> None:
        """Register a new container engine type.

        Args:
            engine_name: Name of the engine
            engine_class: Engine class that inherits from AbstractContainerEngine

        Raises:
            ValueError: If engine_class doesn't inherit from AbstractContainerEngine
        """
        if not issubclass(engine_class, AbstractContainerEngine):
            raise ValueError(f"Engine class must inherit from AbstractContainerEngine, got {engine_class.__name__}")

        cls._engines[engine_name.lower()] = engine_class

    @classmethod
    def get_supported_engines(cls) -> list[str]:
        """Get a list of all supported engine names.

        Returns:
            List of supported engine names
        """
        return list(cls._engines.keys())

    @classmethod
    def _register_engine_instance(cls, engine: AbstractContainerEngine) -> None:
        """Register an engine instance for cleanup tracking.

        Args:
            engine: Container engine instance to track
        """
        # Register cleanup handler only once
        if not cls._cleanup_registered:
            atexit.register(cls.cleanup_all_engines)
            cls._cleanup_registered = True

        # Use weak reference to avoid keeping engines alive unnecessarily
        engine_ref = weakref.ref(engine)
        cls._active_engines.add(engine_ref)

    @classmethod
    def cleanup_all_engines(cls) -> int:
        """Clean up all active container engines and their sessions.

        This method is typically called automatically on program exit,
        but can also be called manually for explicit cleanup.

        Returns:
            Number of engines successfully cleaned up
        """
        logger.debug("Cleaning up active container engines...")

        # Create a copy to avoid modification during iteration
        active_refs = cls._active_engines.copy()
        cls._active_engines.clear()

        cleanup_count = 0
        for engine_ref in active_refs:
            engine = engine_ref()
            if engine is not None:
                try:
                    logger.debug(f"Cleaning up {engine.engine_name} engine sessions...")
                    engine.cleanup_all_sessions()
                    cleanup_count += 1
                except Exception as e:
                    logger.debug(f"Error cleaning up {engine.engine_name} engine: {e}")

        if cleanup_count > 0:
            logger.debug(f"Successfully cleaned up {cleanup_count} container engines")

        return cleanup_count

    @classmethod
    def manual_cleanup(cls) -> None:
        """Manually trigger cleanup of all engines.

        This is useful for explicit cleanup in CLI commands or tests.
        """
        cls.cleanup_all_engines()


# Global factory instance for convenience
container_engine_factory = ContainerEngineFactory()


def get_container_engine(
    engine_type: Optional[str] = None,
    workspace_dir: Optional[Path] = None,
    **kwargs,
) -> AbstractContainerEngine:
    """Convenience function to get a container engine instance.

    Args:
        engine_type: Type of engine to create (None for auto-detection)
        workspace_dir: Workspace directory (defaults to current working directory)
        **kwargs: Additional arguments passed to the engine constructor

    Returns:
        Container engine instance
    """
    if engine_type:
        return container_engine_factory.create_engine(engine_type, workspace_dir=workspace_dir, **kwargs)
    else:
        return container_engine_factory.get_default_engine(workspace_dir=workspace_dir, **kwargs)
