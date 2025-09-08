"""Deprecated container engine factory - now local-only execution."""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_container_engine(
    engine_type: Optional[str] = None,
    workspace_dir: Optional[Path] = None,
    **kwargs,
):
    """Deprecated function that previously provided container engines.

    Docker and Podman engines have been deprecated in favor of local-only execution.
    Users who need containerized execution should run rxiv-maker from within a Docker container.

    Args:
        engine_type: Ignored - was previously 'docker' or 'podman'
        workspace_dir: Ignored - was workspace directory
        **kwargs: Ignored - were additional engine options

    Raises:
        RuntimeError: Always raises to indicate deprecation
    """
    if engine_type in ["docker", "podman"]:
        raise RuntimeError(
            f"Container engine '{engine_type}' is no longer supported. "
            "Docker and Podman engines have been deprecated. "
            "For containerized execution, please run rxiv-maker from within a Docker container. "
            "See the documentation for migration instructions."
        )

    # Even for local engine requests, we don't want to return anything since the architecture has changed
    raise RuntimeError(
        "Container engine factory has been deprecated. "
        "Rxiv-maker now uses local-only execution. "
        "Please update your code to use the local execution path directly."
    )


# Legacy compatibility - deprecated
class ContainerEngineFactory:
    """Deprecated - container engines are no longer supported."""

    @classmethod
    def create_engine(cls, engine_type: str, **kwargs):
        """Deprecated method."""
        return get_container_engine(engine_type, **kwargs)

    @classmethod
    def get_default_engine(cls, **kwargs):
        """Deprecated method."""
        return get_container_engine(None, **kwargs)

    @classmethod
    def list_available_engines(cls):
        """Returns empty dict as no container engines are available."""
        return {}

    @classmethod
    def get_supported_engines(cls):
        """Returns empty list as no container engines are supported."""
        return []


# For backward compatibility
container_engine_factory = ContainerEngineFactory()
