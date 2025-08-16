"""Unit tests for the validate command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from rxiv_maker.cli.commands.validate import validate


class TestValidateCommand:
    """Test the validate command."""

    def setup_method(self):
        """Set up test fixtures before each test."""
        self.runner = CliRunner()

    @patch("rxiv_maker.cli.commands.validate.ValidationCommand")
    def test_successful_validation(self, mock_validation_command):
        """Test successful manuscript validation."""
        # Mock ValidationCommand instance
        mock_command_instance = MagicMock()
        mock_validation_command.return_value = mock_command_instance

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            assert result.exit_code == 0
            # Verify ValidationCommand was created and run was called
            mock_validation_command.assert_called_once()
            mock_command_instance.run.assert_called_once()

    @patch("rxiv_maker.cli.commands.validate.ValidationCommand")
    def test_validation_failure(self, mock_validation_command):
        """Test manuscript validation failure."""
        # Mock ValidationCommand instance to simulate failure
        mock_command_instance = MagicMock()
        # Simulate a command execution error (validation failure)
        from rxiv_maker.cli.framework import CommandExecutionError

        mock_command_instance.run.side_effect = CommandExecutionError("Validation failed", 1)
        mock_validation_command.return_value = mock_command_instance

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            assert result.exit_code == 1
            # Verify ValidationCommand was created and run was called
            mock_validation_command.assert_called_once()
            mock_command_instance.run.assert_called_once()

    @patch("rxiv_maker.cli.commands.validate.ValidationCommand")
    def test_validation_success_exit_zero(self, mock_validation_command):
        """Test validation with success return value - should be treated as success."""
        # Mock ValidationCommand instance for success
        mock_command_instance = MagicMock()
        mock_validation_command.return_value = mock_command_instance

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            # Should be treated as success
            assert result.exit_code == 0
            mock_validation_command.assert_called_once()
            mock_command_instance.run.assert_called_once()

    @patch("rxiv_maker.cli.commands.validate.ValidationCommand")
    def test_keyboard_interrupt_handling(self, mock_validation_command):
        """Test keyboard interrupt handling."""
        # Mock ValidationCommand instance to raise KeyboardInterrupt
        mock_command_instance = MagicMock()
        mock_command_instance.run.side_effect = KeyboardInterrupt()
        mock_validation_command.return_value = mock_command_instance

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            assert result.exit_code == 1
            mock_validation_command.assert_called_once()
            mock_command_instance.run.assert_called_once()

    @patch("rxiv_maker.cli.commands.validate.ValidationCommand")
    def test_unexpected_error_handling(self, mock_validation_command):
        """Test unexpected error handling."""
        # Mock ValidationCommand instance to raise an unexpected error
        mock_command_instance = MagicMock()
        mock_command_instance.run.side_effect = RuntimeError("Unexpected validation error")
        mock_validation_command.return_value = mock_command_instance

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            assert result.exit_code == 1
            mock_validation_command.assert_called_once()
            mock_command_instance.run.assert_called_once()

    def test_nonexistent_manuscript_directory(self):
        """Test handling of nonexistent manuscript directory."""
        # Test with a directory that doesn't exist
        # click.Path(exists=True) will handle this validation
        result = self.runner.invoke(validate, ["nonexistent_directory_that_does_not_exist"])

        assert result.exit_code == 2  # Click parameter validation error
        assert "Invalid value for '[MANUSCRIPT_PATH]': Directory" in result.output
        assert "nonexistent_directory_that_does_not_exist" in result.output
        assert "does not" in result.output
        assert "exist" in result.output
