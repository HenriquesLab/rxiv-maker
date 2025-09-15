"""Tests for Python execution reporter functionality."""

import os
import pytest
from unittest.mock import Mock, patch

from rxiv_maker.utils.python_execution_reporter import (
    PythonExecutionEntry,
    PythonExecutionReporter,
    get_python_execution_reporter,
    reset_python_execution_reporter,
)


class TestPythonExecutionEntry:
    """Test the PythonExecutionEntry data structure."""

    def test_entry_creation_minimal(self):
        """Test creating an entry with minimal required fields."""
        entry = PythonExecutionEntry(
            operation_type="init",
            line_number=42,
            execution_time=0.123
        )

        assert entry.operation_type == "init"
        assert entry.line_number == 42
        assert entry.execution_time == 0.123
        assert entry.file_path is None
        assert entry.output == ""
        assert entry.error is None

    def test_entry_creation_full(self):
        """Test creating an entry with all fields."""
        entry = PythonExecutionEntry(
            operation_type="get",
            line_number=15,
            execution_time=0.456,
            file_path="test.md",
            output="Result: 42",
            error="Some error occurred"
        )

        assert entry.operation_type == "get"
        assert entry.line_number == 15
        assert entry.execution_time == 0.456
        assert entry.file_path == "test.md"
        assert entry.output == "Result: 42"
        assert entry.error == "Some error occurred"

    def test_entry_string_representation(self):
        """Test string representation of entry."""
        entry = PythonExecutionEntry(
            operation_type="exec",
            line_number=10,
            execution_time=0.789,
            output="Hello World"
        )

        str_repr = str(entry)
        assert "exec" in str_repr
        assert "10" in str_repr
        assert "0.789" in str_repr


class TestPythonExecutionReporter:
    """Test the PythonExecutionReporter class."""

    def setup_method(self):
        """Set up for each test."""
        self.reporter = PythonExecutionReporter()

    def test_reporter_initialization(self):
        """Test reporter initialization."""
        assert len(self.reporter.entries) == 0
        assert self.reporter.total_execution_time == 0.0

    def test_track_exec_block(self):
        """Test tracking execution blocks."""
        # Track first exec block
        self.reporter.track_exec_block(
            code="x = 42",
            output="Initialized",
            line_number=5,
            execution_time=0.1
        )

        assert len(self.reporter.entries) == 1

        # Track second exec block
        self.reporter.track_exec_block(
            code="y = 24",
            output="",
            line_number=10,
            file_path="test.md",
            execution_time=0.05
        )

        assert len(self.reporter.entries) == 2

    def test_add_error_entry(self):
        """Test adding error entries."""
        self.reporter.add_entry(
            operation_type="exec",
            line_number=20,
            execution_time=0.02,
            error="NameError: undefined_variable"
        )

        assert len(self.reporter.entries) == 1
        entry = self.reporter.entries[0]
        assert entry.error == "NameError: undefined_variable"
        assert entry.operation_type == "exec"

    def test_get_summary_statistics(self):
        """Test getting summary statistics."""
        # Add various entries
        self.reporter.add_entry("init", 1, 0.1)
        self.reporter.add_entry("init", 5, 0.2)
        self.reporter.add_entry("get", 10, 0.01)
        self.reporter.add_entry("get", 15, 0.02)
        self.reporter.add_entry("get", 20, 0.03)
        self.reporter.add_entry("inline", 25, 0.05)

        stats = self.reporter.get_execution_summary()

        assert stats["total_operations"] == 6
        assert stats["initialization_blocks"] == 2
        assert stats["variable_retrievals"] == 3
        assert stats["inline_executions"] == 1
        assert stats["total_execution_time"] == 0.41

    def test_get_entries_by_type(self):
        """Test filtering entries by operation type."""
        # Add mixed entries
        self.reporter.add_entry("init", 1, 0.1, output="Init 1")
        self.reporter.add_entry("get", 5, 0.05, output="Get 1")
        self.reporter.add_entry("init", 10, 0.15, output="Init 2")
        self.reporter.add_entry("get", 15, 0.03, output="Get 2")

        init_entries = [e for e in self.reporter.entries if e.operation_type == "init"]
        get_entries = [e for e in self.reporter.entries if e.operation_type == "get"]

        assert len(init_entries) == 2
        assert len(get_entries) == 2
        assert init_entries[0].output == "Init 1"
        assert get_entries[1].output == "Get 2"

    def test_reset_reporter(self):
        """Test resetting the reporter."""
        # Add some entries
        self.reporter.add_entry("init", 1, 0.1)
        self.reporter.add_entry("get", 5, 0.05)

        assert len(self.reporter.entries) == 2
        assert self.reporter.total_execution_time == 0.15

        # Reset
        self.reporter.reset()

        assert len(self.reporter.entries) == 0
        assert self.reporter.total_execution_time == 0.0

    def test_get_output_entries_only(self):
        """Test getting only entries with output."""
        # Add entries with and without output
        self.reporter.add_entry("init", 1, 0.1, output="Has output")
        self.reporter.add_entry("get", 5, 0.05)  # No output
        self.reporter.add_entry("exec", 10, 0.2, output="Block output")
        self.reporter.add_entry("inline", 15, 0.03)  # No output

        output_entries = [e for e in self.reporter.entries if e.output]

        assert len(output_entries) == 2
        assert output_entries[0].output == "Has output"
        assert output_entries[1].output == "Block output"

    def test_get_error_entries_only(self):
        """Test getting only entries with errors."""
        # Add entries with and without errors
        self.reporter.add_entry("init", 1, 0.1)  # No error
        self.reporter.add_entry("get", 5, 0.05, error="Variable not found")
        self.reporter.add_entry("exec", 10, 0.2)  # No error
        self.reporter.add_entry("inline", 15, 0.03, error="Syntax error")

        error_entries = [e for e in self.reporter.entries if e.error]

        assert len(error_entries) == 2
        assert error_entries[0].error == "Variable not found"
        assert error_entries[1].error == "Syntax error"


class TestGlobalReporter:
    """Test the global reporter functionality."""

    def test_singleton_behavior(self):
        """Test that get_python_execution_reporter returns same instance."""
        reporter1 = get_python_execution_reporter()
        reporter2 = get_python_execution_reporter()

        assert reporter1 is reporter2

    def test_global_reset_functionality(self):
        """Test global reset functionality."""
        reporter = get_python_execution_reporter()

        # Add some data
        reporter.add_entry("init", 1, 0.1)

        assert len(reporter.entries) == 1

        # Reset globally
        reset_python_execution_reporter()

        # Get reporter again and verify it's clean
        reporter_after_reset = get_python_execution_reporter()
        assert len(reporter_after_reset.entries) == 0
        assert reporter_after_reset.total_execution_time == 0.0

    def test_persistence_across_calls(self):
        """Test that data persists across multiple get_python_execution_reporter calls."""
        reporter1 = get_python_execution_reporter()
        reporter1.add_entry("init", 1, 0.1)

        reporter2 = get_python_execution_reporter()
        assert len(reporter2.entries) == 1
        assert reporter2.total_execution_time == 0.1

        # Clean up
        reset_python_execution_reporter()


class TestReporterIntegrationWithExecutor:
    """Test integration between reporter and executor."""

    def setup_method(self):
        """Set up for each test."""
        # Reset reporter before each test
        reset_python_execution_reporter()

    def test_executor_reports_to_global_reporter(self):
        """Test that PythonExecutor reports to the global reporter."""
        from rxiv_maker.converters.python_executor import PythonExecutor

        executor = PythonExecutor()
        reporter = get_python_execution_reporter()

        # Initially empty
        assert len(reporter.entries) == 0

        # Execute some code
        executor.execute_block("x = 42")

        # Reporter should have recorded the execution
        assert len(reporter.entries) > 0

        # Check that we have the expected entry types
        operation_types = [entry.operation_type for entry in reporter.entries]
        assert "exec" in operation_types or "init" in operation_types

    def test_executor_reports_variable_retrieval(self):
        """Test that variable retrieval is reported."""
        from rxiv_maker.converters.python_executor import PythonExecutor

        executor = PythonExecutor()
        reporter = get_python_execution_reporter()

        # Set up a variable
        executor.execute_initialization_block("test_var = 'hello'")

        # Clear reporter to focus on get operation
        reporter.reset()

        # Retrieve variable
        result = executor.get_variable_value("test_var")

        # Should have reported the get operation
        assert len(reporter.entries) > 0
        get_entries = [e for e in reporter.entries if e.operation_type == "get"]
        assert len(get_entries) > 0

        assert result == "hello"

    def test_executor_reports_errors(self):
        """Test that execution errors are reported."""
        from rxiv_maker.converters.python_executor import PythonExecutor
        from rxiv_maker.converters.python_executor import PythonExecutionError

        executor = PythonExecutor()
        reporter = get_python_execution_reporter()

        # Try to execute code with an error
        try:
            executor.execute_initialization_block("undefined_variable + 5")
        except PythonExecutionError:
            pass  # Expected to fail

        # Should have reported the error
        error_entries = [e for e in reporter.entries if e.error]
        assert len(error_entries) > 0

    def test_timing_information_recorded(self):
        """Test that timing information is properly recorded."""
        from rxiv_maker.converters.python_executor import PythonExecutor
        import time

        executor = PythonExecutor()
        reporter = get_python_execution_reporter()

        # Execute code that takes some time
        code = """
import time
time.sleep(0.01)  # Sleep for 10ms
result = "done"
"""
        executor.execute_block(code)

        # Should have timing information
        assert len(reporter.entries) > 0

        # All entries should have positive execution times
        for entry in reporter.entries:
            assert entry.execution_time >= 0

        # Total execution time should be positive
        assert reporter.total_execution_time > 0


class TestReporterDisplayFormatting:
    """Test the display formatting functionality."""

    def test_format_summary_display(self):
        """Test formatting of summary information for display."""
        reporter = PythonExecutionReporter()

        # Add sample entries
        reporter.add_entry("init", 1, 0.1, output="Initialization complete")
        reporter.add_entry("get", 5, 0.01)
        reporter.add_entry("get", 10, 0.02)
        reporter.add_entry("inline", 15, 0.03, output="42")
        reporter.add_entry("exec", 20, 0.05, error="Some error")

        summary = reporter.get_summary()

        # Verify summary contains expected information
        assert summary["total_operations"] == 5
        assert summary["initialization_blocks"] == 1
        assert summary["variable_retrievals"] == 2
        assert summary["inline_executions"] == 1
        assert abs(summary["total_execution_time"] - 0.21) < 0.001

    def test_format_output_for_cli_display(self):
        """Test formatting output entries for CLI display."""
        reporter = PythonExecutionReporter()

        # Add entries with various outputs
        reporter.add_entry("init", 31, 0.1,
                          file_path="manuscript.md",
                          output="Working directory: /path/to/manuscript\nData loaded successfully")

        reporter.add_entry("get", 45, 0.02,
                          file_path="manuscript.md",
                          output="")

        # Get entries with output
        output_entries = [e for e in reporter.entries if e.output.strip()]

        assert len(output_entries) == 1
        entry = output_entries[0]
        assert entry.line_number == 31
        assert "Working directory:" in entry.output
        assert "Data loaded successfully" in entry.output

    def test_error_reporting_format(self):
        """Test error reporting format."""
        reporter = PythonExecutionReporter()

        # Add error entry
        reporter.add_entry("exec", 25, 0.05,
                          file_path="test.md",
                          error="NameError: name 'undefined_var' is not defined")

        error_entries = [e for e in reporter.entries if e.error]
        assert len(error_entries) == 1

        entry = error_entries[0]
        assert entry.line_number == 25
        assert entry.file_path == "test.md"
        assert "NameError" in entry.error
        assert "undefined_var" in entry.error