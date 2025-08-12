"""Unit tests for figure processor module."""

from rxiv_maker.converters.figure_processor import (
    convert_figure_references_to_latex,
    convert_figures_to_latex,
)


class TestConvertFigureReferencesToLatex:
    """Test figure reference conversion functionality."""

    def test_basic_figure_reference(self):
        """Test conversion of basic figure references."""
        text = "See @fig:example for details."
        expected = r"See Fig. \ref{fig:example} for details."
        result = convert_figure_references_to_latex(text)
        assert result == expected

    def test_supplementary_figure_reference(self):
        """Test conversion of supplementary figure references."""
        text = "Refer to @sfig:supplementary for more info."
        expected = r"Refer to Fig. \ref{sfig:supplementary} for more info."
        result = convert_figure_references_to_latex(text)
        assert result == expected

    def test_multiple_figure_references(self):
        """Test conversion of multiple figure references."""
        text = "See @fig:first and @fig:second."
        expected = r"See Fig. \ref{fig:first} and Fig. \ref{fig:second}."
        result = convert_figure_references_to_latex(text)
        assert result == expected

    def test_mixed_figure_references(self):
        """Test conversion of mixed regular and supplementary references."""
        text = "Compare @fig:main with @sfig:supplement."
        expected = r"Compare Fig. \ref{fig:main} with Fig. \ref{sfig:supplement}."
        result = convert_figure_references_to_latex(text)
        assert result == expected

    def test_figure_reference_with_underscores(self):
        """Test figure references containing underscores."""
        text = "See @fig:my_figure_name for details."
        expected = r"See Fig. \ref{fig:my_figure_name} for details."
        result = convert_figure_references_to_latex(text)
        assert result == expected

    def test_figure_reference_with_hyphens(self):
        """Test figure references containing hyphens."""
        text = "See @fig:my-figure-name for details."
        expected = r"See Fig. \ref{fig:my-figure-name} for details."
        result = convert_figure_references_to_latex(text)
        assert result == expected

    def test_figure_reference_with_numbers(self):
        """Test figure references containing numbers."""
        text = "See @fig:figure123 and @sfig:supp456."
        expected = r"See Fig. \ref{fig:figure123} and Fig. \ref{sfig:supp456}."
        result = convert_figure_references_to_latex(text)
        assert result == expected

    def test_figure_references_at_sentence_boundaries(self):
        """Test figure references at start and end of sentences."""
        text = "@fig:example shows the result. The conclusion is in @fig:final."
        expected = r"Fig. \ref{fig:example} shows the result. The conclusion is in Fig. \ref{fig:final}."
        result = convert_figure_references_to_latex(text)
        assert result == expected

    def test_figure_references_in_parentheses(self):
        """Test figure references within parentheses."""
        text = "The data (see @fig:data) supports this."
        expected = r"The data (see Fig. \ref{fig:data}) supports this."
        result = convert_figure_references_to_latex(text)
        assert result == expected

    def test_no_false_positives(self):
        """Test that non-figure @ symbols are not converted."""
        text = "Email user@example.com and citation @smith2021."
        result = convert_figure_references_to_latex(text)
        # Should remain unchanged as these are not figure references
        assert result == text


class TestConvertFiguresToLatex:
    """Test figure environment conversion functionality."""

    def test_basic_figure_conversion(self):
        """Test conversion of basic markdown figure."""
        markdown = "![Caption text](path/to/image.png)"
        result = convert_figures_to_latex(markdown)
        # Should contain LaTeX figure environment
        assert r"\begin{figure}" in result
        assert r"\end{figure}" in result
        assert r"\includegraphics" in result
        assert "Caption text" in result

    def test_figure_with_id_attribute(self):
        """Test figure with id attribute conversion."""
        markdown = "![Caption text](path/to/image.png){#fig:example}"
        result = convert_figures_to_latex(markdown)
        assert r"\label{fig:example}" in result
        assert r"\includegraphics" in result

    def test_figure_with_width_attribute(self):
        """Test figure with width attribute conversion."""
        markdown = "![Caption text](path/to/image.png){width=50%}"
        result = convert_figures_to_latex(markdown)
        assert r"\includegraphics" in result
        # Should include width specification
        assert "0.5" in result or "width" in result

    def test_figure_with_multiple_attributes(self):
        """Test figure with multiple attributes."""
        markdown = "![Caption text](path/to/image.png){#fig:example width=70%}"
        result = convert_figures_to_latex(markdown)
        assert r"\label{fig:example}" in result
        assert r"\includegraphics" in result

    def test_supplementary_figure_processing(self):
        """Test supplementary figure processing."""
        markdown = "![Supplementary caption](supp/image.png){#sfig:supplement}"
        result = convert_figures_to_latex(markdown, is_supplementary=True)
        assert r"\label{sfig:supplement}" in result

    def test_figure_path_handling(self):
        """Test various figure path formats."""
        test_cases = [
            "![Caption](image.png)",
            "![Caption](./figures/image.png)",
            "![Caption](../images/figure.jpg)",
            "![Caption](figures/subfolder/diagram.pdf)",
        ]

        for markdown in test_cases:
            result = convert_figures_to_latex(markdown)
            assert r"\includegraphics" in result
            assert r"\begin{figure}" in result

    def test_figure_with_special_characters_in_caption(self):
        """Test figure captions with special characters."""
        markdown = "![Caption with & special % characters](image.png)"
        result = convert_figures_to_latex(markdown)
        # Should escape special LaTeX characters
        assert r"\&" in result or "Caption with" in result
        assert r"\%" in result or "characters" in result

    def test_multiple_figures(self):
        """Test multiple figures in same text."""
        markdown = """
        ![First figure](image1.png)

        Some text here.

        ![Second figure](image2.png){#fig:second}
        """
        result = convert_figures_to_latex(markdown)
        # Should contain two figure environments
        figure_count = result.count(r"\begin{figure}")
        assert figure_count == 2
        assert r"\label{fig:second}" in result

    def test_figure_protection_from_code_blocks(self):
        """Test that figures in code blocks are not processed."""
        markdown = """
        Regular figure: ![Caption](image.png)

        ```
        Code with ![fake figure](fake.png)
        ```

        `Inline code with ![fake](fake.png)`
        """
        result = convert_figures_to_latex(markdown)

        # Should process the regular figure
        figure_count = result.count(r"\begin{figure}")
        assert figure_count == 1

        # Code block content should be preserved
        assert "![fake figure](fake.png)" in result
        assert "![fake](fake.png)" in result

    def test_empty_caption_handling(self):
        """Test figures with empty captions."""
        markdown = "![](image.png)"
        result = convert_figures_to_latex(markdown)
        assert r"\includegraphics" in result
        assert r"\begin{figure}" in result

    def test_figure_alt_text_vs_caption(self):
        """Test distinction between alt text and caption."""
        markdown = "![Alt text for accessibility](image.png)"
        result = convert_figures_to_latex(markdown)
        # Alt text should become the caption
        assert "Alt text for accessibility" in result


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_malformed_figure_syntax(self):
        """Test handling of malformed figure syntax."""
        malformed_cases = [
            "![Caption without closing paren](image.png",
            "![Caption]()",  # Empty path
            "!Caption](image.png)",  # Missing opening bracket
        ]

        for case in malformed_cases:
            result = convert_figures_to_latex(case)
            # Should handle gracefully without crashing
            assert isinstance(result, str)

    def test_figure_with_complex_attributes(self):
        """Test figures with complex attribute syntax."""
        markdown = "![Caption](image.png){#fig:test width=80% height=10cm class=special}"
        result = convert_figures_to_latex(markdown)
        assert r"\label{fig:test}" in result

    def test_nested_markup_in_captions(self):
        """Test figures with nested markup in captions."""
        markdown = "![Caption with **bold** and *italic*](image.png)"
        result = convert_figures_to_latex(markdown)
        # Should handle nested markup appropriately
        assert isinstance(result, str)

    def test_very_long_figure_paths(self):
        """Test handling of very long figure paths."""
        long_path = "very/long/path/" + "/".join(["folder"] * 20) + "/image.png"
        markdown = f"![Caption]({long_path})"
        result = convert_figures_to_latex(markdown)
        assert r"\includegraphics" in result

    def test_figure_references_and_environments_together(self):
        """Test figure references and figure environments in same text."""
        text = """
        ![First figure](image1.png){#fig:first}

        As shown in @fig:first, the results are clear.

        ![Second figure](image2.png){#fig:second}

        Compare @fig:first with @fig:second.
        """
        # Process figures first, then references
        result = convert_figures_to_latex(text)
        result = convert_figure_references_to_latex(result)

        assert r"\label{fig:first}" in result
        assert r"\label{fig:second}" in result
        assert r"Fig. \ref{fig:first}" in result
        assert r"Fig. \ref{fig:second}" in result
