#!/usr/bin/env python3
"""Unified validation command for rxiv-maker manuscripts.

This command provides a comprehensive validation system that checks:
- Manuscript structure and required files
- Citation syntax and bibliography consistency
- Cross-reference validity (figures, tables, equations)
- Figure file existence and attributes
- Mathematical expression syntax
- Special Markdown syntax elements
- LaTeX compilation errors (if available)

The command produces user-friendly output with clear error messages,
suggestions for fixes, and optional detailed statistics.
"""

import argparse
import os
import sys
from typing import Any

# Add src/py to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from validators import (
        CitationValidator,
        FigureValidator,
        LaTeXErrorParser,
        MathValidator,
        ReferenceValidator,
        SyntaxValidator,
        ValidationLevel,
    )

    VALIDATORS_AVAILABLE = True
except ImportError:
    VALIDATORS_AVAILABLE = False


class UnifiedValidator:
    """Unified validation system for rxiv-maker manuscripts."""

    def __init__(
        self,
        manuscript_path: str,
        verbose: bool = False,
        include_info: bool = False,
        check_latex: bool = True,
    ):
        """Initialize unified validator.

        Args:
            manuscript_path: Path to manuscript directory
            verbose: Show detailed output
            include_info: Include informational messages
            check_latex: Parse LaTeX compilation errors
        """
        self.manuscript_path = manuscript_path
        self.verbose = verbose
        self.include_info = include_info
        self.check_latex = check_latex

        self.all_errors: list[Any] = []
        self.validation_results: dict[str, Any] = {}

    def validate_all(self) -> bool:
        """Run all available validators."""
        if not VALIDATORS_AVAILABLE:
            print("❌ Enhanced validators not available")
            print("   Install validation dependencies to use this command")
            return False

        # Check if manuscript directory exists
        if not os.path.exists(self.manuscript_path):
            print(f"❌ Manuscript directory not found: {self.manuscript_path}")
            return False

        print(f"🔍 Validating manuscript: {self.manuscript_path}")
        print()

        validators = [
            ("Citations", CitationValidator),
            ("Cross-references", ReferenceValidator),
            ("Figures", FigureValidator),
            ("Mathematics", MathValidator),
            ("Syntax", SyntaxValidator),
        ]

        if self.check_latex:
            validators.append(("LaTeX Errors", LaTeXErrorParser))

        all_passed = True

        for validator_name, validator_class in validators:
            if self.verbose:
                print(f"🔄 Running {validator_name} validation...")

            try:
                validator = validator_class(self.manuscript_path)
                result = validator.validate()
                self.validation_results[validator_name] = result

                # Process results
                errors = self._filter_errors(result.errors)
                self.all_errors.extend(errors)

                if result.has_errors:
                    all_passed = False
                    status = "❌ FAILED"
                elif result.has_warnings:
                    status = "⚠️  WARNINGS"
                else:
                    status = "✅ PASSED"

                if self.verbose:
                    count_msg = ""
                    if result.error_count > 0:
                        count_msg += f" ({result.error_count} errors"
                        if result.warning_count > 0:
                            count_msg += f", {result.warning_count} warnings"
                        count_msg += ")"
                    elif result.warning_count > 0:
                        count_msg += f" ({result.warning_count} warnings)"

                    print(f"   {status}{count_msg}")

            except Exception as e:
                print(f"   ❌ ERROR: {validator_name} validation failed: {e}")
                all_passed = False

        return all_passed

    def _filter_errors(self, errors: list[Any]) -> list[Any]:
        """Filter errors based on settings."""
        if self.include_info:
            return errors
        else:
            return [e for e in errors if e.level != ValidationLevel.INFO]

    def print_detailed_report(self) -> None:
        """Print detailed validation report."""
        print("\n" + "=" * 70)
        print("DETAILED VALIDATION REPORT")
        print("=" * 70)

        if not self.all_errors:
            print("✅ No issues found!")
            self._print_summary_statistics()
            return

        # Group errors by severity
        errors_by_level: dict[Any, list[Any]] = {}
        for error in self.all_errors:
            level = error.level
            if level not in errors_by_level:
                errors_by_level[level] = []
            errors_by_level[level].append(error)

        # Print errors by severity
        level_order = [
            ValidationLevel.ERROR,
            ValidationLevel.WARNING,
            ValidationLevel.INFO,
        ]
        level_icons = {
            ValidationLevel.ERROR: "🚨",
            ValidationLevel.WARNING: "⚠️",
            ValidationLevel.INFO: "💡",
        }

        for level in level_order:
            if level not in errors_by_level:
                continue

            errors = errors_by_level[level]
            icon = level_icons[level]
            print(f"\n{icon} {level.value.upper()} ({len(errors)}):")

            for i, error in enumerate(errors, 1):
                self._print_error_detail(error, i)

        self._print_summary_statistics()

    def _print_error_detail(self, error: Any, number: int) -> None:
        """Print detailed information about an error."""
        print(f"\n  {number}. {error.message}")

        # Location information
        if error.file_path:
            location = f"📄 {error.file_path}"
            if error.line_number:
                location += f":{error.line_number}"
                if error.column:
                    location += f":{error.column}"
            print(f"     {location}")

        # Context
        if error.context and self.verbose:
            print(f"     📝 Context: {error.context}")

        # Suggestion
        if error.suggestion:
            print(f"     💡 Suggestion: {error.suggestion}")

    def _print_summary_statistics(self) -> None:
        """Print summary statistics."""
        if not self.verbose:
            return

        print("\n📊 SUMMARY STATISTICS:")

        for validator_name, result in self.validation_results.items():
            if not result.metadata:
                continue

            print(f"\n  {validator_name}:")

            # Key statistics for each validator
            metadata = result.metadata

            if validator_name == "Citations":
                stats = [
                    ("Total citations", "total_citations"),
                    ("Unique citations", "unique_citations"),
                    ("Bibliography entries", "bibliography_keys"),
                    ("Undefined citations", "undefined_citations"),
                ]
            elif validator_name == "Cross-references":
                stats = [
                    ("Labels defined", "total_labels_defined"),
                    ("References used", "total_references_used"),
                ]
            elif validator_name == "Figures":
                stats = [
                    ("Total figures", "total_figures"),
                    ("Available files", "available_files"),
                ]
            elif validator_name == "Mathematics":
                stats = [
                    ("Math expressions", "total_math_expressions"),
                    ("Equation labels", "unique_equation_labels"),
                ]
            elif validator_name == "Syntax":
                stats = [("Syntax elements", "total_elements")]
            elif validator_name == "LaTeX Errors":
                stats = [
                    ("LaTeX errors", "total_errors"),
                    ("LaTeX warnings", "total_warnings"),
                ]
            else:
                stats = []

            for stat_name, key in stats:
                if key in metadata:
                    print(f"    • {stat_name}: {metadata[key]}")

    def print_summary(self) -> None:
        """Print brief validation summary."""
        if not self.all_errors:
            print("✅ Validation completed successfully - no issues found!")
            return

        error_count = sum(
            1 for e in self.all_errors if e.level == ValidationLevel.ERROR
        )
        warning_count = sum(
            1 for e in self.all_errors if e.level == ValidationLevel.WARNING
        )
        info_count = sum(1 for e in self.all_errors if e.level == ValidationLevel.INFO)

        if error_count > 0:
            print(f"❌ Validation failed with {error_count} error(s)")
        else:
            print("⚠️  Validation passed with warnings")

        if warning_count > 0:
            print(f"   {warning_count} warning(s) found")
        if info_count > 0 and self.include_info:
            print(f"   {info_count} info message(s)")


def main():
    """Main entry point for unified validation command."""
    parser = argparse.ArgumentParser(
        description="Comprehensive manuscript validation for rxiv-maker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s MANUSCRIPT                    # Basic validation
  %(prog)s MANUSCRIPT --verbose          # Detailed output
  %(prog)s MANUSCRIPT --include-info     # Include informational messages
  %(prog)s MANUSCRIPT --no-latex         # Skip LaTeX error parsing
  %(prog)s MANUSCRIPT --detailed         # Full detailed report
        """,
    )

    parser.add_argument("manuscript_path", help="Path to the manuscript directory")

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed validation progress and statistics",
    )

    parser.add_argument(
        "--include-info",
        action="store_true",
        help="Include informational messages in output",
    )

    parser.add_argument(
        "--no-latex", action="store_true", help="Skip LaTeX compilation error parsing"
    )

    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed error report with context and suggestions",
    )

    args = parser.parse_args()

    # Create and run validator
    validator = UnifiedValidator(
        manuscript_path=args.manuscript_path,
        verbose=args.verbose,
        include_info=args.include_info,
        check_latex=not args.no_latex,
    )

    validation_passed = validator.validate_all()

    if args.detailed:
        validator.print_detailed_report()
    else:
        validator.print_summary()

    # Exit with appropriate code
    sys.exit(0 if validation_passed else 1)


if __name__ == "__main__":
    main()
