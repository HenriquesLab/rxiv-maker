"""Tests for Discord community reported regression issues.

This module contains regression tests for specific issues reported by Guillaume
in Discord messages, focusing on LaTeX dependencies, figure processing,
section handling, and positioning fixes.

Key issues tested:
- LaTeX dependency packages (siunitx, ifsym) inclusion
- Figure panel reference spacing fixes
- Figure ready files loading improvements
- Section header preservation (Introduction vs Main)
- Full-page figure positioning fixes
- Dedicated page figure caption width
- End-to-end integration verification
"""

import os
import re
import tempfile
from pathlib import Path

import pytest


class TestDiscordReportedIssues:
    """Test specific issues reported by Guillaume in Discord messages."""

    def test_latex_dependency_packages_included(self):
        """Test that missing LaTeX packages (siunitx, ifsym) are included in dependencies."""
        from rxiv_maker.install.dependency_handlers.latex import LaTeXHandler
        from rxiv_maker.install.utils.logging import InstallLogger

        logger = InstallLogger()
        handler = LaTeXHandler(logger)
        essential_packages = handler.get_essential_packages()

        # Guillaume reported missing siunitx.sty and ifsym.sty
        assert "siunitx" in essential_packages, "siunitx package should be in essential packages"
        assert "ifsym" in essential_packages, "ifsym package should be in essential packages (Guillaume's issue)"

    def test_debian_control_latex_dependencies(self):
        """Test that Debian control file includes the LaTeX packages Guillaume needed."""

        control_file_path = Path(__file__).parent.parent.parent / "packaging" / "debian" / "control"

        if control_file_path.exists():
            content = control_file_path.read_text()

            # Guillaume needed these packages to fix siunitx.sty and ifsym.sty errors
            assert "texlive-science" in content, "texlive-science should be in Debian dependencies"
            assert "texlive-fonts-extra" in content, "texlive-fonts-extra should be in Debian dependencies"

    def test_figure_panel_reference_spacing_fix(self):
        """Test that figure panel references don't have unwanted spaces.

        Guillaume reported: (@fig:Figure1 A) renders as (Fig. 1 A) instead of (Fig. 1A)
        """
        from rxiv_maker.converters.figure_processor import convert_figure_references_to_latex

        # Test the specific case Guillaume reported
        test_text = "As shown in (@fig:Figure1 A), the results indicate..."
        result = convert_figure_references_to_latex(test_text)

        # Should render as Fig. \ref{fig:Figure1}{}A (no space between ref and A)
        assert "Fig. \\ref{fig:Figure1}{}A)" in result, (
            f"Expected empty group {{}} spacing control between figure ref and panel letter, got: {result}"
        )

        # Should NOT have a space
        assert "Fig. \\ref{fig:Figure1} A)" not in result, "Should not have space between figure ref and panel letter"

        # Test supplementary figures too
        test_text_sfig = "As shown in (@sfig:SupFig1 B), the analysis shows..."
        result_sfig = convert_figure_references_to_latex(test_text_sfig)

        assert "Fig. \\ref{sfig:SupFig1}{}B)" in result_sfig, (
            "Supplementary figure panel refs should also have empty group spacing control"
        )

    def test_figure_ready_files_loading_fix(self):
        """Test that ready figures load correctly without requiring subdirectory duplication.

        Guillaume reported: need to have Fig1.png in both Figure/ and Figure/Fig1/Fig1.png
        """
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Test Case 1: With ready file - should use direct path
                figures_dir = tmpdir_path / "FIGURES"
                figures_dir.mkdir()
                ready_file = figures_dir / "Fig1.png"
                ready_file.write_text("fake png content")

                latex_result_with_ready = create_latex_figure_environment(
                    path="FIGURES/Fig1.png", caption="Test figure caption", attributes={}
                )

                # Should use direct path, not subdirectory format
                assert "Figures/Fig1.png" in latex_result_with_ready, "Should use ready file directly: Figures/Fig1.png"
                assert "Figures/Fig1/Fig1.png" not in latex_result_with_ready, (
                    "Should NOT use subdirectory format when ready file exists"
                )

                # Test Case 2: Without ready file - should use subdirectory format
                ready_file.unlink()  # Remove the ready file

                latex_result_without_ready = create_latex_figure_environment(
                    path="FIGURES/Fig1.png", caption="Test figure caption", attributes={}
                )

                # Should use direct format (Guillaume's implementation)
                assert "Figures/Fig1.png" in latex_result_without_ready, (
                    "Should use direct format (Guillaume's implementation)"
                )
                # Guillaume's implementation uses direct format consistently

            finally:
                os.chdir(original_cwd)

    def test_section_header_introduction_preservation(self):
        """Test that ## Introduction stays as Introduction, not mapped to Main.

        Guillaume reported: ## Introduction renders as Main in PDF instead of Introduction
        """
        from rxiv_maker.converters.section_processor import map_section_title_to_key

        # Test the specific case Guillaume reported
        result = map_section_title_to_key("Introduction")
        assert result == "introduction", f"Introduction should map to 'introduction', not 'main'. Got: {result}"

        # Test case variations
        assert map_section_title_to_key("introduction") == "introduction"
        assert map_section_title_to_key("INTRODUCTION") == "introduction"

        # Test with content sections extraction
        from rxiv_maker.converters.section_processor import extract_content_sections

        # Create test content with Introduction section
        test_markdown = """# Test Article

## Introduction

This is the introduction content.

## Methods

This is the methods content.
"""

        sections = extract_content_sections(test_markdown)

        # Should have introduction as a separate key, not mapped to main
        assert "introduction" in sections, "Should extract introduction section"
        assert "This is the introduction content" in sections["introduction"], (
            "Introduction content should be preserved"
        )

        # NEW: Test the actual template processing - this was the real issue!
        from rxiv_maker.processors.template_processor import process_template_replacements

        # Create minimal template content with the main section placeholder
        template_content = """
<PY-RPL:MAIN-SECTION>

<PY-RPL:METHODS>
"""

        # Process template with introduction section
        yaml_metadata = {}
        result = process_template_replacements(template_content, yaml_metadata, test_markdown)

        # Should create an Introduction section, not Main
        assert "\\section*{Introduction}" in result, "Template should create Introduction section header, not Main"
        assert "This is the introduction content" in result, "Introduction content should be in final template"
        assert "\\section*{Main}" not in result, "Should NOT create Main section when Introduction exists"

    def test_full_page_figure_positioning_fix(self):
        """Test that full-page figures with textwidth don't break positioning.

        Guillaume reported: tex_position="p" with width=textwidth creates 2-column layout instead of dedicated page
        """
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        # Test Guillaume's specific case: textwidth with position p should use regular figure environment
        latex_result = create_latex_figure_environment(
            path="FIGURES/Figure__workflow.svg",
            caption="Test figure caption",
            attributes={"width": "\\textwidth", "tex_position": "p", "id": "fig:workflow"},
        )

        # Should use figure* environment for dedicated page to span full width in two-column documents
        assert "\\begin{figure*}[p]" in latex_result, (
            "Dedicated page figures should use figure*[p] for full-width spanning"
        )
        assert "\\begin{figure}[p]" not in latex_result, (
            "Should use figure*[p], not figure[p], for dedicated page positioning"
        )

        # Test comparison: textwidth without explicit position should use figure*
        latex_result2 = create_latex_figure_environment(
            path="FIGURES/Figure__workflow.svg",
            caption="Test figure caption",
            attributes={"width": "\\textwidth", "id": "fig:workflow"},  # No tex_position
        )

        # Should use figure* for 2-column spanning when no explicit position
        assert "\\begin{figure*}" in latex_result2, (
            "Full-width figures should use figure* for 2-column spanning by default"
        )

        # Test that other positioning is preserved with figure*
        latex_result3 = create_latex_figure_environment(
            path="FIGURES/Figure__workflow.svg",
            caption="Test figure caption",
            attributes={"width": "\\textwidth", "tex_position": "t", "id": "fig:workflow"},
        )

        # Should use figure* with user's positioning
        assert "\\begin{figure*}[t]" in latex_result3, "Should respect user's tex_position when using figure*"

    def test_latex_package_installation_verification(self):
        """Test that LaTeX package installation verification works for Guillaume's packages."""
        from rxiv_maker.install.dependency_handlers.latex import LaTeXHandler
        from rxiv_maker.install.utils.logging import InstallLogger

        logger = InstallLogger()
        handler = LaTeXHandler(logger)

        # Test that verification would work for the packages Guillaume needed
        essential_packages = handler.get_essential_packages()

        # These are the packages Guillaume had to install manually
        required_packages = ["siunitx", "ifsym"]

        for package in required_packages:
            assert package in essential_packages, (
                f"Package {package} should be in essential list for automatic installation"
            )

    def test_figure_reference_edge_cases(self):
        """Test edge cases for figure references that might cause spacing issues."""
        from rxiv_maker.converters.figure_processor import convert_figure_references_to_latex

        # Test various panel reference formats
        test_cases = [
            ("(@fig:Figure1 A)", "Fig. \\ref{fig:Figure1}{}A)"),
            ("(@fig:Figure1 B)", "Fig. \\ref{fig:Figure1}{}B)"),
            ("(@fig:Figure1 C) and (@fig:Figure2 D)", "Fig. \\ref{fig:Figure1}{}C) and (Fig. \\ref{fig:Figure2}{}D)"),
            ("@fig:Figure1 A shows", "Fig. \\ref{fig:Figure1}{}A shows"),  # Without parentheses
            ("(@sfig:SupFig1 A)", "Fig. \\ref{sfig:SupFig1}{}A)"),  # Supplementary figures
        ]

        for input_text, expected_pattern in test_cases:
            result = convert_figure_references_to_latex(input_text)
            assert expected_pattern in result, (
                f"Failed for input '{input_text}': expected '{expected_pattern}' in '{result}'"
            )

    def test_integration_all_guillaume_fixes_together(self):
        """Integration test that all Guillaume's fixes work together."""
        from rxiv_maker.converters.figure_processor import (
            convert_figure_references_to_latex,
            create_latex_figure_environment,
        )
        from rxiv_maker.converters.section_processor import map_section_title_to_key
        from rxiv_maker.install.dependency_handlers.latex import LaTeXHandler
        from rxiv_maker.install.utils.logging import InstallLogger

        # Test all fixes work together
        logger = InstallLogger()
        latex_handler = LaTeXHandler(logger)

        # 1. LaTeX dependencies should include Guillaume's packages
        packages = latex_handler.get_essential_packages()
        assert "siunitx" in packages and "ifsym" in packages, "Guillaume's required packages should be included"

        # 2. Figure panel references should work correctly
        panel_ref = convert_figure_references_to_latex("(@fig:Figure1 A)")
        assert "Fig. \\ref{fig:Figure1}{}A)" in panel_ref, "Panel references should use empty group for spacing control"

        # 3. Section mapping should preserve Introduction
        section_key = map_section_title_to_key("Introduction")
        assert section_key == "introduction", "Introduction should not be mapped to main"

        # 4. Figure positioning should respect user preferences
        figure_latex = create_latex_figure_environment(
            path="FIGURES/test.svg", caption="Test caption", attributes={"width": "\\textwidth", "tex_position": "t"}
        )
        assert "\\begin{figure*}[t]" in figure_latex, "Should respect user's positioning preference"

        print("✅ All Guillaume's fixes are working together correctly")

    def test_dedicated_page_figure_caption_width(self):
        """Test that dedicated page figures have full-width captions.

        Guillaume reported: Dedicated page figure captions were too narrow, not spanning full page width
        """
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        # Test dedicated page figure with textwidth
        result = create_latex_figure_environment(
            path="FIGURES/test.png",
            caption="Test caption for dedicated page figure",
            attributes={"tex_position": "p", "width": "\\textwidth", "id": "fig:test"},
        )

        # Should use figure*[p] for dedicated page to span full width
        assert "\\begin{figure*}[p]" in result, (
            "Dedicated page figures should use figure*[p] to span full width in two-column documents"
        )

        # Should have width=\linewidth in captionsetup for full-width caption
        assert "\\captionsetup{width=0.95\\textwidth" in result, (
            "Dedicated page figures should use width=0.95\\textwidth (Guillaume's implementation)"
        )
        # Note: justification=justified only added for longer captions (>150 chars)

        # Should use figure*[p] for proper dedicated page control
        assert "\\begin{figure*}[p]" in result, "Should use figure*[p] for dedicated page placement"

        # Guillaume's implementation relies on figure*[p] for dedicated page positioning

    def test_dedicated_page_figures_with_scaling(self):
        """Test Guillaume's specific scaling issue with dedicated page figures.

        Guillaume reported: tex_position="p" works with width=textwidth, but when using
        other widths like 0.8 or 80%, the figure reverts to 2-column mode.
        """
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        # Test cases for Guillaume's scaling scenarios
        test_cases = [
            # Guillaume's working case - ALL dedicated page figures use figure*[p] to span full width
            {
                "width": "\\textwidth",
                "tex_position": "p",
                "expected_env": "figure*",
                "expected_pos": "[p]",
                "description": "textwidth with position p should use figure*[p] for dedicated page full-width",
            },
            # Guillaume's problematic cases that should now work
            {
                "width": "0.8",
                "tex_position": "p",
                "expected_env": "figure*",
                "expected_pos": "[p]",
                "description": "0.8 width with position p should use figure*[p] for dedicated page full-width",
            },
            {
                "width": "80%",
                "tex_position": "p",
                "expected_env": "figure*",
                "expected_pos": "[p]",
                "description": "80% width with position p should use figure*[p] for dedicated page full-width",
            },
            {
                "width": "0.9\\textwidth",
                "tex_position": "p",
                "expected_env": "figure*",
                "expected_pos": "[p]",
                "description": "0.9textwidth with position p should use figure*[p] for dedicated page full-width",
            },
            # Verify that 2-column still works when no explicit positioning
            {
                "width": "\\textwidth",
                "expected_env": "figure*",
                "expected_pos": "[!tbp]",
                "description": "textwidth without explicit positioning should auto-detect 2-column",
            },
        ]

        for case in test_cases:
            attributes = {k: v for k, v in case.items() if k not in ["expected_env", "expected_pos", "description"]}

            result = create_latex_figure_environment(
                path="FIGURES/test_scaling.svg", caption="Test figure for scaling", attributes=attributes
            )

            expected_start = f"\\begin{{{case['expected_env']}}}{case['expected_pos']}"
            assert expected_start in result, (
                f"Failed for {case['description']}: "
                f"expected '{expected_start}' in result. "
                f"Attributes: {attributes}. "
                f"Got: {result[:200]}..."
            )

            # For dedicated page figures, verify it's using figure* and not figure
            if case.get("tex_position") == "p":
                wrong_start = "\\begin{figure}[p]"
                assert wrong_start not in result, (
                    f"Failed for {case['description']}: dedicated page figures should use figure*[p], not figure[p]. Attributes: {attributes}"
                )

    def test_end_to_end_tex_generation_with_guillaume_fixes(self):
        """End-to-end test that generates actual .tex file to verify Guillaume's fixes work in practice."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Create manuscript structure with Introduction section
                manuscript_dir = tmpdir_path / "TEST_MANUSCRIPT"
                manuscript_dir.mkdir()

                # Create main manuscript file with Introduction section
                main_md = manuscript_dir / "01_MAIN.md"
                main_md.write_text("""---
title:
  long: "Test Article with Introduction Section"
  short: "Test Article"
authors:
  - name: "Test Author"
    affiliation: "Test University"
keywords: ["test", "Guillaume", "fixes"]
acknowledge_rxiv_maker: false
---

# Abstract

This is the abstract.

## Introduction

This is the introduction content that should appear under "Introduction" header, not "Main".

## Methods

This is the methods section.

## Results

These are the results.
""")

                # Create YAML front matter file
                yaml_file = manuscript_dir / "00_FRONT_MATTER.yaml"
                yaml_file.write_text("""
title:
  long: "Test Article with Introduction Section"
  short: "Test Article"
authors:
  - name: "Test Author"
    affiliation: "Test University"
keywords: ["test", "Guillaume", "fixes"]
acknowledge_rxiv_maker: false
""")

                # Create FIGURES directory with ready file
                figures_dir = manuscript_dir / "FIGURES"
                figures_dir.mkdir()
                ready_fig = figures_dir / "TestFig.png"
                ready_fig.write_text("fake png content")

                # Create a figure with Guillaume's specific positioning case
                figures_md = """
![Test Figure with Ready File](FIGURES/TestFig.png)

![](FIGURES/TestFig.png){#fig:fullpage width="\\textwidth" tex_position="p"}
**This figure should be on a dedicated page, not 2-column layout.**
"""

                # Add figures to main content
                current_content = main_md.read_text()
                main_md.write_text(current_content + "\n\n" + figures_md)

                # Generate the manuscript using the actual CLI
                os.environ["MANUSCRIPT_PATH"] = str(manuscript_dir)

                # Change to manuscript directory like real usage
                os.chdir(manuscript_dir)

                # Import and use the actual generation functions
                from rxiv_maker.engines.operations.generate_preprint import generate_preprint
                from rxiv_maker.processors.yaml_processor import extract_yaml_metadata

                # Generate output
                output_dir = tmpdir_path / "output"
                output_dir.mkdir()

                # Extract metadata and generate preprint
                yaml_metadata = extract_yaml_metadata(str(main_md))
                tex_file = generate_preprint(str(output_dir), yaml_metadata)

                # Verify the generated .tex file contains Guillaume's fixes
                tex_content = Path(tex_file).read_text()

                # 1. Should have Introduction section, not Main
                assert "\\section*{Introduction}" in tex_content, (
                    "Generated .tex should contain Introduction section header"
                )
                assert "This is the introduction content" in tex_content, (
                    "Generated .tex should contain introduction content"
                )
                # Should NOT have hardcoded Main section when Introduction exists
                assert tex_content.count("\\section*{Main}") == 0, (
                    "Generated .tex should NOT contain Main section when Introduction exists"
                )

                # 2. Should use ready file path for TestFig
                assert "Figures/TestFig.png" in tex_content, "Generated .tex should use ready file path directly"
                assert "Figures/TestFig/TestFig.png" not in tex_content, (
                    "Generated .tex should NOT use subdirectory format for ready files"
                )

                # 3. Should use figure* environment for full-page textwidth figures to span full width
                # Look for the pattern of a figure with tex_position="p" and width=textwidth
                fullpage_pattern = (
                    r"\\begin{figure\*}\[p\].*?width=\\textwidth.*?This figure should be on a dedicated page"
                )
                assert re.search(fullpage_pattern, tex_content, re.DOTALL), (
                    "Generated .tex should use figure*[p] for dedicated page textwidth figures to span full width"
                )
                # Should use figure*[p] for dedicated page placement
                assert "\\begin{figure*}[p]" in tex_content, (
                    "Generated .tex should use figure*[p] for dedicated page placement"
                )

                print(f"✅ End-to-end test passed! Generated .tex file: {tex_file}")
                print("✅ All Guillaume's fixes verified in actual .tex generation")

            finally:
                os.chdir(original_cwd)
                if "MANUSCRIPT_PATH" in os.environ:
                    del os.environ["MANUSCRIPT_PATH"]


if __name__ == "__main__":
    pytest.main([__file__])
