"""Integration tests for validation workflow."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from rxiv_maker.core import logging_config


@pytest.mark.validation
@pytest.mark.integration
@pytest.mark.xdist_group(name="validation_workflow")
class TestValidationWorkflow:
    """Test validation workflow integration."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = os.path.join(self.temp_dir, "TEST_MANUSCRIPT")
        os.makedirs(self.manuscript_dir)

        # Create FIGURES directory
        self.figures_dir = os.path.join(self.manuscript_dir, "FIGURES")
        os.makedirs(self.figures_dir)

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        # Ensure logging cleanup for Windows file locking issues
        logging_config.cleanup()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_valid_manuscript(self):
        """Create a complete valid manuscript for testing."""
        # Create config file
        config_content = """
title: "Integration Test Article"
authors:
  - name: "Test Author"
    affiliation: "Test University"
    email: "test@example.com"
abstract: "This is a test abstract for integration testing."
date: "2024-01-01"
keywords: ["test", "validation", "integration"]
"""
        with open(os.path.join(self.manuscript_dir, "00_CONFIG.yml"), "w") as f:
            f.write(config_content)

        # Create main manuscript
        main_content = """
# Integration Test Article

## Introduction

This is a test manuscript for integration testing with @smith2023 and @jones2022.

## Methods

We use mathematical expressions like $E = mc^2$ and display equations:

$$F = ma$${#eq:newton}

See @eq:newton for Newton's second law.

## Results

![Test figure](FIGURES/test_plot.png){#fig:test width="0.8"}

Figure @fig:test shows our test results.

| Parameter | Value |
|-----------|-------|
| Alpha     | 1.0   |
| Beta      | 2.0   |

{#table:params} **Parameter values used in analysis.**

See @table:params for parameter details.

## Discussion

This manuscript demonstrates various formatting elements.

## References
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        # Create bibliography
        bib_content = """
@article{smith2023,
    title = {Test Article One},
    author = {Smith, John and Doe, Jane},
    journal = {Test Journal},
    year = {2023},
    volume = {1},
    pages = {1--10}
}

@article{jones2022,
    title = {Test Article Two},
    author = {Jones, Mary},
    journal = {Another Test Journal},
    year = {2022},
    volume = {2},
    pages = {11--20}
}
"""
        with open(os.path.join(self.manuscript_dir, "03_REFERENCES.bib"), "w") as f:
            f.write(bib_content)

        # Create test figure file
        test_fig_path = os.path.join(self.figures_dir, "test_plot.png")
        with open(test_fig_path, "w") as f:
            f.write("fake png content for testing")

    def create_invalid_manuscript(self):
        """Create a manuscript with validation errors."""
        # Create config file with missing required fields
        config_content = """
title: "Invalid Test Article"
# Missing required authors field
date: "2024-01-01"
"""
        with open(os.path.join(self.manuscript_dir, "00_CONFIG.yml"), "w") as f:
            f.write(config_content)

        # Create main manuscript with errors
        main_content = """
# Invalid Test Article

## Introduction

Invalid citation @nonexistent2023 that doesn't exist in bibliography.

## Methods

Unbalanced math: $E = mc^{2$

## Results

![Missing figure](FIGURES/missing.png){#fig:missing}

Reference to undefined figure @fig:nonexistent.

## References
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        # Create bibliography (no entries for nonexistent2023)
        bib_content = """
@article{smith2023,
    title = {Test Article},
    author = {Smith, John},
    year = {2023}
}
"""
        with open(os.path.join(self.manuscript_dir, "03_REFERENCES.bib"), "w") as f:
            f.write(bib_content)

    @pytest.mark.slow
    def test_makefile_validation_valid_manuscript(self, execution_engine):
        """Test validation through Makefile with valid manuscript."""
        self.create_valid_manuscript()

        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent

        # Use CLI validation directly with --no-doi to skip slow DOI validation
        if execution_engine.engine_type == "local":
            result = execution_engine.run(
                [
                    "python",
                    "-m",
                    "rxiv_maker.cli",
                    "validate",
                    str(self.manuscript_dir),
                    "--no-doi",
                ],
                cwd=project_root,
            )
        else:
            # In container, use the installed rxiv command with workspace path
            result = execution_engine.run(
                ["rxiv", "validate", "/workspace", "--no-doi"],
                cwd="/workspace",
            )

        # Valid manuscript should pass validation
        assert result.returncode == 0, f"Validation failed: {result.stderr}"

    def test_makefile_validation_invalid_manuscript(self, execution_engine):
        """Test validation through Makefile with invalid manuscript."""
        self.create_invalid_manuscript()

        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent

        # Use CLI validation directly with --no-doi to skip slow DOI validation
        if execution_engine.engine_type == "local":
            result = execution_engine.run(
                [
                    "python",
                    "-m",
                    "rxiv_maker.cli",
                    "validate",
                    str(self.manuscript_dir),
                    "--no-doi",
                ],
                cwd=project_root,
                check=False,  # Don't raise exception on non-zero exit
            )
        else:
            # In container, use the installed rxiv command with workspace path
            result = execution_engine.run(
                ["rxiv", "validate", "/workspace", "--no-doi"],
                cwd="/workspace",
                check=False,  # Don't raise exception on non-zero exit
            )

        # Invalid manuscript should fail validation
        assert result.returncode != 0, "Expected validation to fail for invalid manuscript"

    def test_validation_script_detailed_mode(self):
        """Test detailed validation script with comprehensive feedback."""
        self.create_invalid_manuscript()

        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent

        # Run detailed validation
        import os

        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root / "src") + ":" + env.get("PYTHONPATH", "")
        result = subprocess.run(
            [
                "python",
                "-m",
                "rxiv_maker.scripts.validate_manuscript",
                "--detailed",
                self.manuscript_dir,
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            env=env,
        )

        # Should fail validation and provide detailed feedback
        assert result.returncode != 0

        # Check that output contains expected error information
        output = result.stdout + result.stderr
        assert "nonexistent2023" in output  # Citation error
        assert "missing.png" in output  # Figure error
        assert "Unbalanced" in output or "delimiters" in output  # Math error

    def test_validation_before_pdf_generation(self):
        """Test that validation is integrated into PDF generation workflow."""
        self.create_invalid_manuscript()

        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent

        # Use CLI validation directly with --no-doi to skip slow DOI validation
        result = subprocess.run(
            [
                "python",
                "-m",
                "rxiv_maker.cli",
                "validate",
                self.manuscript_dir,
                "--no-doi",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        # Should fail due to validation errors
        assert result.returncode != 0

    def test_validation_passes_before_successful_pdf(self):
        """Test that valid manuscripts pass validation and can generate PDFs."""
        self.create_valid_manuscript()

        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent

        # Use CLI validation directly with --no-doi to skip slow DOI validation
        validation_result = subprocess.run(
            [
                "python",
                "-m",
                "rxiv_maker.cli",
                "validate",
                self.manuscript_dir,
                "--no-doi",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        # Validation should pass
        assert validation_result.returncode == 0

        # Note: We don't actually run PDF generation in integration tests
        # as it requires LaTeX installation, but validation passing is a good indicator

    @pytest.mark.slow
    def test_comprehensive_validation_scenarios(self):
        """Test various validation scenarios comprehensively."""
        scenarios = [
            ("missing_config", self._create_missing_config_scenario),
            ("empty_main", self._create_empty_main_scenario),
            ("invalid_yaml", self._create_invalid_yaml_scenario),
            ("citation_mismatch", self._create_citation_mismatch_scenario),
            ("figure_path_errors", self._create_figure_path_errors_scenario),
        ]

        project_root = Path(__file__).parent.parent.parent

        for scenario_name, scenario_creator in scenarios:
            # Clean and recreate manuscript directory
            shutil.rmtree(self.manuscript_dir, ignore_errors=True)
            os.makedirs(self.manuscript_dir)
            os.makedirs(self.figures_dir)

            # Create scenario
            scenario_creator()

            # Run validation
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "rxiv_maker.scripts.validate_manuscript",
                    self.manuscript_dir,
                ],
                cwd=project_root,
                capture_output=True,
                text=True,
            )

            # All scenarios should fail validation
            assert result.returncode != 0, f"Scenario '{scenario_name}' should fail validation"

    def _create_missing_config_scenario(self):
        """Create scenario with missing config file."""
        # Only create main manuscript, no config
        main_content = "# Test without config"
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

    def _create_empty_main_scenario(self):
        """Create scenario with empty main manuscript."""
        # Create minimal config
        config_content = """
title: "Test"
authors:
  - name: "Author"
"""
        with open(os.path.join(self.manuscript_dir, "00_CONFIG.yml"), "w") as f:
            f.write(config_content)

        # Create empty main file
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write("")

    def _create_invalid_yaml_scenario(self):
        """Create scenario with invalid YAML syntax."""
        # Create config with invalid YAML
        config_content = """
title: "Test"
authors:
  - name: "Author"
  invalid_yaml: [unclosed bracket
"""
        with open(os.path.join(self.manuscript_dir, "00_CONFIG.yml"), "w") as f:
            f.write(config_content)

        main_content = "# Test"
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

    def _create_citation_mismatch_scenario(self):
        """Create scenario with citation/bibliography mismatch."""
        config_content = """
title: "Test"
authors:
  - name: "Author"
"""
        with open(os.path.join(self.manuscript_dir, "00_CONFIG.yml"), "w") as f:
            f.write(config_content)

        # Main with citations not in bibliography
        main_content = """
# Test

Citations @ref1 and @ref2 that don't exist.
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        # Bibliography with different references
        bib_content = """
@article{different_ref,
    title = {Different Reference},
    author = {Someone Else},
    year = {2023}
}
"""
        with open(os.path.join(self.manuscript_dir, "03_REFERENCES.bib"), "w") as f:
            f.write(bib_content)

    def _create_figure_path_errors_scenario(self):
        """Create scenario with figure path errors."""
        config_content = """
title: "Test"
authors:
  - name: "Author"
"""
        with open(os.path.join(self.manuscript_dir, "00_CONFIG.yml"), "w") as f:
            f.write(config_content)

        # Main with references to non-existent figures
        main_content = """
# Test

![Missing figure](FIGURES/does_not_exist.png){#fig:missing}

![Another missing](FIGURES/also_missing.jpg){#fig:missing2}

See @fig:missing and @fig:missing2.
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)
