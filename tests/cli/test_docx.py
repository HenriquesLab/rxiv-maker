"""Test DOCX command options."""

import importlib
from unittest.mock import patch

from click.testing import CliRunner

from rxiv_maker.cli.commands.docx import docx

# NOTE: ``rxiv_maker.cli.commands`` re-exports the ``docx`` command (see its
# ``__init__``), which shadows the ``docx`` submodule on the package, so neither
# a dotted patch target ("rxiv_maker.cli.commands.docx.<fn>") nor ``import ... as``
# resolves to the module reliably across Python versions. Fetch the real module
# object explicitly so ``patch.object`` binds the helper functions.
docx_module = importlib.import_module("rxiv_maker.cli.commands.docx")


class TestDocxCommand:
    """Test DOCX command functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_docx_help_shows_split_options(self):
        """Test DOCX command help includes split options."""
        result = self.runner.invoke(docx, ["--help"])

        assert result.exit_code == 0
        assert "--split-si" in result.output
        assert "--split-si-pdf" in result.output

    def test_split_options_are_mutually_exclusive(self, tmp_path):
        """Test split-si and split-si-pdf cannot be combined."""
        manuscript_dir = tmp_path / "MANUSCRIPT"
        manuscript_dir.mkdir()

        result = self.runner.invoke(docx, [str(manuscript_dir), "--split-si", "--split-si-pdf"])

        assert result.exit_code != 0
        assert "cannot be used together" in result.output

    def test_split_si_exports_main_and_si_docx(self, tmp_path):
        """Test split-si exports main and SI DOCX artifacts."""
        manuscript_dir = tmp_path / "MANUSCRIPT"
        manuscript_dir.mkdir()
        main_path = manuscript_dir / "paper__main.docx"
        si_path = manuscript_dir / "paper__si.docx"

        with (
            patch.object(docx_module, "_check_and_offer_poppler_installation"),
            patch.object(
                docx_module,
                "_export_docx_file",
                side_effect=[main_path, si_path],
            ) as mock_export,
        ):
            result = self.runner.invoke(docx, [str(manuscript_dir), "--split-si"])

        assert result.exit_code == 0
        assert mock_export.call_count == 2
        assert mock_export.call_args_list[0].kwargs["content_mode"] == "main"
        assert mock_export.call_args_list[0].kwargs["output_suffix"] == "__main"
        assert mock_export.call_args_list[1].kwargs["content_mode"] == "si"
        assert mock_export.call_args_list[1].kwargs["output_suffix"] == "__si"

    def test_split_si_pdf_exports_main_docx_and_si_pdf(self, tmp_path):
        """Test split-si-pdf exports main DOCX and SI PDF artifacts."""
        manuscript_dir = tmp_path / "MANUSCRIPT"
        manuscript_dir.mkdir()
        main_path = manuscript_dir / "paper__main.docx"
        si_path = manuscript_dir / "paper__si.pdf"

        with (
            patch.object(docx_module, "_check_and_offer_poppler_installation"),
            patch.object(docx_module, "_export_docx_file", return_value=main_path) as mock_export,
            patch.object(docx_module, "_build_and_export_si_pdf", return_value=si_path) as mock_pdf,
        ):
            result = self.runner.invoke(docx, [str(manuscript_dir), "--split-si-pdf"])

        assert result.exit_code == 0
        mock_export.assert_called_once()
        assert mock_export.call_args.kwargs["content_mode"] == "main"
        assert mock_export.call_args.kwargs["output_suffix"] == "__main"
        mock_pdf.assert_called_once_with(str(manuscript_dir), False, False)
