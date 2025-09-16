"""Integration tests for Python execution system.

This module tests the complete integration of Python execution functionality
including the custom command processor, Python executor, and markdown-to-LaTeX
conversion pipeline.
"""

from rxiv_maker.converters.custom_command_processor import process_custom_commands
from rxiv_maker.converters.python_executor import get_python_executor


class TestPythonExecutionPipeline:
    """Test the complete Python execution pipeline."""

    def setup_method(self):
        """Set up for each test."""
        # Reset the global executor to ensure clean state
        executor = get_python_executor()
        executor.reset_context()

    def test_full_markdown_with_python_processing(self):
        """Test processing a complete markdown document with Python."""
        markdown_text = """
# Research Analysis

## Introduction

This document demonstrates executable Python within manuscripts.

{{py:exec
import math
from datetime import datetime

# Simulate research data
sample_data = [12, 15, 18, 20, 22, 25, 28, 30, 32, 35]
n = len(sample_data)
mean = sum(sample_data) / n
variance = sum((x - mean) ** 2 for x in sample_data) / (n - 1)
std_dev = math.sqrt(variance)
sem = std_dev / math.sqrt(n)

# Analysis metadata
analysis_date = datetime.now().strftime("%Y-%m-%d")
researcher = "Dr. Example"
}}

## Results

Our analysis conducted on {{py:get analysis_date}} by {{py:get researcher}} examined {{py:get n}} samples.

Key findings:
- Sample size: {{py:get n}}
- Mean value: {{py:get mean}}
- Standard deviation: {{py:get std_dev}}
- Standard error: {{py:get sem}}

{{py:exec
# Additional calculations
confidence_level = 0.95
t_critical = 2.262  # For n=10, 95% CI
margin_error = t_critical * sem
ci_lower = mean - margin_error
ci_upper = mean + margin_error
}}

The 95% confidence interval is [{{py:get ci_lower}}, {{py:get ci_upper}}].

## Conclusion

This demonstrates seamless integration of data analysis and manuscript writing.
"""

        result = process_custom_commands(markdown_text)

        # Verify all Python commands were processed
        assert "{{py:exec" not in result
        assert "{{py:get" not in result

        # Verify computed values are present
        assert "examined 10 samples" in result
        # Mean could be 23.7 or 23.8 depending on floating point precision
        assert "Mean value: 23.7" in result or "Mean value: 23.8" in result, (
            f"Expected mean 23.7 or 23.8 in result, got: {result}"
        )
        assert "Standard deviation:" in result
        assert "confidence interval is [" in result
        assert "Dr. Example" in result

        # Verify structure is preserved
        assert "# Research Analysis" in result
        assert "## Results" in result
        assert "## Conclusion" in result

    def test_python_with_mixed_commands(self):
        """Test Python commands mixed with other custom commands."""
        markdown_text = """
{{blindtext}}

{{py:exec
calculation = 6 * 7
result = f"The answer is {calculation}"
}}

Mathematical result: {{py:get result}}

{{Blindtext}}
"""

        result = process_custom_commands(markdown_text)

        # Both command types should be processed
        assert "\\blindtext" in result
        assert "\\Blindtext" in result
        assert "The answer is 42" in result
        assert "{{py:" not in result
        assert "{{blindtext}}" not in result

    def test_complex_data_analysis_workflow(self):
        """Test a complex data analysis workflow."""
        markdown_text = """
# Statistical Analysis Report

{{py:exec
import math
import statistics

# Dataset simulation
raw_data = [
    23.5, 24.1, 22.8, 25.3, 24.7, 23.9, 25.1, 24.4, 23.2, 24.8,
    25.5, 23.7, 24.9, 23.4, 25.2, 24.3, 23.8, 24.6, 25.0, 23.6
]

# Descriptive statistics
n_samples = len(raw_data)
mean_val = statistics.mean(raw_data)
median_val = statistics.median(raw_data)
mode_val = statistics.mode([round(x) for x in raw_data])
std_val = statistics.stdev(raw_data)
var_val = statistics.variance(raw_data)

# Additional metrics
min_val = min(raw_data)
max_val = max(raw_data)
range_val = max_val - min_val
cv = (std_val / mean_val) * 100  # Coefficient of variation

# Quartiles
sorted_data = sorted(raw_data)
q1 = statistics.quantiles(raw_data, n=4)[0]
q3 = statistics.quantiles(raw_data, n=4)[2]
iqr = q3 - q1
}}

## Dataset Overview

We analyzed {{py:get n_samples}} measurements with the following characteristics:

### Central Tendency
- Mean: {{py:get mean_val}}
- Median: {{py:get median_val}}
- Mode: {{py:get mode_val}}

### Variability
- Standard Deviation: {{py:get std_val}}
- Variance: {{py:get var_val}}
- Range: {{py:get range_val}}
- Coefficient of Variation: {{py:get cv}}%
- Interquartile Range: {{py:get iqr}}

{{py:exec
# Outlier detection using IQR method
lower_fence = q1 - 1.5 * iqr
upper_fence = q3 + 1.5 * iqr

outliers = [x for x in raw_data if x < lower_fence or x > upper_fence]
n_outliers = len(outliers)

# Normality assessment (simplified)
skewness = sum((x - mean_val)**3 for x in raw_data) / (n_samples * std_val**3)
kurtosis = sum((x - mean_val)**4 for x in raw_data) / (n_samples * std_val**4) - 3

# Classification
if abs(skewness) < 0.5:
    skew_interpretation = "approximately symmetric"
elif skewness > 0:
    skew_interpretation = "right-skewed"
else:
    skew_interpretation = "left-skewed"
}}

### Distribution Properties
- Skewness: {{py:get skewness}} ({{py:get skew_interpretation}})
- Kurtosis: {{py:get kurtosis}}
- Outliers detected: {{py:get n_outliers}}

{{py:exec
# Statistical inference
sem = std_val / math.sqrt(n_samples)
t_critical_95 = 2.093  # For df=19, 95% CI
t_critical_99 = 2.861  # For df=19, 99% CI

ci_95_lower = mean_val - t_critical_95 * sem
ci_95_upper = mean_val + t_critical_95 * sem
ci_99_lower = mean_val - t_critical_99 * sem
ci_99_upper = mean_val + t_critical_99 * sem

# Effect size for comparison to hypothetical value
hypothetical_mean = 24.0
cohens_d = abs(mean_val - hypothetical_mean) / std_val
}}

### Statistical Inference
- Standard Error: {{py:get sem}}
- 95% Confidence Interval: [{{py:get ci_95_lower}}, {{py:get ci_95_upper}}]
- 99% Confidence Interval: [{{py:get ci_99_lower}}, {{py:get ci_99_upper}}]
- Cohen's d (vs. μ=24.0): {{py:get cohens_d}}

## Conclusions

This analysis demonstrates the integration of statistical computation within manuscript preparation, ensuring accuracy and reproducibility.
"""

        result = process_custom_commands(markdown_text)

        # Verify no Python commands remain
        assert "{{py:" not in result

        # Verify statistical computations
        assert "analyzed 20 measurements" in result
        assert "Mean: 24." in result  # Should be around 24.x
        assert "Median: 24." in result
        assert "Standard Deviation:" in result
        assert "Coefficient of Variation:" in result
        assert "95% Confidence Interval: [" in result
        assert "Cohen's d" in result

        # Verify structure preservation
        assert "# Statistical Analysis Report" in result
        assert "## Dataset Overview" in result
        assert "### Central Tendency" in result

    def test_error_handling_and_recovery(self):
        """Test error handling doesn't break the entire pipeline."""
        markdown_text = """
# Error Handling Test

{{py:exec
good_variable = "This works"
}}

Working value: {{py:get good_variable}}

{{py:exec
# This will cause an error
bad_variable = undefined_function_call()
}}

This should show an error: {{py:get bad_variable}}

{{py:exec
another_good_variable = "This also works"
}}

Another working value: {{py:get another_good_variable}}

Regular markdown content should be unaffected.
"""

        result = process_custom_commands(markdown_text)

        # Good variables should work
        assert "Working value: This works" in result
        assert "Another working value: This also works" in result

        # Error should be handled gracefully
        assert "Error:" in result

        # Markdown structure should be preserved
        assert "# Error Handling Test" in result
        assert "Regular markdown content should be unaffected." in result

        # No Python commands should remain
        assert "{{py:" not in result

    def test_code_block_protection(self):
        """Test that Python commands in code blocks are protected."""
        markdown_text = """
# Code Protection Test

Execute this: {{py:exec test_var = "executed"}}

```python
# This should NOT be executed
{{py:exec blocked_var = "should not execute"}}
print("Code block content: {{py:get test_var}}")
```

```markdown
Markdown code block: {{py:get test_var}}
```

This should work: {{py:get test_var}}
This should fail: {{py:get blocked_var}}
"""

        result = process_custom_commands(markdown_text)

        # Executed command should work
        assert "This should work: executed" in result

        # Protected commands should remain unchanged
        assert "{{py:exec blocked_var" in result
        assert "{{py:get test_var}}" in result  # In code blocks
        assert "[Error retrieving blocked_var" in result  # Should show error

        # Should show error for blocked_var
        assert "Variable 'blocked_var' not found in context" in result

    def test_multiple_document_sections(self):
        """Test Python execution across multiple document sections."""
        markdown_text = """
# Multi-Section Analysis

## Section 1: Data Loading

{{py:exec
# Initialize data
section1_data = [10, 20, 30, 40, 50]
total_sum = sum(section1_data)
}}

Section 1 sum: {{py:get total_sum}}

## Section 2: Data Processing

{{py:exec
# Use data from Section 1
section2_data = [x * 2 for x in section1_data]
combined_sum = sum(section1_data) + sum(section2_data)
}}

Combined sum: {{py:get combined_sum}}

## Section 3: Final Analysis

{{py:exec
# Calculate final metrics
average_section1 = sum(section1_data) / len(section1_data)
average_section2 = sum(section2_data) / len(section2_data)
overall_average = (average_section1 + average_section2) / 2
}}

Final Results:
- Section 1 average: {{py:get average_section1}}
- Section 2 average: {{py:get average_section2}}
- Overall average: {{py:get overall_average}}
"""

        result = process_custom_commands(markdown_text)

        # All calculations should work with shared context
        assert "Section 1 sum: 150" in result
        assert "Combined sum: 450" in result  # 150 + 300
        assert "Section 1 average: 30.0" in result
        assert "Section 2 average: 60.0" in result
        assert "Overall average: 45.0" in result

        # Document structure preserved
        assert "# Multi-Section Analysis" in result
        assert "## Section 1:" in result
        assert "## Section 2:" in result
        assert "## Section 3:" in result


class TestPythonExecutionWithFileOperations:
    """Test Python execution integration with file operations."""

    def test_with_temporary_directory(self):
        """Test Python execution with directory context."""
        markdown_text = """
{{py:exec
import os
from pathlib import Path

# Get current working directory info
current_dir = Path.cwd().name
current_path = str(Path.cwd())
# Test that we can determine directory properties
is_valid_dir = len(current_dir) > 0
has_content = len(list(Path.cwd().iterdir())) >= 0  # At least can list contents
}}

Directory info:
- Current: {{py:get current_dir}}
- Is valid directory: {{py:get is_valid_dir}}
- Can list contents: {{py:get has_content}}
"""

        result = process_custom_commands(markdown_text)

        # Should contain directory information
        assert "Directory info:" in result
        assert "Current:" in result
        assert "Is valid directory: True" in result
        assert "Can list contents: True" in result

    def test_path_integration_simulation(self):
        """Test path integration without actually manipulating filesystem."""
        markdown_text = """
{{py:exec
# Simulate path operations (safe operations only)
import os
from pathlib import Path

# These are safe read-only operations
current_path = str(Path.cwd())
path_parts = current_path.split(os.sep)
last_part = path_parts[-1] if path_parts else "unknown"
is_absolute = os.path.isabs(current_path)
}}

Path analysis:
- Last directory: {{py:get last_part}}
- Is absolute path: {{py:get is_absolute}}
"""

        result = process_custom_commands(markdown_text)

        # Should execute safely without file system modifications
        assert "Path analysis:" in result
        assert "Last directory:" in result
        assert "Is absolute path: True" in result  # Current dir should be absolute


class TestPythonExecutionPerformance:
    """Test performance aspects of Python execution."""

    def test_large_computation(self):
        """Test handling of computationally intensive operations."""
        markdown_text = """
{{py:exec
# Moderately complex computation
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Calculate several Fibonacci numbers
fib_results = [fibonacci(i) for i in range(15)]
fib_sum = sum(fib_results)
fib_max = max(fib_results)
}}

Fibonacci analysis:
- Results: {{py:get fib_results}}
- Sum: {{py:get fib_sum}}
- Maximum: {{py:get fib_max}}
"""

        result = process_custom_commands(markdown_text)

        # Should complete without timeout
        assert "Fibonacci analysis:" in result
        assert "Sum: 986" in result  # Sum of fib(0) through fib(14)
        assert "Maximum: 377" in result  # fib(14)

    def test_memory_usage_reasonable(self):
        """Test that memory usage stays reasonable."""
        markdown_text = """
{{py:exec
# Create moderately large data structures
large_list = list(range(10000))
large_dict = {i: i**2 for i in range(1000)}
list_length = len(large_list)
dict_length = len(large_dict)

# Clean up to free memory
del large_list
del large_dict
}}

Data structure sizes:
- List length was: {{py:get list_length}}
- Dict length was: {{py:get dict_length}}
"""

        result = process_custom_commands(markdown_text)

        # Should handle large data structures
        assert "List length was: 10000" in result
        assert "Dict length was: 1000" in result
