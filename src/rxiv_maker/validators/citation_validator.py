"""Citation validator for checking citation syntax and bibliography references."""

import os
import re
from typing import Any, Dict

try:
    from ..core.error_codes import ErrorCode, create_validation_error
    from ..processors.yaml_processor import extract_yaml_metadata, get_doi_validation_setting
    from ..utils.file_helpers import find_manuscript_md
    from .base_validator import BaseValidator, ValidationResult
    from .doi_validator import DOIValidator
except ImportError:
    # Fallback for script execution
    from ..core.error_codes import ErrorCode, create_validation_error
    from ..processors.yaml_processor import extract_yaml_metadata, get_doi_validation_setting
    from ..utils.file_helpers import find_manuscript_md
    from .base_validator import (
        BaseValidator,
        ValidationResult,
    )
    from .doi_validator import DOIValidator


class CitationValidator(BaseValidator):
    """Validates citation syntax and checks against bibliography."""

    # Citation patterns from the codebase analysis
    CITATION_PATTERNS = {
        "bracketed_multiple": re.compile(r"\[(@[^]]+)\]"),  # [@citation1;@citation2]
        "single_citation": re.compile(r"@(?!fig:|eq:|table:|tbl:|sfig:|stable:|snote:)([a-zA-Z0-9_-]+)"),  # @key
        "protected_citation": re.compile(r"XXPROTECTEDTABLEXX\d+XXPROTECTEDTABLEXX"),  # Skip protected content
    }

    # Valid citation key pattern
    VALID_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

    def __init__(self, manuscript_path: str, enable_doi_validation: bool | None = None):
        """Initialize citation validator.

        Args:
            manuscript_path: Path to the manuscript directory
            enable_doi_validation: Whether to enable DOI validation. If None, reads from config
        """
        super().__init__(manuscript_path)
        self.bib_keys: set[str] = set()
        self.bib_key_lines: dict[str, int] = {}  # Map from key to line number
        self.citations_found: dict[str, list[int]] = {}

        # Determine DOI validation setting from config if not explicitly provided
        if enable_doi_validation is None:
            try:
                manuscript_file = find_manuscript_md()
                metadata = extract_yaml_metadata(str(manuscript_file))
                self.enable_doi_validation = get_doi_validation_setting(metadata)
            except Exception:
                # Fall back to default if config reading fails
                self.enable_doi_validation = True
        else:
            self.enable_doi_validation = enable_doi_validation

    def validate(self) -> ValidationResult:
        """Validate citations in manuscript files."""
        errors = []
        metadata: Dict[str, Any] = {}

        # Load bibliography keys
        bib_file_path = os.path.join(self.manuscript_path, "03_REFERENCES.bib")
        if os.path.exists(bib_file_path):
            self.bib_keys, self.bib_key_lines = self._parse_bibliography_keys(bib_file_path)
            metadata["bibliography_keys"] = len(self.bib_keys)
        else:
            errors.append(
                create_validation_error(
                    ErrorCode.BIBLIOGRAPHY_ERROR,
                    "Bibliography file 03_REFERENCES.bib not found",
                    suggestion="Create bibliography file to validate citation references",
                )
            )

        # Check main manuscript
        main_file = os.path.join(self.manuscript_path, "01_MAIN.md")
        if os.path.exists(main_file):
            main_errors = self._validate_file_citations(main_file)
            errors.extend(main_errors)

        # Check supplementary information
        supp_file = os.path.join(self.manuscript_path, "02_SUPPLEMENTARY_INFO.md")
        if os.path.exists(supp_file):
            supp_errors = self._validate_file_citations(supp_file)
            errors.extend(supp_errors)

        # Check for unused bibliography entries
        if self.bib_keys:
            unused_entries = self.bib_keys - set(self.citations_found.keys())

            # Special entries that should be excluded from unused warnings
            # These are typically added dynamically by the system
            system_entries = {
                "saraiva_2025_rxivmaker",  # Dynamically added Rxiv-Maker self-citation
            }

            # Filter out system entries from unused warnings
            unused_entries = unused_entries - system_entries

            for unused_key in sorted(unused_entries):
                line_number = self.bib_key_lines.get(unused_key)
                errors.append(
                    create_validation_error(
                        ErrorCode.CITATION_NOT_FOUND,
                        f"Unused bibliography entry: '{unused_key}'",
                        file_path=bib_file_path,
                        line_number=line_number,
                        suggestion=(
                            f"Bibliography entry '{unused_key}' is not cited in the manuscript. "
                            "Consider removing it or adding citations."
                        ),
                    )
                )

        # Add citation statistics to metadata
        metadata.update(
            {
                "total_citations": sum(len(lines) for lines in self.citations_found.values()),
                "unique_citations": len(self.citations_found),
                "unused_entries": len(self.bib_keys - set(self.citations_found.keys()) - {"saraiva_2025_rxivmaker"})
                if self.bib_keys
                else 0,
                "undefined_citations": len(
                    [key for key in self.citations_found if key not in self.bib_keys and self.bib_keys]
                ),
            }
        )

        # Perform DOI validation if enabled
        if self.enable_doi_validation:
            doi_validator = DOIValidator(
                self.manuscript_path,
                enable_online_validation=self.enable_doi_validation,
                ignore_ci_environment=True,  # Allow validation in CI for consistent test behavior
            )
            doi_result = doi_validator.validate()

            # Merge DOI validation results
            errors.extend(doi_result.errors)
            metadata["doi_validation"] = doi_result.metadata

        return ValidationResult("CitationValidator", errors, metadata)

    def _parse_bibliography_keys(self, bib_file_path: str) -> tuple[set[str], dict[str, int]]:
        """Parse bibliography file to extract citation keys and their line numbers."""
        keys: set[str] = set()
        key_lines: dict[str, int] = {}
        content = self._read_file_safely(bib_file_path)

        if not content:
            return keys, key_lines

        # Split content into lines to track line numbers
        lines = content.split("\n")

        # Find all @article{key, @book{key, etc.
        entry_pattern = re.compile(r"@\w+\s*\{\s*([^,\s}]+)", re.IGNORECASE)

        for line_num, line in enumerate(lines, 1):
            match = entry_pattern.search(line)
            if match:
                key = match.group(1).strip()
                if key:
                    keys.add(key)
                    key_lines[key] = line_num

        return keys, key_lines

    def _validate_file_citations(self, file_path: str) -> list:
        """Validate citations in a specific file."""
        errors = []
        content = self._read_file_safely(file_path)

        if not content:
            errors.append(
                create_validation_error(
                    ErrorCode.FILE_READ_ERROR,
                    f"Could not read file: {os.path.basename(file_path)}",
                    file_path=file_path,
                )
            )
            return errors

        lines = content.split("\n")
        in_code_block = False

        for line_num, line in enumerate(lines, 1):
            # Skip protected content (tables, code blocks, etc.)
            if self.CITATION_PATTERNS["protected_citation"].search(line):
                continue

            # Track fenced code blocks
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            # Skip citations inside fenced code blocks
            if in_code_block:
                continue

            line_errors = self._validate_line_citations(line, file_path, line_num)
            errors.extend(line_errors)

        return errors

    def _validate_line_citations(self, line: str, file_path: str, line_num: int) -> list:
        """Validate citations in a single line."""
        errors = []

        # Check bracketed citations: [@key1;@key2]
        for match in self.CITATION_PATTERNS["bracketed_multiple"].finditer(line):
            # Skip citations inside code spans
            if self._is_position_in_code_span(line, match.start()):
                continue

            citation_group = match.group(1)  # @key1;@key2
            citations = [c.strip() for c in citation_group.split(";")]

            for citation in citations:
                if citation.startswith("@"):
                    key = citation[1:]  # Remove @ prefix
                    cite_errors = self._validate_citation_key(key, file_path, line_num, match.start(), line)
                    errors.extend(cite_errors)

        # Check single citations: @key (but not @fig:, @eq:, etc.)
        for match in self.CITATION_PATTERNS["single_citation"].finditer(line):
            # Skip citations inside code spans
            if self._is_position_in_code_span(line, match.start()):
                continue

            key = match.group(1)
            cite_errors = self._validate_citation_key(key, file_path, line_num, match.start(), line)
            errors.extend(cite_errors)

        return errors

    def _is_position_in_code_span(self, line: str, position: int) -> bool:
        """Check if a position in a line is inside a code span (backticks)."""
        # Find all backtick pairs in the line
        backtick_ranges = []
        in_backtick = False
        start_pos = 0

        for i, char in enumerate(line):
            if char == "`":
                if not in_backtick:
                    start_pos = i
                    in_backtick = True
                else:
                    # End of backtick span
                    backtick_ranges.append((start_pos, i))
                    in_backtick = False

        # Check if position is inside any backtick range
        return any(start <= position <= end for start, end in backtick_ranges)

    def _validate_citation_key(self, key: str, file_path: str, line_num: int, column: int, context: str) -> list:
        """Validate a single citation key."""
        errors = []

        # Track citation usage
        if key not in self.citations_found:
            self.citations_found[key] = []
        self.citations_found[key].append(line_num)

        # Check key format
        if not self.VALID_KEY_PATTERN.match(key):
            errors.append(
                create_validation_error(
                    ErrorCode.INVALID_REFERENCE,
                    f"Invalid citation key format: '{key}'",
                    file_path=file_path,
                    line_number=line_num,
                    context=context,
                    suggestion="Citation keys should contain only letters, numbers, underscores, and hyphens",
                )
            )

        # Check if key exists in bibliography (only if we have bib keys loaded)
        elif self.bib_keys and key not in self.bib_keys:
            errors.append(
                create_validation_error(
                    ErrorCode.CITATION_NOT_FOUND,
                    f"Undefined citation: '{key}'",
                    file_path=file_path,
                    line_number=line_num,
                    context=context,
                    suggestion=f"Add citation key '{key}' to 03_REFERENCES.bib or check spelling",
                )
            )

        # Check for common mistakes
        elif self._is_likely_reference_not_citation(key):
            errors.append(
                create_validation_error(
                    ErrorCode.INVALID_REFERENCE,
                    f"Citation key '{key}' looks like it might be a cross-reference",
                    file_path=file_path,
                    line_number=line_num,
                    context=context,
                    suggestion="Use @fig:label for figures, @table:label for tables, @eq:label for equations",
                )
            )

        return errors

    def _is_likely_reference_not_citation(self, key: str) -> bool:
        """Check if citation key looks like it should be a cross-reference."""
        reference_patterns = [
            r"^fig\d+$",  # fig1, fig2
            r"^figure\d+$",  # figure1, figure2
            r"^table\d+$",  # table1, table2
            r"^tbl\d+$",  # tbl1, tbl2
            r"^eq\d+$",  # eq1, eq2
            r"^equation\d+$",  # equation1, equation2
        ]

        return any(re.match(pattern, key, re.IGNORECASE) for pattern in reference_patterns)

    def get_citation_statistics(self) -> dict[str, Any]:
        """Get statistics about citations found."""
        stats: dict[str, Any] = {
            "total_unique_citations": len(self.citations_found),
            "total_citation_instances": sum(len(lines) for lines in self.citations_found.values()),
            "most_cited": None,
            "unused_bib_entries": [],
            "citation_frequency": {},
        }

        if self.citations_found:
            # Find most cited reference
            most_cited_key = max(self.citations_found.keys(), key=lambda k: len(self.citations_found[k]))
            stats["most_cited"] = {
                "key": most_cited_key,
                "count": len(self.citations_found[most_cited_key]),
            }

            # Citation frequency distribution
            freq_dist: dict[int, int] = stats["citation_frequency"]
            for _key, lines in self.citations_found.items():
                count = len(lines)
                if count not in freq_dist:
                    freq_dist[count] = 0
                freq_dist[count] += 1

        # Find unused bibliography entries
        if self.bib_keys:
            stats["unused_bib_entries"] = list(self.bib_keys - set(self.citations_found.keys()))

        return stats
