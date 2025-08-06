"""Command-line interface modules for Rxiv-Maker.

This package contains the main executable scripts for article and figure generation.
"""

from .generate_figures import FigureGenerator
from .generate_preprint import generate_preprint

__all__ = ["generate_preprint", "FigureGenerator"]
