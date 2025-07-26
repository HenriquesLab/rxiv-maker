"""Unit tests for the yaml_processor module."""

import pytest

from rxiv_maker.processors.yaml_processor import (
    extract_yaml_metadata,
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
