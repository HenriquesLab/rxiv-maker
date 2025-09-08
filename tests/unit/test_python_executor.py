"""Tests for Python code execution in markdown commands.

This module tests the secure Python execution functionality,
including security restrictions, error handling, and output formatting.
"""

import pytest

from rxiv_maker.converters.python_executor import (
    PythonExecutionError,
    PythonExecutor,
    get_python_executor,
)


class TestPythonExecutor:
    """Test the Python executor functionality."""

    def setup_method(self):
        """Set up test executor for each test."""
        self.executor = PythonExecutor(timeout=5)

    def test_basic_arithmetic(self):
        """Test basic arithmetic execution."""
        result = self.executor.execute_inline("2 + 3")
        assert result == "5"

    def test_string_operations(self):
        """Test string operations."""
        result = self.executor.execute_inline("'Hello' + ' World'")
        assert result == "Hello World"

    def test_block_execution_with_print(self):
        """Test block execution with print statements."""
        code = """
x = 10
y = 20
print(f"Sum: {x + y}")
print("Done")
"""
        result = self.executor.execute_block(code)
        expected = "\\begin{verbatim}\nSum: 30\nDone\n\\end{verbatim}"
        assert result == expected

    def test_inline_expression(self):
        """Test inline expression execution."""
        result = self.executor.execute_inline("5 * 6")
        assert result == "30"

    def test_inline_with_variables(self):
        """Test that inline execution can use variables from previous block execution."""
        # First execute a block that sets a variable
        self.executor.execute_block("x = 42")
        # Then use it in inline execution
        result = self.executor.execute_inline("x * 2")
        assert result == "84"

    def test_persistent_context(self):
        """Test that variables persist between executions."""
        # Set a variable
        self.executor.execute_block("counter = 0")

        # Increment it
        self.executor.execute_block("counter += 1")

        # Check the value
        result = self.executor.execute_inline("counter")
        assert result == "1"

    def test_empty_output(self):
        """Test handling of code with no output."""
        result = self.executor.execute_block("x = 5")
        assert result == ""

    def test_syntax_error(self):
        """Test handling of syntax errors."""
        result = self.executor.execute_block("print(")
        assert "Python execution blocked:" in result
        assert "SyntaxError" in result or "syntax" in result.lower()

    def test_runtime_error(self):
        """Test handling of runtime errors."""
        result = self.executor.execute_block("1 / 0")
        assert "Python execution error:" in result
        assert "division by zero" in result.lower() or "zerodivision" in result.lower()

    def test_inline_error(self):
        """Test error handling in inline execution."""
        result = self.executor.execute_inline("undefined_variable")
        assert result.startswith("[Error:")
        assert "not defined" in result.lower()

    def test_timeout_protection(self):
        """Test that infinite loops are terminated."""
        # Use a very short timeout for this test
        executor = PythonExecutor(timeout=1)
        code = "while True: pass"
        result = executor.execute_block(code)
        assert "timed out" in result.lower()

    def test_output_length_limit(self):
        """Test that very long output is truncated."""
        executor = PythonExecutor(max_output_length=100)
        code = """
for i in range(1000):
    print(f"Line {i}: This is a very long line of text that will exceed the limit")
"""
        result = executor.execute_block(code)
        assert "truncated" in result

    def test_math_operations(self):
        """Test mathematical operations."""
        result = self.executor.execute_inline("pow(2, 8)")
        assert result == "256"

    def test_list_comprehension(self):
        """Test list comprehensions."""
        code = "result = [x**2 for x in range(5)]\nprint(result)"
        result = self.executor.execute_block(code)
        assert "[0, 1, 4, 9, 16]" in result

    def test_context_reset(self):
        """Test resetting the execution context."""
        # Set a variable
        self.executor.execute_block("test_var = 'original'")

        # Verify it exists
        result = self.executor.execute_inline("test_var")
        assert result == "original"

        # Reset context
        self.executor.reset_context()

        # Verify variable is gone
        result = self.executor.execute_inline("test_var")
        assert "not defined" in result.lower()


class TestSecurityRestrictions:
    """Test security restrictions and validation."""

    def setup_method(self):
        """Set up test executor for each test."""
        self.executor = PythonExecutor()

    def test_import_restriction(self):
        """Test that dangerous imports are blocked."""
        result = self.executor.execute_block("import os")
        assert "blocked" in result.lower() or "not allowed" in result.lower()

    def test_subprocess_restriction(self):
        """Test that subprocess import is blocked."""
        result = self.executor.execute_block("import subprocess")
        assert "blocked" in result.lower() or "not allowed" in result.lower()

    def test_sys_restriction(self):
        """Test that sys import is blocked."""
        result = self.executor.execute_block("import sys")
        assert "blocked" in result.lower() or "not allowed" in result.lower()

    def test_eval_restriction(self):
        """Test that eval function is blocked."""
        result = self.executor.execute_block("eval('print(\"test\")')")
        assert "blocked" in result.lower() or "not allowed" in result.lower()

    def test_exec_restriction(self):
        """Test that exec function is blocked."""
        result = self.executor.execute_block("exec('print(\"test\")')")
        assert "blocked" in result.lower() or "not allowed" in result.lower()

    def test_file_open_restriction(self):
        """Test that file operations are restricted."""
        result = self.executor.execute_block("open('/etc/passwd', 'r')")
        assert "blocked" in result.lower() or "not allowed" in result.lower()

    def test_safe_math_import(self):
        """Test that safe imports like math are allowed."""
        # Math import should be allowed as it's in the SAFE_MODULES whitelist
        result = self.executor.execute_block("import math; print(math.pi)")
        assert "3.14" in result

    def test_security_validation(self):
        """Test the security validation directly."""
        with pytest.raises(PythonExecutionError):
            self.executor.validate_code_security("import os")

        with pytest.raises(PythonExecutionError):
            self.executor.validate_code_security("eval('test')")

        with pytest.raises(PythonExecutionError):
            self.executor.validate_code_security("open('file.txt')")

    def test_safe_code_validation(self):
        """Test that safe code passes validation."""
        # These should not raise exceptions
        self.executor.validate_code_security("x = 1 + 2")
        self.executor.validate_code_security("print('hello')")
        self.executor.validate_code_security("result = [i for i in range(10)]")


class TestPythonCommandIntegration:
    """Test integration with the custom command processor."""

    def test_inline_command_processing(self):
        """Test inline Python command processing."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = "The result is {py: 3 + 4} and that's it."
        result = process_custom_commands(text)
        assert result == "The result is 7 and that's it."

    def test_block_command_processing(self):
        """Test block Python command processing."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = """
Before block:

{{py:
x = 5
y = 10
print(f"Result: {x * y}")
}}

After block.
"""
        result = process_custom_commands(text)
        assert "Result: 50" in result
        assert "\\begin{verbatim}" in result  # Should be wrapped in LaTeX verbatim block

    def test_mixed_commands(self):
        """Test mixing Python with other commands like blindtext."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = """
{{blindtext}}

Calculation: {py: 2 ** 8}

{{py:
import random
random.seed(42)
print(f"Random number: {random.randint(1, 100)}")
}}
"""
        result = process_custom_commands(text)
        assert "\\blindtext" in result  # Blindtext processed
        assert "256" in result  # Math calculation
        # Random is allowed in SAFE_MODULES, so output should be present
        assert "Random number:" in result

    def test_code_protection(self):
        """Test that Python commands in code blocks are protected."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = """
This should execute: {py: 1 + 1}

```python
# This should NOT execute: {py: 2 + 2}
print("Code block")
```

This should also execute: {py: 3 + 3}
"""
        result = process_custom_commands(text)
        assert "2" in result  # First command executed
        assert "{py: 2 + 2}" in result  # Code block preserved
        assert "6" in result  # Third command executed

    def test_error_handling_in_commands(self):
        """Test error handling in command processing."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = """
Good: {py: 5 + 5}
Bad: {py: undefined_variable}
Also good: {py: 10 - 3}
"""
        result = process_custom_commands(text)
        assert "10" in result  # First command works
        assert "[Error:" in result  # Second command fails gracefully
        assert "7" in result  # Third command works

    def test_multiline_block_commands(self):
        """Test multi-line block commands."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = """
{{py:
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

for i in range(6):
    print(f"fib({i}) = {fibonacci(i)}")
}}
"""
        result = process_custom_commands(text)
        assert "fib(5) = 5" in result
        assert "\\begin{verbatim}" in result  # Should be wrapped in LaTeX verbatim block

    def test_nested_braces_handling(self):
        """Test handling of nested braces in Python code."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = """
{{py:
data = {"a": 1, "b": 2}
print(f"Data: {data}")
}}
"""
        result = process_custom_commands(text)
        assert "Data: {'a': 1, 'b': 2}" in result or 'Data: {"a": 1, "b": 2}' in result


class TestGlobalExecutor:
    """Test the global executor instance."""

    def test_global_executor_singleton(self):
        """Test that get_python_executor returns the same instance."""
        executor1 = get_python_executor()
        executor2 = get_python_executor()
        assert executor1 is executor2

    def test_global_executor_persistence(self):
        """Test that global executor maintains state."""
        executor = get_python_executor()

        # Set a variable
        executor.execute_block("global_test_var = 42")

        # Get executor again and check variable persists
        executor2 = get_python_executor()
        result = executor2.execute_inline("global_test_var")
        assert result == "42"

    def test_context_isolation(self):
        """Test that different executor instances have isolated contexts."""
        executor1 = PythonExecutor()
        executor2 = PythonExecutor()

        # Set variable in first executor
        executor1.execute_block("isolated_var = 'first'")

        # Check it doesn't exist in second executor
        result = executor2.execute_inline("isolated_var")
        assert "not defined" in result.lower()


class TestEdgeCases:
    """Test edge cases and unusual scenarios."""

    def setup_method(self):
        """Set up test executor for each test."""
        self.executor = PythonExecutor()

    def test_empty_code(self):
        """Test execution of empty code."""
        result = self.executor.execute_block("")
        assert result == ""

        result = self.executor.execute_inline("")
        assert result == ""

    def test_whitespace_only_code(self):
        """Test execution of whitespace-only code."""
        result = self.executor.execute_block("   \n\n   ")
        assert result == ""

    def test_comment_only_code(self):
        """Test execution of comment-only code."""
        result = self.executor.execute_block("# This is just a comment")
        assert result == ""

    def test_unicode_handling(self):
        """Test handling of Unicode characters."""
        result = self.executor.execute_inline("'Hello 🌍'")
        assert result == "Hello 🌍"

    def test_large_numbers(self):
        """Test handling of large numbers."""
        result = self.executor.execute_inline("2 ** 100")
        assert len(result) > 20  # Should be a very large number

    def test_complex_data_structures(self):
        """Test complex data structures."""
        code = """
data = {
    'list': [1, 2, 3],
    'dict': {'nested': True},
    'tuple': (4, 5, 6)
}
print(f"Keys: {list(data.keys())}")
"""
        result = self.executor.execute_block(code)
        assert "Keys: ['list', 'dict', 'tuple']" in result

    def test_exception_in_inline(self):
        """Test exception handling in inline execution."""
        result = self.executor.execute_inline("int('not_a_number')")
        assert "[Error:" in result
        assert "invalid literal" in result.lower()

    def test_print_vs_expression_inline(self):
        """Test difference between print statements and expressions in inline."""
        # Expression should work
        result = self.executor.execute_inline("42")
        assert result == "42"

        # Print statement should also work
        result = self.executor.execute_inline("print('test')")
        assert result == "test"


class TestNewExecutionModel:
    """Test the new 3-step execution model with initialization and variable retrieval."""

    def setup_method(self):
        """Set up test executor for each test."""
        self.executor = PythonExecutor()

    def test_execute_initialization_block_basic(self):
        """Test basic initialization block execution."""
        code = """
x = 42
y = "hello world"
data = [1, 2, 3, 4, 5]
"""

        # Should not raise exception
        self.executor.execute_initialization_block(code)

        # Variables should be in context
        assert self.executor.execution_context.get("x") == 42
        assert self.executor.execution_context.get("y") == "hello world"
        assert self.executor.execution_context.get("data") == [1, 2, 3, 4, 5]

    def test_execute_initialization_block_with_imports(self):
        """Test initialization block with safe imports."""
        code = """
import math
from datetime import datetime

pi_value = math.pi
current_time = datetime.now().strftime("%Y-%m-%d")
"""

        self.executor.execute_initialization_block(code)

        # Should have imported successfully
        assert abs(self.executor.execution_context.get("pi_value") - 3.14159) < 0.001
        assert len(self.executor.execution_context.get("current_time")) == 10  # YYYY-MM-DD format

    def test_execute_initialization_block_with_functions(self):
        """Test initialization block with function definitions."""
        code = """
def calculate_mean(data):
    return sum(data) / len(data)

def calculate_std(data, mean):
    import math
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    return math.sqrt(variance)

sample_data = [1, 2, 3, 4, 5]
sample_mean = calculate_mean(sample_data)
sample_std = calculate_std(sample_data, sample_mean)
"""

        self.executor.execute_initialization_block(code)

        # Functions and results should be available
        assert callable(self.executor.execution_context.get("calculate_mean"))
        assert abs(self.executor.execution_context.get("sample_mean") - 3.0) < 0.001
        assert self.executor.execution_context.get("sample_std") > 0

    def test_execute_initialization_block_with_manuscript_context(self):
        """Test initialization block with manuscript context for error reporting."""
        code = "result = 'initialization_successful'"

        self.executor.execute_initialization_block(code, manuscript_file="test_manuscript.md", line_number=25)

        assert self.executor.execution_context.get("result") == "initialization_successful"

    def test_execute_initialization_block_error_handling(self):
        """Test error handling in initialization block."""
        code = "undefined_variable_that_causes_error"

        with pytest.raises((ValueError, RuntimeError)):  # Should raise PythonExecutionError or similar
            self.executor.execute_initialization_block(code)

    def test_get_variable_value_basic(self):
        """Test basic variable retrieval."""
        # Set up context
        self.executor.execution_context = {
            "x": 42,
            "message": "Hello World",
            "pi": 3.14159,
            "flag": True,
            "none_value": None,
        }

        # Test retrieving different types
        assert self.executor.get_variable_value("x") == "42"
        assert self.executor.get_variable_value("message") == "Hello World"
        assert self.executor.get_variable_value("pi") == "3.14159"
        assert self.executor.get_variable_value("flag") == "True"
        assert self.executor.get_variable_value("none_value") == "None"

    def test_get_variable_value_complex_types(self):
        """Test variable retrieval for complex data types."""
        self.executor.execution_context = {
            "list_data": [1, 2, 3, 4, 5],
            "dict_data": {"key": "value", "number": 42},
            "tuple_data": (1, 2, 3),
            "set_data": {1, 2, 3},
        }

        # These should return string representations
        list_result = self.executor.get_variable_value("list_data")
        assert "[1, 2, 3, 4, 5]" in list_result

        dict_result = self.executor.get_variable_value("dict_data")
        assert "key" in dict_result and "value" in dict_result

        tuple_result = self.executor.get_variable_value("tuple_data")
        assert "(1, 2, 3)" in tuple_result

    def test_get_variable_value_nonexistent(self):
        """Test retrieval of non-existent variable."""
        result = self.executor.get_variable_value("nonexistent_variable")

        assert "Error:" in result
        assert "not found" in result or "not defined" in result

    def test_get_variable_value_function(self):
        """Test retrieval of function objects."""
        # Define a function in context
        self.executor.execute_initialization_block("""
def test_function(x):
    return x * 2
""")

        result = self.executor.get_variable_value("test_function")
        assert "function" in result.lower()

    def test_three_step_workflow_integration(self):
        """Test complete 3-step workflow: exec → get → manuscript integration."""
        # Step 1: Execute initialization block
        init_code = """
import math
from datetime import datetime

# Simulate data analysis
raw_data = [1, 4, 7, 8, 9, 10, 12, 15, 18, 20]
sample_size = len(raw_data)
mean_value = sum(raw_data) / len(raw_data)
std_dev = math.sqrt(sum((x - mean_value) ** 2 for x in raw_data) / len(raw_data))
analysis_date = datetime.now().strftime("%Y-%m-%d")

# Derived metrics
cv = std_dev / mean_value * 100  # Coefficient of variation
summary = f"n={sample_size}, μ={mean_value:.2f}, σ={std_dev:.2f}"
"""

        self.executor.execute_initialization_block(init_code)

        # Step 2: Retrieve variables for manuscript
        sample_size_result = self.executor.get_variable_value("sample_size")
        mean_result = self.executor.get_variable_value("mean_value")
        std_result = self.executor.get_variable_value("std_dev")
        cv_result = self.executor.get_variable_value("cv")
        date_result = self.executor.get_variable_value("analysis_date")
        summary_result = self.executor.get_variable_value("summary")

        # Step 3: Verify results are manuscript-ready
        assert sample_size_result == "10"
        assert "10.4" in mean_result  # Should be approximately 10.4
        assert float(std_result) > 0  # Should be a positive number
        assert float(cv_result) > 0  # Should be a positive percentage
        assert len(date_result) == 10  # YYYY-MM-DD format
        assert "n=10" in summary_result and "μ=10.40" in summary_result

    def test_context_persistence_across_methods(self):
        """Test that context persists between initialization and retrieval."""
        # Initialize with some data
        self.executor.execute_initialization_block("persistent_var = 'test_value'")

        # Add more data through regular execution
        self.executor.execute_block("additional_var = persistent_var + '_extended'")

        # Retrieve both variables
        first_var = self.executor.get_variable_value("persistent_var")
        second_var = self.executor.get_variable_value("additional_var")

        assert first_var == "test_value"
        assert second_var == "test_value_extended"

    def test_initialization_error_with_context(self):
        """Test error handling in initialization with manuscript context."""
        code = "result = undefined_variable + 5"

        try:
            self.executor.execute_initialization_block(code, manuscript_file="error_test.md", line_number=42)
            raise AssertionError("Should have raised an exception")
        except Exception as e:
            # Error should contain useful information
            error_str = str(e)
            assert "error" in error_str.lower() or "Error" in error_str

    def test_variable_formatting_consistency(self):
        """Test that variable formatting is consistent and appropriate."""
        # Set up various data types
        self.executor.execute_initialization_block("""
integer_val = 42
float_val = 3.14159265359
string_val = "Hello World"
boolean_true = True
boolean_false = False
none_val = None
large_number = 123456789
scientific = 1.23e-5
""")

        # Test formatting
        assert self.executor.get_variable_value("integer_val") == "42"
        assert "3.14159" in self.executor.get_variable_value("float_val")
        assert self.executor.get_variable_value("string_val") == "Hello World"
        assert self.executor.get_variable_value("boolean_true") == "True"
        assert self.executor.get_variable_value("boolean_false") == "False"
        assert self.executor.get_variable_value("none_val") == "None"
        assert self.executor.get_variable_value("large_number") == "123456789"
        assert "1.23e-05" in self.executor.get_variable_value(
            "scientific"
        ) or "1.23e-5" in self.executor.get_variable_value("scientific")

    def test_security_in_initialization_block(self):
        """Test that security restrictions apply to initialization blocks."""
        dangerous_code = "import os; os.system('echo test')"

        with pytest.raises((ValueError, RuntimeError)):  # Should raise PythonExecutionError
            self.executor.execute_initialization_block(dangerous_code)

    def test_imports_available_across_methods(self):
        """Test that imports in initialization are available in later executions."""
        # Import in initialization
        self.executor.execute_initialization_block("""
import math
import random
from datetime import datetime

math_pi = math.pi
""")

        # Use imports in regular execution
        self.executor.execute_block("sqrt_result = math.sqrt(16)")

        # Should be available
        pi_result = self.executor.get_variable_value("math_pi")
        sqrt_result = self.executor.get_variable_value("sqrt_result")

        assert "3.14159" in pi_result
        assert sqrt_result == "4.0"
