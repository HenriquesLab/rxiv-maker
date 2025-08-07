"""LaTeX error parser for interpreting compilation errors."""

import os
import re
from dataclasses import dataclass
from typing import Any

from .base_validator import BaseValidator, ValidationLevel, ValidationResult


@dataclass
class LaTeXError:
    """Represents a LaTeX compilation error."""

    error_type: str
    message: str
    file_path: str | None = None
    line_number: int | None = None
    context: str | None = None
    raw_error: str | None = None


class LaTeXErrorParser(BaseValidator):
    """Parser for LaTeX compilation errors from log files."""

    # Common LaTeX error patterns with user-friendly explanations
    ERROR_PATTERNS = {
        r"Undefined control sequence": {
            "type": "undefined_command",
            "message": "Unknown LaTeX command used",
            "suggestion": "Check spelling of LaTeX commands or add required packages",
        },
        r"Missing \\begin\{document\}": {
            "type": "missing_begin_document",
            "message": "Document structure is incomplete",
            "suggestion": "Ensure the LaTeX template includes \\begin{document}",
        },
        r"File `([^']+)' not found": {
            "type": "missing_file",
            "message": "Referenced file cannot be found",
            "suggestion": "Check file paths and ensure all referenced files exist",
        },
        r"Package (\w+) Error": {
            "type": "package_error",
            "message": "LaTeX package error occurred",
            "suggestion": ("Check package usage and ensure required packages are installed"),
        },
        r"LaTeX Error: Environment (\w+) undefined": {
            "type": "undefined_environment",
            "message": "Unknown LaTeX environment used",
            "suggestion": "Check environment spelling or add required packages",
        },
        r"Runaway argument": {
            "type": "runaway_argument",
            "message": "Unmatched braces or missing closing delimiter",
            "suggestion": "Check for matching braces {} and proper command syntax",
        },
        r"Missing \$ inserted": {
            "type": "math_mode_error",
            "message": "Math expression not properly enclosed",
            "suggestion": "Ensure math expressions are wrapped in $ or $$ delimiters",
        },
        r"Extra \}, or forgotten \$": {
            "type": "brace_mismatch",
            "message": "Unmatched braces or math delimiters",
            "suggestion": "Check for matching braces and proper math mode delimiters",
        },
        r"Citation '([^']+)' on page \d+ undefined": {
            "type": "undefined_citation",
            "message": "Bibliography reference not found",
            "suggestion": "Check citation key exists in bibliography file",
        },
        r"Reference '([^']+)' on page \d+ undefined": {
            "type": "undefined_reference",
            "message": "Cross-reference label not found",
            "suggestion": "Check that referenced label exists and is properly defined",
        },
        r"Float too large": {
            "type": "oversized_float",
            "message": "Figure or table is too large for page",
            "suggestion": "Reduce figure size or use different positioning options",
        },
        r"Overfull \\hbox": {
            "type": "overfull_hbox",
            "message": "Text extends beyond page margins",
            "suggestion": ("This is often caused by long URLs or code that should be broken"),
        },
    }

    def __init__(self, manuscript_path: str, log_file_path: str | None = None):
        """Initialize LaTeX error parser.

        Args:
            manuscript_path: Path to manuscript directory
            log_file_path: Optional specific path to .log file
        """
        super().__init__(manuscript_path)
        self.log_file_path = log_file_path or self._find_log_file()

    def _find_log_file(self) -> str | None:
        """Find the LaTeX log file in output directory."""
        possible_paths = [
            os.path.join(self.manuscript_path, "output", "MANUSCRIPT.log"),
            os.path.join(self.manuscript_path, "MANUSCRIPT.log"),
            os.path.join("output", "MANUSCRIPT.log"),
            "MANUSCRIPT.log",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def validate(self) -> ValidationResult:
        """Parse LaTeX log file for errors and warnings."""
        errors = []
        metadata: dict[str, Any] = {"log_file": self.log_file_path}

        if not self.log_file_path or not os.path.exists(self.log_file_path):
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    "LaTeX log file not found - cannot analyze compilation errors",
                    suggestion="Run 'make pdf' to generate LaTeX compilation log",
                )
            )
            return ValidationResult("LaTeXErrorParser", errors, metadata)

        log_content = self._read_file_safely(self.log_file_path)
        if not log_content:
            errors.append(
                self._create_error(
                    ValidationLevel.ERROR,
                    "Failed to read LaTeX log file",
                    file_path=self.log_file_path,
                )
            )
            return ValidationResult("LaTeXErrorParser", errors, metadata)

        # Parse errors from log
        latex_errors = self._parse_log_file(log_content)

        # Convert to validation errors
        for latex_error in latex_errors:
            level = ValidationLevel.ERROR if latex_error.error_type != "warning" else ValidationLevel.WARNING

            errors.append(
                self._create_error(
                    level=level,
                    message=latex_error.message,
                    file_path=latex_error.file_path,
                    line_number=latex_error.line_number,
                    context=latex_error.context,
                    suggestion=self._get_error_suggestion(latex_error),
                    error_code=latex_error.error_type,
                )
            )

        # Add summary metadata
        metadata.update(
            {
                "total_errors": len([e for e in latex_errors if e.error_type != "warning"]),
                "total_warnings": len([e for e in latex_errors if e.error_type == "warning"]),
                "parsed_errors": len(latex_errors),
            }
        )

        return ValidationResult("LaTeXErrorParser", errors, metadata)

    def _parse_log_file(self, log_content: str) -> list[LaTeXError]:
        """Parse LaTeX log file content for errors."""
        errors = []
        lines = log_content.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Check for error patterns
            latex_error = self._parse_error_line(line, lines, i)
            if latex_error:
                errors.append(latex_error)

            i += 1

        return errors

    def _parse_error_line(self, line: str, all_lines: list[str], line_index: int) -> LaTeXError | None:
        """Parse a single line for LaTeX errors."""
        # Check each error pattern
        for pattern, error_info in self.ERROR_PATTERNS.items():
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                # Extract file and line info from surrounding context
                file_path, line_number = self._extract_location_info(all_lines, line_index)

                # Get additional context
                context = self._extract_error_context(all_lines, line_index)

                return LaTeXError(
                    error_type=error_info["type"],
                    message=error_info["message"],
                    file_path=file_path,
                    line_number=line_number,
                    context=context,
                    raw_error=line,
                )

        # Check for generic error markers
        if re.match(r"^!", line):
            return LaTeXError(error_type="generic_error", message=line[1:].strip(), raw_error=line)

        return None

    def _extract_location_info(self, lines: list[str], start_index: int) -> tuple[str | None, int | None]:
        """Extract file path and line number from log context."""
        file_path = None
        line_number = None

        # Look backward for file information
        for i in range(max(0, start_index - 10), start_index):
            line = lines[i]

            # Look for file path patterns
            file_match = re.search(r"\(([^)]+\.tex)", line)
            if file_match:
                file_path = file_match.group(1)

            # Look for line number patterns
            line_match = re.search(r"l\.(\d+)", line)
            if line_match:
                line_number = int(line_match.group(1))

        return file_path, line_number

    def _extract_error_context(self, lines: list[str], start_index: int, context_lines: int = 3) -> str | None:
        """Extract context around error location."""
        start = max(0, start_index - context_lines)
        end = min(len(lines), start_index + context_lines + 1)

        context = []
        for i in range(start, end):
            marker = ">>> " if i == start_index else "    "
            context.append(f"{marker}{lines[i]}")

        return "\n".join(context) if context else None

    def _get_error_suggestion(self, latex_error: LaTeXError) -> str | None:
        """Get user-friendly suggestion for fixing the error."""
        for _pattern, error_info in self.ERROR_PATTERNS.items():
            if error_info["type"] == latex_error.error_type:
                suggestion = error_info.get("suggestion")

                # Customize suggestion based on specific error content
                if latex_error.error_type == "missing_file" and latex_error.raw_error:
                    file_match = re.search(r"File `([^']+)' not found", latex_error.raw_error)
                    if file_match:
                        missing_file = file_match.group(1)
                        suggestion = (
                            f"The file '{missing_file}' cannot be found. Check the file path and ensure it exists."
                        )

                elif latex_error.error_type == "undefined_citation" and latex_error.raw_error:
                    cite_match = re.search(r"Citation '([^']+)'", latex_error.raw_error)
                    if cite_match:
                        citation_key = cite_match.group(1)
                        suggestion = (
                            f"Citation key '{citation_key}' not found in bibliography. Check 03_REFERENCES.bib file."
                        )

                return suggestion

        return "Check LaTeX syntax and package requirements"
