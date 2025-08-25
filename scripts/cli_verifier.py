#!/usr/bin/env python3
"""
CLI Documentation Verifier

Compares actual CLI implementation with documentation to find mismatches
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# Import our custom modules
from cli_scanner import CLIScanner
from docs_parser import DocumentationScanner


@dataclass
class PhantomOption:
    """Represents an option documented but not implemented."""

    command_name: str
    option_name: str
    documented_in: str
    line_number: int = 0


@dataclass
class MissingOption:
    """Represents an implemented option not documented."""

    command_name: str
    option_name: str
    implemented_in: str
    line_number: int = 0
    help_text: Optional[str] = None


@dataclass
class MismatchedDescription:
    """Represents an option with different descriptions in code vs docs."""

    command_name: str
    option_name: str
    implementation_description: str
    documentation_description: str
    implemented_in: str
    documented_in: str


@dataclass
class MissingCommand:
    """Represents a command that exists in implementation but not in docs."""

    command_name: str
    implemented_in: str
    function_name: str
    help_text: Optional[str] = None


@dataclass
class PhantomCommand:
    """Represents a command documented but not implemented."""

    command_name: str
    documented_in: str
    description: Optional[str] = None


@dataclass
class VerificationReport:
    """Complete verification report with all types of mismatches."""

    phantom_options: List[PhantomOption]
    missing_options: List[MissingOption]
    mismatched_descriptions: List[MismatchedDescription]
    missing_commands: List[MissingCommand]
    phantom_commands: List[PhantomCommand]

    # Summary statistics
    total_implemented_commands: int = 0
    total_documented_commands: int = 0
    total_implemented_options: int = 0
    total_documented_options: int = 0

    def __post_init__(self):
        if self.phantom_options is None:
            self.phantom_options = []
        if self.missing_options is None:
            self.missing_options = []
        if self.mismatched_descriptions is None:
            self.mismatched_descriptions = []
        if self.missing_commands is None:
            self.missing_commands = []
        if self.phantom_commands is None:
            self.phantom_commands = []

    @property
    def has_issues(self) -> bool:
        """Check if any issues were found."""
        return bool(
            self.phantom_options
            or self.missing_options
            or self.mismatched_descriptions
            or self.missing_commands
            or self.phantom_commands
        )

    @property
    def critical_issues_count(self) -> int:
        """Count of critical issues (phantom options and commands)."""
        return len(self.phantom_options) + len(self.phantom_commands)

    @property
    def total_issues_count(self) -> int:
        """Total count of all issues."""
        return (
            len(self.phantom_options)
            + len(self.missing_options)
            + len(self.mismatched_descriptions)
            + len(self.missing_commands)
            + len(self.phantom_commands)
        )


class CLIDocumentationVerifier:
    """Main verifier that compares CLI implementation with documentation."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.cli_scanner = CLIScanner(project_root)
        self.docs_scanner = DocumentationScanner(project_root)

    def verify(self) -> VerificationReport:
        """Run complete verification and return report."""
        print("🔍 Scanning CLI implementation...")
        implemented_commands = self.cli_scanner.scan_cli_files()

        print("📖 Scanning documentation...")
        documented_commands = self.docs_scanner.scan_documentation_files()

        print("⚖️  Comparing implementation with documentation...")

        report = VerificationReport(
            phantom_options=[],
            missing_options=[],
            mismatched_descriptions=[],
            missing_commands=[],
            phantom_commands=[],
            total_implemented_commands=len(implemented_commands),
            total_documented_commands=len(documented_commands),
            total_implemented_options=sum(len(cmd.options) for cmd in implemented_commands.values()),
            total_documented_options=sum(len(cmd.options) for cmd in documented_commands.values()),
        )

        # Find phantom and missing commands
        implemented_cmd_names = set(implemented_commands.keys())
        documented_cmd_names = set(documented_commands.keys())

        # Commands implemented but not documented
        for missing_cmd in implemented_cmd_names - documented_cmd_names:
            cmd = implemented_commands[missing_cmd]
            report.missing_commands.append(
                MissingCommand(
                    command_name=missing_cmd,
                    implemented_in=cmd.file_path,
                    function_name=cmd.function_name,
                    help_text=cmd.help_text,
                )
            )

        # Commands documented but not implemented
        for phantom_cmd in documented_cmd_names - implemented_cmd_names:
            cmd = documented_commands[phantom_cmd]
            report.phantom_commands.append(
                PhantomCommand(command_name=phantom_cmd, documented_in=cmd.source_file, description=cmd.description)
            )

        # Compare options for commands that exist in both
        common_commands = implemented_cmd_names & documented_cmd_names

        for cmd_name in common_commands:
            impl_cmd = implemented_commands[cmd_name]
            doc_cmd = documented_commands[cmd_name]

            # Create option name mappings
            impl_options = {opt.name: opt for opt in impl_cmd.options}
            doc_options = {opt.name: opt for opt in doc_cmd.options}

            # Also map short names to full names
            impl_short_to_full = {}
            for opt in impl_cmd.options:
                if opt.short_name:
                    impl_short_to_full[opt.short_name] = opt.name

            # Find phantom options (documented but not implemented)
            for doc_opt_name, doc_opt in doc_options.items():
                # Check if this documented option exists in implementation
                found = False

                if doc_opt_name in impl_options:
                    found = True
                elif doc_opt_name in impl_short_to_full:
                    found = True
                else:
                    # Try without leading dashes for comparison
                    clean_doc_name = doc_opt_name.lstrip("-")
                    for impl_opt_name in impl_options:
                        if impl_opt_name.lstrip("-") == clean_doc_name:
                            found = True
                            break

                if not found:
                    report.phantom_options.append(
                        PhantomOption(
                            command_name=cmd_name,
                            option_name=doc_opt_name,
                            documented_in=doc_cmd.source_file,
                            line_number=doc_opt.line_number,
                        )
                    )

            # Find missing options (implemented but not documented)
            for impl_opt_name, impl_opt in impl_options.items():
                found = False

                if impl_opt_name in doc_options:
                    found = True
                else:
                    # Check if documented by short name
                    if impl_opt.short_name and impl_opt.short_name in doc_options:
                        found = True
                    else:
                        # Try fuzzy matching
                        clean_impl_name = impl_opt_name.lstrip("-")
                        for doc_opt_name in doc_options:
                            if doc_opt_name.lstrip("-") == clean_impl_name:
                                found = True
                                break

                if not found:
                    report.missing_options.append(
                        MissingOption(
                            command_name=cmd_name,
                            option_name=impl_opt_name,
                            implemented_in=impl_cmd.file_path,
                            line_number=impl_cmd.line_number,
                            help_text=impl_opt.help_text,
                        )
                    )

            # Find mismatched descriptions
            for impl_opt_name, impl_opt in impl_options.items():
                # Find matching documented option
                doc_opt = None
                if impl_opt_name in doc_options:
                    doc_opt = doc_options[impl_opt_name]
                elif impl_opt.short_name and impl_opt.short_name in doc_options:
                    doc_opt = doc_options[impl_opt.short_name]

                if doc_opt and impl_opt.help_text and doc_opt.description:
                    # Simple comparison - could be made more sophisticated
                    if (
                        impl_opt.help_text.strip().lower() != doc_opt.description.strip().lower()
                        and len(abs(len(impl_opt.help_text) - len(doc_opt.description))) > 10
                    ):
                        report.mismatched_descriptions.append(
                            MismatchedDescription(
                                command_name=cmd_name,
                                option_name=impl_opt_name,
                                implementation_description=impl_opt.help_text,
                                documentation_description=doc_opt.description,
                                implemented_in=impl_cmd.file_path,
                                documented_in=doc_cmd.source_file,
                            )
                        )

        return report

    def generate_report(self, report: VerificationReport, format: str = "text") -> str:
        """Generate a human-readable report."""
        if format == "json":
            return self._generate_json_report(report)
        elif format == "markdown":
            return self._generate_markdown_report(report)
        else:
            return self._generate_text_report(report)

    def _generate_text_report(self, report: VerificationReport) -> str:
        """Generate plain text report."""
        lines = []
        lines.append("CLI DOCUMENTATION VERIFICATION REPORT")
        lines.append("=" * 60)
        lines.append(f"Project: {self.project_root}")
        lines.append(f"Timestamp: {__import__('datetime').datetime.now().isoformat()}")
        lines.append("")

        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 30)
        lines.append(f"Commands implemented: {report.total_implemented_commands}")
        lines.append(f"Commands documented: {report.total_documented_commands}")
        lines.append(f"Options implemented: {report.total_implemented_options}")
        lines.append(f"Options documented: {report.total_documented_options}")
        lines.append("")
        lines.append(f"Total issues found: {report.total_issues_count}")
        lines.append(f"Critical issues: {report.critical_issues_count}")
        lines.append("")

        if not report.has_issues:
            lines.append("✅ NO ISSUES FOUND!")
            lines.append("Documentation perfectly matches implementation.")
            return "\n".join(lines)

        # Issues breakdown
        if report.phantom_options:
            lines.append("❌ PHANTOM OPTIONS (documented but not implemented)")
            lines.append("-" * 50)
            for phantom in report.phantom_options:
                lines.append(f"  {phantom.command_name}: {phantom.option_name}")
                lines.append(f"    Documented in: {phantom.documented_in}")
            lines.append("")

        if report.missing_options:
            lines.append("⚠️  MISSING OPTIONS (implemented but not documented)")
            lines.append("-" * 50)
            for missing in report.missing_options:
                lines.append(f"  {missing.command_name}: {missing.option_name}")
                lines.append(f"    Implemented in: {missing.implemented_in}")
                if missing.help_text:
                    lines.append(f"    Help: {missing.help_text}")
            lines.append("")

        if report.phantom_commands:
            lines.append("❌ PHANTOM COMMANDS (documented but not implemented)")
            lines.append("-" * 50)
            for phantom in report.phantom_commands:
                lines.append(f"  {phantom.command_name}")
                lines.append(f"    Documented in: {phantom.documented_in}")
                if phantom.description:
                    lines.append(f"    Description: {phantom.description}")
            lines.append("")

        if report.missing_commands:
            lines.append("⚠️  MISSING COMMANDS (implemented but not documented)")
            lines.append("-" * 50)
            for missing in report.missing_commands:
                lines.append(f"  {missing.command_name}")
                lines.append(f"    Implemented in: {missing.implemented_in}")
                if missing.help_text:
                    lines.append(f"    Help: {missing.help_text[:100]}...")
            lines.append("")

        if report.mismatched_descriptions:
            lines.append("🔄 MISMATCHED DESCRIPTIONS")
            lines.append("-" * 50)
            for mismatch in report.mismatched_descriptions:
                lines.append(f"  {mismatch.command_name}: {mismatch.option_name}")
                lines.append(f"    Implementation: {mismatch.implementation_description[:60]}...")
                lines.append(f"    Documentation: {mismatch.documentation_description[:60]}...")
            lines.append("")

        # Recommendations
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 30)

        if report.phantom_options or report.phantom_commands:
            lines.append("🚨 CRITICAL: Remove phantom options/commands from documentation")
            lines.append("   These confuse users and break their workflows.")

        if report.missing_options or report.missing_commands:
            lines.append("📝 Add missing documentation for implemented features")

        if report.mismatched_descriptions:
            lines.append("🔄 Sync descriptions between code and documentation")

        lines.append("")
        lines.append("💡 Run this verification regularly to prevent documentation drift!")

        return "\n".join(lines)

    def _generate_markdown_report(self, report: VerificationReport) -> str:
        """Generate markdown report."""
        lines = []
        lines.append("# 🔍 CLI Documentation Verification Report")
        lines.append("")
        lines.append(f"**Project**: `{self.project_root}`")
        lines.append(f"**Generated**: {__import__('datetime').datetime.now().isoformat()}")
        lines.append("")

        # Summary
        lines.append("## 📊 Summary")
        lines.append("")
        lines.append(f"- **Commands implemented**: {report.total_implemented_commands}")
        lines.append(f"- **Commands documented**: {report.total_documented_commands}")
        lines.append(f"- **Options implemented**: {report.total_implemented_options}")
        lines.append(f"- **Options documented**: {report.total_documented_options}")
        lines.append("")
        lines.append(f"- **Total issues found**: {report.total_issues_count}")
        lines.append(f"- **Critical issues**: {report.critical_issues_count}")
        lines.append("")

        if not report.has_issues:
            lines.append("## ✅ Perfect Match!")
            lines.append("")
            lines.append("Documentation perfectly matches implementation. No issues found!")
            return "\n".join(lines)

        # Issues sections
        if report.phantom_options:
            lines.append("## ❌ Phantom Options")
            lines.append("")
            lines.append("Options documented but **not implemented** (confuses users):")
            lines.append("")
            for phantom in report.phantom_options:
                lines.append(f"- **`{phantom.command_name}`**: `{phantom.option_name}`")
                lines.append(f"  - Source: `{phantom.documented_in}`")
            lines.append("")

        if report.missing_options:
            lines.append("## ⚠️ Missing Documentation")
            lines.append("")
            lines.append("Options implemented but **not documented**:")
            lines.append("")
            for missing in report.missing_options:
                lines.append(f"- **`{missing.command_name}`**: `{missing.option_name}`")
                lines.append(f"  - Source: `{missing.implemented_in}`")
                if missing.help_text:
                    lines.append(f"  - Help: {missing.help_text}")
            lines.append("")

        if report.phantom_commands:
            lines.append("## ❌ Phantom Commands")
            lines.append("")
            lines.append("Commands documented but **not implemented**:")
            lines.append("")
            for phantom in report.phantom_commands:
                lines.append(f"- **`{phantom.command_name}`**")
                lines.append(f"  - Source: `{phantom.documented_in}`")
                if phantom.description:
                    lines.append(f"  - Description: {phantom.description}")
            lines.append("")

        if report.missing_commands:
            lines.append("## ⚠️ Missing Command Documentation")
            lines.append("")
            lines.append("Commands implemented but **not documented**:")
            lines.append("")
            for missing in report.missing_commands:
                lines.append(f"- **`{missing.command_name}`**")
                lines.append(f"  - Source: `{missing.implemented_in}`")
                if missing.help_text:
                    lines.append(f"  - Help: {missing.help_text[:100]}...")
            lines.append("")

        # Action items
        lines.append("## 🎯 Action Items")
        lines.append("")

        priority = 1
        if report.phantom_options:
            lines.append(f"{priority}. **Remove phantom options** from documentation")
            priority += 1

        if report.phantom_commands:
            lines.append(f"{priority}. **Remove phantom commands** from documentation")
            priority += 1

        if report.missing_options:
            lines.append(f"{priority}. **Add missing option documentation**")
            priority += 1

        if report.missing_commands:
            lines.append(f"{priority}. **Add missing command documentation**")
            priority += 1

        lines.append("")
        lines.append("## 🛡️ Prevention")
        lines.append("")
        lines.append("- Run this verification in CI/CD pipeline")
        lines.append("- Add pre-commit hooks for documentation checks")
        lines.append("- Review CLI changes with documentation updates")

        return "\n".join(lines)

    def _generate_json_report(self, report: VerificationReport) -> str:
        """Generate JSON report."""
        data = {
            "metadata": {
                "project_root": str(self.project_root),
                "timestamp": __import__("datetime").datetime.now().isoformat(),
                "total_issues": report.total_issues_count,
                "critical_issues": report.critical_issues_count,
            },
            "summary": {
                "commands_implemented": report.total_implemented_commands,
                "commands_documented": report.total_documented_commands,
                "options_implemented": report.total_implemented_options,
                "options_documented": report.total_documented_options,
                "has_issues": report.has_issues,
            },
            "issues": {
                "phantom_options": [
                    {
                        "command": p.command_name,
                        "option": p.option_name,
                        "documented_in": p.documented_in,
                        "line_number": p.line_number,
                    }
                    for p in report.phantom_options
                ],
                "missing_options": [
                    {
                        "command": m.command_name,
                        "option": m.option_name,
                        "implemented_in": m.implemented_in,
                        "help_text": m.help_text,
                    }
                    for m in report.missing_options
                ],
                "phantom_commands": [
                    {"command": p.command_name, "documented_in": p.documented_in, "description": p.description}
                    for p in report.phantom_commands
                ],
                "missing_commands": [
                    {
                        "command": m.command_name,
                        "implemented_in": m.implemented_in,
                        "function_name": m.function_name,
                        "help_text": m.help_text,
                    }
                    for m in report.missing_commands
                ],
            },
        }

        return json.dumps(data, indent=2)


def main():
    """Main function for CLI documentation verifier."""
    parser = argparse.ArgumentParser(description="Verify rxiv-maker CLI documentation matches implementation")
    parser.add_argument(
        "project_path", nargs="?", default=".", help="Path to rxiv-maker project (default: current directory)"
    )
    parser.add_argument(
        "--format", choices=["text", "markdown", "json"], default="text", help="Output format (default: text)"
    )
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--fix", action="store_true", help="Generate fixes for documentation issues (future feature)")

    args = parser.parse_args()

    project_root = Path(args.project_path).resolve()
    if not project_root.exists():
        print(f"Error: Project path does not exist: {project_root}")
        sys.exit(1)

    verifier = CLIDocumentationVerifier(project_root)
    report = verifier.verify()

    output_text = verifier.generate_report(report, args.format)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"Report written to {args.output}")
    else:
        print(output_text)

    # Exit with error code if critical issues found
    if report.critical_issues_count > 0:
        sys.exit(2)  # Critical issues
    elif report.has_issues:
        sys.exit(1)  # Non-critical issues
    else:
        sys.exit(0)  # No issues


if __name__ == "__main__":
    main()
