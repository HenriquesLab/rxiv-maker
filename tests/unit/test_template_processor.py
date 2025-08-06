"""Unit tests for the template_processor module."""

from pathlib import Path

from rxiv_maker.processors.template_processor import (
    generate_bibliography,
    generate_keywords,
    get_template_path,
    process_template_replacements,
)


class TestTemplateProcessor:
    """Test template processing functionality."""

    def test_get_template_path(self):
        """Test getting the template path."""
        template_path = get_template_path()
        assert isinstance(template_path, str | Path)
        assert "template.tex" in str(template_path)

    def test_generate_keywords(self):
        """Test keyword generation from metadata."""
        yaml_metadata = {"keywords": ["keyword1", "keyword2", "keyword3"]}
        result = generate_keywords(yaml_metadata)
        assert "keyword1" in result
        assert "keyword2" in result
        assert "keyword3" in result

    def test_generate_keywords_empty(self):
        """Test keyword generation with no keywords."""
        yaml_metadata = {}
        result = generate_keywords(yaml_metadata)
        assert isinstance(result, str)

    def test_generate_bibliography(self):
        """Test bibliography generation from metadata."""
        yaml_metadata = {"bibliography": "02_REFERENCES.bib"}
        result = generate_bibliography(yaml_metadata)
        assert "02_REFERENCES" in result

    def test_process_template_replacements_basic(self):
        """Test basic template processing."""
        template_content = "Title: <PY-RPL:LONG-TITLE-STR>"
        yaml_metadata = {"title": {"long": "Test Article Title"}}
        article_md = "# Test Content"

        result = process_template_replacements(template_content, yaml_metadata, article_md)
        assert "Test Article Title" in result

    def test_process_template_replacements_with_authors(self):
        """Test template processing with authors."""
        template_content = "<PY-RPL:AUTHORS-AND-AFFILIATIONS>"
        yaml_metadata = {
            "authors": [{"name": "John Doe", "affiliations": ["University A"]}],
            "affiliations": [{"shortname": "University A", "full_name": "University A"}],
        }
        article_md = "# Test Content"

        result = process_template_replacements(template_content, yaml_metadata, article_md)
        assert "John Doe" in result

    def test_process_template_replacements_with_keywords(self):
        """Test template processing with keywords."""
        template_content = "<PY-RPL:KEYWORDS>"
        yaml_metadata = {"keywords": ["test", "article", "template"]}
        article_md = "# Test Content"

        result = process_template_replacements(template_content, yaml_metadata, article_md)
        assert "test" in result

    def test_process_template_replacements_comprehensive(self):
        """Test comprehensive template processing."""
        template_content = """
        Title: <PY-RPL:LONG-TITLE-STR>
        Authors: <PY-RPL:AUTHORS-AND-AFFILIATIONS>
        Keywords: <PY-RPL:KEYWORDS>
        Content: <PY-RPL:MAIN-CONTENT>
        """
        yaml_metadata = {
            "title": {"long": "Comprehensive Test"},
            "authors": [{"name": "Jane Doe"}],
            "keywords": ["comprehensive", "test"],
        }
        article_md = "# Main content here"

        result = process_template_replacements(template_content, yaml_metadata, article_md)
        assert "Comprehensive Test" in result
        assert "Jane Doe" in result
        assert "comprehensive" in result
