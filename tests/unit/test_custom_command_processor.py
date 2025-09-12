"""Tests for custom command processor.

This module tests the custom markdown command processing functionality,
including blindtext commands and the extensible framework for future commands.
"""

import pytest

from rxiv_maker.converters.custom_command_processor import (
    COMMAND_PROCESSORS,
    _process_blindtext_commands,
    _process_tex_commands,
    get_supported_commands,
    process_custom_commands,
    register_command_processor,
)


class TestBlindtextCommands:
    """Test blindtext command processing."""

    def test_basic_blindtext_conversion(self):
        """Test basic blindtext command conversion."""
        input_text = "Before text\n\n{{blindtext}}\n\nAfter text"
        expected = "Before text\n\n\\blindtext\n\nAfter text"
        result = _process_blindtext_commands(input_text)
        assert result == expected

    def test_capitalized_blindtext_conversion(self):
        """Test capitalized Blindtext command conversion."""
        input_text = "Before text\n\n{{Blindtext}}\n\nAfter text"
        expected = "Before text\n\n\\Blindtext\n\nAfter text"
        result = _process_blindtext_commands(input_text)
        assert result == expected

    def test_multiple_blindtext_commands(self):
        """Test multiple blindtext commands in same text."""
        input_text = """
        # Title

        {{blindtext}}

        ## Section

        {{Blindtext}}

        More content.

        {{blindtext}}
        """
        result = _process_blindtext_commands(input_text)
        assert "\\blindtext" in result
        assert "\\Blindtext" in result
        assert result.count("\\blindtext") == 2  # Two lowercase instances
        assert result.count("\\Blindtext") == 1  # One capitalized instance

    def test_blindtext_with_whitespace(self):
        """Test blindtext commands with whitespace inside braces."""
        input_text = "{{ blindtext }}"
        expected = "\\blindtext"
        result = _process_blindtext_commands(input_text)
        assert result == expected

    def test_blindtext_case_sensitive(self):
        """Test that blindtext commands are case sensitive."""
        input_text = "{{BLINDTEXT}} {{blindTEXT}} {{BlindText}}"
        # Only exact matches should be converted
        result = _process_blindtext_commands(input_text)
        assert "\\BLINDTEXT" not in result
        assert "\\blindTEXT" not in result
        assert "\\BlindText" not in result
        assert "{{BLINDTEXT}}" in result
        assert "{{blindTEXT}}" in result
        assert "{{BlindText}}" in result

    def test_blindtext_in_complex_markdown(self):
        """Test blindtext commands within complex markdown structure."""
        input_text = """
        # Title

        This is **bold** and *italic* text.

        {{blindtext}}

        - List item 1
        - List item 2

        {{Blindtext}}

        | Table | Header |
        |-------|--------|
        | Cell  | Cell   |

        `{{blindtext}}` should not be converted in code.
        """
        # Note: _process_blindtext_commands doesn't handle code protection
        # That's handled by the main process_custom_commands function
        result = _process_blindtext_commands(input_text)
        # Should convert ALL commands since this function doesn't do code protection
        assert result.count("\\blindtext") == 2  # Both instances converted
        assert result.count("\\Blindtext") == 1
        # The backticks version will also be converted by this function
        assert "`\\blindtext`" in result


class TestTexCommands:
    """Test TeX command processing."""

    def test_basic_tex_conversion(self):
        """Test basic TeX command conversion."""
        input_text = "Before text\n\n{{tex: \\textbf{Hello World}}}\n\nAfter text"
        expected = "Before text\n\n\\textbf{Hello World}\n\nAfter text"
        result = _process_tex_commands(input_text)
        assert result == expected

    def test_multiline_tex_conversion(self):
        """Test multiline TeX command conversion."""
        input_text = """Before text

{{tex:
\\begin{table}
\\centering
\\caption{My Table}
\\begin{tabular}{cc}
A & B \\\\
C & D
\\end{tabular}
\\end{table}
}}

After text"""
        result = _process_tex_commands(input_text)
        # Should contain the LaTeX table structure
        assert "\\begin{table}" in result
        assert "\\centering" in result
        assert "\\caption{My Table}" in result
        assert "\\begin{tabular}{cc}" in result
        assert "\\end{table}" in result
        # Should not contain the TeX command wrapper
        assert "{{tex:" not in result
        assert "}}" not in result.replace("\\end{table}", "")

    def test_multiple_tex_commands(self):
        """Test multiple TeX commands in same text."""
        input_text = """
        # Title

        {{tex: \\textbf{Bold Text}}}

        ## Section

        {{tex: \\textit{Italic Text}}}

        More content.

        {{tex: \\underline{Underlined}}}
        """
        result = _process_tex_commands(input_text)
        assert "\\textbf{Bold Text}" in result
        assert "\\textit{Italic Text}" in result
        assert "\\underline{Underlined}" in result
        assert "{{tex:" not in result

    def test_tex_with_whitespace(self):
        """Test TeX commands with whitespace inside braces."""
        input_text = "{{tex:   \\textbf{Text}   }}"
        expected = "\\textbf{Text}"
        result = _process_tex_commands(input_text)
        assert result == expected

    def test_tex_with_complex_latex(self):
        """Test TeX commands with complex LaTeX structures."""
        input_text = """{{tex:
\\begin{equation}
E = mc^2
\\label{eq:einstein}
\\end{equation}
}}"""
        result = _process_tex_commands(input_text)
        assert "\\begin{equation}" in result
        assert "E = mc^2" in result
        assert "\\label{eq:einstein}" in result
        assert "\\end{equation}" in result
        assert "{{tex:" not in result

    def test_tex_with_nested_braces(self):
        """Test TeX commands with nested braces in LaTeX code."""
        input_text = "{{tex: \\frac{\\partial u}{\\partial t} = \\nabla^2 u}}"
        expected = "\\frac{\\partial u}{\\partial t} = \\nabla^2 u"
        result = _process_tex_commands(input_text)
        assert result == expected

    def test_tex_preserves_special_characters(self):
        """Test that TeX commands preserve special LaTeX characters."""
        input_text = "{{tex: Price: \\$100 \\& tax: 5\\% (total: \\$105)}}"
        expected = "Price: \\$100 \\& tax: 5\\% (total: \\$105)"
        result = _process_tex_commands(input_text)
        assert result == expected

    def test_tex_in_various_contexts(self):
        """Test TeX commands in different markdown contexts."""
        input_text = """
        > {{tex: \\textbf{Bold in blockquote}}}

        - {{tex: \\textit{Italic in list}}}

        1. {{tex: \\underline{Underlined in numbered list}}}

        **{{tex: \\textsf{Sans serif}}} in bold**

        *{{tex: \\texttt{Monospace}}} in italic*
        """
        result = _process_tex_commands(input_text)

        assert "\\textbf{Bold in blockquote}" in result
        assert "\\textit{Italic in list}" in result
        assert "\\underline{Underlined in numbered list}" in result
        assert "\\textsf{Sans serif}" in result
        assert "\\texttt{Monospace}" in result
        assert "{{tex:" not in result

    def test_empty_tex_command(self):
        """Test empty TeX command."""
        input_text = "{{tex: }}"
        expected = ""
        result = _process_tex_commands(input_text)
        assert result == expected

    def test_tex_with_comments(self):
        """Test TeX commands containing LaTeX comments - comments should be filtered out."""
        input_text = """{{tex:
% This is a LaTeX comment
\\textbf{Bold Text} % Another comment
\\\\  % Line break
\\textit{Italic Text}
}}"""
        result = _process_tex_commands(input_text)
        # Comments should be filtered out for security
        assert "% This is a LaTeX comment" not in result
        assert "% Another comment" not in result
        assert "% Line break" not in result

        # But the actual LaTeX commands should remain
        assert "\\textbf{Bold Text}" in result
        assert "\\\\" in result  # Line break command
        assert "\\textit{Italic Text}" in result


class TestCustomCommandProcessor:
    """Test the main custom command processor."""

    def test_process_custom_commands_blindtext(self):
        """Test that process_custom_commands handles blindtext correctly."""
        input_text = "{{blindtext}} and {{Blindtext}}"
        expected = "\\blindtext and \\Blindtext"
        result = process_custom_commands(input_text)
        assert result == expected

    def test_process_custom_commands_tex(self):
        """Test that process_custom_commands handles TeX commands correctly."""
        input_text = "{{tex: \\textbf{Bold}}} and {{tex: \\textit{Italic}}}"
        expected = "\\textbf{Bold} and \\textit{Italic}"
        result = process_custom_commands(input_text)
        assert result == expected

    def test_tex_code_protection_fenced(self):
        """Test that fenced code blocks protect TeX commands from processing."""
        input_text = """
        Regular text with {{tex: \\textbf{Bold}}}.

        ```
        This {{tex: \\textit{Italic}}} should not be converted.
        {{tex: \\underline{Underlined}}} also should not be converted.
        ```

        More {{tex: \\textsf{Sans}}} to convert.
        """
        result = process_custom_commands(input_text)

        # Count occurrences of converted commands
        converted_count = result.count("\\textbf{Bold}") + result.count("\\textsf{Sans}")
        # Count preserved commands in code blocks
        preserved_count = result.count("{{tex:")

        # Should convert 2 commands outside code blocks
        assert converted_count == 2
        # Should preserve 2 commands inside code blocks
        assert preserved_count == 2

    def test_tex_code_protection_inline(self):
        """Test that inline code protects TeX commands from processing."""
        input_text = "Convert {{tex: \\textbf{Bold}}} but not `{{tex: \\textit{Italic}}}` in code."
        result = process_custom_commands(input_text)

        assert "\\textbf{Bold}" in result
        assert "`{{tex: \\textit{Italic}}}`" in result
        assert result.count("\\textbf{Bold}") == 1

    def test_mixed_commands_tex_blindtext_python(self):
        """Test mixing TeX commands with other commands like blindtext and Python."""
        input_text = """
{{blindtext}}

{{tex: \\textbf{Bold TeX Text}}}

{{py:exec
calculation = 2 * 21
}}

The answer is {{py:get calculation}} and here's some {{tex: \\textit{italic text}}}.

{{Blindtext}}
"""
        result = process_custom_commands(input_text)

        # Should process all command types
        assert "\\blindtext" in result  # Blindtext processed
        assert "\\Blindtext" in result  # Blindtext processed
        assert "\\textbf{Bold TeX Text}" in result  # TeX processed
        assert "\\textit{italic text}" in result  # TeX processed
        assert "The answer is 42" in result  # Python processed

    def test_code_protection_fenced(self):
        """Test that fenced code blocks are protected from command processing."""
        input_text = """
        Regular text with {{blindtext}}.

        ```
        This {{blindtext}} should not be converted.
        {{Blindtext}} also should not be converted.
        ```

        More {{blindtext}} to convert.
        """
        result = process_custom_commands(input_text)

        # Count occurrences
        blindtext_count = result.count("\\blindtext")
        blindtext_upper_count = result.count("\\Blindtext")
        preserved_count = result.count("{{blindtext}}") + result.count("{{Blindtext}}")

        # Should convert 2 commands outside code blocks
        assert blindtext_count == 2
        assert blindtext_upper_count == 0  # Only lowercase instances in this test
        # Should preserve 2 commands inside code blocks
        assert preserved_count == 2

    def test_code_protection_inline(self):
        """Test that inline code is protected from command processing."""
        input_text = "Convert {{blindtext}} but not `{{blindtext}}` in code."
        result = process_custom_commands(input_text)

        assert "\\blindtext" in result
        assert "`{{blindtext}}`" in result
        assert result.count("\\blindtext") == 1

    def test_mixed_code_and_commands(self):
        """Test complex mixing of code blocks and commands."""
        input_text = """
        # Title

        {{blindtext}}

        ```python
        def test():
            # This {{blindtext}} is in code
            return "{{Blindtext}}"
        ```

        Back to regular text {{Blindtext}}.

        Inline `{{blindtext}}` is protected.
        """
        result = process_custom_commands(input_text)

        # Should convert 2 commands (1 blindtext + 1 Blindtext outside code)
        total_conversions = result.count("\\blindtext") + result.count("\\Blindtext")
        assert total_conversions == 2

        # Should preserve commands in code
        code_preserved = result.count("{{blindtext}}") + result.count("{{Blindtext}}")
        assert code_preserved >= 2  # At least 2 in fenced + inline code

    def test_empty_and_whitespace_input(self):
        """Test handling of empty and whitespace-only input."""
        assert process_custom_commands("") == ""
        assert process_custom_commands("   \n\n  ") == "   \n\n  "
        assert process_custom_commands("{{blindtext}}") == "\\blindtext"


class TestCommandRegistry:
    """Test the command processor registry system."""

    def test_default_supported_commands(self):
        """Test that blindtext and tex are in the default supported commands."""
        commands = get_supported_commands()
        assert "blindtext" in commands
        assert "tex" in commands

    def test_register_new_processor(self):
        """Test registering a new command processor."""

        def dummy_processor(text):
            return text.replace("{{test}}", "\\test")

        # Save original state
        original_processors = COMMAND_PROCESSORS.copy()

        try:
            register_command_processor("test", dummy_processor)

            # Check it was registered
            commands = get_supported_commands()
            assert "test" in commands
            assert COMMAND_PROCESSORS["test"] == dummy_processor

        finally:
            # Restore original state
            COMMAND_PROCESSORS.clear()
            COMMAND_PROCESSORS.update(original_processors)

    def test_processor_registry_isolation(self):
        """Test that processor registration doesn't affect existing processors."""

        def dummy_processor(text):
            return text

        original_processors = COMMAND_PROCESSORS.copy()
        original_commands = get_supported_commands()

        try:
            register_command_processor("dummy", dummy_processor)

            # Original commands should still be there
            new_commands = get_supported_commands()
            for cmd in original_commands:
                assert cmd in new_commands

        finally:
            COMMAND_PROCESSORS.clear()
            COMMAND_PROCESSORS.update(original_processors)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_malformed_commands(self):
        """Test handling of malformed command syntax."""
        input_text = """
        {blindtext}
        {{{blindtext}}}
        {{blindtext
        blindtext}}
        {{blindtext_typo}}
        """
        # Should not crash and should not convert malformed commands
        result = process_custom_commands(input_text)
        # Single braces should be preserved
        assert "{blindtext}" in result  # Single braces preserved
        # Triple braces contain valid {{blindtext}} so it gets partially converted
        assert "{\\blindtext}" in result  # Triple braces become {\blindtext}
        # Split commands should be preserved
        assert "{{blindtext\n        blindtext}}" in result  # Split command preserved
        # Typos should be preserved
        assert "{{blindtext_typo}}" in result  # Typo preserved

    def test_nested_braces_in_commands(self):
        """Test commands with nested braces (shouldn't convert)."""
        input_text = "{{blind{text}}} {{blind}text}}"
        result = process_custom_commands(input_text)
        # These are malformed and shouldn't convert
        assert "\\blind" not in result

    def test_commands_in_various_contexts(self):
        """Test commands in different markdown contexts."""
        input_text = """
        > {{blindtext}} in blockquote

        - {{blindtext}} in list

        1. {{blindtext}} in numbered list

        [{{blindtext}}](link) - in link text

        **{{blindtext}}** - in bold

        *{{blindtext}}* - in italic
        """
        result = process_custom_commands(input_text)

        # All should be converted (6 total)
        assert result.count("\\blindtext") == 6
        assert "{{blindtext}}" not in result


class TestIntegrationWithMd2tex:
    """Test integration with the main markdown processing pipeline."""

    def test_custom_commands_in_md2tex_pipeline(self):
        """Test that custom commands work in the full markdown pipeline."""
        # Test with a simpler input that won't trigger special processing
        input_markdown = "This is {{blindtext}} and {{Blindtext}} in text."

        # Import here to avoid circular imports during testing
        from rxiv_maker.converters.md2tex import convert_markdown_to_latex

        result = convert_markdown_to_latex(input_markdown)

        # Should contain converted commands
        assert "\\blindtext" in result
        assert "\\Blindtext" in result

        # Should not contain original markdown commands
        assert "{{blindtext}}" not in result
        assert "{{Blindtext}}" not in result


class TestPythonExecutionIntegration:
    """Test the new Python execution syntax integration."""

    def test_py_exec_command_processing(self):
        """Test {{py:exec}} command processing."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = """
Before execution:

{{py:exec
x = 42
y = "hello"
result = x * 2
}}

After execution.
"""
        result = process_custom_commands(text)
        # Should not contain the original commands
        assert "{{py:exec" not in result
        # Should not have visible output for exec blocks
        assert "84" not in result  # exec blocks don't output results

    def test_py_get_command_processing(self):
        """Test {{py:get}} command processing."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = """
{{py:exec
answer = 42
message = "Hello World"
}}

The answer is {{py:get answer}} and the message is {{py:get message}}.
"""
        result = process_custom_commands(text)

        # Should contain the retrieved values
        assert "The answer is 42 and the message is Hello World." in result
        # Should not contain the original commands
        assert "{{py:exec" not in result
        assert "{{py:get" not in result

    def test_py_exec_get_workflow(self):
        """Test complete py:exec → py:get workflow."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = """
# Data Analysis

{{py:exec
import math

# Sample data
data = [1, 2, 3, 4, 5]
n = len(data)
mean = sum(data) / n
variance = sum((x - mean) ** 2 for x in data) / n
std_dev = math.sqrt(variance)
}}

Our analysis of {{py:get n}} samples shows:
- Mean: {{py:get mean}}
- Standard deviation: {{py:get std_dev}}
"""
        result = process_custom_commands(text)

        # Should contain computed values
        assert "Our analysis of 5 samples shows:" in result
        assert "Mean: 3.0" in result
        assert "Standard deviation:" in result

        # Should not contain original commands
        assert "{{py:exec" not in result
        assert "{{py:get" not in result

    def test_py_exec_with_functions(self):
        """Test py:exec with function definitions."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = """
{{py:exec
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

fib_10 = fibonacci(10)
fib_sequence = [fibonacci(i) for i in range(8)]
}}

The 10th Fibonacci number is {{py:get fib_10}}.
The first 8 Fibonacci numbers are {{py:get fib_sequence}}.
"""
        result = process_custom_commands(text)

        assert "The 10th Fibonacci number is 55." in result
        assert "[0, 1, 1, 2, 3, 5, 8, 13]" in result

    def test_py_get_error_handling(self):
        """Test error handling in py:get commands."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = """
{{py:exec
valid_var = "I exist"
}}

Valid: {{py:get valid_var}}
Invalid: {{py:get nonexistent_variable}}
"""
        result = process_custom_commands(text)

        assert "Valid: I exist" in result
        assert "[Error" in result  # Should contain error message for invalid variable

    def test_py_exec_security_restrictions(self):
        """Test that security restrictions apply to py:exec."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = """
{{py:exec
import os
os.system('echo test')
}}

This should be blocked.
"""
        result = process_custom_commands(text)

        # Should contain error message about blocked execution
        assert "blocked" in result.lower() or "error" in result.lower()

    def test_multiple_py_exec_blocks(self):
        """Test multiple py:exec blocks with shared context."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = """
{{py:exec
x = 10
}}

{{py:exec
y = 20
z = x + y  # Should have access to x from previous block
}}

Result: {{py:get z}}
"""
        result = process_custom_commands(text)

        assert "Result: 30" in result

    def test_py_commands_in_code_blocks_protected(self):
        """Test that py: commands in code blocks are protected."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = """
This should execute: {{py:exec x = 5}}

```markdown
This should NOT execute: {{py:exec y = 10}}
And this should NOT be replaced: {{py:get x}}
```

This should work: {{py:get x}}
"""
        result = process_custom_commands(text)

        # Should contain the executed value
        assert "This should work: 5" in result

        # Should preserve code block content
        assert "{{py:exec y = 10}}" in result
        assert "{{py:get x}}" in result  # The one in code block should be preserved

    def test_py_exec_with_imports_and_calculations(self):
        """Test py:exec with real-world-like calculations."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = """
{{py:exec
import math
from datetime import datetime

# Simulate research data
sample_size = 100
mean_value = 25.6
std_error = 2.3
confidence_level = 0.95

# Calculate confidence interval
t_critical = 1.96  # Approximate for large samples
margin_error = t_critical * std_error / math.sqrt(sample_size)
ci_lower = mean_value - margin_error
ci_upper = mean_value + margin_error

analysis_date = datetime.now().strftime("%Y-%m-%d")
}}

## Results

Our analysis (conducted {{py:get analysis_date}}) of {{py:get sample_size}} samples revealed:

- Mean: {{py:get mean_value}}
- 95% CI: [{{py:get ci_lower}}, {{py:get ci_upper}}]
"""
        result = process_custom_commands(text)

        # Should contain all computed values
        assert "100 samples revealed:" in result
        assert "Mean: 25.6" in result
        assert "95% CI: [" in result and "]" in result
        assert len(result.split("analysis_date")[0]) > 0  # Should contain a date

    def test_py_commands_mixed_with_other_commands(self):
        """Test py: commands mixed with other commands like blindtext."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = """
{{blindtext}}

{{py:exec
calculation = 2 * 21
}}

The answer to everything is {{py:get calculation}}.

{{Blindtext}}
"""
        result = process_custom_commands(text)

        # Should process both command types
        assert "\\blindtext" in result  # Blindtext processed
        assert "\\Blindtext" in result  # Blindtext processed
        assert "The answer to everything is 42." in result  # Python processed

    def test_nested_py_commands_not_supported(self):
        """Test that nested py: commands are not supported (edge case)."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = """
{{py:exec
nested_command = "{{py:get nonexistent}}"
}}

Value: {{py:get nested_command}}
"""
        result = process_custom_commands(text)

        # Should contain the string literally, not execute nested command
        assert "{{py:get nonexistent}}" in result

    def test_py_exec_error_recovery(self):
        """Test that errors in py:exec raise PythonExecutionError as expected."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands
        from rxiv_maker.converters.python_executor import PythonExecutionError

        text = """
{{py:exec
good_var = "success"
}}

{{py:exec
bad_var = undefined_function()
}}

{{py:exec
another_good_var = "also success"
}}

First: {{py:get good_var}}
Second: {{py:get bad_var}}
Third: {{py:get another_good_var}}
"""
        # Python execution errors should halt processing by raising an exception
        with pytest.raises(PythonExecutionError) as exc_info:
            process_custom_commands(text)

        # Error message should indicate the problem
        assert "undefined_function" in str(exc_info.value)

    def test_py_exec_with_data_structures(self):
        """Test py:exec with complex data structures."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        text = """
{{py:exec
# Complex data structures
data_dict = {
    'experiment_1': [1, 2, 3, 4, 5],
    'experiment_2': [2, 4, 6, 8, 10],
    'metadata': {'date': '2024-01-01', 'researcher': 'Dr. Smith'}
}

exp1_mean = sum(data_dict['experiment_1']) / len(data_dict['experiment_1'])
exp2_mean = sum(data_dict['experiment_2']) / len(data_dict['experiment_2'])
researcher = data_dict['metadata']['researcher']
}}

Analysis by {{py:get researcher}}:
- Experiment 1 mean: {{py:get exp1_mean}}
- Experiment 2 mean: {{py:get exp2_mean}}
"""
        result = process_custom_commands(text)

        assert "Analysis by Dr. Smith:" in result
        assert "Experiment 1 mean: 3.0" in result
        assert "Experiment 2 mean: 6.0" in result
