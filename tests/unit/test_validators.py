"""Unit tests for the validation system."""

import os
import tempfile
import unittest

try:
    import pytest

    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

    # Define mock pytest.mark for when pytest is not available
    class MockPytest:
        class mark:
            @staticmethod
            def validation(cls):
                return cls

    pytest = MockPytest()

try:
    from rxiv_maker.validators import (
        CitationValidator,
        FigureValidator,
        LaTeXErrorParser,
        MathValidator,
        ReferenceValidator,
        SyntaxValidator,
        ValidationError,
        ValidationLevel,
        ValidationResult,
    )

    VALIDATORS_AVAILABLE = True
except ImportError:
    VALIDATORS_AVAILABLE = False


@pytest.mark.validation
@unittest.skipUnless(VALIDATORS_AVAILABLE, "Validators not available")
class TestBaseValidator(unittest.TestCase):
    """Test base validator functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validation_error_formatting(self):
        """Test validation error string formatting."""
        error = ValidationError(
            level=ValidationLevel.ERROR,
            message="Test error message",
            file_path="test.md",
            line_number=10,
            column=5,
            context="Test context",
            suggestion="Test suggestion",
        )

        error_str = str(error)
        self.assertIn("ERROR", error_str)
        self.assertIn("Test error message", error_str)
        self.assertIn("test.md:10:5", error_str)
        self.assertIn("Test context", error_str)
        self.assertIn("Test suggestion", error_str)

    def test_validation_result_properties(self):
        """Test validation result properties."""
        errors = [
            ValidationError(ValidationLevel.ERROR, "Error 1"),
            ValidationError(ValidationLevel.WARNING, "Warning 1"),
            ValidationError(ValidationLevel.INFO, "Info 1"),
        ]

        result = ValidationResult("TestValidator", errors, {})

        self.assertTrue(result.has_errors)
        self.assertTrue(result.has_warnings)
        self.assertEqual(result.error_count, 1)
        self.assertEqual(result.warning_count, 1)

        error_level_errors = result.get_errors_by_level(ValidationLevel.ERROR)
        self.assertEqual(len(error_level_errors), 1)
        self.assertEqual(error_level_errors[0].message, "Error 1")


@pytest.mark.validation
@unittest.skipUnless(VALIDATORS_AVAILABLE, "Validators not available")
class TestCitationValidator(unittest.TestCase):
    """Test citation validator."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

        # Create test manuscript structure
        self.manuscript_dir = os.path.join(self.temp_dir, "manuscript")
        os.makedirs(self.manuscript_dir)

        # Create test bibliography
        self.bib_content = """
@article{smith2023,
    title = {Test Article},
    author = {Smith, John},
    year = {2023}
}

@book{jones2022,
    title = {Test Book},
    author = {Jones, Jane},
    year = {2022}
}
"""
        with open(os.path.join(self.manuscript_dir, "03_REFERENCES.bib"), "w") as f:
            f.write(self.bib_content)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_citation_validation_valid_citations(self):
        """Test validation of valid citations."""
        # Create main manuscript with valid citations
        main_content = """
# Test Manuscript

This is a test with valid citations @smith2023 and [@jones2022].
Multiple citations work too [@smith2023;@jones2022].
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        validator = CitationValidator(self.manuscript_dir)
        result = validator.validate()

        # Should pass with no errors
        self.assertFalse(result.has_errors)

    def test_citation_validation_invalid_citations(self):
        """Test validation of invalid citations."""
        # Create main manuscript with invalid citations
        main_content = """
# Test Manuscript

This citation does not exist @nonexistent2023.
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        validator = CitationValidator(self.manuscript_dir)
        result = validator.validate()

        # Should have errors for undefined citation
        self.assertTrue(result.has_errors)
        error_messages = [error.message for error in result.errors]
        self.assertTrue(any("nonexistent2023" in msg for msg in error_messages))

    def test_citation_validation_unused_references(self):
        """Test detection of unused bibliography entries as warnings."""
        # Create main manuscript with only one citation
        main_content = """
# Test Manuscript

This text only cites one reference @smith2023.
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        validator = CitationValidator(self.manuscript_dir, enable_doi_validation=False)
        result = validator.validate()

        # Should have warnings for unused bibliography entries
        self.assertTrue(result.has_warnings)
        warning_messages = [error.message for error in result.errors if error.level.value == "warning"]

        # Should warn about unused jones2022 entry
        self.assertTrue(any("jones2022" in msg and "Unused bibliography entry" in msg for msg in warning_messages))

        # Check metadata
        self.assertEqual(result.metadata.get("unused_entries"), 1)
        self.assertEqual(result.metadata.get("unique_citations"), 1)

    def test_citation_validation_checks_both_main_and_supplementary(self):
        """Test that citations in both main and supplementary files are considered."""
        # Create main manuscript with one citation
        main_content = """
# Test Manuscript

This text cites @smith2023.
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        # Create supplementary with the other citation
        supp_content = """
# Supplementary Information

Additional details with reference to @jones2022.
"""
        with open(os.path.join(self.manuscript_dir, "02_SUPPLEMENTARY_INFO.md"), "w") as f:
            f.write(supp_content)

        validator = CitationValidator(self.manuscript_dir, enable_doi_validation=False)
        result = validator.validate()

        # Should NOT have warnings for unused entries since both are cited
        self.assertFalse(result.has_warnings)

        # Check metadata shows both citations found and no unused entries
        self.assertEqual(result.metadata.get("unused_entries"), 0)
        self.assertEqual(result.metadata.get("unique_citations"), 2)

    def test_citation_validation_excludes_system_entries(self):
        """Test that system entries like saraiva_2025_rxivmaker are not flagged as unused."""
        # Create bibliography with system entry and regular entry
        bib_content_with_system = """
@article{smith2023,
    title = {Test Article},
    author = {Smith, John},
    year = {2023}
}

@article{saraiva_2025_rxivmaker,
    title = {Rxiv-Maker: Automated LaTeX Article Generation},
    author = {Saraiva, Paulo},
    year = {2025}
}

@article{unused_entry,
    title = {Unused Article},
    author = {Nobody},
    year = {2023}
}
"""
        with open(os.path.join(self.manuscript_dir, "03_REFERENCES.bib"), "w") as f:
            f.write(bib_content_with_system)

        # Create main manuscript with only one citation (not citing system entry or unused entry)
        main_content = """
# Test Manuscript

This text only cites @smith2023.
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        validator = CitationValidator(self.manuscript_dir, enable_doi_validation=False)
        result = validator.validate()

        # Should have warnings for unused_entry but NOT for saraiva_2025_rxivmaker
        warning_messages = [error.message for error in result.errors if error.level.value == "warning"]

        # Should warn about unused_entry but not saraiva_2025_rxivmaker
        self.assertTrue(any("unused_entry" in msg and "Unused bibliography entry" in msg for msg in warning_messages))
        self.assertFalse(any("saraiva_2025_rxivmaker" in msg for msg in warning_messages))

        # Check metadata shows only 1 unused entry (not counting system entry)
        self.assertEqual(result.metadata.get("unused_entries"), 1)
        self.assertEqual(result.metadata.get("unique_citations"), 1)


@pytest.mark.validation
@unittest.skipUnless(VALIDATORS_AVAILABLE, "Validators not available")
class TestReferenceValidator(unittest.TestCase):
    """Test reference validator."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = os.path.join(self.temp_dir, "manuscript")
        os.makedirs(self.manuscript_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_reference_validation_valid_references(self):
        """Test validation of valid cross-references."""
        main_content = """
# Test Manuscript

See @fig:test for details.

![Test figure](FIGURES/test.png){#fig:test}
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        validator = ReferenceValidator(self.manuscript_dir)
        result = validator.validate()

        # Should pass with no errors
        self.assertFalse(result.has_errors)

    def test_reference_validation_undefined_references(self):
        """Test validation of undefined references."""
        main_content = """
# Test Manuscript

See @fig:nonexistent for details.
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        validator = ReferenceValidator(self.manuscript_dir)
        result = validator.validate()

        # Should have errors for undefined reference
        self.assertTrue(result.has_errors)
        error_messages = [error.message for error in result.errors]
        self.assertTrue(any("nonexistent" in msg for msg in error_messages))


@pytest.mark.validation
@unittest.skipUnless(VALIDATORS_AVAILABLE, "Validators not available")
class TestMathValidator(unittest.TestCase):
    """Test math validator."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = os.path.join(self.temp_dir, "manuscript")
        os.makedirs(self.manuscript_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_math_validation_valid_expressions(self):
        """Test validation of valid math expressions."""
        main_content = """
# Test Manuscript

Inline math: $E = mc^2$

Display math:
$$E = mc^2$$

Labeled equation:
$$\\frac{1}{2}mv^2 = mgh$${#eq:energy}
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        validator = MathValidator(self.manuscript_dir)
        result = validator.validate()

        # Should pass with no major errors
        self.assertFalse(result.has_errors)

    def test_math_validation_invalid_expressions(self):
        """Test validation of invalid math expressions."""
        main_content = """
# Test Manuscript

Unbalanced braces: $E = mc^{2$

Empty math: $$$$

Nested delimiters: $$E = mc^2 $$inside$$ more$$
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        validator = MathValidator(self.manuscript_dir)
        result = validator.validate()

        # Should have errors for invalid math
        self.assertTrue(result.has_errors)


@pytest.mark.validation
@unittest.skipUnless(VALIDATORS_AVAILABLE, "Validators not available")
class TestFigureValidator(unittest.TestCase):
    """Test figure validator."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = os.path.join(self.temp_dir, "manuscript")
        os.makedirs(self.manuscript_dir)

        # Create FIGURES directory
        self.figures_dir = os.path.join(self.manuscript_dir, "FIGURES")
        os.makedirs(self.figures_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_figure_validation_existing_files(self):
        """Test validation of existing figure files."""
        # Create test figure file
        test_fig_path = os.path.join(self.figures_dir, "test.png")
        with open(test_fig_path, "w") as f:
            f.write("fake png content")

        main_content = """
# Test Manuscript

![Test figure](FIGURES/test.png){#fig:test}

See @fig:test for details.
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        validator = FigureValidator(self.manuscript_dir)
        result = validator.validate()

        # Should pass with no errors for existing files
        self.assertFalse(result.has_errors)

    def test_figure_validation_missing_files(self):
        """Test validation of missing figure files."""
        main_content = """
# Test Manuscript

![Missing figure](FIGURES/missing.png){#fig:missing}
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        validator = FigureValidator(self.manuscript_dir)
        result = validator.validate()

        # Should have errors for missing files
        self.assertTrue(result.has_errors)
        error_messages = [error.message for error in result.errors]
        self.assertTrue(any("missing.png" in msg for msg in error_messages))


@pytest.mark.validation
@unittest.skipUnless(VALIDATORS_AVAILABLE, "Validators not available")
class TestSyntaxValidator(unittest.TestCase):
    """Test syntax validator."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = os.path.join(self.temp_dir, "manuscript")
        os.makedirs(self.manuscript_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_syntax_validation_valid_formatting(self):
        """Test validation of valid formatting."""
        main_content = """
# Test Manuscript

This has **bold** and *italic* text.
Also `inline code` and lists:

- Item 1
- Item 2
1. Numbered item
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        validator = SyntaxValidator(self.manuscript_dir)
        result = validator.validate()

        # Should pass with no major errors
        self.assertFalse(result.has_errors)

    def test_syntax_validation_unbalanced_formatting(self):
        """Test validation of unbalanced formatting."""
        main_content = """
# Test Manuscript

This has **unmatched bold and *mixed formatting problems.
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        validator = SyntaxValidator(self.manuscript_dir)
        result = validator.validate()

        # Should detect formatting issues
        # Note: This might generate warnings rather than errors depending on
        # implementation
        self.assertTrue(result.has_warnings or result.has_errors)


@pytest.mark.validation
@unittest.skipUnless(VALIDATORS_AVAILABLE, "Validators not available")
class TestLaTeXErrorParser(unittest.TestCase):
    """Test LaTeX error parser."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = os.path.join(self.temp_dir, "manuscript")
        os.makedirs(self.manuscript_dir)

        # Create output directory
        self.output_dir = os.path.join(self.manuscript_dir, "output")
        os.makedirs(self.output_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_latex_error_parsing(self):
        """Test parsing of LaTeX log file."""
        # Create a mock LaTeX log with errors
        log_content = """
This is pdfTeX, Version 3.14159265-2.6-1.40.20 (TeX Live 2019)

! Undefined control sequence.
l.42 \\unknowncommand
                     {test}

! Missing $ inserted.
<inserted text>
                $
l.45 E = mc^2

! File `missing.png' not found.
<argument> ...includegraphics {missing.png}
"""

        log_file_path = os.path.join(self.output_dir, "MANUSCRIPT.log")
        with open(log_file_path, "w") as f:
            f.write(log_content)

        parser = LaTeXErrorParser(self.manuscript_dir, log_file_path)
        result = parser.validate()

        # Should detect LaTeX errors
        self.assertTrue(result.has_errors)

        # Check that specific error types are detected
        error_messages = [error.message for error in result.errors]
        self.assertTrue(any("Unknown LaTeX command" in msg or "control sequence" in msg for msg in error_messages))


@pytest.mark.validation
@unittest.skipUnless(VALIDATORS_AVAILABLE, "Validators not available")
class TestValidationIntegration(unittest.TestCase):
    """Test integration of multiple validators."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = os.path.join(self.temp_dir, "manuscript")
        os.makedirs(self.manuscript_dir)

        # Create FIGURES directory
        self.figures_dir = os.path.join(self.manuscript_dir, "FIGURES")
        os.makedirs(self.figures_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_comprehensive_validation_valid_manuscript(self):
        """Test comprehensive validation of a valid manuscript."""
        # Create valid manuscript files
        config_content = """
title: "Test Article"
authors:
  - name: "Test Author"
date: "2024-01-01"
keywords: ["test", "validation"]
"""
        with open(os.path.join(self.manuscript_dir, "00_CONFIG.yml"), "w") as f:
            f.write(config_content)

        main_content = """
# Test Manuscript

This is a test manuscript with valid citations @smith2023 and figures.

![Test figure](FIGURES/test.png){#fig:test}

See @fig:test for mathematical details: $E = mc^2$.

## References
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        bib_content = """
@article{smith2023,
    title = {Test Article},
    author = {Smith, John},
    year = {2023}
}
"""
        with open(os.path.join(self.manuscript_dir, "03_REFERENCES.bib"), "w") as f:
            f.write(bib_content)

        # Create test figure file
        test_fig_path = os.path.join(self.figures_dir, "test.png")
        with open(test_fig_path, "w") as f:
            f.write("fake png content")

        # Test each validator
        validators = [
            CitationValidator(self.manuscript_dir),
            ReferenceValidator(self.manuscript_dir),
            FigureValidator(self.manuscript_dir),
            MathValidator(self.manuscript_dir),
            SyntaxValidator(self.manuscript_dir),
        ]

        for validator in validators:
            result = validator.validate()
            # Valid manuscript should pass all validations
            self.assertFalse(result.has_errors, f"{validator.__class__.__name__} failed validation")

    def test_comprehensive_validation_invalid_manuscript(self):
        """Test comprehensive validation of an invalid manuscript."""
        # Create manuscript with multiple issues
        config_content = """
title: "Test Article"
# Missing required fields like authors
"""
        with open(os.path.join(self.manuscript_dir, "00_CONFIG.yml"), "w") as f:
            f.write(config_content)

        main_content = """
# Test Manuscript

Invalid citation @nonexistent2023 and missing figure.

![Missing figure](FIGURES/missing.png){#fig:missing}

See @fig:nonexistent for details.

Invalid math: $E = mc^{2$ (unbalanced brace)
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        bib_content = """
@article{smith2023,
    title = {Test Article},
    author = {Smith, John},
    year = {2023}
}
"""
        with open(os.path.join(self.manuscript_dir, "03_REFERENCES.bib"), "w") as f:
            f.write(bib_content)

        # Test that validators catch different types of errors
        citation_validator = CitationValidator(self.manuscript_dir)
        citation_result = citation_validator.validate()
        self.assertTrue(citation_result.has_errors)  # Should catch nonexistent citation

        reference_validator = ReferenceValidator(self.manuscript_dir)
        reference_result = reference_validator.validate()
        self.assertTrue(reference_result.has_errors)  # Should catch undefined reference

        figure_validator = FigureValidator(self.manuscript_dir)
        figure_result = figure_validator.validate()
        self.assertTrue(figure_result.has_errors)  # Should catch missing figure

        math_validator = MathValidator(self.manuscript_dir)
        math_result = math_validator.validate()
        self.assertTrue(math_result.has_errors)  # Should catch unbalanced math


if __name__ == "__main__":
    unittest.main()
