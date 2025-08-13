"""Universal system dependency installer for rxiv-maker.

This module provides cross-platform installation and management of system dependencies
required by rxiv-maker, including LaTeX, Node.js, R, and system libraries.
"""

from .manager import InstallManager
from .utils.verification import verify_installation

__all__ = ["InstallManager", "verify_installation"]
