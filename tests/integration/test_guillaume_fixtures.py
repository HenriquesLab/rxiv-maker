"""Integration tests using Guillaume's test manuscript fixture."""

import sys
from pathlib import Path

import pytest

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rxiv_maker.converters.figure_processor import convert_figure_references_to_latex


class TestGuillaumeFixtures:
    """Tests using the Guillaume test manuscript fixture."""

    @pytest.fixture
    def guillaume_manuscript_dir(self):
        """Provide path to Guillaume test manuscript fixture."""
        fixture_dir = Path(__file__).parent.parent / "fixtures"
        return fixture_dir

    def test_guillaume_fixture_exists(self, guillaume_manuscript_dir):
        """Test that Guillaume fixture exists and has expected structure."""
        assert guillaume_manuscript_dir.exists(), "Guillaume fixture directory should exist"

        # Check main files
        assert (guillaume_manuscript_dir / "01_MAIN.md").exists(), "Main manuscript should exist"
        assert (guillaume_manuscript_dir / "00_CONFIG.yml").exists(), "Config should exist"
        assert (guillaume_manuscript_dir / "03_REFERENCES.bib").exists(), "References should exist"

        # Check figures
        figures_dir = guillaume_manuscript_dir / "FIGURES"
        assert figures_dir.exists(), "FIGURES directory should exist"

        expected_figures = ["Fig1.png", "Fig2.png"]
        for fig in expected_figures:
            assert (figures_dir / fig).exists(), f"Figure {fig} should exist"

    def test_guillaume_manuscript_content(self, guillaume_manuscript_dir):
        """Test that Guillaume manuscript contains expected content."""
        main_md = guillaume_manuscript_dir / "01_MAIN.md"
        content = main_md.read_text()

        # Check for Guillaume's specific test cases
        assert "## Introduction" in content, "Should have Introduction section"
        assert "(@fig:" in content, "Should have panel references"
        assert 'tex_position="p"' in content, "Should have full-page positioning"
        assert "Guillaume" in content, "Should reference Guillaume's issues"

    def test_guillaume_panel_references_from_fixture(self, guillaume_manuscript_dir):
        """Test panel reference conversion using content from Guillaume fixture."""
        main_md = guillaume_manuscript_dir / "01_MAIN.md"
        content = main_md.read_text()

        # Extract lines with panel references
        panel_lines = [line for line in content.split("\n") if "(@fig:" in line and " A)" in line]
        assert len(panel_lines) > 0, "Should find panel reference lines in fixture"

        # Test conversion
        for line in panel_lines:
            result = convert_figure_references_to_latex(line)
            # Should have no space between figure number and panel letter
            assert "A)" in result, f"Should have panel letter A in: {result}"
            assert " A)" not in result, f"Should not have space before A in: {result}"

    def test_guillaume_ready_files_structure(self, guillaume_manuscript_dir):
        """Test that ready files follow Guillaume's expected structure."""
        figures_dir = guillaume_manuscript_dir / "FIGURES"

        # Guillaume's issue was needing files in multiple places
        # With our fix, files should only need to be in FIGURES/ directly
        ready_files = list(figures_dir.glob("*.png"))
        assert len(ready_files) >= 2, "Should have multiple ready files"

        # Files should be directly in FIGURES/, not in subdirectories
        for fig_file in ready_files:
            assert fig_file.parent == figures_dir, f"Ready file {fig_file.name} should be directly in FIGURES/"

        # Should NOT have subdirectory structure (Guillaume's original problem)
        subdirs = [item for item in figures_dir.iterdir() if item.is_dir()]
        assert len(subdirs) == 0, "Should not have subdirectories in FIGURES/ for ready files"

    def test_guillaume_fixture_documentation(self, guillaume_manuscript_dir):
        """Test that fixture has proper documentation."""
        readme = guillaume_manuscript_dir / "README.md"
        assert readme.exists(), "Fixtures directory should have README.md"

        readme_content = readme.read_text()
        assert "GUILLAUME_TEST_MANUSCRIPT" in readme_content, "README should document Guillaume fixture"
        assert "Issue #1" in readme_content, "README should document Guillaume's issues"
        assert "Issue #2" in readme_content, "README should document ready file issue"
