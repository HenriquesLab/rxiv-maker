#!/usr/bin/env python3
"""
Documentation Parser for rxiv-maker CLI

Extracts CLI commands, options, and arguments from documentation files
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class DocumentedOption:
    """Represents a CLI option documented in markdown."""

    name: str
    short_name: Optional[str] = None
    description: Optional[str] = None
    default: Optional[str] = None
    is_flag: bool = False
    source_file: str = ""
    line_number: int = 0


@dataclass
class DocumentedArgument:
    """Represents a CLI argument documented in markdown."""

    name: str
    description: Optional[str] = None
    required: bool = True
    source_file: str = ""
    line_number: int = 0


@dataclass
class DocumentedCommand:
    """Represents a CLI command documented in markdown."""

    name: str
    description: Optional[str] = None
    options: List[DocumentedOption] = None
    arguments: List[DocumentedArgument] = None
    source_file: str = ""
    examples: List[str] = None

    def __post_init__(self):
        if self.options is None:
            self.options = []
        if self.arguments is None:
            self.arguments = []
        if self.examples is None:
            self.examples = []


class MarkdownCLIParser:
    """Parses markdown documentation to extract CLI command information."""

    def __init__(self):
        self.commands = {}

        # Regular expressions for parsing
        self.command_header_pattern = re.compile(
            r"^#{1,4}\s*`rxiv\s+(\w+(?:-\w+)*)`\s*-\s*(.+)$", re.IGNORECASE | re.MULTILINE
        )
        self.option_patterns = [
            # Pattern for options like: - `--option`, `-o` - Description (default: value)
            re.compile(
                r"^\s*-\s*`([^`]+)`(?:,\s*`([^`]+)`)?\s*-\s*([^(]+)(?:\(default:\s*`?([^`)]+)`?\))?", re.MULTILINE
            ),
            # Pattern for options like: --option <value> - Description
            re.compile(r"^\s*([--]\w+(?:-\w+)*)\s*(?:<(\w+)>)?\s*-\s*(.+)$", re.MULTILINE),
            # Pattern for options in code blocks
            re.compile(r"^\s*([--]\w+(?:-\w+)*)\s*(?:\|\s*([--]\w+(?:-\w+)*))?\s*(.*)$", re.MULTILINE),
        ]
        self.argument_pattern = re.compile(r"^\s*-\s*`([^`]+)`\s*-\s*(.+?)(?:\s*\(optional\))?$", re.MULTILINE)
        self.example_pattern = re.compile(r"```(?:bash|shell)?\n(.*?)```", re.DOTALL)

    def parse_file(self, file_path: Path) -> Dict[str, DocumentedCommand]:
        """Parse a markdown file and extract CLI documentation."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return self._extract_commands_from_content(content, str(file_path))

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return {}

    def _extract_commands_from_content(self, content: str, file_path: str) -> Dict[str, DocumentedCommand]:
        """Extract commands from markdown content."""
        commands = {}

        # Find all command sections
        command_matches = self.command_header_pattern.findall(content)

        for match in command_matches:
            command_name = match[0].replace("_", "-")
            command_description = match[1].strip() if match[1] else None

            # Extract the section content for this command
            section_content = self._extract_command_section(content, command_name)
            if section_content:
                command = self._parse_command_section(section_content, command_name, command_description, file_path)
                if command:
                    commands[command_name] = command
            else:
                # Create basic command even if section extraction fails
                command = DocumentedCommand(name=command_name, description=command_description, source_file=file_path)
                commands[command_name] = command

        return commands

    def _extract_command_section(self, content: str, command_name: str) -> Optional[str]:
        """Extract the content section for a specific command."""
        # Find the start of this command section
        command_pattern = re.compile(
            rf"^#{1, 4}\s*`rxiv\s+{re.escape(command_name)}`\s*-.*?$", re.IGNORECASE | re.MULTILINE
        )
        match = command_pattern.search(content)

        if not match:
            return None

        start_pos = match.start()

        # Find the next command section (either another rxiv command or a major section)
        next_section_patterns = [
            re.compile(r"^#{1,4}\s*`rxiv\s+\w+", re.IGNORECASE | re.MULTILINE),  # Next rxiv command
            re.compile(r"^#{1,2}\s*[^`]", re.MULTILINE),  # Major section header
        ]

        end_pos = len(content)
        for pattern in next_section_patterns:
            next_matches = list(pattern.finditer(content, start_pos + 1))
            if next_matches:
                end_pos = min(end_pos, next_matches[0].start())

        return content[start_pos:end_pos]

    def _parse_command_section(
        self, section_content: str, command_name: str, command_description: str, file_path: str
    ) -> Optional[DocumentedCommand]:
        """Parse a command section to extract options, arguments, and examples."""
        command = DocumentedCommand(name=command_name, description=command_description, source_file=file_path)

        # Extract options
        command.options = self._extract_options(section_content, file_path)

        # Extract arguments
        command.arguments = self._extract_arguments(section_content, file_path)

        # Extract examples
        command.examples = self._extract_examples(section_content)

        return command

    def _extract_options(self, content: str, file_path: str) -> List[DocumentedOption]:
        """Extract options from command section content."""
        options = []

        # Look for options sections
        options_section_pattern = re.compile(
            r"(?:^#{1,6}\s*Options?\s*$|^\*\*Options?\*\*:?\s*$)", re.IGNORECASE | re.MULTILINE
        )
        options_match = options_section_pattern.search(content)

        if not options_match:
            return options

        # Extract content after "Options" header until next header
        start_pos = options_match.end()
        next_header_pattern = re.compile(r"^#{1,6}\s|\*\*[^*]+\*\*:", re.MULTILINE)
        next_header_match = next_header_pattern.search(content, start_pos)

        options_content = content[start_pos : next_header_match.start()] if next_header_match else content[start_pos:]

        # Parse options using different patterns
        for pattern in self.option_patterns:
            matches = pattern.findall(options_content)
            for match in matches:
                option = self._parse_option_match(match, file_path)
                if option:
                    options.append(option)

        return options

    def _parse_option_match(self, match: tuple, file_path: str) -> Optional[DocumentedOption]:
        """Parse a regex match to create a DocumentedOption."""
        if len(match) >= 3:
            name = match[0].strip()
            short_name = match[1].strip() if len(match) > 1 and match[1] else None
            description = match[2].strip() if len(match) > 2 else None
            default = match[3].strip() if len(match) > 3 and match[3] else None

            # Clean up the name
            if not name.startswith("-"):
                name = f"--{name}"

            # Determine if it's a flag
            is_flag = "flag" in description.lower() if description else False

            return DocumentedOption(
                name=name,
                short_name=short_name if short_name and short_name.startswith("-") else None,
                description=description,
                default=default,
                is_flag=is_flag,
                source_file=file_path,
            )

        return None

    def _extract_arguments(self, content: str, file_path: str) -> List[DocumentedArgument]:
        """Extract arguments from command section content."""
        arguments = []

        # Look for arguments sections
        args_section_pattern = re.compile(
            r"(?:^#{1,6}\s*Arguments?\s*$|^\*\*Arguments?\*\*:?\s*$)", re.IGNORECASE | re.MULTILINE
        )
        args_match = args_section_pattern.search(content)

        if not args_match:
            # Also look for argument patterns in the main content
            arg_matches = self.argument_pattern.findall(content)
            for match in arg_matches:
                arg_name = match[0].strip()
                arg_description = match[1].strip()
                required = "(optional)" not in content

                arguments.append(
                    DocumentedArgument(
                        name=arg_name, description=arg_description, required=required, source_file=file_path
                    )
                )

            return arguments

        # Extract content after "Arguments" header
        start_pos = args_match.end()
        next_header_pattern = re.compile(r"^#{1,6}\s|\*\*[^*]+\*\*:", re.MULTILINE)
        next_header_match = next_header_pattern.search(content, start_pos)

        args_content = content[start_pos : next_header_match.start()] if next_header_match else content[start_pos:]

        # Parse arguments
        arg_matches = self.argument_pattern.findall(args_content)
        for match in arg_matches:
            arg_name = match[0].strip()
            arg_description = match[1].strip()
            required = "(optional)" not in args_content

            arguments.append(
                DocumentedArgument(name=arg_name, description=arg_description, required=required, source_file=file_path)
            )

        return arguments

    def _extract_examples(self, content: str) -> List[str]:
        """Extract code examples from command section content."""
        examples = []

        example_matches = self.example_pattern.findall(content)
        for match in example_matches:
            # Filter for lines that contain rxiv commands
            lines = match.strip().split("\n")
            rxiv_lines = [line.strip() for line in lines if "rxiv" in line and not line.strip().startswith("#")]
            examples.extend(rxiv_lines)

        return examples


class DocumentationScanner:
    """Main documentation scanner that finds and analyzes CLI documentation."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.parser = MarkdownCLIParser()
        self.commands = {}

    def scan_documentation_files(self) -> Dict[str, DocumentedCommand]:
        """Scan all documentation files in the project."""
        doc_dirs = [
            self.project_root / "docs",
            self.project_root / "README.md",
        ]

        # Scan directories
        for doc_path in doc_dirs:
            if doc_path.is_dir():
                self._scan_directory(doc_path)
            elif doc_path.is_file():
                self._scan_file(doc_path)

        return self.commands

    def _scan_directory(self, directory: Path):
        """Recursively scan a directory for markdown files."""
        for file_path in directory.rglob("*.md"):
            self._scan_file(file_path)

    def _scan_file(self, file_path: Path):
        """Scan a single markdown file for CLI documentation."""
        file_commands = self.parser.parse_file(file_path)

        # Merge commands, prioritizing more detailed descriptions
        for cmd_name, command in file_commands.items():
            if cmd_name in self.commands:
                # Merge information from multiple sources
                existing = self.commands[cmd_name]
                if len(command.options) > len(existing.options):
                    existing.options = command.options
                if len(command.arguments) > len(existing.arguments):
                    existing.arguments = command.arguments
                if command.examples:
                    existing.examples.extend(command.examples)
            else:
                self.commands[cmd_name] = command

    def generate_report(self, output_format: str = "json") -> str:
        """Generate a report of documented commands."""
        if output_format == "json":
            return self._generate_json_report()
        elif output_format == "markdown":
            return self._generate_markdown_report()
        else:
            return self._generate_text_report()

    def _generate_json_report(self) -> str:
        """Generate JSON report."""
        data = {
            "scan_info": {
                "project_root": str(self.project_root),
                "total_commands": len(self.commands),
                "scan_timestamp": __import__("datetime").datetime.now().isoformat(),
            },
            "commands": {},
        }

        for cmd_name, command in self.commands.items():
            data["commands"][cmd_name] = {
                "name": command.name,
                "description": command.description,
                "source_file": command.source_file,
                "options": [
                    {
                        "name": opt.name,
                        "short_name": opt.short_name,
                        "description": opt.description,
                        "default": opt.default,
                        "is_flag": opt.is_flag,
                    }
                    for opt in command.options
                ],
                "arguments": [
                    {"name": arg.name, "description": arg.description, "required": arg.required}
                    for arg in command.arguments
                ],
                "examples": command.examples,
            }

        return json.dumps(data, indent=2)

    def _generate_markdown_report(self) -> str:
        """Generate Markdown report."""
        report = ["# Documentation Scanner Report", ""]
        report.append(f"**Project Root**: `{self.project_root}`")
        report.append(f"**Commands Documented**: {len(self.commands)}")
        report.append("")

        for cmd_name, command in sorted(self.commands.items()):
            report.append(f"## `{cmd_name}` Command (Documented)")
            report.append("")
            report.append(f"**Source**: `{command.source_file}`")

            if command.description:
                report.append(f"**Description**: {command.description}")

            report.append("")

            if command.options:
                report.append("### Documented Options")
                report.append("")
                for opt in command.options:
                    option_line = f"- `{opt.name}`"
                    if opt.short_name:
                        option_line += f", `{opt.short_name}`"
                    if opt.description:
                        option_line += f" - {opt.description}"
                    if opt.is_flag:
                        option_line += " (flag)"
                    if opt.default:
                        option_line += f" (default: `{opt.default}`)"
                    report.append(option_line)
                report.append("")

            if command.arguments:
                report.append("### Documented Arguments")
                report.append("")
                for arg in command.arguments:
                    arg_line = f"- `{arg.name}`"
                    if arg.description:
                        arg_line += f" - {arg.description}"
                    if not arg.required:
                        arg_line += " (optional)"
                    report.append(arg_line)
                report.append("")

            if command.examples:
                report.append("### Examples")
                report.append("")
                for example in command.examples[:3]:  # Show first 3 examples
                    report.append(f"- `{example}`")
                report.append("")

        return "\n".join(report)

    def _generate_text_report(self) -> str:
        """Generate plain text report."""
        lines = []
        lines.append("DOCUMENTATION SCANNER REPORT")
        lines.append("=" * 50)
        lines.append(f"Project: {self.project_root}")
        lines.append(f"Commands documented: {len(self.commands)}")
        lines.append("")

        for cmd_name, command in sorted(self.commands.items()):
            lines.append(f"Command: {cmd_name}")
            lines.append(f"  Source: {command.source_file}")

            if command.options:
                lines.append("  Documented Options:")
                for opt in command.options:
                    opt_info = f"    {opt.name}"
                    if opt.short_name:
                        opt_info += f" ({opt.short_name})"
                    if opt.description:
                        opt_info += f": {opt.description}"
                    lines.append(opt_info)

            if command.arguments:
                lines.append("  Documented Arguments:")
                for arg in command.arguments:
                    arg_info = f"    {arg.name}"
                    if arg.description:
                        arg_info += f": {arg.description}"
                    lines.append(arg_info)

            lines.append("")

        return "\n".join(lines)


def main():
    """Main function for documentation scanner."""
    parser = argparse.ArgumentParser(description="Scan rxiv-maker CLI documentation")
    parser.add_argument(
        "project_path", nargs="?", default=".", help="Path to rxiv-maker project (default: current directory)"
    )
    parser.add_argument(
        "--format", choices=["json", "markdown", "text"], default="text", help="Output format (default: text)"
    )
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")

    args = parser.parse_args()

    project_root = Path(args.project_path).resolve()
    if not project_root.exists():
        print(f"Error: Project path does not exist: {project_root}")
        sys.exit(1)

    scanner = DocumentationScanner(project_root)
    commands = scanner.scan_documentation_files()

    if not commands:
        print("No CLI documentation found in project")
        sys.exit(1)

    report = scanner.generate_report(args.format)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
