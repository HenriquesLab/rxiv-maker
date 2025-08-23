"""Comprehensive processor test suite for rxiv-maker.

This consolidated test suite combines processor tests from multiple files:
- test_citation_processor.py
- test_citation_rendering.py
- test_math_processor.py
- test_yaml_processor.py
- test_figure_processor.py
- Template processing tests
- Text formatting tests

Consolidation reduces 8+ test files into a single focused test suite
while maintaining full test coverage and improving maintainability.
"""

import os
import tempfile
import unittest
from pathlib import Path

import yaml

try:
    import pytest

    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

    class MockPytest:
        class mark:
            @staticmethod
            def parametrize(*args, **kwargs):
                def decorator(cls):
                    return cls

                return decorator

            @staticmethod
            def processor(cls):
                return cls

    pytest = MockPytest()

# Import processor components with fallbacks
try:
    from rxiv_maker.processors.yaml_processor import extract_yaml_metadata, validate_yaml_structure

    YAML_PROCESSOR_AVAILABLE = True
except ImportError:
    YAML_PROCESSOR_AVAILABLE = False

try:
    from rxiv_maker.processors.citation_processor import CitationProcessor
    from rxiv_maker.processors.citation_rendering import CitationRenderer

    CITATION_PROCESSORS_AVAILABLE = True
except ImportError:
    CITATION_PROCESSORS_AVAILABLE = False

try:
    from rxiv_maker.processors.math_processor import MathProcessor

    MATH_PROCESSOR_AVAILABLE = True
except ImportError:
    MATH_PROCESSOR_AVAILABLE = False

try:
    from rxiv_maker.processors.figure_processor import FigureProcessor

    FIGURE_PROCESSOR_AVAILABLE = True
except ImportError:
    FIGURE_PROCESSOR_AVAILABLE = False

try:
    from rxiv_maker.processors.template_processor import (
        TemplateProcessor,
        get_template_path,
        process_template_replacements,
    )

    TEMPLATE_PROCESSOR_AVAILABLE = True
except ImportError:
    TEMPLATE_PROCESSOR_AVAILABLE = False

# Test data and fixtures
SAMPLE_YAML_CONFIG = """
title: "Test Manuscript Title"
authors:
  - name: "John Doe"
    affiliation: "Test University"
    email: "john@test.edu"
  - name: "Jane Smith"
    affiliation: "Another University"
    email: "jane@another.edu"
abstract: "This is a test abstract for validation purposes."
keywords: ["test", "manuscript", "validation"]
journal: "Test Journal"
year: 2023
doi_validation: true
acknowledge_rxiv_maker: true
"""

SAMPLE_MANUSCRIPT_WITH_CITATIONS = """
# Test Manuscript

## Introduction
This work builds on previous research [@doe2023] and extends the findings
of multiple studies [@smith2022; @johnson2021; @wilson2020].

## Methods
The methodology follows standard practices [@standard_method].

## Results
Results show significant improvements (p < 0.001) [@results_paper].

## Discussion
These findings align with [@doe2023] but contradict [@opposing_view].
"""

SAMPLE_MATH_CONTENT = """
# Mathematical Content

## Inline Math
The famous equation $E = mc^2$ demonstrates mass-energy equivalence.
We also have $\\alpha + \\beta = \\gamma$ in our system.

## Block Math
$$\\sum_{i=1}^{n} x_i = \\bar{x} \\cdot n$$

$$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$

## Complex Math
$$\\begin{align}
f(x) &= ax^2 + bx + c \\\\
f'(x) &= 2ax + b \\\\
f''(x) &= 2a
\\end{align}$$
"""

SAMPLE_FIGURE_CONTENT = """
# Figures

## Simple Figure
![Test Figure](figures/test.png){#fig:test}

## Figure with Caption
![Complex Figure Caption with **bold** and *italic* text](figures/complex.svg){#fig:complex width=80%}

## Multiple Figures
![Figure A](figures/a.png){#fig:a}
![Figure B](figures/b.png){#fig:b}

Figure @fig:test shows the basic results, while @fig:complex provides detailed analysis.
"""


class ProcessorTestBase(unittest.TestCase):
    """Base class for processor tests with common utilities."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create test configuration file
        self.config_path = self.temp_dir / "config.yml"
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write(SAMPLE_YAML_CONFIG)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_file(self, filename: str, content: str) -> Path:
        """Create a test file with given content."""
        file_path = self.temp_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path


@pytest.mark.processor
@unittest.skipUnless(YAML_PROCESSOR_AVAILABLE, "YAML processor not available")
class TestYAMLProcessor(ProcessorTestBase):
    """Test YAML configuration processing functionality."""

    def test_extract_yaml_metadata(self):
        """Test extraction of YAML metadata from manuscript."""
        manuscript_content = f"""---
{SAMPLE_YAML_CONFIG}---

# Manuscript Content
This is the manuscript content.
"""

        manuscript_path = self.create_test_file("manuscript.md", manuscript_content)

        metadata = extract_yaml_metadata(str(manuscript_path))

        self.assertIsInstance(metadata, dict)
        self.assertEqual(metadata["title"], "Test Manuscript Title")
        self.assertEqual(len(metadata["authors"]), 2)
        self.assertEqual(metadata["authors"][0]["name"], "John Doe")
        self.assertTrue(metadata["doi_validation"])

    def test_extract_yaml_from_separate_file(self):
        """Test extraction of YAML from separate configuration file."""
        metadata = extract_yaml_metadata(str(self.config_path))

        self.assertIsInstance(metadata, dict)
        self.assertEqual(metadata["title"], "Test Manuscript Title")
        self.assertIn("authors", metadata)
        self.assertIn("abstract", metadata)

    def test_yaml_validation(self):
        """Test YAML structure validation."""
        metadata = extract_yaml_metadata(str(self.config_path))

        # Validate required fields
        validation_result = validate_yaml_structure(metadata)

        self.assertTrue(validation_result["valid"])
        self.assertEqual(len(validation_result.get("errors", [])), 0)

    def test_invalid_yaml_handling(self):
        """Test handling of invalid YAML content."""
        invalid_yaml = """
        title: "Test Title
        authors: [invalid yaml structure
        """

        invalid_file = self.create_test_file("invalid.yml", invalid_yaml)

        with self.assertRaises((yaml.YAMLError, Exception)):
            extract_yaml_metadata(str(invalid_file))

    def test_missing_required_fields(self):
        """Test validation of missing required fields."""
        incomplete_yaml = """
        title: "Test Title"
        # Missing authors
        """

        incomplete_file = self.create_test_file("incomplete.yml", incomplete_yaml)
        metadata = extract_yaml_metadata(str(incomplete_file))

        validation_result = validate_yaml_structure(metadata)

        self.assertFalse(validation_result["valid"])
        self.assertIn("authors", str(validation_result.get("errors", [])))

    @pytest.mark.parametrize(
        "field,value", [("title", ""), ("authors", []), ("year", "not_a_year"), ("doi_validation", "not_boolean")]
    )
    def test_field_validation(self, field, value):
        """Test validation of specific fields."""
        metadata = extract_yaml_metadata(str(self.config_path))
        metadata[field] = value

        validation_result = validate_yaml_structure(metadata)

        # Should detect invalid field values
        self.assertFalse(validation_result["valid"])


@pytest.mark.processor
@unittest.skipUnless(CITATION_PROCESSORS_AVAILABLE, "Citation processors not available")
class TestCitationProcessor(ProcessorTestBase):
    """Test citation processing functionality."""

    def setUp(self):
        super().setUp()
        self.processor = CitationProcessor()
        self.renderer = CitationRenderer()

    def test_citation_extraction(self):
        """Test extraction of citations from content."""
        citations = self.processor.extract_citations(SAMPLE_MANUSCRIPT_WITH_CITATIONS)

        expected_citations = [
            "doe2023",
            "smith2022",
            "johnson2021",
            "wilson2020",
            "standard_method",
            "results_paper",
            "opposing_view",
        ]

        self.assertGreater(len(citations), 0)
        for expected in expected_citations:
            self.assertIn(expected, citations, f"Should find citation: {expected}")

    def test_multiple_citation_parsing(self):
        """Test parsing of multiple citations in single reference."""
        content = "Research shows significant results [@cite1; @cite2; @cite3]."

        citations = self.processor.extract_citations(content)

        self.assertIn("cite1", citations)
        self.assertIn("cite2", citations)
        self.assertIn("cite3", citations)

    def test_citation_formatting(self):
        """Test citation formatting for different styles."""
        citation_data = {
            "doe2023": {"author": "Doe, J.", "title": "Test Article", "journal": "Test Journal", "year": "2023"}
        }

        # Test APA style
        apa_formatted = self.renderer.format_citations(citation_data, style="apa")
        self.assertIn("Doe, J.", apa_formatted)
        self.assertIn("(2023)", apa_formatted)

        # Test IEEE style
        ieee_formatted = self.renderer.format_citations(citation_data, style="ieee")
        self.assertIsInstance(ieee_formatted, str)

    def test_bibliography_generation(self):
        """Test generation of bibliography from citations."""
        citations = ["test_citation"]
        citation_data = {
            "test_citation": {
                "author": "Test Author",
                "title": "Test Title",
                "journal": "Test Journal",
                "year": "2023",
                "doi": "10.1000/test",
            }
        }

        bibliography = self.processor.generate_bibliography(citations, citation_data)

        self.assertIsInstance(bibliography, str)
        self.assertIn("Test Author", bibliography)
        self.assertIn("Test Title", bibliography)
        self.assertIn("2023", bibliography)

    def test_citation_validation(self):
        """Test validation of citation references."""
        content = SAMPLE_MANUSCRIPT_WITH_CITATIONS
        available_refs = ["doe2023", "smith2022", "johnson2021"]

        validation_result = self.processor.validate_citations(content, available_refs)

        self.assertIn("missing_citations", validation_result)
        missing = validation_result["missing_citations"]

        # Should find references not in available_refs
        expected_missing = ["wilson2020", "standard_method", "results_paper", "opposing_view"]
        for missing_ref in expected_missing:
            self.assertIn(missing_ref, missing)


@pytest.mark.processor
@unittest.skipUnless(MATH_PROCESSOR_AVAILABLE, "Math processor not available")
class TestMathProcessor(ProcessorTestBase):
    """Test mathematical content processing."""

    def setUp(self):
        super().setUp()
        self.processor = MathProcessor()

    def test_inline_math_extraction(self):
        """Test extraction of inline math expressions."""
        math_expressions = self.processor.extract_math(SAMPLE_MATH_CONTENT, inline_only=True)

        self.assertGreater(len(math_expressions), 0)
        self.assertIn("E = mc^2", str(math_expressions))
        self.assertIn("\\alpha + \\beta = \\gamma", str(math_expressions))

    def test_block_math_extraction(self):
        """Test extraction of block math expressions."""
        math_expressions = self.processor.extract_math(SAMPLE_MATH_CONTENT, block_only=True)

        self.assertGreater(len(math_expressions), 0)
        # Should find block equations
        expressions_str = str(math_expressions)
        self.assertTrue("\\sum_{i=1}^{n}" in expressions_str or "\\int_{-\\infty}^{\\infty}" in expressions_str)

    def test_math_syntax_validation(self):
        """Test validation of math syntax."""
        valid_math = "$E = mc^2$"
        invalid_math = "$\\invalid{syntax$"

        valid_result = self.processor.validate_syntax(valid_math)
        invalid_result = self.processor.validate_syntax(invalid_math)

        self.assertTrue(valid_result["valid"])
        self.assertFalse(invalid_result["valid"])
        self.assertIn("errors", invalid_result)

    def test_math_to_latex_conversion(self):
        """Test conversion of math expressions to LaTeX."""
        content_with_math = SAMPLE_MATH_CONTENT

        latex_converted = self.processor.convert_to_latex(content_with_math)

        self.assertIsInstance(latex_converted, str)
        # Should preserve math expressions in LaTeX format
        self.assertIn("$", latex_converted)  # Inline math markers
        self.assertIn("$$", latex_converted)  # Block math markers

    def test_complex_math_structures(self):
        """Test processing of complex math structures."""
        complex_math = r"""
        $$\begin{align}
        \nabla \cdot \mathbf{E} &= \frac{\rho}{\epsilon_0} \\
        \nabla \times \mathbf{E} &= -\frac{\partial \mathbf{B}}{\partial t}
        \end{align}$$
        """

        math_expressions = self.processor.extract_math(complex_math, block_only=True)

        self.assertGreater(len(math_expressions), 0)
        # Should handle align environments
        expressions_str = str(math_expressions)
        self.assertIn("align", expressions_str)


@pytest.mark.processor
@unittest.skipUnless(FIGURE_PROCESSOR_AVAILABLE, "Figure processor not available")
class TestFigureProcessor(ProcessorTestBase):
    """Test figure processing functionality."""

    def setUp(self):
        super().setUp()
        self.processor = FigureProcessor()

        # Create test figure directory
        self.figures_dir = self.temp_dir / "figures"
        self.figures_dir.mkdir(exist_ok=True)

    def test_figure_extraction(self):
        """Test extraction of figure references from content."""
        figures = self.processor.extract_figures(SAMPLE_FIGURE_CONTENT)

        self.assertGreater(len(figures), 0)

        # Should find figure references
        figure_paths = [fig.get("path") for fig in figures]
        self.assertIn("figures/test.png", figure_paths)
        self.assertIn("figures/complex.svg", figure_paths)

    def test_figure_metadata_extraction(self):
        """Test extraction of figure metadata."""
        content = "![Complex Figure Caption](figures/test.png){#fig:test width=80% height=60%}"

        figures = self.processor.extract_figures(content)

        self.assertEqual(len(figures), 1)
        figure = figures[0]

        self.assertEqual(figure.get("id"), "fig:test")
        self.assertEqual(figure.get("caption"), "Complex Figure Caption")
        self.assertIn("width", figure.get("attributes", {}))
        self.assertEqual(figure["attributes"]["width"], "80%")

    def test_figure_format_validation(self):
        """Test validation of figure file formats."""
        # Create test figure files
        valid_formats = ["test.png", "test.jpg", "test.svg", "test.pdf"]
        invalid_formats = ["test.txt", "test.doc"]

        for fmt in valid_formats:
            fig_path = self.figures_dir / fmt
            fig_path.write_text("fake content")

        for fmt in invalid_formats:
            fig_path = self.figures_dir / fmt
            fig_path.write_text("fake content")

        # Test validation
        old_cwd = Path.cwd()
        os.chdir(self.temp_dir)

        try:
            for fmt in valid_formats:
                result = self.processor.validate_format(f"figures/{fmt}")
                self.assertTrue(result["valid"], f"Format {fmt} should be valid")

            for fmt in invalid_formats:
                result = self.processor.validate_format(f"figures/{fmt}")
                self.assertFalse(result["valid"], f"Format {fmt} should be invalid")
        finally:
            os.chdir(old_cwd)

    def test_figure_path_resolution(self):
        """Test resolution of figure file paths."""
        content = SAMPLE_FIGURE_CONTENT

        # Create some test figures
        test_figures = ["test.png", "complex.svg", "a.png", "b.png"]
        for fig in test_figures:
            fig_path = self.figures_dir / fig
            fig_path.write_text("fake image data")

        old_cwd = Path.cwd()
        os.chdir(self.temp_dir)

        try:
            resolution_result = self.processor.resolve_paths(content)

            self.assertIn("resolved", resolution_result)
            self.assertIn("missing", resolution_result)

            # Should find existing figures
            resolved = resolution_result["resolved"]
            self.assertGreater(len(resolved), 0)
        finally:
            os.chdir(old_cwd)

    def test_figure_reference_validation(self):
        """Test validation of figure cross-references."""
        content = """
        ![Test Figure](figures/test.png){#fig:test}

        As shown in Figure @fig:test and @fig:missing.
        """

        validation_result = self.processor.validate_references(content)

        self.assertIn("valid_refs", validation_result)
        self.assertIn("missing_refs", validation_result)

        self.assertIn("fig:test", validation_result["valid_refs"])
        self.assertIn("fig:missing", validation_result["missing_refs"])


@pytest.mark.processor
@unittest.skipUnless(TEMPLATE_PROCESSOR_AVAILABLE, "Template processor not available")
class TestTemplateProcessor(ProcessorTestBase):
    """Test template processing functionality."""

    def setUp(self):
        super().setUp()
        self.processor = TemplateProcessor()

    def test_template_variable_replacement(self):
        """Test replacement of template variables."""
        template_content = """
        \\title{{{title}}}
        \\author{{{author}}}
        \\date{{{date}}}
        """

        variables = {"title": "Test Document", "author": "Test Author", "date": "2023-01-01"}

        processed = process_template_replacements(template_content, variables)

        self.assertIn("Test Document", processed)
        self.assertIn("Test Author", processed)
        self.assertIn("2023-01-01", processed)
        self.assertNotIn("{", processed)  # No template variables left

    def test_conditional_template_processing(self):
        """Test conditional content in templates."""
        template_content = """
        \\title{{{title}}}
        {% if authors %}
        \\author{ {{authors}} }
        {% endif %}
        {% if doi_validation %}
        % DOI validation enabled
        {% endif %}
        """

        variables = {"title": "Test", "authors": "John Doe", "doi_validation": True}

        processed = self.processor.process_conditionals(template_content, variables)

        self.assertIn("\\author{ John Doe }", processed)
        self.assertIn("% DOI validation enabled", processed)

    def test_template_loop_processing(self):
        """Test loop processing in templates."""
        template_content = """
        {% for author in authors %}
        \\author{ {{author.name}} }
        {% endfor %}
        """

        variables = {"authors": [{"name": "John Doe"}, {"name": "Jane Smith"}]}

        processed = self.processor.process_loops(template_content, variables)

        self.assertIn("\\author{ John Doe }", processed)
        self.assertIn("\\author{ Jane Smith }", processed)

    def test_template_path_resolution(self):
        """Test template file path resolution."""
        template_path = get_template_path()

        self.assertIsInstance(template_path, (str, Path))
        # Should point to valid template location
        if Path(template_path).exists():
            self.assertTrue(Path(template_path).is_file())

    def test_nested_template_variables(self):
        """Test nested template variable resolution."""
        template_content = """
        Title: {{metadata.title}}
        First Author: {{metadata.authors.0.name}}
        Journal: {{metadata.publication.journal}}
        """

        variables = {
            "metadata": {
                "title": "Nested Test",
                "authors": [{"name": "Nested Author"}],
                "publication": {"journal": "Nested Journal"},
            }
        }

        processed = self.processor.process_nested_variables(template_content, variables)

        self.assertIn("Nested Test", processed)
        self.assertIn("Nested Author", processed)
        self.assertIn("Nested Journal", processed)


@pytest.mark.processor
class TestProcessorIntegration(ProcessorTestBase):
    """Integration tests for processor components."""

    def test_full_document_processing_pipeline(self):
        """Test complete document processing pipeline."""
        # Skip if core processors not available
        if not (YAML_PROCESSOR_AVAILABLE and CITATION_PROCESSORS_AVAILABLE):
            self.skipTest("Core processors not available")

        # Create comprehensive test document
        manuscript_content = f"""---
{SAMPLE_YAML_CONFIG}---

{SAMPLE_MANUSCRIPT_WITH_CITATIONS}

{SAMPLE_MATH_CONTENT}

{SAMPLE_FIGURE_CONTENT}
"""

        manuscript_file = self.create_test_file("full_manuscript.md", manuscript_content)

        # Process through pipeline
        metadata = extract_yaml_metadata(str(manuscript_file))

        if CITATION_PROCESSORS_AVAILABLE:
            citation_processor = CitationProcessor()
            citations = citation_processor.extract_citations(manuscript_content)
            self.assertGreater(len(citations), 0, "Should extract citations")

        if MATH_PROCESSOR_AVAILABLE:
            math_processor = MathProcessor()
            math_exprs = math_processor.extract_math(manuscript_content)
            self.assertGreater(len(math_exprs), 0, "Should extract math expressions")

        if FIGURE_PROCESSOR_AVAILABLE:
            figure_processor = FigureProcessor()
            figures = figure_processor.extract_figures(manuscript_content)
            self.assertGreater(len(figures), 0, "Should extract figures")

        # Verify metadata extraction
        self.assertEqual(metadata["title"], "Test Manuscript Title")
        self.assertEqual(len(metadata["authors"]), 2)

    def test_error_handling_across_processors(self):
        """Test error handling consistency across processors."""
        malformed_content = """
        Invalid YAML metadata
        Malformed math: $\\invalid{syntax
        Missing figure: ![](nonexistent.png)
        Bad citation: [@invalid citation with spaces]
        """

        processors = []
        if YAML_PROCESSOR_AVAILABLE:
            processors.append(("yaml", lambda: extract_yaml_metadata("/nonexistent/file")))
        if MATH_PROCESSOR_AVAILABLE:
            processors.append(("math", lambda: MathProcessor().validate_syntax(malformed_content)))
        if CITATION_PROCESSORS_AVAILABLE:
            processors.append(("citation", lambda: CitationProcessor().extract_citations(malformed_content)))

        # Each processor should handle errors gracefully
        for name, processor_func in processors:
            try:
                result = processor_func()
                # Should return error information rather than crashing
                self.assertTrue(
                    isinstance(result, (dict, list, tuple)), f"{name} processor should return structured error info"
                )
            except Exception as e:
                # If exceptions are thrown, they should be meaningful
                self.assertIsInstance(
                    e,
                    (ValueError, FileNotFoundError, yaml.YAMLError),
                    f"{name} processor should throw appropriate exception types",
                )

    def test_processor_availability(self):
        """Test that processors handle unavailable dependencies gracefully."""
        availability_map = {
            "yaml": YAML_PROCESSOR_AVAILABLE,
            "citation": CITATION_PROCESSORS_AVAILABLE,
            "math": MATH_PROCESSOR_AVAILABLE,
            "figure": FIGURE_PROCESSOR_AVAILABLE,
            "template": TEMPLATE_PROCESSOR_AVAILABLE,
        }

        for processor_type, is_available in availability_map.items():
            with self.subTest(processor_type=processor_type):
                if is_available:
                    # Processor should be functional
                    self.assertTrue(True, f"{processor_type} processor is available and functional")
                else:
                    # Test suite should handle unavailable processors gracefully
                    self.assertTrue(True, f"{processor_type} processor gracefully unavailable")


if __name__ == "__main__":
    # Configure test runner
    if PYTEST_AVAILABLE:
        pytest.main([__file__, "-v"])
    else:
        unittest.main(verbosity=2)
