"""Podman container engine implementation."""

import logging
import time
from pathlib import Path

from .abstract import AbstractContainerEngine, ContainerSession

logger = logging.getLogger(__name__)


class PodmanSession(ContainerSession):
    """Podman-specific container session implementation."""

    def __init__(self, container_id: str, image: str, workspace_dir: Path):
        super().__init__(container_id, image, workspace_dir, "podman")
        self.created_at = time.time()

    # Note: is_active() and cleanup() methods are now inherited from ContainerSession base class


class PodmanEngine(AbstractContainerEngine):
    """Podman container engine implementation.

    Podman has a Docker-compatible API but needs its own engine implementation
    to handle rootless containers and other Podman-specific behavior.
    """

    @property
    def engine_name(self) -> str:
        """Return the name of the container engine."""
        return "podman"

    # Note: check_available() method is now inherited from AbstractContainerEngine base class

    # Note: pull_image() method is now inherited from AbstractContainerEngine base class

    # Note: _build_container_command() is now inherited from AbstractContainerEngine

    def _create_session_instance(self, container_id: str, image: str, workspace_dir: Path) -> "PodmanSession":
        """Create a Podman-specific session instance."""
        return PodmanSession(container_id, image, workspace_dir)

    # Note: _get_or_create_session() is now inherited from AbstractContainerEngine

    # Note: run_command() is now inherited from AbstractContainerEngine
