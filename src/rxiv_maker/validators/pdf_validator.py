#!/usr/bin/env python3
"""PDF post-build validator for verifying final PDF output.

This validator extracts text from the generated PDF and verifies that:
- Citations are properly rendered (no "?" citations)
- Equations are properly rendered (no malformed LaTeX)
- Figure references are properly resolved
- Table references are properly resolved
- Cross-references are working correctly
- Bibliography entries are present
"""

import logging
import os
import re
import sys
from pathlib import Path

# Add the parent directory to the path to allow imports when run as a script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    import pypdf
except ImportError:
    pypdf = None

if __name__ == "__main__":
    from rxiv_maker.validators.base_validator import (
        BaseValidator,
        ValidationError,
        ValidationLevel,
        ValidationResult,
    )
else:
    from .base_validator import (
        BaseValidator,
        ValidationError,
        ValidationLevel,
        ValidationResult,
    )

logger = logging.getLogger(__name__)


class PDFValidator(BaseValidator):
    """Validator for checking final PDF output quality."""

    def __init__(self, manuscript_path: str, pdf_path: str | None = None):
        """Initialize PDF validator.

        Args:
            manuscript_path: Path to manuscript directory
            pdf_path: Path to PDF file (if None, looks for standard output)
        """
        super().__init__(manuscript_path)
        self.pdf_path = pdf_path
        self.pdf_text = ""
        self.pdf_pages = []

        # Patterns for validation
        self.citation_pattern = re.compile(r"\[([^\]]+)\]")
        self.figure_ref_pattern = re.compile(r"Fig(?:ure)?\.?\s*(\d+)", re.IGNORECASE)
        self.table_ref_pattern = re.compile(r"Table\.?\s*(\d+)", re.IGNORECASE)
        self.equation_ref_pattern = re.compile(r"Eq(?:uation)?\.?\s*(\d+)", re.IGNORECASE)
        self.section_ref_pattern = re.compile(r"Section\.?\s*(\d+(?:\.\d+)*)", re.IGNORECASE)

        # Problem patterns
        self.unresolved_citation_pattern = re.compile(r"\[\?\]|\[cite\]")
        self.malformed_equation_pattern = re.compile(r"\\[a-zA-Z]+\{[^}]*$|\\[a-zA-Z]+$|\$[^$]*$")
        self.missing_figure_pattern = re.compile(r"Figure\s*\?\?|\?\?\s*Figure", re.IGNORECASE)

    def _find_pdf_file(self) -> Path | None:
        """Find the PDF file to validate."""
        if self.pdf_path:
            pdf_file = Path(self.pdf_path)
            if pdf_file.exists():
                return pdf_file

        # Look for PDF in standard locations
        manuscript_dir = Path(self.manuscript_path)
        manuscript_name = manuscript_dir.name

        # Check in manuscript directory
        manuscript_pdf = manuscript_dir / f"{manuscript_name}.pdf"
        if manuscript_pdf.exists():
            return manuscript_pdf

        # Check in output directory
        output_dir = Path("output")
        output_pdf = output_dir / f"{manuscript_name}.pdf"
        if output_pdf.exists():
            return output_pdf

        # Check for any PDF in manuscript directory
        pdf_files = list(manuscript_dir.glob("*.pdf"))
        if pdf_files:
            return pdf_files[0]  # Return first PDF found

        return None

    def _extract_pdf_text(self, pdf_path: Path) -> tuple[str, list[str]]:
        """Extract text from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (full_text, pages_text_list)
        """
        if not pypdf:
            raise ImportError("pypdf package is required for PDF validation")

        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)

                pages_text = []
                full_text = ""

                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        pages_text.append(page_text)
                        full_text += page_text + "\n"
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                        pages_text.append("")

                return full_text, pages_text

        except Exception as e:
            logger.error(f"Failed to read PDF file {pdf_path}: {e}")
            return "", []

    def _validate_citations(self) -> list[ValidationError]:
        """Validate citations in PDF text."""
        errors = []

        # Check for unresolved citations
        unresolved_citations = self.unresolved_citation_pattern.findall(self.pdf_text)
        if unresolved_citations:
            errors.append(
                self._create_error(
                    ValidationLevel.ERROR,
                    f"Found {len(unresolved_citations)} unresolved citations in PDF (showing as '?' or '[cite]')",
                    context=f"Unresolved citations found: {', '.join(unresolved_citations[:5])}{'...' if len(unresolved_citations) > 5 else ''}",
                    suggestion="Check bibliography file and ensure all cited works are included",
                    error_code="PDF_UNRESOLVED_CITATIONS",
                )
            )

        # Check for proper citation format
        citations = self.citation_pattern.findall(self.pdf_text)
        citation_count = len(citations)

        if citation_count == 0:
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    "No citations found in PDF text",
                    suggestion="Verify that citations are properly formatted and included",
                    error_code="PDF_NO_CITATIONS",
                )
            )
        else:
            # Check for suspicious citation patterns
            suspicious_citations = [c for c in citations if c.strip() in ["?", "cite", ""]]
            if suspicious_citations:
                errors.append(
                    self._create_error(
                        ValidationLevel.WARNING,
                        f"Found {len(suspicious_citations)} suspicious citations in PDF",
                        context=f"Suspicious citations: {', '.join(suspicious_citations[:5])}",
                        suggestion="Check that all citations are properly resolved",
                        error_code="PDF_SUSPICIOUS_CITATIONS",
                    )
                )

        return errors

    def _validate_equations(self) -> list[ValidationError]:
        """Validate equations in PDF text."""
        errors = []

        # Check for malformed LaTeX equations
        malformed_equations = self.malformed_equation_pattern.findall(self.pdf_text)
        if malformed_equations:
            # Truncate context to avoid overwhelming output
            sample_equations = [eq[:50] + "..." if len(eq) > 50 else eq for eq in malformed_equations[:2]]
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    f"Found {len(malformed_equations)} potentially malformed equations in PDF",
                    context=f"Sample equations: {', '.join(sample_equations)}",
                    suggestion="Note: PyPDF text extraction may cause false positives for equations. Check actual PDF visually if needed.",
                    error_code="PDF_MALFORMED_EQUATIONS",
                )
            )

        # Check for equation references
        equation_refs = self.equation_ref_pattern.findall(self.pdf_text)
        if equation_refs:
            # Check for unresolved equation references
            unresolved_eq_refs = [ref for ref in equation_refs if "?" in ref]
            if unresolved_eq_refs:
                errors.append(
                    self._create_error(
                        ValidationLevel.ERROR,
                        f"Found {len(unresolved_eq_refs)} unresolved equation references",
                        context=f"Unresolved equation references: {', '.join(unresolved_eq_refs)}",
                        suggestion="Check equation labels and references",
                        error_code="PDF_UNRESOLVED_EQUATION_REFS",
                    )
                )

        return errors

    def _validate_figures(self) -> list[ValidationError]:
        """Validate figure references in PDF text."""
        errors = []

        # Check for missing figure references
        missing_figures = self.missing_figure_pattern.findall(self.pdf_text)
        if missing_figures:
            errors.append(
                self._create_error(
                    ValidationLevel.ERROR,
                    f"Found {len(missing_figures)} missing figure references in PDF",
                    context="Figure references showing as '??' or similar",
                    suggestion="Check figure labels and ensure all referenced figures exist",
                    error_code="PDF_MISSING_FIGURE_REFS",
                )
            )

        # Check for figure references
        figure_refs = self.figure_ref_pattern.findall(self.pdf_text)
        if figure_refs:
            # Check for unresolved figure references (containing '?')
            unresolved_fig_refs = [ref for ref in figure_refs if "?" in ref]
            if unresolved_fig_refs:
                errors.append(
                    self._create_error(
                        ValidationLevel.ERROR,
                        f"Found {len(unresolved_fig_refs)} unresolved figure references",
                        context=f"Unresolved figure references: {', '.join(unresolved_fig_refs)}",
                        suggestion="Check figure labels and references",
                        error_code="PDF_UNRESOLVED_FIGURE_REFS",
                    )
                )

        return errors

    def _validate_tables(self) -> list[ValidationError]:
        """Validate table references in PDF text."""
        errors = []

        # Check for table references
        table_refs = self.table_ref_pattern.findall(self.pdf_text)
        if table_refs:
            # Check for unresolved table references
            unresolved_table_refs = [ref for ref in table_refs if "?" in ref]
            if unresolved_table_refs:
                errors.append(
                    self._create_error(
                        ValidationLevel.ERROR,
                        f"Found {len(unresolved_table_refs)} unresolved table references",
                        context=f"Unresolved table references: {', '.join(unresolved_table_refs)}",
                        suggestion="Check table labels and references",
                        error_code="PDF_UNRESOLVED_TABLE_REFS",
                    )
                )

        return errors

    def _validate_sections(self) -> list[ValidationError]:
        """Validate section references in PDF text."""
        errors = []

        # Check for section references
        section_refs = self.section_ref_pattern.findall(self.pdf_text)
        if section_refs:
            # Check for unresolved section references
            unresolved_section_refs = [ref for ref in section_refs if "?" in ref]
            if unresolved_section_refs:
                errors.append(
                    self._create_error(
                        ValidationLevel.ERROR,
                        f"Found {len(unresolved_section_refs)} unresolved section references",
                        context=f"Unresolved section references: {', '.join(unresolved_section_refs)}",
                        suggestion="Check section labels and references",
                        error_code="PDF_UNRESOLVED_SECTION_REFS",
                    )
                )

        return errors

    def _validate_bibliography(self) -> list[ValidationError]:
        """Validate bibliography presence in PDF text."""
        errors = []

        # Check for common bibliography section headers
        bibliography_headers = [
            "references",
            "bibliography",
            "works cited",
            "literature cited",
        ]

        bibliography_found = False
        for header in bibliography_headers:
            if header in self.pdf_text.lower():
                bibliography_found = True
                break

        if not bibliography_found:
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    "No bibliography section found in PDF",
                    suggestion="Verify that bibliography is properly included and formatted",
                    error_code="PDF_NO_BIBLIOGRAPHY",
                )
            )

        return errors

    def _validate_page_structure(self) -> list[ValidationError]:
        """Validate basic page structure."""
        errors = []

        if not self.pdf_pages:
            errors.append(
                self._create_error(
                    ValidationLevel.ERROR,
                    "No pages could be extracted from PDF",
                    suggestion="Check PDF file integrity and ensure it's not corrupted",
                    error_code="PDF_NO_PAGES",
                )
            )
            return errors

        # Check for extremely short pages (possible extraction issues)
        short_pages = [i for i, page in enumerate(self.pdf_pages) if len(page.strip()) < 100]
        if short_pages:
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    f"Found {len(short_pages)} pages with very little text",
                    context=f"Pages with little text: {', '.join(str(p + 1) for p in short_pages[:5])}",
                    suggestion="Check if these pages should contain more text or if text extraction failed",
                    error_code="PDF_SHORT_PAGES",
                )
            )

        return errors

    def _get_validation_statistics(self) -> dict[str, any]:
        """Get validation statistics from PDF text."""
        stats = {
            "total_pages": len(self.pdf_pages),
            "total_characters": len(self.pdf_text),
            "total_words": len(self.pdf_text.split()),
            "citations_found": len(self.citation_pattern.findall(self.pdf_text)),
            "figure_references": len(self.figure_ref_pattern.findall(self.pdf_text)),
            "table_references": len(self.table_ref_pattern.findall(self.pdf_text)),
            "equation_references": len(self.equation_ref_pattern.findall(self.pdf_text)),
            "section_references": len(self.section_ref_pattern.findall(self.pdf_text)),
        }

        # Add page statistics
        if self.pdf_pages:
            page_lengths = [len(page.strip()) for page in self.pdf_pages]
            stats.update(
                {
                    "avg_page_length": sum(page_lengths) / len(page_lengths),
                    "min_page_length": min(page_lengths),
                    "max_page_length": max(page_lengths),
                }
            )

        return stats

    def validate(self) -> ValidationResult:
        """Validate PDF output quality.

        Returns:
            ValidationResult with PDF validation issues
        """
        errors = []

        # Find PDF file
        pdf_file = self._find_pdf_file()
        if not pdf_file:
            errors.append(
                self._create_error(
                    ValidationLevel.ERROR,
                    "No PDF file found for validation",
                    suggestion="Ensure PDF build completed successfully",
                    error_code="PDF_FILE_NOT_FOUND",
                )
            )
            return ValidationResult(self.name, errors, {})

        # Extract text from PDF
        try:
            self.pdf_text, self.pdf_pages = self._extract_pdf_text(pdf_file)
        except Exception as e:
            errors.append(
                self._create_error(
                    ValidationLevel.ERROR,
                    f"Failed to extract text from PDF: {str(e)}",
                    file_path=str(pdf_file),
                    suggestion="Check PDF file integrity and ensure pypdf is installed",
                    error_code="PDF_EXTRACTION_FAILED",
                )
            )
            return ValidationResult(self.name, errors, {})

        if not self.pdf_text.strip():
            errors.append(
                self._create_error(
                    ValidationLevel.ERROR,
                    "No text could be extracted from PDF",
                    file_path=str(pdf_file),
                    suggestion="Check if PDF contains text or if text extraction failed",
                    error_code="PDF_NO_TEXT",
                )
            )
            return ValidationResult(self.name, errors, {})

        # Run all validation checks
        errors.extend(self._validate_page_structure())
        errors.extend(self._validate_citations())
        errors.extend(self._validate_equations())
        errors.extend(self._validate_figures())
        errors.extend(self._validate_tables())
        errors.extend(self._validate_sections())
        errors.extend(self._validate_bibliography())

        # Get validation statistics
        metadata = self._get_validation_statistics()
        metadata["pdf_file"] = str(pdf_file)

        # Note: Removed success message to simplify output - statistics shown separately

        return ValidationResult(self.name, errors, metadata)


def validate_pdf(manuscript_path: str, pdf_path: str | None = None) -> ValidationResult:
    """Convenience function to validate a PDF file.

    Args:
        manuscript_path: Path to manuscript directory
        pdf_path: Path to PDF file (optional)

    Returns:
        ValidationResult with PDF validation issues
    """
    validator = PDFValidator(manuscript_path, pdf_path)
    return validator.validate()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate PDF output quality")
    parser.add_argument("manuscript_path", help="Path to manuscript directory")
    parser.add_argument("--pdf-path", help="Path to PDF file (optional)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # Run validation
    result = validate_pdf(args.manuscript_path, args.pdf_path)

    # Print results - simplified format
    if result.errors:
        print(f"\nPDF Validation Results for {args.manuscript_path}")
        print("=" * 60)
        for error in result.errors:
            level_str = error.level.name
            print(f"[{level_str}] {error.message}")
            if error.context:
                print(f"  Context: {error.context}")
            if error.suggestion:
                print(f"  Suggestion: {error.suggestion}")
        print()

    # Show key statistics only
    if result.metadata:
        total_pages = result.metadata.get("total_pages", "unknown")
        total_words = result.metadata.get("total_words", "unknown")
        citations_found = result.metadata.get("citations_found", 0)
        figure_references = result.metadata.get("figure_references", 0)

        print(
            f"📄 {total_pages} pages, {total_words} words, {citations_found} citations, {figure_references} figure references"
        )
        if result.errors:
            print("💡 Check the generated PDF visually to confirm all content appears correctly")

    print()

    # Exit with appropriate code
    has_errors = any(e.level == ValidationLevel.ERROR for e in result.errors)
    exit(1 if has_errors else 0)
