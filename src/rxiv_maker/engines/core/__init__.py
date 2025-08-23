"""Container engine abstractions for rxiv-maker.

This module provides a unified interface for different container engines
(Docker, Podman, etc.) used by rxiv-maker for containerized operations.
"""

from .abstract import AbstractContainerEngine, ContainerSession
from .docker_engine import DockerEngine
from .exceptions import ContainerEngineError
from .factory import get_container_engine
from .podman_engine import PodmanEngine

__all__ = [
    "AbstractContainerEngine",
    "ContainerSession",
    "DockerEngine",
    "PodmanEngine",
    "get_container_engine",
    "ContainerEngineError",
]
