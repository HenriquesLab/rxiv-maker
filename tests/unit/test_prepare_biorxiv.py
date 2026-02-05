"""Unit tests for bioRxiv author template generation."""

import csv

import pytest

from rxiv_maker.engines.operations.prepare_biorxiv import (
    BioRxivAuthorError,
    encode_html_entities,
    format_author_row,
    generate_biorxiv_author_tsv,
    validate_author_data,
)


class TestValidateAuthorData:
    """Test author data validation."""

    def test_no_authors(self):
        """Test error when no authors provided."""
        with pytest.raises(BioRxivAuthorError, match="No authors found"):
            validate_author_data([])

    def test_no_corresponding_author(self):
        """Test error when no corresponding author marked."""
        authors = [
            {"name": "John Smith", "corresponding_author": False},
            {"name": "Jane Doe", "corresponding_author": False},
        ]
        with pytest.raises(BioRxivAuthorError, match="No corresponding author found"):
            validate_author_data(authors)

    def test_multiple_corresponding_authors(self):
        """Test error when multiple corresponding authors marked."""
        authors = [
            {"name": "John Smith", "corresponding_author": True},
            {"name": "Jane Doe", "corresponding_author": True},
        ]
        with pytest.raises(BioRxivAuthorError, match="Multiple corresponding authors found"):
            validate_author_data(authors)

    def test_valid_single_corresponding_author(self):
        """Test validation passes with single corresponding author."""
        authors = [
            {"name": "John Smith", "corresponding_author": False},
            {"name": "Jane Doe", "corresponding_author": True},
        ]
        # Should not raise
        validate_author_data(authors)

    def test_missing_name(self):
        """Test error when author missing name field."""
        authors = [
            {"email": "test@example.com", "corresponding_author": True},
        ]
        with pytest.raises(BioRxivAuthorError, match="missing the 'name' field"):
            validate_author_data(authors)


class TestFormatAuthorRow:
    """Test formatting individual author rows."""

    def test_basic_author_formatting(self):
        """Test basic author formatting with all fields."""
        author_data = {
            "name": "John A. Smith",
            "email": "john@example.com",
            "affiliations": ["inst1"],
            "corresponding_author": True,
            "orcid": "0000-0001-2345-6789",
        }
        affiliation_map = {
            "inst1": {"full_name": "Example University"},
        }

        row = format_author_row(author_data, affiliation_map)

        assert len(row) == 10
        assert row[0] == "john@example.com"  # Email
        assert row[1] == "Example University"  # Institution
        assert row[2] == "John"  # First name
        assert row[3] == "A."  # Middle name
        assert row[4] == "Smith"  # Last name
        assert row[5] == ""  # Suffix
        assert row[6] == "Yes"  # Corresponding author
        assert row[7] == ""  # Home page URL
        assert row[8] == ""  # Collaborative group
        assert row[9] == "0000-0001-2345-6789"  # ORCiD

    def test_non_corresponding_author(self):
        """Test non-corresponding author formatting."""
        author_data = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "affiliations": ["inst1"],
            "corresponding_author": False,
        }
        affiliation_map = {
            "inst1": {"full_name": "Example University"},
        }

        row = format_author_row(author_data, affiliation_map)
        assert row[6] == ""  # Corresponding author should be empty string for non-corresponding

    def test_comma_format_name(self):
        """Test parsing comma-format names."""
        author_data = {
            "name": "Smith, John Alan",
            "email": "",
            "affiliations": [],
            "corresponding_author": False,
        }
        affiliation_map = {}

        row = format_author_row(author_data, affiliation_map)
        assert row[2] == "John"  # First name
        assert row[3] == "Alan"  # Middle name
        assert row[4] == "Smith"  # Last name

    def test_name_with_suffix(self):
        """Test parsing names with suffixes."""
        author_data = {
            "name": "Martin, James Jr.",
            "email": "",
            "affiliations": [],
            "corresponding_author": False,
        }
        affiliation_map = {}

        row = format_author_row(author_data, affiliation_map)
        assert row[2] == "James"  # First name
        assert row[4] == "Martin"  # Last name
        assert row[5] == "Jr."  # Suffix

    def test_no_email(self):
        """Test author without email."""
        author_data = {
            "name": "John Smith",
            "affiliations": [],
            "corresponding_author": False,
        }
        affiliation_map = {}

        row = format_author_row(author_data, affiliation_map)
        assert row[0] == ""  # Email should be empty string

    def test_no_affiliation(self):
        """Test author without affiliation."""
        author_data = {
            "name": "John Smith",
            "email": "",
            "affiliations": [],
            "corresponding_author": False,
        }
        affiliation_map = {}

        row = format_author_row(author_data, affiliation_map)
        assert row[1] == ""  # Institution should be empty string

    def test_multiple_affiliations_uses_first(self):
        """Test that only first affiliation is used."""
        author_data = {
            "name": "John Smith",
            "email": "",
            "affiliations": ["inst1", "inst2"],
            "corresponding_author": False,
        }
        affiliation_map = {
            "inst1": {"full_name": "Primary University"},
            "inst2": {"full_name": "Secondary Institute"},
        }

        row = format_author_row(author_data, affiliation_map)
        assert row[1] == "Primary University"  # Only first affiliation


class TestGenerateBiorxivAuthorTsv:
    """Test full TSV generation."""

    def test_tsv_generation_creates_file(self, tmp_path):
        """Test that TSV file is created successfully."""
        # Create a minimal config file
        config_path = tmp_path / "00_CONFIG.yml"
        config_content = """
authors:
  - name: John Smith
    email: john@example.com
    affiliations: [inst1]
    corresponding_author: true
    orcid: 0000-0001-2345-6789

affiliations:
  - shortname: inst1
    full_name: Example University
"""
        config_path.write_text(config_content)

        output_path = tmp_path / "output" / "biorxiv_authors.tsv"

        # Generate TSV
        result_path = generate_biorxiv_author_tsv(config_path, output_path)

        # Verify file exists
        assert result_path.exists()
        assert result_path == output_path

    def test_tsv_format_and_content(self, tmp_path):
        """Test that TSV has correct format and content."""
        config_path = tmp_path / "00_CONFIG.yml"
        config_content = """
authors:
  - name: Smith, John A.
    email: john@example.com
    affiliations: [inst1]
    corresponding_author: true
    orcid: 0000-0001-2345-6789

affiliations:
  - shortname: inst1
    full_name: Example University
"""
        config_path.write_text(config_content)

        output_path = tmp_path / "biorxiv_authors.tsv"
        generate_biorxiv_author_tsv(config_path, output_path)

        # Read and verify TSV
        with open(output_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            rows = list(reader)

        # Check header
        assert len(rows) == 2  # Header + 1 author
        header = rows[0]
        assert header[0] == "Email"
        assert header[2] == "First Name"
        assert header[6] == "Corresponding Author"

        # Check author data
        author_row = rows[1]
        assert author_row[0] == "john@example.com"
        assert author_row[1] == "Example University"
        assert author_row[2] == "John"
        assert author_row[3] == "A."
        assert author_row[4] == "Smith"
        assert author_row[6] == "Yes"
        assert author_row[9] == "0000-0001-2345-6789"

    def test_email64_decoding(self, tmp_path):
        """Test that email64 is properly decoded."""
        config_path = tmp_path / "00_CONFIG.yml"
        # Base64 for "test@example.com"
        config_content = """
authors:
  - name: John Smith
    email64: dGVzdEBleGFtcGxlLmNvbQ==
    affiliations: [inst1]
    corresponding_author: true

affiliations:
  - shortname: inst1
    full_name: Example University
"""
        config_path.write_text(config_content)

        output_path = tmp_path / "biorxiv_authors.tsv"
        generate_biorxiv_author_tsv(config_path, output_path)

        with open(output_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            rows = list(reader)

        assert rows[1][0] == "test@example.com"

    def test_config_file_not_found(self, tmp_path):
        """Test error when config file doesn't exist."""
        config_path = tmp_path / "nonexistent.yml"
        output_path = tmp_path / "output.tsv"

        with pytest.raises(FileNotFoundError):
            generate_biorxiv_author_tsv(config_path, output_path)

    def test_multiple_authors(self, tmp_path):
        """Test TSV with multiple authors."""
        config_path = tmp_path / "00_CONFIG.yml"
        config_content = """
authors:
  - name: John Smith
    email: john@example.com
    affiliations: [inst1]
    corresponding_author: false
  - name: Jane Doe
    email: jane@example.com
    affiliations: [inst2]
    corresponding_author: true

affiliations:
  - shortname: inst1
    full_name: University A
  - shortname: inst2
    full_name: University B
"""
        config_path.write_text(config_content)

        output_path = tmp_path / "biorxiv_authors.tsv"
        generate_biorxiv_author_tsv(config_path, output_path)

        with open(output_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            rows = list(reader)

        assert len(rows) == 3  # Header + 2 authors
        assert rows[1][6] == ""  # First author not corresponding (empty string)
        assert rows[2][6] == "Yes"  # Second author is corresponding


class TestEncodeHtmlEntities:
    """Test HTML entity encoding for special characters."""

    def test_accented_characters(self):
        """Test encoding of common accented characters."""
        # Portuguese/Spanish characters
        assert encode_html_entities("António") == "Ant&oacute;nio"
        assert encode_html_entities("José") == "Jos&eacute;"
        assert encode_html_entities("García") == "Garc&iacute;a"

    def test_nordic_characters(self):
        """Test encoding of Nordic characters."""
        assert encode_html_entities("Åbo") == "&Aring;bo"
        assert encode_html_entities("Øyvind") == "&Oslash;yvind"

    def test_complex_text(self):
        """Test encoding of text with multiple special characters."""
        text = "Instituto de Tecnologia Química e Biológica António Xavier"
        expected = "Instituto de Tecnologia Qu&iacute;mica e Biol&oacute;gica Ant&oacute;nio Xavier"
        assert encode_html_entities(text) == expected

    def test_no_special_characters(self):
        """Test that text without special characters is unchanged."""
        text = "Bruno Saraiva"
        assert encode_html_entities(text) == text

    def test_empty_string(self):
        """Test that empty string is handled correctly."""
        assert encode_html_entities("") == ""

    def test_none_value(self):
        """Test that None is handled correctly."""
        assert encode_html_entities(None) is None

    def test_author_formatting_with_html_entities(self):
        """Test that author formatting correctly encodes HTML entities."""
        author_data = {
            "name": "António da Silva",
            "email": "antonio@example.com",
            "affiliations": ["inst1"],
            "corresponding_author": False,
        }
        affiliation_map = {
            "inst1": {"full_name": "Universidade de São Paulo"},
        }

        row = format_author_row(author_data, affiliation_map)

        # Check that name components have HTML entities
        assert row[2] == "Ant&oacute;nio"  # First name
        assert row[4] == "da Silva"  # Last name (no special chars)
        # Check institution has HTML entities
        assert "S&atilde;o Paulo" in row[1]
