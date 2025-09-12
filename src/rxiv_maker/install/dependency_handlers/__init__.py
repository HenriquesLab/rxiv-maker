"""Dependency-specific installation handlers."""

from .latex import LaTeXHandler
from .r_lang import RLanguageHandler
from .system_libs import SystemLibsHandler

__all__ = ["LaTeXHandler", "RLanguageHandler", "SystemLibsHandler"]
