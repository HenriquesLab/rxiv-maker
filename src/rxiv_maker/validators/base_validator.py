"""Base validator class and common validation types."""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ValidationLevel(Enum):
    """Validation result severity levels."""

    ERROR = "error"  # Blocks manuscript processing
    WARNING = "warning"  # Should be addressed but doesn't block
    INFO = "info"  # Informational message
    SUCCESS = "success"  # Validation passed


@dataclass
class ValidationError:
    """Represents a single validation issue."""

    level: ValidationLevel
    message: str
    file_path: str | None = None
    line_number: int | None = None
    column: int | None = None
    context: str | None = None
    suggestion: str | None = None
    error_code: str | None = None

    def __str__(self) -> str:
        """Format validation error for display."""
        parts = []

        # Add severity level
        parts.append(f"[{self.level.value.upper()}]")

        # Add location if available
        if self.file_path:
            location = os.path.basename(self.file_path)
            if self.line_number:
                location += f":{self.line_number}"
                if self.column:
                    location += f":{self.column}"
            parts.append(f"({location})")

        # Add main message
        parts.append(self.message)

        result = " ".join(parts)

        # Add context if available
        if self.context:
            result += f"\n  Context: {self.context}"

        # Add suggestion if available
        if self.suggestion:
            result += f"\n  Suggestion: {self.suggestion}"

        return result


@dataclass
class ValidationResult:
    """Results from a validation operation."""

    validator_name: str
    errors: list[ValidationError]
    metadata: dict[str, Any]

    @property
    def has_errors(self) -> bool:
        """Check if there are any error-level issues."""
        return any(error.level == ValidationLevel.ERROR for error in self.errors)

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warning-level issues."""
        return any(error.level == ValidationLevel.WARNING for error in self.errors)

    @property
    def error_count(self) -> int:
        """Count of error-level issues."""
        return sum(1 for error in self.errors if error.level == ValidationLevel.ERROR)

    @property
    def warning_count(self) -> int:
        """Count of warning-level issues."""
        return sum(1 for error in self.errors if error.level == ValidationLevel.WARNING)

    def get_errors_by_level(self, level: ValidationLevel) -> list[ValidationError]:
        """Get all errors of a specific level."""
        return [error for error in self.errors if error.level == level]


class BaseValidator(ABC):
    """Abstract base class for all validators."""

    def __init__(self, manuscript_path: str):
        """Initialize validator with manuscript path.

        Args:
            manuscript_path: Path to the manuscript directory
        """
        self.manuscript_path = manuscript_path
        self.name = self.__class__.__name__

    @abstractmethod
    def validate(self) -> ValidationResult:
        """Perform validation and return results.

        Returns:
            ValidationResult with any issues found
        """
        pass

    def _create_error(
        self,
        level: ValidationLevel,
        message: str,
        file_path: str | None = None,
        line_number: int | None = None,
        column: int | None = None,
        context: str | None = None,
        suggestion: str | None = None,
        error_code: str | None = None,
    ) -> ValidationError:
        """Helper to create validation errors.

        Note: This method is deprecated in favor of using create_validation_error
        with structured ErrorCode enums for better consistency.
        """
        return ValidationError(
            level=level,
            message=message,
            file_path=file_path,
            line_number=line_number,
            column=column,
            context=context,
            suggestion=suggestion,
            error_code=error_code,
        )

    def _read_file_safely(self, file_path: str) -> str | None:
        """Safely read a file, returning None if it fails."""
        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # LaTeX log files may be in latin-1 encoding, try fallback
            try:
                with open(file_path, encoding="latin-1") as f:
                    return f.read()
            except OSError:
                return None
        except OSError:
            return None

    def _get_line_context(self, content: str, line_number: int, context_lines: int = 2) -> str:
        """Get context around a specific line number."""
        lines = content.split("\n")
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)

        context_lines_list = []
        for i in range(start, end):
            prefix = ">>> " if i == line_number - 1 else "    "
            context_lines_list.append(f"{prefix}{i + 1:4d}: {lines[i]}")

        return "\n".join(context_lines_list)
