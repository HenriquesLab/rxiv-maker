"""Unit tests for the validate command."""

from unittest.mock import patch

from click.testing import CliRunner

from rxiv_maker.cli.commands.validate import validate


class TestValidateCommand:
    """Test the validate command."""

    def setup_method(self):
        """Set up test fixtures before each test."""
        self.runner = CliRunner()

    @patch("rxiv_maker.cli.framework.ValidationCommand.run")
    def test_successful_validation(self, mock_run):
        """Test successful manuscript validation."""
        # Mock ValidationCommand.run to succeed (return 0)
        mock_run.return_value = 0

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            assert result.exit_code == 0
            mock_run.assert_called_once()

    @patch("rxiv_maker.engines.operations.validate.validate_manuscript")
    def test_validation_failure(self, mock_validate):
        """Test manuscript validation failure."""
        # Mock validate_manuscript to fail (return False)
        mock_validate.return_value = False

        # Use isolated filesystem to create actual directory for Click validation
        with self.runner.isolated_filesystem():
            import os

            os.makedirs("test_manuscript")

            result = self.runner.invoke(validate, ["test_manuscript"], obj={"verbose": False})

            # Should fail with exit code 1
            assert result.exit_code == 1
            mock_validate.assert_called_once()

    def test_nonexistent_manuscript_directory(self):
        """Test handling of nonexistent manuscript directory."""
        result = self.runner.invoke(validate, ["nonexistent"])

        assert result.exit_code == 2  # Click parameter validation error
        assert "Invalid value for '[MANUSCRIPT_PATH]': Directory" in result.output
        assert "nonexistent" in result.output
        assert "does not" in result.output
        assert "exist" in result.output
