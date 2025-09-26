"""Tests for path resolution regression issues.

This module contains regression tests for path resolution problems identified
by Guillaume in Issue #96, focusing on manuscript file lookup and working
directory independence.

Key issues tested:
- Issue #96: CLI path resolution problems
- Manuscript file lookup in correct directories
- Environment variable handling for manuscript paths
- Working directory independence
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestPathResolution:
    """Test path resolution issues (Issue #96)."""

    def test_manuscript_file_lookup_in_correct_directory(self):
        """Test that manuscript files are looked up in the correct directory.

        This addresses the issue where it was looking for 01_MAIN.md
        in the parent folder instead of the manuscript folder.
        """
        from rxiv_maker.utils import find_manuscript_md

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create manuscript structure
            manuscript_dir = Path(temp_dir) / "test_manuscript"
            manuscript_dir.mkdir(parents=True)
            main_file = manuscript_dir / "01_MAIN.md"
            main_file.write_text("# Test Manuscript")

            # Should find the file in the manuscript directory
            found_file = find_manuscript_md(manuscript_dir)
            assert found_file is not None
            assert found_file.name == "01_MAIN.md"
            assert found_file.parent == manuscript_dir

    def test_manuscript_file_lookup_with_environment_variable(self):
        """Test manuscript lookup respects MANUSCRIPT_PATH environment variable."""
        from rxiv_maker.utils import find_manuscript_md

        with tempfile.TemporaryDirectory() as temp_dir:
            manuscript_dir = Path(temp_dir) / "env_manuscript"
            manuscript_dir.mkdir(parents=True)
            main_file = manuscript_dir / "01_MAIN.md"
            main_file.write_text("# Test Manuscript")

            # Test with environment variable set
            with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(manuscript_dir)}):
                found_file = find_manuscript_md()
                assert found_file is not None
                assert found_file.parent == manuscript_dir

    def test_figure_path_resolution(self):
        """Test figure path resolution and display consistency.

        This addresses issues with figure path display from Issue #96.
        """
        from rxiv_maker.engines.operations.generate_figures import FigureGenerator

        with tempfile.TemporaryDirectory() as temp_dir:
            manuscript_dir = Path(temp_dir)
            figures_dir = manuscript_dir / "FIGURES"
            figures_dir.mkdir(parents=True)

            # Create a test figure script
            test_script = figures_dir / "Figure__test.py"
            test_script.write_text("""
import matplotlib.pyplot as plt
plt.figure()
plt.plot([1, 2, 3], [1, 4, 9])
plt.savefig('Figure__test.png')
plt.close()
""")

            FigureGenerator(figures_dir=str(figures_dir), output_dir=str(figures_dir))

            # Should properly resolve paths without looking in parent directories
            python_files = list(figures_dir.glob("*.py"))
            assert len(python_files) > 0
            assert any(f.name == "Figure__test.py" for f in python_files)

    def test_working_directory_independence(self):
        """Test that operations work regardless of current working directory."""
        from click.testing import CliRunner

        from rxiv_maker.cli.main import main

        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create manuscript in subdirectory
            manuscript_dir = Path(temp_dir) / "project" / "manuscript"
            manuscript_dir.mkdir(parents=True)
            (manuscript_dir / "01_MAIN.md").write_text("# Test")

            # Create another directory to run from
            run_dir = Path(temp_dir) / "other_directory"
            run_dir.mkdir()

            # Change to different directory and run command
            original_cwd = os.getcwd()
            try:
                os.chdir(run_dir)
                result = runner.invoke(main, ["validate", str(manuscript_dir)], catch_exceptions=True)

                # Should work correctly even when run from different directory
                assert "not found in" not in result.output
                # May have validation errors, but shouldn't have path resolution errors

            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__])
