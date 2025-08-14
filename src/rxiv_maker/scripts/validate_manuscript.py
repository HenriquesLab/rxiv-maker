#!/usr/bin/env python3
"""Enhanced Manuscript Validation Script for Rxiv-Maker.

This script provides comprehensive validation for manuscript directories,
including structure, content, syntax, and LaTeX compilation error analysis.

The validator checks for:
- Required files (config, main content, bibliography)
- Required directories (figures)
- Configuration file validity
- Basic content structure
- Citation syntax and bibliography references
- Cross-reference consistency (figures, tables, equations)
- Figure file existence and syntax
- Mathematical expression validity
- Special Markdown syntax elements
- LaTeX compilation errors (if log file exists)
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

# Import new validators with proper fallback handling
if TYPE_CHECKING:
    from ..validators import (
        CitationValidator,
        FigureValidator,
        LaTeXErrorParser,
        MathValidator,
        ReferenceValidator,
        SyntaxValidator,
        ValidationLevel,
    )

ENHANCED_VALIDATION_AVAILABLE = False

try:
    from ..validators import (
        CitationValidator,
        FigureValidator,
        LaTeXErrorParser,
        MathValidator,
        ReferenceValidator,
        SyntaxValidator,
        ValidationLevel,
    )

    ENHANCED_VALIDATION_AVAILABLE = True
except ImportError:
    try:
        # Try absolute import when run as script
        from rxiv_maker.validators import (  # type: ignore[no-redef]
            CitationValidator,  # type: ignore[no-redef]
            FigureValidator,  # type: ignore[no-redef]
            LaTeXErrorParser,  # type: ignore[no-redef]
            MathValidator,  # type: ignore[no-redef]
            ReferenceValidator,  # type: ignore[no-redef]
            SyntaxValidator,  # type: ignore[no-redef]
            ValidationLevel,  # type: ignore[no-redef]
        )

        ENHANCED_VALIDATION_AVAILABLE = True
    except ImportError:
        pass

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class ManuscriptValidator:
    """Validates manuscript structure and requirements for Rxiv-Maker."""

    REQUIRED_FILES = {
        "00_CONFIG.yml": "Configuration file with manuscript metadata",
        "01_MAIN.md": "Main manuscript content in Markdown format",
        "03_REFERENCES.bib": "Bibliography file in BibTeX format",
    }

    OPTIONAL_FILES = {
        "02_SUPPLEMENTARY_INFO.md": "Supplementary information content",
    }

    REQUIRED_DIRS = {
        "FIGURES": "Directory for manuscript figures",
    }

    REQUIRED_CONFIG_FIELDS = {
        "title": "Manuscript title",
        "authors": "List of authors",
        "date": "Publication date",
        "keywords": "Keywords for the manuscript",
    }

    def __init__(
        self,
        manuscript_path: Path,
        skip_enhanced: bool = False,
        show_stats: bool = False,
    ):
        """Initialize validator with manuscript directory path."""
        self.manuscript_path = Path(manuscript_path)
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info_messages: list[str] = []
        self.validation_metadata: dict[str, Any] = {}
        self.skip_enhanced = skip_enhanced
        self.show_stats = show_stats

    def validate_directory_structure(self) -> bool:
        """Validate that the manuscript directory exists and is accessible."""
        if not self.manuscript_path.exists():
            self.errors.append(f"Manuscript directory not found: {self.manuscript_path}")
            return False

        if not self.manuscript_path.is_dir():
            self.errors.append(f"Path is not a directory: {self.manuscript_path}")
            return False

        logger.info(f"✓ Manuscript directory found: {self.manuscript_path}")
        return True

    def validate_required_files(self) -> bool:
        """Check for required files in the manuscript directory."""
        all_files_present = True

        for filename, description in self.REQUIRED_FILES.items():
            file_path = self.manuscript_path / filename
            if not file_path.exists():
                self.errors.append(f"Required file missing: {filename} ({description})")
                all_files_present = False
            else:
                logger.info(f"✓ Found required file: {filename}")

        return all_files_present

    def validate_optional_files(self) -> None:
        """Check for optional files and warn if missing."""
        for filename, description in self.OPTIONAL_FILES.items():
            file_path = self.manuscript_path / filename
            if not file_path.exists():
                self.warnings.append(f"Optional file missing: {filename} ({description})")
            else:
                logger.info(f"✓ Found optional file: {filename}")

    def validate_required_directories(self) -> bool:
        """Check for required directories."""
        all_dirs_present = True

        for dirname, description in self.REQUIRED_DIRS.items():
            dir_path = self.manuscript_path / dirname
            if not dir_path.exists():
                self.errors.append(f"Required directory missing: {dirname} ({description})")
                all_dirs_present = False
            elif not dir_path.is_dir():
                self.errors.append(f"Path exists but is not a directory: {dirname}")
                all_dirs_present = False
            else:
                logger.info(f"✓ Found required directory: {dirname}")

        return all_dirs_present

    def validate_config_file(self) -> bool:
        """Validate the configuration YAML file."""
        config_path = self.manuscript_path / "00_CONFIG.yml"
        if not config_path.exists():
            # This error is already caught in validate_required_files
            return False

        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML in config file: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading config file: {e}")
            return False

        if not isinstance(config, dict):
            self.errors.append("Config file must contain a YAML dictionary")
            return False

        # Check required fields
        config_valid = True
        for field, description in self.REQUIRED_CONFIG_FIELDS.items():
            if field not in config:
                self.errors.append(f"Missing required config field: {field} ({description})")
                config_valid = False
            elif not config[field]:
                self.warnings.append(f"Config field is empty: {field} ({description})")

        if config_valid:
            logger.info("✓ Configuration file is valid")

        return config_valid

    def validate_bibliography(self) -> bool:
        """Basic validation of the bibliography file."""
        bib_path = self.manuscript_path / "03_REFERENCES.bib"
        if not bib_path.exists():
            # This error is already caught in validate_required_files
            return False

        try:
            with open(bib_path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"Error reading bibliography file: {e}")
            return False

        # Basic check for BibTeX entries
        if not content.strip():
            self.warnings.append("Bibliography file is empty")
        elif "@" not in content:
            self.warnings.append("Bibliography file appears to contain no BibTeX entries")
        else:
            logger.info("✓ Bibliography file appears to contain BibTeX entries")

        return True

    def validate_main_content(self) -> bool:
        """Basic validation of the main manuscript file."""
        main_path = self.manuscript_path / "01_MAIN.md"
        if not main_path.exists():
            # This error is already caught in validate_required_files
            return False

        try:
            with open(main_path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"Error reading main manuscript file: {e}")
            return False

        if not content.strip():
            self.errors.append("Main manuscript file is empty")
            return False

        # Check for common sections
        content_lower = content.lower()
        common_sections = [
            "abstract",
            "introduction",
            "methods",
            "results",
            "discussion",
        ]
        found_sections = [section for section in common_sections if section in content_lower]

        if len(found_sections) < 2:
            self.warnings.append(
                f"Main manuscript appears to have few standard sections. "
                f"Found: {', '.join(found_sections) if found_sections else 'none'}"
            )

        logger.info("✓ Main manuscript file is readable and non-empty")
        return True

    def check_figure_references(self) -> None:
        """Check if referenced figures exist in the FIGURES directory."""
        main_path = self.manuscript_path / "01_MAIN.md"
        figures_dir = self.manuscript_path / "FIGURES"

        if not main_path.exists() or not figures_dir.exists():
            return

        try:
            with open(main_path, encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return

        # Simple regex to find figure references
        import re

        figure_refs = re.findall(r"!\[.*?\]\((FIGURES/[^)]+)\)", content)

        missing_figures = []
        for fig_ref in figure_refs:
            fig_path = self.manuscript_path / fig_ref
            if not fig_path.exists():
                missing_figures.append(fig_ref)

        if missing_figures:
            self.warnings.append(f"Referenced figures not found: {', '.join(missing_figures)}")
        elif figure_refs:
            logger.info(f"✓ All {len(figure_refs)} referenced figures found")

    def run_enhanced_validation(self) -> bool:
        """Run enhanced semantic validation using new validators."""
        if self.skip_enhanced:
            logger.info("Skipping enhanced validation (--basic-only)")
            return True

        if not ENHANCED_VALIDATION_AVAILABLE:
            self.warnings.append("Enhanced validation not available - install validation dependencies")
            return True

        enhanced_validation_passed = True
        manuscript_str = str(self.manuscript_path)

        # Run citation validation
        try:
            citation_validator = CitationValidator(manuscript_str)
            citation_result = citation_validator.validate()
            enhanced_validation_passed &= self._process_validation_result(citation_result)
        except Exception as e:
            self.warnings.append(f"Citation validation failed: {e}")

        # Run reference validation
        try:
            reference_validator = ReferenceValidator(manuscript_str)
            reference_result = reference_validator.validate()
            enhanced_validation_passed &= self._process_validation_result(reference_result)
        except Exception as e:
            self.warnings.append(f"Reference validation failed: {e}")

        # Run figure validation
        try:
            figure_validator = FigureValidator(manuscript_str)
            figure_result = figure_validator.validate()
            enhanced_validation_passed &= self._process_validation_result(figure_result)
        except Exception as e:
            self.warnings.append(f"Figure validation failed: {e}")

        # Run math validation
        try:
            math_validator = MathValidator(manuscript_str)
            math_result = math_validator.validate()
            enhanced_validation_passed &= self._process_validation_result(math_result)
        except Exception as e:
            self.warnings.append(f"Math validation failed: {e}")

        # Run syntax validation
        try:
            syntax_validator = SyntaxValidator(manuscript_str)
            syntax_result = syntax_validator.validate()
            enhanced_validation_passed &= self._process_validation_result(syntax_result)
        except Exception as e:
            self.warnings.append(f"Syntax validation failed: {e}")

        # Run LaTeX error parsing (if log file exists)
        try:
            latex_parser = LaTeXErrorParser(manuscript_str, None)  # Let it auto-find the log file
            latex_result = latex_parser.validate()
            enhanced_validation_passed &= self._process_validation_result(latex_result)
        except Exception as e:
            self.warnings.append(f"LaTeX error parsing failed: {e}")

        return enhanced_validation_passed

    def _process_validation_result(self, result) -> bool:
        """Process validation result and add to error/warning lists."""
        validation_passed = True

        # Store metadata
        self.validation_metadata[result.validator_name] = result.metadata

        for error in result.errors:
            if error.level == ValidationLevel.ERROR:
                self.errors.append(self._format_validation_error(error))
                validation_passed = False
            elif error.level == ValidationLevel.WARNING:
                self.warnings.append(self._format_validation_error(error))
            elif error.level == ValidationLevel.INFO:
                self.info_messages.append(self._format_validation_error(error))

        return validation_passed

    def _format_validation_error(self, error) -> str:
        """Format validation error for display."""
        parts = []

        # Add file location if available
        if error.file_path:
            location = error.file_path
            if error.line_number:
                location += f":{error.line_number}"
                if error.column:
                    location += f":{error.column}"
            parts.append(f"({location})")

        # Add main message
        parts.append(error.message)

        # Add suggestion if available
        if error.suggestion:
            parts.append(f"→ {error.suggestion}")

        return " ".join(parts)

    def validate(self) -> bool:
        """Run all validation checks."""
        logger.info(f"Validating manuscript: {self.manuscript_path}")

        # Check directory structure first
        if not self.validate_directory_structure():
            return False

        # Run all validation checks
        checks = [
            self.validate_required_files,
            self.validate_required_directories,
            self.validate_config_file,
            self.validate_bibliography,
            self.validate_main_content,
        ]

        validation_passed = all(check() for check in checks)

        # Run optional checks that don't affect overall validation
        self.validate_optional_files()
        self.check_figure_references()

        # Run enhanced validation
        enhanced_passed = self.run_enhanced_validation()
        validation_passed = validation_passed and enhanced_passed

        return validation_passed

    def print_summary(self) -> None:
        """Print validation summary."""
        print("\n" + "=" * 60)
        print("MANUSCRIPT VALIDATION SUMMARY")
        print("=" * 60)

        if not self.errors and not self.warnings:
            print("✅ Validation PASSED - No issues found!")
        elif not self.errors:
            print("⚠️  Validation PASSED with warnings")
        else:
            print("❌ Validation FAILED")

        if self.errors:
            print(f"\n🚨 ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        if self.info_messages:
            print(f"\n💡 INFO ({len(self.info_messages)}):")
            for i, info in enumerate(self.info_messages, 1):
                print(f"  {i}. {info}")

        # Print validation statistics if available
        if self.validation_metadata and ENHANCED_VALIDATION_AVAILABLE and self.show_stats:
            self._print_validation_statistics()

        print("\n" + "=" * 60)

    def _print_validation_statistics(self) -> None:
        """Print enhanced validation statistics."""
        print("\n📊 VALIDATION STATISTICS:")

        for validator_name, metadata in self.validation_metadata.items():
            if not metadata:
                continue

            validator_display = validator_name.replace("Validator", "").replace("Parser", "")
            print(f"\n  {validator_display}:")

            # Display key statistics for each validator
            if validator_name == "CitationValidator":
                if "total_citations" in metadata:
                    print(f"    • Total citations: {metadata['total_citations']}")
                if "unique_citations" in metadata:
                    print(f"    • Unique citations: {metadata['unique_citations']}")
                if "bibliography_keys" in metadata:
                    print(f"    • Bibliography entries: {metadata['bibliography_keys']}")

            elif validator_name == "ReferenceValidator":
                if "total_labels_defined" in metadata:
                    print(f"    • Labels defined: {metadata['total_labels_defined']}")
                if "total_references_used" in metadata:
                    print(f"    • References used: {metadata['total_references_used']}")

            elif validator_name == "FigureValidator":
                if "total_figures" in metadata:
                    print(f"    • Total figures: {metadata['total_figures']}")
                if "available_files" in metadata:
                    print(f"    • Available files: {metadata['available_files']}")

            elif validator_name == "MathValidator":
                if "total_math_expressions" in metadata:
                    print(f"    • Math expressions: {metadata['total_math_expressions']}")
                if "unique_equation_labels" in metadata:
                    print(f"    • Equation labels: {metadata['unique_equation_labels']}")

            elif validator_name == "SyntaxValidator":
                if "total_elements" in metadata:
                    print(f"    • Syntax elements: {metadata['total_elements']}")

            elif validator_name == "LaTeXErrorParser":
                if "total_errors" in metadata:
                    print(f"    • LaTeX errors: {metadata['total_errors']}")
                if "total_warnings" in metadata:
                    print(f"    • LaTeX warnings: {metadata['total_warnings']}")


def main():
    """Main entry point for the manuscript validator."""
    parser = argparse.ArgumentParser(
        description="Validate Rxiv-Maker manuscript structure and requirements",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s MANUSCRIPT                    # Basic validation
  %(prog)s MANUSCRIPT --detailed         # Comprehensive analysis
  %(prog)s MANUSCRIPT --show-stats       # Include statistics
  %(prog)s MANUSCRIPT --basic-only       # Structure only
  %(prog)s MANUSCRIPT --verbose          # Detailed output

Validation Types:
  • Basic validation: File structure, YAML syntax, bibliography format
  • Enhanced validation: Citations, cross-references, figures, math syntax
  • Detailed validation: Comprehensive error analysis with context and suggestions

Common Validation Issues:
  • Undefined citations: Add missing entries to 03_REFERENCES.bib
  • Missing figures: Check file paths in FIGURES/ directory
  • Broken references: Ensure labels are properly defined
  • Table formatting: Add separator rows (| --- |) after headers
  • Math errors: Check for balanced braces in LaTeX expressions

For LaTeX compilation errors after building, check the .log file in output/
        """,
    )

    parser.add_argument(
        "manuscript_path",
        help="Path to the manuscript directory to validate",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational messages",
    )

    parser.add_argument(
        "--basic-only",
        action="store_true",
        help="Run only basic validation (skip enhanced semantic validation)",
    )

    parser.add_argument(
        "--show-stats",
        action="store_true",
        help="Show detailed validation statistics",
    )

    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Run comprehensive validation with detailed error analysis",
    )

    args = parser.parse_args()

    # Configure logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle detailed mode by calling the unified validator
    if args.detailed:
        import os
        import subprocess

        try:
            # Set PYTHONPATH to include src directory
            env = os.environ.copy()
            src_path = os.path.join(os.getcwd(), "src")
            if "PYTHONPATH" in env:
                env["PYTHONPATH"] = src_path + ":" + env["PYTHONPATH"]
            else:
                env["PYTHONPATH"] = src_path

            cmd = [
                sys.executable,
                "-m",
                "rxiv_maker.cli",
                "validate",
                args.manuscript_path,
                "--detailed",
            ]
            result = subprocess.run(cmd, check=False, env=env)
            sys.exit(result.returncode)
        except FileNotFoundError:
            print("❌ Detailed validation not available")
            print("💡 Use basic validation options instead")
            sys.exit(1)

    # Validate the manuscript
    validator = ManuscriptValidator(args.manuscript_path, skip_enhanced=args.basic_only, show_stats=args.show_stats)
    validation_passed = validator.validate()
    validator.print_summary()

    # Exit with appropriate code
    sys.exit(0 if validation_passed else 1)


if __name__ == "__main__":
    main()
