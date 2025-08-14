"""Tests for the validate command functionality."""

import os
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from rxiv_maker.cli.commands.validate import validate


class TestValidateCommand:
    """Test the validate command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("rxiv_maker.cli.commands.validate.Path")
    def test_nonexistent_manuscript_directory(self, mock_path):
        """Test handling of nonexistent manuscript directory."""
        mock_path.return_value.exists.return_value = False

        result = self.runner.invoke(validate, ["nonexistent"])

        assert result.exit_code == 1
        assert "❌ Error: Manuscript directory 'nonexistent' does not exist" in result.output
        assert "💡 Run 'rxiv init nonexistent' to create a new manuscript" in result.output

    @patch("rxiv_maker.cli.commands.validate.Path")
    @patch("rxiv_maker.cli.commands.validate.Progress")
    @patch("rxiv_maker.engine.validate.main")
    def test_successful_validation(self, mock_validate_main, mock_progress, mock_path):
        """Test successful manuscript validation."""
        # Mock Path.exists() to return True for manuscript directory
        mock_path.return_value.exists.return_value = True

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_main to succeed (no exception)
        mock_validate_main.return_value = None

        result = self.runner.invoke(validate, ["test_manuscript"])

        assert result.exit_code == 0
        assert "✅ Validation passed!" in result.output
        mock_validate_main.assert_called_once()

    @patch("rxiv_maker.cli.commands.validate.Path")
    @patch("rxiv_maker.cli.commands.validate.Progress")
    @patch("rxiv_maker.engine.validate.main")
    def test_validation_failure(self, mock_validate_main, mock_progress, mock_path):
        """Test manuscript validation failure."""
        mock_path.return_value.exists.return_value = True

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_main to fail with SystemExit
        mock_validate_main.side_effect = SystemExit(1)

        result = self.runner.invoke(validate, ["test_manuscript"])

        assert result.exit_code == 1
        assert "❌ Validation failed. See details above." in result.output
        assert "💡 Run with --detailed for more information" in result.output
        assert "💡 Use 'rxiv pdf --skip-validation' to build anyway" in result.output

    @patch("rxiv_maker.cli.commands.validate.Path")
    @patch("rxiv_maker.cli.commands.validate.Progress")
    @patch("rxiv_maker.engine.validate.main")
    def test_validation_success_exit_zero(self, mock_validate_main, mock_progress, mock_path):
        """Test validation with SystemExit(0) - should be treated as success."""
        mock_path.return_value.exists.return_value = True

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_main to exit with code 0 (success)
        mock_validate_main.side_effect = SystemExit(0)

        result = self.runner.invoke(validate, ["test_manuscript"])

        # SystemExit(0) should not be treated as failure
        assert result.exit_code == 0

    @patch("rxiv_maker.cli.commands.validate.Path")
    @patch("rxiv_maker.cli.commands.validate.Progress")
    @patch("rxiv_maker.engine.validate.main")
    def test_keyboard_interrupt_handling(self, mock_validate_main, mock_progress, mock_path):
        """Test keyboard interrupt handling."""
        mock_path.return_value.exists.return_value = True

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_main to raise KeyboardInterrupt
        mock_validate_main.side_effect = KeyboardInterrupt()

        result = self.runner.invoke(validate, ["test_manuscript"])

        assert result.exit_code == 1
        assert "⏹️  Validation interrupted by user" in result.output

    @patch("rxiv_maker.cli.commands.validate.Path")
    @patch("rxiv_maker.cli.commands.validate.Progress")
    @patch("rxiv_maker.engine.validate.main")
    def test_unexpected_error_handling(self, mock_validate_main, mock_progress, mock_path):
        """Test unexpected error handling."""
        mock_path.return_value.exists.return_value = True

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_main to raise unexpected error
        mock_validate_main.side_effect = RuntimeError("Unexpected validation error")

        result = self.runner.invoke(validate, ["test_manuscript"])

        assert result.exit_code == 1
        assert "❌ Unexpected error during validation: Unexpected validation error" in result.output

    @patch("rxiv_maker.cli.commands.validate.Path")
    @patch("rxiv_maker.cli.commands.validate.Progress")
    @patch("rxiv_maker.engine.validate.main")
    def test_default_manuscript_path_from_env(self, mock_validate_main, mock_progress, mock_path):
        """Test using MANUSCRIPT_PATH environment variable."""
        mock_path.return_value.exists.return_value = True

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_main to succeed
        mock_validate_main.return_value = None

        # Test with environment variable
        with patch.dict(os.environ, {"MANUSCRIPT_PATH": "custom_manuscript"}):
            result = self.runner.invoke(validate, [])

        assert result.exit_code == 0
        mock_validate_main.assert_called_once()

    @patch("rxiv_maker.cli.commands.validate.Path")
    @patch("rxiv_maker.cli.commands.validate.Progress")
    @patch("rxiv_maker.engine.validate.main")
    @patch("rxiv_maker.cli.commands.validate.sys")
    def test_argv_manipulation(self, mock_sys, mock_validate_main, mock_progress, mock_path):
        """Test sys.argv manipulation for validate_main."""
        mock_path.return_value.exists.return_value = True

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_main to succeed
        mock_validate_main.return_value = None

        # Mock sys.argv
        original_argv = ["original", "command"]
        mock_sys.argv = original_argv

        result = self.runner.invoke(validate, ["test_manuscript", "--detailed", "--no-doi"], obj={"verbose": True})

        assert result.exit_code == 0

        # Verify argv was restored
        assert mock_sys.argv == original_argv

    @patch("rxiv_maker.cli.commands.validate.Path")
    @patch("rxiv_maker.cli.commands.validate.Progress")
    @patch("rxiv_maker.engine.validate.main")
    def test_validation_options(self, mock_validate_main, mock_progress, mock_path):
        """Test various validation options."""
        mock_path.return_value.exists.return_value = True

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_main to succeed
        mock_validate_main.return_value = None

        # Test with detailed flag
        result = self.runner.invoke(validate, ["test_manuscript", "--detailed"])
        assert result.exit_code == 0

        # Test with no-doi flag
        result = self.runner.invoke(validate, ["test_manuscript", "--no-doi"])
        assert result.exit_code == 0

        # Test with verbose context
        result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": True})
        assert result.exit_code == 0

    @patch("rxiv_maker.cli.commands.validate.Path")
    @patch("rxiv_maker.cli.commands.validate.Progress")
    @patch("rxiv_maker.engine.validate.main")
    def test_verbose_error_reporting(self, mock_validate_main, mock_progress, mock_path):
        """Test verbose error reporting."""
        mock_path.return_value.exists.return_value = True

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_main to raise unexpected error
        mock_validate_main.side_effect = RuntimeError("Detailed error")

        # Test with verbose context - should show exception details
        result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": True})

        assert result.exit_code == 1
        assert "❌ Unexpected error during validation: Detailed error" in result.output

    @patch("rxiv_maker.cli.commands.validate.Path")
    @patch("rxiv_maker.cli.commands.validate.Progress")
    @patch("rxiv_maker.engine.validate.main")
    def test_progress_update_on_success(self, mock_validate_main, mock_progress, mock_path):
        """Test progress update on successful validation."""
        mock_path.return_value.exists.return_value = True

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_task = MagicMock()
        mock_progress_instance.add_task.return_value = mock_task
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_main to succeed
        mock_validate_main.return_value = None

        result = self.runner.invoke(validate, ["test_manuscript"])

        assert result.exit_code == 0

        # Verify progress was updated with success message
        update_calls = mock_progress_instance.update.call_args_list
        success_update = any("✅ Validation completed" in str(call) for call in update_calls)
        assert success_update

    @patch("rxiv_maker.cli.commands.validate.Path")
    @patch("rxiv_maker.cli.commands.validate.Progress")
    @patch("rxiv_maker.engine.validate.main")
    def test_progress_update_on_failure(self, mock_validate_main, mock_progress, mock_path):
        """Test progress update on validation failure."""
        mock_path.return_value.exists.return_value = True

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_task = MagicMock()
        mock_progress_instance.add_task.return_value = mock_task
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_main to fail
        mock_validate_main.side_effect = SystemExit(1)

        result = self.runner.invoke(validate, ["test_manuscript"])

        assert result.exit_code == 1

        # Verify progress was updated with failure message
        update_calls = mock_progress_instance.update.call_args_list
        failure_update = any("❌ Validation failed" in str(call) for call in update_calls)
        assert failure_update


class TestValidateCommandEdgeCases:
    """Test edge cases for the validate command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("rxiv_maker.cli.commands.validate.Path")
    @patch("rxiv_maker.cli.commands.validate.Progress")
    @patch("rxiv_maker.engine.validate.main")
    def test_argv_restoration_on_exception(self, mock_validate_main, mock_progress, mock_path):
        """Test that sys.argv is properly restored even when validate_main raises an exception."""
        mock_path.return_value.exists.return_value = True

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_main to raise SystemExit
        mock_validate_main.side_effect = SystemExit(1)

        # Capture original argv
        with patch("rxiv_maker.cli.commands.validate.sys") as mock_sys:
            original_argv = ["original", "command"]
            mock_sys.argv = original_argv.copy()

            result = self.runner.invoke(validate, ["test_manuscript"])

            # Verify argv was restored even after exception
            assert mock_sys.argv == original_argv
            assert result.exit_code == 1

    @patch("rxiv_maker.cli.commands.validate.Path")
    def test_default_manuscript_path(self, mock_path):
        """Test default manuscript path when no path provided and no environment variable."""
        mock_path.return_value.exists.return_value = False

        # Clear MANUSCRIPT_PATH if it exists
        with patch.dict(os.environ, {}, clear=True):
            result = self.runner.invoke(validate, [])

        # Should use "MANUSCRIPT" as default and fail because it doesn't exist
        assert result.exit_code == 1
        assert "Manuscript directory 'MANUSCRIPT' does not exist" in result.output

    @patch("rxiv_maker.cli.commands.validate.Path")
    @patch("rxiv_maker.cli.commands.validate.Progress")
    @patch("rxiv_maker.engine.validate.main")
    def test_all_options_combined(self, mock_validate_main, mock_progress, mock_path):
        """Test validation with all options combined."""
        mock_path.return_value.exists.return_value = True

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_main to succeed
        mock_validate_main.return_value = None

        result = self.runner.invoke(validate, ["test_manuscript", "--detailed", "--no-doi"], obj={"verbose": True})

        assert result.exit_code == 0
        mock_validate_main.assert_called_once()

    @patch("rxiv_maker.cli.commands.validate.Path")
    @patch("rxiv_maker.cli.commands.validate.Progress")
    @patch("rxiv_maker.engine.validate.main")
    def test_progress_task_creation(self, mock_validate_main, mock_progress, mock_path):
        """Test that progress task is created correctly."""
        mock_path.return_value.exists.return_value = True

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_main to succeed
        mock_validate_main.return_value = None

        result = self.runner.invoke(validate, ["test_manuscript"])

        assert result.exit_code == 0

        # Verify progress task was created
        mock_progress_instance.add_task.assert_called_once_with("Running validation...", total=None)
