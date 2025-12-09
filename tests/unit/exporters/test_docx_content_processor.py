"""Tests for DOCX content processor."""

from rxiv_maker.exporters.docx_content_processor import DocxContentProcessor


class TestDocxContentProcessor:
    """Test content processing for DOCX export."""

    def test_parse_simple_heading(self):
        """Test parsing a simple heading."""
        processor = DocxContentProcessor()
        # First H1 is skipped (treated as title from metadata)
        # So we need a title H1 followed by the actual heading we're testing
        markdown = "# Title\n\n# Introduction"
        result = processor.parse(markdown, {})

        assert len(result["sections"]) == 1
        section = result["sections"][0]
        assert section["type"] == "heading"
        assert section["level"] == 1
        assert section["text"] == "Introduction"

    def test_parse_multiple_heading_levels(self):
        """Test parsing different heading levels."""
        processor = DocxContentProcessor()
        # First H1 is skipped (title), so add it before the actual content
        markdown = "# Title\n\n# Level 1\n\n## Level 2\n\n### Level 3"
        result = processor.parse(markdown, {})

        assert len(result["sections"]) == 3
        assert result["sections"][0]["level"] == 1
        assert result["sections"][1]["level"] == 2
        assert result["sections"][2]["level"] == 3

    def test_parse_simple_paragraph(self):
        """Test parsing a simple paragraph."""
        processor = DocxContentProcessor()
        markdown = "This is a simple paragraph."
        result = processor.parse(markdown, {})

        assert len(result["sections"]) == 1
        section = result["sections"][0]
        assert section["type"] == "paragraph"
        assert len(section["runs"]) == 1
        assert section["runs"][0]["text"] == "This is a simple paragraph."

    def test_parse_paragraph_with_bold(self):
        """Test parsing paragraph with bold text."""
        processor = DocxContentProcessor()
        markdown = "Text with **bold** word."
        result = processor.parse(markdown, {})

        section = result["sections"][0]
        runs = section["runs"]

        # Should have 3 runs: before, bold, after
        assert any(run.get("bold") for run in runs if run["type"] == "text")

    def test_parse_paragraph_with_italic(self):
        """Test parsing paragraph with italic text."""
        processor = DocxContentProcessor()
        markdown = "Text with *italic* word."
        result = processor.parse(markdown, {})

        section = result["sections"][0]
        runs = section["runs"]

        # Should have italic run
        assert any(run.get("italic") for run in runs if run["type"] == "text")

    def test_parse_paragraph_with_code(self):
        """Test parsing paragraph with inline code."""
        processor = DocxContentProcessor()
        markdown = "Text with `code` inline."
        result = processor.parse(markdown, {})

        section = result["sections"][0]
        runs = section["runs"]

        # Should have code run
        assert any(run.get("code") for run in runs if run["type"] == "text")

    def test_parse_paragraph_with_citations(self):
        """Test parsing paragraph with citations."""
        processor = DocxContentProcessor()
        markdown = "Study shows [1] results."
        result = processor.parse(markdown, {})

        section = result["sections"][0]
        runs = section["runs"]

        # Should have citation run
        citation_runs = [r for r in runs if r["type"] == "citation"]
        assert len(citation_runs) == 1
        assert citation_runs[0]["number"] == 1

    def test_parse_bullet_list(self):
        """Test parsing bullet list."""
        processor = DocxContentProcessor()
        markdown = "- Item 1\n- Item 2\n- Item 3"
        result = processor.parse(markdown, {})

        assert len(result["sections"]) == 1
        section = result["sections"][0]
        assert section["type"] == "list"
        assert section["list_type"] == "bullet"
        assert len(section["items"]) == 3
        # Items are lists of runs, not plain strings
        assert len(section["items"][0]) == 1
        assert section["items"][0][0]["text"] == "Item 1"

    def test_parse_numbered_list(self):
        """Test parsing numbered list."""
        processor = DocxContentProcessor()
        markdown = "1. First\n2. Second\n3. Third"
        result = processor.parse(markdown, {})

        section = result["sections"][0]
        assert section["type"] == "list"
        assert section["list_type"] == "number"
        assert len(section["items"]) == 3

    def test_parse_code_block(self):
        """Test parsing fenced code block."""
        processor = DocxContentProcessor()
        markdown = "```python\nprint('hello')\n```"
        result = processor.parse(markdown, {})

        section = result["sections"][0]
        assert section["type"] == "code_block"
        assert "print('hello')" in section["content"]

    def test_parse_mixed_content(self):
        """Test parsing mixed content types."""
        processor = DocxContentProcessor()
        markdown = """# Introduction

This is a paragraph with **bold** text.

## Methods

We used the following:

- Method 1
- Method 2

Results show [1, 2] support."""

        result = processor.parse(markdown, {})

        sections = result["sections"]
        types = [s["type"] for s in sections]

        assert "heading" in types
        assert "paragraph" in types
        assert "list" in types

    def test_parse_multiline_paragraph(self):
        """Test parsing paragraph spanning multiple lines."""
        processor = DocxContentProcessor()
        markdown = "Line 1\nLine 2\nLine 3"
        result = processor.parse(markdown, {})

        section = result["sections"][0]
        # Should join into single paragraph
        assert section["type"] == "paragraph"
        assert "Line 1 Line 2 Line 3" in section["runs"][0]["text"]

    def test_parse_empty_lines_ignored(self):
        """Test that empty lines are ignored."""
        processor = DocxContentProcessor()
        # Add title H1 first, then the actual content
        markdown = "# Title\n\n# Heading\n\n\n\nParagraph"
        result = processor.parse(markdown, {})

        # Should only have heading and paragraph, not empty sections
        assert len(result["sections"]) == 2

    def test_parse_heading_with_id(self):
        """Test parsing heading with ID attribute."""
        processor = DocxContentProcessor()
        # Add title H1 first
        markdown = "# Title\n\n# Introduction {#intro}"
        result = processor.parse(markdown, {})

        section = result["sections"][0]
        # ID should be stripped
        assert section["text"] == "Introduction"
        assert "{#intro}" not in section["text"]

    def test_parse_multiple_citations(self):
        """Test parsing multiple citations in brackets."""
        processor = DocxContentProcessor()
        markdown = "Studies [1, 2, 3] show results."
        result = processor.parse(markdown, {})

        section = result["sections"][0]
        citation_runs = [r for r in section["runs"] if r["type"] == "citation"]
        assert len(citation_runs) == 3
        assert citation_runs[0]["number"] == 1
        assert citation_runs[1]["number"] == 2
        assert citation_runs[2]["number"] == 3

    def test_parse_preserves_text_order(self):
        """Test that text order is preserved with formatting."""
        processor = DocxContentProcessor()
        markdown = "Before **bold** after *italic* end."
        result = processor.parse(markdown, {})

        section = result["sections"][0]
        runs = section["runs"]

        # Reconstruct text to verify order
        texts = [r["text"] for r in runs if r["type"] == "text"]
        assert "Before " in texts[0]
        assert "bold" in texts[1]
        assert " after " in texts[2]

    def test_inline_formatting_complex(self):
        """Test complex inline formatting."""
        processor = DocxContentProcessor()
        text = "Normal **bold** normal *italic* normal `code` end"
        citation_map = {}

        runs = processor._parse_inline_formatting(text, citation_map)

        # Should have alternating formatted and normal text
        assert len(runs) > 3
        bold_runs = [r for r in runs if r.get("bold")]
        italic_runs = [r for r in runs if r.get("italic")]
        code_runs = [r for r in runs if r.get("code")]

        assert len(bold_runs) == 1
        assert len(italic_runs) == 1
        assert len(code_runs) == 1
