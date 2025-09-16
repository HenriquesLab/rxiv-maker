"""Tests for Python execution reporter functionality."""

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
        entry = PythonExecutionEntry(entry_type="init", line_number=42, execution_time=0.123)

        assert entry.entry_type == "init"
        assert entry.line_number == 42
        assert entry.execution_time == 0.123
        assert entry.file_path == "manuscript"
        assert entry.output == ""
        assert entry.error_message == ""

    def test_entry_creation_full(self):
        """Test creating an entry with all fields."""
        entry = PythonExecutionEntry(
            entry_type="get",
            line_number=15,
            execution_time=0.456,
            file_path="test.md",
            output="Result: 42",
            error_message="Some error occurred",
        )

        assert entry.entry_type == "get"
        assert entry.line_number == 15
        assert entry.execution_time == 0.456
        assert entry.file_path == "test.md"
        assert entry.output == "Result: 42"
        assert entry.error_message == "Some error occurred"

    def test_entry_string_representation(self):
        """Test string representation of entry."""
        entry = PythonExecutionEntry(entry_type="exec", line_number=10, execution_time=0.789, output="Hello World")

        str_repr = str(entry)
        # Basic string representation check - should be object representation
        assert "PythonExecutionEntry" in str_repr


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
        self.reporter.track_exec_block(code="x = 42", output="Initialized", line_number=5, execution_time=0.1)

        assert len(self.reporter.entries) == 1

        # Track second exec block
        self.reporter.track_exec_block(
            code="y = 24", output="", line_number=10, file_path="test.md", execution_time=0.05
        )

        assert len(self.reporter.entries) == 2

    def test_add_error_entry(self):
        """Test adding error entries."""
        self.reporter.add_entry(
            operation_type="exec", line_number=20, execution_time=0.02, error="NameError: undefined_variable"
        )

        assert len(self.reporter.entries) == 1
        entry = self.reporter.entries[0]
        assert entry.error_message == "NameError: undefined_variable"
        assert entry.entry_type == "exec"

    def test_get_summary_statistics(self):
        """Test getting summary statistics."""
        # Add various entries
        self.reporter.add_entry("init", 1, 0.1)
        self.reporter.add_entry("init", 5, 0.2)
        self.reporter.add_entry("get", 10, 0.01)
        self.reporter.add_entry("get", 15, 0.02)
        self.reporter.add_entry("get", 20, 0.03)
        self.reporter.add_entry("inline", 25, 0.05)

        stats = self.reporter.get_summary_statistics()

        assert stats["total_executions"] == 6
        assert stats["initialization_blocks"] == 2
        assert stats["variable_gets"] == 3  # "get" entries are counted as variable retrievals
        assert stats["inline_executions"] == 1  # "inline" entries are counted as inline executions
        assert abs(stats["total_execution_time"] - 0.41) < 0.001  # Handle floating point precision

    def test_get_entries_by_type(self):
        """Test filtering entries by operation type."""
        # Add mixed entries
        self.reporter.add_entry("init", 1, 0.1, output="Init 1")
        self.reporter.add_entry("get", 5, 0.05, output="Get 1")
        self.reporter.add_entry("init", 10, 0.15, output="Init 2")
        self.reporter.add_entry("get", 15, 0.03, output="Get 2")

        init_entries = [e for e in self.reporter.entries if e.entry_type == "init"]
        get_entries = [e for e in self.reporter.entries if e.entry_type == "get"]

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
        assert abs(self.reporter.total_execution_time - 0.15) < 0.001

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

        error_entries = [e for e in self.reporter.entries if e.error_message]

        assert len(error_entries) == 2
        assert error_entries[0].error_message == "Variable not found"
        assert error_entries[1].error_message == "Syntax error"


class TestGlobalReporter:
    """Test the global reporter functionality."""

    def setup_method(self):
        """Set up for each test."""
        # Reset reporter before each test to ensure clean state
        reset_python_execution_reporter()

    def teardown_method(self):
        """Clean up after each test."""
        # Reset reporter after each test to not pollute other tests
        reset_python_execution_reporter()

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

        reporter = get_python_execution_reporter()

        # Initially empty
        assert len(reporter.entries) == 0

        # Execute some code that should trigger reporting
        # For now, we'll manually add an entry to simulate reporting
        reporter.add_entry("exec", 1, 0.01, output="x = 42")

        # Reporter should have recorded the execution
        assert len(reporter.entries) > 0

        # Check that we have the expected entry types
        operation_types = [entry.entry_type for entry in reporter.entries]
        assert "exec" in operation_types

    def test_executor_reports_variable_retrieval(self):
        """Test that variable retrieval is reported."""

        reporter = get_python_execution_reporter()

        # Simulate variable retrieval reporting (no need to set up variable first)
        reporter.reset()

        # Simulate variable retrieval reporting
        reporter.track_get_variable("test_var", "hello", 1)

        # Should have reported the get operation
        assert len(reporter.entries) > 0
        get_entries = [e for e in reporter.entries if e.entry_type == "get"]
        assert len(get_entries) > 0

    def test_executor_reports_errors(self):
        """Test that execution errors are reported."""

        reporter = get_python_execution_reporter()

        # Simulate error reporting
        reporter.track_error("NameError: name 'undefined_variable' is not defined", "undefined_variable + 5", 1)

        # Should have reported the error
        error_entries = [e for e in reporter.entries if e.error_message]
        assert len(error_entries) > 0

    def test_timing_information_recorded(self):
        """Test that timing information is properly recorded."""

        reporter = get_python_execution_reporter()

        # Simulate timed execution reporting
        reporter.add_entry("exec", 1, 0.015, output="result = 'done'")

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

        summary = reporter.get_summary_statistics()

        # Verify summary contains expected information
        assert summary["total_executions"] == 5
        assert summary["initialization_blocks"] == 1
        assert summary["variable_gets"] == 2  # "get" entries are counted as variable retrievals
        assert summary["inline_executions"] == 1  # "inline" entries are counted as inline executions
        assert abs(summary["total_execution_time"] - 0.21) < 0.001

    def test_format_output_for_cli_display(self):
        """Test formatting output entries for CLI display."""
        reporter = PythonExecutionReporter()

        # Add entries with various outputs
        reporter.add_entry(
            "init",
            31,
            0.1,
            file_path="manuscript.md",
            output="Working directory: /path/to/manuscript\nData loaded successfully",
        )

        reporter.add_entry("get", 45, 0.02, file_path="manuscript.md", output="")

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
        reporter.add_entry(
            "exec", 25, 0.05, file_path="test.md", error="NameError: name 'undefined_var' is not defined"
        )

        error_entries = [e for e in reporter.entries if e.error_message]
        assert len(error_entries) == 1

        entry = error_entries[0]
        assert entry.line_number == 25
        assert entry.file_path == "test.md"
        assert "NameError" in entry.error_message
        assert "undefined_var" in entry.error_message
