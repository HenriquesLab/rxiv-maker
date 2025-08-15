"""Unit tests for citation utilities module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from rxiv_maker.utils.citation_utils import inject_rxiv_citation


class TestInjectRxivCitation:
    """Test Rxiv-Maker citation injection functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = Path(self.temp_dir) / "MANUSCRIPT"
        self.manuscript_dir.mkdir(parents=True, exist_ok=True)
        self.bib_file = self.manuscript_dir / "03_REFERENCES.bib"

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_inject_citation_when_acknowledge_false(self):
        """Test that citation is not injected when acknowledge_rxiv_maker is False."""
        yaml_metadata = {"acknowledge_rxiv_maker": False}

        with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
            with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                inject_rxiv_citation(yaml_metadata)

        # Bibliography file should not be created
        assert not self.bib_file.exists()

    def test_inject_citation_when_acknowledge_missing(self):
        """Test that citation is not injected when acknowledge_rxiv_maker key is missing."""
        yaml_metadata = {}

        with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
            with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                inject_rxiv_citation(yaml_metadata)

        # Bibliography file should not be created
        assert not self.bib_file.exists()

    def test_inject_citation_creates_new_bib_file(self):
        """Test that citation injection creates a new bibliography file if it doesn't exist."""
        yaml_metadata = {"acknowledge_rxiv_maker": True}

        with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
            with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                inject_rxiv_citation(yaml_metadata)

        # Bibliography file should be created
        assert self.bib_file.exists()

        # Check content contains the citation
        content = self.bib_file.read_text(encoding="utf-8")
        assert "saraiva_2025_rxivmaker" in content
        assert "Rxiv-Maker: an automated template engine" in content
        assert "Bruno M. Saraiva and Guillaume Jaquemet and Ricardo Henriques" in content
        assert "2025" in content
        assert "arxiv.org/abs/2508.00836" in content

    def test_inject_citation_appends_to_existing_bib_file(self):
        """Test that citation is appended to existing bibliography file."""
        # Create existing bibliography content
        existing_content = """@article{example2024,
    title={Example Article},
    author={Jane Doe},
    journal={Example Journal},
    year={2024}
}
"""
        self.bib_file.write_text(existing_content, encoding="utf-8")

        yaml_metadata = {"acknowledge_rxiv_maker": True}

        with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
            with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                inject_rxiv_citation(yaml_metadata)

        # Check content contains both existing and new citations
        content = self.bib_file.read_text(encoding="utf-8")
        assert "example2024" in content
        assert "Jane Doe" in content
        assert "saraiva_2025_rxivmaker" in content
        assert "Bruno M. Saraiva" in content

    def test_inject_citation_skips_if_already_exists(self, capsys):
        """Test that citation injection is skipped if citation already exists."""
        # Create bibliography with existing rxiv-maker citation
        existing_content = """@misc{saraiva_2025_rxivmaker,
      title={Existing Rxiv-Maker Citation},
      author={Bruno M. Saraiva},
      year={2025}
}
"""
        self.bib_file.write_text(existing_content, encoding="utf-8")

        yaml_metadata = {"acknowledge_rxiv_maker": True}

        with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
            with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                inject_rxiv_citation(yaml_metadata)

        # Check that warning message was printed
        captured = capsys.readouterr()
        assert "Rxiv-Maker citation already exists in bibliography" in captured.out

        # Content should remain unchanged
        content = self.bib_file.read_text(encoding="utf-8")
        assert content == existing_content

    def test_inject_citation_with_custom_bibliography_filename(self):
        """Test citation injection with custom bibliography filename."""
        custom_bib_file = self.manuscript_dir / "custom_refs.bib"
        yaml_metadata = {
            "acknowledge_rxiv_maker": True,
            "bibliography": "custom_refs",  # Without .bib extension
        }

        with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
            with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                inject_rxiv_citation(yaml_metadata)

        # Custom bibliography file should be created
        assert custom_bib_file.exists()

        # Check content contains the citation
        content = custom_bib_file.read_text(encoding="utf-8")
        assert "saraiva_2025_rxivmaker" in content

    def test_inject_citation_with_bib_extension_in_filename(self):
        """Test citation injection when bibliography filename already has .bib extension."""
        custom_bib_file = self.manuscript_dir / "custom_refs.bib"
        yaml_metadata = {
            "acknowledge_rxiv_maker": True,
            "bibliography": "custom_refs.bib",  # With .bib extension
        }

        with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
            with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                inject_rxiv_citation(yaml_metadata)

        # Custom bibliography file should be created
        assert custom_bib_file.exists()

        # Check content contains the citation
        content = custom_bib_file.read_text(encoding="utf-8")
        assert "saraiva_2025_rxivmaker" in content

    def test_inject_citation_adds_newline_to_file_without_trailing_newline(self):
        """Test that citation injection adds newline when existing file doesn't end with one."""
        # Create existing bibliography content without trailing newline
        existing_content = """@article{example2024,
    title={Example Article},
    author={Jane Doe},
    year={2024}
}"""  # No trailing newline
        self.bib_file.write_text(existing_content, encoding="utf-8")

        yaml_metadata = {"acknowledge_rxiv_maker": True}

        with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
            with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                inject_rxiv_citation(yaml_metadata)

        # Check content has proper newline separation
        content = self.bib_file.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Should have newline between existing and new citation
        assert "}" in lines  # End of existing citation
        assert any("@misc{saraiva_2025_rxivmaker" in line for line in lines)

        # No double newlines at the junction
        assert "\n\n\n" not in content

    def test_inject_citation_uses_default_manuscript_path(self):
        """Test citation injection uses default MANUSCRIPT path when env var not set."""
        # Create MANUSCRIPT directory in temp_dir
        default_manuscript_dir = Path(self.temp_dir) / "MANUSCRIPT"
        default_manuscript_dir.mkdir(parents=True, exist_ok=True)
        default_bib_file = default_manuscript_dir / "03_REFERENCES.bib"

        yaml_metadata = {"acknowledge_rxiv_maker": True}

        # Don't set MANUSCRIPT_PATH environment variable - explicitly clear it
        with patch.dict(os.environ, {}, clear=False):
            with patch("os.getenv") as mock_getenv:

                def getenv_side_effect(key, default=None):
                    if key == "MANUSCRIPT_PATH":
                        return default
                    return os.environ.get(key, default)

                mock_getenv.side_effect = getenv_side_effect

                with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                    inject_rxiv_citation(yaml_metadata)

        # Default bibliography file should be created
        assert default_bib_file.exists()

        # Check content contains the citation
        content = default_bib_file.read_text(encoding="utf-8")
        assert "saraiva_2025_rxivmaker" in content

    def test_inject_citation_handles_read_error(self, capsys):
        """Test citation injection handles file read errors gracefully."""
        yaml_metadata = {"acknowledge_rxiv_maker": True}

        with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
            with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                with patch("builtins.open", side_effect=IOError("Read error")):
                    inject_rxiv_citation(yaml_metadata)

        # Check that error message was printed
        captured = capsys.readouterr()
        assert "Error reading bibliography file" in captured.out

    def test_inject_citation_handles_write_error(self, capsys):
        """Test citation injection handles file write errors gracefully."""
        # Create existing bibliography file
        self.bib_file.write_text("", encoding="utf-8")

        yaml_metadata = {"acknowledge_rxiv_maker": True}

        with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
            with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                # Mock open to succeed for read but fail for write
                original_open = open

                def mock_open(*args, **kwargs):
                    if "a" in args or kwargs.get("mode") == "a":
                        raise IOError("Write error")
                    return original_open(*args, **kwargs)

                with patch("builtins.open", side_effect=mock_open):
                    inject_rxiv_citation(yaml_metadata)

        # Check that error message was printed
        captured = capsys.readouterr()
        assert "Error writing to bibliography file" in captured.out

    def test_citation_content_validation(self):
        """Test that the injected citation has all required BibTeX fields."""
        yaml_metadata = {"acknowledge_rxiv_maker": True}

        with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
            with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                inject_rxiv_citation(yaml_metadata)

        content = self.bib_file.read_text(encoding="utf-8")

        # Validate required BibTeX fields
        assert "@misc{saraiva_2025_rxivmaker," in content
        assert "title={Rxiv-Maker: an automated template engine for streamlined scientific publications}" in content
        assert "author={Bruno M. Saraiva and Guillaume Jaquemet and Ricardo Henriques}" in content
        assert "year={2025}" in content
        assert "eprint={2508.00836}" in content
        assert "archivePrefix={arXiv}" in content
        assert "primaryClass={cs.DL}" in content
        assert "url={https://arxiv.org/abs/2508.00836}" in content
        assert "}" in content  # Closing brace

    def test_inject_citation_success_message(self, capsys):
        """Test that success message is printed when citation is injected."""
        yaml_metadata = {"acknowledge_rxiv_maker": True}

        with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(self.manuscript_dir)}):
            with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
                inject_rxiv_citation(yaml_metadata)

        # Check that success message was printed
        captured = capsys.readouterr()
        assert "✅ Rxiv-Maker citation injected into" in captured.out
        assert str(self.bib_file) in captured.out
