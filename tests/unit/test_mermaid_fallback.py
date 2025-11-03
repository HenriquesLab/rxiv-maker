"""Tests for Mermaid diagram generation with fallback behavior."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


class TestMermaidFallbackBehavior(unittest.TestCase):
    """Test Mermaid diagram fallback mechanisms when service is unavailable."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.figures_dir = Path(self.temp_dir) / "FIGURES"
        self.output_dir = Path(self.temp_dir) / "output"
        self.figures_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

        # Create a test mermaid file
        self.test_mmd_file = self.figures_dir / "test_diagram.mmd"
        mermaid_content = """
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process 1]
    B -->|No| D[Process 2]
    C --> E[End]
    D --> E
"""
        with open(self.test_mmd_file, "w") as f:
            f.write(mermaid_content)

    @patch("requests.get")
    def test_mermaid_ink_503_error_fallback_pdf(self, mock_get):
        """Test that 503 error from mermaid.ink creates a valid PDF fallback."""
        # Import here to use the patched requests
        from rxiv_maker.engines.operations.generate_figures import FigureGenerator

        # Mock 503 Service Unavailable response
        mock_response = Mock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response

        # Create generator with PDF output
        generator = FigureGenerator(
            figures_dir=str(self.figures_dir),
            output_dir=str(self.output_dir),
            output_format="pdf",
            enable_content_caching=False,
        )

        # Generate figures
        generator.process_figures(use_rich=False)

        # Verify fallback PDF was created
        output_pdf = self.output_dir / "test_diagram.pdf"
        self.assertTrue(output_pdf.exists(), "Fallback PDF should be created")

        # Verify it's a valid PDF file (starts with %PDF)
        with open(output_pdf, "rb") as f:
            header = f.read(4)
            self.assertEqual(header, b"%PDF", "File should be a valid PDF")

    @patch("requests.get")
    def test_mermaid_ink_503_error_fallback_png(self, mock_get):
        """Test that 503 error from mermaid.ink creates a valid PNG fallback."""
        from rxiv_maker.engines.operations.generate_figures import FigureGenerator

        # Mock 503 Service Unavailable response
        mock_response = Mock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response

        # Create generator with PNG output
        generator = FigureGenerator(
            figures_dir=str(self.figures_dir),
            output_dir=str(self.output_dir),
            output_format="png",
            enable_content_caching=False,
        )

        # Generate figures
        generator.process_figures(use_rich=False)

        # Verify fallback PNG was created
        output_png = self.output_dir / "test_diagram.png"
        self.assertTrue(output_png.exists(), "Fallback PNG should be created")

        # Verify it's a valid PNG file (PNG magic bytes)
        with open(output_png, "rb") as f:
            header = f.read(8)
            self.assertEqual(header, b"\x89PNG\r\n\x1a\n", "File should be a valid PNG")

    @patch("rxiv_maker.engines.operations.generate_figures.get_with_retry")
    def test_mermaid_ink_503_error_fallback_svg(self, mock_retry):
        """Test that 503 error from mermaid.ink creates a valid SVG fallback."""
        from rxiv_maker.engines.operations.generate_figures import FigureGenerator

        # Mock 503 Service Unavailable response - make retry fail
        mock_retry.side_effect = Exception("Service unavailable after retries")

        # Create generator with SVG output
        generator = FigureGenerator(
            figures_dir=str(self.figures_dir),
            output_dir=str(self.output_dir),
            output_format="svg",
            enable_content_caching=False,
        )

        # Generate figures
        generator.process_figures(use_rich=False)

        # Verify fallback SVG was created
        output_svg = self.output_dir / "test_diagram.svg"
        self.assertTrue(output_svg.exists(), "Fallback SVG should be created")

        # Verify it's a valid SVG file
        with open(output_svg, "r") as f:
            content = f.read()
            self.assertIn("<?xml", content, "File should be valid XML")
            self.assertIn("<svg", content, "File should contain SVG element")
            self.assertIn("Service temporarily unavailable", content)

    @patch("rxiv_maker.engines.operations.generate_figures.get_with_retry")
    def test_mermaid_ink_retry_mechanism(self, mock_retry):
        """Test that get_with_retry is used for mermaid.ink requests."""
        from rxiv_maker.engines.operations.generate_figures import FigureGenerator

        # Mock successful retry after failures
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"%PDF-1.4\n"
        mock_retry.return_value = mock_response

        # Create generator
        generator = FigureGenerator(
            figures_dir=str(self.figures_dir),
            output_dir=str(self.output_dir),
            output_format="pdf",
            enable_content_caching=False,
        )

        # Generate figures
        generator.process_figures(use_rich=False)

        # Verify get_with_retry was called
        self.assertTrue(mock_retry.called, "get_with_retry should be used")

        # Verify it was called with retry parameters
        call_args = mock_retry.call_args
        self.assertIsNotNone(call_args)
        # Check that max_attempts was set
        if call_args[1]:  # kwargs
            self.assertIn("max_attempts", call_args[1])
            self.assertEqual(call_args[1]["max_attempts"], 5)

    @patch("rxiv_maker.engines.operations.generate_figures.get_with_retry")
    def test_mermaid_ink_complete_failure_creates_fallback(self, mock_retry):
        """Test that complete failure after retries creates fallback."""
        from rxiv_maker.engines.operations.generate_figures import FigureGenerator

        # Mock complete failure (all retries exhausted)
        mock_retry.side_effect = Exception("Service unavailable after retries")

        # Create generator
        generator = FigureGenerator(
            figures_dir=str(self.figures_dir),
            output_dir=str(self.output_dir),
            output_format="pdf",
            enable_content_caching=False,
        )

        # Generate figures
        generator.process_figures(use_rich=False)

        # Verify fallback PDF was created
        output_pdf = self.output_dir / "test_diagram.pdf"
        self.assertTrue(output_pdf.exists(), "Fallback PDF should be created even after complete failure")

        # Verify it's a valid PDF
        with open(output_pdf, "rb") as f:
            header = f.read(4)
            self.assertEqual(header, b"%PDF", "Fallback should be a valid PDF")

    def test_fallback_pdf_has_correct_structure(self):
        """Test that fallback PDF has correct structure and content."""
        from rxiv_maker.engines.operations.generate_figures import FigureGenerator

        generator = FigureGenerator(
            figures_dir=str(self.figures_dir),
            output_dir=str(self.output_dir),
            output_format="pdf",
            enable_content_caching=False,
        )

        # Create fallback directly
        output_pdf = self.output_dir / "test_diagram.pdf"
        success = generator._create_fallback_mermaid_diagram(self.test_mmd_file, output_pdf)

        self.assertTrue(success, "Fallback creation should succeed")
        self.assertTrue(output_pdf.exists(), "Fallback PDF should exist")

        # Read and verify PDF structure
        with open(output_pdf, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("%PDF-1.4", content)
            self.assertIn("/Type /Catalog", content)
            self.assertIn("/Type /Pages", content)
            self.assertIn("Mermaid Diagram Placeholder", content)
            self.assertIn("Service temporarily unavailable", content)
            self.assertIn("%%EOF", content)


if __name__ == "__main__":
    unittest.main()
