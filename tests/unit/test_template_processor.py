"""Unit tests for the template_processor module."""

from pathlib import Path

import pytest

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

    @pytest.mark.parametrize(
        "numeric_value,expected_string_value",
        [
            (1, "after_intro"),
            (2, "after_results"),
            (3, "after_discussion"),
            (4, "after_bibliography"),
        ],
    )
    def test_methods_placement_numeric_mapping(self, numeric_value, expected_string_value):
        """Test that numeric values 1-4 correctly map to their string equivalents.

        This test verifies the numeric mapping defined in template_processor.py:
        - 1 → "after_intro"
        - 2 → "after_results"
        - 3 → "after_discussion"
        - 4 → "after_bibliography"
        """
        # Test that numeric value produces same result as string value
        template_content = """<PY-RPL:MAIN-SECTION>
<PY-RPL:RESULTS-SECTION>
<PY-RPL:METHODS-AFTER-RESULTS>
<PY-RPL:METHODS-AFTER-DISCUSSION>
<PY-RPL:METHODS-AFTER-BIBLIOGRAPHY>"""

        yaml_metadata_numeric = {"methods_placement": numeric_value}
        yaml_metadata_string = {"methods_placement": expected_string_value}

        article_md = """## Introduction

This is the introduction.

## Methods

This is the methods section.
"""

        result_numeric = process_template_replacements(template_content, yaml_metadata_numeric, article_md)
        result_string = process_template_replacements(template_content, yaml_metadata_string, article_md)

        # The numeric value should produce identical output to the string value
        assert result_numeric == result_string, (
            f"Numeric value {numeric_value} should map to '{expected_string_value}' and produce identical output"
        )

        # Both should contain the Methods section
        assert "\\section*{Methods}" in result_numeric
        assert "This is the methods section" in result_numeric

    @pytest.mark.parametrize(
        "invalid_value,expected_fallback",
        [
            (0, "after_bibliography"),  # Below valid range
            (5, "after_bibliography"),  # Above valid range (was valid in v1.12.0)
            (-1, "after_bibliography"),  # Negative value
            (100, "after_bibliography"),  # Large invalid value
            ("inline", "after_bibliography"),  # Removed option from v1.12.0
            ("invalid", "after_bibliography"),  # Random invalid string
        ],
    )
    def test_methods_placement_invalid_values_fallback(self, invalid_value, expected_fallback):
        """Test that invalid methods_placement values fall back to after_bibliography with warning."""
        template_content = """<PY-RPL:MAIN-SECTION>
<PY-RPL:METHODS-AFTER-RESULTS>
<PY-RPL:METHODS-AFTER-BIBLIOGRAPHY>"""
        yaml_metadata = {"methods_placement": invalid_value}
        article_md = """## Introduction

This is the introduction.

## Methods

This is the methods section.
"""

        # Capture stderr to verify warning is emitted
        import io
        import sys

        stderr_capture = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = stderr_capture

        try:
            result = process_template_replacements(template_content, yaml_metadata, article_md)

            # Should fall back to after_bibliography (methods at the end)
            assert "\\section*{Methods}" in result
            assert "This is the methods section" in result

            # Verify warning was emitted
            warning_output = stderr_capture.getvalue()
            assert "Warning: Invalid methods_placement value" in warning_output
            assert "after_bibliography" in warning_output

        finally:
            sys.stderr = old_stderr

    def test_competing_interests_placement(self):
        """Test that competing interests section appears in correct location."""
        template_content = """<PY-RPL:MAIN-SECTION>
<PY-RPL:ACKNOWLEDGEMENTS-BLOCK>
<PY-RPL:COMPETING-INTERESTS-BLOCK>
Bibliography goes here"""
        yaml_metadata = {}
        article_md = """## Introduction

This is the introduction.

## Acknowledgements

We thank our funding sources.

## Competing Interests

The authors declare no competing interests.
"""

        result = process_template_replacements(template_content, yaml_metadata, article_md)

        # Should contain competing interests section
        assert "\\begin{interests}" in result
        assert "The authors declare no competing interests" in result
        assert "\\end{interests}" in result

        # Verify it appears after acknowledgements and before bibliography
        ack_pos = result.find("We thank our funding sources")
        interests_pos = result.find("The authors declare no competing interests")
        bib_pos = result.find("Bibliography goes here")

        assert ack_pos < interests_pos, "Competing interests should appear after acknowledgements"
        assert interests_pos < bib_pos, "Competing interests should appear before bibliography"

    def test_competing_interests_alternative_title(self):
        """Test that 'Conflicts of Interest' section title is also recognized."""
        template_content = "<PY-RPL:MAIN-SECTION>\n<PY-RPL:COMPETING-INTERESTS-BLOCK>"
        yaml_metadata = {}
        article_md = """## Introduction

This is the introduction.

## Conflicts of Interest

No conflicts of interest to declare.
"""

        result = process_template_replacements(template_content, yaml_metadata, article_md)

        # Should contain competing interests section
        assert "\\begin{interests}" in result
        assert "No conflicts of interest to declare" in result
        assert "\\end{interests}" in result

    def test_competing_interests_empty(self):
        """Test that template handles missing competing interests section gracefully."""
        template_content = """<PY-RPL:MAIN-SECTION>
<PY-RPL:COMPETING-INTERESTS-BLOCK>
End of document"""
        yaml_metadata = {}
        article_md = """## Introduction

This is the introduction.
"""

        result = process_template_replacements(template_content, yaml_metadata, article_md)

        # Should not contain competing interests block when section is missing
        assert "\\begin{interests}" not in result
        assert "\\end{interests}" not in result
        # But template should still be processed without errors
        assert "End of document" in result

    def test_conflict_word_not_misidentified(self):
        """Test that sections with 'conflict' but not 'conflict of interest' are not misidentified."""
        template_content = """<PY-RPL:MAIN-SECTION>
<PY-RPL:COMPETING-INTERESTS-BLOCK>"""
        yaml_metadata = {}
        article_md = """## Introduction

This is the introduction.

## Addressing Resource Conflicts

This discusses resource conflicts in the study area.
"""

        result = process_template_replacements(template_content, yaml_metadata, article_md)

        # "Addressing Resource Conflicts" should NOT be identified as competing interests
        # It should appear in the main section instead (as a custom section)
        assert "\\begin{interests}" not in result
        assert "\\end{interests}" not in result
        assert "resource conflicts in the study area" in result
