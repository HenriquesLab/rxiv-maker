"""Unified engines package for rxiv-maker.

This package provides operations for manuscript processing,
focusing on local execution for simplicity and reliability.
"""

# Note: Container engines (Docker/Podman) have been deprecated.
# For containerized execution, use the docker-rxiv-maker repository.

# Core operations - manuscript processing functionality
from .operations import (
    # Bibliography
    BibliographyAdder,
    BibliographyFixer,
    BuildManager,
    CleanupManager,
    EnvironmentSetup,
    # Core generation
    FigureGenerator,
    PDFValidator,
    TrackChangesManager,
    analyze_manuscript_word_count,
    # Utilities
    copy_pdf_with_custom_filename,
    generate_api_docs,
    generate_preprint,
    # Publishing
    prepare_arxiv_package,
    # Validation
    validate_manuscript,
)

__all__ = [
    # Core operations
    "FigureGenerator",
    "generate_preprint",
    "BuildManager",
    "BibliographyAdder",
    "BibliographyFixer",
    "validate_manuscript",
    "PDFValidator",
    "analyze_manuscript_word_count",
    "prepare_arxiv_package",
    "TrackChangesManager",
    "copy_pdf_with_custom_filename",
    "CleanupManager",
    "EnvironmentSetup",
    "generate_api_docs",
]
