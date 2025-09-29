#!/usr/bin/env python3
"""
Backtick validation script for rxiv-maker.

This script validates that all backtick content in markdown files appears correctly
in the generated PDF, ensuring proper conversion and display of LaTeX commands,
code snippets, and other verbatim content.
"""

import argparse
import logging
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


# Color codes for terminal output
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


@dataclass
class BacktickItem:
    """Represents a backtick item found in markdown."""

    content: str
    file_path: str
    line_number: int
    context: str
    backtick_type: str  # 'single', 'double'


@dataclass
class ValidationResult:
    """Result of validating a backtick item."""

    backtick_item: BacktickItem
    found_in_pdf: bool
    expected_text: str
    actual_matches: List[str]
    issues: List[str]


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
    return logging.getLogger(__name__)


def extract_backticks_from_file(file_path: Path) -> List[BacktickItem]:
    """Extract all backtick content from a markdown file."""
    backticks = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        logging.error(f"Failed to read {file_path}: {e}")
        return backticks

    for line_num, line in enumerate(lines, 1):
        # Find double backticks first (to avoid conflicts with single)
        double_backtick_pattern = r"``([^`]+)``"
        for match in re.finditer(double_backtick_pattern, line):
            content = match.group(1)
            context = line.strip()
            backticks.append(
                BacktickItem(
                    content=content,
                    file_path=str(file_path),
                    line_number=line_num,
                    context=context,
                    backtick_type="double",
                )
            )

        # Find single backticks (but not those already captured by double)
        # Remove double backticks first to avoid interference
        line_no_doubles = re.sub(r"``[^`]+``", "", line)
        single_backtick_pattern = r"`([^`]+)`"
        for match in re.finditer(single_backtick_pattern, line_no_doubles):
            content = match.group(1)
            context = line.strip()
            backticks.append(
                BacktickItem(
                    content=content,
                    file_path=str(file_path),
                    line_number=line_num,
                    context=context,
                    backtick_type="single",
                )
            )

    return backticks


def extract_all_backticks(manuscript_dir: Path) -> List[BacktickItem]:
    """Extract all backticks from all markdown files in manuscript."""
    all_backticks = []

    # Standard manuscript files to check
    markdown_files = ["01_MAIN.md", "02_SUPPLEMENTARY_INFO.md"]

    for filename in markdown_files:
        file_path = manuscript_dir / filename
        if file_path.exists():
            logging.info(f"Extracting backticks from {filename}...")
            file_backticks = extract_backticks_from_file(file_path)
            all_backticks.extend(file_backticks)
            logging.info(f"Found {len(file_backticks)} backtick items in {filename}")
        else:
            logging.warning(f"File not found: {file_path}")

    return all_backticks


def build_pdf(manuscript_dir: Path) -> bool:
    """Build the PDF using rxiv pdf command."""
    logging.info("Building PDF with rxiv pdf...")

    try:
        # Change to manuscript directory and run rxiv pdf
        result = subprocess.run(
            ["rxiv", "pdf", "."],
            cwd=manuscript_dir,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode == 0:
            logging.info("PDF built successfully")
            return True
        else:
            logging.error(f"PDF build failed with return code {result.returncode}")
            if result.stdout:
                logging.error(f"STDOUT: {result.stdout}")
            if result.stderr:
                logging.error(f"STDERR: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logging.error("PDF build timed out after 5 minutes")
        return False
    except Exception as e:
        logging.error(f"Error building PDF: {e}")
        return False


def extract_pdf_text(manuscript_dir: Path) -> Optional[str]:
    """Extract text from the generated PDF."""
    pdf_path = manuscript_dir / "output" / "../manuscript-rxiv-maker/MANUSCRIPT.pdf"

    if not pdf_path.exists():
        logging.error(f"PDF not found at {pdf_path}")
        return None

    try:
        logging.info("Extracting text from PDF...")
        result = subprocess.run(["pdftotext", str(pdf_path), "-"], capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            logging.info(f"Successfully extracted {len(result.stdout)} characters from PDF")
            return result.stdout
        else:
            logging.error(f"pdftotext failed with return code {result.returncode}")
            if result.stderr:
                logging.error(f"STDERR: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        logging.error("PDF text extraction timed out")
        return None
    except FileNotFoundError:
        logging.error("pdftotext command not found. Please install poppler-utils.")
        return None
    except Exception as e:
        logging.error(f"Error extracting PDF text: {e}")
        return None


def normalize_text_for_comparison(text: str) -> str:
    """Normalize text for comparison by handling whitespace and special characters."""
    # Remove extra whitespace and normalize
    normalized = " ".join(text.split())

    # Handle common PDF text extraction issues
    # Remove spaces around braces that might be introduced by PDF extraction
    normalized = re.sub(r"\s*\{\s*", "{", normalized)
    normalized = re.sub(r"\s*\}\s*", "}", normalized)

    # Handle backslash spacing issues
    normalized = re.sub(r"\\\s+", r"\\", normalized)

    return normalized


def get_expected_pdf_text(backtick_content: str) -> str:
    """Get the expected text that should appear in the PDF for given backtick content."""
    # For LaTeX commands, we expect them to appear literally with braces
    # The detokenize should preserve the exact content

    # Special handling for common cases
    if backtick_content.startswith("\\") and "{" in backtick_content and "}" in backtick_content:
        # This is a LaTeX command - should appear exactly as written
        return backtick_content
    elif backtick_content.startswith("@"):
        # Citation reference - should appear as-is
        return backtick_content
    elif backtick_content.startswith("http"):
        # URL - should appear as-is
        return backtick_content
    elif backtick_content.startswith(".") and len(backtick_content) < 10:
        # File extension - should appear as-is
        return backtick_content
    else:
        # Regular code content - should appear as-is
        return backtick_content


def validate_backtick_item(item: BacktickItem, pdf_text: str) -> ValidationResult:
    """Validate a single backtick item against PDF text."""
    expected = get_expected_pdf_text(item.content)
    normalized_pdf_text = normalize_text_for_comparison(pdf_text)
    normalized_expected = normalize_text_for_comparison(expected)

    # Find all occurrences of the expected text in PDF
    actual_matches = []
    issues = []

    # Simple substring search
    if normalized_expected in normalized_pdf_text:
        # Find all matches with some context
        pattern = re.escape(normalized_expected)
        for match in re.finditer(pattern, normalized_pdf_text):
            start = max(0, match.start() - 20)
            end = min(len(normalized_pdf_text), match.end() + 20)
            context = normalized_pdf_text[start:end]
            actual_matches.append(context)

    found_in_pdf = len(actual_matches) > 0

    # Check for common issues
    if not found_in_pdf:
        # Check if it appears without braces
        if "{" in normalized_expected and "}" in normalized_expected:
            without_braces = normalized_expected.replace("{", "").replace("}", "")
            if without_braces in normalized_pdf_text:
                issues.append("Content found but missing braces")

        # Check if backslashes are missing
        if "\\" in normalized_expected:
            without_backslashes = normalized_expected.replace("\\", "")
            if without_backslashes in normalized_pdf_text:
                issues.append("Content found but missing backslashes")

    return ValidationResult(
        backtick_item=item,
        found_in_pdf=found_in_pdf,
        expected_text=expected,
        actual_matches=actual_matches,
        issues=issues,
    )


def print_validation_results(results: List[ValidationResult], verbose: bool = False):
    """Print formatted validation results."""
    passed = sum(1 for r in results if r.found_in_pdf)
    failed = len(results) - passed

    print(f"\n{Colors.BOLD}=== BACKTICK VALIDATION RESULTS ==={Colors.END}")
    print(f"Total backticks checked: {len(results)}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
    print(f"{Colors.RED}Failed: {failed}{Colors.END}")

    if failed > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}FAILED VALIDATIONS:{Colors.END}")
        for i, result in enumerate(results):
            if not result.found_in_pdf:
                print(f"\n{Colors.RED}❌ Failed #{i + 1}:{Colors.END}")
                print(f"  File: {result.backtick_item.file_path}")
                print(f"  Line: {result.backtick_item.line_number}")
                print(f"  Content: {Colors.CYAN}`{result.backtick_item.content}`{Colors.END}")
                print(f"  Expected: {Colors.YELLOW}{result.expected_text}{Colors.END}")
                print(f"  Context: {result.backtick_item.context[:100]}...")
                if result.issues:
                    print(f"  Issues: {', '.join(result.issues)}")

    if verbose and passed > 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}PASSED VALIDATIONS:{Colors.END}")
        for i, result in enumerate(results):
            if result.found_in_pdf:
                print(f"\n{Colors.GREEN}✅ Passed #{i + 1}:{Colors.END}")
                print(f"  Content: {Colors.CYAN}`{result.backtick_item.content}`{Colors.END}")
                print(f"  Matches: {len(result.actual_matches)}")
                if verbose and result.actual_matches:
                    for j, match in enumerate(result.actual_matches[:2]):  # Show first 2 matches
                        print(f"    Match {j + 1}: ...{match}...")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Validate backtick content in rxiv-maker manuscripts")
    parser.add_argument(
        "--manuscript-dir",
        type=Path,
        default=Path("."),
        help="Path to manuscript directory (default: current directory)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--no-build", action="store_true", help="Skip PDF building and use existing PDF")

    args = parser.parse_args()
    logger = setup_logging(args.verbose)

    manuscript_dir = args.manuscript_dir.resolve()

    if not manuscript_dir.exists():
        logger.error(f"Manuscript directory does not exist: {manuscript_dir}")
        return 1

    logger.info(f"Validating backticks in manuscript: {manuscript_dir}")

    # Extract all backticks from markdown files
    logger.info("Extracting backticks from markdown files...")
    all_backticks = extract_all_backticks(manuscript_dir)

    if not all_backticks:
        logger.warning("No backticks found in manuscript files")
        return 0

    logger.info(f"Found {len(all_backticks)} total backtick items")

    # Build PDF if requested
    if not args.no_build:
        if not build_pdf(manuscript_dir):
            logger.error("Failed to build PDF")
            return 1

    # Extract PDF text
    pdf_text = extract_pdf_text(manuscript_dir)
    if pdf_text is None:
        logger.error("Failed to extract text from PDF")
        return 1

    # Validate each backtick item
    logger.info("Validating backtick items against PDF content...")
    results = []
    for item in all_backticks:
        result = validate_backtick_item(item, pdf_text)
        results.append(result)

    # Print results
    print_validation_results(results, args.verbose)

    # Return appropriate exit code
    failed_count = sum(1 for r in results if not r.found_in_pdf)
    return 1 if failed_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
