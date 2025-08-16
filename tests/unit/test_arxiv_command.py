"""Tests for the arXiv command functionality."""

import os
import sys
from unittest.mock import MagicMock, mock_open, patch

from click.testing import CliRunner

from rxiv_maker.cli.commands.arxiv import arxiv


class TestArxivCommand:
    """Test the arXiv command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("rxiv_maker.cli.commands.arxiv.PathManager")
    def test_nonexistent_manuscript_directory(self, mock_path_manager):
        """Test handling of nonexistent manuscript directory."""
        # Mock PathManager to raise PathResolutionError
        from rxiv_maker.core.path_manager import PathResolutionError

        mock_path_manager.side_effect = PathResolutionError(
            "Manuscript directory not found: nonexistent. Ensure the directory exists or set MANUSCRIPT_PATH environment variable."
        )

        result = self.runner.invoke(arxiv, ["nonexistent"])

        assert result.exit_code == 1
        # Updated to match new PathManager error message format
        assert "❌ Path resolution error:" in result.output
        assert "💡 Run 'rxiv init nonexistent' to create a new manuscript" in result.output

    @patch("rxiv_maker.cli.commands.arxiv.prepare_arxiv_main")
    @patch("rxiv_maker.cli.commands.arxiv.Progress")
    @patch("rxiv_maker.cli.commands.arxiv.BuildManager")
    @patch("rxiv_maker.cli.commands.arxiv.PathManager")
    def test_pdf_building_when_missing(self, mock_path_manager, mock_build_manager, mock_progress, mock_prepare_arxiv):
        """Test PDF building when PDF doesn't exist."""

        # Mock PathManager to succeed
        from pathlib import Path

        mock_path_manager_instance = MagicMock()
        mock_path_manager_instance.output_dir = Path("output")  # Return Path object, not string
        mock_path_manager.return_value = mock_path_manager_instance

        # Mock BuildManager successful run
        mock_manager_instance = MagicMock()
        mock_manager_instance.run.return_value = True
        mock_build_manager.return_value = mock_manager_instance

        # Mock Progress context manager
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress_instance)
        mock_progress.return_value.__exit__ = MagicMock(return_value=None)

        # Mock prepare_arxiv_main to avoid actual execution
        mock_prepare_arxiv.return_value = None

        result = self.runner.invoke(arxiv, ["test_manuscript", "--no-zip"], obj={"verbose": False})

        assert result.exit_code == 0
        mock_build_manager.assert_called_once()
        mock_manager_instance.run.assert_called_once()

    @patch("rxiv_maker.cli.commands.arxiv.Progress")
    @patch("rxiv_maker.cli.commands.arxiv.BuildManager")
    @patch("rxiv_maker.cli.commands.arxiv.PathManager")
    def test_build_manager_failure(self, mock_path_manager, mock_build_manager, mock_progress):
        """Test handling of BuildManager failure."""

        # Mock PathManager to succeed
        from pathlib import Path

        mock_path_manager_instance = MagicMock()
        mock_path_manager_instance.output_dir = Path("output")  # Return Path object, not string
        mock_path_manager.return_value = mock_path_manager_instance

        # Mock BuildManager failure
        mock_manager_instance = MagicMock()
        mock_manager_instance.run.return_value = False
        mock_build_manager.return_value = mock_manager_instance

        # Mock Progress context manager
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress_instance)
        mock_progress.return_value.__exit__ = MagicMock(return_value=None)

        result = self.runner.invoke(arxiv, ["test_manuscript"], obj={"verbose": False})

        assert result.exit_code == 1
        assert "❌ PDF build failed. Cannot prepare arXiv package." in result.output

    @patch("rxiv_maker.cli.commands.arxiv.prepare_arxiv_main")
    @patch("rxiv_maker.cli.commands.arxiv.Progress")
    @patch("rxiv_maker.cli.commands.arxiv.PathManager")
    @patch("rxiv_maker.cli.commands.arxiv.BuildManager")
    def test_custom_options(self, mock_build_manager, mock_path_manager, mock_progress, mock_prepare):
        """Test arXiv command with custom options."""

        # Create a mock PathManager instance that won't raise PathResolutionError
        from pathlib import Path

        mock_path_manager_instance = MagicMock()
        mock_path_manager_instance.output_dir = Path("custom_output")
        mock_path_manager_instance.manuscript_path = Path("test_manuscript")
        mock_path_manager_instance.data_path = Path("test_data")
        mock_path_manager_instance.manuscript_name = "test_manuscript"

        # The key is to ensure PathManager constructor doesn't raise an exception
        mock_path_manager.return_value = mock_path_manager_instance

        # Mock BuildManager
        mock_build_manager_instance = MagicMock()
        mock_build_manager_instance.run.return_value = True
        mock_build_manager.return_value = mock_build_manager_instance

        # Mock Progress context manager
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress_instance)
        mock_progress.return_value.__exit__ = MagicMock(return_value=None)

        # Mock sys.argv manipulation
        original_argv = sys.argv.copy()

        # Mock prepare_arxiv_main to raise SystemExit(0) to trigger successful completion
        mock_prepare.side_effect = SystemExit(0)

        # Mock PDF file existence
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True  # Pretend PDF exists

            with patch("yaml.safe_load") as mock_yaml, patch("builtins.open", mock_open()):
                # Mock YAML config
                mock_yaml.return_value = {"date": "2024-01-01", "authors": [{"name": "Test Author"}]}

                result = self.runner.invoke(
                    arxiv,
                    [
                        "test_manuscript",
                        "--output-dir",
                        "custom_output",
                        "--arxiv-dir",
                        "custom_arxiv",
                        "--zip-filename",
                        "custom.zip",
                    ],
                    obj={"verbose": False},  # Provide proper context object
                )

            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")

            # Remove debug output
            assert result.exit_code == 0
            mock_prepare.assert_called_once()

            # Verify sys.argv was restored
            assert sys.argv == original_argv

    @patch("rxiv_maker.cli.commands.arxiv.PathManager")
    def test_environment_variable_manuscript_path(self, mock_path_manager):
        """Test using MANUSCRIPT_PATH environment variable."""
        with patch.dict(os.environ, {"MANUSCRIPT_PATH": "env_manuscript"}):
            # Mock PathManager to raise PathResolutionError
            from rxiv_maker.core.path_manager import PathResolutionError

            mock_path_manager.side_effect = PathResolutionError(
                "Manuscript directory not found: env_manuscript. Ensure the directory exists or set MANUSCRIPT_PATH environment variable."
            )

            result = self.runner.invoke(arxiv, [])

            assert result.exit_code == 1
            assert "env_manuscript" in result.output

    @patch("rxiv_maker.cli.commands.arxiv.prepare_arxiv_main")
    @patch("rxiv_maker.cli.commands.arxiv.Progress")
    @patch("rxiv_maker.cli.commands.arxiv.PathManager")
    def test_no_zip_option(self, mock_path_manager, mock_progress, mock_prepare):
        """Test --no-zip option."""
        # Mock PathManager to succeed
        from pathlib import Path

        mock_path_manager_instance = MagicMock()
        mock_path_manager_instance.manuscript_path = Path("test_manuscript")
        mock_path_manager_instance.manuscript_name = "test_manuscript"

        # Create a real Path for output_dir to avoid mocking issues
        mock_path_manager_instance.output_dir = Path("output")

        mock_path_manager.return_value = mock_path_manager_instance

        # Mock Progress context manager
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress_instance)
        mock_progress.return_value.__exit__ = MagicMock(return_value=None)

        # Mock prepare_arxiv_main to avoid actual execution
        mock_prepare.return_value = None

        # Patch Path.exists to return True for the PDF path to skip BuildManager
        with patch.object(Path, "exists", return_value=True):
            result = self.runner.invoke(arxiv, ["test_manuscript", "--no-zip"], obj={"verbose": False})

        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        print(f"Exception: {result.exception}")

        assert result.exit_code == 0
        mock_prepare.assert_called_once()

    @patch("rxiv_maker.cli.commands.arxiv.Progress")
    @patch("rxiv_maker.cli.commands.arxiv.prepare_arxiv_main")
    @patch("rxiv_maker.cli.commands.arxiv.PathManager")
    def test_pdf_copying_to_manuscript(self, mock_path_manager, mock_prepare, mock_progress):
        """Test copying PDF to manuscript directory with proper naming."""
        from pathlib import Path

        # Mock PathManager instance
        mock_path_manager_instance = MagicMock()
        mock_path_manager_instance.manuscript_path = Path("test_manuscript")
        mock_path_manager_instance.manuscript_name = "test_manuscript"

        # Mock output_dir and PDF exists check
        mock_output_dir = MagicMock()
        mock_pdf_path = MagicMock()
        mock_pdf_path.exists.return_value = True
        mock_pdf_path.name = "test_manuscript.pdf"
        mock_output_dir.__truediv__.return_value = mock_pdf_path
        mock_path_manager_instance.output_dir = mock_output_dir

        mock_path_manager.return_value = mock_path_manager_instance

        # Mock Progress context manager
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress_instance)
        mock_progress.return_value.__exit__ = MagicMock(return_value=None)

        # Mock prepare_arxiv_main to complete successfully without raising SystemExit
        mock_prepare.return_value = None

        with (
            patch("yaml.safe_load") as mock_yaml,
            patch("builtins.open", mock_open()),
            patch("shutil.copy2") as mock_copy,
        ):
            # Mock YAML config
            mock_yaml.return_value = {
                "date": "2024-01-15",
                "authors": [{"name": "John Doe"}],
            }

            result = self.runner.invoke(arxiv, ["test_manuscript"], obj={"verbose": False})

        assert result.exit_code == 0
        mock_copy.assert_called_once()

    @patch("rxiv_maker.cli.commands.arxiv.Progress")
    @patch("rxiv_maker.cli.commands.arxiv.prepare_arxiv_main")
    @patch("rxiv_maker.cli.commands.arxiv.PathManager")
    def test_keyboard_interrupt(self, mock_path_manager, mock_prepare, mock_progress):
        """Test handling of KeyboardInterrupt."""
        from pathlib import Path

        # Mock PathManager instance
        mock_path_manager_instance = MagicMock()
        mock_path_manager_instance.manuscript_path = Path("test_manuscript")
        mock_path_manager_instance.manuscript_name = "test_manuscript"

        # Mock output_dir and PDF exists check
        mock_output_dir = MagicMock()
        mock_pdf_path = MagicMock()
        mock_pdf_path.exists.return_value = True
        mock_pdf_path.name = "test_manuscript.pdf"
        mock_output_dir.__truediv__.return_value = mock_pdf_path
        mock_path_manager_instance.output_dir = mock_output_dir

        mock_path_manager.return_value = mock_path_manager_instance

        # Mock KeyboardInterrupt during prepare_arxiv_main
        mock_prepare.side_effect = KeyboardInterrupt()

        # Mock Progress context manager
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress_instance)
        mock_progress.return_value.__exit__ = MagicMock(return_value=None)

        result = self.runner.invoke(arxiv, ["test_manuscript"])

        assert result.exit_code == 1
        assert "⏹️  arXiv preparation interrupted by user" in result.output

    @patch("rxiv_maker.cli.commands.arxiv.Progress")
    @patch("rxiv_maker.cli.commands.arxiv.prepare_arxiv_main")
    @patch("rxiv_maker.cli.commands.arxiv.PathManager")
    def test_regression_build_manager_method_call(self, mock_path_manager, mock_prepare, mock_progress):
        """Regression test: Ensure BuildManager.run() is called, not build()."""
        from pathlib import Path

        # Mock PathManager instance
        mock_path_manager_instance = MagicMock()
        mock_path_manager_instance.manuscript_path = Path("test_manuscript")
        mock_path_manager_instance.manuscript_name = "test_manuscript"

        # Mock output_dir and PDF doesn't exist - this will trigger BuildManager call
        mock_output_dir = MagicMock()
        mock_pdf_path = MagicMock()
        mock_pdf_path.exists.return_value = False
        mock_pdf_path.name = "test_manuscript.pdf"
        mock_output_dir.__truediv__.return_value = mock_pdf_path
        mock_path_manager_instance.output_dir = mock_output_dir

        mock_path_manager.return_value = mock_path_manager_instance

        # Mock Progress context manager
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress_instance)
        mock_progress.return_value.__exit__ = MagicMock(return_value=None)

        with patch("rxiv_maker.cli.commands.arxiv.BuildManager") as mock_build_manager:
            mock_manager_instance = MagicMock()
            mock_manager_instance.run.return_value = True
            # Ensure 'build' method doesn't exist to catch regression
            del mock_manager_instance.build
            mock_build_manager.return_value = mock_manager_instance

            result = self.runner.invoke(arxiv, ["test_manuscript", "--no-zip"], obj={"verbose": False})

        assert result.exit_code == 0
        # Verify run() method was called, not build()
        mock_manager_instance.run.assert_called_once()

    @patch("rxiv_maker.cli.commands.arxiv.Progress")
    @patch("rxiv_maker.cli.commands.arxiv.prepare_arxiv_main")
    @patch("rxiv_maker.cli.commands.arxiv.PathManager")
    def test_create_zip_flag_regression(self, mock_path_manager, mock_prepare, mock_progress):
        """Regression test: Ensure --create-zip flag is used, not --zip."""
        from pathlib import Path

        # Mock PathManager instance
        mock_path_manager_instance = MagicMock()
        mock_path_manager_instance.manuscript_path = Path("test_manuscript")
        mock_path_manager_instance.manuscript_name = "test_manuscript"

        # Mock output_dir and PDF exists (so BuildManager won't be called)
        mock_output_dir = MagicMock()
        mock_pdf_path = MagicMock()
        mock_pdf_path.exists.return_value = True
        mock_pdf_path.name = "test_manuscript.pdf"
        mock_output_dir.__truediv__.return_value = mock_pdf_path
        mock_path_manager_instance.output_dir = mock_output_dir

        mock_path_manager.return_value = mock_path_manager_instance

        # Mock Progress context manager
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__ = MagicMock(return_value=mock_progress_instance)
        mock_progress.return_value.__exit__ = MagicMock(return_value=None)

        # Capture sys.argv to verify correct flag is used
        captured_argv = []

        def capture_argv(*args, **kwargs):
            captured_argv.extend(sys.argv)
            # Use SystemExit(0) to trigger successful completion
            raise SystemExit(0)

        mock_prepare.side_effect = capture_argv

        result = self.runner.invoke(arxiv, ["test_manuscript"], obj={"verbose": False})

        assert result.exit_code == 0
        # Verify --create-zip is in the arguments, not --zip
        assert "--create-zip" in captured_argv
        assert "--zip" not in captured_argv or captured_argv.count("--zip") <= captured_argv.count("--create-zip")
