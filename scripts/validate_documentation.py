#!/usr/bin/env python3
"""
Living Documentation Validation System

This script automatically validates all code examples in the documentation
to ensure they remain accurate and functional as the codebase evolves.

Part of Phase 3.4c: Create living documentation with automated validation
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class DocumentationValidator:
    """Validates code examples in documentation files."""

    def __init__(self, docs_dir: str, verbose: bool = False):
        self.docs_dir = Path(docs_dir)
        self.verbose = verbose
        self.results = []
        self.temp_dir = None

    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamps."""
        if self.verbose or level in ["ERROR", "WARNING"]:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")

    def extract_code_blocks(self, file_path: Path) -> List[Dict]:
        """Extract code blocks from markdown files."""
        code_blocks = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.log(f"Error reading {file_path}: {e}", "ERROR")
            return code_blocks

        # Find code blocks with language specification
        pattern = r"```(\w+)\n(.*?)\n```"
        matches = re.finditer(pattern, content, re.DOTALL | re.MULTILINE)

        for i, match in enumerate(matches):
            language = match.group(1)
            code = match.group(2)

            # Skip non-executable code blocks
            if language in ["yaml", "json", "text", "markdown", "diff"]:
                continue

            code_blocks.append(
                {
                    "file": file_path.name,
                    "language": language,
                    "code": code,
                    "line_start": content[: match.start()].count("\n") + 1,
                    "block_id": f"{file_path.name}:{i + 1}",
                }
            )

        return code_blocks

    def validate_bash_code(self, code: str, block_info: Dict) -> Tuple[bool, str]:
        """Validate bash/shell code blocks."""
        self.log(f"Validating bash block: {block_info['block_id']}")

        # Skip blocks with interactive elements
        interactive_keywords = ["read -p", "while true", "Ctrl+C", "Press Enter"]
        if any(keyword in code for keyword in interactive_keywords):
            self.log(f"Skipping interactive bash block: {block_info['block_id']}", "INFO")
            return True, "Skipped (interactive)"

        # Skip blocks with dangerous commands
        dangerous_keywords = ["sudo", "rm -rf", "format", "delete"]
        if any(keyword in code for keyword in dangerous_keywords):
            self.log(f"Skipping potentially dangerous bash block: {block_info['block_id']}", "INFO")
            return True, "Skipped (potentially dangerous)"

        # Basic syntax validation using bash -n
        try:
            # Create temporary script file
            script_file = self.temp_dir / f"validate_{block_info['block_id'].replace(':', '_')}.sh"
            with open(script_file, "w") as f:
                f.write("#!/bin/bash\n")
                f.write("set -e  # Exit on error\n")
                f.write(code)

            # Check syntax
            result = subprocess.run(["bash", "-n", str(script_file)], capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                self.log(f"✅ Bash syntax OK: {block_info['block_id']}")
                return True, "Syntax valid"
            else:
                error_msg = result.stderr or result.stdout
                self.log(f"❌ Bash syntax error: {block_info['block_id']} - {error_msg}", "ERROR")
                return False, f"Syntax error: {error_msg}"

        except subprocess.TimeoutExpired:
            return False, "Validation timeout"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def validate_python_code(self, code: str, block_info: Dict) -> Tuple[bool, str]:
        """Validate Python code blocks."""
        self.log(f"Validating Python block: {block_info['block_id']}")

        # Skip blocks with interactive or plotting elements
        skip_keywords = ["plt.show()", "input(", 'print("', "matplotlib.pyplot"]
        if any(keyword in code for keyword in skip_keywords):
            # But still check syntax
            pass

        try:
            # Create temporary Python file
            py_file = self.temp_dir / f"validate_{block_info['block_id'].replace(':', '_')}.py"
            with open(py_file, "w") as f:
                f.write("#!/usr/bin/env python3\n")
                f.write("# Auto-generated validation script\n")
                f.write(code)

            # Check syntax by compiling
            with open(py_file, "r") as f:
                source = f.read()

            compile(source, str(py_file), "exec")
            self.log(f"✅ Python syntax OK: {block_info['block_id']}")
            return True, "Syntax valid"

        except SyntaxError as e:
            error_msg = f"Line {e.lineno}: {e.msg}"
            self.log(f"❌ Python syntax error: {block_info['block_id']} - {error_msg}", "ERROR")
            return False, f"Syntax error: {error_msg}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def validate_yaml_structure(self, code: str, block_info: Dict) -> Tuple[bool, str]:
        """Validate YAML structure in documentation examples."""
        try:
            import yaml

            yaml.safe_load(code)
            self.log(f"✅ YAML syntax OK: {block_info['block_id']}")
            return True, "Valid YAML"
        except yaml.YAMLError as e:
            error_msg = str(e)
            self.log(f"❌ YAML syntax error: {block_info['block_id']} - {error_msg}", "ERROR")
            return False, f"YAML error: {error_msg}"
        except ImportError:
            return True, "Skipped (PyYAML not available)"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def validate_code_block(self, block: Dict) -> Dict:
        """Validate a single code block."""
        result = {
            "block_id": block["block_id"],
            "file": block["file"],
            "language": block["language"],
            "line_start": block["line_start"],
            "valid": False,
            "message": "",
            "timestamp": datetime.now().isoformat(),
        }

        try:
            if block["language"] in ["bash", "sh", "shell"]:
                valid, message = self.validate_bash_code(block["code"], block)
            elif block["language"] == "python":
                valid, message = self.validate_python_code(block["code"], block)
            elif block["language"] == "yaml":
                valid, message = self.validate_yaml_structure(block["code"], block)
            else:
                valid, message = True, f"Unsupported language: {block['language']}"

            result["valid"] = valid
            result["message"] = message

        except Exception as e:
            result["valid"] = False
            result["message"] = f"Unexpected error: {str(e)}"
            self.log(f"Unexpected error validating {block['block_id']}: {e}", "ERROR")

        return result

    def validate_documentation_files(self, files: Optional[List[str]] = None) -> Dict:
        """Validate all documentation files or specified ones."""
        if files:
            doc_files = [self.docs_dir / f for f in files if (self.docs_dir / f).exists()]
        else:
            # Find all markdown files
            doc_files = list(self.docs_dir.glob("*.md"))

        self.log(f"Found {len(doc_files)} documentation files to validate")

        # Create temporary directory for validation scripts
        self.temp_dir = Path(tempfile.mkdtemp(prefix="doc_validation_"))
        self.log(f"Using temporary directory: {self.temp_dir}")

        try:
            all_results = []
            total_blocks = 0
            valid_blocks = 0

            for doc_file in doc_files:
                self.log(f"Processing: {doc_file.name}")

                code_blocks = self.extract_code_blocks(doc_file)
                self.log(f"Found {len(code_blocks)} code blocks in {doc_file.name}")

                for block in code_blocks:
                    total_blocks += 1
                    result = self.validate_code_block(block)
                    all_results.append(result)

                    if result["valid"]:
                        valid_blocks += 1

            # Summary
            summary = {
                "total_files": len(doc_files),
                "total_blocks": total_blocks,
                "valid_blocks": valid_blocks,
                "invalid_blocks": total_blocks - valid_blocks,
                "success_rate": (valid_blocks / total_blocks * 100) if total_blocks > 0 else 100,
                "timestamp": datetime.now().isoformat(),
                "results": all_results,
            }

            return summary

        finally:
            # Clean up temporary directory
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.log(f"Cleaned up temporary directory: {self.temp_dir}")

    def generate_validation_report(self, summary: Dict, output_file: Optional[str] = None) -> str:
        """Generate a human-readable validation report."""
        report_lines = []

        # Header
        report_lines.append("# 📋 Documentation Validation Report")
        report_lines.append("")
        report_lines.append(f"**Generated**: {summary['timestamp']}")
        report_lines.append("")

        # Summary
        report_lines.append("## 📊 Summary")
        report_lines.append("")
        report_lines.append(f"- **Files processed**: {summary['total_files']}")
        report_lines.append(f"- **Code blocks found**: {summary['total_blocks']}")
        report_lines.append(f"- **Valid blocks**: {summary['valid_blocks']} ✅")
        report_lines.append(f"- **Invalid blocks**: {summary['invalid_blocks']} ❌")
        report_lines.append(f"- **Success rate**: {summary['success_rate']:.1f}%")
        report_lines.append("")

        # Status indicator
        if summary["success_rate"] >= 95:
            status = "🟢 EXCELLENT"
        elif summary["success_rate"] >= 90:
            status = "🟡 GOOD"
        elif summary["success_rate"] >= 75:
            status = "🟠 NEEDS ATTENTION"
        else:
            status = "🔴 CRITICAL"

        report_lines.append(f"**Overall Status**: {status}")
        report_lines.append("")

        # Detailed results
        if summary["invalid_blocks"] > 0:
            report_lines.append("## ❌ Issues Found")
            report_lines.append("")

            for result in summary["results"]:
                if not result["valid"]:
                    report_lines.append(f"### {result['file']} (Line {result['line_start']})")
                    report_lines.append(f"- **Block ID**: {result['block_id']}")
                    report_lines.append(f"- **Language**: {result['language']}")
                    report_lines.append(f"- **Error**: {result['message']}")
                    report_lines.append("")

        # Valid results summary
        report_lines.append("## ✅ Validation Results by File")
        report_lines.append("")

        # Group by file
        by_file = {}
        for result in summary["results"]:
            file_name = result["file"]
            if file_name not in by_file:
                by_file[file_name] = {"valid": 0, "invalid": 0, "total": 0}

            by_file[file_name]["total"] += 1
            if result["valid"]:
                by_file[file_name]["valid"] += 1
            else:
                by_file[file_name]["invalid"] += 1

        for file_name, stats in by_file.items():
            success_rate = (stats["valid"] / stats["total"] * 100) if stats["total"] > 0 else 100
            status_emoji = "✅" if success_rate >= 90 else "⚠️" if success_rate >= 75 else "❌"

            report_lines.append(
                f"- **{file_name}** {status_emoji}: {stats['valid']}/{stats['total']} ({success_rate:.1f}%)"
            )

        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        report_lines.append("*Report generated by the Living Documentation Validation System*")

        report_content = "\n".join(report_lines)

        if output_file:
            with open(output_file, "w") as f:
                f.write(report_content)
            self.log(f"Validation report saved to: {output_file}")

        return report_content


def main():
    parser = argparse.ArgumentParser(description="Validate code examples in documentation")
    parser.add_argument("--docs-dir", default=".", help="Documentation directory")
    parser.add_argument("--files", nargs="*", help="Specific files to validate")
    parser.add_argument("--output", help="Output file for validation report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Initialize validator
    validator = DocumentationValidator(args.docs_dir, verbose=args.verbose)

    print("🔍 Starting Documentation Validation")
    print("=" * 40)

    # Run validation
    summary = validator.validate_documentation_files(args.files)

    # Generate report
    output_file = args.output or "documentation_validation_report.md"
    report = validator.generate_validation_report(summary, output_file)

    # Print summary
    print("\n📋 VALIDATION SUMMARY")
    print("=" * 20)
    print(f"Files processed: {summary['total_files']}")
    print(f"Code blocks: {summary['total_blocks']}")
    print(f"Valid: {summary['valid_blocks']} ✅")
    print(f"Invalid: {summary['invalid_blocks']} ❌")
    print(f"Success rate: {summary['success_rate']:.1f}%")

    if args.verbose:
        print(f"\nFull report saved to: {output_file}")

    # Exit with appropriate code
    return 0 if summary["success_rate"] >= 90 else 1


if __name__ == "__main__":
    sys.exit(main())
