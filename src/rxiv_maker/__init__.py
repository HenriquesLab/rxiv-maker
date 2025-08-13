"""Rxiv-Maker Python Package.

A comprehensive toolkit for automated scientific article generation and building.
"""

from .__version__ import __version__


# Maintain backward compatibility
def get_version():
    """Get version information."""
    return __version__


def get_versions():
    """Get version information in versioneer-compatible format."""
    return {"version": __version__}


__author__ = "Rxiv-Maker Contributors"
