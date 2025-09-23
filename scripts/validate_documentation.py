#!/usr/bin/env python3
"""
Documentation validation script for rxiv-maker.

Validates code examples in documentation files to ensure they're syntactically correct
and follow project conventions.
"""

import argparse
import ast
import logging
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def extract_python_code_blocks(content: str) -> List[Tuple[str, int]]:
    """Extract Python code blocks from markdown content."""
    code_blocks = []
    lines = content.split("\n")
    in_python_block = False
    current_block = []
    block_start_line = 0

    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```python"):
            in_python_block = True
            block_start_line = i
            current_block = []
        elif line.strip() == "```" and in_python_block:
            in_python_block = False
            if current_block:
                code_blocks.append(("\n".join(current_block), block_start_line))
        elif in_python_block:
            current_block.append(line)

    return code_blocks


def validate_python_syntax(code: str, filename: str, line_num: int) -> bool:
    """Validate Python code syntax."""
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        logger.error(f"{filename}:{line_num + e.lineno}: Syntax error in Python code block: {e}")
        return False
    except Exception as e:
        logger.error(f"{filename}:{line_num}: Error parsing Python code block: {e}")
        return False


def validate_shell_commands(content: str, filename: str) -> bool:
    """Basic validation of shell commands in documentation."""
    # Find shell code blocks
    shell_pattern = r"```(?:bash|sh|shell)\n(.*?)\n```"
    shell_blocks = re.findall(shell_pattern, content, re.DOTALL)

    valid = True
    for block in shell_blocks:
        # Basic checks for dangerous commands
        if re.search(r"\brm\s+-rf\s+/", block):
            logger.warning(f"{filename}: Potentially dangerous rm -rf / command found")
            # Don't fail for this, just warn

    return valid


def validate_documentation_file(file_path: Path) -> bool:
    """Validate a single documentation file."""
    logger.info(f"Validating {file_path}")

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return False

    valid = True

    # Validate Python code blocks
    python_blocks = extract_python_code_blocks(content)
    for code, line_num in python_blocks:
        if not validate_python_syntax(code, str(file_path), line_num):
            valid = False

    # Validate shell commands
    if not validate_shell_commands(content, str(file_path)):
        valid = False

    return valid


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Validate documentation code examples")
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"), help="Documentation directory to validate")
    parser.add_argument("--include-root", action="store_true", help="Include markdown files in root directory")
    parser.add_argument("--output", type=Path, help="Output file for validation report (optional)")

    args = parser.parse_args()

    # Find all markdown files
    markdown_files = []

    if args.docs_dir.exists():
        markdown_files.extend(args.docs_dir.rglob("*.md"))

    if args.include_root:
        for pattern in ["*.md", "**/*.md"]:
            markdown_files.extend(Path(".").glob(pattern))

    # Remove duplicates and filter out hidden files and auto-generated API docs
    markdown_files = list(
        {
            f
            for f in markdown_files
            if not any(part.startswith(".") for part in f.parts)
            and not str(f).startswith("src/docs/api/")  # Skip auto-generated API docs
        }
    )

    if not markdown_files:
        logger.info("No markdown files found to validate")
        return True

    logger.info(f"Found {len(markdown_files)} markdown files to validate")

    valid = True
    for file_path in sorted(markdown_files):
        if not validate_documentation_file(file_path):
            valid = False

    # Write output report if requested
    if args.output:
        report_content = f"""# Documentation Validation Report

## Summary
- **Files checked**: {len(markdown_files)}
- **Status**: {"✅ PASSED" if valid else "❌ FAILED"}

## Files Validated
"""
        for file_path in sorted(markdown_files):
            report_content += f"- {file_path}\n"

        args.output.write_text(report_content)
        logger.info(f"Validation report written to {args.output}")

    if valid:
        logger.info("✅ All documentation validation checks passed")
        return True
    else:
        logger.error("❌ Documentation validation failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
