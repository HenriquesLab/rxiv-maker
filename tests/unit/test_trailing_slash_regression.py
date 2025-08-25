"""Test for trailing slash issue in manuscript paths (Issue #100)."""

import os

from rxiv_maker.engines.operations.build_manager import BuildManager


class TestTrailingSlashRegression:
    """Test cases for Issue #100 - BibTeX returned error code 1 due to trailing slash paths."""

    def setup_manuscript_dir(self, temp_dir, name):
        """Set up a minimal manuscript directory for testing."""
        manuscript_dir = temp_dir / name
        manuscript_dir.mkdir(parents=True, exist_ok=True)

        # Create minimal required files
        (manuscript_dir / "01_MAIN.md").write_text("# Test Manuscript")
        (manuscript_dir / "00_CONFIG.yml").write_text("title: Test")

        return manuscript_dir

    def test_manuscript_name_trailing_slash_paths(self, temp_dir):
        """Test that BuildManager handles trailing slashes correctly in manuscript paths."""

        test_cases = [
            ("CCT8_paper", "CCT8_paper"),  # No slash
            ("CCT8_paper/", "CCT8_paper"),  # Single slash (Guillaume's case)
            ("CCT8_paper//", "CCT8_paper"),  # Double slash
            ("my_project/", "my_project"),  # Different name with slash
        ]

        for input_path_suffix, expected_name in test_cases:
            # Create manuscript directory
            manuscript_dir = self.setup_manuscript_dir(temp_dir, expected_name)

            # Build full path with the suffix (slash variations)
            if input_path_suffix.endswith("/"):
                # For paths with trailing slash, use the directory + slash
                manuscript_path = str(manuscript_dir) + input_path_suffix[len(expected_name) :]
            else:
                manuscript_path = str(manuscript_dir)

            output_dir = temp_dir / "output" / expected_name

            # Create BuildManager instance
            build_manager = BuildManager(
                manuscript_path=manuscript_path, output_dir=str(output_dir), skip_validation=True
            )

            # Verify the manuscript name is extracted correctly
            assert build_manager.manuscript_name == expected_name, (
                f"Failed for input '{input_path_suffix}': "
                f"expected '{expected_name}', got '{build_manager.manuscript_name}'"
            )

            # Verify output file paths use the correct name
            assert build_manager.output_tex.name == f"{expected_name}.tex"
            assert build_manager.output_pdf.name == f"{expected_name}.pdf"

    def test_environment_variable_setting_with_trailing_slash(self, temp_dir):
        """Test that MANUSCRIPT_PATH environment variable is set correctly with trailing slashes."""

        manuscript_dir = self.setup_manuscript_dir(temp_dir, "test_project")
        output_dir = temp_dir / "output"

        # Test with trailing slash
        manuscript_path_with_slash = str(manuscript_dir) + "/"

        build_manager = BuildManager(
            manuscript_path=manuscript_path_with_slash, output_dir=str(output_dir), skip_validation=True
        )

        # Simulate the environment variable setting logic from generate_tex_files
        normalized_path = build_manager.manuscript_path.rstrip("/")
        manuscript_name = os.path.basename(normalized_path)
        if not manuscript_name or manuscript_name in (".", ".."):
            manuscript_name = "MANUSCRIPT"

        # Should extract correct name despite trailing slash
        assert manuscript_name == "test_project"

    def test_edge_cases_for_invalid_paths(self, temp_dir):
        """Test edge cases that should default to MANUSCRIPT."""

        output_dir = temp_dir / "output"

        edge_cases = [
            ("", "MANUSCRIPT"),  # Empty string
            (".", "MANUSCRIPT"),  # Current directory
            ("..", "MANUSCRIPT"),  # Parent directory
        ]

        for input_path, expected_name in edge_cases:
            build_manager = BuildManager(manuscript_path=input_path, output_dir=str(output_dir), skip_validation=True)

            assert build_manager.manuscript_name == expected_name, (
                f"Failed for input '{input_path}': expected '{expected_name}', got '{build_manager.manuscript_name}'"
            )

    def test_guillaume_exact_case(self, temp_dir):
        """Test Guillaume's exact use case: 'rxiv pdf CCT8_paper/'."""

        # Set up exactly like Guillaume's case
        manuscript_dir = self.setup_manuscript_dir(temp_dir, "CCT8_paper")
        manuscript_path = str(manuscript_dir) + "/"  # With trailing slash
        output_dir = manuscript_dir / "output"

        build_manager = BuildManager(manuscript_path=manuscript_path, output_dir=str(output_dir), skip_validation=True)

        # This should work correctly now
        assert build_manager.manuscript_name == "CCT8_paper"
        assert build_manager.output_tex.name == "CCT8_paper.tex"
        assert build_manager.output_pdf.name == "CCT8_paper.pdf"

        # Verify that the expected LaTeX file name matches what will be generated
        # This ensures LaTeX compilation will find the right file
        normalized_path = manuscript_path.rstrip("/")
        manuscript_name = os.path.basename(normalized_path)
        if not manuscript_name or manuscript_name in (".", ".."):
            manuscript_name = "MANUSCRIPT"

        assert manuscript_name == "CCT8_paper"
        assert manuscript_name == build_manager.manuscript_name
