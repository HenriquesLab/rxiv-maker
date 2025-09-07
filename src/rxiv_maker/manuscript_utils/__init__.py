"""Manuscript utilities for rxiv-maker.

This module provides utility functions that can be called from manuscript Python code
to perform common tasks like figure generation, data processing, and document management.
"""

from .figure_utils import (
    convert_figures_bulk,
    convert_mermaid,
    convert_python_figure,
    convert_r_figure,
)

__all__ = [
    "convert_mermaid",
    "convert_python_figure",
    "convert_r_figure",
    "convert_figures_bulk",
]
