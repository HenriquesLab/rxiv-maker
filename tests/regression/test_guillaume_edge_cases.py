"""Tests for Guillaume's edge case regression issues.

This module contains regression tests for edge case scenarios identified
by Guillaume to prevent regressions in figure processing, path resolution,
and positioning logic.

Key issues tested:
- Mixed ready and generated figures handling
- Panel reference edge cases and spacing
- Complex positioning combinations
- Manuscript path edge cases with nested structures
"""

import os
import tempfile
from pathlib import Path

import pytest


class TestGuillaumeEdgeCases:
    """Test edge cases for Guillaume's issues to prevent regressions."""

    def test_mixed_ready_and_generated_figures(self):
        """Test manuscripts with both ready files and generated figures."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            original_cwd = os.getcwd()
            original_manuscript_path = os.getenv("MANUSCRIPT_PATH")

            try:
                os.environ["MANUSCRIPT_PATH"] = str(tmpdir_path)
                os.chdir(tmpdir)

                # Create FIGURES directory
                figures_dir = tmpdir_path / "FIGURES"
                figures_dir.mkdir()

                # Create one ready file, leave another as generated
                ready_file = figures_dir / "ReadyFig.png"
                ready_file.write_text("ready figure content")

                # Test ready file
                ready_latex = create_latex_figure_environment(
                    path="FIGURES/ReadyFig.png", caption="Ready figure", attributes={}
                )
                assert "Figures/ReadyFig.png" in ready_latex, "Ready file should use direct path"

                # Test generated file (no ready file exists)
                generated_latex = create_latex_figure_environment(
                    path="FIGURES/GeneratedFig.png", caption="Generated figure", attributes={}
                )
                assert "Figures/GeneratedFig.png" in generated_latex, (
                    "Generated file should use direct format (Guillaume's implementation)"
                )

            finally:
                os.chdir(original_cwd)
                if original_manuscript_path is not None:
                    os.environ["MANUSCRIPT_PATH"] = original_manuscript_path
                elif "MANUSCRIPT_PATH" in os.environ:
                    del os.environ["MANUSCRIPT_PATH"]

    def test_panel_references_edge_cases(self):
        """Test panel reference edge cases."""
        from rxiv_maker.converters.figure_processor import convert_figure_references_to_latex

        test_cases = [
            # Multiple panels in sequence - note the {} prevents unwanted spaces after \ref{}
            (
                "(@fig:test A), (@fig:test B), (@fig:test C)",
                "Fig. \\ref{fig:test}{}A), (Fig. \\ref{fig:test}{}B), (Fig. \\ref{fig:test}{}C)",
            ),
            # Mixed with other text
            (
                "As shown in (@fig:test A) and described in (@fig:test B), the results...",
                "Fig. \\ref{fig:test}{}A) and described in (Fig. \\ref{fig:test}{}B)",
            ),
            # Different figure IDs
            ("(@fig:first A) vs (@fig:second B)", "Fig. \\ref{fig:first}{}A) vs (Fig. \\ref{fig:second}{}B)"),
            # Supplementary figures
            ("(@sfig:sup A) and (@sfig:sup B)", "Fig. \\ref{sfig:sup}{}A) and (Fig. \\ref{sfig:sup}{}B)"),
        ]

        for input_text, expected_pattern in test_cases:
            result = convert_figure_references_to_latex(input_text)
            assert expected_pattern in result, f"Failed for: {input_text} -> {result}"

    def test_complex_positioning_combinations(self):
        """Test complex combinations of figure positioning and width."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        test_cases = [
            # Guillaume's specific case - dedicated page figures use figure*[p] for full-width spanning
            {"width": "\\textwidth", "tex_position": "p", "expected_env": "figure*", "expected_pos": "[p]"},
            # Two-column spanning variations
            {"width": "\\textwidth", "expected_env": "figure*", "expected_pos": "[!tbp]"},
            {"width": "\\textwidth", "tex_position": "t", "expected_env": "figure*", "expected_pos": "[t]"},
            {"width": "\\textwidth", "tex_position": "b", "expected_env": "figure*", "expected_pos": "[b]"},
            # Regular figures - dedicated page figures use figure*[p] for full-width spanning
            {"width": "0.8", "tex_position": "p", "expected_env": "figure*", "expected_pos": "[p]"},
            {"width": "\\linewidth", "expected_env": "figure", "expected_pos": "[!htbp]"},
        ]

        for case in test_cases:
            attributes = {k: v for k, v in case.items() if k not in ["expected_env", "expected_pos"]}
            result = create_latex_figure_environment(
                path="FIGURES/test.png", caption="Test caption", attributes=attributes
            )

            expected_start = f"\\begin{{{case['expected_env']}}}{case['expected_pos']}"
            assert expected_start in result, f"Failed for {attributes}: expected {expected_start} in {result}"

    def test_manuscript_path_edge_cases(self):
        """Test edge cases for manuscript path resolution."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            original_cwd = os.getcwd()
            original_manuscript_path = os.getenv("MANUSCRIPT_PATH")

            try:
                # Test with nested manuscript structure
                nested_manuscript = tmpdir_path / "project" / "manuscript"
                nested_manuscript.mkdir(parents=True)
                figures_dir = nested_manuscript / "FIGURES"
                figures_dir.mkdir()

                ready_file = figures_dir / "NestedFig.png"
                ready_file.write_text("nested figure content")

                # Test with MANUSCRIPT_PATH pointing to nested directory
                os.environ["MANUSCRIPT_PATH"] = str(nested_manuscript)
                os.chdir(tmpdir)  # Different from manuscript directory

                result = create_latex_figure_environment(
                    path="FIGURES/NestedFig.png", caption="Nested figure", attributes={}
                )

                assert "Figures/NestedFig.png" in result, "Should handle nested manuscript paths"

            finally:
                os.chdir(original_cwd)
                if original_manuscript_path is not None:
                    os.environ["MANUSCRIPT_PATH"] = original_manuscript_path
                elif "MANUSCRIPT_PATH" in os.environ:
                    del os.environ["MANUSCRIPT_PATH"]


if __name__ == "__main__":
    pytest.main([__file__])
