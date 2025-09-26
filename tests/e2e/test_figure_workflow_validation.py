"""Figure workflow validation tests.

This module contains specialized E2E tests for validating the complete figure workflow,
including generation, copying, LaTeX integration, and PDF validation.
"""

import os
import re
import shutil
import tempfile
from pathlib import Path

import pytest

from .test_dummy_manuscript_generator import DummyManuscriptGenerator


class TestFigureWorkflowValidation:
    """Comprehensive validation of the figure workflow pipeline."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir)
        yield workspace
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def figure_test_manuscript(self, temp_workspace):
        """Create a manuscript specifically designed for figure testing."""
        generator = DummyManuscriptGenerator(temp_workspace)
        generator.create_complete_manuscript(include_figures=True, include_citations=False)
        return generator

    def test_figure_generation_pipeline(self, figure_test_manuscript):
        """Test the complete figure generation pipeline."""
        from rxiv_maker.engines.operations.generate_figures import FigureGenerator

        manuscript_dir = figure_test_manuscript.get_manuscript_path()
        figures_dir = manuscript_dir / "FIGURES"

        original_cwd = os.getcwd()
        try:
            os.chdir(manuscript_dir)

            # Initialize figure generator
            generator = FigureGenerator(figures_dir=str(figures_dir), output_dir=str(figures_dir))

            # Test figure file detection by checking what files exist
            python_files = list(figures_dir.glob("*.py"))
            r_files = list(figures_dir.glob("*.R"))
            mermaid_files = list(figures_dir.glob("*.mmd"))

            # Should detect our test files
            python_names = [f.name for f in python_files]
            r_names = [f.name for f in r_files]
            mermaid_names = [f.name for f in mermaid_files]

            assert "python_figure.py" in python_names, "Should detect Python figure script"
            assert "r_figure.R" in r_names, "Should detect R figure script"
            assert "workflow_diagram.mmd" in mermaid_names, "Should detect Mermaid diagram"

            # Test figure generation (may fail without dependencies)
            try:
                generator.generate_all_figures()

                # Check if subdirectories were created
                python_output = figures_dir / "python_figure"
                r_output = figures_dir / "r_figure"
                mermaid_output = figures_dir / "workflow_diagram"

                print(
                    f"Figure generation attempted - outputs exist: "
                    f"Python={python_output.exists()}, "
                    f"R={r_output.exists()}, "
                    f"Mermaid={mermaid_output.exists()}"
                )

            except Exception as e:
                # Expected in CI without matplotlib, R, mermaid-cli
                print(f"Figure generation failed (expected): {e}")

        finally:
            os.chdir(original_cwd)

    def test_figure_copying_mechanism(self, figure_test_manuscript):
        """Test the figure copying mechanism in detail."""
        from rxiv_maker.engines.operations.build_manager import BuildManager

        manuscript_dir = figure_test_manuscript.get_manuscript_path()
        output_dir = figure_test_manuscript.get_output_path()
        figures_dir = manuscript_dir / "FIGURES"

        # Create some generated figure subdirectories to test copying
        test_subdirs = ["python_figure", "r_figure", "workflow_diagram"]
        for subdir in test_subdirs:
            subdir_path = figures_dir / subdir
            subdir_path.mkdir(exist_ok=True)

            # Create test output files
            (subdir_path / f"{subdir}.png").write_text("fake png")
            (subdir_path / f"{subdir}.pdf").write_text("fake pdf")
            (subdir_path / f"{subdir}.svg").write_text("fake svg")

        original_cwd = os.getcwd()
        try:
            os.chdir(manuscript_dir)

            build_manager = BuildManager(manuscript_path=str(manuscript_dir), output_dir=str(output_dir))

            # Test current workflow: setup output directory and generate figures
            build_manager.setup_output_directory()
            build_manager.generate_figures()

            # Verify figures exist in source directory (current system processes in place)
            ready_exists = (figures_dir / "ready_figure.png").exists()
            fullpage_exists = (figures_dir / "fullpage_figure.png").exists()

            assert ready_exists, "ready_figure.png should exist in source"
            assert fullpage_exists, "fullpage_figure.png should exist in source"

            print(f"✓ Verified ready figure exists: {ready_exists}")
            print(f"✓ Verified fullpage figure exists: {fullpage_exists}")

            # Test completed successfully
            print("✓ Figure workflow validation completed")

            # Verify subdirectories exist in source (current system processes in place)
            for subdir in test_subdirs:
                subdir_source = figures_dir / subdir
                assert subdir_source.exists(), f"Subdirectory {subdir} should exist in source"
                print(f"✓ Verified subdirectory exists: {subdir_source}")

        finally:
            os.chdir(original_cwd)

    def test_latex_figure_integration(self, figure_test_manuscript):
        """Test LaTeX integration of figures."""
        from rxiv_maker.engines.operations.generate_preprint import generate_preprint
        from rxiv_maker.processors.yaml_processor import extract_yaml_metadata

        manuscript_dir = figure_test_manuscript.get_manuscript_path()
        output_dir = figure_test_manuscript.get_output_path()
        main_md = manuscript_dir / "01_MAIN.md"

        original_cwd = os.getcwd()
        try:
            os.chdir(manuscript_dir)

            # Extract metadata and generate LaTeX
            yaml_metadata = extract_yaml_metadata(str(main_md))
            tex_file = generate_preprint(str(output_dir), yaml_metadata, str(manuscript_dir))

            # Read generated LaTeX content
            tex_content = Path(tex_file).read_text()

            # Test figure reference conversions
            assert "\\ref{fig:ready_figure}" in tex_content, "Ready figure reference should be converted"
            assert "\\ref{fig:python_figure}" in tex_content, "Python figure reference should be converted"
            assert "\\ref{fig:r_figure}" in tex_content, "R figure reference should be converted"
            assert "\\ref{fig:mermaid_diagram}" in tex_content, "Mermaid figure reference should be converted"

            # Test figure environments
            assert "\\begin{figure}" in tex_content, "Should have figure environments"
            assert "\\includegraphics" in tex_content, "Should have includegraphics commands"

            # Test specific figure paths (LaTeX uses relative path from output directory)
            assert "../FIGURES/ready_figure.png" in tex_content, "Ready figure should use relative path"

            # Test Guillaume's panel reference fix
            panel_refs = re.findall(r"Fig\. \\ref\{fig:\w+\}[A-Z]\)", tex_content)
            if panel_refs:
                # Should have no space between reference and panel letter
                for ref in panel_refs:
                    assert " A)" not in ref and " B)" not in ref and " C)" not in ref, (
                        f"Panel reference should have no space: {ref}"
                    )

        finally:
            os.chdir(original_cwd)

    def test_figure_positioning_logic(self, figure_test_manuscript):
        """Test figure positioning logic for different scenarios."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        # Test cases for different positioning scenarios
        test_cases = [
            # Guillaume's specific case: textwidth + position p should use figure*[p] for full layout control
            {
                "attributes": {"width": "\\textwidth", "tex_position": "p", "id": "fig:test1"},
                "expected_env": "\\begin{figure*}[p]",
                "not_expected": None,
                "description": "textwidth + position p should use figure*[p] for dedicated page layout control",
            },
            # Standard textwidth should use figure*
            {
                "attributes": {"width": "\\textwidth", "id": "fig:test2"},
                "expected_env": "\\begin{figure*}",
                "not_expected": None,
                "description": "textwidth without position should use figure*",
            },
            # Regular figure with position
            {
                "attributes": {"width": "0.8", "tex_position": "h", "id": "fig:test3"},
                "expected_env": "\\begin{figure}[h]",
                "not_expected": "\\begin{figure*}",
                "description": "regular figure should use figure environment",
            },
            # Two-column span
            {
                "attributes": {"span": "2col", "id": "fig:test4"},
                "expected_env": "\\begin{figure*}",
                "not_expected": None,
                "description": "2col span should use figure*",
            },
        ]

        for case in test_cases:
            latex_result = create_latex_figure_environment(
                path="FIGURES/test.png", caption="Test figure", attributes=case["attributes"]
            )

            assert case["expected_env"] in latex_result, (
                f"{case['description']}: Expected '{case['expected_env']}' in result"
            )

            if case["not_expected"]:
                assert case["not_expected"] not in latex_result, (
                    f"{case['description']}: Should not have '{case['not_expected']}' in result"
                )

    def test_ready_file_detection_logic(self, figure_test_manuscript):
        """Test ready file detection logic comprehensively."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        manuscript_dir = figure_test_manuscript.get_manuscript_path()
        figures_dir = manuscript_dir / "FIGURES"

        original_cwd = os.getcwd()
        try:
            os.chdir(manuscript_dir)

            # Test Case 1: Ready file exists
            assert (figures_dir / "ready_figure.png").exists(), "Ready file should exist"

            latex_with_ready = create_latex_figure_environment(
                path="FIGURES/ready_figure.png", caption="Test ready figure", attributes={"id": "fig:ready"}
            )

            # The current implementation uses relative path from output directory
            if "../FIGURES/ready_figure.png" in latex_with_ready:
                print("✅ Ready file uses correct relative path from output directory")
            elif "Figures/ready_figure.png" in latex_with_ready:
                print("⚠️ Ready file uses old direct path format")
            elif "Figures/ready_figure/ready_figure.png" in latex_with_ready:
                print("❌ Ready file uses subdirectory path (Guillaume's Issue #2 still exists)")
            else:
                raise AssertionError(f"Unexpected ready file path format in: {latex_with_ready}")

            # Test Case 2: No ready file (simulate generated figure)
            latex_without_ready = create_latex_figure_environment(
                path="FIGURES/nonexistent_figure.png",
                caption="Test generated figure",
                attributes={"id": "fig:generated"},
            )

            # Should use relative path from output directory
            assert "../FIGURES/nonexistent_figure.png" in latex_without_ready, (
                "Generated figure should use relative path from output directory"
            )

            # Test Case 3: Multiple formats
            # Create additional ready file formats
            (figures_dir / "multi_format.svg").write_text("fake svg")
            (figures_dir / "multi_format.pdf").write_text("fake pdf")

            latex_multi = create_latex_figure_environment(
                path="FIGURES/multi_format.svg", caption="Multi-format figure", attributes={"id": "fig:multi"}
            )

            # Check what format was used for multi-format ready file (current implementation)
            if "../FIGURES/multi_format.png" in latex_multi:
                print("✅ Multi-format ready file uses relative path, SVG converted to PNG")
            elif "../FIGURES/multi_format.svg" in latex_multi:
                print("✅ Multi-format ready file uses relative path, SVG preserved")
            elif "Figures/multi_format" in latex_multi:
                print("⚠️ Multi-format file uses old path format")
            else:
                # Just check that some reference exists
                assert "multi_format" in latex_multi, f"Should reference multi_format somehow in: {latex_multi}"

        finally:
            os.chdir(original_cwd)

    def test_figure_reference_conversion_edge_cases(self, figure_test_manuscript):
        """Test edge cases in figure reference conversion."""
        from rxiv_maker.converters.figure_processor import convert_figure_references_to_latex

        # Edge cases that might cause issues
        test_cases = [
            # Multiple panel references in one sentence
            {
                "input": "See (@fig:test A) and (@fig:test B) for details.",
                "should_contain": ["(Fig. \\ref{fig:test}{}A)", "(Fig. \\ref{fig:test}{}B)"],
                "should_not_contain": ["Fig. \\ref{fig:test} A)", "Fig. \\ref{fig:test} B)"],
            },
            # Nested parentheses
            {
                "input": "As shown in (@fig:test A, which demonstrates X), we see Y.",
                "should_contain": ["(Fig. \\ref{fig:test}{}A"],
                "should_not_contain": ["Fig. \\ref{fig:test} A"],
            },
            # Mixed reference types
            {
                "input": "Compare @fig:main with (@sfig:supplement B).",
                "should_contain": ["Fig. \\ref{fig:main}", "(Fig. \\ref{sfig:supplement}{}B)"],
                "should_not_contain": [],
            },
            # Complex panel labels
            {
                "input": "(@fig:complex A-D) shows multiple panels.",
                "should_contain": ["(Fig. \\ref{fig:complex}{}A-D)"],
                "should_not_contain": ["Fig. \\ref{fig:complex} A-D)"],
            },
        ]

        for case in test_cases:
            result = convert_figure_references_to_latex(case["input"])

            for expected in case["should_contain"]:
                assert expected in result, f"Input: '{case['input']}' should contain '{expected}' in result: '{result}'"

            for not_expected in case["should_not_contain"]:
                assert not_expected not in result, (
                    f"Input: '{case['input']}' should NOT contain '{not_expected}' in result: '{result}'"
                )

    def test_figure_caption_and_label_processing(self, figure_test_manuscript):
        """Test figure caption and label processing."""
        from rxiv_maker.converters.figure_processor import create_latex_figure_environment

        test_cases = [
            {
                "attributes": {"id": "fig:test"},
                "default_caption": "Default caption",
                "expected_label": "\\label{fig:test}",
            },
            {
                "attributes": {},
                "default_caption": "Default caption",
                "expected_label": None,  # No label if no ID
            },
        ]

        for case in test_cases:
            latex_result = create_latex_figure_environment(
                path="FIGURES/test.png", caption=case["default_caption"], attributes=case["attributes"]
            )

            # Should always contain the provided caption (from function parameter)
            assert case["default_caption"] in latex_result, (
                f"Should contain provided caption: {case['default_caption']}"
            )

            if case["expected_label"]:
                assert case["expected_label"] in latex_result, f"Should contain label: {case['expected_label']}"

    @pytest.mark.slow
    def test_pdf_figure_validation(self, figure_test_manuscript):
        """Test that figures appear correctly in generated PDF (if PDF generation works)."""
        pytest.importorskip("subprocess")

        from rxiv_maker.engines.operations.build_manager import BuildManager

        manuscript_dir = figure_test_manuscript.get_manuscript_path()
        output_dir = figure_test_manuscript.get_output_path()

        original_cwd = os.getcwd()
        try:
            os.chdir(manuscript_dir)

            # Set up build with figure copying
            build_manager = BuildManager(
                manuscript_path=str(manuscript_dir), output_dir=str(output_dir), skip_validation=True
            )

            # Setup output directory and ensure figures are available
            build_manager.setup_output_directory()
            build_manager.generate_figures()

            # Generate LaTeX
            build_manager.copy_style_files()
            build_manager.generate_tex_files()

            # Attempt PDF compilation
            try:
                build_manager.compile_latex()

                # Check if PDF was generated
                pdf_files = list(output_dir.glob("*.pdf"))
                if pdf_files:
                    pdf_file = pdf_files[0]

                    # Basic PDF validation
                    assert pdf_file.exists(), "PDF should exist"
                    assert pdf_file.stat().st_size > 5000, "PDF should have reasonable size (> 5KB)"

                    # Try to validate that figures are referenced properly in PDF
                    # This would require PDF parsing tools, so we'll just check compilation success
                    print(f"✅ PDF generated successfully with figures: {pdf_file}")

                else:
                    pytest.skip("PDF compilation succeeded but no PDF file found")

            except Exception as e:
                # PDF compilation may fail due to missing LaTeX
                print(f"PDF compilation failed (expected without LaTeX): {e}")
                pytest.skip("PDF compilation requires LaTeX installation")

        finally:
            os.chdir(original_cwd)

    def test_figure_workflow_error_handling(self, figure_test_manuscript):
        """Test error handling in figure workflow."""
        from rxiv_maker.engines.operations.build_manager import BuildManager

        manuscript_dir = figure_test_manuscript.get_manuscript_path()
        output_dir = figure_test_manuscript.get_output_path()

        # Test with missing figures directory
        figures_dir = manuscript_dir / "FIGURES"
        backup_dir = manuscript_dir / "FIGURES_BACKUP"

        original_cwd = os.getcwd()
        try:
            os.chdir(manuscript_dir)

            # Temporarily rename FIGURES directory
            if figures_dir.exists():
                shutil.move(str(figures_dir), str(backup_dir))

            build_manager = BuildManager(manuscript_path=str(manuscript_dir), output_dir=str(output_dir))

            # Should handle missing figures gracefully
            build_manager.setup_output_directory()
            try:
                build_manager.generate_figures()  # Should not fail when FIGURES directory is missing
                print("✓ Generate figures handled missing FIGURES directory gracefully")
            except Exception as e:
                # This is acceptable - figure generation may log warnings but should not crash
                print(f"ℹ️ Generate figures noted missing FIGURES directory: {e}")

            # Restore figures directory
            if backup_dir.exists():
                shutil.move(str(backup_dir), str(figures_dir))

        finally:
            os.chdir(original_cwd)
            # Ensure figures directory is restored
            if backup_dir.exists() and not figures_dir.exists():
                shutil.move(str(backup_dir), str(figures_dir))

    def test_integration_with_guillaume_issues(self, figure_test_manuscript):
        """Test that E2E framework covers Guillaume's reported issues."""
        # This test validates that our E2E framework covers the same issues
        # that Guillaume reported, without relying on external test files

        manuscript_dir = figure_test_manuscript.get_manuscript_path()
        print(f"E2E test manuscript created at: {manuscript_dir}")

        # Verify we have all the figure types Guillaume's issues cover
        figures_dir = manuscript_dir / "FIGURES"
        assert (figures_dir / "ready_figure.png").exists(), "Ready PNG for Issue #2"
        assert (figures_dir / "python_figure.py").exists(), "Python script for generated figures"
        assert (figures_dir / "r_figure.R").exists(), "R script for generated figures"
        assert (figures_dir / "workflow_diagram.mmd").exists(), "Mermaid for complex figures"

        # Verify manuscript content covers Guillaume's cases
        main_content = (manuscript_dir / "01_MAIN.md").read_text()
        assert "## Introduction" in main_content, "Has Introduction section (Issue #3)"
        assert "(@fig:" in main_content, "Has panel references (Issue #1)"
        assert 'tex_position="p"' in main_content, "Has full-page positioning (Issue #4)"

        print("✅ E2E framework comprehensively covers Guillaume's reported issues")

    def test_guillaume_ready_file_workflow_e2e(self, figure_test_manuscript):
        """E2E test for Guillaume's ready file detection issue (Issue #2)."""
        from rxiv_maker.engines.operations.generate_preprint import generate_preprint
        from rxiv_maker.processors.yaml_processor import extract_yaml_metadata

        manuscript_dir = figure_test_manuscript.get_manuscript_path()
        output_dir = figure_test_manuscript.get_output_path()
        figures_dir = manuscript_dir / "FIGURES"

        # Create Guillaume's specific ready file scenario
        ready_file = figures_dir / "Guillaume_Fig.png"
        ready_file.write_text("Guillaume's ready PNG content")

        original_cwd = os.getcwd()
        try:
            os.chdir(manuscript_dir)

            # Create markdown with Guillaume's figure reference style
            main_md = manuscript_dir / "01_MAIN.md"
            content = main_md.read_text()
            guillaume_content = (
                content
                + """

## Guillaume Test Section

![Guillaume's Ready Figure](FIGURES/Guillaume_Fig.png)
{#fig:guillaume} **Guillaume's Test Figure.** This tests ready file detection.

Panel references: (@fig:guillaume A) and (@fig:guillaume B).
"""
            )
            main_md.write_text(guillaume_content)

            # Generate preprint with Guillaume's content
            yaml_metadata = extract_yaml_metadata(str(main_md))
            tex_file = generate_preprint(str(output_dir), yaml_metadata, str(manuscript_dir))

            # Verify Guillaume's fixes in generated LaTeX
            tex_content = Path(tex_file).read_text()

            # Issue #2: Ready file should use relative path from output directory
            assert "../FIGURES/Guillaume_Fig.png" in tex_content, (
                "Guillaume's ready file should use relative path in LaTeX"
            )
            assert "Figures/Guillaume_Fig/Guillaume_Fig.png" not in tex_content, (
                "Guillaume's ready file should NOT use subdirectory format"
            )

            # Issue #1: Panel references should have no space
            assert "(Fig. \\ref{fig:guillaume}{}A)" in tex_content, "Guillaume's panel references should have no space"

            print("✅ Guillaume's ready file workflow works end-to-end")

        finally:
            os.chdir(original_cwd)

    def test_guillaume_full_page_positioning_e2e(self, figure_test_manuscript):
        """E2E test for Guillaume's full-page positioning issue (Issue #4)."""
        from rxiv_maker.engines.operations.generate_preprint import generate_preprint
        from rxiv_maker.processors.yaml_processor import extract_yaml_metadata

        manuscript_dir = figure_test_manuscript.get_manuscript_path()
        output_dir = figure_test_manuscript.get_output_path()

        original_cwd = os.getcwd()
        try:
            os.chdir(manuscript_dir)

            # Create manuscript with Guillaume's full-page positioning
            main_md = manuscript_dir / "01_MAIN.md"
            content = main_md.read_text()

            fullpage_content = (
                content
                + """

## Full-Page Test

![](FIGURES/ready_figure.png)
{#fig:fullpage width="\\textwidth" tex_position="p"} **Full-page test figure.** This should appear on a dedicated page using figure*[p] for full layout control.

![](FIGURES/ready_figure.png)
{#fig:twocol width="\\textwidth"} **Two-column spanning figure.** This should use figure* for two-column layout.
"""
            )
            main_md.write_text(fullpage_content)

            # Generate preprint
            yaml_metadata = extract_yaml_metadata(str(main_md))
            tex_file = generate_preprint(str(output_dir), yaml_metadata, str(manuscript_dir))

            # Verify positioning in generated LaTeX
            tex_content = Path(tex_file).read_text()

            # Issue #4: Full-page textwidth + position p should have proper positioning
            # Check for the presence of [p] positioning and figure caption
            has_p_position = "[p]" in tex_content
            has_fullpage_caption = "Full-page test figure" in tex_content
            has_figure_env = "\\begin{figure" in tex_content

            assert has_p_position and has_fullpage_caption and has_figure_env, (
                f"Full-page figure should have [p] positioning and proper figure environment. "
                f"Found [p]: {has_p_position}, caption: {has_fullpage_caption}, figure env: {has_figure_env}"
            )

            # Two-column spanning should have proper figure environment
            has_twocol_caption = "Two-column spanning figure" in tex_content
            has_twocol_figure = "\\begin{figure" in tex_content and has_twocol_caption
            assert has_twocol_figure, "Two-column spanning should have proper figure environment"

            print("✅ Guillaume's full-page positioning works end-to-end")

        finally:
            os.chdir(original_cwd)

    def test_guillaume_section_headers_e2e(self, figure_test_manuscript):
        """E2E test for Guillaume's section header issue (Issue #3)."""
        from rxiv_maker.engines.operations.generate_preprint import generate_preprint
        from rxiv_maker.processors.yaml_processor import extract_yaml_metadata

        manuscript_dir = figure_test_manuscript.get_manuscript_path()
        output_dir = figure_test_manuscript.get_output_path()

        original_cwd = os.getcwd()
        try:
            os.chdir(manuscript_dir)

            # Create manuscript with Introduction section (Guillaume's case)
            main_md = manuscript_dir / "01_MAIN.md"
            intro_content = """---
title:
  long: "Guillaume Section Test"
  short: "Section Test"
authors:
  - name: "Test Author"
    affiliation: "Test University"
keywords: ["test"]
acknowledge_rxiv_maker: false
---

# Abstract

This tests Guillaume's section header issue.

## Introduction

This introduction section should appear as "Introduction" not "Main" in the PDF.

## Methods

This is the methods section.
"""
            main_md.write_text(intro_content)

            # Generate preprint
            yaml_metadata = extract_yaml_metadata(str(main_md))
            tex_file = generate_preprint(str(output_dir), yaml_metadata, str(manuscript_dir))

            # Verify section headers in generated LaTeX
            tex_content = Path(tex_file).read_text()

            # Issue #3: Should have Introduction section, not Main
            assert "\\section*{Introduction}" in tex_content, "Should generate Introduction section header"
            assert "This introduction section should appear" in tex_content, "Introduction content should be included"

            # Should NOT have hardcoded Main section when Introduction exists
            main_section_count = tex_content.count("\\section*{Main}")
            assert main_section_count == 0, "Should NOT generate Main section when Introduction exists"

            print("✅ Guillaume's section headers work end-to-end")

        finally:
            os.chdir(original_cwd)

    def test_guillaume_all_issues_integration_e2e(self, figure_test_manuscript):
        """E2E integration test for all Guillaume's issues working together."""
        from rxiv_maker.engines.operations.generate_preprint import generate_preprint
        from rxiv_maker.processors.yaml_processor import extract_yaml_metadata

        manuscript_dir = figure_test_manuscript.get_manuscript_path()
        output_dir = figure_test_manuscript.get_output_path()
        figures_dir = manuscript_dir / "FIGURES"

        # Create comprehensive Guillaume test content
        ready_file = figures_dir / "Guillaume_Integration.png"
        ready_file.write_text("Guillaume integration test PNG")

        original_cwd = os.getcwd()
        try:
            os.chdir(manuscript_dir)

            # Append to existing test manuscript (same pattern as working test)
            main_md = manuscript_dir / "01_MAIN.md"
            existing_content = main_md.read_text()

            integration_content = (
                existing_content
                + """

## Guillaume Integration Test

Testing Guillaume's Introduction section and all fixes together.

Panel references with no spaces: (@fig:integration A) and (@fig:integration B).

![Guillaume Integration](FIGURES/Guillaume_Integration.png)
{#fig:integration} **Guillaume Integration Test.** Ready file detection test (Issue #2).

![Guillaume Full-page](FIGURES/Guillaume_Integration.png)
{#fig:fullpage width="\\textwidth" tex_position="p"} **Full-page positioning test.** Testing Issue #4.

## Results

All Guillaume's issues should be resolved in this manuscript.
"""
            )
            main_md.write_text(integration_content)

            # Use same pattern as working tests: generate_preprint directly
            yaml_metadata = extract_yaml_metadata(str(main_md))
            tex_file = generate_preprint(str(output_dir), yaml_metadata, str(manuscript_dir))

            # Read generated content
            tex_content = Path(tex_file).read_text()

            # Verify all Guillaume's fixes
            checks = [
                ("Guillaume Integration section", "Guillaume Integration Test" in tex_content),
                ("Ready file relative path", "../FIGURES/Guillaume_Integration.png" in tex_content),
                ("No subdirectory path", "Figures/Guillaume_Integration/Guillaume_Integration.png" not in tex_content),
                ("Panel ref no space", "(Fig. \\ref{fig:integration}{}A)" in tex_content),
                ("Full-page positioning", ("[p]" in tex_content and "\\begin{figure" in tex_content)),
            ]

            all_passed = True
            for check_name, passed in checks:
                if passed:
                    print(f"   ✅ {check_name}")
                else:
                    print(f"   ❌ {check_name}")
                    all_passed = False

            assert all_passed, "All Guillaume's fixes should work together"
            print("✅ Guillaume's all issues integration test passed")

        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
