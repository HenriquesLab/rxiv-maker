"""Unit tests for text_formatters module."""

import pytest

from rxiv_maker.converters.md2tex import convert_markdown_to_latex
from rxiv_maker.converters.text_formatters import (
    convert_text_formatting_to_latex,
    process_code_spans,
    protect_underline_outside_texttt,
)


class TestCodeSpanMathProcessing:
    """Test mathematical expression handling in code spans."""

    def test_single_dollar_math_uses_detokenize(self):
        """Test that single dollar math in code spans uses detokenize."""
        input_text = "Use dollar signs like `$x = y$` for inline math"
        result = process_code_spans(input_text)

        assert "\\texttt{\\detokenize{$x = y$}}" in result
        assert "seqsplit" not in result

    def test_double_dollar_math_uses_detokenize(self):
        """Test that double dollar math in code spans uses detokenize."""
        input_text = "Display math uses `$$E = mc^2$$` syntax"
        result = process_code_spans(input_text)

        assert "\\texttt{\\detokenize{$$E = mc^2$$}}" in result
        assert "seqsplit" not in result

    def test_example_manuscript_problematic_text(self):
        """Test the specific problematic text from ../manuscript-rxiv-maker/MANUSCRIPT."""
        input_text = "Display equations utilise double dollar sign delimiters (`$$...$$`) for prominent expressions"
        result = process_code_spans(input_text)

        assert "\\texttt{\\detokenize{$$...$$}}" in result
        assert "seqsplit" not in result

    def test_inline_math_problematic_text(self):
        """Test inline math version of the problematic text."""
        input_text = "Inline mathematical expressions use delimiters (`$...$`) for simple formulas"
        result = process_code_spans(input_text)

        assert "\\texttt{\\detokenize{$...$}}" in result
        assert "seqsplit" not in result

    def test_long_code_without_math_uses_seqsplit(self):
        """Test that long code spans without math still use seqsplit."""
        input_text = "`This is a very long code span that exceeds twenty characters but has no mathematical content`"
        result = process_code_spans(input_text)

        assert "PROTECTED_TEXTTT_SEQSPLIT_START" in result
        assert "detokenize" not in result

    def test_short_code_without_math_uses_texttt(self):
        """Test that short code spans without math use regular texttt."""
        input_text = "`short code`"
        result = process_code_spans(input_text)

        assert "\\texttt{short code}" in result
        assert "seqsplit" not in result
        assert "detokenize" not in result

    def test_mixed_dollar_signs_use_detokenize(self):
        """Test code spans with mixed single and double dollar signs."""
        input_text = "Examples: `$inline$` and `$$display$$` math"
        result = process_code_spans(input_text)

        assert "\\texttt{\\detokenize{$inline$}}" in result
        assert "\\texttt{\\detokenize{$$display$$}}" in result
        assert "seqsplit" not in result

    def test_dollar_paren_combinations_use_detokenize(self):
        """Test that $( and $) combinations use detokenize."""
        input_text = "Function calls like `$(selector)` in jQuery"
        result = process_code_spans(input_text)

        assert "\\texttt{\\detokenize{$(selector)}}" in result
        assert "seqsplit" not in result

    def test_complex_math_expressions_use_detokenize(self):
        """Test complex mathematical expressions in code spans."""
        input_text = "Complex formula: `$\\alpha = \\frac{\\beta}{\\gamma}$`"
        result = process_code_spans(input_text)

        assert "\\texttt{\\detokenize{$\\alpha = \\frac{\\beta}{\\gamma}$}}" in result
        assert "seqsplit" not in result

    def test_multiple_code_spans_with_math(self):
        """Test multiple code spans with different math content."""
        input_text = "Use `$x$` for variables and `$$\\sum_{i=1}^{n} x_i$$` for summations"
        result = process_code_spans(input_text)

        assert "\\texttt{\\detokenize{$x$}}" in result
        assert "\\texttt{\\detokenize{$$\\sum_{i=1}^{n} x_i$$}}" in result
        assert "seqsplit" not in result


class TestFullPipelineMathProcessing:
    """Test mathematical expression handling through the full markdown to
    LaTeX pipeline."""

    def test_full_pipeline_handles_math_in_code_spans(self):
        """Test that the full pipeline correctly handles math in code spans."""
        markdown_content = """
# Test Document

Inline math uses (`$...$`) delimiters.

Display math uses (`$$...$$`) delimiters.

Regular code: `normal code without math`

Long code: `This is a very long code span that exceeds twenty characters`
"""

        result = convert_markdown_to_latex(markdown_content, is_supplementary=False)

        # Should use detokenize for math content
        assert "\\texttt{\\detokenize{$...$}}" in result
        assert "\\texttt{\\detokenize{$$...$$}}" in result

        # Should not have seqsplit for math content
        lines_with_math_and_seqsplit = [line for line in result.split("\n") if "seqsplit" in line and "$" in line]
        assert len(lines_with_math_and_seqsplit) == 0, f"Found math in seqsplit: {lines_with_math_and_seqsplit}"

    def test_supplementary_content_handles_math_in_code_spans(self):
        """Test that supplementary content correctly handles math in code spans."""
        markdown_content = """
{#snote:test} **Test Note**

Mathematical expressions are supported through (`$...$`) and (`$$...$$`) delimiters.
"""

        result = convert_markdown_to_latex(markdown_content, is_supplementary=True)

        # Should use detokenize for math content
        assert "\\texttt{\\detokenize{$...$}}" in result
        assert "\\texttt{\\detokenize{$$...$$}}" in result

        # Should not have seqsplit for math content
        lines_with_math_and_seqsplit = [line for line in result.split("\n") if "seqsplit" in line and "$" in line]
        assert len(lines_with_math_and_seqsplit) == 0, f"Found math in seqsplit: {lines_with_math_and_seqsplit}"

    def test_actual_example_manuscript_content(self):
        """Test the actual problematic content from ../manuscript-rxiv-maker/MANUSCRIPT."""
        markdown_content = """
{#snote:mathematical-formulas} **Mathematical Formula Support**

Inline mathematical expressions are supported through dollar sign delimiters
(`$...$`), enabling simple formulas.

Display equations utilise double dollar sign delimiters (`$$...$$`) for
prominent mathematical expressions.
"""

        result = convert_markdown_to_latex(markdown_content, is_supplementary=True)

        # Should use detokenize for math content
        assert "\\texttt{\\detokenize{$...$}}" in result
        assert "\\texttt{\\detokenize{$$...$$}}" in result

        # Should not have seqsplit for math content
        lines_with_math_and_seqsplit = [line for line in result.split("\n") if "seqsplit" in line and "$" in line]
        assert len(lines_with_math_and_seqsplit) == 0, f"Found math in seqsplit: {lines_with_math_and_seqsplit}"


class TestCodeSpanEdgeCases:
    """Test edge cases in code span processing."""

    def test_empty_code_span(self):
        """Test empty code spans."""
        input_text = "Empty: ``"
        result = process_code_spans(input_text)
        # Should handle gracefully without errors
        assert "Empty:" in result

    def test_nested_backticks(self):
        """Test code spans with nested backticks."""
        input_text = "Code with `nested \\`backticks\\` inside`"
        result = process_code_spans(input_text)
        # Should process without errors
        assert "\\texttt{" in result

    def test_code_span_with_backslashes(self):
        """Test that code spans with backslashes don't use seqsplit."""
        input_text = "`This is a very long code span with \\backslashes that should not use the seqsplit command`"
        result = process_code_spans(input_text)

        # Should use regular texttt, not seqsplit, because of backslashes
        assert "\\texttt{" in result
        assert "\\seqsplit" not in result  # Check for LaTeX command, not the word

    def test_math_with_backslashes_uses_detokenize(self):
        """Test that math with backslashes still uses detokenize."""
        input_text = "Complex math: `$\\alpha + \\beta$`"
        result = process_code_spans(input_text)

        assert "\\texttt{\\detokenize{$\\alpha + \\beta$}}" in result
        assert "seqsplit" not in result


class TestRegressionTests:
    """Regression tests to ensure the fix doesn't break existing functionality."""

    def test_regular_texttt_still_works(self):
        """Test that regular code spans without math still work."""
        input_text = "Regular `code` spans"
        result = process_code_spans(input_text)

        assert "\\texttt{code}" in result

    def test_seqsplit_still_works_for_long_code(self):
        """Test that seqsplit still works for long code without math."""
        input_text = "`This is a very long code span without any mathematical content that should trigger seqsplit`"
        result = process_code_spans(input_text)

        # Should still use seqsplit for long non-math content
        assert "PROTECTED_TEXTTT_SEQSPLIT_START" in result

    def test_hash_escaping_still_works(self):
        """Test that hash character handling works with detokenize."""
        input_text = "Code with `#hashtag` content"
        result = process_code_spans(input_text)

        # With detokenize, hash characters are handled literally without escaping
        assert "\\texttt{\\detokenize{#hashtag}}" in result

    def test_underscore_escaping_still_works(self):
        """Test that underscore escaping still works."""
        input_text = "Code with `file_name` content"
        result = process_code_spans(input_text)

        assert "XUNDERSCOREX" in result


@pytest.mark.ci_exclude  # Test for function that doesn't exist yet
class TestLongTechnicalIdentifiers:
    """Test the new long technical identifier wrapping functionality."""

    def test_identify_long_gene_names_with_underscores(self):
        """Test that long gene names with underscores are wrapped with seqsplit."""
        from rxiv_maker.converters.text_formatters import identify_long_technical_identifiers

        input_text = "The gene VERY_LONG_GENE_NAME_123 was analyzed along with SHORT_NAME."
        result = identify_long_technical_identifiers(input_text)

        # Long gene name should be wrapped
        assert "\\seqsplit{VERY_LONG_GENE_NAME_123}" in result
        # Short name should not be wrapped
        assert "SHORT_NAME" in result
        assert "\\seqsplit{SHORT_NAME}" not in result

    def test_identify_long_protein_names(self):
        """Test that long protein names are wrapped with seqsplit."""
        from rxiv_maker.converters.text_formatters import identify_long_technical_identifiers

        input_text = "The protein SuperLongProteinNameForTesting123 is important."
        result = identify_long_technical_identifiers(input_text)

        assert "\\seqsplit{SuperLongProteinNameForTesting123}" in result

    def test_identify_mixed_alphanumeric_identifiers(self):
        """Test that very long alphanumeric strings are wrapped."""
        from rxiv_maker.converters.text_formatters import identify_long_technical_identifiers

        input_text = "The identifier ABCDEFGHIJKLMNOPQRSTUVWXYZ123 is too long."
        result = identify_long_technical_identifiers(input_text)

        assert "\\seqsplit{ABCDEFGHIJKLMNOPQRSTUVWXYZ123}" in result

    def test_preserve_existing_latex_commands(self):
        """Test that existing LaTeX commands are not modified."""
        from rxiv_maker.converters.text_formatters import identify_long_technical_identifiers

        input_text = "See \\cite{VeryLongCitationKeyThatShouldNotBeModified} for details."
        result = identify_long_technical_identifiers(input_text)

        # Citation should remain unchanged
        assert "\\cite{VeryLongCitationKeyThatShouldNotBeModified}" in result
        assert "seqsplit" not in result

    def test_wrap_identifiers_in_parentheses(self):
        """Test that long identifiers in parentheses are wrapped correctly."""
        from rxiv_maker.converters.text_formatters import identify_long_technical_identifiers

        input_text = "The method (SuperLongMethodNameForTesting) was used."
        result = identify_long_technical_identifiers(input_text)

        assert "(\\seqsplit{SuperLongMethodNameForTesting})" in result

    def test_scientific_identifiers_with_dots(self):
        """Test that scientific identifiers with dots are wrapped."""
        from rxiv_maker.converters.text_formatters import identify_long_technical_identifiers

        input_text = "The domain protein.complex.subunit.123.alpha is analyzed."
        result = identify_long_technical_identifiers(input_text)

        assert "\\seqsplit{protein.complex.subunit.123.alpha}" in result

    def test_preserve_math_expressions(self):
        """Test that math expressions are not modified."""
        from rxiv_maker.converters.text_formatters import identify_long_technical_identifiers

        input_text = "The equation $VeryLongMathematicalExpressionHere$ should not change."
        result = identify_long_technical_identifiers(input_text)

        # Math should remain unchanged
        assert "$VeryLongMathematicalExpressionHere$" in result
        assert "seqsplit" not in result

    def test_contextual_long_strings(self):
        """Test the contextual long string wrapping function."""
        from rxiv_maker.converters.text_formatters import wrap_long_strings_in_context

        input_text = "We used the algorithm SuperLongAlgorithmNameForTesting in our analysis."
        result = wrap_long_strings_in_context(input_text)

        assert "algorithm \\seqsplit{SuperLongAlgorithmNameForTesting}" in result

    def test_contextual_with_short_strings(self):
        """Test that short strings after keywords are not wrapped."""
        from rxiv_maker.converters.text_formatters import wrap_long_strings_in_context

        input_text = "We used the method ABC for testing."
        result = wrap_long_strings_in_context(input_text)

        # Short string should not be wrapped
        assert "method ABC" in result
        assert "seqsplit" not in result

    def test_multiple_identifiers_in_text(self):
        """Test handling multiple long identifiers in the same text."""
        from rxiv_maker.converters.text_formatters import identify_long_technical_identifiers

        input_text = "Compare VERY_LONG_GENE_NAME_A with VERY_LONG_GENE_NAME_B for differences."
        result = identify_long_technical_identifiers(input_text)

        assert "\\seqsplit{VERY_LONG_GENE_NAME_A}" in result
        assert "\\seqsplit{VERY_LONG_GENE_NAME_B}" in result

    def test_edge_case_minimum_lengths(self):
        """Test that strings at minimum length thresholds are handled correctly."""
        from rxiv_maker.converters.text_formatters import identify_long_technical_identifiers

        # 15 characters exactly (should be wrapped)
        input_text = "Gene GENE_NAME_12345 is analyzed."
        result = identify_long_technical_identifiers(input_text)

        assert "\\seqsplit{GENE_NAME_12345}" in result

    def test_no_modification_of_existing_seqsplit(self):
        """Test that existing seqsplit commands are not double-wrapped."""
        from rxiv_maker.converters.text_formatters import identify_long_technical_identifiers

        input_text = "Already wrapped \\seqsplit{VERY_LONG_IDENTIFIER_ALREADY_WRAPPED} text."
        result = identify_long_technical_identifiers(input_text)

        # Should remain as single seqsplit
        assert "\\seqsplit{VERY_LONG_IDENTIFIER_ALREADY_WRAPPED}" in result
        # Should not be double-wrapped
        assert "\\seqsplit{\\seqsplit{" not in result


class TestUnderlineFormatting:
    """Test underline formatting functionality."""

    def test_basic_underline_conversion(self):
        """Test basic underline markdown to LaTeX conversion."""
        input_text = "This is __underlined text__ in a sentence."
        result = convert_text_formatting_to_latex(input_text)

        assert "\\underline{underlined text}" in result
        assert "__underlined text__" not in result

    def test_multiple_underlines_in_text(self):
        """Test multiple underlined sections in the same text."""
        input_text = "Both __first__ and __second__ are underlined."
        result = convert_text_formatting_to_latex(input_text)

        assert "\\underline{first}" in result
        assert "\\underline{second}" in result
        assert "__" not in result

    def test_underline_with_other_formatting(self):
        """Test underline combined with bold and italic formatting."""
        input_text = "Text with **bold**, *italic*, and __underlined__ formatting."
        result = convert_text_formatting_to_latex(input_text)

        assert "\\textbf{bold}" in result
        assert "\\textit{italic}" in result
        assert "\\underline{underlined}" in result

    def test_nested_formatting_combinations(self):
        """Test that formatting doesn't interfere with each other."""
        input_text = "Mix __underlined text with *italic* inside__ and **bold**."
        result = convert_text_formatting_to_latex(input_text)

        # Should handle nested formatting properly
        assert "\\underline{" in result
        assert "\\textbf{bold}" in result

    def test_single_underscore_not_converted(self):
        """Test that single underscores are not converted to underlines."""
        input_text = "Variables like _private_var and __underlined__ text."
        result = convert_text_formatting_to_latex(input_text)

        assert "_private_var" in result  # Single underscores preserved
        assert "\\underline{underlined}" in result  # Double underscores converted

    def test_underline_protection_in_code_blocks(self):
        """Test that underlines inside code blocks are not converted."""
        input_text = "Regular __underlined__ and code `__not_underlined__`."

        # First apply underline conversion
        result = convert_text_formatting_to_latex(input_text)
        # Then apply code span processing
        result = process_code_spans(result)

        assert "\\underline{underlined}" in result
        assert "\\texttt{" in result
        # The code block should contain either literal underscores or underscore placeholders
        assert "__not_underlined__" in result or "not\\_underlined" in result or "XUNDERSCOREX" in result

    def test_protect_underline_outside_texttt_function(self):
        """Test the protect_underline_outside_texttt function directly."""
        input_text = "Normal __underlined__ and \\texttt{__not_converted__} text."
        result = protect_underline_outside_texttt(input_text)

        assert "\\underline{underlined}" in result
        assert "\\texttt{__not_converted__}" in result  # Code block unchanged

    def test_underline_in_different_contexts(self):
        """Test underlines in various contexts like lists and quotes."""
        input_text = """
- List item with __underlined text__
- Another item

> Quote with __underlined content__ here

Regular paragraph with __underlined words__.
"""
        result = convert_text_formatting_to_latex(input_text)

        # All underlines should be converted regardless of context
        underline_count = result.count("\\underline{")
        assert underline_count == 3

    def test_empty_underline_tags(self):
        """Test handling of empty or malformed underline tags."""
        input_text = "Empty __ __ tags and incomplete __text"
        result = convert_text_formatting_to_latex(input_text)

        # Should handle gracefully without breaking
        assert "Empty" in result
        assert "incomplete" in result

    def test_underline_with_special_characters(self):
        """Test underlines containing special characters."""
        input_text = "Underline with __special #chars & symbols__ inside."
        result = convert_text_formatting_to_latex(input_text)

        assert "\\underline{special #chars & symbols}" in result

    def test_underline_preservation_in_latex_environments(self):
        """Test that underlines are not processed inside LaTeX environments."""
        input_text = """
Regular __underlined__ text.

\\begin{equation}
__not_processed__ = equation
\\end{equation}

More __underlined__ text.
"""
        result = protect_underline_outside_texttt(input_text)

        # Should have 2 underlined sections (not the one in equation)
        underline_count = result.count("\\underline{")
        assert underline_count == 2

    def test_long_underlined_text(self):
        """Test underlines with long content."""
        long_text = "This is a very long piece of text that should be underlined completely"
        input_text = f"Here is __{long_text}__ for testing."
        result = convert_text_formatting_to_latex(input_text)

        assert f"\\underline{{{long_text}}}" in result

    def test_underline_with_line_breaks(self):
        """Test that underlines don't span across line breaks inappropriately."""
        input_text = "Start __underlined\ntext continuing__ end"
        result = convert_text_formatting_to_latex(input_text)

        # Should NOT convert underlines that span line breaks (by design)
        assert "\\underline{" not in result
        assert "__underlined" in result  # Should remain unchanged

    def test_full_pipeline_underline_processing(self):
        """Test underline processing through the full markdown to LaTeX pipeline."""
        markdown_content = """
# Test Document

This paragraph contains __underlined text__ for testing.

- List with __underlined item__
- Regular item

Code example: `__this_should_not_be_underlined__`

More __underlined content__ here.
"""
        result = convert_markdown_to_latex(markdown_content, is_supplementary=False)

        # Should have 3 underlined sections (not the one in code)
        underline_count = result.count("\\underline{")
        assert underline_count == 3

        # Code block should preserve literal underscores
        assert "\\texttt{" in result

    def test_nested_underscores_in_underlined_text(self):
        """Test underlined text containing underscores within the content."""
        input_text = "Variable __my_variable_name__ should be underlined."
        result = convert_text_formatting_to_latex(input_text)

        assert "\\underline{my_variable_name}" in result
        assert "__my_variable_name__" not in result

    def test_very_long_underlined_text_performance(self):
        """Test underline processing with very long text for performance validation."""
        # Create a 1000+ character underlined text
        long_content = "a" * 1000
        input_text = f"Start __{long_content}__ end"
        result = convert_text_formatting_to_latex(input_text)

        assert f"\\underline{{{long_content}}}" in result
        assert f"__{long_content}__" not in result

    def test_complex_nested_formatting_combinations(self):
        """Test complex combinations of underline with other formatting."""
        test_cases = [
            # Underline containing bold
            ("Text __with **bold inside** underline__ here.", "\\underline{with \\textbf{bold inside} underline}"),
            # Bold containing underline
            ("Text **with __underline inside__ bold** here.", "\\textbf{with \\underline{underline inside} bold}"),
            # Multiple nested combinations
            (
                "Mix __underline *and italic*__ with **bold __and underline__** text.",
                "\\underline{underline \\textit{and italic}} with \\textbf{bold \\underline{and underline}}",
            ),
        ]

        for input_text, expected_pattern in test_cases:
            result = convert_text_formatting_to_latex(input_text)
            assert expected_pattern in result

    def test_underline_regex_performance_benchmark(self):
        """Test regex performance with multiple underlined sections."""
        # Create text with many underlined sections
        sections = ["__section{}__".format(i) for i in range(100)]
        input_text = " ".join(sections)

        import time

        start_time = time.time()
        result = convert_text_formatting_to_latex(input_text)
        end_time = time.time()

        # Should process quickly (less than 1 second for 100 sections)
        assert (end_time - start_time) < 1.0

        # Should convert all sections
        underline_count = result.count("\\underline{")
        assert underline_count == 100

    def test_environment_protection_with_proper_matching(self):
        """Test that the fixed regex properly matches begin/end environment pairs."""
        input_text = """
Regular __underlined__ text.

\\begin{equation}
x = __not_underlined__
\\end{equation}

\\begin{align}
y = __also_not_underlined__
\\end{align}

More __underlined__ text.
"""
        result = protect_underline_outside_texttt(input_text)

        # Should have 2 underlined sections (not the ones in math environments)
        underline_count = result.count("\\underline{")
        assert underline_count == 2

        # Math environments should remain unchanged
        assert "x = __not_underlined__" in result
        assert "y = __also_not_underlined__" in result
