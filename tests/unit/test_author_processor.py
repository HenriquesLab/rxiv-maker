"""Unit tests for the author_processor module."""

from rxiv_maker.processors.author_processor import (
    generate_authors_and_affiliations,
    generate_corresponding_authors,
    generate_extended_author_info,
)


class TestAuthorProcessor:
    """Test author processing functionality."""

    def test_single_author_no_affiliation(self):
        """Test formatting single author without affiliation."""
        yaml_metadata = {"authors": [{"name": "John Doe"}]}
        result = generate_authors_and_affiliations(yaml_metadata)
        assert "John Doe" in result

    def test_single_author_with_affiliation(self):
        """Test formatting single author with affiliation."""
        yaml_metadata = {
            "authors": [{"name": "John Doe", "affiliations": ["University A"]}],
            "affiliations": [{"shortname": "University A", "full_name": "University A"}],
        }
        result = generate_authors_and_affiliations(yaml_metadata)
        assert "John Doe" in result
        assert "University A" in result

    def test_multiple_authors_same_affiliation(self):
        """Test formatting multiple authors with same affiliation."""
        yaml_metadata = {
            "authors": [
                {"name": "John Doe", "affiliations": ["University A"]},
                {"name": "Jane Smith", "affiliations": ["University A"]},
            ],
            "affiliations": [{"shortname": "University A", "full_name": "University A"}],
        }
        result = generate_authors_and_affiliations(yaml_metadata)
        assert "John Doe" in result
        assert "Jane Smith" in result
        assert "University A" in result

    def test_multiple_authors_different_affiliations(self):
        """Test formatting multiple authors with different affiliations."""
        yaml_metadata = {
            "authors": [
                {"name": "John Doe", "affiliations": ["University A"]},
                {"name": "Jane Smith", "affiliations": ["University B"]},
            ],
            "affiliations": [
                {"shortname": "University A", "full_name": "University A"},
                {"shortname": "University B", "full_name": "University B"},
            ],
        }
        result = generate_authors_and_affiliations(yaml_metadata)
        assert "John Doe" in result
        assert "Jane Smith" in result
        assert "University A" in result
        assert "University B" in result

    def test_corresponding_authors(self):
        """Test corresponding author generation."""
        yaml_metadata = {
            "authors": [
                {
                    "name": "John Doe",
                    "corresponding_author": True,
                    "email": "john@test.com",
                }
            ]
        }
        result = generate_corresponding_authors(yaml_metadata)
        assert "john" in result.lower()
        # Check for LaTeX formatted email (@ is escaped as \at in LaTeX)
        assert "john@test.com" in result or "john\\at test.com" in result

    def test_extended_author_info(self):
        """Test extended author information generation."""
        yaml_metadata = {"authors": [{"name": "John Doe", "orcid": "0000-0000-0000-0000", "x": "@johndoe"}]}
        result = generate_extended_author_info(yaml_metadata)
        assert "0000-0000-0000-0000" in result

    def test_empty_authors_fallback(self):
        """Test fallback when no authors are provided."""
        yaml_metadata = {}
        result = generate_authors_and_affiliations(yaml_metadata)
        assert "Author Name" in result
        assert "Institution" in result

    def test_author_with_special_characters(self):
        """Test handling of special characters in author names."""
        yaml_metadata = {"authors": [{"name": "João Dõe & Smith"}]}
        result = generate_authors_and_affiliations(yaml_metadata)
        # Should handle special characters appropriately for LaTeX
        assert result is not None
