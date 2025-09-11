"""Universal system dependency installer for rxiv-maker.

This module provides cross-platform installation and management of system dependencies
required by rxiv-maker, including LaTeX, R, and system libraries.
"""

from .utils.verification import verify_installation


# Avoid circular import - InstallManager will be imported on-demand
def get_install_manager():
    """Get InstallManager with lazy import to avoid circular dependency."""
    from ..core.managers.install_manager import InstallManager

    return InstallManager


__all__ = ["get_install_manager", "verify_installation"]
