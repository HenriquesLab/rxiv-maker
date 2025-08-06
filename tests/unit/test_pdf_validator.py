"""Unit tests for PDF validator improvements."""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

try:
    import pytest

    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

    # Define mock pytest.mark for when pytest is not available
    class MockPytest:
        class mark:
            @staticmethod
            def pdf_validation(cls):
                return cls

    pytest = MockPytest()

try:
    from rxiv_maker.validators.base_validator import ValidationLevel, ValidationResult
    from rxiv_maker.validators.pdf_validator import PDFValidator

    PDF_VALIDATOR_AVAILABLE = True
except ImportError:
    PDF_VALIDATOR_AVAILABLE = False


@pytest.mark.pdf_validation
@unittest.skipUnless(PDF_VALIDATOR_AVAILABLE, "PDF validator not available")
class TestPDFValidator(unittest.TestCase):
    """Test PDF validator functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = os.path.join(self.temp_dir, "manuscript")
        os.makedirs(self.manuscript_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_malformed_equation_context_truncation(self):
        """Test that malformed equation context is properly truncated."""
        validator = PDFValidator(self.manuscript_dir)

        # Mock PDF text with a very long malformed equation
        long_equation = "x" * 200  # Very long equation
        validator.pdf_text = f"Some text with malformed equation: ${long_equation}$ and more text"

        # Mock the regex to find the long equation
        with patch.object(validator, "malformed_equation_pattern") as mock_pattern:
            mock_pattern.findall.return_value = [long_equation]

            errors = validator._validate_equations()

            # Should have one warning
            self.assertEqual(len(errors), 1)
            error = errors[0]

            # Should be WARNING level, not ERROR
            self.assertEqual(error.level, ValidationLevel.WARNING)

            # Context should be truncated
            self.assertIn("...", error.context)

            # Should contain PyPDF limitation note
            self.assertIn("PyPDF text extraction", error.suggestion)

    def test_malformed_equation_downgraded_to_warning(self):
        """Test that malformed equations are warnings, not errors."""
        validator = PDFValidator(self.manuscript_dir)
        validator.pdf_text = "Some text with malformed equation: $incomplete"

        with patch.object(validator, "malformed_equation_pattern") as mock_pattern:
            mock_pattern.findall.return_value = ["incomplete"]

            errors = validator._validate_equations()

            # Should have one warning
            self.assertEqual(len(errors), 1)
            error = errors[0]

            # Should be WARNING level
            self.assertEqual(error.level, ValidationLevel.WARNING)

            # Should mention potential false positives
            self.assertIn("potentially malformed", error.message)
            self.assertIn("PyPDF text extraction", error.suggestion)

    def test_pdf_validation_output_format(self):
        """Test that PDF validation output includes proper formatting."""
        # Create a mock PDF validator result
        errors = [
            Mock(
                level=ValidationLevel.WARNING,
                message="Test warning",
                context="Test context",
                suggestion="Test suggestion",
            )
        ]

        metadata = {
            "total_pages": 5,
            "total_words": 1000,
            "citations_found": 3,
            "figure_references": 2,
        }

        result = ValidationResult("PDFValidator", errors, metadata)

        # Test the output format directly by simulating the print statements
        # This tests the logic without importing the __main__ block

        # Check that metadata contains the expected values
        self.assertEqual(result.metadata["total_pages"], 5)
        self.assertEqual(result.metadata["total_words"], 1000)
        self.assertEqual(result.metadata["citations_found"], 3)
        self.assertEqual(result.metadata["figure_references"], 2)

        # Check that errors are present (which would trigger the visual check message)
        self.assertTrue(len(result.errors) > 0)

    def test_no_success_message_in_result(self):
        """Test that SUCCESS level messages are not added to validation results."""
        validator = PDFValidator(self.manuscript_dir)

        # Mock successful validation scenario
        validator.pdf_text = "Some normal text"

        with patch.object(validator, "_find_pdf_file") as mock_find:
            with patch.object(validator, "_extract_pdf_text") as mock_extract:
                mock_find.return_value = Mock()
                mock_extract.return_value = ("Some normal text", ["page1"])

                with patch.object(validator, "_get_validation_statistics") as mock_stats:
                    mock_stats.return_value = {"total_pages": 1, "total_words": 3}

                    result = validator.validate()

                    # Should not have any SUCCESS level messages
                    success_messages = [e for e in result.errors if e.level == ValidationLevel.SUCCESS]
                    self.assertEqual(len(success_messages), 0)

    def test_pdf_file_not_found_error(self):
        """Test that proper error is returned when PDF file is not found."""
        validator = PDFValidator(self.manuscript_dir)

        with patch.object(validator, "_find_pdf_file", return_value=None):
            result = validator.validate()

            # Should have error about PDF not found
            self.assertTrue(result.has_errors)
            error_messages = [error.message for error in result.errors]
            self.assertTrue(any("No PDF file found" in msg for msg in error_messages))

    def test_multiple_malformed_equations_sampling(self):
        """Test that only sample equations are shown in context."""
        validator = PDFValidator(self.manuscript_dir)

        # Mock multiple malformed equations
        equations = [
            "eq1_short",
            "eq2_very_long_equation_" + "x" * 100,
            "eq3_short",
            "eq4_short",
        ]

        with patch.object(validator, "malformed_equation_pattern") as mock_pattern:
            mock_pattern.findall.return_value = equations

            errors = validator._validate_equations()

            # Should have one warning
            self.assertEqual(len(errors), 1)
            error = errors[0]

            # Should mention the total count
            self.assertIn("Found 4 potentially malformed", error.message)

            # Context should only show first 2 equations (samples)
            self.assertIn("eq1_short", error.context)
            self.assertIn("eq2_very_long_equation_", error.context)  # Should be truncated
            self.assertIn("...", error.context)  # Should show truncation

            # Should not show all equations
            self.assertNotIn("eq3_short", error.context)
            self.assertNotIn("eq4_short", error.context)


@pytest.mark.pdf_validation
@unittest.skipUnless(PDF_VALIDATOR_AVAILABLE, "PDF validator not available")
class TestPDFValidatorIntegration(unittest.TestCase):
    """Integration tests for PDF validator."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = os.path.join(self.temp_dir, "manuscript")
        os.makedirs(self.manuscript_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_pdf_validation_with_mock_pdf(self):
        """Test PDF validation with a mock PDF file."""
        # Create a mock PDF file
        pdf_path = os.path.join(self.manuscript_dir, "test.pdf")
        with open(pdf_path, "w") as f:
            f.write("fake pdf content")

        validator = PDFValidator(self.manuscript_dir, pdf_path=pdf_path)

        # Mock pypdf functionality
        with patch("src.rxiv_maker.validators.pdf_validator.pypdf") as mock_pypdf:
            mock_reader = Mock()
            mock_page = Mock()
            mock_page.extract_text.return_value = "This is test text with some equations $E=mc^2$"
            mock_reader.pages = [mock_page]
            mock_pypdf.PdfReader.return_value = mock_reader

            result = validator.validate()

            # Should successfully validate
            self.assertIsNotNone(result)
            self.assertEqual(result.validator_name, "PDFValidator")


if __name__ == "__main__":
    unittest.main()
