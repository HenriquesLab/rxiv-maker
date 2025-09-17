"""Python execution reporting utility for rxiv-maker.

This module provides centralized reporting of Python code execution during manuscript
build process, including code blocks executed, outputs generated, and any errors encountered.
"""

from typing import Any, Dict, List, Optional


class PythonExecutionEntry:
    """Represents a single Python execution event."""

    def __init__(
        self,
        entry_type: str,
        line_number: int,
        execution_time: float,
        file_path: str = "manuscript",
        output: str = "",
        error_message: str = "",
    ):
        """Initialize execution entry."""
        self.entry_type = entry_type
        self.line_number = line_number
        self.execution_time = execution_time
        self.file_path = file_path
        self.output = output
        self.error_message = error_message


class PythonExecutionReporter:
    """Centralized reporting system for Python execution events during manuscript build."""

    def __init__(self):
        """Initialize the reporter."""
        self.entries: List[PythonExecutionEntry] = []
        self.total_execution_time = 0.0

    def reset(self) -> None:
        """Reset the reporter for a new build."""
        self.entries.clear()
        self.total_execution_time = 0.0

    def track_exec_block(
        self, code: str, output: str, line_number: int, file_path: str = "manuscript", execution_time: float = 0.0
    ) -> None:
        """Track execution of a Python code block."""
        entry = PythonExecutionEntry(
            entry_type="exec",
            line_number=line_number,
            execution_time=execution_time,
            file_path=file_path,
            output=output,
        )
        self.entries.append(entry)
        self.total_execution_time += execution_time

    def track_inline_execution(
        self, code: str, output: str, line_number: int, file_path: str = "manuscript", execution_time: float = 0.0
    ) -> None:
        """Track execution of inline Python code (for variable substitution)."""
        entry = PythonExecutionEntry(
            entry_type="inline",
            line_number=line_number,
            execution_time=execution_time,
            file_path=file_path,
            output=output,
        )
        self.entries.append(entry)
        self.total_execution_time += execution_time

    def track_get_variable(
        self, variable_name: str, variable_value: str, line_number: int, file_path: str = "manuscript"
    ) -> None:
        """Track variable access during manuscript processing."""
        entry = PythonExecutionEntry(
            entry_type="get",
            line_number=line_number,
            execution_time=0.0,  # Variable access is immediate
            file_path=file_path,
            output=str(variable_value),
        )
        self.entries.append(entry)

    def track_error(
        self, error_message: str, code_snippet: str, line_number: int, file_path: str = "manuscript"
    ) -> None:
        """Track execution errors during manuscript processing."""
        entry = PythonExecutionEntry(
            entry_type="error",
            line_number=line_number,
            execution_time=0.0,  # Error tracking is immediate
            file_path=file_path,
            output="",
            error_message=error_message,
        )
        self.entries.append(entry)

    def add_entry(
        self,
        operation_type: str,
        line_number: int,
        execution_time: float,
        file_path: str = "manuscript",
        output: str = "",
        error: str = "",
    ) -> None:
        """Add a general execution entry."""
        entry = PythonExecutionEntry(
            entry_type=operation_type,
            line_number=line_number,
            execution_time=execution_time,
            file_path=file_path,
            output=output,
            error_message=error,
        )
        self.entries.append(entry)
        self.total_execution_time += execution_time

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics of Python execution."""
        if not self.entries:
            return {
                "total_executions": 0,
                "total_execution_time": 0.0,
                "initialization_blocks": 0,
                "execution_blocks": 0,
                "variable_gets": 0,
                "inline_executions": 0,
                "errors": 0,
                "files_processed": 0,
            }

        # Count different types of operations
        init_count = sum(1 for entry in self.entries if entry.entry_type == "init")
        exec_count = sum(1 for entry in self.entries if entry.entry_type == "exec")
        get_count = sum(1 for entry in self.entries if entry.entry_type == "get")
        inline_count = sum(1 for entry in self.entries if entry.entry_type == "inline")
        error_count = sum(1 for entry in self.entries if entry.error_message)

        # Count unique files
        files_processed = len({entry.file_path for entry in self.entries})

        return {
            "total_executions": len(self.entries),
            "total_execution_time": self.total_execution_time,
            "initialization_blocks": init_count,
            "execution_blocks": exec_count,
            "variable_gets": get_count,
            "inline_executions": inline_count,
            "errors": error_count,
            "files_processed": files_processed,
        }

    def get_entries_with_output(self) -> List[PythonExecutionEntry]:
        """Get all entries that have output."""
        return [entry for entry in self.entries if entry.output.strip()]

    def get_error_entries(self) -> List[PythonExecutionEntry]:
        """Get all entries that have errors."""
        return [entry for entry in self.entries if entry.error_message]

    def format_summary_for_display(self) -> str:
        """Format summary statistics for display."""
        stats = self.get_summary_statistics()

        if stats["total_executions"] == 0:
            return "📊 No Python code was executed during the build."

        lines = [
            "📊 Python Execution Summary:",
            f"   • Total operations: {stats['total_executions']}",
            f"   • Execution time: {stats['total_execution_time']:.3f}s",
            f"   • Files processed: {stats['files_processed']}",
        ]

        # Add breakdown if we have multiple types
        if stats["initialization_blocks"] > 0:
            lines.append(f"   • Initialization blocks: {stats['initialization_blocks']}")

        if stats["execution_blocks"] > 0:
            lines.append(f"   • Execution blocks: {stats['execution_blocks']}")

        if stats["variable_gets"] > 0:
            lines.append(f"   • Variable retrievals: {stats['variable_gets']}")

        if stats["inline_executions"] > 0:
            lines.append(f"   • Inline evaluations: {stats['inline_executions']}")

        if stats["errors"] > 0:
            lines.append(f"   • Errors encountered: {stats['errors']}")

        return "\n".join(lines)

    def format_outputs_for_display(self) -> str:
        """Format execution outputs for display."""
        output_entries = self.get_entries_with_output()

        if not output_entries:
            return ""

        lines = ["📋 Python Execution Outputs:"]

        for entry in output_entries:
            # Format file and line info
            location = f"{entry.file_path}:{entry.line_number}"

            # Clean and format output
            output_lines = entry.output.strip().split("\n")

            lines.append(f"   🐍 {location} ({entry.execution_time:.3f}s)")

            # Add output with proper indentation
            for output_line in output_lines:
                if output_line.strip():
                    lines.append(f"      {output_line}")

            lines.append("")  # Empty line between entries

        return "\n".join(lines)

    def format_errors_for_display(self) -> str:
        """Format execution errors for display."""
        error_entries = self.get_error_entries()

        if not error_entries:
            return ""

        lines = ["❌ Python Execution Errors:"]

        for entry in error_entries:
            location = f"{entry.file_path}:{entry.line_number}"
            lines.append(f"   🚨 {location}: {entry.error_message}")

        return "\n".join(lines)

    def has_python_activity(self) -> bool:
        """Check if any Python activity was recorded."""
        return len(self.entries) > 0

    def get_execution_summary(self) -> dict:
        """Get execution summary compatible with build manager expectations."""
        stats = self.get_summary_statistics()

        return {
            "total_entries": stats["total_executions"],
            "exec_blocks": stats["execution_blocks"] + stats["initialization_blocks"],
            "get_variables": stats["variable_gets"],
            "inline_blocks": stats["inline_executions"],
            "total_execution_time": stats["total_execution_time"],
            "errors": stats["errors"],
        }

    def format_verbose_report(self) -> str:
        """Format a comprehensive report for verbose output."""
        if not self.entries:
            return "📊 No Python code was executed during the build."

        parts = [self.format_summary_for_display()]

        # Add outputs if any
        outputs = self.format_outputs_for_display()
        if outputs:
            parts.append("")
            parts.append(outputs)

        # Add errors if any
        errors = self.format_errors_for_display()
        if errors:
            parts.append("")
            parts.append(errors)

        return "\n".join(parts)

    def display_report(self, verbose: bool = False) -> None:
        """Display the Python execution report."""
        if verbose:
            report = self.format_verbose_report()
        else:
            report = self.format_summary_for_display()

        if report:
            print(report)


# Global reporter instance
_global_reporter: Optional[PythonExecutionReporter] = None


def get_python_execution_reporter() -> PythonExecutionReporter:
    """Get or create the global Python execution reporter."""
    global _global_reporter
    if _global_reporter is None:
        _global_reporter = PythonExecutionReporter()
    return _global_reporter


def reset_python_execution_reporter() -> None:
    """Reset the global Python execution reporter for a new build."""
    global _global_reporter
    if _global_reporter is not None:
        _global_reporter.reset()
