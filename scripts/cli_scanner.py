#!/usr/bin/env python3
"""
CLI Scanner for rxiv-maker

Extracts actual CLI commands, options, and arguments from implementation files
"""

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ClickOption:
    """Represents a Click option decorator."""

    name: str
    short_name: Optional[str] = None
    help_text: Optional[str] = None
    default: Optional[Any] = None
    is_flag: bool = False
    option_type: Optional[str] = None
    choices: Optional[List[str]] = None
    required: bool = False


@dataclass
class ClickArgument:
    """Represents a Click argument decorator."""

    name: str
    help_text: Optional[str] = None
    required: bool = True
    option_type: Optional[str] = None


@dataclass
class ClickCommand:
    """Represents a Click command with its options and arguments."""

    name: str
    function_name: str
    help_text: Optional[str] = None
    options: List[ClickOption] = None
    arguments: List[ClickArgument] = None
    file_path: str = ""
    line_number: int = 0

    def __post_init__(self):
        if self.options is None:
            self.options = []
        if self.arguments is None:
            self.arguments = []


class ClickASTParser:
    """Parses Python AST to extract Click decorators."""

    def __init__(self):
        self.commands = {}

    def parse_file(self, file_path: Path) -> Dict[str, ClickCommand]:
        """Parse a Python file and extract Click commands."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            return self._extract_commands(tree, str(file_path))

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return {}

    def _extract_commands(self, tree: ast.AST, file_path: str) -> Dict[str, ClickCommand]:
        """Extract commands from AST tree."""
        commands = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                command = self._parse_function_decorators(node, file_path)
                if command:
                    commands[command.name] = command

        return commands

    def _parse_function_decorators(self, func_node: ast.FunctionDef, file_path: str) -> Optional[ClickCommand]:
        """Parse decorators of a function to extract Click command info."""
        command = None
        options = []
        arguments = []

        for decorator in func_node.decorator_list:
            if self._is_click_command(decorator):
                command = ClickCommand(
                    name=self._extract_command_name(decorator, func_node.name),
                    function_name=func_node.name,
                    help_text=self._extract_docstring(func_node),
                    file_path=file_path,
                    line_number=func_node.lineno,
                )
            elif self._is_click_option(decorator):
                option = self._parse_option_decorator(decorator)
                if option:
                    options.append(option)
            elif self._is_click_argument(decorator):
                argument = self._parse_argument_decorator(decorator)
                if argument:
                    arguments.append(argument)

        if command:
            command.options = options
            command.arguments = arguments
            return command

        return None

    def _is_click_command(self, decorator: ast.expr) -> bool:
        """Check if decorator is a click.command or click.group."""
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                return (
                    decorator.func.attr in ["command", "group"]
                    and isinstance(decorator.func.value, ast.Name)
                    and decorator.func.value.id == "click"
                )
        elif isinstance(decorator, ast.Attribute):
            return (
                decorator.attr in ["command", "group"]
                and isinstance(decorator.value, ast.Name)
                and decorator.value.id == "click"
            )
        return False

    def _is_click_option(self, decorator: ast.expr) -> bool:
        """Check if decorator is a click.option."""
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                return (
                    decorator.func.attr == "option"
                    and isinstance(decorator.func.value, ast.Name)
                    and decorator.func.value.id == "click"
                )
        return False

    def _is_click_argument(self, decorator: ast.expr) -> bool:
        """Check if decorator is a click.argument."""
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                return (
                    decorator.func.attr == "argument"
                    and isinstance(decorator.func.value, ast.Name)
                    and decorator.func.value.id == "click"
                )
        return False

    def _extract_command_name(self, decorator: ast.expr, func_name: str) -> str:
        """Extract command name from decorator or use function name."""
        # For now, use function name - can be enhanced to parse command name from decorator
        return func_name.replace("_", "-")

    def _extract_docstring(self, func_node: ast.FunctionDef) -> Optional[str]:
        """Extract docstring from function."""
        if (
            func_node.body
            and isinstance(func_node.body[0], ast.Expr)
            and isinstance(func_node.body[0].value, ast.Constant)
            and isinstance(func_node.body[0].value.value, str)
        ):
            return func_node.body[0].value.value
        return None

    def _parse_option_decorator(self, decorator: ast.Call) -> Optional[ClickOption]:
        """Parse click.option decorator."""
        if not decorator.args:
            return None

        # First argument is the option name
        option_name = None
        short_name = None

        if decorator.args:
            first_arg = decorator.args[0]
            if isinstance(first_arg, ast.Constant):
                option_name = first_arg.value

        # Check for short name in second argument
        if len(decorator.args) > 1:
            second_arg = decorator.args[1]
            if isinstance(second_arg, ast.Constant):
                short_name = second_arg.value

        if not option_name:
            return None

        # Parse keyword arguments
        help_text = None
        default = None
        is_flag = False
        option_type = None
        choices = None
        required = False

        for keyword in decorator.keywords:
            if keyword.arg == "help":
                if isinstance(keyword.value, ast.Constant):
                    help_text = keyword.value.value
            elif keyword.arg == "default":
                if isinstance(keyword.value, ast.Constant):
                    default = keyword.value.value
            elif keyword.arg == "is_flag":
                if isinstance(keyword.value, ast.Constant):
                    is_flag = keyword.value.value
            elif keyword.arg == "type":
                option_type = self._extract_type_info(keyword.value)
            elif keyword.arg == "required":
                if isinstance(keyword.value, ast.Constant):
                    required = keyword.value.value

        return ClickOption(
            name=option_name,
            short_name=short_name,
            help_text=help_text,
            default=default,
            is_flag=is_flag,
            option_type=option_type,
            choices=choices,
            required=required,
        )

    def _parse_argument_decorator(self, decorator: ast.Call) -> Optional[ClickArgument]:
        """Parse click.argument decorator."""
        if not decorator.args:
            return None

        # First argument is the argument name
        argument_name = None
        if isinstance(decorator.args[0], ast.Constant):
            argument_name = decorator.args[0].value

        if not argument_name:
            return None

        # Parse keyword arguments
        help_text = None
        required = True
        option_type = None

        for keyword in decorator.keywords:
            if keyword.arg == "help":
                if isinstance(keyword.value, ast.Constant):
                    help_text = keyword.value.value
            elif keyword.arg == "required":
                if isinstance(keyword.value, ast.Constant):
                    required = keyword.value.value
            elif keyword.arg == "type":
                option_type = self._extract_type_info(keyword.value)

        return ClickArgument(name=argument_name, help_text=help_text, required=required, option_type=option_type)

    def _extract_type_info(self, type_node: ast.expr) -> Optional[str]:
        """Extract type information from AST node."""
        if isinstance(type_node, ast.Call):
            if isinstance(type_node.func, ast.Attribute):
                if (
                    type_node.func.attr == "Choice"
                    and isinstance(type_node.func.value, ast.Name)
                    and type_node.func.value.id == "click"
                ):
                    # This is click.Choice
                    return "Choice"
            elif isinstance(type_node.func, ast.Attribute):
                if (
                    type_node.func.attr == "Path"
                    and isinstance(type_node.func.value, ast.Name)
                    and type_node.func.value.id == "click"
                ):
                    return "Path"
        return None


class CLIScanner:
    """Main CLI scanner that discovers and analyzes CLI commands."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.parser = ClickASTParser()
        self.commands = {}

    def scan_cli_files(self) -> Dict[str, ClickCommand]:
        """Scan all CLI files in the project."""
        cli_dirs = [
            self.project_root / "src" / "rxiv_maker" / "cli" / "commands",
            self.project_root / "rxiv_maker" / "cli" / "commands",  # Alternative structure
        ]

        # Also scan the parent CLI directory for commands like config.py
        parent_cli_dirs = [
            self.project_root / "src" / "rxiv_maker" / "cli",
            self.project_root / "rxiv_maker" / "cli",
        ]

        for cli_dir in cli_dirs:
            if cli_dir.exists():
                self._scan_directory(cli_dir)

        for cli_dir in parent_cli_dirs:
            if cli_dir.exists():
                self._scan_directory(cli_dir, include_subdirs=False)

        # Check for command aliases in __init__.py
        self._check_command_aliases()

        return self.commands

    def _scan_directory(self, directory: Path, include_subdirs: bool = True):
        """Scan a directory for Python CLI files."""
        pattern = "**/*.py" if include_subdirs else "*.py"
        for file_path in directory.glob(pattern):
            if file_path.name.startswith("__"):
                continue
            # Skip main.py and framework.py as they don't contain individual commands
            if file_path.name in ["main.py", "framework.py"]:
                continue

            file_commands = self.parser.parse_file(file_path)
            self.commands.update(file_commands)

    def _check_command_aliases(self):
        """Check for command aliases in commands/__init__.py and main.py."""
        # Check commands/__init__.py for aliases like: from .build import build as pdf
        init_files = [
            self.project_root / "src" / "rxiv_maker" / "cli" / "commands" / "__init__.py",
            self.project_root / "rxiv_maker" / "cli" / "commands" / "__init__.py",
        ]

        for init_file in init_files:
            if init_file.exists():
                try:
                    with open(init_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Look for aliases like: from .build import build as pdf
                    import re

                    alias_pattern = re.compile(r"from\s+\.(\w+)\s+import\s+(\w+)\s+as\s+(\w+)")

                    for match in alias_pattern.findall(content):
                        module_name, original_func, alias_name = match

                        # Find the original command
                        original_cmd = None
                        for _cmd_name, cmd in self.commands.items():
                            if cmd.function_name == original_func:
                                original_cmd = cmd
                                break

                        if original_cmd:
                            # Create alias command
                            alias_cmd = ClickCommand(
                                name=alias_name,
                                function_name=original_func,
                                help_text=original_cmd.help_text,
                                options=original_cmd.options.copy(),
                                arguments=original_cmd.arguments.copy(),
                                file_path=original_cmd.file_path,
                                line_number=original_cmd.line_number,
                            )
                            self.commands[alias_name] = alias_cmd

                except Exception as e:
                    print(f"Warning: Could not parse {init_file} for aliases: {e}")
                break  # Only process the first found init file

        # Also check main.py for command registrations like: main.add_command(config_cmd, name="config")
        main_files = [
            self.project_root / "src" / "rxiv_maker" / "cli" / "main.py",
            self.project_root / "rxiv_maker" / "cli" / "main.py",
        ]

        for main_file in main_files:
            if main_file.exists():
                try:
                    with open(main_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Look for registrations like: main.add_command(config_cmd, name="config")
                    import re

                    registration_pattern = re.compile(r'main\.add_command\(([^,]+),\s*name="([^"]+)"\)')

                    for match in registration_pattern.findall(content):
                        func_ref, alias_name = match

                        # Handle imports from other modules
                        # Find the matching command by function reference
                        for _cmd_name, cmd in self.commands.items():
                            if cmd.function_name == func_ref:
                                alias_cmd = ClickCommand(
                                    name=alias_name,
                                    function_name=cmd.function_name,
                                    help_text=cmd.help_text,
                                    options=cmd.options.copy(),
                                    arguments=cmd.arguments.copy(),
                                    file_path=cmd.file_path,
                                    line_number=cmd.line_number,
                                )
                                self.commands[alias_name] = alias_cmd
                                # Also remove the original command with transformed name if it exists
                                transformed_name = func_ref.replace("_", "-")
                                if transformed_name in self.commands and transformed_name != alias_name:
                                    del self.commands[transformed_name]
                                break

                except Exception as e:
                    print(f"Warning: Could not parse {main_file} for registrations: {e}")
                break  # Only process the first found main file

    def generate_report(self, output_format: str = "json") -> str:
        """Generate a report of discovered commands."""
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
                "function_name": command.function_name,
                "help_text": command.help_text,
                "file_path": command.file_path,
                "line_number": command.line_number,
                "options": [
                    {
                        "name": opt.name,
                        "short_name": opt.short_name,
                        "help_text": opt.help_text,
                        "default": opt.default,
                        "is_flag": opt.is_flag,
                        "type": opt.option_type,
                        "required": opt.required,
                    }
                    for opt in command.options
                ],
                "arguments": [
                    {"name": arg.name, "help_text": arg.help_text, "required": arg.required, "type": arg.option_type}
                    for arg in command.arguments
                ],
            }

        return json.dumps(data, indent=2)

    def _generate_markdown_report(self) -> str:
        """Generate Markdown report."""
        report = ["# CLI Scanner Report", ""]
        report.append(f"**Project Root**: `{self.project_root}`")
        report.append(f"**Commands Found**: {len(self.commands)}")
        report.append("")

        for cmd_name, command in sorted(self.commands.items()):
            report.append(f"## `{cmd_name}` Command")
            report.append("")
            report.append(f"**File**: `{command.file_path}:{command.line_number}`")
            report.append(f"**Function**: `{command.function_name}`")

            if command.help_text:
                report.append(f"**Description**: {command.help_text.split('.')[0]}")

            report.append("")

            if command.options:
                report.append("### Options")
                report.append("")
                for opt in command.options:
                    option_line = f"- `{opt.name}`"
                    if opt.short_name:
                        option_line += f", `{opt.short_name}`"
                    if opt.help_text:
                        option_line += f" - {opt.help_text}"
                    if opt.is_flag:
                        option_line += " (flag)"
                    if opt.default is not None:
                        option_line += f" (default: `{opt.default}`)"
                    report.append(option_line)
                report.append("")

            if command.arguments:
                report.append("### Arguments")
                report.append("")
                for arg in command.arguments:
                    arg_line = f"- `{arg.name}`"
                    if arg.help_text:
                        arg_line += f" - {arg.help_text}"
                    if not arg.required:
                        arg_line += " (optional)"
                    report.append(arg_line)
                report.append("")

        return "\n".join(report)

    def _generate_text_report(self) -> str:
        """Generate plain text report."""
        lines = []
        lines.append("CLI SCANNER REPORT")
        lines.append("=" * 50)
        lines.append(f"Project: {self.project_root}")
        lines.append(f"Commands found: {len(self.commands)}")
        lines.append("")

        for cmd_name, command in sorted(self.commands.items()):
            lines.append(f"Command: {cmd_name}")
            lines.append(f"  File: {command.file_path}:{command.line_number}")
            lines.append(f"  Function: {command.function_name}")

            if command.options:
                lines.append("  Options:")
                for opt in command.options:
                    opt_info = f"    {opt.name}"
                    if opt.short_name:
                        opt_info += f" ({opt.short_name})"
                    if opt.help_text:
                        opt_info += f": {opt.help_text}"
                    lines.append(opt_info)

            if command.arguments:
                lines.append("  Arguments:")
                for arg in command.arguments:
                    arg_info = f"    {arg.name}"
                    if arg.help_text:
                        arg_info += f": {arg.help_text}"
                    lines.append(arg_info)

            lines.append("")

        return "\n".join(lines)


def main():
    """Main function for CLI scanner."""
    parser = argparse.ArgumentParser(description="Scan rxiv-maker CLI implementation")
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

    scanner = CLIScanner(project_root)
    commands = scanner.scan_cli_files()

    if not commands:
        print("No CLI commands found in project")
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
