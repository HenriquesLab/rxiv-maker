"""Unit tests for the utils module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from rxiv_maker.utils import (
    copy_pdf_to_manuscript_folder,
    create_output_dir,
    find_manuscript_md,
    get_custom_pdf_filename,
    write_manuscript_output,
)


class TestUtils:
    """Test utility functions."""

    def test_create_output_dir(self, temp_dir):
        """Test creating output directory."""
        output_path = temp_dir / "output"
        create_output_dir(str(output_path))

        assert output_path.exists()
        assert output_path.is_dir()

    def test_create_output_dir_existing(self, temp_dir):
        """Test creating output directory when it already exists."""
        output_path = temp_dir / "existing_output"
        output_path.mkdir()

        # Should not raise error
        create_output_dir(str(output_path))
        assert output_path.exists()

    def test_find_manuscript_md_standard_name(self, temp_dir, monkeypatch):
        """Test finding manuscript markdown with standard name."""
        # Change to temp directory
        monkeypatch.chdir(temp_dir)

        # Clean up environment variable to ensure clean test
        import os

        if "MANUSCRIPT_PATH" in os.environ:
            monkeypatch.delenv("MANUSCRIPT_PATH")

        # Create manuscript directory and file
        manuscript_dir = temp_dir / "MANUSCRIPT"
        manuscript_dir.mkdir()
        manuscript_file = manuscript_dir / "01_MAIN.md"
        manuscript_file.write_text("# Test Manuscript")

        result = find_manuscript_md()
        assert Path(result).name == "01_MAIN.md"

    def test_find_manuscript_md_custom_path(self, temp_dir, monkeypatch):
        """Test finding manuscript markdown with custom path."""
        # Change to temp directory
        monkeypatch.chdir(temp_dir)

        # Set custom manuscript path
        monkeypatch.setenv("MANUSCRIPT_PATH", "MY_PAPER")

        # Create custom manuscript directory and file
        manuscript_dir = temp_dir / "MY_PAPER"
        manuscript_dir.mkdir()
        manuscript_file = manuscript_dir / "01_MAIN.md"
        manuscript_file.write_text("# Test Manuscript")

        result = find_manuscript_md()
        assert Path(result).name == "01_MAIN.md"
        assert "MY_PAPER" in str(result)

    def test_find_manuscript_md_not_found(self, temp_dir, monkeypatch):
        """Test finding manuscript markdown when none exists."""
        # Change to temp directory with no manuscript files
        monkeypatch.chdir(temp_dir)

        with pytest.raises(FileNotFoundError):
            find_manuscript_md()

    def test_write_manuscript_output(self, temp_dir, monkeypatch):
        """Test writing manuscript output to file."""
        # Clean up environment variable to ensure predictable behavior
        import os

        if "MANUSCRIPT_PATH" in os.environ:
            monkeypatch.delenv("MANUSCRIPT_PATH")

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        latex_content = r"""
        \documentclass{article}
        \title{Test Manuscript}
        \begin{document}
        \maketitle
        Test content
        \end{document}
        """

        result_file = write_manuscript_output(str(output_dir), latex_content)

        assert Path(result_file).exists()
        assert Path(result_file).suffix == ".tex"
        # The filename should match the manuscript path (default: MANUSCRIPT)
        manuscript_path = os.getenv("MANUSCRIPT_PATH", "MANUSCRIPT")
        expected_name = f"{os.path.basename(manuscript_path)}.tex"
        assert Path(result_file).name == expected_name

        # Check content was written
        written_content = Path(result_file).read_text()
        assert "Test Manuscript" in written_content
        assert r"\documentclass{article}" in written_content

    def test_write_manuscript_output_overwrite(self, temp_dir):
        """Test overwriting existing manuscript output."""
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Write initial content
        initial_content = r"\documentclass{article}\title{Initial}"
        result_file = write_manuscript_output(str(output_dir), initial_content)

        # Write new content
        new_content = r"\documentclass{article}\title{Updated}"
        result_file_2 = write_manuscript_output(str(output_dir), new_content)

        # Should be same file
        assert result_file == result_file_2

        # Content should be updated
        written_content = Path(result_file).read_text()
        assert "Updated" in written_content
        assert "Initial" not in written_content

    def test_get_custom_pdf_filename_with_yaml_metadata(self):
        """Test generating custom PDF filename from YAML metadata."""
        # Test with complete metadata
        yaml_metadata = {"date": "2025-06-25", "title": {"lead_author": "Smith"}}

        result = get_custom_pdf_filename(yaml_metadata)
        assert result == "2025__smith_et_al__rxiv.pdf"

        # Test with different author format (list)
        yaml_metadata_list = {
            "date": "2024-12-01",
            "title": [{"lead_author": "García-López"}, {"other": "data"}],
        }

        result = get_custom_pdf_filename(yaml_metadata_list)
        assert result == "2024__garcía-lópez_et_al__rxiv.pdf"

        # Test with missing metadata (fallback to current year and unknown)
        import datetime

        current_year = str(datetime.datetime.now().year)

        yaml_metadata_minimal = {}
        result = get_custom_pdf_filename(yaml_metadata_minimal)
        assert result == f"{current_year}__unknown_et_al__rxiv.pdf"

    def test_copy_pdf_to_manuscript_folder_success(self, temp_dir, monkeypatch):
        """Test successfully copying PDF to manuscript folder with custom naming."""
        # Set up test environment
        monkeypatch.chdir(temp_dir)
        monkeypatch.setenv("MANUSCRIPT_PATH", "MY_PAPER")

        # Create manuscript directory
        manuscript_dir = temp_dir / "MY_PAPER"
        manuscript_dir.mkdir()

        # Create output directory with a test PDF
        output_dir = temp_dir / "output"
        output_dir.mkdir()
        test_pdf = output_dir / "MY_PAPER.pdf"
        test_pdf.write_text("fake pdf content")

        # Test metadata for custom naming
        yaml_metadata = {"date": "2025-01-15", "title": {"lead_author": "TestAuthor"}}

        # Copy PDF with custom naming
        result = copy_pdf_to_manuscript_folder(str(output_dir), yaml_metadata)

        # Verify the PDF was copied with correct name
        expected_pdf = manuscript_dir / "2025__testauthor_et_al__rxiv.pdf"
        assert expected_pdf.exists()
        assert expected_pdf.read_text() == "fake pdf content"
        # Use resolve() to handle macOS path resolution
        assert result.resolve() == expected_pdf.resolve()

    def test_copy_pdf_to_manuscript_folder_missing_pdf(self, temp_dir, monkeypatch):
        """Test behavior when source PDF is missing."""
        monkeypatch.chdir(temp_dir)
        monkeypatch.setenv("MANUSCRIPT_PATH", "MY_PAPER")

        # Create manuscript directory but no output directory/PDF
        manuscript_dir = temp_dir / "MY_PAPER"
        manuscript_dir.mkdir()

        output_dir = temp_dir / "output"
        output_dir.mkdir()
        # No PDF file created

        yaml_metadata = {"date": "2025", "title": {"lead_author": "Test"}}

        result = copy_pdf_to_manuscript_folder(str(output_dir), yaml_metadata)
        assert result is None

    def test_write_manuscript_output_custom_path(self, temp_dir, monkeypatch):
        """Test writing manuscript output with custom manuscript path."""
        monkeypatch.setenv("MANUSCRIPT_PATH", "CUSTOM_MANUSCRIPT")

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        latex_content = r"\documentclass{article}\title{Custom Path Test}"

        result_file = write_manuscript_output(str(output_dir), latex_content)

        # Should use custom path name for output file
        assert Path(result_file).name == "CUSTOM_MANUSCRIPT.tex"
        assert "Custom Path Test" in Path(result_file).read_text()


class TestManuscriptDirectorySetup:
    """Test setting up new manuscript directories and build validation."""

    def test_setup_new_manuscript_directory_structure(self, temp_dir, monkeypatch):
        """Test setting up a complete new manuscript directory."""
        monkeypatch.chdir(temp_dir)

        # Create new manuscript with custom path
        manuscript_path = "NEW_RESEARCH_PROJECT"
        monkeypatch.setenv("MANUSCRIPT_PATH", manuscript_path)

        # Create the manuscript directory structure
        manuscript_dir = temp_dir / manuscript_path
        manuscript_dir.mkdir()

        # Create required files
        config_file = manuscript_dir / "00_CONFIG.yml"
        config_content = """
title:
  main: "New Research on AI Systems"
  lead_author: "researcher"
date: "2025-06-25"
authors:
  - name: "Dr. Researcher"
    affiliation: "University of Testing"
    email: "researcher@test.edu"
"""
        config_file.write_text(config_content)

        main_file = manuscript_dir / "01_MAIN.md"
        main_content = """---
title: "New Research on AI Systems"
authors:
  - name: "Dr. Researcher"
    affiliation: "University of Testing"
    email: "researcher@test.edu"
---

# Introduction

This is a new manuscript for testing the directory setup.

## Methods

Testing methodology here.

## Results

Results go here.
"""
        main_file.write_text(main_content)

        bib_file = manuscript_dir / "03_REFERENCES.bib"
        bib_content = """@article{example2025,
  title={Example Reference},
  author={Example, Author},
  journal={Test Journal},
  year={2025}
}"""
        bib_file.write_text(bib_content)

        # Create figures directory
        figures_dir = manuscript_dir / "FIGURES"
        figures_dir.mkdir()

        # Test that find_manuscript_md works with new structure
        found_manuscript = find_manuscript_md()
        assert Path(found_manuscript).name == "01_MAIN.md"
        assert manuscript_path in str(found_manuscript)

        # Test output directory creation
        output_dir = temp_dir / "output"
        create_output_dir(str(output_dir))
        assert output_dir.exists()

        # Test writing manuscript output with correct naming
        test_content = "\\documentclass{article}\\title{Test}"
        result_file = write_manuscript_output(str(output_dir), test_content)

        # Should use the custom manuscript name
        expected_name = f"{manuscript_path}.tex"
        assert Path(result_file).name == expected_name

    def test_build_places_files_in_correct_locations(self, temp_dir, monkeypatch):
        """Test that build process places files correctly with correct names."""
        monkeypatch.chdir(temp_dir)

        # Set up custom manuscript path
        manuscript_path = "AI_RESEARCH_2025"
        monkeypatch.setenv("MANUSCRIPT_PATH", manuscript_path)

        # Create manuscript structure
        manuscript_dir = temp_dir / manuscript_path
        manuscript_dir.mkdir()

        # Create metadata that will generate specific PDF name
        yaml_metadata = {"date": "2025-06-25", "title": {"lead_author": "Rodriguez"}}

        # Create a fake PDF in output directory
        output_dir = temp_dir / "output"
        output_dir.mkdir()
        source_pdf = output_dir / f"{manuscript_path}.pdf"
        source_pdf.write_text("test pdf content")

        # Test the copy operation
        result_pdf = copy_pdf_to_manuscript_folder(str(output_dir), yaml_metadata)

        # Verify correct location and naming
        expected_location = manuscript_dir / "2025__rodriguez_et_al__rxiv.pdf"
        # Use resolve() to handle macOS path resolution (/private/var vs /var)
        assert result_pdf.resolve() == expected_location.resolve()
        assert expected_location.exists()
        assert expected_location.read_text() == "test pdf content"

        # Test LaTeX output naming
        latex_content = "\\documentclass{article}\\title{AI Research}"
        tex_result = write_manuscript_output(str(output_dir), latex_content)

        expected_tex = output_dir / f"{manuscript_path}.tex"
        assert Path(tex_result) == expected_tex
        assert expected_tex.exists()

    def test_multiple_manuscript_directories_isolated(self, temp_dir, monkeypatch):
        """Test that multiple manuscript directories work independently."""
        monkeypatch.chdir(temp_dir)

        # Create first manuscript
        manuscript1 = "PROJECT_ALPHA"
        monkeypatch.setenv("MANUSCRIPT_PATH", manuscript1)

        dir1 = temp_dir / manuscript1
        dir1.mkdir()
        (dir1 / "01_MAIN.md").write_text("# Project Alpha")

        # Verify first manuscript is found
        found1 = find_manuscript_md()
        assert manuscript1 in str(found1)

        # Switch to second manuscript
        manuscript2 = "PROJECT_BETA"
        monkeypatch.setenv("MANUSCRIPT_PATH", manuscript2)

        dir2 = temp_dir / manuscript2
        dir2.mkdir()
        (dir2 / "01_MAIN.md").write_text("# Project Beta")

        # Verify second manuscript is found
        found2 = find_manuscript_md()
        assert manuscript2 in str(found2)
        assert manuscript1 not in str(found2)

        # Test that output files get correct names
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Test with first manuscript
        monkeypatch.setenv("MANUSCRIPT_PATH", manuscript1)
        result1 = write_manuscript_output(str(output_dir), "\\title{Alpha}")
        assert Path(result1).name == f"{manuscript1}.tex"

        # Test with second manuscript
        monkeypatch.setenv("MANUSCRIPT_PATH", manuscript2)
        result2 = write_manuscript_output(str(output_dir), "\\title{Beta}")
        assert Path(result2).name == f"{manuscript2}.tex"

        # Both files should exist with different names
        assert Path(result1).exists()
        assert Path(result2).exists()
        assert result1 != result2

    def test_complete_manuscript_setup_from_scratch(self, temp_dir, monkeypatch):
        """Test complete setup of a new manuscript directory from scratch."""
        monkeypatch.chdir(temp_dir)

        # Set up a completely new manuscript project
        project_name = "BREAKTHROUGH_RESEARCH_2025"
        monkeypatch.setenv("MANUSCRIPT_PATH", project_name)

        # Create the manuscript directory structure as a user would
        manuscript_dir = temp_dir / project_name
        manuscript_dir.mkdir()

        # Create all required directories
        figures_dir = manuscript_dir / "FIGURES"
        figures_dir.mkdir()

        # Create config file with realistic metadata
        config_file = manuscript_dir / "00_CONFIG.yml"
        config_content = """---
title:
  main: "Breakthrough Research in Quantum Computing"
  lead_author: "Smith-Johnson"
date: "2025-12-15"
authors:
  - name: "Dr. Alice Smith-Johnson"
    affiliation: "Quantum Research Institute"
    email: "a.smith-johnson@qri.edu"
    orcid: "0000-0001-2345-6789"
  - name: "Prof. Bob Chen"
    affiliation: "Advanced Computing Lab"
    email: "b.chen@acl.edu"
affiliations:
  - name: "Quantum Research Institute"
    address: "123 Quantum Ave, Tech City, TC 12345, USA"
  - name: "Advanced Computing Lab"
    address: "456 Computing Blvd, Science City, SC 67890, USA"
keywords: ["quantum computing", "breakthrough research", "algorithms"]
abstract: "We present breakthrough research in quantum computing algorithms."
"""
        config_file.write_text(config_content)

        # Create main manuscript
        main_file = manuscript_dir / "01_MAIN.md"
        main_content = """---
title: "Breakthrough Research in Quantum Computing"
authors:
  - name: "Dr. Alice Smith-Johnson"
    affiliation: "Quantum Research Institute"
    email: "a.smith-johnson@qri.edu"
  - name: "Prof. Bob Chen"
    affiliation: "Advanced Computing Lab"
    email: "b.chen@acl.edu"
keywords: ["quantum computing", "algorithms"]
---

# Introduction

This research presents breakthrough findings in quantum computing.

# Methods

Our innovative methodology combines classical and quantum approaches.

# Results

The results demonstrate significant improvements over existing methods.

# Conclusion

This work opens new possibilities for quantum computing applications.
"""
        main_file.write_text(main_content)

        # Create bibliography
        bib_file = manuscript_dir / "03_REFERENCES.bib"
        bib_content = """@article{quantum2024,
  title={Quantum Computing Advances},
  author={Quantum, Alice and Computing, Bob},
  journal={Nature Quantum},
  volume={10},
  pages={123-145},
  year={2024}
}"""
        bib_file.write_text(bib_content)

        # Create supplementary info
        supp_file = manuscript_dir / "02_SUPPLEMENTARY_INFO.md"
        supp_content = """# Supplementary Information

## Additional Methods

Detailed methodology descriptions.

## Additional Results

Extended results and analysis.
"""
        supp_file.write_text(supp_content)

        # Test the manuscript discovery
        found_manuscript = find_manuscript_md()
        assert Path(found_manuscript).name == "01_MAIN.md"
        assert project_name in str(found_manuscript)

        # Test output directory creation and file generation
        output_dir = temp_dir / "output"
        create_output_dir(str(output_dir))
        assert output_dir.exists()

        # Test LaTeX output generation with correct naming
        latex_content = r"""
\documentclass[letterpaper,10pt]{article}
\title{Breakthrough Research in Quantum Computing}
\author{Dr. Alice Smith-Johnson and Prof. Bob Chen}
\begin{document}
\maketitle
\section{Introduction}
This research presents breakthrough findings.
\end{document}
"""
        result_tex = write_manuscript_output(str(output_dir), latex_content)
        expected_tex_name = f"{project_name}.tex"
        assert Path(result_tex).name == expected_tex_name
        assert Path(result_tex).exists()

        # Verify content was written correctly
        written_content = Path(result_tex).read_text()
        assert "Breakthrough Research" in written_content
        assert r"\documentclass" in written_content

        # Test PDF naming and placement
        # Create a mock PDF file
        mock_pdf = output_dir / f"{project_name}.pdf"
        mock_pdf.write_text("mock pdf content for testing")

        # Test custom PDF naming based on metadata
        yaml_metadata = {
            "date": "2025-12-15",
            "title": {"lead_author": "Smith-Johnson"},
        }

        copied_pdf = copy_pdf_to_manuscript_folder(str(output_dir), yaml_metadata)

        # Verify correct custom naming: 2025__smith-johnson_et_al__rxiv.pdf
        expected_pdf_name = "2025__smith-johnson_et_al__rxiv.pdf"
        expected_pdf_path = manuscript_dir / expected_pdf_name

        assert copied_pdf.resolve() == expected_pdf_path.resolve()
        assert expected_pdf_path.exists()
        assert expected_pdf_path.read_text() == "mock pdf content for testing"

        print(f"✅ Complete manuscript setup validated for: {project_name}")

    def test_build_with_special_characters_in_names(self, temp_dir, monkeypatch):
        """Test build handles special characters in manuscript and author names."""
        monkeypatch.chdir(temp_dir)

        # Test with manuscript path containing underscores and numbers
        manuscript_path = "AI_ML_2025_STUDY"
        monkeypatch.setenv("MANUSCRIPT_PATH", manuscript_path)

        # Create manuscript directory
        manuscript_dir = temp_dir / manuscript_path
        manuscript_dir.mkdir()
        (manuscript_dir / "01_MAIN.md").write_text("# ML Study")

        # Test that manuscript finding works with special characters
        found = find_manuscript_md()
        assert manuscript_path in str(found)

        # Test output file naming with special characters
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        result_tex = write_manuscript_output(str(output_dir), "\\title{ML Study}")
        expected_name = f"{manuscript_path}.tex"
        assert Path(result_tex).name == expected_name

        # Test PDF naming with special author names
        yaml_metadata = {
            "date": "2025-06-25",
            "title": {"lead_author": "García-López O'Connor"},
        }

        # Create mock PDF
        mock_pdf = output_dir / f"{manuscript_path}.pdf"
        mock_pdf.write_text("mock content")

        copied_pdf = copy_pdf_to_manuscript_folder(str(output_dir), yaml_metadata)

        # Should clean special characters appropriately
        expected_pdf_name = "2025__garcía-lópez_o'connor_et_al__rxiv.pdf"
        expected_pdf_path = manuscript_dir / expected_pdf_name

        assert copied_pdf.resolve() == expected_pdf_path.resolve()
        assert expected_pdf_path.exists()

    def test_manuscript_directory_permissions_and_error_handling(self, temp_dir, monkeypatch):
        """Test error handling for various manuscript directory issues."""
        monkeypatch.chdir(temp_dir)

        # Test with non-existent manuscript directory
        monkeypatch.setenv("MANUSCRIPT_PATH", "NON_EXISTENT_DIR")

        with pytest.raises(FileNotFoundError, match="01_MAIN.md not found"):
            find_manuscript_md()

        # Test with manuscript directory that exists but has no main file
        empty_dir = temp_dir / "EMPTY_MANUSCRIPT"
        empty_dir.mkdir()
        monkeypatch.setenv("MANUSCRIPT_PATH", "EMPTY_MANUSCRIPT")

        with pytest.raises(FileNotFoundError, match="01_MAIN.md not found"):
            find_manuscript_md()

        # Test with manuscript directory that has incorrect file structure
        wrong_structure_dir = temp_dir / "WRONG_STRUCTURE"
        wrong_structure_dir.mkdir()
        (wrong_structure_dir / "main.md").write_text("# Wrong name")  # Wrong filename
        monkeypatch.setenv("MANUSCRIPT_PATH", "WRONG_STRUCTURE")

        with pytest.raises(FileNotFoundError, match="01_MAIN.md not found"):
            find_manuscript_md()

        # Test PDF copying with missing source PDF
        valid_dir = temp_dir / "VALID_MANUSCRIPT"
        valid_dir.mkdir()
        (valid_dir / "01_MAIN.md").write_text("# Valid")
        monkeypatch.setenv("MANUSCRIPT_PATH", "VALID_MANUSCRIPT")

        output_dir = temp_dir / "output"
        output_dir.mkdir()
        # No PDF file created - should handle gracefully

        yaml_metadata = {"date": "2025", "title": {"lead_author": "Test"}}
        result = copy_pdf_to_manuscript_folder(str(output_dir), yaml_metadata)

        # Should return None for missing PDF
        assert result is None


class TestMultiLanguageUnicode:
    """Test Unicode handling for multiple languages and scripts."""

    def test_unicode_support_detection(self):
        """Test Unicode support detection."""
        from rxiv_maker.utils.unicode_safe import supports_unicode

        # Should return a boolean
        result = supports_unicode()
        assert isinstance(result, bool)

    def test_safe_print_with_various_languages(self):
        """Test safe_print with various language texts."""
        from unittest.mock import patch

        from rxiv_maker.utils.unicode_safe import safe_print

        texts = {
            "English": "Hello, World!",
            "Spanish": "¡Hola, Mundo! ñáéíóú",
            "French": "Bonjour, Monde! àâçèéêëîïôùûü",
            "German": "Hallo, Welt! äöüßÄÖÜ",
            "Chinese": "你好，世界！",
            "Japanese": "こんにちは、世界！",
            "Russian": "Привет, мир!",
            "Greek": "Γεια σου κόσμε!",
        }

        # Test that safe_print handles all languages without crashing
        with patch("builtins.print") as mock_print:
            for _, text in texts.items():
                safe_print(text)
                # Should have been called
                assert mock_print.called

    def test_get_safe_icon(self):
        """Test get_safe_icon function."""
        from rxiv_maker.utils.unicode_safe import get_safe_icon

        # Test with Unicode support
        with patch("rxiv_maker.utils.unicode_safe.supports_unicode", return_value=True):
            icon = get_safe_icon("✅", "[OK]")
            assert icon == "✅"

        # Test without Unicode support
        with patch("rxiv_maker.utils.unicode_safe.supports_unicode", return_value=False):
            icon = get_safe_icon("✅", "[OK]")
            assert icon == "[OK]"

    def test_safe_print_fallback(self):
        """Test safe_print fallback for non-Unicode environments."""
        from unittest.mock import patch

        from rxiv_maker.utils.unicode_safe import safe_print

        # Test normal print works
        with patch("builtins.print") as mock_print:
            safe_print("Test with emoji ✅")
            mock_print.assert_called_with("Test with emoji ✅")

        # Test fallback on UnicodeEncodeError
        with patch("builtins.print") as mock_print:
            mock_print.side_effect = [
                UnicodeEncodeError("utf-8", "✅", 0, 1, "test"),
                None,
            ]
            safe_print("Test with emoji ✅")
            # Should have tried twice - first with original, then with ASCII
            assert mock_print.call_count == 2
