"""Consolidated managers package for rxiv-maker core functionality.

This package consolidates all manager classes that handle different aspects
of the rxiv-maker system: caching, dependencies, execution, resources, state,
validation, workflows, configuration, and installation.
"""

# Core system managers
from .cache_manager import get_cache_manager

# Specialized managers
from .config_manager import ConfigManager
from .dependency_manager import DependencyManager
from .execution_manager import ExecutionManager
from .install_manager import InstallManager
from .resource_manager import ResourceManager
from .state_manager import StateManager
from .validation_manager import ValidationManager
from .workflow_manager import WorkflowManager

__all__ = [
    # Core system managers
    "get_cache_manager",
    "DependencyManager",
    "ExecutionManager",
    "ResourceManager",
    "StateManager",
    "ValidationManager",
    "WorkflowManager",
    # Specialized managers
    "ConfigManager",
    "InstallManager",
]
