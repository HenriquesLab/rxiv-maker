"""Integration tests for Python execution reporting in manuscripts."""

import os
from unittest.mock import patch

from rxiv_maker.converters.custom_command_processor import process_custom_commands
from rxiv_maker.converters.python_executor import reset_python_executor
from rxiv_maker.core.environment_manager import EnvironmentManager
from rxiv_maker.engines.operations.build_manager import BuildManager
from rxiv_maker.utils.python_execution_reporter import (
    get_python_execution_reporter,
    reset_python_execution_reporter,
)


class TestPythonExecutionReportingIntegration:
    """Test complete integration of Python execution reporting."""

    def setup_method(self):
        """Set up for each test."""
        # Reset Python execution reporter
        reset_python_execution_reporter()
        # Reset global Python executor to ensure clean state
        reset_python_executor()

        # Save original environment
        self.original_env = os.environ.copy()
        EnvironmentManager.clear_rxiv_vars()

    def teardown_method(self):
        """Clean up after each test."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

        # Reset reporter and executor
        reset_python_execution_reporter()
        reset_python_executor()

    def test_end_to_end_python_execution_with_reporting(self, tmp_path):
        """Test complete end-to-end Python execution with reporting."""
        # Create test manuscript directory
        manuscript_dir = tmp_path / "reporting_integration_test"
        manuscript_dir.mkdir()

        # Set up manuscript environment
        EnvironmentManager.set_manuscript_path(manuscript_dir)

        # Create test markdown with various Python operations
        test_markdown = """
# Data Analysis Report

## Initialization

{{py:exec
import math
import random

# Set up data
random.seed(42)
sample_data = [random.randint(1, 100) for _ in range(20)]
sample_size = len(sample_data)
mean_value = sum(sample_data) / sample_size
variance = sum((x - mean_value) ** 2 for x in sample_data) / (sample_size - 1)
std_dev = math.sqrt(variance)

print(f"Initialized with {sample_size} data points")
print(f"Mean: {mean_value:.2f}")
}}

## Results

We analyzed {{py:get sample_size}} data points.

The mean value is {{py:get mean_value}}.

The standard deviation is {{py:get std_dev}}.

Quick calculation: {py: 2 + 3}

## Summary

{{py:exec
# Generate summary
summary_text = f"Analysis complete: n={sample_size}, μ={mean_value:.2f}, σ={std_dev:.2f}"
print(summary_text)
}}

Final result: {{py:get summary_text}}
"""

        # Process the markdown
        result = process_custom_commands(test_markdown)

        # Get the reporter
        reporter = get_python_execution_reporter()

        # Verify that operations were recorded
        assert len(reporter.entries) > 0

        # Check that we have different types of operations
        operation_types = {entry.entry_type for entry in reporter.entries}
        expected_types = {"exec", "get", "inline"}
        assert expected_types.issubset(operation_types) or "init" in operation_types

        # Verify timing information is recorded
        assert reporter.total_execution_time > 0

        # Check that we have entries with output
        output_entries = [e for e in reporter.entries if e.output.strip()]
        assert len(output_entries) > 0

        # Verify specific outputs are captured
        all_output = " ".join(entry.output for entry in output_entries)
        assert "Initialized with 20 data points" in all_output
        assert "Analysis complete:" in all_output

        # Verify the processed result contains expected values
        assert "20" in result  # sample_size
        assert "5" in result  # inline calculation 2 + 3

    def test_manuscript_path_in_python_execution_reporting(self, tmp_path):
        """Test that MANUSCRIPT_PATH is available and reported correctly."""
        manuscript_dir = tmp_path / "manuscript_path_test"
        manuscript_dir.mkdir()

        # Create a data directory
        data_dir = manuscript_dir / "DATA"
        data_dir.mkdir()

        # Set environment
        EnvironmentManager.set_manuscript_path(manuscript_dir)

        # Test markdown that uses MANUSCRIPT_PATH
        test_markdown = """
# Path Testing

{{py:exec
import os
current_manuscript = MANUSCRIPT_PATH
print(f"Working with manuscript at: {current_manuscript}")

# Test relative path access
data_path = os.path.join(current_manuscript, "DATA")
data_exists = os.path.exists(data_path)
print(f"DATA directory exists: {data_exists}")
}}

Manuscript location: {{py:get current_manuscript}}
Data directory exists: {{py:get data_exists}}
"""

        # Process the markdown
        result = process_custom_commands(test_markdown)

        # Get reporter
        reporter = get_python_execution_reporter()

        # Find entries with MANUSCRIPT_PATH output
        path_outputs = [e for e in reporter.entries if e.output and str(manuscript_dir) in e.output]
        assert len(path_outputs) > 0

        # Verify the result contains the correct path
        assert str(manuscript_dir) in result
        assert "True" in result  # data_exists should be True

    def test_error_handling_in_reporting(self, tmp_path):
        """Test that Python execution errors are properly reported."""
        manuscript_dir = tmp_path / "error_reporting_test"
        manuscript_dir.mkdir()

        EnvironmentManager.set_manuscript_path(manuscript_dir)

        # Test markdown with intentional errors
        test_markdown = """
# Error Testing

{{py:exec
good_variable = "This works"
print("First execution successful")
}}

Good variable: {{py:get good_variable}}

{{py:exec
# This will cause an error
undefined_variable_error
}}

This should still work: {py: 10 + 5}

Bad variable: {{py:get nonexistent_variable}}
"""

        # Process the markdown (should handle errors gracefully)
        result = process_custom_commands(test_markdown)

        # Get reporter
        reporter = get_python_execution_reporter()

        # Should have recorded both successful and failed operations
        assert len(reporter.entries) > 0

        # Check for error entries
        error_entries = [e for e in reporter.entries if e.error]
        assert len(error_entries) > 0

        # Verify successful operations still recorded
        successful_entries = [e for e in reporter.entries if not e.error and e.output]
        assert len(successful_entries) > 0

        # Result should contain successful parts and error indicators
        assert "This works" in result
        assert "15" in result  # inline calculation should work
        assert "Error" in result or "[Error:" in result  # Should show error for bad variable

    def test_complex_python_workflow_reporting(self, tmp_path):
        """Test reporting for complex Python workflows with multiple stages."""
        manuscript_dir = tmp_path / "complex_workflow_test"
        manuscript_dir.mkdir()

        # Create test data file
        data_file = manuscript_dir / "test_data.csv"
        data_file.write_text("value,category\n1,A\n2,B\n3,A\n4,B\n5,A\n")

        EnvironmentManager.set_manuscript_path(manuscript_dir)

        # Complex workflow markdown
        test_markdown = """
# Complex Data Analysis

## Data Loading

{{py:exec
import os
import csv

# Load data using MANUSCRIPT_PATH
data_file = os.path.join(MANUSCRIPT_PATH, "test_data.csv")
print(f"Loading data from: {data_file}")

data = []
with open(data_file, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append({
            'value': int(row['value']),
            'category': row['category']
        })

print(f"Loaded {len(data)} records")
}}

## Analysis

{{py:exec
# Group by category
categories = {}
for record in data:
    cat = record['category']
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(record['value'])

print("Data grouped by category:")
for cat, values in categories.items():
    print(f"  {cat}: {values}")

# Calculate statistics
stats = {}
for cat, values in categories.items():
    stats[cat] = {
        'count': len(values),
        'sum': sum(values),
        'mean': sum(values) / len(values)
    }

print("\\nStatistics calculated")
}}

## Results

Total records: {{py:get len(data)}}

Category A mean: {{py:get stats['A']['mean']}}

Category B mean: {{py:get stats['B']['mean']}}

Quick check: {py: len(data) > 0}
"""

        # Process the complex workflow
        result = process_custom_commands(test_markdown)

        # Get reporter
        reporter = get_python_execution_reporter()

        # Verify comprehensive reporting
        assert len(reporter.entries) >= 5  # Multiple operations should be recorded

        # Check for different operation types
        operation_types = {entry.entry_type for entry in reporter.entries}
        assert len(operation_types) >= 2  # Should have at least exec/init and get operations

        # Verify output capture
        output_entries = [e for e in reporter.entries if e.output.strip()]
        assert len(output_entries) > 0

        # Check specific outputs
        all_output = " ".join(entry.output for entry in output_entries)
        assert "Loaded 5 records" in all_output
        assert "Data grouped by category:" in all_output

        # Verify final result
        assert "5" in result  # Total records
        assert "True" in result  # Quick check result

    def test_line_number_tracking_in_reporting(self, tmp_path):
        """Test that line numbers are correctly tracked in reporting."""
        manuscript_dir = tmp_path / "line_tracking_test"
        manuscript_dir.mkdir()

        EnvironmentManager.set_manuscript_path(manuscript_dir)

        # Create markdown with operations at known line positions
        test_markdown = """Line 1
Line 2
Line 3
{{py:exec
x = 42
}}
Line 7
Line 8
{{py:get x}}
Line 10
{py: x * 2}
Line 12
"""

        # Process with line tracking
        process_custom_commands(test_markdown)

        # Get reporter
        reporter = get_python_execution_reporter()

        # Check that line numbers are recorded
        line_numbers = [entry.line_number for entry in reporter.entries if entry.line_number]
        assert len(line_numbers) > 0

        # Line numbers should be reasonable (within the content)
        for line_num in line_numbers:
            assert line_num > 0
            assert line_num <= 15  # Should be within reasonable range

    @patch.object(BuildManager, "generate_figures")
    @patch.object(BuildManager, "validate_manuscript", return_value=True)
    @patch.object(BuildManager, "generate_latex")
    @patch.object(BuildManager, "compile_pdf")
    @patch.object(BuildManager, "validate_pdf")
    @patch.object(BuildManager, "copy_final_pdf")
    @patch.object(BuildManager, "run_word_count_analysis")
    def test_reporting_integration_with_build_manager(self, *mocks, tmp_path):
        """Test integration of reporting with BuildManager."""
        # Create minimal manuscript
        manuscript_dir = tmp_path / "build_integration_test"
        manuscript_dir.mkdir()

        # Create required files
        config_file = manuscript_dir / "00_CONFIG.yml"
        config_file.write_text("""
title: Integration Test
authors:
  - name: Test Author
""")

        main_file = manuscript_dir / "01_MAIN.md"
        main_file.write_text("""
# Integration Test

{{py:exec
test_value = "integration_successful"
print("Build integration test running")
}}

Result: {{py:get test_value}}
""")

        # Create BuildManager
        build_manager = BuildManager(
            manuscript_path=str(manuscript_dir), skip_validation=True, skip_pdf_validation=True, clear_output=False
        )

        # Mock display_python_execution_report to capture it being called
        with patch.object(BuildManager, "display_python_execution_report") as mock_display:
            # Run build
            success = build_manager.build()

            # Verify build succeeded
            assert success

            # Verify Python execution reporting was called
            mock_display.assert_called_once()

        # Verify reporter has entries
        reporter = get_python_execution_reporter()
        assert len(reporter.entries) > 0

        # Check that MANUSCRIPT_PATH was properly set
        assert EnvironmentManager.get_manuscript_path() == str(manuscript_dir.resolve())


class TestPythonExecutionReportingEdgeCases:
    """Test edge cases for Python execution reporting."""

    def setup_method(self):
        """Set up for each test."""
        reset_python_execution_reporter()
        reset_python_executor()

    def teardown_method(self):
        """Clean up after each test."""
        reset_python_execution_reporter()
        reset_python_executor()

    def test_empty_python_blocks_reporting(self, tmp_path):
        """Test reporting behavior with empty Python blocks."""
        manuscript_dir = tmp_path / "empty_blocks_test"
        manuscript_dir.mkdir()

        EnvironmentManager.set_manuscript_path(manuscript_dir)

        # Test markdown with empty blocks
        test_markdown = """
# Empty Block Testing

{{py:exec
# Just a comment
}}

{{py:exec

}}

{py: }

Normal text here.
"""

        # Process the markdown
        process_custom_commands(test_markdown)

        # Get reporter
        reporter = get_python_execution_reporter()

        # Should handle empty blocks gracefully
        # May or may not record entries depending on implementation
        # But should not crash or produce errors
        assert isinstance(reporter.entries, list)
        assert reporter.total_execution_time >= 0

    def test_unicode_content_in_reporting(self, tmp_path):
        """Test reporting with Unicode content."""
        manuscript_dir = tmp_path / "unicode_test"
        manuscript_dir.mkdir()

        EnvironmentManager.set_manuscript_path(manuscript_dir)

        # Test markdown with Unicode content
        test_markdown = """
# Unicode Testing 🔬

{{py:exec
unicode_message = "Résumé: Analysis complète ✅"
emoji_data = ["🔬", "📊", "📈"]
print(f"Message: {unicode_message}")
print(f"Emojis: {' '.join(emoji_data)}")
}}

Message: {{py:get unicode_message}}
"""

        # Process the markdown
        process_custom_commands(test_markdown)

        # Get reporter
        reporter = get_python_execution_reporter()

        # Should handle Unicode content properly
        output_entries = [e for e in reporter.entries if e.output]
        if output_entries:
            # Check that Unicode characters are preserved
            all_output = " ".join(entry.output for entry in output_entries)
            assert "Résumé" in all_output or "complète" in all_output or "✅" in all_output

    def test_very_long_output_reporting(self, tmp_path):
        """Test reporting behavior with very long output."""
        manuscript_dir = tmp_path / "long_output_test"
        manuscript_dir.mkdir()

        EnvironmentManager.set_manuscript_path(manuscript_dir)

        # Test markdown that generates long output
        test_markdown = """
# Long Output Testing

{{py:exec
# Generate a lot of output
for i in range(100):
    print(f"Line {i}: This is a test line with some content to make it longer")

long_string = "Very long result: " + "x" * 1000
}}

Result: {{py:get long_string}}
"""

        # Process the markdown
        process_custom_commands(test_markdown)

        # Get reporter
        reporter = get_python_execution_reporter()

        # Should handle long output appropriately
        assert len(reporter.entries) > 0

        # Output may be truncated, but should be handled gracefully
        output_entries = [e for e in reporter.entries if e.output]
        for entry in output_entries:
            # Output should be a string and not cause errors
            assert isinstance(entry.output, str)
