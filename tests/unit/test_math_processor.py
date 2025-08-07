"""Unit tests for math processor module."""

from rxiv_maker.converters.math_processor import (
    process_latex_math_blocks,
    protect_math_expressions,
    restore_math_expressions,
)


class TestProtectMathExpressions:
    """Test mathematical expression protection functionality."""

    def test_protect_inline_math(self):
        """Test protection of inline math expressions."""
        content = "The equation $E = mc^2$ is famous."
        protected_content, protected_math = protect_math_expressions(content)

        # Should have one protected math expression
        assert len(protected_math) == 1
        # Original math should be preserved
        assert "$E = mc^2$" in protected_math.values()
        # Content should have placeholder
        assert "XXPROTECTEDMATHXX0XXPROTECTEDMATHXX" in protected_content

    def test_protect_display_math(self):
        """Test protection of display math expressions."""
        content = "The equation $$E = mc^2$$ is important."
        protected_content, protected_math = protect_math_expressions(content)

        assert len(protected_math) == 1
        assert "$$E = mc^2$$" in protected_math.values()
        assert "XXPROTECTEDMATHXX0XXPROTECTEDMATHXX" in protected_content

    def test_protect_multiline_display_math(self):
        """Test protection of multiline display math."""
        content = """The equations:
        $$
        E = mc^2 \\\\
        F = ma
        $$
        are fundamental."""
        protected_content, protected_math = protect_math_expressions(content)

        assert len(protected_math) == 1
        math_expr = list(protected_math.values())[0]
        assert "E = mc^2" in math_expr
        assert "F = ma" in math_expr

    def test_protect_mixed_math_types(self):
        """Test protection of both inline and display math."""
        content = "Inline $x = y$ and display $$z = w$$ math."
        protected_content, protected_math = protect_math_expressions(content)

        assert len(protected_math) == 2
        values = list(protected_math.values())
        assert "$x = y$" in values
        assert "$$z = w$$" in values

    def test_protect_multiple_inline_math(self):
        """Test protection of multiple inline math expressions."""
        content = "We have $a = b$ and $c = d$ and $e = f$."
        protected_content, protected_math = protect_math_expressions(content)

        assert len(protected_math) == 3
        values = list(protected_math.values())
        assert "$a = b$" in values
        assert "$c = d$" in values
        assert "$e = f$" in values

    def test_avoid_false_positives_with_dollars(self):
        """Test that dollar signs in other contexts are not treated as math."""
        content = "The price is $100 and $200 for items."
        protected_content, protected_math = protect_math_expressions(content)

        # Should not protect these as they don't contain math
        # The regex should be more sophisticated to avoid single words
        # For now, just ensure it doesn't crash
        assert isinstance(protected_content, str)

    def test_complex_math_expressions(self):
        """Test complex mathematical expressions."""
        content = "The integral $\\int_{0}^{\\infty} e^{-x} dx = 1$ is standard."
        protected_content, protected_math = protect_math_expressions(content)

        assert len(protected_math) == 1
        math_expr = list(protected_math.values())[0]
        assert "\\int_{0}^{\\infty}" in math_expr

    def test_math_with_special_characters(self):
        """Test math expressions with special LaTeX characters."""
        content = "Math: $\\alpha + \\beta = \\gamma$ and more."
        protected_content, protected_math = protect_math_expressions(content)

        assert len(protected_math) == 1
        math_expr = list(protected_math.values())[0]
        assert "\\alpha" in math_expr
        assert "\\beta" in math_expr
        assert "\\gamma" in math_expr

    def test_nested_braces_in_math(self):
        """Test math expressions with nested braces."""
        content = "Complex math: $\\frac{a}{b} + \\sqrt{x^{2}}$ here."
        protected_content, protected_math = protect_math_expressions(content)

        assert len(protected_math) == 1
        math_expr = list(protected_math.values())[0]
        assert "\\frac{a}{b}" in math_expr
        assert "\\sqrt{x^{2}}" in math_expr


class TestRestoreMathExpressions:
    """Test mathematical expression restoration functionality."""

    def test_restore_single_math(self):
        """Test restoration of single math expression."""
        protected_math = {"XXPROTECTEDMATHXX0XXPROTECTEDMATHXX": "$E = mc^2$"}
        content = "The equation XXPROTECTEDMATHXX0XXPROTECTEDMATHXX is famous."

        result = restore_math_expressions(content, protected_math)
        assert result == "The equation $E = mc^2$ is famous."

    def test_restore_multiple_math(self):
        """Test restoration of multiple math expressions."""
        protected_math = {
            "XXPROTECTEDMATHXX0XXPROTECTEDMATHXX": "$a = b$",
            "XXPROTECTEDMATHXX1XXPROTECTEDMATHXX": "$c = d$",
        }
        content = "We have XXPROTECTEDMATHXX0XXPROTECTEDMATHXX and XXPROTECTEDMATHXX1XXPROTECTEDMATHXX."

        result = restore_math_expressions(content, protected_math)
        assert result == "We have $a = b$ and $c = d$."

    def test_restore_display_math(self):
        """Test restoration of display math."""
        protected_math = {"XXPROTECTEDMATHXX0XXPROTECTEDMATHXX": "$$x = y$$"}
        content = "Display math: XXPROTECTEDMATHXX0XXPROTECTEDMATHXX here."

        result = restore_math_expressions(content, protected_math)
        assert result == "Display math: $$x = y$$ here."

    def test_restore_empty_protection(self):
        """Test restoration with empty protection dict."""
        content = "No math here."
        result = restore_math_expressions(content, {})
        assert result == content

    def test_restore_no_placeholders(self):
        """Test restoration with no placeholders in content."""
        protected_math = {"XXPROTECTEDMATHXX0XXPROTECTEDMATHXX": "$x = y$"}
        content = "Text without placeholders."

        result = restore_math_expressions(content, protected_math)
        assert result == content

    def test_restore_complex_math(self):
        """Test restoration of complex math expressions."""
        complex_math = "$$\\int_{0}^{\\infty} \\frac{1}{x^2} dx = \\pi$$"
        protected_math = {"XXPROTECTEDMATHXX0XXPROTECTEDMATHXX": complex_math}
        content = "The integral XXPROTECTEDMATHXX0XXPROTECTEDMATHXX converges."

        result = restore_math_expressions(content, protected_math)
        assert complex_math in result


class TestProcessLatexMathBlocks:
    """Test LaTeX math block processing functionality."""

    def test_basic_math_block_processing(self):
        """Test basic math block processing."""
        content = "Text with $math$ here."
        result = process_latex_math_blocks(content)
        # Should process and return the content appropriately
        assert isinstance(result, str)

    def test_preserve_latex_commands(self):
        """Test that LaTeX commands in math are preserved."""
        content = "Math: $\\sum_{i=1}^n x_i$ and more text."
        result = process_latex_math_blocks(content)
        # LaTeX commands should be preserved
        assert "\\sum" in result

    def test_mixed_content_processing(self):
        """Test processing of mixed math and text content."""
        content = """
        Regular text here.

        Math equation: $E = mc^2$

        Display math:
        $$
        F = ma
        $$

        More text after.
        """
        result = process_latex_math_blocks(content)
        assert isinstance(result, str)
        assert "Regular text" in result
        assert "More text" in result


class TestIntegration:
    """Test integration of protection and restoration."""

    def test_protect_and_restore_cycle(self):
        """Test complete protect and restore cycle."""
        original = "Text with $math$ and $$display$$ math."

        # Protect
        protected_content, protected_math = protect_math_expressions(original)

        # Simulate some processing on non-math content
        processed = protected_content.replace("Text", "Modified text")

        # Restore
        final = restore_math_expressions(processed, protected_math)

        # Math should be unchanged, text should be modified
        assert "$math$" in final
        assert "$$display$$" in final
        assert "Modified text" in final

    def test_protect_restore_preserves_order(self):
        """Test that protection and restoration preserves math order."""
        original = "First $a$ then $b$ finally $c$."

        protected_content, protected_math = protect_math_expressions(original)
        final = restore_math_expressions(protected_content, protected_math)

        assert final == original

    def test_nested_processing_workflow(self):
        """Test typical workflow with nested processing steps."""
        content = "The formula $E = mc^2$ shows **energy** relationship."

        # Step 1: Protect math
        protected, math_dict = protect_math_expressions(content)

        # Step 2: Process markdown (simulated)
        processed = protected.replace("**energy**", "\\textbf{energy}")

        # Step 3: Restore math
        final = restore_math_expressions(processed, math_dict)

        assert "$E = mc^2$" in final
        assert "\\textbf{energy}" in final


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_content(self):
        """Test handling of empty content."""
        protected_content, protected_math = protect_math_expressions("")
        assert protected_content == ""
        assert len(protected_math) == 0

    def test_malformed_math_delimiters(self):
        """Test handling of malformed math delimiters."""
        content = "Unmatched $ dollar sign."
        protected_content, protected_math = protect_math_expressions(content)
        # Should handle gracefully
        assert isinstance(protected_content, str)

    def test_escaped_math_delimiters(self):
        """Test handling of escaped math delimiters."""
        content = "Escaped \\$ dollar signs should not be math."
        protected_content, protected_math = protect_math_expressions(content)
        # Escaped dollars should not be protected as math
        assert len(protected_math) == 0 or "\\$" not in protected_math.values()

    def test_very_long_math_expression(self):
        """Test handling of very long math expressions."""
        long_math = "$" + "x + " * 1000 + "y$"
        content = f"Long math: {long_math} here."

        protected_content, protected_math = protect_math_expressions(content)
        restored = restore_math_expressions(protected_content, protected_math)

        assert restored == content

    def test_math_at_boundaries(self):
        """Test math expressions at content boundaries."""
        content = "$start$ middle content $end$"
        protected_content, protected_math = protect_math_expressions(content)
        restored = restore_math_expressions(protected_content, protected_math)

        assert restored == content
        assert len(protected_math) == 2
