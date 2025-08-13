"""Reference validator for checking cross-references to figures and tables."""

import os
import re
from typing import Any

from .base_validator import BaseValidator, ValidationLevel, ValidationResult


class ReferenceValidator(BaseValidator):
    """Validates cross-references to figures, tables, equations, and notes."""

    # Reference patterns based on codebase analysis
    REFERENCE_PATTERNS = {
        "figure_ref": re.compile(r"@fig:([a-zA-Z0-9_-]+)"),
        "supplementary_figure_ref": re.compile(r"@sfig:([a-zA-Z0-9_-]+)"),
        "table_ref": re.compile(r"@table:([a-zA-Z0-9_-]+)"),
        "supplementary_table_ref": re.compile(r"@stable:([a-zA-Z0-9_-]+)"),
        "equation_ref": re.compile(r"@eq:([a-zA-Z0-9_-]+)"),
        "supplementary_note_ref": re.compile(r"@snote:([a-zA-Z0-9_-]+)"),
    }

    # Label definition patterns
    LABEL_PATTERNS = {
        "figure_label": re.compile(r"\{#fig:([a-zA-Z0-9_:-]+)([^}]*)\}"),
        "supplementary_figure_label": re.compile(r"\{#sfig:([a-zA-Z0-9_:-]+)([^}]*)\}"),
        "table_label": re.compile(r"\{#table:([a-zA-Z0-9_:-]+)([^}]*)\}"),
        "supplementary_table_label": re.compile(r"\{#stable:([a-zA-Z0-9_:-]+)([^}]*)\}"),
        "equation_label": re.compile(r"\$\$.*?\$\$\s*\{[^}]*#eq:([a-zA-Z0-9_:-]+)[^}]*\}"),
        "supplementary_note_label": re.compile(r"\{#snote:([a-zA-Z0-9_:-]+)\}"),
    }

    def __init__(self, manuscript_path: str):
        """Initialize reference validator.

        Args:
            manuscript_path: Path to the manuscript directory
        """
        super().__init__(manuscript_path)
        self.defined_labels: dict[str, dict[str, Any]] = {
            "fig": {},
            "sfig": {},
            "table": {},
            "stable": {},
            "eq": {},
            "snote": {},
        }
        self.referenced_labels: dict[str, list[dict[str, Any]]] = {
            "fig": [],
            "sfig": [],
            "table": [],
            "stable": [],
            "eq": [],
            "snote": [],
        }

    def validate(self) -> ValidationResult:
        """Validate cross-references in manuscript files."""
        errors = []
        metadata = {}

        # Process all manuscript files
        files_to_check = [
            ("01_MAIN.md", "main"),
            ("02_SUPPLEMENTARY_INFO.md", "supplementary"),
        ]

        for filename, file_type in files_to_check:
            file_path = os.path.join(self.manuscript_path, filename)
            if os.path.exists(file_path):
                file_errors = self._validate_file_references(file_path, file_type)
                errors.extend(file_errors)
            elif filename == "01_MAIN.md":
                errors.append(
                    self._create_error(
                        ValidationLevel.ERROR,
                        "Main manuscript file 01_MAIN.md not found",
                        suggestion="Ensure the main manuscript file exists",
                    )
                )

        # Check for undefined references
        undefined_errors = self._check_undefined_references()
        errors.extend(undefined_errors)

        # Check for unused labels
        unused_warnings = self._check_unused_labels()
        errors.extend(unused_warnings)

        # Add statistics to metadata
        metadata.update(self._generate_reference_statistics())

        return ValidationResult("ReferenceValidator", errors, metadata)

    def _validate_file_references(self, file_path: str, file_type: str) -> list:
        """Validate references in a specific file."""
        errors = []
        content = self._read_file_safely(file_path)

        if not content:
            errors.append(
                self._create_error(
                    ValidationLevel.ERROR,
                    f"Could not read file: {os.path.basename(file_path)}",
                    file_path=file_path,
                )
            )
            return errors

        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Find label definitions
            label_errors = self._extract_label_definitions(line, file_path, line_num, file_type)
            errors.extend(label_errors)

            # Find reference uses
            ref_errors = self._extract_reference_uses(line, file_path, line_num)
            errors.extend(ref_errors)

        return errors

    def _extract_label_definitions(self, line: str, file_path: str, line_num: int, file_type: str) -> list:
        """Extract label definitions from a line."""
        errors = []

        for label_type, pattern in self.LABEL_PATTERNS.items():
            for match in pattern.finditer(line):
                label_id = match.group(1)

                # Determine the reference type
                ref_type = self._get_reference_type_from_label(label_type)

                # Check for duplicate labels
                if label_id in self.defined_labels[ref_type]:
                    existing = self.defined_labels[ref_type][label_id]
                    errors.append(
                        self._create_error(
                            ValidationLevel.ERROR,
                            f"Duplicate {ref_type} label: '{label_id}'",
                            file_path=file_path,
                            line_number=line_num,
                            context=line,
                            suggestion=(
                                f"Label '{label_id}' is already defined in "
                                f"{existing['file']} at line {existing['line']}"
                            ),
                            error_code="duplicate_label",
                        )
                    )
                else:
                    # Store label definition
                    self.defined_labels[ref_type][label_id] = {
                        "file": os.path.basename(file_path),
                        "line": line_num,
                        "file_type": file_type,
                        "context": line.strip(),
                    }

                # Check label format
                if not self._is_valid_label_format(label_id):
                    errors.append(
                        self._create_error(
                            ValidationLevel.WARNING,
                            f"Non-standard label format: '{label_id}'",
                            file_path=file_path,
                            line_number=line_num,
                            context=line,
                            suggestion=("Use lowercase letters, numbers, underscores, and hyphens for consistency"),
                            error_code="non_standard_label",
                        )
                    )

        return errors

    def _extract_reference_uses(self, line: str, file_path: str, line_num: int) -> list:
        """Extract reference uses from a line."""
        errors: list = []

        # Skip references inside backticks (code/syntax examples)
        if self._is_syntax_example_line(line):
            return errors

        for ref_type, pattern in self.REFERENCE_PATTERNS.items():
            for match in pattern.finditer(line):
                # Check if this match is inside backticks
                if self._is_inside_backticks(line, match.start()):
                    continue

                label_id = match.group(1)

                # Determine the reference type
                ref_key = self._get_reference_type_from_pattern(ref_type)

                # Store reference use
                self.referenced_labels[ref_key].append(
                    {
                        "label": label_id,
                        "file": os.path.basename(file_path),
                        "line": line_num,
                        "context": line.strip(),
                        "column": match.start(),
                    }
                )

                # Check reference format
                if not self._is_valid_label_format(label_id):
                    errors.append(
                        self._create_error(
                            ValidationLevel.WARNING,
                            f"Non-standard reference format: '{label_id}'",
                            file_path=file_path,
                            line_number=line_num,
                            column=match.start(),
                            context=line,
                            suggestion=("Use lowercase letters, numbers, underscores, and hyphens for consistency"),
                            error_code="non_standard_reference",
                        )
                    )

        return errors

    def _check_undefined_references(self) -> list:
        """Check for references to undefined labels."""
        errors = []

        for ref_type, references in self.referenced_labels.items():
            for ref in references:
                label_id = ref["label"]
                if label_id not in self.defined_labels[ref_type]:
                    # Check if it might be in the wrong category
                    suggestion = self._suggest_correct_reference_type(label_id, ref_type)

                    errors.append(
                        self._create_error(
                            ValidationLevel.ERROR,
                            f"Undefined {ref_type} reference: '{label_id}'",
                            file_path=ref["file"],
                            line_number=ref["line"],
                            column=ref.get("column"),
                            context=ref["context"],
                            suggestion=suggestion,
                            error_code="undefined_reference",
                        )
                    )

        return errors

    def _check_unused_labels(self) -> list:
        """Check for defined labels that are never referenced."""
        warnings = []

        for ref_type, labels in self.defined_labels.items():
            referenced_in_type = {ref["label"] for ref in self.referenced_labels[ref_type]}

            for label_id, label_info in labels.items():
                if label_id not in referenced_in_type:
                    warnings.append(
                        self._create_error(
                            ValidationLevel.INFO,
                            f"Unused {ref_type} label: '{label_id}'",
                            file_path=label_info["file"],
                            line_number=label_info["line"],
                            context=label_info["context"],
                            suggestion=("Consider removing unused labels or add references to them"),
                            error_code="unused_label",
                        )
                    )

        return warnings

    def _get_reference_type_from_label(self, label_type: str) -> str:
        """Map label pattern name to reference type."""
        mapping = {
            "figure_label": "fig",
            "supplementary_figure_label": "sfig",
            "table_label": "table",
            "supplementary_table_label": "stable",
            "equation_label": "eq",
            "supplementary_note_label": "snote",
        }
        return mapping.get(label_type, "unknown")

    def _get_reference_type_from_pattern(self, pattern_name: str) -> str:
        """Map reference pattern name to reference type."""
        mapping = {
            "figure_ref": "fig",
            "supplementary_figure_ref": "sfig",
            "table_ref": "table",
            "supplementary_table_ref": "stable",
            "equation_ref": "eq",
            "supplementary_note_ref": "snote",
        }
        return mapping.get(pattern_name, "unknown")

    def _is_valid_label_format(self, label_id: str) -> bool:
        """Check if label follows recommended format."""
        # Allow letters, numbers, underscores, hyphens, and colons
        return re.match(r"^[a-zA-Z0-9_:-]+$", label_id) is not None

    def _suggest_correct_reference_type(self, label_id: str, current_type: str) -> str:
        """Suggest correct reference type if label exists in another category."""
        for ref_type, labels in self.defined_labels.items():
            if ref_type != current_type and label_id in labels:
                type_names = {
                    "fig": "figure (@fig:)",
                    "sfig": "supplementary figure (@sfig:)",
                    "table": "table (@table:)",
                    "stable": "supplementary table (@stable:)",
                    "eq": "equation (@eq:)",
                    "snote": "supplementary note (@snote:)",
                }
                return (
                    f"Label '{label_id}' exists as a "
                    f"{type_names.get(ref_type, ref_type)}. "
                    f"Use @{ref_type}:{label_id} instead."
                )

        return f"Ensure label '{label_id}' is defined with the appropriate syntax."

    def _is_syntax_example_line(self, line: str) -> bool:
        """Check if the line is primarily a syntax example that should be ignored."""
        # Skip table rows that contain syntax examples
        if "|" in line and ("`@" in line or "`[" in line or "`#" in line):
            return True
        # Skip lines that are entirely code blocks or contain only syntax examples
        stripped = line.strip()
        return bool(stripped.startswith("```") or stripped.startswith("    "))

    def _is_inside_backticks(self, line: str, position: int) -> bool:
        """Check if a position in the line is inside backticks."""
        # Find all backtick pairs in the line
        backtick_positions = []
        in_code = False
        i = 0
        while i < len(line):
            if line[i] == "`":
                # Handle double backticks
                if i + 1 < len(line) and line[i + 1] == "`":
                    backtick_positions.append((i, i + 1, not in_code))
                    in_code = not in_code
                    i += 2
                else:
                    backtick_positions.append((i, i, not in_code))
                    in_code = not in_code
                    i += 1
            else:
                i += 1

        # Check if position falls within any code span
        in_code_span = False
        for start, end, is_opening in backtick_positions:
            if is_opening and start <= position:
                in_code_span = True
            elif not is_opening and end < position and in_code_span:
                in_code_span = False

        return in_code_span

    def _generate_reference_statistics(self) -> dict[str, Any]:
        """Generate statistics about references and labels."""
        stats: dict[str, Any] = {
            "total_labels_defined": sum(len(labels) for labels in self.defined_labels.values()),
            "total_references_used": sum(len(refs) for refs in self.referenced_labels.values()),
            "labels_by_type": {k: len(v) for k, v in self.defined_labels.items()},
            "references_by_type": {k: len(v) for k, v in self.referenced_labels.items()},
            "unused_labels": {},
            "undefined_references": {},
        }

        # Count unused labels by type
        unused_labels: dict[str, int] = stats["unused_labels"]
        for ref_type, labels in self.defined_labels.items():
            referenced_in_type = {ref["label"] for ref in self.referenced_labels[ref_type]}
            unused = set(labels.keys()) - referenced_in_type
            unused_labels[ref_type] = len(unused)

        # Count undefined references by type
        undefined_refs: dict[str, int] = stats["undefined_references"]
        for ref_type, references in self.referenced_labels.items():
            undefined = {ref["label"] for ref in references} - set(self.defined_labels[ref_type].keys())
            undefined_refs[ref_type] = len(undefined)

        return stats
