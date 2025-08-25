"""Unit tests for the validate command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from rxiv_maker.cli.commands.validate import validate


class TestValidateCommand:
    """Test the validate command."""

    def setup_method(self):
        """Set up test fixtures before each test."""
        self.runner = CliRunner()

    @patch("rxiv_maker.cli.framework.Progress")
    @patch("rxiv_maker.engines.operations.validate.validate_manuscript")
    def test_successful_validation(self, mock_validate_manuscript, mock_progress):
        """Test successful manuscript validation."""
        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_manuscript to succeed (return True)
        mock_validate_manuscript.return_value = True

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            assert result.exit_code == 0
            assert "✅ Validation passed!" in result.output
            mock_validate_manuscript.assert_called_once()

    @patch("rxiv_maker.cli.framework.Progress")
    @patch("rxiv_maker.engines.operations.validate.validate_manuscript")
    def test_validation_failure(self, mock_validate_manuscript, mock_progress):
        """Test manuscript validation failure."""
        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_manuscript to return False (validation failed)
        mock_validate_manuscript.return_value = False

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            assert result.exit_code == 1
            assert "❌ Validation failed. See details above." in result.output
            assert "💡 Run with --detailed for more information" in result.output
            # Check for the core message ignoring line breaks
            assert "rxiv pdf" in result.output and "--skip-validation" in result.output
            assert "to build anyway" in result.output

    @patch("rxiv_maker.cli.framework.Progress")
    @patch("rxiv_maker.engines.operations.validate.validate_manuscript")
    def test_validation_success_exit_zero(self, mock_validate_manuscript, mock_progress):
        """Test validation with successful return - should be treated as success."""
        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_manuscript to return True (success)
        mock_validate_manuscript.return_value = True

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            # Should succeed with exit code 0
            assert result.exit_code == 0

    @patch("rxiv_maker.cli.framework.Progress")
    @patch("rxiv_maker.engines.operations.validate.validate_manuscript")
    def test_keyboard_interrupt_handling(self, mock_validate_manuscript, mock_progress):
        """Test keyboard interrupt handling."""
        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_manuscript to raise KeyboardInterrupt
        mock_validate_manuscript.side_effect = KeyboardInterrupt()

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            assert result.exit_code == 1
            assert "⏹️  validation interrupted by user" in result.output

    @patch("rxiv_maker.cli.framework.Progress")
    @patch("rxiv_maker.engines.operations.validate.validate_manuscript")
    def test_unexpected_error_handling(self, mock_validate_manuscript, mock_progress):
        """Test unexpected error handling."""
        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_manuscript to raise an unexpected error
        mock_validate_manuscript.side_effect = RuntimeError("Unexpected validation error")

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            assert result.exit_code == 1
            assert "❌ Unexpected error during validation" in result.output
            # The full error message contains the original error
            assert "Unexpected validation error" in result.output

    @patch("rxiv_maker.cli.framework.Progress")
    @patch("rxiv_maker.engines.operations.validate.validate_manuscript")
    def test_default_manuscript_path_from_env(self, mock_validate_manuscript, mock_progress):
        """Test that default manuscript path is taken from environment."""
        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_manuscript to succeed
        mock_validate_manuscript.return_value = True

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("custom_manuscript")
            os.environ["MANUSCRIPT_PATH"] = "custom_manuscript"

            try:
                result = self.runner.invoke(validate, [], obj={"verbose": False})

                assert result.exit_code == 0
                mock_validate_manuscript.assert_called_once()

                # Verify the call was made with the environment variable path
                args, kwargs = mock_validate_manuscript.call_args
                # The manuscript_path is passed as a keyword argument and resolved to absolute path
                assert kwargs["manuscript_path"].endswith("custom_manuscript")
            finally:
                # Clean up environment variable
                del os.environ["MANUSCRIPT_PATH"]

    @patch("rxiv_maker.cli.framework.Progress")
    @patch("rxiv_maker.engines.operations.validate.validate_manuscript")
    def test_argv_manipulation(self, mock_validate_manuscript, mock_progress):
        """Test that argv manipulation doesn't affect validation."""
        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_manuscript to succeed
        mock_validate_manuscript.return_value = True

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            assert result.exit_code == 0

            # Verify the validation function was called correctly
            mock_validate_manuscript.assert_called_once()

    @patch("rxiv_maker.cli.framework.Progress")
    @patch("rxiv_maker.engines.operations.validate.validate_manuscript")
    def test_validation_options(self, mock_validate_manuscript, mock_progress):
        """Test that validation options are passed correctly."""
        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_manuscript to succeed
        mock_validate_manuscript.return_value = True

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            # Test with detailed and no-doi flags
            result = self.runner.invoke(
                validate,
                ["test_manuscript", "--detailed", "--no-doi"],
                obj={"verbose": True},
            )

            assert result.exit_code == 0

            # Verify the options were passed correctly
            mock_validate_manuscript.assert_called_once()
            args, kwargs = mock_validate_manuscript.call_args
            assert kwargs["detailed"] is True
            assert kwargs["verbose"] is True
            assert kwargs["check_latex"] is True

    @patch("rxiv_maker.cli.framework.Progress")
    @patch("rxiv_maker.engines.operations.validate.validate_manuscript")
    def test_verbose_error_reporting(self, mock_validate_manuscript, mock_progress):
        """Test that verbose mode shows exception traceback."""
        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        # Mock validate_manuscript to raise an error
        mock_validate_manuscript.side_effect = RuntimeError("Detailed error")

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": True})

            assert result.exit_code == 1
            assert "❌ Unexpected error during validation" in result.output

    @patch("rxiv_maker.cli.framework.Progress")
    @patch("rxiv_maker.engines.operations.validate.validate_manuscript")
    def test_progress_update_on_success(self, mock_validate_manuscript, mock_progress):
        """Test that progress is updated correctly on successful validation."""
        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_task = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance
        mock_progress_instance.add_task.return_value = mock_task

        # Mock validate_manuscript to succeed
        mock_validate_manuscript.return_value = True

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            assert result.exit_code == 0

            # Verify progress was updated correctly
            mock_progress_instance.add_task.assert_called_once_with("Running validation...", total=None)
            mock_progress_instance.update.assert_called_with(mock_task, description="✅ Validation completed")

    @patch("rxiv_maker.cli.framework.Progress")
    @patch("rxiv_maker.engines.operations.validate.validate_manuscript")
    def test_progress_update_on_failure(self, mock_validate_manuscript, mock_progress):
        """Test that progress is updated correctly on failed validation."""
        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_task = MagicMock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance
        mock_progress_instance.add_task.return_value = mock_task

        # Mock validate_manuscript to fail
        mock_validate_manuscript.return_value = False

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            assert result.exit_code == 1

            # Verify progress was updated correctly
            mock_progress_instance.add_task.assert_called_once_with("Running validation...", total=None)
            mock_progress_instance.update.assert_called_with(mock_task, description="❌ Validation failed")

    def test_nonexistent_manuscript_directory(self):
        """Test handling of nonexistent manuscript directory."""
        result = self.runner.invoke(validate, ["nonexistent"])

        assert result.exit_code == 2  # Click parameter validation error
        assert "Invalid value for '[MANUSCRIPT_PATH]': Directory" in result.output
        assert "nonexistent" in result.output
        assert "does not" in result.output
        assert "exist" in result.output
