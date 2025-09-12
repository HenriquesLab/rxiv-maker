"""Tests for manuscript figure utilities.

This module tests the figure generation utilities that are automatically
available in the Python execution context for manuscript processing.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from rxiv_maker.manuscript_utils.figure_utils import (
    clean_figure_outputs,
    convert_figures_bulk,
    convert_mermaid,
    convert_python_figure,
    convert_r_figure,
    get_figure_info,
    list_available_figures,
)


class TestMermaidConversion:
    """Test Mermaid diagram conversion functionality."""

    @pytest.mark.skip(reason="Mermaid figure generation functionality deprecated with RXIV_ENGINE removal")
    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.write_text")
    def test_convert_mermaid_basic(self, mock_write, mock_exists, mock_run):
        """Test basic Mermaid conversion."""
        # Setup mocks
        mock_exists.return_value = True
        mock_run.return_value = Mock(returncode=0)

        # Use a proper file path instead of mermaid content
        mermaid_file = "test_diagram.mmd"

        result = convert_mermaid(mermaid_file, "svg")

        # Should return the output path
        assert result == "FIGURES/Figure__test_diagram/Figure__test_diagram.svg"

        # Should have written the mermaid file
        mock_write.assert_called_once()

        # Should have called mermaid CLI
        mock_run.assert_called_once()

    @pytest.mark.skip(reason="Mermaid figure generation functionality deprecated with RXIV_ENGINE removal")
    @patch("subprocess.run")
    def test_convert_mermaid_error_handling(self, mock_run):
        """Test Mermaid conversion error handling."""
        # Simulate mermaid command failure
        mock_run.return_value = Mock(returncode=1, stderr="Error message")

        mermaid_code = "invalid mermaid syntax"

        with pytest.raises((ValueError, OSError, RuntimeError)):
            convert_mermaid(mermaid_code, "invalid_diagram")

    @pytest.mark.skip(reason="Mermaid figure generation functionality deprecated with RXIV_ENGINE removal")
    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.write_text")
    def test_convert_mermaid_custom_output_path(self, mock_write, mock_exists, mock_run):
        """Test Mermaid conversion with custom output path."""
        mock_exists.return_value = True
        mock_run.return_value = Mock(returncode=0)

        mermaid_code = "graph TD; A-->B"
        custom_path = "custom/path/diagram.svg"

        result = convert_mermaid(mermaid_code, "test", output_path=custom_path)

        assert result == custom_path


@pytest.mark.skip(reason="Python figure generation functionality deprecated with RXIV_ENGINE removal")
class TestPythonFigureConversion:
    """Test Python figure conversion functionality."""

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_convert_python_figure_basic(self, mock_exists, mock_run):
        """Test basic Python figure conversion."""
        mock_exists.return_value = True
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = convert_python_figure("FIGURES/test_figure.py")

        # Should return success
        assert result is True

        # Should have executed Python script
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "python" in args[0].lower()
        assert "test_figure.py" in " ".join(args)

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_convert_python_figure_missing_file(self, mock_exists, mock_run):
        """Test Python figure conversion with missing file."""
        mock_exists.return_value = False

        result = convert_python_figure("nonexistent.py")

        assert result is False
        mock_run.assert_not_called()

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_convert_python_figure_execution_error(self, mock_exists, mock_run):
        """Test Python figure conversion with execution error."""
        mock_exists.return_value = True
        mock_run.return_value = Mock(returncode=1, stderr="Python error")

        result = convert_python_figure("error_script.py")

        assert result is False

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_convert_python_figure_with_args(self, mock_exists, mock_run):
        """Test Python figure conversion with additional arguments."""
        mock_exists.return_value = True
        mock_run.return_value = Mock(returncode=0)

        result = convert_python_figure("script.py", ["--output", "test.png", "--dpi", "300"])

        assert result is True

        # Check that arguments were passed
        args = mock_run.call_args[0][0]
        assert "--output" in args
        assert "test.png" in args
        assert "--dpi" in args
        assert "300" in args


@pytest.mark.skip(reason="R figure generation functionality deprecated with RXIV_ENGINE removal")
class TestRFigureConversion:
    """Test R figure conversion functionality."""

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_convert_r_figure_basic(self, mock_exists, mock_run):
        """Test basic R figure conversion."""
        mock_exists.return_value = True
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        result = convert_r_figure("FIGURES/test_plot.R")

        assert result is True

        # Should have executed R script
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "Rscript" in args[0] or "r" in args[0].lower()

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_convert_r_figure_missing_file(self, mock_exists, mock_run):
        """Test R figure conversion with missing file."""
        mock_exists.return_value = False

        result = convert_r_figure("nonexistent.R")

        assert result is False
        mock_run.assert_not_called()

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_convert_r_figure_no_r_installed(self, mock_exists, mock_run):
        """Test R figure conversion when R is not installed."""
        mock_exists.return_value = True
        mock_run.side_effect = FileNotFoundError("Rscript not found")

        result = convert_r_figure("script.R")

        assert result is False


@pytest.mark.skip(reason="Bulk figure generation functionality deprecated with RXIV_ENGINE removal")
class TestBulkFigureConversion:
    """Test bulk figure conversion functionality."""

    @patch("pathlib.Path.glob")
    @patch("rxiv_maker.manuscript_utils.figure_utils.convert_python_figure")
    @patch("rxiv_maker.manuscript_utils.figure_utils.convert_r_figure")
    @patch("rxiv_maker.manuscript_utils.figure_utils.convert_mermaid")
    def test_convert_figures_bulk_all_types(self, mock_mermaid, mock_r, mock_python, mock_glob):
        """Test bulk conversion of all figure types."""
        # Mock file discovery
        mock_glob.side_effect = [
            [Path("FIGURES/plot1.py"), Path("FIGURES/plot2.py")],  # Python files
            [Path("FIGURES/chart1.R"), Path("FIGURES/chart2.R")],  # R files
            [Path("FIGURES/diagram1.mmd"), Path("FIGURES/diagram2.mmd")],  # Mermaid files
        ]

        # Mock conversion functions
        mock_python.return_value = True
        mock_r.return_value = True
        mock_mermaid.return_value = "output.svg"

        results = convert_figures_bulk()

        # Should have found and converted all files
        assert len(results["python"]) == 2
        assert len(results["r"]) == 2
        assert len(results["mermaid"]) == 2

        # Should have called conversion functions
        assert mock_python.call_count == 2
        assert mock_r.call_count == 2
        assert mock_mermaid.call_count == 2

    @patch("pathlib.Path.glob")
    def test_convert_figures_bulk_no_figures(self, mock_glob):
        """Test bulk conversion with no figures found."""
        # Mock no files found
        mock_glob.return_value = []

        results = convert_figures_bulk()

        # Should return empty results
        assert results["python"] == []
        assert results["r"] == []
        assert results["mermaid"] == []

    @patch("pathlib.Path.glob")
    @patch("rxiv_maker.manuscript_utils.figure_utils.convert_python_figure")
    def test_convert_figures_bulk_with_errors(self, mock_python, mock_glob):
        """Test bulk conversion with some failures."""
        mock_glob.side_effect = [
            [Path("FIGURES/good.py"), Path("FIGURES/bad.py")],  # Python files
            [],  # No R files
            [],  # No Mermaid files
        ]

        # Mock one success, one failure
        mock_python.side_effect = [True, False]

        results = convert_figures_bulk()

        # Should record both attempts
        assert len(results["python"]) == 2
        assert results["python"][0]["success"] is True
        assert results["python"][1]["success"] is False

    @patch("pathlib.Path.glob")
    @patch("rxiv_maker.manuscript_utils.figure_utils.convert_python_figure")
    def test_convert_figures_bulk_specific_directory(self, mock_python, mock_glob):
        """Test bulk conversion in specific directory."""
        mock_glob.return_value = [Path("custom/dir/plot.py")]
        mock_python.return_value = True

        convert_figures_bulk(figures_dir="custom/dir")

        # Should search in custom directory
        mock_glob.assert_called()
        call_patterns = [call[0][0] for call in mock_glob.call_args_list]
        assert any("custom/dir" in str(pattern) for pattern in call_patterns)


@pytest.mark.skip(reason="Figure utility functions deprecated with RXIV_ENGINE removal")
class TestFigureUtilityFunctions:
    """Test figure utility and helper functions."""

    @pytest.mark.skip(reason="Figure listing functionality deprecated with RXIV_ENGINE removal")
    @patch("pathlib.Path.glob")
    def test_list_available_figures(self, mock_glob):
        """Test listing available figure files."""
        # Mock discovered files
        mock_glob.side_effect = [
            [Path("FIGURES/analysis.py"), Path("FIGURES/plot.py")],
            [Path("FIGURES/chart.R")],
            [Path("FIGURES/diagram.mmd")],
        ]

        figures = list_available_figures()

        assert "python" in figures
        assert "r" in figures
        assert "mermaid" in figures
        assert len(figures["python"]) == 2
        assert len(figures["r"]) == 1
        assert len(figures["mermaid"]) == 1

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    @patch("pathlib.Path.read_text")
    def test_get_figure_info(self, mock_read, mock_stat, mock_exists):
        """Test getting figure file information."""
        mock_exists.return_value = True
        mock_stat.return_value = Mock(st_size=1024, st_mtime=1640000000)
        mock_read.return_value = "import matplotlib.pyplot as plt\n# Simple plot"

        info = get_figure_info("FIGURES/test.py")

        assert info["exists"] is True
        assert info["size"] == 1024
        assert info["type"] == "python"
        assert "matplotlib" in info["content"]

    @patch("pathlib.Path.exists")
    def test_get_figure_info_missing_file(self, mock_exists):
        """Test getting info for missing figure file."""
        mock_exists.return_value = False

        info = get_figure_info("nonexistent.py")

        assert info["exists"] is False
        assert info["size"] is None

    def test_get_figure_info_type_detection(self):
        """Test figure type detection from file extension."""
        assert get_figure_info("test.py")["type"] == "python"
        assert get_figure_info("test.R")["type"] == "r"
        assert get_figure_info("test.mmd")["type"] == "mermaid"
        assert get_figure_info("test.txt")["type"] == "unknown"

    @patch("pathlib.Path.glob")
    @patch("pathlib.Path.unlink")
    @patch("pathlib.Path.exists")
    def test_clean_figure_outputs(self, mock_exists, mock_unlink, mock_glob):
        """Test cleaning figure output files."""
        # Mock output files
        mock_glob.return_value = [
            Path("FIGURES/Figure__test1/output1.png"),
            Path("FIGURES/Figure__test2/output2.svg"),
        ]
        mock_exists.return_value = True

        result = clean_figure_outputs()

        # Should have attempted to remove files
        assert mock_unlink.call_count == 2
        assert len(result["removed"]) == 2

    @patch("pathlib.Path.glob")
    def test_clean_figure_outputs_no_files(self, mock_glob):
        """Test cleaning when no output files exist."""
        mock_glob.return_value = []

        result = clean_figure_outputs()

        assert result["removed"] == []
        assert result["errors"] == []

    @patch("pathlib.Path.glob")
    @patch("pathlib.Path.unlink")
    def test_clean_figure_outputs_with_errors(self, mock_unlink, mock_glob):
        """Test cleaning with some files failing to delete."""
        mock_glob.return_value = [Path("FIGURES/protected.png")]
        mock_unlink.side_effect = PermissionError("Cannot delete")

        result = clean_figure_outputs()

        # Should record the error
        assert len(result["errors"]) == 1
        assert "protected.png" in str(result["errors"][0])


@pytest.mark.skip(reason="Figure utils integration tests deprecated with RXIV_ENGINE removal")
class TestFigureUtilsIntegration:
    """Test integration of figure utilities with Python execution."""

    @patch("rxiv_maker.manuscript_utils.figure_utils.convert_python_figure")
    def test_figure_utils_in_python_context(self, mock_convert):
        """Test that figure utilities are available in Python execution context."""
        from rxiv_maker.converters.python_executor import PythonExecutor

        mock_convert.return_value = True
        executor = PythonExecutor()

        # Test that figure utilities are available
        code = """
# Test that figure utility functions are available
available_funcs = []
if 'convert_python_figure' in globals():
    available_funcs.append('convert_python_figure')
if 'convert_r_figure' in globals():
    available_funcs.append('convert_r_figure')
if 'convert_mermaid' in globals():
    available_funcs.append('convert_mermaid')
if 'list_available_figures' in globals():
    available_funcs.append('list_available_figures')

result = convert_python_figure("test.py")
"""

        output, success = executor.execute_code_safely(code)

        assert success is True

        # Check that functions were available
        assert "convert_python_figure" in executor.execution_context.get("available_funcs", [])
        assert executor.execution_context.get("result") is True

    def test_figure_utils_with_custom_command_processor(self):
        """Test figure utilities integration with custom command processor."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        with patch("rxiv_maker.manuscript_utils.figure_utils.list_available_figures") as mock_list:
            mock_list.return_value = {
                "python": ["plot1.py", "plot2.py"],
                "r": ["chart1.R"],
                "mermaid": ["diagram1.mmd"],
            }

            markdown_text = """
{{py:exec
available = list_available_figures()
python_count = len(available["python"])
total_count = sum(len(files) for files in available.values())
}}

We have {{py:get total_count}} figures available:
- Python: {{py:get python_count}}
"""

            result = process_custom_commands(markdown_text)

            assert "We have 4 figures available:" in result
            assert "Python: 2" in result

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.write_text")
    @patch("subprocess.run")
    def test_mermaid_integration_with_execution(self, mock_run, mock_write, mock_mkdir):
        """Test Mermaid integration with Python execution."""
        from rxiv_maker.converters.custom_command_processor import process_custom_commands

        mock_run.return_value = Mock(returncode=0)

        markdown_text = """
{{py:exec
mermaid_code = '''
graph TD
    A[Data] --> B[Process]
    B --> C[Results]
'''

diagram_path = convert_mermaid(mermaid_code, "workflow")
}}

Generated diagram at: {{py:get diagram_path}}
"""

        result = process_custom_commands(markdown_text)

        assert "Generated diagram at:" in result
        assert "FIGURES/Figure__workflow" in result


@pytest.mark.skip(reason="Figure utils edge case tests deprecated with RXIV_ENGINE removal")
class TestFigureUtilsEdgeCases:
    """Test edge cases and error conditions."""

    def test_invalid_file_extensions(self):
        """Test handling of invalid file extensions."""
        info = get_figure_info("test.xyz")
        assert info["type"] == "unknown"

    @patch("pathlib.Path.exists")
    def test_convert_functions_with_none_input(self, mock_exists):
        """Test conversion functions with None input."""
        mock_exists.return_value = False

        # Should handle None gracefully
        assert convert_python_figure(None) is False
        assert convert_r_figure(None) is False

    @patch("subprocess.run")
    def test_subprocess_timeout_handling(self, mock_run):
        """Test handling of subprocess timeouts."""
        from subprocess import TimeoutExpired

        mock_run.side_effect = TimeoutExpired("python", timeout=30)

        result = convert_python_figure("long_script.py")
        assert result is False

    @patch("pathlib.Path.glob")
    def test_bulk_conversion_empty_directory(self, mock_glob):
        """Test bulk conversion in empty directory."""
        mock_glob.return_value = []

        results = convert_figures_bulk("empty_dir")

        assert all(len(files) == 0 for files in results.values())

    def test_figure_path_normalization(self):
        """Test that figure paths are normalized correctly."""
        # Test various path formats
        paths = [
            "FIGURES/test.py",
            "./FIGURES/test.py",
            "FIGURES\\test.py",  # Windows-style path
        ]

        for path in paths:
            info = get_figure_info(path)
            # Should not crash and should normalize path
            assert isinstance(info, dict)
            assert "type" in info
