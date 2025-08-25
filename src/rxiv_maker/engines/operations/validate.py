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

import os
from typing import Any

try:
    from ...processors.yaml_processor import extract_yaml_metadata, get_doi_validation_setting
    from ...utils.file_helpers import find_manuscript_md
    from ...validators.base_validator import ValidationLevel
    from ...validators.citation_validator import CitationValidator
    from ...validators.figure_validator import FigureValidator
    from ...validators.latex_error_parser import LaTeXErrorParser
    from ...validators.math_validator import MathValidator
    from ...validators.reference_validator import ReferenceValidator
    from ...validators.syntax_validator import SyntaxValidator

    VALIDATORS_AVAILABLE = True
except ImportError:
    # Try absolute import when run as script
    try:
        from rxiv_maker.processors.yaml_processor import (  # type: ignore
            extract_yaml_metadata,
            get_doi_validation_setting,
        )
        from rxiv_maker.utils.file_helpers import find_manuscript_md  # type: ignore
        from rxiv_maker.validators.base_validator import ValidationLevel  # type: ignore
        from rxiv_maker.validators.citation_validator import CitationValidator  # type: ignore
        from rxiv_maker.validators.figure_validator import FigureValidator  # type: ignore
        from rxiv_maker.validators.latex_error_parser import LaTeXErrorParser  # type: ignore
        from rxiv_maker.validators.math_validator import MathValidator  # type: ignore
        from rxiv_maker.validators.reference_validator import ReferenceValidator  # type: ignore
        from rxiv_maker.validators.syntax_validator import SyntaxValidator  # type: ignore

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
        enable_doi_validation: bool = True,
    ):
        """Initialize unified validator.

        Args:
            manuscript_path: Path to manuscript directory
            verbose: Show detailed output
            include_info: Include informational messages
            check_latex: Parse LaTeX compilation errors
            enable_doi_validation: Enable DOI validation against CrossRef API
        """
        self.manuscript_path = manuscript_path
        self.verbose = verbose
        self.include_info = include_info
        self.check_latex = check_latex
        self.enable_doi_validation = enable_doi_validation

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

        if self.verbose:
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
                # Pass DOI validation option to CitationValidator
                if validator_class == CitationValidator:
                    validator = validator_class(
                        self.manuscript_path,
                        enable_doi_validation=self.enable_doi_validation,
                    )
                else:
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
                if self.verbose:
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
                    ("Unused entries", "unused_entries"),
                    ("Undefined citations", "undefined_citations"),
                ]
                # Add DOI validation statistics if available
                if "doi_validation" in metadata:
                    doi_stats = metadata["doi_validation"]
                    stats.extend(
                        [
                            ("DOIs found", "total_dois"),
                            ("DOIs validated", "validated_dois"),
                            ("DOI format errors", "invalid_format"),
                            ("API failures", "api_failures"),
                            ("Metadata mismatches", "mismatched_metadata"),
                        ]
                    )
                    # Update metadata with doi_validation data for display
                    metadata.update({f"doi_{k}": v for k, v in doi_stats.items()})
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
            print("✅ Validation passed!")
            return

        error_count = sum(1 for e in self.all_errors if e.level == ValidationLevel.ERROR)
        warning_count = sum(1 for e in self.all_errors if e.level == ValidationLevel.WARNING)
        info_count = sum(1 for e in self.all_errors if e.level == ValidationLevel.INFO)

        # Print status
        if error_count > 0:
            print(f"❌ Validation failed with {error_count} error(s)")
            if warning_count > 0:
                print(f"   {warning_count} warning(s) found")
        elif warning_count > 0:
            print("⚠️  Validation passed with warnings")
            print(f"   {warning_count} warning(s) found")
        else:
            print("✅ Validation passed!")

        # Show errors
        if error_count > 0:
            print("\n🚨 ERRORS:")
            errors = [e for e in self.all_errors if e.level == ValidationLevel.ERROR]
            for i, error in enumerate(errors, 1):
                location = ""
                if error.file_path:
                    location = f" ({error.file_path}"
                    if error.line_number:
                        location += f":{error.line_number}"
                    location += ")"
                print(f"  {i}. {error.message}{location}")

        # Show warnings
        if warning_count > 0:
            print("\n⚠️  WARNINGS:")
            warnings = [e for e in self.all_errors if e.level == ValidationLevel.WARNING]
            for i, warning in enumerate(warnings, 1):
                location = ""
                if warning.file_path:
                    location = f" ({warning.file_path}"
                    if warning.line_number:
                        location += f":{warning.line_number}"
                    location += ")"
                print(f"  {i}. {warning.message}{location}")

        # Show info messages only in verbose or include-info mode
        if info_count > 0 and self.include_info:
            print(f"\n💡 INFO ({info_count}):")
            info_messages = [e for e in self.all_errors if e.level == ValidationLevel.INFO]
            for i, info in enumerate(info_messages, 1):
                location = ""
                if info.file_path:
                    location = f" ({info.file_path}"
                    if info.line_number:
                        location += f":{info.line_number}"
                    location += ")"
                print(f"  {i}. {info.message}{location}")


def validate_manuscript(
    manuscript_path: str,
    verbose: bool = False,
    include_info: bool = False,
    check_latex: bool = True,
    enable_doi_validation: bool | None = None,
    detailed: bool = False,
) -> bool:
    """Validate manuscript with comprehensive checks.

    Args:
        manuscript_path: Path to the manuscript directory
        verbose: Show detailed validation progress and statistics
        include_info: Include informational messages in output
        check_latex: Skip LaTeX compilation error parsing
        enable_doi_validation: Enable/disable DOI validation. If None, reads from config
        detailed: Show detailed error report with context and suggestions

    Returns:
        True if validation passed, False otherwise
    """
    # Determine DOI validation setting from config if not explicitly provided
    if enable_doi_validation is None:
        try:
            manuscript_file = find_manuscript_md(manuscript_path)
            metadata = extract_yaml_metadata(str(manuscript_file))
            enable_doi_validation = get_doi_validation_setting(metadata)
        except Exception:
            # Fall back to default if config reading fails
            enable_doi_validation = True

    # Create and run validator
    validator = UnifiedValidator(
        manuscript_path=manuscript_path,
        verbose=verbose,
        include_info=include_info,
        check_latex=check_latex,
        enable_doi_validation=enable_doi_validation,
    )

    validation_passed = validator.validate_all()

    if detailed:
        validator.print_detailed_report()
    else:
        validator.print_summary()

    return validation_passed


def main():
    """Main entry point for validate command."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate rxiv-maker manuscript structure and content")
    parser.add_argument(
        "manuscript_path",
        nargs="?",
        default="MANUSCRIPT",
        help="Path to manuscript directory",
    )
    parser.add_argument("--detailed", action="store_true", help="Show detailed validation report")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--include-info", action="store_true", help="Include informational messages")
    parser.add_argument("--check-latex", action="store_true", help="Check LaTeX compilation")
    parser.add_argument("--no-doi", action="store_true", help="Disable DOI validation")

    args = parser.parse_args()

    # Determine DOI validation setting: CLI flag overrides config
    enable_doi_validation = None if not args.no_doi else False

    # Run validation
    success = validate_manuscript(
        manuscript_path=args.manuscript_path,
        detailed=args.detailed,
        verbose=args.verbose,
        include_info=args.include_info,
        check_latex=args.check_latex,
        enable_doi_validation=enable_doi_validation,
    )

    if not success:
        exit(1)


if __name__ == "__main__":
    main()
