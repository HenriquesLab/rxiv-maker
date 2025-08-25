"""Docker container engine implementation."""

import logging
import time
from pathlib import Path

from .abstract import AbstractContainerEngine, ContainerSession

logger = logging.getLogger(__name__)


class DockerSession(ContainerSession):
    """Docker-specific container session implementation."""

    def __init__(self, container_id: str, image: str, workspace_dir: Path):
        super().__init__(container_id, image, workspace_dir, "docker")
        self.created_at = time.time()


class DockerEngine(AbstractContainerEngine):
    """Docker container engine implementation."""

    @property
    def engine_name(self) -> str:
        """Return the name of the container engine."""
        return "docker"

    # Note: check_available() method is now inherited from AbstractContainerEngine base class

    # Note: pull_image() method is now inherited from AbstractContainerEngine base class

    # Note: run_command() is now inherited from AbstractContainerEngine

    # Note: _build_container_command() is now inherited from AbstractContainerEngine

    def _create_session_instance(self, container_id: str, image: str, workspace_dir: Path) -> "DockerSession":
        """Create a Docker-specific session instance."""
        return DockerSession(container_id, image, workspace_dir)

    # Note: _get_or_create_session() is now inherited from AbstractContainerEngine
