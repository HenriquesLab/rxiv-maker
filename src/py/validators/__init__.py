"""Validation system for rxiv-maker manuscripts.

This package provides comprehensive validation for markdown manuscripts,
YAML configuration, and LaTeX compilation errors.
"""

from .base_validator import (
    BaseValidator,
    ValidationError,
    ValidationLevel,
    ValidationResult,
)
from .citation_validator import CitationValidator
from .figure_validator import FigureValidator
from .latex_error_parser import LaTeXErrorParser
from .math_validator import MathValidator
from .reference_validator import ReferenceValidator
from .syntax_validator import SyntaxValidator

__all__ = [
    "BaseValidator",
    "ValidationResult",
    "ValidationError",
    "ValidationLevel",
    "LaTeXErrorParser",
    "CitationValidator",
    "ReferenceValidator",
    "FigureValidator",
    "MathValidator",
    "SyntaxValidator",
]
