"""Docker management utilities for Rxiv-Maker."""

from .build_manager import DockerBuildManager, DockerBuildMode, build_docker_image
from .manager import (
    DockerManager,
    DockerSession,
    cleanup_global_docker_manager,
    get_docker_manager,
    get_docker_stats,
)
from .optimization import DockerBuildOptimizer, DockerResourceManager

__all__ = [
    # Core Docker management
    "DockerManager",
    "DockerSession",
    "get_docker_manager",
    "cleanup_global_docker_manager",
    "get_docker_stats",
    # Build management
    "DockerBuildManager",
    "DockerBuildMode",
    "build_docker_image",
    # Optimization utilities
    "DockerBuildOptimizer",
    "DockerResourceManager",
]
