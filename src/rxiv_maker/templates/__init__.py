"""Template system for rxiv-maker manuscript initialization.

This module provides centralized template management for creating new manuscripts.
Templates include configuration files, main content, supplementary materials,
bibliography, figures, and other standard manuscript files.
"""

from .manager import TemplateManager, TemplateType, get_template_manager
from .registry import TemplateRegistry, get_template_registry

__all__ = [
    "TemplateManager",
    "TemplateType",
    "TemplateRegistry",
    "get_template_manager",
    "get_template_registry",
]
