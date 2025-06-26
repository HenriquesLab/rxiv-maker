"""Citation validator for checking citation syntax and bibliography references."""

import os
import re
from typing import Any

from .base_validator import BaseValidator, ValidationLevel, ValidationResult


class CitationValidator(BaseValidator):
    """Validates citation syntax and checks against bibliography."""

    # Citation patterns from the codebase analysis
    CITATION_PATTERNS = {
        "bracketed_multiple": re.compile(r"\[(@[^]]+)\]"),  # [@citation1;@citation2]
        "single_citation": re.compile(
            r"@(?!fig:|eq:|tbl:|sfig:|stable:|snote:)([a-zA-Z0-9_-]+)"
        ),  # @key
        "protected_citation": re.compile(
            r"XXPROTECTEDTABLEXX\d+XXPROTECTEDTABLEXX"
        ),  # Skip protected content
    }

    # Valid citation key pattern
    VALID_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

    def __init__(self, manuscript_path: str):
        """Initialize citation validator.

        Args:
            manuscript_path: Path to the manuscript directory
        """
        super().__init__(manuscript_path)
        self.bib_keys: set[str] = set()
        self.citations_found: dict[str, list[int]] = {}

    def validate(self) -> ValidationResult:
        """Validate citations in manuscript files."""
        errors = []
        metadata = {}

        # Load bibliography keys
        bib_file_path = os.path.join(self.manuscript_path, "03_REFERENCES.bib")
        if os.path.exists(bib_file_path):
            self.bib_keys = self._parse_bibliography_keys(bib_file_path)
            metadata["bibliography_keys"] = len(self.bib_keys)
        else:
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    "Bibliography file 03_REFERENCES.bib not found",
                    suggestion=(
                        "Create bibliography file to validate citation references"
                    ),
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

        # Add citation statistics to metadata
        metadata.update(
            {
                "total_citations": sum(
                    len(lines) for lines in self.citations_found.values()
                ),
                "unique_citations": len(self.citations_found),
                "undefined_citations": len(
                    [
                        key
                        for key in self.citations_found
                        if key not in self.bib_keys and self.bib_keys
                    ]
                ),
            }
        )

        return ValidationResult("CitationValidator", errors, metadata)

    def _parse_bibliography_keys(self, bib_file_path: str) -> set[str]:
        """Parse bibliography file to extract citation keys."""
        keys: set[str] = set()
        content = self._read_file_safely(bib_file_path)

        if not content:
            return keys

        # Find all @article{key, @book{key, etc.
        entry_pattern = re.compile(r"@\w+\s*\{\s*([^,\s}]+)", re.IGNORECASE)
        for match in entry_pattern.finditer(content):
            key = match.group(1).strip()
            if key:
                keys.add(key)

        return keys

    def _validate_file_citations(self, file_path: str) -> list:
        """Validate citations in a specific file."""
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
            # Skip protected content (tables, code blocks, etc.)
            if self.CITATION_PATTERNS["protected_citation"].search(line):
                continue

            line_errors = self._validate_line_citations(line, file_path, line_num)
            errors.extend(line_errors)

        return errors

    def _validate_line_citations(
        self, line: str, file_path: str, line_num: int
    ) -> list:
        """Validate citations in a single line."""
        errors = []

        # Check bracketed citations: [@key1;@key2]
        for match in self.CITATION_PATTERNS["bracketed_multiple"].finditer(line):
            citation_group = match.group(1)  # @key1;@key2
            citations = [c.strip() for c in citation_group.split(";")]

            for citation in citations:
                if citation.startswith("@"):
                    key = citation[1:]  # Remove @ prefix
                    cite_errors = self._validate_citation_key(
                        key, file_path, line_num, match.start(), line
                    )
                    errors.extend(cite_errors)

        # Check single citations: @key (but not @fig:, @eq:, etc.)
        for match in self.CITATION_PATTERNS["single_citation"].finditer(line):
            key = match.group(1)
            cite_errors = self._validate_citation_key(
                key, file_path, line_num, match.start(), line
            )
            errors.extend(cite_errors)

        return errors

    def _validate_citation_key(
        self, key: str, file_path: str, line_num: int, column: int, context: str
    ) -> list:
        """Validate a single citation key."""
        errors = []

        # Track citation usage
        if key not in self.citations_found:
            self.citations_found[key] = []
        self.citations_found[key].append(line_num)

        # Check key format
        if not self.VALID_KEY_PATTERN.match(key):
            errors.append(
                self._create_error(
                    ValidationLevel.ERROR,
                    f"Invalid citation key format: '{key}'",
                    file_path=file_path,
                    line_number=line_num,
                    column=column,
                    context=context,
                    suggestion=(
                        "Citation keys should contain only letters, numbers, "
                        "underscores, and hyphens"
                    ),
                    error_code="invalid_citation_key",
                )
            )

        # Check if key exists in bibliography (only if we have bib keys loaded)
        elif self.bib_keys and key not in self.bib_keys:
            errors.append(
                self._create_error(
                    ValidationLevel.ERROR,
                    f"Undefined citation: '{key}'",
                    file_path=file_path,
                    line_number=line_num,
                    column=column,
                    context=context,
                    suggestion=(
                        f"Add citation key '{key}' to 03_REFERENCES.bib "
                        "or check spelling"
                    ),
                    error_code="undefined_citation",
                )
            )

        # Check for common mistakes
        elif self._is_likely_reference_not_citation(key):
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    f"Citation key '{key}' looks like it might be a cross-reference",
                    file_path=file_path,
                    line_number=line_num,
                    column=column,
                    context=context,
                    suggestion=(
                        "Use @fig:label for figures, @tbl:label for tables, "
                        "@eq:label for equations"
                    ),
                    error_code="possible_reference_error",
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

        return any(
            re.match(pattern, key, re.IGNORECASE) for pattern in reference_patterns
        )

    def get_citation_statistics(self) -> dict[str, Any]:
        """Get statistics about citations found."""
        stats: dict[str, Any] = {
            "total_unique_citations": len(self.citations_found),
            "total_citation_instances": sum(
                len(lines) for lines in self.citations_found.values()
            ),
            "most_cited": None,
            "unused_bib_entries": [],
            "citation_frequency": {},
        }

        if self.citations_found:
            # Find most cited reference
            most_cited_key = max(
                self.citations_found.keys(), key=lambda k: len(self.citations_found[k])
            )
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
            stats["unused_bib_entries"] = list(
                self.bib_keys - set(self.citations_found.keys())
            )

        return stats
