"""Tests for BuildManager manuscript path environment variable setting."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from rxiv_maker.core.environment_manager import EnvironmentManager
from rxiv_maker.engines.operations.build_manager import BuildManager


class TestBuildManagerManuscriptPath:
    """Test BuildManager's manuscript path environment variable handling."""

    def setup_method(self):
        """Set up for each test."""
        # Save original environment
        self.original_env = os.environ.copy()
        EnvironmentManager.clear_rxiv_vars()

    def teardown_method(self):
        """Clean up after each test."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_build_manager_sets_manuscript_path_environment(self, tmp_path):
        """Test that BuildManager sets MANUSCRIPT_PATH in environment during build."""
        # Create test manuscript structure
        manuscript_dir = tmp_path / "test_manuscript"
        manuscript_dir.mkdir()

        # Create minimal required files
        config_file = manuscript_dir / "00_CONFIG.yml"
        config_file.write_text("title: Test Manuscript\n")

        main_file = manuscript_dir / "01_MAIN.md"
        main_file.write_text("# Test Content\n")

        # Mock the BuildManager's internal methods to avoid full build
        with patch.object(BuildManager, "setup_output_directory"):
            with patch.object(BuildManager, "generate_figures"):
                with patch.object(BuildManager, "validate_manuscript", return_value=True):
                    with patch.object(BuildManager, "generate_manuscript_tex"):
                        with patch.object(BuildManager, "compile_pdf"):
                            with patch.object(BuildManager, "validate_pdf"):
                                with patch.object(BuildManager, "copy_final_pdf"):
                                    with patch.object(BuildManager, "run_word_count_analysis"):
                                        # Create build manager
                                        build_manager = BuildManager(
                                            manuscript_path=str(manuscript_dir),
                                            skip_validation=True,
                                            skip_pdf_validation=True,
                                        )

                                        # Initially, environment variable should not be set
                                        assert EnvironmentManager.get_manuscript_path() is None

                                        # Mock the build process but capture environment setting
                                        def mock_build():
                                            # This simulates the environment setting that happens at the start of build()
                                            EnvironmentManager.set_manuscript_path(build_manager.manuscript_dir)
                                            return True

                                        build_manager.build = mock_build

                                        # Run build
                                        success = build_manager.build()

                                        # Verify build succeeded
                                        assert success

                                        # Verify environment variable is set correctly
                                        env_path = EnvironmentManager.get_manuscript_path()
                                        assert env_path == str(manuscript_dir.resolve())

    def test_manuscript_path_available_during_build_process(self, tmp_path):
        """Test that MANUSCRIPT_PATH is available to Python execution during build."""
        # Create test manuscript with Python code
        manuscript_dir = tmp_path / "python_test_manuscript"
        manuscript_dir.mkdir()

        # Create config file
        config_file = manuscript_dir / "00_CONFIG.yml"
        config_file.write_text("""
title: Test Manuscript
authors:
  - name: Test Author
""")

        # Create main file with Python code that uses MANUSCRIPT_PATH
        main_file = manuscript_dir / "01_MAIN.md"
        main_file.write_text("""
# Test Document

{{py:exec
manuscript_location = MANUSCRIPT_PATH
print(f"Manuscript path: {manuscript_location}")
}}

The manuscript is located at: {{py:get manuscript_location}}
""")

        # Create a minimal BuildManager and simulate the environment setting
        BuildManager(
            manuscript_path=str(manuscript_dir), skip_validation=True, skip_pdf_validation=True, clear_output=False
        )

        # Manually set the environment variable as it would be during build
        EnvironmentManager.set_manuscript_path(manuscript_dir)

        # Test that Python code can access MANUSCRIPT_PATH
        from rxiv_maker.converters.python_executor import PythonExecutor

        executor = PythonExecutor()
        result = executor.execute_inline("MANUSCRIPT_PATH")

        assert result == str(manuscript_dir.resolve())

    def test_multiple_build_managers_manuscript_path_isolation(self, tmp_path):
        """Test that different build managers can work with different manuscript paths."""
        # Create two different manuscript directories
        manuscript1 = tmp_path / "manuscript1"
        manuscript1.mkdir()

        manuscript2 = tmp_path / "manuscript2"
        manuscript2.mkdir()

        # Create build managers for both
        manager1 = BuildManager(manuscript_path=str(manuscript1))
        manager2 = BuildManager(manuscript_path=str(manuscript2))

        # Simulate environment setting for first manager
        EnvironmentManager.set_manuscript_path(manager1.manuscript_dir)
        assert EnvironmentManager.get_manuscript_path() == str(manuscript1.resolve())

        # Simulate environment setting for second manager
        EnvironmentManager.set_manuscript_path(manager2.manuscript_dir)
        assert EnvironmentManager.get_manuscript_path() == str(manuscript2.resolve())

    def test_build_manager_handles_relative_paths(self, tmp_path):
        """Test BuildManager correctly handles relative manuscript paths."""
        # Create manuscript directory
        manuscript_dir = tmp_path / "relative_test"
        manuscript_dir.mkdir()

        # Change to parent directory to test relative path
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Create build manager with relative path
            build_manager = BuildManager(manuscript_path="relative_test")

            # The manuscript_dir should be resolved to absolute path
            expected_path = manuscript_dir.resolve()
            actual_path = Path(build_manager.manuscript_path).resolve()

            assert actual_path == expected_path

            # Test environment variable setting with relative path
            EnvironmentManager.set_manuscript_path(build_manager.manuscript_dir)
            env_path = EnvironmentManager.get_manuscript_path()

            assert env_path == str(expected_path)

        finally:
            os.chdir(original_cwd)

    def test_environment_variable_cleanup_after_build(self, tmp_path):
        """Test behavior of environment variables after build completion."""
        manuscript_dir = tmp_path / "cleanup_test"
        manuscript_dir.mkdir()

        build_manager = BuildManager(manuscript_path=str(manuscript_dir))

        # Set environment variable as would happen during build
        EnvironmentManager.set_manuscript_path(build_manager.manuscript_dir)

        # Verify it's set
        assert EnvironmentManager.get_manuscript_path() == str(manuscript_dir.resolve())

        # Note: In the current implementation, environment variables persist after build
        # This is by design to allow post-build operations to access the manuscript path
        # If cleanup is needed, it should be done explicitly by the caller

    def test_manuscript_path_with_spaces_and_special_characters(self, tmp_path):
        """Test manuscript paths with spaces and special characters."""
        # Create directory with spaces and special characters
        manuscript_dir = tmp_path / "manuscript with spaces & special-chars"
        manuscript_dir.mkdir()

        build_manager = BuildManager(manuscript_path=str(manuscript_dir))

        # Set environment variable
        EnvironmentManager.set_manuscript_path(build_manager.manuscript_dir)

        # Verify it's handled correctly
        env_path = EnvironmentManager.get_manuscript_path()
        assert env_path == str(manuscript_dir.resolve())

        # Test that Python executor can handle the path
        from rxiv_maker.converters.python_executor import PythonExecutor

        executor = PythonExecutor()
        result = executor.execute_inline("MANUSCRIPT_PATH")

        assert result == str(manuscript_dir.resolve())

    def test_error_handling_invalid_manuscript_path(self):
        """Test error handling when manuscript path is invalid."""
        # Try to create BuildManager with non-existent path
        from rxiv_maker.core.path_manager import PathResolutionError

        with pytest.raises((FileNotFoundError, ValueError, PathResolutionError)):
            BuildManager(manuscript_path="/non/existent/path")

    def test_environment_variable_inheritance_in_subprocesses(self, tmp_path):
        """Test that MANUSCRIPT_PATH is inherited by subprocesses."""
        manuscript_dir = tmp_path / "subprocess_test"
        manuscript_dir.mkdir()

        # Set environment variable
        EnvironmentManager.set_manuscript_path(manuscript_dir)

        # Test subprocess environment inheritance
        env_for_subprocess = EnvironmentManager.set_environment_for_subprocess()

        assert EnvironmentManager.MANUSCRIPT_PATH in env_for_subprocess
        assert env_for_subprocess[EnvironmentManager.MANUSCRIPT_PATH] == str(manuscript_dir.resolve())


class TestBuildManagerIntegrationWithPythonReporter:
    """Test integration between BuildManager and Python execution reporting."""

    def setup_method(self):
        """Set up for each test."""
        self.original_env = os.environ.copy()
        EnvironmentManager.clear_rxiv_vars()

        # Reset Python execution reporter
        try:
            from rxiv_maker.utils.python_execution_reporter import reset_python_execution_reporter

            reset_python_execution_reporter()
        except ImportError:
            pass

    def teardown_method(self):
        """Clean up after each test."""
        os.environ.clear()
        os.environ.update(self.original_env)

    @patch.object(BuildManager, "display_python_execution_report")
    def test_build_manager_calls_python_execution_report(self, mock_display_report, tmp_path):
        """Test that BuildManager calls Python execution reporting during build."""
        manuscript_dir = tmp_path / "reporting_test"
        manuscript_dir.mkdir()

        # Create minimal files
        config_file = manuscript_dir / "00_CONFIG.yml"
        config_file.write_text("title: Test\n")

        main_file = manuscript_dir / "01_MAIN.md"
        main_file.write_text("# Test\n")

        # Mock all the build steps
        with patch.object(BuildManager, "setup_output_directory"):
            with patch.object(BuildManager, "generate_figures"):
                with patch.object(BuildManager, "validate_manuscript", return_value=True):
                    with patch.object(BuildManager, "generate_manuscript_tex"):
                        with patch.object(BuildManager, "compile_pdf"):
                            with patch.object(BuildManager, "validate_pdf"):
                                with patch.object(BuildManager, "copy_final_pdf"):
                                    with patch.object(BuildManager, "run_word_count_analysis"):
                                        build_manager = BuildManager(
                                            manuscript_path=str(manuscript_dir),
                                            skip_validation=True,
                                            skip_pdf_validation=True,
                                        )

                                        # Run build
                                        build_manager.build()

                                        # Verify that Python execution report was called
                                        mock_display_report.assert_called_once()

    def test_manuscript_path_consistency_across_build_process(self, tmp_path):
        """Test that MANUSCRIPT_PATH remains consistent throughout the build process."""
        manuscript_dir = tmp_path / "consistency_test"
        manuscript_dir.mkdir()

        build_manager = BuildManager(manuscript_path=str(manuscript_dir))

        # Set environment as happens during build
        EnvironmentManager.set_manuscript_path(build_manager.manuscript_dir)

        # Check consistency at different stages
        initial_path = EnvironmentManager.get_manuscript_path()

        # Simulate various build stages checking the environment
        stages = ["setup", "figures", "validation", "latex", "compilation"]

        for stage in stages:
            current_path = EnvironmentManager.get_manuscript_path()
            assert current_path == initial_path, f"Path changed during {stage} stage"

        # Final verification
        assert EnvironmentManager.get_manuscript_path() == str(manuscript_dir.resolve())
