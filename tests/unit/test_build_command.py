"""Tests for the build (PDF) command functionality."""

import os
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from rxiv_maker.cli.commands.build import build


class TestBuildCommand:
    """Test the build command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_nonexistent_manuscript_directory_click_validation(self):
        """Test Click's built-in path validation for nonexistent directories."""
        result = self.runner.invoke(build, ["nonexistent_directory"])

        # Click should return exit code 2 for validation errors
        assert result.exit_code == 2
        # Click should show its own error message for invalid path
        assert "does not exist" in result.output.lower() or "invalid" in result.output.lower()

    @patch("rxiv_maker.engines.operations.build_manager.BuildManager")
    @patch("rxiv_maker.core.progress_framework.progress_operation")
    def test_successful_pdf_generation(self, mock_progress_operation, mock_build_manager):
        """Test successful PDF generation."""
        # Mock BuildManager
        mock_manager = MagicMock()
        mock_manager.build.return_value = True
        mock_build_manager.return_value = mock_manager

        # Mock progress_operation context manager
        mock_progress_context = MagicMock()
        mock_progress_context.__enter__ = MagicMock(return_value=MagicMock())
        mock_progress_context.__exit__ = MagicMock(return_value=None)
        mock_progress_operation.return_value = mock_progress_context

        # Use a real temporary directory that exists to pass Click validation
        with self.runner.isolated_filesystem():
            # Create a test manuscript directory
            os.makedirs("test_manuscript")
            result = self.runner.invoke(build, ["test_manuscript"], obj={"verbose": False, "engine": "local"})

        assert result.exit_code == 0
        mock_build_manager.assert_called_once()
        mock_manager.build.assert_called_once()

    @patch("rxiv_maker.core.logging_config.set_log_directory")
    @patch("rxiv_maker.engines.operations.build_manager.BuildManager")
    @patch("rxiv_maker.core.progress_framework.progress_operation")
    def test_build_failure(self, mock_progress_operation, mock_build_manager, mock_set_log_directory):
        """Test PDF generation failure."""
        # Mock BuildManager with failure
        mock_manager = MagicMock()
        mock_manager.build.return_value = False
        mock_build_manager.return_value = mock_manager

        # Mock progress_operation context manager
        mock_progress_context = MagicMock()
        mock_progress_context.__enter__ = MagicMock(return_value=MagicMock())
        mock_progress_context.__exit__ = MagicMock(return_value=None)
        mock_progress_operation.return_value = mock_progress_context

        # Use a real temporary directory that exists to pass Click validation
        with self.runner.isolated_filesystem():
            # Create a test manuscript directory
            os.makedirs("test_manuscript")
            result = self.runner.invoke(build, ["test_manuscript"], obj={"verbose": False, "engine": "local"})

        assert result.exit_code == 1
        mock_manager.build.assert_called_once()

    @patch("rxiv_maker.core.logging_config.set_log_directory")
    @patch("rxiv_maker.engines.operations.build_manager.BuildManager")
    @patch("rxiv_maker.core.progress_framework.progress_operation")
    def test_keyboard_interrupt_handling(self, mock_progress_operation, mock_build_manager, mock_set_log_directory):
        """Test keyboard interrupt handling."""
        # Mock BuildManager to raise KeyboardInterrupt
        mock_manager = MagicMock()
        mock_manager.build.side_effect = KeyboardInterrupt()
        mock_build_manager.return_value = mock_manager

        # Mock progress_operation context manager
        mock_progress_context = MagicMock()
        mock_progress_context.__enter__ = MagicMock(return_value=MagicMock())
        mock_progress_context.__exit__ = MagicMock(return_value=None)
        mock_progress_operation.return_value = mock_progress_context

        # Use a real temporary directory that exists to pass Click validation
        with self.runner.isolated_filesystem():
            # Create a test manuscript directory
            os.makedirs("test_manuscript")
            result = self.runner.invoke(build, ["test_manuscript"], obj={"verbose": False, "engine": "local"})

        assert result.exit_code == 1
        assert "build interrupted by user" in result.output

    @patch("rxiv_maker.core.logging_config.set_log_directory")
    @patch("rxiv_maker.engines.operations.build_manager.BuildManager")
    @patch("rxiv_maker.core.progress_framework.progress_operation")
    def test_unexpected_error_handling(self, mock_progress_operation, mock_build_manager, mock_set_log_directory):
        """Test unexpected error handling."""
        # Mock BuildManager to raise unexpected error
        mock_manager = MagicMock()
        mock_manager.build.side_effect = RuntimeError("Unexpected error")
        mock_build_manager.return_value = mock_manager

        # Mock progress_operation context manager
        mock_progress_context = MagicMock()
        mock_progress_context.__enter__ = MagicMock(return_value=MagicMock())
        mock_progress_context.__exit__ = MagicMock(return_value=None)
        mock_progress_operation.return_value = mock_progress_context

        # Use a real temporary directory that exists to pass Click validation
        with self.runner.isolated_filesystem():
            # Create a test manuscript directory
            os.makedirs("test_manuscript")
            result = self.runner.invoke(build, ["test_manuscript"], obj={"verbose": False, "engine": "local"})

        assert result.exit_code == 1
        # Error message should contain the actual error
        assert "Unexpected error" in result.output

    @patch("rxiv_maker.core.logging_config.set_log_directory")
    @patch("rxiv_maker.engines.operations.build_manager.BuildManager")
    @patch("rxiv_maker.core.progress_framework.progress_operation")
    def test_default_manuscript_path_from_env(
        self, mock_progress_operation, mock_build_manager, mock_set_log_directory
    ):
        """Test using MANUSCRIPT_PATH environment variable."""
        # Mock BuildManager
        mock_manager = MagicMock()
        mock_manager.build.return_value = True
        mock_build_manager.return_value = mock_manager

        # Mock progress_operation context manager
        mock_progress_context = MagicMock()
        mock_progress_context.__enter__ = MagicMock(return_value=MagicMock())
        mock_progress_context.__exit__ = MagicMock(return_value=None)
        mock_progress_operation.return_value = mock_progress_context

        # Test with environment variable
        with self.runner.isolated_filesystem():
            os.makedirs("custom_manuscript")
            with patch.dict(os.environ, {"MANUSCRIPT_PATH": "custom_manuscript"}):
                result = self.runner.invoke(build, [], obj={"verbose": False, "engine": "local"})

        assert result.exit_code == 0
        # Verify BuildManager was called with the environment variable value
        args, kwargs = mock_build_manager.call_args
        assert kwargs["manuscript_path"].endswith("custom_manuscript")

    @patch("rxiv_maker.core.logging_config.set_log_directory")
    @patch("rxiv_maker.engines.operations.build_manager.BuildManager")
    @patch("rxiv_maker.core.progress_framework.progress_operation")
    def test_build_options(self, mock_progress_operation, mock_build_manager, mock_set_log_directory):
        """Test various build options."""
        # Mock BuildManager
        mock_manager = MagicMock()
        mock_manager.build.return_value = True
        mock_build_manager.return_value = mock_manager

        # Mock progress_operation context manager
        mock_progress_context = MagicMock()
        mock_progress_context.__enter__ = MagicMock(return_value=MagicMock())
        mock_progress_context.__exit__ = MagicMock(return_value=None)
        mock_progress_operation.return_value = mock_progress_context

        # Use a real temporary directory
        with self.runner.isolated_filesystem():
            os.makedirs("test_manuscript")
            result = self.runner.invoke(
                build,
                [
                    "test_manuscript",
                    "--output-dir",
                    "custom_output",
                    "--force-figures",
                    "--skip-validation",
                    "--track-changes",
                    "v1.0.0",
                    "--verbose",
                ],
                obj={"verbose": False, "engine": "local"},
            )

        assert result.exit_code == 0

        # Verify BuildManager was called with correct options
        args, kwargs = mock_build_manager.call_args
        assert kwargs["manuscript_path"].endswith("test_manuscript")
        assert kwargs["output_dir"] == "custom_output"
        assert kwargs["force_figures"] is True
        assert kwargs["skip_validation"] is True
        assert kwargs["track_changes_tag"] == "v1.0.0"
        assert kwargs["verbose"] is True

    @patch("rxiv_maker.core.logging_config.set_debug")
    @patch("rxiv_maker.core.logging_config.set_quiet")
    @patch("rxiv_maker.cli.framework.Path")
    @patch("rxiv_maker.engines.operations.build_manager.BuildManager")
    @patch("rxiv_maker.cli.framework.Progress")
    @pytest.mark.skip(reason="Complex mocking test - needs refactoring")
    def test_logging_configuration(self, mock_progress, mock_build_manager, mock_path, mock_set_quiet, mock_set_debug):
        """Test logging configuration based on flags."""
        mock_path.return_value.exists.return_value = True

        # Mock BuildManager
        mock_manager = MagicMock()
        mock_manager.build.return_value = True
        mock_build_manager.return_value = mock_manager

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress_context = MagicMock()
        mock_progress_context.__enter__ = MagicMock(return_value=mock_progress_instance)
        mock_progress_context.__exit__ = MagicMock(return_value=None)
        mock_progress.return_value = mock_progress_context

        # Test debug flag with real directory
        with self.runner.isolated_filesystem():
            os.makedirs("test_manuscript")
            result = self.runner.invoke(
                build, ["test_manuscript", "--debug"], obj={"verbose": False, "engine": "local"}
            )
            assert result.exit_code == 0
            mock_set_debug.assert_called_with(True)

            # Reset mocks
            mock_set_debug.reset_mock()
            mock_set_quiet.reset_mock()

            # Test quiet flag
            result = self.runner.invoke(
                build, ["test_manuscript", "--quiet"], obj={"verbose": False, "engine": "local"}
            )
            assert result.exit_code == 0
            mock_set_quiet.assert_called_with(True)

    @patch("rxiv_maker.cli.framework.Path")
    @patch("rxiv_maker.core.logging_config.set_log_directory")
    @patch("rxiv_maker.engines.operations.build_manager.BuildManager")
    @patch("rxiv_maker.cli.framework.Progress")
    @pytest.mark.skip(reason="Complex mocking test - needs refactoring")
    def test_output_directory_handling(self, mock_progress, mock_build_manager, mock_set_log_directory, mock_path):
        """Test output directory handling."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_absolute.return_value = False

        # Mock BuildManager
        mock_manager = MagicMock()
        mock_manager.build.return_value = True
        mock_build_manager.return_value = mock_manager

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress_context = MagicMock()
        mock_progress_context.__enter__ = MagicMock(return_value=mock_progress_instance)
        mock_progress_context.__exit__ = MagicMock(return_value=None)
        mock_progress.return_value = mock_progress_context

        result = self.runner.invoke(build, ["test_manuscript", "--output-dir", "custom_output"])

        assert result.exit_code == 0
        # Verify log directory was set
        mock_set_log_directory.assert_called_once()

    @patch("rxiv_maker.cli.framework.Path")
    @patch("rxiv_maker.engines.operations.build_manager.BuildManager")
    @patch("rxiv_maker.cli.framework.Progress")
    @pytest.mark.skip(reason="Complex mocking test - needs refactoring")
    def test_progress_callback_handling(self, mock_progress, mock_build_manager, mock_path):
        """Test progress callback functionality."""
        mock_path.return_value.exists.return_value = True

        # Mock BuildManager
        mock_manager = MagicMock()
        mock_manager.build.return_value = True
        mock_build_manager.return_value = mock_manager

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_task = MagicMock()
        mock_progress_instance.add_task.return_value = mock_task
        mock_progress_context = MagicMock()
        mock_progress_context.__enter__ = MagicMock(return_value=mock_progress_instance)
        mock_progress_context.__exit__ = MagicMock(return_value=None)
        mock_progress.return_value = mock_progress_context

        result = self.runner.invoke(build, ["test_manuscript"])

        assert result.exit_code == 0

        # Verify progress callback was passed to build
        args, kwargs = mock_manager.build.call_args
        assert "progress_callback" in kwargs
        assert callable(kwargs["progress_callback"])

        # Test the progress callback
        progress_callback = kwargs["progress_callback"]
        progress_callback("Test step", 1, 5)
        mock_progress_instance.update.assert_called()


class TestBuildCommandEdgeCases:
    """Test edge cases for the build command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("rxiv_maker.cli.framework.Path")
    @patch("rxiv_maker.engines.operations.build_manager.BuildManager")
    @patch("rxiv_maker.cli.framework.Progress")
    @pytest.mark.skip(reason="Complex mocking test - needs refactoring")
    def test_skip_validation_removes_step(self, mock_progress, mock_build_manager, mock_path):
        """Test that skip-validation removes validation step from progress."""
        mock_path.return_value.exists.return_value = True

        # Mock BuildManager
        mock_manager = MagicMock()
        mock_manager.build.return_value = True
        mock_build_manager.return_value = mock_manager

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress_context = MagicMock()
        mock_progress_context.__enter__ = MagicMock(return_value=mock_progress_instance)
        mock_progress_context.__exit__ = MagicMock(return_value=None)
        mock_progress.return_value = mock_progress_context

        result = self.runner.invoke(build, ["test_manuscript", "--skip-validation"])

        assert result.exit_code == 0

        # The build steps should not include "Validating manuscript" when skip-validation is used
        # This is verified by checking the total parameter passed to add_task
        add_task_calls = mock_progress_instance.add_task.call_args_list
        main_task_call = [call for call in add_task_calls if "Building PDF" in str(call)][0]
        total_steps = main_task_call[1]["total"]  # kwargs["total"]

        # Normal build has 10 steps, skip-validation should have 9
        assert total_steps == 9

    @patch("rxiv_maker.cli.framework.Path")
    @patch("rxiv_maker.engines.operations.build_manager.BuildManager")
    @patch("rxiv_maker.cli.framework.Progress")
    @pytest.mark.skip(reason="Complex mocking test - needs refactoring")
    def test_build_success_output_messages(self, mock_progress, mock_build_manager, mock_path):
        """Test success output messages."""
        mock_path.return_value.exists.return_value = True
        mock_path.return_value.name = "test_manuscript"

        # Mock BuildManager
        mock_manager = MagicMock()
        mock_manager.build.return_value = True
        mock_build_manager.return_value = mock_manager

        # Mock Progress
        mock_progress_instance = MagicMock()
        mock_progress_context = MagicMock()
        mock_progress_context.__enter__ = MagicMock(return_value=mock_progress_instance)
        mock_progress_context.__exit__ = MagicMock(return_value=None)
        mock_progress.return_value = mock_progress_context

        result = self.runner.invoke(build, ["test_manuscript", "--track-changes", "v1.0.0", "--force-figures"])

        assert result.exit_code == 0
        # These messages should appear in the logs, not necessarily in CLI output
        # The test verifies the command completes successfully with these options

    @patch("rxiv_maker.cli.framework.PathManager")
    def test_absolute_output_path_handling(self, mock_path_manager):
        """Test handling of absolute output paths through PathManager."""
        # Mock PathManager instance
        mock_path_manager_instance = MagicMock()
        mock_path_manager_instance.manuscript_path = "/absolute/path/to/manuscript"
        mock_path_manager_instance.output_dir = "/absolute/path/to/output"
        mock_path_manager.return_value = mock_path_manager_instance

        # Use a real temporary directory that exists to pass Click validation
        with self.runner.isolated_filesystem():
            # Create a test manuscript directory
            os.makedirs("test_manuscript")

            # Test with absolute output path - this should work through PathManager
            self.runner.invoke(
                build,
                ["test_manuscript", "--output-dir", "/absolute/output/path"],
                obj={"verbose": False, "engine": "local"},
            )

        # The command should handle absolute paths through PathManager
        # Even if it fails later (due to missing BuildManager setup),
        # the PathManager should be created successfully
        mock_path_manager.assert_called_once()
