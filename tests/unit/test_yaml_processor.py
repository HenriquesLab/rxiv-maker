"""Unit tests for the yaml_processor module."""

import pytest

from rxiv_maker.processors.yaml_processor import (
    extract_yaml_metadata,
    get_doi_validation_setting,
    parse_yaml_simple,
)


class TestYAMLProcessor:
    """Test YAML processing functionality."""

    def test_extract_yaml_metadata_from_file(self, temp_dir, sample_markdown):
        """Test extracting YAML metadata from a markdown file."""
        markdown_file = temp_dir / "test.md"
        markdown_file.write_text(sample_markdown)

        metadata = extract_yaml_metadata(str(markdown_file))

        assert metadata is not None
        assert metadata["title"] == "Test Article"
        assert len(metadata["authors"]) == 1
        assert metadata["authors"][0]["name"] == "John Doe"
        assert metadata["keywords"] == ["test", "article"]

    def test_parse_yaml_block(self):
        """Test parsing a YAML block string."""
        yaml_content = """title: "Test Title"
authors:
  - name: "Author One"
    affiliation: "University A"
  - name: "Author Two"
    affiliation: "University B"
keywords: ["research", "testing"]
"""

        metadata = parse_yaml_simple(yaml_content)

        assert metadata["title"] == "Test Title"
        assert len(metadata["authors"]) == 2
        assert metadata["authors"][0]["name"] == "Author One"
        assert metadata["authors"][1]["affiliation"] == "University B"
        assert metadata["keywords"] == ["research", "testing"]

    def test_extract_yaml_metadata_no_yaml(self, temp_dir):
        """Test handling of markdown files without YAML frontmatter."""
        markdown_content = "# Just a title\n\nSome content without YAML."
        markdown_file = temp_dir / "no_yaml.md"
        markdown_file.write_text(markdown_content)

        metadata = extract_yaml_metadata(str(markdown_file))

        assert metadata == {}

    def test_extract_yaml_metadata_invalid_yaml(self, temp_dir):
        """Test handling of invalid YAML frontmatter."""
        markdown_content = """---
title: "Unclosed quote
authors:
  - invalid: yaml: structure
---

# Content
"""
        markdown_file = temp_dir / "invalid_yaml.md"
        markdown_file.write_text(markdown_content)

        # Should handle invalid YAML gracefully
        metadata = extract_yaml_metadata(str(markdown_file))
        assert metadata == {}

    def test_extract_yaml_metadata_missing_file(self):
        """Test handling of missing files."""
        with pytest.raises(FileNotFoundError):
            extract_yaml_metadata("nonexistent_file.md")


class TestDOIValidationSettings:
    """Test DOI validation configuration functionality."""

    def test_get_doi_validation_setting_default(self):
        """Test default behavior when no DOI validation setting is present."""
        metadata = {"title": "Test", "authors": []}
        result = get_doi_validation_setting(metadata)
        assert result is True

    def test_get_doi_validation_setting_empty_metadata(self):
        """Test behavior with empty metadata."""
        metadata = {}
        result = get_doi_validation_setting(metadata)
        assert result is True

    def test_get_doi_validation_setting_none_metadata(self):
        """Test behavior with None metadata."""
        result = get_doi_validation_setting(None)
        assert result is True

    def test_get_doi_validation_setting_explicit_true(self):
        """Test explicit true setting."""
        metadata = {"enable_doi_validation": True}
        result = get_doi_validation_setting(metadata)
        assert result is True

    def test_get_doi_validation_setting_explicit_false(self):
        """Test explicit false setting."""
        metadata = {"enable_doi_validation": False}
        result = get_doi_validation_setting(metadata)
        assert result is False

    def test_get_doi_validation_setting_string_true(self):
        """Test string representations of true."""
        test_cases = ["true", "True", "TRUE", "yes", "Yes", "1", "on", "On"]
        for case in test_cases:
            metadata = {"enable_doi_validation": case}
            result = get_doi_validation_setting(metadata)
            assert result is True, f"Failed for case: {case}"

    def test_get_doi_validation_setting_string_false(self):
        """Test string representations of false."""
        test_cases = ["false", "False", "FALSE", "no", "No", "0", "off", "Off"]
        for case in test_cases:
            metadata = {"enable_doi_validation": case}
            result = get_doi_validation_setting(metadata)
            assert result is False, f"Failed for case: {case}"

    def test_get_doi_validation_setting_numeric(self):
        """Test numeric representations."""
        # Truthy numbers
        for val in [1, 42, -1]:
            metadata = {"enable_doi_validation": val}
            result = get_doi_validation_setting(metadata)
            assert result is True

        # Falsy numbers
        metadata = {"enable_doi_validation": 0}
        result = get_doi_validation_setting(metadata)
        assert result is False
