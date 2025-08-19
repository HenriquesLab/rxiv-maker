"""Tests for Python code execution in markdown commands.

This module tests the secure Python execution functionality,
including security restrictions, error handling, and output formatting.
"""

import pytest

from rxiv_maker.converters.python_executor import (
    PythonExecutor,
    SecurityError,
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
        with pytest.raises(SecurityError):
            self.executor.validate_code_security("import os")

        with pytest.raises(SecurityError):
            self.executor.validate_code_security("eval('test')")

        with pytest.raises(SecurityError):
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
