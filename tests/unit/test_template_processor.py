"""Unit tests for the template_processor module."""

from pathlib import Path

from rxiv_maker.processors.template_processor import (
    generate_bibliography,
    generate_keywords,
    get_template_path,
    process_template_replacements,
)

try:
    from rxiv_maker import __version__
except ImportError:
    __version__ = "unknown"


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

    def test_acknowledgment_with_version_injection(self):
        """Test that acknowledgment includes version when acknowledge_rxiv_maker is true."""
        template_content = "<PY-RPL:MANUSCRIPT-PREPARATION-BLOCK>"
        yaml_metadata = {"acknowledge_rxiv_maker": True}
        article_md = "# Test Content"

        result = process_template_replacements(template_content, yaml_metadata, article_md)

        # Should contain acknowledgment text
        assert "This manuscript was prepared using" in result
        assert "R}$\\chi$iv-Maker" in result
        # Should include version information
        assert f"v{__version__}" in result or "vunknown" in result
        # Should contain citation
        assert "saraiva_2025_rxivmaker" in result

    def test_acknowledgment_disabled(self):
        """Test that acknowledgment is not included when acknowledge_rxiv_maker is false."""
        template_content = "<PY-RPL:MANUSCRIPT-PREPARATION-BLOCK>"
        yaml_metadata = {"acknowledge_rxiv_maker": False}
        article_md = "# Test Content"

        result = process_template_replacements(template_content, yaml_metadata, article_md)

        # Should not contain acknowledgment text
        assert "This manuscript was prepared using" not in result

    def test_acknowledgment_with_existing_manuscript_prep(self):
        """Test that acknowledgment doesn't override existing manuscript preparation content."""
        template_content = "Block: <PY-RPL:MANUSCRIPT-PREPARATION-BLOCK>"
        yaml_metadata = {"acknowledge_rxiv_maker": True}
        article_md = """# Test Content

## Manuscript Preparation

Custom manuscript preparation content here.
"""

        result = process_template_replacements(template_content, yaml_metadata, article_md)

        # Should contain the custom content, not the default acknowledgment
        assert "Custom manuscript preparation content here" in result
        assert "This manuscript was prepared using" not in result

    def test_methods_placement_after_results(self):
        """Test that Methods appears after Results when methods_placement is after_results."""
        template_content = """<PY-RPL:MAIN-SECTION>
<PY-RPL:RESULTS-SECTION>
<PY-RPL:METHODS-AFTER-RESULTS>
<PY-RPL:METHODS-AFTER-BIBLIOGRAPHY>"""
        yaml_metadata = {"methods_placement": "after_results"}
        article_md = """## Introduction

This is the introduction.

## Methods

This is the methods section.
"""

        result = process_template_replacements(template_content, yaml_metadata, article_md)

        # Methods should appear in the METHODS-AFTER-RESULTS placeholder
        assert "\\section*{Methods}" in result
        assert "This is the methods section" in result
        # Verify Methods is not in MAIN-SECTION (Introduction should be there, but not Methods)

    def test_methods_placement_after_bibliography(self):
        """Test that Methods appears after Bibliography when methods_placement is after_bibliography."""
        template_content = """<PY-RPL:MAIN-SECTION>
<PY-RPL:METHODS-AFTER-RESULTS>
<PY-RPL:METHODS-AFTER-BIBLIOGRAPHY>"""
        yaml_metadata = {"methods_placement": "after_bibliography"}
        article_md = """## Introduction

This is the introduction.

## Methods

This is the methods section.
"""

        result = process_template_replacements(template_content, yaml_metadata, article_md)

        # Methods should appear in the METHODS-AFTER-BIBLIOGRAPHY placeholder
        assert "\\section*{Methods}" in result
        assert "This is the methods section" in result

    def test_methods_placement_default(self):
        """Test that default behavior is after_bibliography when methods_placement is omitted."""
        template_content = """<PY-RPL:MAIN-SECTION>
<PY-RPL:METHODS-AFTER-RESULTS>
<PY-RPL:METHODS-AFTER-BIBLIOGRAPHY>"""
        yaml_metadata = {}  # No methods_placement setting
        article_md = """## Introduction

This is the introduction.

## Methods

This is the methods section.
"""

        result = process_template_replacements(template_content, yaml_metadata, article_md)

        # Default should be after_bibliography (Methods in METHODS-AFTER-BIBLIOGRAPHY placeholder)
        assert "\\section*{Methods}" in result
        assert "This is the methods section" in result

        # Verify Methods is not in MAIN-SECTION (only Introduction should be there)
        assert "\\section*{Introduction}" in result

    def test_methods_placement_after_intro(self):
        """Test that Methods appears after Introduction when methods_placement is after_intro."""
        template_content = """<PY-RPL:MAIN-SECTION>
<PY-RPL:RESULTS-SECTION>
<PY-RPL:METHODS-AFTER-RESULTS>
<PY-RPL:METHODS-AFTER-BIBLIOGRAPHY>"""
        yaml_metadata = {"methods_placement": "after_intro"}
        article_md = """## Introduction

This is the introduction.

## Results

This is the results section.

## Methods

This is the methods section.
"""

        result = process_template_replacements(template_content, yaml_metadata, article_md)

        # Methods should appear in MAIN-SECTION right after Introduction
        assert "\\section*{Methods}" in result
        assert "This is the methods section" in result
        assert "\\section*{Introduction}" in result

        # Verify order: Introduction should come before Methods in MAIN-SECTION
        intro_match = result.find("\\section*{Introduction}")
        methods_match = result.find("\\section*{Methods}")
        assert intro_match < methods_match, "Introduction should appear before Methods in after_intro mode"

        # Results should be in its own placeholder, not in MAIN-SECTION
        assert "\\section*{Results}" in result

    def test_methods_placement_after_discussion(self):
        """Test that Methods appears after Discussion when methods_placement is after_discussion."""
        template_content = """<PY-RPL:MAIN-SECTION>
<PY-RPL:DISCUSSION-SECTION>
<PY-RPL:CONCLUSIONS-SECTION>
<PY-RPL:METHODS-AFTER-DISCUSSION>
<PY-RPL:METHODS-AFTER-BIBLIOGRAPHY>"""
        yaml_metadata = {"methods_placement": "after_discussion"}
        article_md = """## Introduction

This is the introduction.

## Discussion

This is the discussion section.

## Methods

This is the methods section.
"""

        result = process_template_replacements(template_content, yaml_metadata, article_md)

        # Methods should appear in the METHODS-AFTER-DISCUSSION placeholder
        assert "\\section*{Methods}" in result
        assert "This is the methods section" in result

        # Verify Discussion appears before Methods section
        discussion_match = result.find("\\section*{Discussion}")
        methods_match = result.find("\\section*{Methods}")
        assert discussion_match < methods_match, "Discussion should appear before Methods in after_discussion mode"

        # Verify Methods is not in MAIN-SECTION
        assert "\\section*{Introduction}" in result
