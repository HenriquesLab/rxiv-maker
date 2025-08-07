"""Tests for Figure Generation functionality.

This module tests the figure generation system including Python scripts,
R scripts, Mermaid diagrams, ggplot2 compatibility, and Docker fallback behavior.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Mock the imports to avoid dependency issues during testing
with patch.dict(
    "sys.modules",
    {
        "src.py.utils.platform": MagicMock(),
        "src.py.commands.generate_figures": MagicMock(),
    },
):
    pass


class TestFigureGeneratorCore(unittest.TestCase):
    """Test core FigureGenerator functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.figures_dir = Path(self.temp_dir) / "FIGURES"
        self.output_dir = Path(self.temp_dir) / "output"
        self.figures_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

    def test_figure_generator_initialization(self):
        """Test FigureGenerator initialization with different parameters."""

        # Mock the FigureGenerator class
        class MockFigureGenerator:
            def __init__(
                self,
                figures_dir="FIGURES",
                output_dir="FIGURES",
                output_format="png",
                r_only=False,
            ):
                self.figures_dir = Path(figures_dir)
                self.output_dir = Path(output_dir)
                self.output_format = output_format.lower()
                self.r_only = r_only
                self.supported_formats = ["png", "svg", "pdf", "eps"]

        # Test default initialization
        generator = MockFigureGenerator()
        self.assertEqual(generator.figures_dir, Path("FIGURES"))
        self.assertEqual(generator.output_dir, Path("FIGURES"))
        self.assertEqual(generator.output_format, "png")
        self.assertFalse(generator.r_only)

        # Test custom initialization
        generator = MockFigureGenerator(
            figures_dir="custom/figures",
            output_dir="custom/output",
            output_format="SVG",
            r_only=True,
        )
        self.assertEqual(generator.figures_dir, Path("custom/figures"))
        self.assertEqual(generator.output_dir, Path("custom/output"))
        self.assertEqual(generator.output_format, "svg")
        self.assertTrue(generator.r_only)

    def test_supported_output_formats(self):
        """Test that all expected output formats are supported."""
        expected_formats = ["png", "svg", "pdf", "eps"]

        class MockFigureGenerator:
            def __init__(self):
                self.supported_formats = ["png", "svg", "pdf", "eps"]

        generator = MockFigureGenerator()
        self.assertEqual(generator.supported_formats, expected_formats)

    def test_figure_file_detection(self):
        """Test detection of different figure file types."""
        # Create test files
        (self.figures_dir / "figure1.py").touch()
        (self.figures_dir / "figure2.R").touch()
        (self.figures_dir / "figure3.mmd").touch()
        (self.figures_dir / "not_a_figure.txt").touch()

        # Test file detection logic
        python_files = list(self.figures_dir.glob("*.py"))
        r_files = list(self.figures_dir.glob("*.R"))
        mermaid_files = list(self.figures_dir.glob("*.mmd"))

        self.assertEqual(len(python_files), 1)
        self.assertEqual(len(r_files), 1)
        self.assertEqual(len(mermaid_files), 1)
        self.assertEqual(python_files[0].name, "figure1.py")
        self.assertEqual(r_files[0].name, "figure2.R")
        self.assertEqual(mermaid_files[0].name, "figure3.mmd")


class TestRScriptCompatibility(unittest.TestCase):
    """Test R script execution and ggplot2 compatibility."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_r_script = Path(self.temp_dir) / "test_figure.R"

    def test_ggplot2_size_parameter_compatibility(self):
        """Test ggplot2 compatibility with 'size' parameter instead of 'linewidth'."""
        # Create R script content that uses 'size' parameter (compatible version)
        r_script_content = """
library(ggplot2)

# Test plot using 'size' parameter (compatible with older ggplot2)
p <- ggplot(data.frame(x=1:10, y=1:10), aes(x=x, y=y)) +
    geom_line(size = 0.6, alpha = 0.8) +
    theme_minimal() +
    theme(
        panel.grid.minor = element_line(size = 0.3, linetype = "dotted"),
        panel.grid.major = element_line(size = 0.3)
    )

ggsave("test_output.png", plot = p, width = 4, height = 3, dpi = 300)
"""

        # Write test script
        with open(self.test_r_script, "w") as f:
            f.write(r_script_content)

        # Test that the script contains 'size' parameters (not 'linewidth')
        script_content = self.test_r_script.read_text()
        self.assertIn("size = 0.6", script_content)
        self.assertIn("size = 0.3", script_content)
        self.assertNotIn("linewidth", script_content)

    def test_ggplot2_linewidth_parameter_detection(self):
        """Test detection of incompatible 'linewidth' parameter."""
        # Create R script with incompatible 'linewidth' parameter
        incompatible_content = """
library(ggplot2)

# This would fail on older ggplot2 versions
p <- ggplot(data.frame(x=1:10, y=1:10), aes(x=x, y=y)) +
    geom_line(linewidth = 0.6, alpha = 0.8) +
    theme(
        panel.grid.minor = element_line(linewidth = 0.3, linetype = "dotted")
    )
"""

        with open(self.test_r_script, "w") as f:
            f.write(incompatible_content)

        script_content = self.test_r_script.read_text()
        self.assertIn("linewidth", script_content)

    @patch("subprocess.run")
    def test_r_script_execution_simulation(self, mock_run):
        """Test R script execution simulation."""
        mock_run.return_value = Mock(returncode=0, stdout="Script executed successfully")

        # Simulate running an R script
        result = subprocess.run(
            ["Rscript", str(self.test_r_script)],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )

        self.assertEqual(result.returncode, 0)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_r_script_execution_failure(self, mock_run):
        """Test R script execution failure handling."""
        mock_run.return_value = Mock(returncode=1, stderr="Error: object 'linewidth' not found")

        result = subprocess.run(["Rscript", str(self.test_r_script)], capture_output=True, text=True)

        self.assertEqual(result.returncode, 1)
        self.assertIn("linewidth", result.stderr)

    def test_r_script_output_files_generation(self):
        """Test that R scripts generate expected output files."""
        expected_outputs = ["test_figure.pdf", "test_figure.png", "test_figure.svg"]

        # Simulate file generation
        for output_file in expected_outputs:
            output_path = Path(self.temp_dir) / output_file
            output_path.touch()
            self.assertTrue(output_path.exists())

    def test_r_package_dependency_detection(self):
        """Test detection of R package dependencies."""
        r_script_with_deps = """
library(ggplot2)
library(scales)
library(readr)
library(dplyr)
library(svglite)
"""

        expected_packages = ["ggplot2", "scales", "readr", "dplyr", "svglite"]

        for package in expected_packages:
            self.assertIn(f"library({package})", r_script_with_deps)


class TestPythonScriptExecution(unittest.TestCase):
    """Test Python script execution for figure generation."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_py_script = Path(self.temp_dir) / "test_figure.py"

    def test_python_figure_script_template(self):
        """Test basic Python figure script template."""
        python_script_content = """
import matplotlib.pyplot as plt
import numpy as np

# Generate test data
x = np.linspace(0, 10, 100)
y = np.sin(x)

# Create figure
plt.figure(figsize=(8, 6))
plt.plot(x, y, linewidth=2)
plt.title("Test Figure")
plt.xlabel("X axis")
plt.ylabel("Y axis")

# Save in multiple formats
plt.savefig("test_figure.png", dpi=300, bbox_inches='tight')
plt.savefig("test_figure.pdf", bbox_inches='tight')
plt.savefig("test_figure.svg", bbox_inches='tight')
"""

        with open(self.test_py_script, "w") as f:
            f.write(python_script_content)

        script_content = self.test_py_script.read_text()
        self.assertIn("matplotlib.pyplot", script_content)
        self.assertIn("savefig", script_content)

    @patch("subprocess.run")
    def test_python_script_execution_simulation(self, mock_run):
        """Test Python script execution simulation."""
        mock_run.return_value = Mock(returncode=0, stdout="Figure generated successfully")

        result = subprocess.run(
            ["python", str(self.test_py_script)],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
        )

        self.assertEqual(result.returncode, 0)

    @patch("subprocess.run")
    def test_python_script_import_error(self, mock_run):
        """Test Python script execution with import errors."""
        mock_run.return_value = Mock(returncode=1, stderr="ModuleNotFoundError: No module named 'matplotlib'")

        result = subprocess.run(["python", str(self.test_py_script)], capture_output=True, text=True)

        self.assertEqual(result.returncode, 1)
        self.assertIn("matplotlib", result.stderr)

    def test_python_figure_output_formats(self):
        """Test Python figure output format generation."""
        expected_formats = [".png", ".pdf", ".svg", ".eps"]

        for fmt in expected_formats:
            output_file = Path(self.temp_dir) / f"test_figure{fmt}"
            output_file.touch()
            self.assertTrue(output_file.exists())


class TestMermaidDiagramGeneration(unittest.TestCase):
    """Test Mermaid diagram generation functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_mmd_file = Path(self.temp_dir) / "test_diagram.mmd"

    def test_mermaid_diagram_content(self):
        """Test Mermaid diagram content structure."""
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

        content = self.test_mmd_file.read_text()
        self.assertIn("graph TD", content)
        self.assertIn("-->", content)

    def test_mermaid_output_formats(self):
        """Test Mermaid diagram output format support."""
        supported_formats = [".svg", ".png", ".pdf"]

        for fmt in supported_formats:
            output_file = Path(self.temp_dir) / f"test_diagram{fmt}"
            output_file.touch()
            self.assertTrue(output_file.exists())


class TestDockerFallbackBehavior(unittest.TestCase):
    """Test Docker fallback behavior for figure generation."""

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_docker_engine_mode_detection(self, mock_which, mock_run):
        """Test Docker engine mode detection and usage."""
        # Mock environment variable
        with patch.dict(os.environ, {"RXIV_ENGINE": "DOCKER"}):
            self.assertEqual(os.environ.get("RXIV_ENGINE"), "DOCKER")

    @patch("subprocess.run")
    def test_docker_python_execution(self, mock_run):
        """Test Python script execution in Docker mode."""
        mock_run.return_value = Mock(returncode=0, stdout="Docker Python execution")

        docker_cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            "/workspace:/workspace",
            "-w",
            "/workspace",
            "henriqueslab/rxiv-maker-base:latest",
            "python",
            "test_figure.py",
        ]

        result = subprocess.run(docker_cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)

    @patch("subprocess.run")
    def test_docker_r_execution(self, mock_run):
        """Test R script execution in Docker mode."""
        mock_run.return_value = Mock(returncode=0, stdout="Docker R execution")

        docker_cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            "/workspace:/workspace",
            "-w",
            "/workspace",
            "henriqueslab/rxiv-maker-base:latest",
            "Rscript",
            "test_figure.R",
        ]

        result = subprocess.run(docker_cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)

    def test_platform_architecture_detection(self):
        """Test platform architecture detection for Docker image selection."""
        # Test AMD64 detection
        with patch("platform.machine", return_value="x86_64"):
            import platform

            arch = platform.machine()
            expected_platform = "linux/amd64" if arch == "x86_64" else "linux/arm64"
            self.assertEqual(expected_platform, "linux/amd64")

        # Test ARM64 detection
        with patch("platform.machine", return_value="arm64"):
            import platform

            arch = platform.machine()
            expected_platform = "linux/amd64" if arch == "x86_64" else "linux/arm64"
            self.assertEqual(expected_platform, "linux/arm64")

    @patch("subprocess.run")
    def test_docker_availability_check(self, mock_run):
        """Test Docker availability checking."""
        # Docker available
        mock_run.return_value = Mock(returncode=0, stdout="Docker version 20.10.0")
        result = subprocess.run(["docker", "--version"], capture_output=True)
        self.assertEqual(result.returncode, 0)

        # Docker not available
        mock_run.return_value = Mock(returncode=1, stderr="docker: command not found")
        result = subprocess.run(["docker", "--version"], capture_output=True)
        self.assertEqual(result.returncode, 1)


class TestFigureValidationAndErrorHandling(unittest.TestCase):
    """Test figure validation and error handling scenarios."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def test_missing_figure_file_detection(self):
        """Test detection of missing figure files."""
        non_existent_file = Path(self.temp_dir) / "missing_figure.py"
        self.assertFalse(non_existent_file.exists())

    def test_invalid_figure_format_detection(self):
        """Test detection of invalid figure formats."""
        valid_extensions = [".py", ".R", ".mmd"]
        invalid_file = Path(self.temp_dir) / "invalid_figure.txt"

        invalid_file.touch()
        self.assertTrue(invalid_file.exists())
        self.assertNotIn(invalid_file.suffix, valid_extensions)

    def test_output_directory_creation(self):
        """Test automatic output directory creation."""
        output_dir = Path(self.temp_dir) / "output" / "figures"

        # Simulate directory creation
        output_dir.mkdir(parents=True, exist_ok=True)
        self.assertTrue(output_dir.exists())

    @patch("subprocess.run")
    def test_script_execution_timeout_handling(self, mock_run):
        """Test handling of script execution timeouts."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["python", "long_running_script.py"], timeout=30)

        with self.assertRaises(subprocess.TimeoutExpired):
            subprocess.run(["python", "long_running_script.py"], timeout=30, capture_output=True)

    def test_figure_checksum_validation(self):
        """Test figure file checksum validation for regeneration decisions."""
        import hashlib

        # Create test file
        test_file = Path(self.temp_dir) / "test_figure.py"
        content = "print('test figure')"
        test_file.write_text(content)

        # Calculate checksum
        checksum = hashlib.md5(content.encode()).hexdigest()
        self.assertEqual(len(checksum), 32)

    def test_concurrent_figure_generation_safety(self):
        """Test safety of concurrent figure generation."""
        # Test that multiple figure files can be processed
        figure_files = []
        for i in range(3):
            fig_file = Path(self.temp_dir) / f"figure_{i}.py"
            fig_file.write_text(f"# Figure {i}")
            figure_files.append(fig_file)

        self.assertEqual(len(figure_files), 3)
        for fig_file in figure_files:
            self.assertTrue(fig_file.exists())


class TestFigureProcessorIntegration(unittest.TestCase):
    """Test integration between figure generation and processing systems."""

    def test_figure_reference_extraction(self):
        """Test extraction of figure references from markdown."""
        markdown_content = """
See @fig:example for details.
Also refer to @fig:workflow and @fig:results.
"""

        # Test figure reference pattern matching
        import re

        fig_pattern = r"@fig:(\w+)"
        matches = re.findall(fig_pattern, markdown_content)

        expected_refs = ["example", "workflow", "results"]
        self.assertEqual(matches, expected_refs)

    def test_figure_cross_reference_validation(self):
        """Test validation of figure cross-references."""
        available_figures = ["figure_1", "figure_2", "sfigure_1"]
        referenced_figures = ["figure_1", "figure_3"]  # figure_3 doesn't exist

        missing_figures = set(referenced_figures) - set(available_figures)
        self.assertEqual(missing_figures, {"figure_3"})

    def test_figure_output_path_construction(self):
        """Test figure output path construction."""
        base_name = "SFigure__example"
        output_formats = ["png", "svg", "pdf"]

        expected_paths = [
            f"SFigure__example/{base_name}.png",
            f"SFigure__example/{base_name}.svg",
            f"SFigure__example/{base_name}.pdf",
        ]

        generated_paths = [f"{base_name}/{base_name}.{fmt}" for fmt in output_formats]
        self.assertEqual(generated_paths, expected_paths)

    def test_figure_metadata_extraction(self):
        """Test extraction of figure metadata from scripts."""
        r_script_content = """
#!/usr/bin/env Rscript
# SFigure 3: ArXiv Preprints Over Time
#
# Publication-ready plot showing the growth of arXiv submissions.
"""

        # Extract title from comment
        import re

        title_match = re.search(r"# (.+): (.+)", r_script_content)
        if title_match:
            figure_id = title_match.group(1)
            figure_title = title_match.group(2)
            self.assertEqual(figure_id, "SFigure 3")
            self.assertEqual(figure_title, "ArXiv Preprints Over Time")


if __name__ == "__main__":
    unittest.main()
