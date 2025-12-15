"""Integration tests for bibliography author name formatting in DOCX export."""

import pytest
from docx import Document

from rxiv_maker.exporters.docx_exporter import DocxExporter


class TestBibliographyAuthorFormatDocx:
    """Test bibliography author name formatting in DOCX exports."""

    @pytest.fixture
    def temp_manuscript(self, tmp_path):
        """Create a temporary manuscript with configurable author format."""
        manuscript_dir = tmp_path / "test_manuscript"
        manuscript_dir.mkdir()

        # Create main markdown file
        main_md = manuscript_dir / "01_MAIN.md"
        main_md.write_text(
            """---
title: "Test Manuscript for Author Format"
authors:
  - name: "Test Author"
    affiliation: "Test University"
keywords: ["test"]
citation_style: "numbered"
---

# Introduction

This manuscript tests author name formatting [@smith2021;@jones2022].

# Methods

We used standard methods [@doe2020].
"""
        )

        # Create bibliography file with various author name formats
        bib_file = manuscript_dir / "03_REFERENCES.bib"
        bib_file.write_text(
            """@article{smith2021,
  author = {Smith, John Alan and Johnson, Mary Beth},
  title = {First Test Article},
  journal = {Nature},
  year = {2021},
  volume = {500},
  pages = {1--10},
  doi = {10.1234/nature.2021.001}
}

@article{jones2022,
  author = {Jones, Sarah Jane and Brown, Robert Charles and Garcia-Lopez, Maria},
  title = {Second Test Article},
  journal = {Science},
  year = {2022},
  volume = {600},
  pages = {20--30}
}

@article{doe2020,
  author = {Doe, J. and Smith, A. B.},
  title = {Third Test Article},
  journal = {Cell},
  year = {2020},
  volume = {400},
  pages = {5--15}
}

@article{vonneumann1945,
  author = {von Neumann, John},
  title = {Single Author Article},
  journal = {Math Review},
  year = {1945},
  volume = {1},
  pages = {1--5}
}
"""
        )

        return manuscript_dir

    def _create_config_file(self, manuscript_dir, author_format):
        """Create config file with specified author format."""
        # Use rxiv.yml which is what ConfigManager looks for
        config_file = manuscript_dir / "rxiv.yml"
        config_file.write_text(
            f"""title: "Test Manuscript"
authors:
  - name: "Test Author"
keywords: ["test"]
citation_style: "numbered"
bibliography_author_format: "{author_format}"
"""
        )

    def _extract_bibliography_text(self, docx_path):
        """Extract bibliography section text from DOCX file."""
        doc = Document(str(docx_path))

        # Find bibliography section
        in_bibliography = False
        bibliography_text = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if text == "Bibliography":
                in_bibliography = True
                continue
            if in_bibliography and text:
                bibliography_text.append(text)

        return "\n".join(bibliography_text)

    def test_lastname_firstname_format(self, temp_manuscript):
        """Test lastname_firstname format (default)."""
        self._create_config_file(temp_manuscript, "lastname_firstname")

        exporter = DocxExporter(
            manuscript_path=str(temp_manuscript),
            resolve_dois=False,
            include_footnotes=True,
        )

        result_path = exporter.export()
        assert result_path.exists()

        # Extract bibliography text
        bib_text = self._extract_bibliography_text(result_path)

        # Check author formatting
        assert "Smith, John Alan and Johnson, Mary Beth" in bib_text
        assert "Jones, Sarah Jane and Brown, Robert Charles and Garcia-Lopez, Maria" in bib_text
        assert "Doe, J. and Smith, A. B." in bib_text
        # Note: vonneumann1945 not cited, won't appear in bibliography

    def test_lastname_initials_format(self, temp_manuscript):
        """Test lastname_initials format."""
        self._create_config_file(temp_manuscript, "lastname_initials")

        exporter = DocxExporter(
            manuscript_path=str(temp_manuscript),
            resolve_dois=False,
            include_footnotes=True,
        )

        result_path = exporter.export()
        assert result_path.exists()

        # Extract bibliography text
        bib_text = self._extract_bibliography_text(result_path)

        # Check author formatting - should have initials
        assert "Smith, J.A." in bib_text
        assert "Johnson, M.B." in bib_text
        assert "Jones, S.J." in bib_text
        assert "Brown, R.C." in bib_text
        assert "Garcia-Lopez, M." in bib_text
        # Note: vonneumann1945 is not cited in the test markdown, so won't appear in bibliography

    def test_firstname_lastname_format(self, temp_manuscript):
        """Test firstname_lastname format."""
        self._create_config_file(temp_manuscript, "firstname_lastname")

        exporter = DocxExporter(
            manuscript_path=str(temp_manuscript),
            resolve_dois=False,
            include_footnotes=True,
        )

        result_path = exporter.export()
        assert result_path.exists()

        # Extract bibliography text
        bib_text = self._extract_bibliography_text(result_path)

        # Check author formatting - firstname lastname order
        assert "John Alan Smith" in bib_text
        assert "Mary Beth Johnson" in bib_text
        assert "Sarah Jane Jones" in bib_text
        assert "Robert Charles Brown" in bib_text
        assert "Maria Garcia-Lopez" in bib_text
        # Note: vonneumann1945 not cited, won't appear in bibliography

    def test_default_format_when_not_specified(self, temp_manuscript):
        """Test that default format is lastname_firstname when not specified."""
        # Don't create config file, rely on defaults

        exporter = DocxExporter(
            manuscript_path=str(temp_manuscript),
            resolve_dois=False,
            include_footnotes=True,
        )

        result_path = exporter.export()
        assert result_path.exists()

        # Extract bibliography text
        bib_text = self._extract_bibliography_text(result_path)

        # Should use lastname_firstname (default)
        assert "Smith, John Alan" in bib_text or "Smith, J.A." in bib_text  # Depending on .bib format

    def test_format_consistency_across_entries(self, temp_manuscript):
        """Test that format is applied consistently to all entries."""
        self._create_config_file(temp_manuscript, "lastname_initials")

        exporter = DocxExporter(
            manuscript_path=str(temp_manuscript),
            resolve_dois=False,
            include_footnotes=True,
        )

        result_path = exporter.export()
        bib_text = self._extract_bibliography_text(result_path)

        # All entries should have initials format, not mixed
        # Count periods after capital letters (initials)
        import re

        initial_pattern = r"\b[A-Z]\."
        initials_count = len(re.findall(initial_pattern, bib_text))

        # Should have many initials (at least one per author)
        assert initials_count >= 7  # We have multiple authors with middle names

    def test_handles_already_initialized_names(self, temp_manuscript):
        """Test that already-initialized names in .bib are handled correctly."""
        self._create_config_file(temp_manuscript, "lastname_firstname")

        exporter = DocxExporter(
            manuscript_path=str(temp_manuscript),
            resolve_dois=False,
            include_footnotes=True,
        )

        result_path = exporter.export()
        bib_text = self._extract_bibliography_text(result_path)

        # "Doe, J." should be expanded or kept as is
        assert "Doe, J." in bib_text or "Doe," in bib_text
