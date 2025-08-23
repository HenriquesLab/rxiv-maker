"""Tests for generate_docs.py module."""

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rxiv_maker.engines.operations import generate_docs


class TestGenerateDocs:
    """Test suite for generate_docs module functions."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.docs_dir = Path(self.temp_dir) / "docs"
        self.module_path = Path(self.temp_dir) / "test_module.py"

    def teardown_method(self):
        """Clean up after each test method."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("shutil.which")
    @patch("builtins.print")
    def test_generate_module_docs_no_lazydocs(self, mock_print, mock_which):
        """Test generate_module_docs when lazydocs is not available."""
        mock_which.return_value = None

        result = generate_docs.generate_module_docs(self.docs_dir, self.module_path)

        assert result is None
        mock_print.assert_called_once()
        assert "lazydocs not found" in mock_print.call_args[0][0]

    @patch("shutil.which")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_generate_module_docs_success(self, mock_print, mock_subprocess, mock_which):
        """Test successful module documentation generation."""
        mock_which.return_value = "/usr/local/bin/lazydocs"
        mock_subprocess.return_value.returncode = 0

        result = generate_docs.generate_module_docs(self.docs_dir, self.module_path)

        assert result is True
        mock_subprocess.assert_called_once()

    @patch("shutil.which")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_generate_module_docs_failure(self, mock_print, mock_subprocess, mock_which):
        """Test module documentation generation failure."""
        mock_which.return_value = "/usr/local/bin/lazydocs"
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "lazydocs")

        result = generate_docs.generate_module_docs(self.docs_dir, self.module_path)

        assert result is False
        mock_print.assert_called()
