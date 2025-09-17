"""Unit tests for the validate command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from rxiv_maker.cli.commands.validate import validate


class TestValidateCommand:
    """Test the validate command."""

    def setup_method(self):
        """Set up test fixtures before each test."""
        self.runner = CliRunner()

    @patch("rxiv_maker.cli.commands.validate.validate_manuscript")
    @patch("rich.console.Console.status")
    def test_successful_validation(self, mock_status, mock_validate_manuscript):
        """Test successful manuscript validation."""
        # Mock status context manager
        mock_status.return_value.__enter__.return_value = MagicMock()
        mock_status.return_value.__exit__.return_value = None

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

    @patch("rxiv_maker.cli.commands.validate.validate_manuscript")
    @patch("rich.console.Console.status")
    def test_validation_failure(self, mock_status, mock_validate_manuscript):
        """Test manuscript validation failure."""
        # Mock status context manager
        mock_status.return_value.__enter__.return_value = MagicMock()
        mock_status.return_value.__exit__.return_value = None

        # Mock validate_manuscript to return False (validation failed)
        mock_validate_manuscript.return_value = False

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            assert result.exit_code == 1
            assert "❌ Validation failed - see errors above" in result.output
            mock_validate_manuscript.assert_called_once()

    @patch("rxiv_maker.cli.commands.validate.validate_manuscript")
    @patch("rich.console.Console.status")
    def test_validation_success_exit_zero(self, mock_status, mock_validate_manuscript):
        """Test validation with successful return - should be treated as success."""
        # Mock status context manager
        mock_status.return_value.__enter__.return_value = MagicMock()
        mock_status.return_value.__exit__.return_value = None

        # Mock validate_manuscript to return True (success)
        mock_validate_manuscript.return_value = True

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            # Should succeed with exit code 0
            assert result.exit_code == 0
            mock_validate_manuscript.assert_called_once()

    @patch("rxiv_maker.cli.commands.validate.validate_manuscript")
    @patch("rich.console.Console.status")
    def test_keyboard_interrupt_handling(self, mock_status, mock_validate_manuscript):
        """Test keyboard interrupt handling."""
        # Mock status context manager
        mock_status.return_value.__enter__.return_value = MagicMock()
        mock_status.return_value.__exit__.return_value = None

        # Mock validate_manuscript to raise KeyboardInterrupt
        mock_validate_manuscript.side_effect = KeyboardInterrupt()

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            assert result.exit_code == 1
            # Click intercepts KeyboardInterrupt and shows "Aborted."
            assert "Aborted." in result.output

    @patch("rxiv_maker.cli.commands.validate.validate_manuscript")
    @patch("rich.console.Console.status")
    def test_unexpected_error_handling(self, mock_status, mock_validate_manuscript):
        """Test unexpected error handling."""
        # Mock status context manager
        mock_status.return_value.__enter__.return_value = MagicMock()
        mock_status.return_value.__exit__.return_value = None

        # Mock validate_manuscript to raise an unexpected error
        mock_validate_manuscript.side_effect = RuntimeError("Unexpected validation error")

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            assert result.exit_code == 1
            assert "❌ Validation error: Unexpected validation error" in result.output
            assert "Unexpected validation error" in result.output

    @patch("rxiv_maker.cli.commands.validate.validate_manuscript")
    @patch("rich.console.Console.status")
    def test_default_manuscript_path_from_env(self, mock_status, mock_validate_manuscript):
        """Test that default manuscript path is taken from environment."""
        # Mock status context manager
        mock_status.return_value.__enter__.return_value = MagicMock()
        mock_status.return_value.__exit__.return_value = None

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

    @patch("rxiv_maker.cli.commands.validate.validate_manuscript")
    @patch("rich.console.Console.status")
    def test_argv_manipulation(self, mock_status, mock_validate_manuscript):
        """Test that argv manipulation doesn't affect validation."""
        # Mock status context manager
        mock_status.return_value.__enter__.return_value = MagicMock()
        mock_status.return_value.__exit__.return_value = None

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

    @patch("rxiv_maker.cli.commands.validate.validate_manuscript")
    @patch("rich.console.Console.status")
    def test_validation_options(self, mock_status, mock_validate_manuscript):
        """Test that validation options are passed correctly."""
        # Mock status context manager
        mock_status.return_value.__enter__.return_value = MagicMock()
        mock_status.return_value.__exit__.return_value = None

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

    @patch("rxiv_maker.cli.commands.validate.validate_manuscript")
    @patch("rich.console.Console.status")
    def test_verbose_error_reporting(self, mock_status, mock_validate_manuscript):
        """Test that verbose mode shows exception traceback."""
        # Mock status context manager
        mock_status.return_value.__enter__.return_value = MagicMock()
        mock_status.return_value.__exit__.return_value = None

        # Mock validate_manuscript to raise an error
        mock_validate_manuscript.side_effect = RuntimeError("Detailed error")

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": True})

            assert result.exit_code == 1
            assert "❌ Validation error: Detailed error" in result.output

    @patch("rxiv_maker.cli.commands.validate.validate_manuscript")
    @patch("rich.console.Console.status")
    def test_progress_update_on_success(self, mock_status, mock_validate_manuscript):
        """Test that progress is updated correctly on successful validation."""
        # Mock status context manager
        mock_status.return_value.__enter__.return_value = MagicMock()
        mock_status.return_value.__exit__.return_value = None

        # Mock validate_manuscript to succeed
        mock_validate_manuscript.return_value = True

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            assert result.exit_code == 0
            assert "✅ Validation passed!" in result.output
            mock_validate_manuscript.assert_called_once()

    @patch("rxiv_maker.cli.commands.validate.validate_manuscript")
    @patch("rich.console.Console.status")
    def test_progress_update_on_failure(self, mock_status, mock_validate_manuscript):
        """Test that progress is updated correctly on failed validation."""
        # Mock status context manager
        mock_status.return_value.__enter__.return_value = MagicMock()
        mock_status.return_value.__exit__.return_value = None

        # Mock validate_manuscript to fail
        mock_validate_manuscript.return_value = False

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            assert result.exit_code == 1
            assert "❌ Validation failed - see errors above" in result.output
            mock_validate_manuscript.assert_called_once()

    def test_nonexistent_manuscript_directory(self):
        """Test handling of nonexistent manuscript directory."""
        result = self.runner.invoke(validate, ["nonexistent"])

        assert result.exit_code == 2  # Click parameter validation error
        assert "Invalid value for '[MANUSCRIPT_PATH]': Directory" in result.output
        assert "nonexistent" in result.output
        assert "does not" in result.output
        assert "exist" in result.output
