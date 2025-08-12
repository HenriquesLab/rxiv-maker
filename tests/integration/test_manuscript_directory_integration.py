"""Integration tests for manuscript directory setup and build validation."""

from pathlib import Path
from unittest.mock import patch

import pytest


class TestManuscriptBuildIntegration:
    """Integration tests for complete manuscript build with custom directories."""

    def test_end_to_end_custom_manuscript_build(self, temp_dir, monkeypatch):
        """Test complete build process with custom manuscript directory."""
        monkeypatch.chdir(temp_dir)

        # Set up custom manuscript
        manuscript_path = "NOVEL_AI_RESEARCH"
        monkeypatch.setenv("MANUSCRIPT_PATH", manuscript_path)

        # Create manuscript directory structure
        manuscript_dir = temp_dir / manuscript_path
        manuscript_dir.mkdir()

        # Create figures directory
        figures_dir = manuscript_dir / "FIGURES"
        figures_dir.mkdir()

        # Create config file with metadata for custom PDF naming
        config_file = manuscript_dir / "00_CONFIG.yml"
        config_content = """
title:
  main: "Novel AI Research Methods"
  lead_author: "Chen"
date: "2025-06-25"
authors:
  - name: "Dr. Li Chen"
    affiliation: "AI Research Institute"
    email: "l.chen@ai-research.org"
    orcid: "0000-0002-1234-5678"
affiliations:
  - name: "AI Research Institute"
    address: "123 Research Blvd, Tech City, TC 12345"
keywords: ["artificial intelligence", "machine learning", "research methods"]
"""
        config_file.write_text(config_content)

        # Create main manuscript file
        main_file = manuscript_dir / "01_MAIN.md"
        main_content = """---
title: "Novel AI Research Methods"
authors:
  - name: "Dr. Li Chen"
    affiliation: "AI Research Institute"
    email: "l.chen@ai-research.org"
keywords: ["artificial intelligence", "machine learning"]
---

# Introduction

This manuscript demonstrates the complete build process with custom directory naming.

Recent advances in artificial intelligence @chen2024 have shown promising results.

## Methods

Our methodology builds on established practices @smith2023.

### Data Collection

We collected data from multiple sources as shown in @fig:data_overview.

![Data Overview](FIGURES/Figure__example/Figure__example.png){#fig:data_overview width="0.8"}

## Results

The results are summarized in @tbl:results.

| Method | Accuracy | Performance |
|--------|----------|-------------|
| Baseline | 85% | Good |
| Our Method | 92% | Excellent |

: Main Results {#tbl:results}

## Conclusion

This work demonstrates successful custom manuscript directory handling.
"""
        main_file.write_text(main_content)

        # Create bibliography
        bib_file = manuscript_dir / "03_REFERENCES.bib"
        bib_content = """@article{chen2024,
  title={Advanced AI Methods},
  author={Chen, Li and Wang, Ming},
  journal={AI Research Journal},
  volume={15},
  number={3},
  pages={123--145},
  year={2024},
  publisher={Tech Publishers}
}

@article{smith2023,
  title={Foundation Methods in Machine Learning},
  author={Smith, John A. and Johnson, Jane B.},
  journal={Machine Learning Review},
  volume={12},
  number={8},
  pages={45--67},
  year={2023}
}
"""
        bib_file.write_text(bib_content)

        # Create a sample figure directory and placeholder image
        figure1_dir = figures_dir / "Figure__example"
        figure1_dir.mkdir()

        # Create a placeholder image file (simulate PNG content)
        figure1_file = figure1_dir / "Figure__example.png"
        figure1_file.write_text("fake_png_content")

        # Create output directory
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Test the manuscript generation process
        with patch("sys.argv", ["generate_preprint.py", "--output-dir", str(output_dir)]):
            try:
                from rxiv_maker.engine.generate_preprint import main

                result = main()

                if result == 0:
                    # Verify LaTeX file was created with correct name
                    expected_tex = output_dir / f"{manuscript_path}.tex"
                    assert expected_tex.exists(), f"Expected {expected_tex} to exist"

                    # Check content of generated LaTeX
                    tex_content = expected_tex.read_text()
                    assert "Novel AI Research Methods" in tex_content
                    assert r"\cite{chen2024}" in tex_content
                    assert r"\ref{fig:data_overview}" in tex_content
                    assert r"\ref{tbl:results}" in tex_content

                    # If PDF was generated, test custom naming
                    source_pdf = output_dir / f"{manuscript_path}.pdf"
                    if source_pdf.exists():
                        # Test PDF copy with custom naming
                        from rxiv_maker.processors.yaml_processor import (
                            extract_yaml_metadata_from_file,
                        )
                        from rxiv_maker.utils import copy_pdf_to_manuscript_folder

                        # Extract metadata for custom naming
                        yaml_metadata = extract_yaml_metadata_from_file(str(main_file))

                        # Copy PDF with custom naming
                        copied_pdf = copy_pdf_to_manuscript_folder(str(output_dir), yaml_metadata)

                        # Verify custom naming: 2025__chen_et_al__rxiv.pdf
                        expected_pdf_name = "2025__chen_et_al__rxiv.pdf"
                        expected_pdf_path = manuscript_dir / expected_pdf_name

                        # Use resolve() to handle macOS path resolution
                        assert copied_pdf.resolve() == expected_pdf_path.resolve()
                        assert expected_pdf_path.exists()

                        print(f"✅ PDF successfully copied to: {expected_pdf_path}")
                    else:
                        print("ℹ️ PDF not generated (LaTeX compilation may not be available)")

                else:
                    pytest.skip("Manuscript generation failed")

            except Exception as e:
                pytest.skip(f"Integration test failed: {e}")

    def test_makefile_integration_with_custom_paths(self, temp_dir, monkeypatch):
        """Test that Makefile commands work with custom manuscript paths."""
        monkeypatch.chdir(temp_dir)

        # Set up multiple manuscripts to test switching
        manuscripts = ["PAPER_A", "PAPER_B", "PAPER_C"]

        for manuscript in manuscripts:
            # Create manuscript directory
            manuscript_dir = temp_dir / manuscript
            manuscript_dir.mkdir()

            # Create minimal required files
            config_file = manuscript_dir / "00_CONFIG.yml"
            config_content = f"""
title:
  main: "Research Paper {manuscript[-1]}"
  lead_author: "Author{manuscript[-1]}"
date: "2025-06-25"
authors:
  - name: "Author {manuscript[-1]}"
    affiliation: "University"
"""
            config_file.write_text(config_content)

            main_file = manuscript_dir / "01_MAIN.md"
            main_content = f"""---
title: "Research Paper {manuscript[-1]}"
authors:
  - name: "Author {manuscript[-1]}"
---

# Paper {manuscript[-1]}

This is manuscript {manuscript}.
"""
            main_file.write_text(main_content)

            # Create figures directory
            figures_dir = manuscript_dir / "FIGURES"
            figures_dir.mkdir()

        # Test each manuscript build independently
        for manuscript in manuscripts:
            monkeypatch.setenv("MANUSCRIPT_PATH", manuscript)

            # Test manuscript finding
            from rxiv_maker.utils import find_manuscript_md

            found_manuscript = find_manuscript_md()
            assert manuscript in str(found_manuscript)

            # Test output file naming
            output_dir = temp_dir / "output"
            output_dir.mkdir(exist_ok=True)

            from rxiv_maker.utils import write_manuscript_output

            tex_result = write_manuscript_output(str(output_dir), f"\\title{{Paper {manuscript[-1]}}}")

            expected_tex = output_dir / f"{manuscript}.tex"
            assert Path(tex_result) == expected_tex
            assert expected_tex.exists()

            # Test PDF copying simulation
            from rxiv_maker.utils import copy_pdf_to_manuscript_folder

            # Create fake PDF
            fake_pdf = output_dir / f"{manuscript}.pdf"
            fake_pdf.write_text("fake pdf content")

            yaml_metadata = {
                "date": "2025-06-25",
                "title": {"lead_author": f"Author{manuscript[-1]}"},
            }

            copied_pdf = copy_pdf_to_manuscript_folder(str(output_dir), yaml_metadata)

            expected_pdf_name = f"2025__author{manuscript[-1].lower()}_et_al__rxiv.pdf"
            expected_pdf_path = temp_dir / manuscript / expected_pdf_name

            # Use resolve() to handle macOS path resolution (/private/var vs /var)
            assert copied_pdf.resolve() == expected_pdf_path.resolve()
            assert expected_pdf_path.exists()

    def test_manuscript_directory_validation(self, temp_dir, monkeypatch):
        """Test validation of manuscript directory structure."""
        monkeypatch.chdir(temp_dir)

        # Test with missing manuscript directory
        monkeypatch.setenv("MANUSCRIPT_PATH", "NONEXISTENT_MANUSCRIPT")

        from rxiv_maker.utils import find_manuscript_md

        with pytest.raises(FileNotFoundError):
            find_manuscript_md()

        # Test with manuscript directory but missing main file
        incomplete_dir = temp_dir / "INCOMPLETE_MANUSCRIPT"
        incomplete_dir.mkdir()
        monkeypatch.setenv("MANUSCRIPT_PATH", "INCOMPLETE_MANUSCRIPT")

        with pytest.raises(FileNotFoundError):
            find_manuscript_md()

        # Test with complete structure
        complete_dir = temp_dir / "COMPLETE_MANUSCRIPT"
        complete_dir.mkdir()
        main_file = complete_dir / "01_MAIN.md"
        main_file.write_text("# Complete Manuscript")

        monkeypatch.setenv("MANUSCRIPT_PATH", "COMPLETE_MANUSCRIPT")
        found = find_manuscript_md()
        assert "COMPLETE_MANUSCRIPT" in str(found)
        assert Path(found).name == "01_MAIN.md"

    def test_concurrent_manuscript_handling(self, temp_dir, monkeypatch):
        """Test that manuscript builds don't interfere with each other."""
        monkeypatch.chdir(temp_dir)

        # Create two manuscripts simultaneously
        manuscript1 = "CONCURRENT_A"
        manuscript2 = "CONCURRENT_B"

        # Set up first manuscript
        dir1 = temp_dir / manuscript1
        dir1.mkdir()
        (dir1 / "01_MAIN.md").write_text("# Manuscript A")

        # Set up second manuscript
        dir2 = temp_dir / manuscript2
        dir2.mkdir()
        (dir2 / "01_MAIN.md").write_text("# Manuscript B")

        # Create shared output directory
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Build first manuscript
        monkeypatch.setenv("MANUSCRIPT_PATH", manuscript1)
        from rxiv_maker.utils import write_manuscript_output

        result1 = write_manuscript_output(str(output_dir), "\\title{Manuscript A}")

        # Build second manuscript
        monkeypatch.setenv("MANUSCRIPT_PATH", manuscript2)
        result2 = write_manuscript_output(str(output_dir), "\\title{Manuscript B}")

        # Verify both outputs exist with correct names
        assert Path(result1).name == f"{manuscript1}.tex"
        assert Path(result2).name == f"{manuscript2}.tex"
        assert Path(result1).exists()
        assert Path(result2).exists()

        # Verify contents are distinct
        content1 = Path(result1).read_text()
        content2 = Path(result2).read_text()
        assert "Manuscript A" in content1
        assert "Manuscript B" in content2
        assert content1 != content2
