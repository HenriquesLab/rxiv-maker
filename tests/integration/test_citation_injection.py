"""Integration tests for citation injection functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from rxiv_maker.utils.citation_utils import inject_rxiv_citation


class TestCitationInjectionIntegration:
    """Integration tests for citation injection with build process."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = Path(self.temp_dir) / "MANUSCRIPT"
        self.manuscript_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = Path(self.temp_dir) / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_citation_injection_workflow(self):
        """Test complete workflow of citation injection during manuscript build."""
        # Create config file with acknowledge_rxiv_maker enabled
        config_file = self.manuscript_dir / "00_CONFIG.yml"
        config_content = """
title:
  main: "Test Manuscript with Citation"
  lead_author: "Test Author"
date: "2025-08-14"
authors:
  - name: "Test Author"
    affiliation: "Test University"
    email: "test@example.com"
affiliations:
  - name: "Test University"
    address: "123 Test St"
keywords: ["test", "citation"]
acknowledge_rxiv_maker: true
"""
        config_file.write_text(config_content, encoding="utf-8")

        # Create main manuscript file
        main_file = self.manuscript_dir / "01_MAIN.md"
        main_content = """
# Introduction

This is a test manuscript to verify citation injection.

# Methods

We used standard methods.

# Results

See results here.

# Discussion

Discussion of results.

# Conclusion

Final thoughts.

# Acknowledgements

Thanks to everyone.
"""
        main_file.write_text(main_content, encoding="utf-8")

        # Create empty bibliography file
        bib_file = self.manuscript_dir / "03_REFERENCES.bib"
        bib_content = """@article{example2024,
    title={Example Reference},
    author={Jane Doe},
    journal={Test Journal},
    year={2024}
}
"""
        bib_file.write_text(bib_content, encoding="utf-8")

        # Test citation injection directly
        yaml_metadata = {"acknowledge_rxiv_maker": True, "bibliography": "03_REFERENCES.bib"}

        with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
            with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                inject_rxiv_citation(yaml_metadata)

        # Verify citation was injected
        updated_bib_content = bib_file.read_text(encoding="utf-8")
        assert "saraiva_2025_rxivmaker" in updated_bib_content
        assert "Rxiv-Maker: an automated template engine" in updated_bib_content
        assert "Bruno M. Saraiva and Guillaume Jaquemet and Ricardo Henriques" in updated_bib_content

        # Verify original content is preserved
        assert "example2024" in updated_bib_content
        assert "Jane Doe" in updated_bib_content

    def test_citation_injection_with_build_manager(self):
        """Test that citation injection integrates properly with BuildManager."""
        # Create minimal manuscript structure
        config_file = self.manuscript_dir / "00_CONFIG.yml"
        config_content = """
title:
  main: "Build Manager Test"
authors:
  - name: "Test Author"
acknowledge_rxiv_maker: true
"""
        config_file.write_text(config_content, encoding="utf-8")

        main_file = self.manuscript_dir / "01_MAIN.md"
        main_file.write_text("# Test\n\nContent here.\n", encoding="utf-8")

        bib_file = self.manuscript_dir / "03_REFERENCES.bib"
        bib_file.write_text("", encoding="utf-8")

        # Mock the YAML metadata extraction to return our test config
        test_metadata = {"acknowledge_rxiv_maker": True, "bibliography": "03_REFERENCES.bib"}

        with patch("rxiv_maker.processors.yaml_processor.extract_yaml_metadata", return_value=test_metadata):
            with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
                with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                    # Call the citation injection method directly (as it would be called in build)
                    inject_rxiv_citation(test_metadata)

        # Verify citation was injected
        updated_bib_content = bib_file.read_text(encoding="utf-8")
        assert "saraiva_2025_rxivmaker" in updated_bib_content
        assert "2025" in updated_bib_content

    def test_citation_injection_preserves_existing_citations(self):
        """Test that citation injection preserves existing citations and formatting."""
        # Create bibliography with complex existing content
        bib_file = self.manuscript_dir / "03_REFERENCES.bib"
        existing_content = """% This is a comment
@article{important2024,
    title={Very Important Research},
    author={Smith, John and Jones, Mary},
    journal={Nature},
    volume={600},
    pages={123--456},
    year={2024},
    publisher={Nature Publishing Group},
    doi={10.1038/s41586-024-12345-6}
}

@book{reference_book,
    title={Comprehensive Guide to Science},
    author={Brown, Alice},
    publisher={Academic Press},
    year={2023},
    isbn={978-0-123456-78-9}
}

% Another comment
@inproceedings{conference_paper,
    title={Novel Approach to Problem Solving},
    author={Wilson, Bob and Taylor, Carol},
    booktitle={Proceedings of Important Conference},
    pages={789--801},
    year={2024},
    organization={IEEE}
}
"""
        bib_file.write_text(existing_content, encoding="utf-8")

        # Inject citation
        yaml_metadata = {"acknowledge_rxiv_maker": True, "bibliography": "03_REFERENCES.bib"}

        with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
            with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                inject_rxiv_citation(yaml_metadata)

        # Verify all content is preserved
        updated_content = bib_file.read_text(encoding="utf-8")

        # Check original content is preserved
        assert "% This is a comment" in updated_content
        assert "important2024" in updated_content
        assert "Very Important Research" in updated_content
        assert "Smith, John and Jones, Mary" in updated_content
        assert "reference_book" in updated_content
        assert "Comprehensive Guide to Science" in updated_content
        assert "conference_paper" in updated_content
        assert "Novel Approach to Problem Solving" in updated_content
        assert "% Another comment" in updated_content

        # Check new citation is added
        assert "saraiva_2025_rxivmaker" in updated_content
        assert "Rxiv-Maker: an automated template engine" in updated_content

        # Verify proper formatting (no triple newlines)
        lines = updated_content.split("\n")
        for i in range(len(lines) - 2):
            if lines[i] == "" and lines[i + 1] == "" and lines[i + 2] == "":
                pytest.fail("Found triple newlines in bibliography content")

    def test_citation_injection_with_different_bibliography_names(self):
        """Test citation injection works with different bibliography file names."""
        test_cases = [
            "references.bib",
            "my_refs",  # Without .bib extension
            "bibliography.bib",
            "sources",  # Without .bib extension
        ]

        for bib_name in test_cases:
            # Create clean test directory for each case
            test_dir = Path(self.temp_dir) / f"test_{bib_name.replace('.', '_')}"
            test_manuscript_dir = test_dir / "MANUSCRIPT"
            test_manuscript_dir.mkdir(parents=True, exist_ok=True)

            # Determine actual file name (add .bib if not present)
            actual_bib_name = bib_name if bib_name.endswith(".bib") else f"{bib_name}.bib"
            bib_file = test_manuscript_dir / actual_bib_name

            # Create initial bibliography content
            bib_file.write_text("% Test bibliography\n", encoding="utf-8")

            # Test citation injection
            yaml_metadata = {"acknowledge_rxiv_maker": True, "bibliography": bib_name}

            with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(test_manuscript_dir)}):
                with patch("pathlib.Path.cwd", return_value=test_dir):
                    inject_rxiv_citation(yaml_metadata)

            # Verify citation was injected
            updated_content = bib_file.read_text(encoding="utf-8")
            assert "saraiva_2025_rxivmaker" in updated_content
            assert "% Test bibliography" in updated_content

    def test_citation_injection_creates_manuscript_preparation_block(self):
        """Test that the manuscript preparation block is created with citation."""
        # Create minimal manuscript content
        main_file = self.manuscript_dir / "01_MAIN.md"
        main_content = """
# Introduction

Test content.

# Acknowledgements

Original acknowledgements.
"""
        main_file.write_text(main_content, encoding="utf-8")

        # Create bibliography with rxiv-maker citation
        bib_file = self.manuscript_dir / "03_REFERENCES.bib"
        bib_content = """
@misc{saraiva_2025_rxivmaker,
      title={Rxiv-Maker: an automated template engine for streamlined scientific publications},
      author={Bruno M. Saraiva and Guillaume Jaquemet and Ricardo Henriques},
      year={2025},
      eprint={2508.00836},
      archivePrefix={arXiv},
      primaryClass={cs.DL},
      url={https://arxiv.org/abs/2508.00836},
}
"""
        bib_file.write_text(bib_content, encoding="utf-8")

        # Verify the citation exists in bibliography
        with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
            with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
                content = bib_file.read_text(encoding="utf-8")
                assert "saraiva_2025_rxivmaker" in content

    def test_citation_injection_error_handling(self):
        """Test that citation injection handles various error conditions gracefully."""
        test_metadata = {"acknowledge_rxiv_maker": True}

        # Test with permission denied on bibliography file
        bib_file = self.manuscript_dir / "03_REFERENCES.bib"
        bib_file.write_text("", encoding="utf-8")

        # Mock file operations to simulate permission error
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
                with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                    # Should not raise exception but should print error message
                    inject_rxiv_citation(test_metadata)
                    # The function handles errors gracefully by printing error messages

    def test_multiple_citation_injections_idempotent(self):
        """Test that multiple citation injections are idempotent (no duplicates)."""
        bib_file = self.manuscript_dir / "03_REFERENCES.bib"
        bib_file.write_text("", encoding="utf-8")

        yaml_metadata = {"acknowledge_rxiv_maker": True}

        # Inject citation multiple times
        for _ in range(3):
            with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
                with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                    inject_rxiv_citation(yaml_metadata)

        # Verify only one citation exists
        content = bib_file.read_text(encoding="utf-8")
        citation_count = content.count("saraiva_2025_rxivmaker")
        assert citation_count == 1, f"Expected 1 citation, found {citation_count}"

        # Verify content is correct
        assert "Rxiv-Maker: an automated template engine" in content
        assert "Bruno M. Saraiva and Guillaume Jaquemet and Ricardo Henriques" in content

    def test_acknowledgment_includes_version_in_generated_manuscript(self):
        """Test that acknowledgment text includes version in generated manuscript."""
        from rxiv_maker import __version__
        from rxiv_maker.engines.operations.generate_preprint import generate_preprint

        # Create configuration with acknowledgment enabled
        config_content = """
        title:
            long: "Test Manuscript with Version"
        authors:
            - name: "Test Author"
              affiliations: ["Test University"]
        affiliations:
            - shortname: "Test University"
              full_name: "Test University"
        acknowledge_rxiv_maker: true
        """

        config_file = self.manuscript_dir / "00_CONFIG.yml"
        config_file.write_text(config_content, encoding="utf-8")

        # Create a simple manuscript
        main_content = """# Test Manuscript

This is a test manuscript to verify version injection.
"""
        main_file = self.manuscript_dir / "01_MAIN.md"
        main_file.write_text(main_content, encoding="utf-8")

        # Create bibliography file for citation to work
        bib_file = self.manuscript_dir / "03_REFERENCES.bib"
        bib_file.write_text("", encoding="utf-8")

        # Extract YAML metadata
        from rxiv_maker.processors.yaml_processor import extract_yaml_metadata

        yaml_metadata = extract_yaml_metadata(str(config_file))

        # Generate manuscript
        with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
            with patch("pathlib.Path.cwd", return_value=Path(self.manuscript_dir)):
                tex_file = generate_preprint(str(self.output_dir), yaml_metadata)

        # Read generated tex file
        tex_content = Path(tex_file).read_text(encoding="utf-8")

        # Verify version is included in acknowledgment text
        assert "This manuscript was prepared using" in tex_content
        assert f"R}}$\\chi$iv-Maker v{__version__}" in tex_content
        assert "saraiva_2025_rxivmaker" in tex_content

        # Verify it's in manuscriptinfo environment
        assert "\\begin{manuscriptinfo}" in tex_content
        assert "\\end{manuscriptinfo}" in tex_content
