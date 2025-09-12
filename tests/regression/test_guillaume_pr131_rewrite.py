"""Tests for Guillaume's PR #131 figure processor rewrite regression issues.

This module contains regression tests for specific features introduced in
Guillaume's PR #131 figure processor rewrite, focusing on new figure
processing capabilities and enhanced attribute parsing.

Key features tested:
- PR #131: Complete figure processor rewrite
- Inline figure support
- Enhanced width parsing (percentages, fractions, LaTeX units)
- Landscape orientation support
- Better error handling and attribute parsing
- Improved positioning logic for dedicated pages
"""

import pytest


class TestGuillaumePR131Rewrite:
    """Test specific features introduced in Guillaume's PR #131 figure processor rewrite.

    PR #131 completely rewrote the create_latex_figure_environment function with:
    - Inline figure support
    - Enhanced width parsing (percentages, fractions, LaTeX units)
    - Landscape orientation support
    - Better error handling and attribute parsing
    - Improved positioning logic for dedicated pages
    """

    def test_inline_figure_support(self):
        """Test the new inline=true attribute for non-floating figures."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        # Test inline figure with basic attributes
        result = create_latex_figure_environment(
            path="FIGURES/test.png",
            caption="Test inline figure caption",
            attributes={"inline": True, "width": "0.8", "id": "fig:inline"},
        )

        # Should use center environment, not figure
        assert "\\begin{center}" in result, "Inline figures should use center environment"
        assert "\\end{center}" in result, "Should properly close center environment"
        assert "\\begin{figure" not in result, "Inline figures should NOT use figure environment"

        # Should use captionof for local caption
        assert "\\captionof{figure}" in result, "Inline figures should use captionof for local captions"
        assert "\\label{fig:inline}" in result, "Should include label when provided"

        # Should have raggedright justification (not center)
        assert "justification=raggedright" in result, "Inline captions should be left-aligned"
        assert "singlelinecheck=false" in result, "Should disable single line centering"

    def test_enhanced_width_parsing_percentages(self):
        """Test enhanced width parsing for percentage values."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        test_cases = [
            ("80%", "0.800\\linewidth"),
            ("50%", "0.500\\linewidth"),
            ("100%", "1.000\\linewidth"),
            ("75%", "0.750\\linewidth"),
        ]

        for input_width, expected_width in test_cases:
            result = create_latex_figure_environment(
                path="FIGURES/test.png", caption="Test caption", attributes={"width": input_width}
            )

            assert expected_width in result, (
                f"Width '{input_width}' should be parsed to '{expected_width}' but got: {result}"
            )

    def test_enhanced_width_parsing_fractions(self):
        """Test enhanced width parsing for decimal fractions."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        test_cases = [
            ("0.8", "0.800\\linewidth"),
            ("0.5", "0.500\\linewidth"),
            ("1.0", "1.000\\linewidth"),
            ("0.75", "0.750\\linewidth"),
        ]

        for input_width, expected_width in test_cases:
            result = create_latex_figure_environment(
                path="FIGURES/test.png", caption="Test caption", attributes={"width": input_width}
            )

            assert expected_width in result, (
                f"Width '{input_width}' should be parsed to '{expected_width}' but got: {result}"
            )

    def test_enhanced_width_parsing_latex_units(self):
        """Test enhanced width parsing for various LaTeX units."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        # Test LaTeX relative units (these get processed correctly)
        test_cases = [
            ("0.8\\textwidth", "0.800\\textwidth"),
            ("0.9\\columnwidth", "0.900\\columnwidth"),
        ]

        for input_width, expected_width in test_cases:
            result = create_latex_figure_environment(
                path="FIGURES/test.png", caption="Test caption", attributes={"width": input_width}
            )

            assert expected_width in result, (
                f"Width '{input_width}' should be parsed to '{expected_width}' but got: {result}"
            )

        # Test absolute units - these get clamped to \linewidth due to safety clamp for single-column figures
        absolute_test_cases = ["10cm", "5in", "200pt"]

        for input_width in absolute_test_cases:
            result = create_latex_figure_environment(
                path="FIGURES/test.png", caption="Test caption", attributes={"width": input_width}
            )
            # Absolute units in single-column figures get safety-clamped to \linewidth
            assert "width=\\linewidth" in result, (
                f"Absolute width '{input_width}' should be safety-clamped to \\linewidth for single-column figures"
            )

        # Test absolute units with strict_width=true - should preserve exact width
        for input_width in absolute_test_cases:
            result = create_latex_figure_environment(
                path="FIGURES/test.png", caption="Test caption", attributes={"width": input_width, "strict_width": True}
            )
            assert f"width={input_width}" in result, (
                f"Absolute width '{input_width}' with strict_width=true should preserve exact width"
            )

    def test_landscape_figure_support(self):
        """Test the new landscape=true attribute for sideways figures."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        # Test regular landscape figure
        result = create_latex_figure_environment(
            path="FIGURES/wide_plot.png",
            caption="Wide landscape plot",
            attributes={"landscape": True, "id": "fig:landscape"},
        )

        assert "\\begin{sidewaysfigure}" in result, "Landscape figures should use sidewaysfigure"
        assert "\\end{sidewaysfigure}" in result, "Should properly close sidewaysfigure"
        assert "\\begin{figure}" not in result, "Should not use regular figure environment"

        # Test landscape with two-column spanning
        result2 = create_latex_figure_environment(
            path="FIGURES/wide_plot.png",
            caption="Wide landscape plot spanning columns",
            attributes={"landscape": True, "width": "\\textwidth", "id": "fig:landscape2"},
        )

        assert "\\begin{sidewaysfigure*}" in result2, "Two-column landscape should use sidewaysfigure*"
        assert "\\end{sidewaysfigure*}" in result2, "Should properly close sidewaysfigure*"

    def test_barrier_support(self):
        """Test the new barrier=true attribute for float barriers."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        result = create_latex_figure_environment(
            path="FIGURES/test.png", caption="Figure with barrier", attributes={"barrier": True}
        )

        assert "\\FloatBarrier" in result, "Barrier=true should add FloatBarrier command"

        # Test without barrier
        result2 = create_latex_figure_environment(
            path="FIGURES/test.png", caption="Figure without barrier", attributes={}
        )

        assert "\\FloatBarrier" not in result2, "Should not add FloatBarrier by default"

    def test_max_height_attribute(self):
        """Test the new max_height attribute for height constraints."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        result = create_latex_figure_environment(
            path="FIGURES/tall_figure.png",
            caption="Tall figure with height constraint",
            attributes={"width": "\\textwidth", "max_height": "0.8\\textheight"},
        )

        assert "height=0.800\\textheight" in result, "Should include height constraint"
        assert "width=\\textwidth" in result, "Should still include width"
        assert "keepaspectratio" in result, "Should maintain aspect ratio with both width and height"

    def test_fit_presets(self):
        """Test the new fit attribute with page/width/height presets."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        # Test fit=page with dedicated page positioning
        result_page = create_latex_figure_environment(
            path="FIGURES/full_page.png", caption="Full page figure", attributes={"fit": "page", "tex_position": "p"}
        )

        assert "width=\\textwidth" in result_page, "fit=page should use full textwidth"
        assert "height=0.95\\textheight" in result_page, "fit=page should use most of textheight"
        assert "\\begin{figure*}[p]" in result_page, "fit=page with position=p should use figure*[p]"

        # Test fit=width
        result_width = create_latex_figure_environment(
            path="FIGURES/wide.png", caption="Full width figure", attributes={"fit": "width"}
        )

        assert "width=\\linewidth" in result_width, "fit=width should use full linewidth"

        # Test fit=height
        result_height = create_latex_figure_environment(
            path="FIGURES/tall.png", caption="Full height figure", attributes={"fit": "height"}
        )

        assert "height=\\textheight" in result_height, "fit=height should use full textheight"

    def test_fullpage_attribute_alias(self):
        """Test that fullpage=true is equivalent to fit=page."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        result = create_latex_figure_environment(
            path="FIGURES/fullpage.png",
            caption="Full page figure using fullpage attribute",
            attributes={"fullpage": True, "tex_position": "p"},
        )

        assert "width=\\textwidth" in result, "fullpage=true should use full textwidth"
        assert "height=0.95\\textheight" in result, "fullpage=true should use most of textheight"
        assert "\\begin{figure*}[p]" in result, "fullpage=true should use figure*[p] for dedicated page"

    def test_improved_position_parsing(self):
        """Test improved positioning attribute parsing."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        # Test positions with brackets are properly stripped
        test_cases = [
            ("[!htbp]", "[!htbp]"),
            ("!htbp", "[!htbp]"),
            ("[tp]", "[tp]"),
            ("tp", "[tp]"),
            ("[p]", "[p]"),
            ("p", "[p]"),
        ]

        for input_pos, expected_pos in test_cases:
            result = create_latex_figure_environment(
                path="FIGURES/test.png", caption="Test positioning", attributes={"tex_position": input_pos}
            )

            # For dedicated page positioning, should use figure*
            if "[p]" in expected_pos:
                assert f"\\begin{{figure*}}{expected_pos}" in result, (
                    f"Position '{input_pos}' should parse to '{expected_pos}' and use figure* for dedicated page"
                )
            else:
                assert f"\\begin{{figure}}{expected_pos}" in result, (
                    f"Position '{input_pos}' should parse to '{expected_pos}' in regular figure"
                )

    def test_caption_width_customization(self):
        """Test the new caption_width attribute for custom caption widths."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        result = create_latex_figure_environment(
            path="FIGURES/test.png",
            caption="Figure with custom caption width",
            attributes={"width": "\\textwidth", "caption_width": "0.8\\textwidth"},
        )

        assert "width=0.8\\textwidth" in result, "Should use custom caption width"
        assert "\\captionsetup{" in result, "Should have caption setup"

    def test_strict_width_attribute(self):
        """Test the new strict_width attribute to prevent width clamping."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        # Test without strict_width - should clamp textwidth to linewidth for single-column
        result1 = create_latex_figure_environment(
            path="FIGURES/test.png",
            caption="Regular figure",
            attributes={"width": "\\textwidth"},  # No strict_width, should get clamped to linewidth
        )

        # With textwidth, should auto-upgrade to figure* for proper two-column spanning
        assert "\\begin{figure*}" in result1, "textwidth should auto-upgrade to figure* for spanning"

        # Test with strict_width=true - should preserve exact width
        result2 = create_latex_figure_environment(
            path="FIGURES/test.png",
            caption="Strict width figure",
            attributes={"width": "\\textwidth", "strict_width": True},
        )

        assert "width=\\textwidth" in result2, "strict_width=true should preserve exact width"
        assert "\\begin{figure*}" in result2, "textwidth should still use figure* for proper rendering"

    def test_error_handling_graceful_fallbacks(self):
        """Test that PR #131's error handling provides graceful fallbacks."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        # Test with invalid width value - should still work
        result = create_latex_figure_environment(
            path="FIGURES/test.png", caption="Figure with invalid width", attributes={"width": "invalid_width_value"}
        )

        # Should still generate valid LaTeX even with invalid width
        assert "\\begin{figure}" in result, "Should generate valid figure even with invalid width"
        assert "\\includegraphics" in result, "Should include graphics command"
        assert "\\caption{Figure with invalid width}" in result, "Should include caption"

    def test_complex_attribute_combinations(self):
        """Test complex combinations of new PR #131 attributes."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        # Test landscape + barrier + custom positioning
        result1 = create_latex_figure_environment(
            path="FIGURES/complex1.png",
            caption="Complex landscape figure",
            attributes={
                "landscape": True,
                "barrier": True,
                "tex_position": "!t",
                "width": "0.9\\textwidth",
                "id": "fig:complex1",
            },
        )

        assert "\\begin{sidewaysfigure*}[!t]" in result1, "Should combine landscape + two-column + positioning"
        assert "\\FloatBarrier" in result1, "Should include barrier"
        assert "width=0.900\\textwidth" in result1, "Should parse width correctly"

        # Test inline + max_height + custom caption width
        result2 = create_latex_figure_environment(
            path="FIGURES/complex2.png",
            caption="Complex inline figure with height constraint",
            attributes={"inline": True, "width": "80%", "max_height": "10cm", "id": "fig:complex2"},
        )

        assert "\\begin{center}" in result2, "Should use center for inline"
        assert "width=0.800\\linewidth" in result2, "Should parse percentage width"
        assert "height=10cm" in result2, "Should include height constraint"
        assert "\\captionof{figure}" in result2, "Should use captionof for inline"

    def test_pr131_regression_prevention(self):
        """Test that PR #131 changes don't break existing functionality."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        # Test basic figure (should work exactly as before)
        basic_result = create_latex_figure_environment(path="FIGURES/basic.png", caption="Basic figure", attributes={})

        assert "\\begin{figure}[!htbp]" in basic_result, "Basic figures should still work"
        assert "width=\\linewidth" in basic_result, "Should default to linewidth"
        assert "\\includegraphics" in basic_result, "Should include graphics"
        assert "\\caption{Basic figure}" in basic_result, "Should include caption"

        # Test textwidth auto-detection (key Guillaume fix)
        textwidth_result = create_latex_figure_environment(
            path="FIGURES/wide.png", caption="Wide figure", attributes={"width": "\\textwidth"}
        )

        assert "\\begin{figure*}" in textwidth_result, "textwidth should auto-upgrade to figure*"
        assert "width=\\textwidth" in textwidth_result, "Should preserve textwidth"

        # Test dedicated page positioning (key Guillaume fix)
        dedicated_result = create_latex_figure_environment(
            path="FIGURES/dedicated.png",
            caption="Dedicated page figure",
            attributes={"tex_position": "p", "width": "\\textwidth"},
        )

        assert "\\begin{figure*}[p]" in dedicated_result, "Dedicated page should use figure*[p]"
        assert "width=\\textwidth" in dedicated_result, "Should use full textwidth for dedicated page"


if __name__ == "__main__":
    pytest.main([__file__])
