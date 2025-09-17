"""Core operations for manuscript processing and PDF generation.

This package contains all the core operations used by rxiv-maker for
manuscript processing, bibliography management, figure generation, and PDF compilation.
"""

# Core generation operations
# Bibliography operations
from .add_bibliography import BibliographyAdder
from .build_manager import BuildManager
from .cleanup import CleanupManager

# Utility operations
from .fix_bibliography import BibliographyFixer
from .generate_docs import generate_api_docs
from .generate_figures import FigureGenerator
from .generate_preprint import generate_preprint

# Publishing operations
from .prepare_arxiv import prepare_arxiv_package
from .setup_environment import EnvironmentSetup
from .track_changes import TrackChangesManager

# Validation and analysis
from .validate import validate_manuscript
from .validate_pdf import PDFValidator

__all__ = [
    # Core generation
    "FigureGenerator",
    "generate_preprint",
    "BuildManager",
    # Bibliography
    "BibliographyAdder",
    "BibliographyFixer",
    # Validation
    "validate_manuscript",
    "PDFValidator",
    # Publishing
    "prepare_arxiv_package",
    "TrackChangesManager",
    # Utilities
    "CleanupManager",
    "EnvironmentSetup",
    "generate_api_docs",
]
