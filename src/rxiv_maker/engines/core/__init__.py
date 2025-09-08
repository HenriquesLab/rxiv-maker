"""Deprecated container engine abstractions - now local-only execution.

This module previously provided container engine abstractions for Docker and Podman.
These have been deprecated in favor of local-only execution.
"""

# Import for backward compatibility - these will raise RuntimeError when used
from .exceptions import ContainerEngineError
from .factory import get_container_engine

# Keep abstract classes for any remaining references but they're deprecated
try:
    from .abstract import AbstractContainerEngine, ContainerSession
except ImportError:
    # In case abstract.py gets removed in the future
    AbstractContainerEngine = None  # type: ignore
    ContainerSession = None  # type: ignore

__all__ = [
    "get_container_engine",  # Deprecated - raises RuntimeError
    "ContainerEngineError",
    # Removed: DockerEngine, PodmanEngine (deleted)
    # Kept for compatibility: AbstractContainerEngine, ContainerSession (deprecated)
]

# Note for developers: Container engines have been deprecated.
# Rxiv-maker now uses local-only execution for better simplicity and reliability.
# Users who need containerized execution should run rxiv-maker from within a Docker container.
