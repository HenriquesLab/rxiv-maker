"""Core operations for manuscript processing and PDF generation.

This package contains all the core operations used by rxiv-maker for
manuscript processing, bibliography management, figure generation, and PDF compilation.
"""

# Core generation operations
# Bibliography operations
from .add_bibliography import BibliographyAdder
from .analyze_word_count import analyze_manuscript_word_count
from .build_manager import BuildManager
from .cleanup import CleanupManager

# Utility operations
from .copy_pdf import copy_pdf_with_custom_filename
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
    "analyze_manuscript_word_count",
    # Publishing
    "prepare_arxiv_package",
    "TrackChangesManager",
    # Utilities
    "copy_pdf_with_custom_filename",
    "CleanupManager",
    "EnvironmentSetup",
    "generate_api_docs",
]
