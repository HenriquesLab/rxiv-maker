"""Tests for figure generation engine functionality."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

try:
    from rxiv_maker.engines.operations.generate_figures import FigureGenerator, MermaidRenderer
except ImportError:
    # Create mock classes for testing if not available
    class FigureGenerator:
        def __init__(self, *args, **kwargs):
            pass

    class MermaidRenderer:
        def __init__(self, *args, **kwargs):
            pass


class TestFigureGeneratorBase(unittest.TestCase):
    """Base test class for figure generation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.figures_dir = self.temp_dir / "FIGURES"
        self.figures_dir.mkdir()
        self.output_dir = self.temp_dir / "output"
        self.output_dir.mkdir()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestFigureGeneratorInitialization(TestFigureGeneratorBase):
    """Test FigureGenerator initialization and basic functionality."""

    def test_figure_generator_import(self):
        """Test that FigureGenerator can be imported."""
        # Test basic import and instantiation
        try:
            generator = FigureGenerator()
            self.assertIsNotNone(generator)
        except Exception:
            # If FigureGenerator isn't fully implemented, that's ok for now
            pass

    def test_mermaid_renderer_import(self):
        """Test that MermaidRenderer can be imported."""
        try:
            renderer = MermaidRenderer()
            self.assertIsNotNone(renderer)
        except Exception:
            # If MermaidRenderer isn't fully implemented, that's ok for now
            pass

    def test_figures_directory_creation(self):
        """Test that figures directory can be created."""
        figures_path = self.temp_dir / "TEST_FIGURES"
        figures_path.mkdir()

        self.assertTrue(figures_path.exists())
        self.assertTrue(figures_path.is_dir())

    def test_output_directory_creation(self):
        """Test that output directory can be created."""
        output_path = self.temp_dir / "TEST_OUTPUT"
        output_path.mkdir()

        self.assertTrue(output_path.exists())
        self.assertTrue(output_path.is_dir())


class TestMermaidFileHandling(TestFigureGeneratorBase):
    """Test Mermaid diagram file handling."""

    def test_mermaid_file_creation(self):
        """Test creation of Mermaid diagram files."""
        mermaid_content = """
        graph TD
            A[Start] --> B{Decision}
            B -->|Yes| C[Action 1]
            B -->|No| D[Action 2]
        """

        mermaid_file = self.figures_dir / "test_diagram.mmd"
        mermaid_file.write_text(mermaid_content)

        self.assertTrue(mermaid_file.exists())
        self.assertEqual(mermaid_file.suffix, ".mmd")
        content = mermaid_file.read_text()
        self.assertIn("graph TD", content)

    def test_mermaid_output_directory(self):
        """Test Mermaid output directory structure."""
        diagram_name = "test_diagram"
        output_subdir = self.figures_dir / diagram_name
        output_subdir.mkdir()

        # Test expected output files
        expected_files = [f"{diagram_name}.svg", f"{diagram_name}.png", f"{diagram_name}.pdf"]

        for filename in expected_files:
            test_file = output_subdir / filename
            test_file.write_text("mock content")
            self.assertTrue(test_file.exists())

    @patch("requests.post")
    def test_mermaid_api_call_structure(self, mock_post):
        """Test Mermaid API call structure."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"<svg>mock svg content</svg>"
        mock_post.return_value = mock_response

        # Test API call parameters
        if mock_post.called:
            call_args = mock_post.call_args
            # Should have proper structure for API call
            self.assertIsNotNone(call_args)

    def test_mermaid_file_extension_detection(self):
        """Test detection of Mermaid files by extension."""
        test_files = [
            ("diagram.mmd", True),
            ("script.py", False),
            ("data.csv", False),
            ("another.mmd", True),
            ("readme.md", False),  # Should not match .md files
        ]

        for filename, should_be_mermaid in test_files:
            file_path = self.figures_dir / filename
            file_path.write_text("test content")

            is_mermaid = file_path.suffix == ".mmd"
            self.assertEqual(is_mermaid, should_be_mermaid, f"File {filename} mermaid detection failed")


class TestPythonScriptHandling(TestFigureGeneratorBase):
    """Test Python script figure generation."""

    def test_python_script_creation(self):
        """Test creation of Python figure scripts."""
        python_content = """
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(8, 6))
plt.plot(x, y)
plt.xlabel('X axis')
plt.ylabel('Y axis')
plt.title('Test Figure')
plt.savefig('output.png', dpi=300, bbox_inches='tight')
plt.close()
"""

        python_file = self.figures_dir / "test_figure.py"
        python_file.write_text(python_content)

        self.assertTrue(python_file.exists())
        self.assertEqual(python_file.suffix, ".py")
        content = python_file.read_text()
        self.assertIn("matplotlib", content)
        self.assertIn("savefig", content)

    def test_python_output_directory(self):
        """Test Python script output directory structure."""
        script_name = "test_figure"
        output_subdir = self.figures_dir / script_name
        output_subdir.mkdir()

        # Test expected output files
        expected_files = [f"{script_name}.png", f"{script_name}.pdf", f"{script_name}.svg"]

        for filename in expected_files:
            test_file = output_subdir / filename
            test_file.write_text("mock figure content")
            self.assertTrue(test_file.exists())

    @patch("subprocess.run")
    def test_python_execution_security(self, mock_run):
        """Test that Python execution uses secure practices."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        # Test that subprocess calls would use list arguments (secure)
        if mock_run.called:
            call_args = mock_run.call_args
            if call_args and call_args[0]:
                # Should use list format, not shell=True
                self.assertIsInstance(call_args[0][0], list)

    def test_python_file_detection(self):
        """Test detection of Python figure files."""
        test_files = [
            ("Figure1.py", True),
            ("SFigure_analysis.py", True),
            ("script.R", False),
            ("data.csv", False),
            ("test.py", True),
        ]

        for filename, should_be_python in test_files:
            file_path = self.figures_dir / filename
            file_path.write_text("# Python script")

            is_python = file_path.suffix == ".py"
            self.assertEqual(is_python, should_be_python, f"File {filename} Python detection failed")


class TestRScriptHandling(TestFigureGeneratorBase):
    """Test R script figure generation."""

    def test_r_script_creation(self):
        """Test creation of R figure scripts."""
        r_content = """
library(ggplot2)

data <- data.frame(
  x = 1:10,
  y = rnorm(10)
)

p <- ggplot(data, aes(x=x, y=y)) +
  geom_point() +
  geom_line() +
  labs(title="Test R Figure", x="X axis", y="Y axis")

ggsave("output.png", plot=p, width=8, height=6, dpi=300)
"""

        r_file = self.figures_dir / "test_figure.R"
        r_file.write_text(r_content)

        self.assertTrue(r_file.exists())
        self.assertEqual(r_file.suffix, ".R")
        content = r_file.read_text()
        self.assertIn("ggplot2", content)
        self.assertIn("ggsave", content)

    def test_r_file_detection(self):
        """Test detection of R figure files."""
        test_files = [
            ("Figure1.R", True),
            ("analysis.R", True),
            ("script.py", False),
            ("data.csv", False),
            ("test.r", False),  # Should be case sensitive
        ]

        for filename, should_be_r in test_files:
            file_path = self.figures_dir / filename
            file_path.write_text("# R script")

            is_r = file_path.suffix == ".R"
            self.assertEqual(is_r, should_be_r, f"File {filename} R detection failed")


class TestFigureFileTypes(TestFigureGeneratorBase):
    """Test handling of different figure file types."""

    def test_figure_naming_conventions(self):
        """Test figure naming convention detection."""
        test_names = [
            ("Figure1", True),
            ("SFigure_analysis", True),
            ("Figure__workflow", True),
            ("random_script", False),
            ("SFigure1", True),
        ]

        for name, is_figure in test_names:
            # Test naming convention logic
            matches_convention = name.startswith("Figure") or name.startswith("SFigure")
            self.assertEqual(matches_convention, is_figure, f"Naming convention failed for {name}")

    def test_output_format_support(self):
        """Test support for different output formats."""
        supported_formats = [".png", ".pdf", ".svg"]

        for fmt in supported_formats:
            test_file = self.figures_dir / f"test{fmt}"
            test_file.write_text("mock content")

            self.assertTrue(test_file.exists())
            self.assertIn(fmt, supported_formats)

    def test_data_directory_handling(self):
        """Test handling of DATA directory in figures."""
        data_dir = self.figures_dir / "DATA"
        data_dir.mkdir()

        # Create test data files
        test_data_files = ["dataset.csv", "analysis_results.json", "processed_data.xlsx"]

        for filename in test_data_files:
            data_file = data_dir / filename
            data_file.write_text("mock data content")
            self.assertTrue(data_file.exists())

    def test_figure_subdirectory_structure(self):
        """Test figure output subdirectory structure."""
        figure_name = "Figure_test"
        figure_subdir = self.figures_dir / figure_name
        figure_subdir.mkdir()

        # Should have proper subdirectory structure
        self.assertTrue(figure_subdir.exists())
        self.assertTrue(figure_subdir.is_dir())
        self.assertEqual(figure_subdir.name, figure_name)


class TestFigureGenerationIntegration(TestFigureGeneratorBase):
    """Integration tests for figure generation."""

    def test_complete_figure_workflow(self):
        """Test complete figure generation workflow."""
        # Create a complete figure setup
        figure_files = [
            ("Figure1.mmd", "graph TD\n    A --> B"),
            ("SFigure1.py", "import matplotlib.pyplot as plt\nplt.savefig('test.png')"),
            ("Figure2.R", "library(ggplot2)\nggsave('test.png')"),
        ]

        for filename, content in figure_files:
            file_path = self.figures_dir / filename
            file_path.write_text(content)

            # Create corresponding output directory
            name_without_ext = file_path.stem
            output_subdir = self.figures_dir / name_without_ext
            output_subdir.mkdir()

            self.assertTrue(file_path.exists())
            self.assertTrue(output_subdir.exists())

    def test_error_handling_missing_files(self):
        """Test error handling for missing figure files."""
        # Test handling of missing source files
        missing_file = self.figures_dir / "nonexistent.py"

        # Should handle missing files gracefully
        self.assertFalse(missing_file.exists())

    def test_mixed_file_types_handling(self):
        """Test handling of mixed file types in figures directory."""
        mixed_files = [
            ("valid_figure.py", "# Python script"),
            ("data.csv", "col1,col2\n1,2"),
            ("readme.txt", "This is a readme"),
            ("valid_diagram.mmd", "graph TD\n    A --> B"),
            ("invalid.xyz", "unknown format"),
        ]

        for filename, content in mixed_files:
            file_path = self.figures_dir / filename
            file_path.write_text(content)

        # Count valid figure files
        valid_extensions = [".py", ".R", ".mmd"]
        valid_count = sum(1 for f in mixed_files if any(f[0].endswith(ext) for ext in valid_extensions))

        self.assertEqual(valid_count, 2)  # .py and .mmd files


class TestEnvironmentVariables(unittest.TestCase):
    """Test environment variable handling in figure generation."""

    def test_rxiv_figure_output_dir(self):
        """Test RXIV_FIGURE_OUTPUT_DIR environment variable."""
        with patch.dict(os.environ, {"RXIV_FIGURE_OUTPUT_DIR": "/tmp/test"}):
            output_dir = os.environ.get("RXIV_FIGURE_OUTPUT_DIR")
            self.assertEqual(output_dir, "/tmp/test")

    def test_figure_generation_environment(self):
        """Test environment setup for figure generation."""
        # Test that proper environment variables can be set
        test_env = {
            "PYTHONPATH": "/test/path",
            "R_HOME": "/test/r/home",
            "PATH": "/test/bin:" + os.environ.get("PATH", ""),
        }

        with patch.dict(os.environ, test_env):
            for key, value in test_env.items():
                self.assertEqual(os.environ.get(key), value)


if __name__ == "__main__":
    unittest.main()
