"""Command-line tool for PDF validation.

This script validates PDF output quality by extracting text and checking
for common issues like unresolved citations, malformed equations, and
missing references.
"""

import os
import sys

# Add the parent directory to the path to allow imports when run as a script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rxiv_maker.utils.unicode_safe import (
    get_safe_icon,
    print_error,
    print_info,
    print_success,
    print_warning,
    safe_print,
)
from rxiv_maker.validators.pdf_validator import PDFValidator, ValidationLevel


def validate_pdf_output(
    manuscript_path: str,
    pdf_path: str | None = None,
    verbose: bool = False,
    detailed: bool = False,
) -> int:
    """Validate PDF output quality.

    Args:
        manuscript_path: Path to manuscript directory
        pdf_path: Path to PDF file (optional)
        verbose: Enable verbose output
        detailed: Enable detailed output with statistics

    Returns:
        0 if successful, 1 if errors found
    """
    try:
        # Create validator
        validator = PDFValidator(manuscript_path, pdf_path)

        # Run validation
        result = validator.validate()

        # Display results
        if detailed:
            print(f"\nPDF Validation Results for {manuscript_path}")
            print("=" * 60)

        # Count issues by level
        error_count = sum(1 for e in result.errors if e.level == ValidationLevel.ERROR)
        warning_count = sum(1 for e in result.errors if e.level == ValidationLevel.WARNING)
        success_count = sum(1 for e in result.errors if e.level == ValidationLevel.SUCCESS)

        # Print errors and warnings
        if result.errors:
            for error in result.errors:
                if error.level == ValidationLevel.ERROR:
                    print_error(f"ERROR: {error.message}")
                elif error.level == ValidationLevel.WARNING:
                    print_warning(f"WARNING: {error.message}")
                elif error.level == ValidationLevel.SUCCESS:
                    print_success(f"SUCCESS: {error.message}")
                elif error.level == ValidationLevel.INFO:
                    print_info(f"INFO: {error.message}")

                if verbose:
                    if error.context:
                        print(f"   Context: {error.context}")
                    if error.suggestion:
                        print(f"   Suggestion: {error.suggestion}")
                    if error.file_path:
                        print(f"   File: {error.file_path}")
                    if error.line_number:
                        print(f"   Line: {error.line_number}")
                    print()

        # Print statistics if detailed mode
        if detailed and result.metadata:
            stats_icon = get_safe_icon("📊", "[STATS]")
            safe_print(f"\n{stats_icon} PDF Statistics:")
            print("-" * 30)
            for key, value in result.metadata.items():
                if key == "pdf_file":
                    pdf_icon = get_safe_icon("📄", "[PDF]")
                    safe_print(f"{pdf_icon} PDF File: {value}")
                elif key == "total_pages":
                    pages_icon = get_safe_icon("📑", "[PAGES]")
                    safe_print(f"{pages_icon} Total Pages: {value}")
                elif key == "total_words":
                    words_icon = get_safe_icon("📝", "[WORDS]")
                    safe_print(f"{words_icon} Total Words: {value}")
                elif key == "citations_found":
                    citations_icon = get_safe_icon("📚", "[CITATIONS]")
                    safe_print(f"{citations_icon} Citations Found: {value}")
                elif key == "figure_references":
                    figures_icon = get_safe_icon("🖼️", "[FIGURES]")
                    safe_print(f"{figures_icon} Figure References: {value}")
                elif key == "table_references":
                    tables_icon = get_safe_icon("📊", "[TABLES]")
                    safe_print(f"{tables_icon} Table References: {value}")
                elif key == "equation_references":
                    equations_icon = get_safe_icon("🔢", "[EQUATIONS]")
                    safe_print(f"{equations_icon} Equation References: {value}")
                elif key == "section_references":
                    sections_icon = get_safe_icon("📖", "[SECTIONS]")
                    safe_print(f"{sections_icon} Section References: {value}")
                elif key.startswith("avg_") or key.startswith("min_") or key.startswith("max_"):
                    measure_icon = get_safe_icon("📏", "[MEASURE]")
                    safe_print(f"{measure_icon} {key.replace('_', ' ').title()}: {value:.0f}")

        # Summary
        if detailed:
            summary_icon = get_safe_icon("📋", "[SUMMARY]")
            safe_print(f"\n{summary_icon} Summary:")
            print(f"   Errors: {error_count}")
            print(f"   Warnings: {warning_count}")
            print(f"   Success: {success_count}")

        # Exit with appropriate code
        return 1 if error_count > 0 else 0

    except Exception as e:
        print_error(f"PDF validation failed: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        return 1
