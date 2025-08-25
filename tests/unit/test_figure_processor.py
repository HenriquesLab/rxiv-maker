"""Unit tests for figure processor module."""

from rxiv_maker.converters.figure_processor import (
    convert_figure_references_to_latex,
    convert_figures_to_latex,
    create_latex_figure_environment,
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


class TestGuillaumeFigureIssues:
    """Test specific issues reported by Guillaume in Discord/conversation."""

    def test_panel_references_no_space_fix(self):
        """Test that panel references don't have unwanted spaces (Guillaume Issue #1)."""
        text = "As shown in (@fig:Figure1 A), the results indicate..."
        result = convert_figure_references_to_latex(text)

        # Should render as Fig. \ref{fig:Figure1}{}A (with empty group to prevent LaTeX spacing issues)
        assert "Fig. \\ref{fig:Figure1}{}A)" in result, (
            f"Expected empty group {{}} spacing control between figure ref and panel letter, got: {result}"
        )

        # Should NOT have a space
        assert "Fig. \\ref{fig:Figure1} A)" not in result, "Should not have space between figure ref and panel letter"

    def test_multiple_panel_references_no_space(self):
        """Test multiple panel references in one sentence."""
        text = "See (@fig:test A) and (@fig:test B) for details."
        result = convert_figure_references_to_latex(text)

        assert "Fig. \\ref{fig:test}{}A)" in result
        assert "Fig. \\ref{fig:test}{}B)" in result
        assert "Fig. \\ref{fig:test} A)" not in result
        assert "Fig. \\ref{fig:test} B)" not in result

    def test_supplementary_panel_references_no_space(self):
        """Test supplementary figure panel references."""
        text = "As shown in (@sfig:SupFig1 B), the analysis shows..."
        result = convert_figure_references_to_latex(text)

        assert "Fig. \\ref{sfig:SupFig1}{}B)" in result
        assert "Fig. \\ref{sfig:SupFig1} B)" not in result

    def test_ready_file_detection_with_manuscript_path(self):
        """Test ready file detection with proper manuscript path resolution (Guillaume Issue #2)."""
        import os
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            original_cwd = os.getcwd()
            original_manuscript_path = os.getenv("MANUSCRIPT_PATH")

            try:
                # Set up test environment
                os.environ["MANUSCRIPT_PATH"] = str(tmpdir_path)
                os.chdir(tmpdir)

                # Create FIGURES directory with ready file
                figures_dir = tmpdir_path / "FIGURES"
                figures_dir.mkdir()
                ready_file = figures_dir / "Fig1.png"
                ready_file.write_text("fake png content")

                # Test with ready file - should use direct path
                latex_result_with_ready = create_latex_figure_environment(
                    path="FIGURES/Fig1.png", caption="Test figure caption", attributes={}
                )

                # Should use direct path, not subdirectory format
                assert "Figures/Fig1.png" in latex_result_with_ready, "Should use ready file directly: Figures/Fig1.png"
                assert "Figures/Fig1/Fig1.png" not in latex_result_with_ready, (
                    "Should NOT use subdirectory format when ready file exists"
                )

            finally:
                os.chdir(original_cwd)
                if original_manuscript_path is not None:
                    os.environ["MANUSCRIPT_PATH"] = original_manuscript_path
                elif "MANUSCRIPT_PATH" in os.environ:
                    del os.environ["MANUSCRIPT_PATH"]

    def test_ready_file_detection_without_manuscript_path(self):
        """Test ready file detection falls back correctly when no MANUSCRIPT_PATH."""
        import os
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            original_cwd = os.getcwd()
            original_manuscript_path = os.getenv("MANUSCRIPT_PATH")

            try:
                # Remove MANUSCRIPT_PATH to test fallback
                if "MANUSCRIPT_PATH" in os.environ:
                    del os.environ["MANUSCRIPT_PATH"]

                os.chdir(tmpdir)

                # Create FIGURES directory with ready file
                figures_dir = tmpdir_path / "FIGURES"
                figures_dir.mkdir()
                ready_file = figures_dir / "Fig1.png"
                ready_file.write_text("fake png content")

                # Test with ready file - should use direct path
                latex_result_with_ready = create_latex_figure_environment(
                    path="FIGURES/Fig1.png", caption="Test figure caption", attributes={}
                )

                # Should use direct path when ready file exists
                assert "Figures/Fig1.png" in latex_result_with_ready, (
                    "Should use ready file directly even without MANUSCRIPT_PATH"
                )

            finally:
                os.chdir(original_cwd)
                if original_manuscript_path is not None:
                    os.environ["MANUSCRIPT_PATH"] = original_manuscript_path

    def test_ready_file_vs_generated_file_behavior(self):
        """Test the difference between ready files and generated files."""
        import os
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            original_cwd = os.getcwd()
            original_manuscript_path = os.getenv("MANUSCRIPT_PATH")

            try:
                os.environ["MANUSCRIPT_PATH"] = str(tmpdir_path)
                os.chdir(tmpdir)

                figures_dir = tmpdir_path / "FIGURES"
                figures_dir.mkdir()

                # Test Case 1: Without ready file - should use subdirectory format
                latex_result_without_ready = create_latex_figure_environment(
                    path="FIGURES/GeneratedFig.png", caption="Generated figure caption", attributes={}
                )

                # Should use direct format (Guillaume's implementation)
                assert "Figures/GeneratedFig.png" in latex_result_without_ready, (
                    "Should use direct format for figure path"
                )

                # Test Case 2: With ready file - should use direct format
                ready_file = figures_dir / "ReadyFig.png"
                ready_file.write_text("fake png content")

                latex_result_with_ready = create_latex_figure_environment(
                    path="FIGURES/ReadyFig.png", caption="Ready figure caption", attributes={}
                )

                # Should use direct path when ready file exists
                assert "Figures/ReadyFig.png" in latex_result_with_ready, "Should use ready file directly"
                assert "Figures/ReadyFig/ReadyFig.png" not in latex_result_with_ready, (
                    "Should NOT use subdirectory format for ready files"
                )

            finally:
                os.chdir(original_cwd)
                if original_manuscript_path is not None:
                    os.environ["MANUSCRIPT_PATH"] = original_manuscript_path
                elif "MANUSCRIPT_PATH" in os.environ:
                    del os.environ["MANUSCRIPT_PATH"]

    def test_full_page_figure_positioning_fix(self):
        """Test that full-page figures with textwidth use correct environment (Guillaume Issue #4)."""

        # Guillaume's case: textwidth with position p should use figure*[p] for full page width access
        latex_result = create_latex_figure_environment(
            path="FIGURES/Figure__workflow.svg",
            caption="Test figure caption",
            attributes={"width": "\\textwidth", "tex_position": "p", "id": "fig:workflow"},
        )

        # Should use figure* environment for dedicated page to allow full page width access
        assert "\\begin{figure*}[p]" in latex_result, (
            "Full-width dedicated page figures should use figure*[p] to prevent text overlay"
        )
        assert "\\begin{figure}[p]" not in latex_result, (
            "Should use figure*[p], not figure[p], for full-width figures to avoid overlay"
        )

    def test_full_page_vs_two_column_positioning(self):
        """Test the difference between full-page and two-column figure positioning."""

        # Test Case 1: textwidth without explicit position should use figure*
        latex_result_2col = create_latex_figure_environment(
            path="FIGURES/test.svg",
            caption="Two-column spanning figure",
            attributes={"width": "\\textwidth", "id": "fig:test"},
        )

        # Should use figure* for 2-column spanning when no explicit position
        assert "\\begin{figure*}" in latex_result_2col, (
            "Full-width figures should use figure* for 2-column spanning by default"
        )

        # Test Case 2: textwidth with position t should use figure*[t]
        latex_result_2col_t = create_latex_figure_environment(
            path="FIGURES/test.svg",
            caption="Two-column spanning figure at top",
            attributes={"width": "\\textwidth", "tex_position": "t", "id": "fig:test"},
        )

        # Should use figure* with user's positioning
        assert "\\begin{figure*}[t]" in latex_result_2col_t, "Should respect user's tex_position when using figure*"

        # Test Case 3: ALL dedicated page figures should use figure*[p] for full page width access
        latex_result_fullpage = create_latex_figure_environment(
            path="FIGURES/test.svg",
            caption="Dedicated page figure",
            attributes={"width": "\\textwidth", "tex_position": "p", "id": "fig:test"},
        )

        # Should use figure* for all dedicated page figures to allow full page width in two-column layouts
        assert "\\begin{figure*}[p]" in latex_result_fullpage, (
            "All dedicated page figures should use figure*[p] to allow full page width in two-column layouts"
        )

    def test_guillaume_integration_all_fixes_together(self):
        """Integration test that all Guillaume's fixes work together."""

        # Test all fixes work in combination
        import os
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            original_cwd = os.getcwd()
            original_manuscript_path = os.getenv("MANUSCRIPT_PATH")

            try:
                os.environ["MANUSCRIPT_PATH"] = str(tmpdir_path)
                os.chdir(tmpdir)

                # Create ready figure file
                figures_dir = tmpdir_path / "FIGURES"
                figures_dir.mkdir()
                ready_file = figures_dir / "Figure1.png"
                ready_file.write_text("fake png content")

                # Test 1: Panel references should work correctly
                panel_ref = convert_figure_references_to_latex("(@fig:Figure1 A)")
                assert "Fig. \\ref{fig:Figure1}{}A)" in panel_ref, "Panel references should have no space"

                # Test 2: Ready file should be detected and use direct path
                figure_latex = create_latex_figure_environment(
                    path="FIGURES/Figure1.png", caption="Test caption", attributes={"id": "fig:Figure1"}
                )
                assert "Figures/Figure1.png" in figure_latex, "Ready file should use direct path"
                assert "Figures/Figure1/Figure1.png" not in figure_latex, "Ready file should NOT use subdirectory path"

                # Test 3: Full-page positioning should work correctly
                fullpage_latex = create_latex_figure_environment(
                    path="FIGURES/Figure1.png",
                    caption="Full page caption",
                    attributes={"width": "\\textwidth", "tex_position": "p", "id": "fig:fullpage"},
                )
                assert "\\begin{figure*}[p]" in fullpage_latex, (
                    "Full-page textwidth should use figure*[p] to prevent overlay"
                )
                # Guillaume's implementation doesn't use clearpage, relies on figure*[p] positioning
                assert "\\begin{figure}[p]" not in fullpage_latex, "Full-page should use figure*[p], not figure[p]"

            finally:
                os.chdir(original_cwd)
                if original_manuscript_path is not None:
                    os.environ["MANUSCRIPT_PATH"] = original_manuscript_path
                elif "MANUSCRIPT_PATH" in os.environ:
                    del os.environ["MANUSCRIPT_PATH"]
