"""Deprecated global container manager - now raises errors for container engine usage.

This module previously provided centralized container engine management.
Container engines have been deprecated in favor of local-only execution.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class GlobalContainerManager:
    """Deprecated singleton manager - container engines no longer supported."""

    _instance = None

    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the deprecated container manager."""
        pass

    def get_container_engine(self, engine_type: str, workspace_dir: Optional[Path] = None):
        """Deprecated method that raises an error."""
        raise RuntimeError(
            f"Container engine '{engine_type}' is no longer supported. "
            "Docker and Podman engines have been deprecated. "
            "For containerized execution, please run rxiv-maker from within a Docker container. "
            "See the documentation for migration instructions."
        )

    def get_engine_stats(self) -> Dict[str, Any]:
        """Returns empty stats since no container engines are supported."""
        return {
            "cached_engines": 0,
            "engines": [],
            "session_config": {"mode": "deprecated", "session_timeout": 0, "max_sessions": 0},
        }

    def cleanup_all_engines(self) -> int:
        """No cleanup needed since no engines are active."""
        return 0


def get_global_container_manager() -> GlobalContainerManager:
    """Get the global container manager instance (deprecated)."""
    return GlobalContainerManager()


def cleanup_global_containers() -> int:
    """Deprecated function - no containers to clean up."""
    return 0
