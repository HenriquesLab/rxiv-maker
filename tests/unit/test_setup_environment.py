"""Tests for the setup environment functionality."""

import subprocess
from unittest.mock import Mock, patch

import pytest

from rxiv_maker.engines.operations.setup_environment import EnvironmentSetup


class TestEnvironmentSetup:
    """Test the EnvironmentSetup class functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.setup = EnvironmentSetup(verbose=True, check_system_deps=False)

    def test_init_default_values(self):
        """Test EnvironmentSetup initialization with default values."""
        setup = EnvironmentSetup()
        assert setup.reinstall is False
        assert setup.verbose is False
        assert setup.check_system_deps is True
        assert setup.platform is not None
        assert setup.dependency_checker is not None

    def test_init_custom_values(self):
        """Test EnvironmentSetup initialization with custom values."""
        setup = EnvironmentSetup(reinstall=True, verbose=True, check_system_deps=False)
        assert setup.reinstall is True
        assert setup.verbose is True
        assert setup.check_system_deps is False

    def test_log_info_message(self, capsys):
        """Test logging info messages."""
        self.setup.log("Test message", "INFO")
        captured = capsys.readouterr()
        assert "✅ Test message" in captured.out

    def test_log_warning_message(self, capsys):
        """Test logging warning messages."""
        self.setup.log("Warning message", "WARNING")
        captured = capsys.readouterr()
        assert "⚠️  Warning message" in captured.out

    def test_log_error_message(self, capsys):
        """Test logging error messages."""
        self.setup.log("Error message", "ERROR")
        captured = capsys.readouterr()
        assert "❌ Error message" in captured.out

    def test_log_step_message(self, capsys):
        """Test logging step messages."""
        self.setup.log("Step message", "STEP")
        captured = capsys.readouterr()
        assert "🔧 Step message" in captured.out

    def test_log_default_message(self, capsys):
        """Test logging with default/unknown level."""
        self.setup.log("Default message", "UNKNOWN")
        captured = capsys.readouterr()
        assert "Default message" in captured.out

    @patch("subprocess.run")
    def test_check_uv_installation_success(self, mock_run):
        """Test successful uv installation check."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "uv 0.1.0"
        mock_run.return_value = mock_result

        result = self.setup.check_uv_installation()

        assert result is True
        mock_run.assert_called_once_with(["uv", "--version"], capture_output=True, text=True, timeout=10)

    @patch("subprocess.run")
    def test_check_uv_installation_failure(self, mock_run):
        """Test failed uv installation check."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = self.setup.check_uv_installation()

        assert result is False

    @patch("subprocess.run")
    def test_check_uv_installation_file_not_found(self, mock_run):
        """Test uv installation check when uv is not found."""
        mock_run.side_effect = FileNotFoundError()

        result = self.setup.check_uv_installation()

        assert result is False

    @patch("subprocess.run")
    def test_check_uv_installation_timeout(self, mock_run):
        """Test uv installation check timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("uv", 10)

        result = self.setup.check_uv_installation()

        assert result is False

    @patch("subprocess.run")
    def test_install_uv_windows_success(self, mock_run):
        """Test successful uv installation on Windows."""
        self.setup.platform.is_windows = Mock(return_value=True)
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = self.setup.install_uv()

        assert result is True
        mock_run.assert_called_once_with(
            ["powershell", "-Command", "irm https://astral.sh/uv/install.ps1 | iex"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )

    @patch("subprocess.run")
    def test_install_uv_unix_success(self, mock_run):
        """Test successful uv installation on Unix-like systems."""
        self.setup.platform.is_windows = Mock(return_value=False)

        # Mock curl result
        curl_result = Mock()
        curl_result.returncode = 0
        curl_result.stdout = "#!/bin/sh\necho 'Installing uv'"

        # Mock install result
        install_result = Mock()
        install_result.returncode = 0

        mock_run.side_effect = [curl_result, install_result]

        result = self.setup.install_uv()

        assert result is True
        assert mock_run.call_count == 2

    @patch("subprocess.run")
    def test_install_uv_unix_curl_failure(self, mock_run):
        """Test uv installation failure during curl download."""
        self.setup.platform.is_windows = Mock(return_value=False)

        # Mock curl failure
        curl_result = Mock()
        curl_result.returncode = 1
        curl_result.stderr = "Download failed"
        mock_run.return_value = curl_result

        result = self.setup.install_uv()

        assert result is False

    @patch("subprocess.run")
    def test_install_uv_failure(self, mock_run):
        """Test failed uv installation."""
        self.setup.platform.is_windows = Mock(return_value=True)
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Installation failed"
        mock_run.return_value = mock_result

        result = self.setup.install_uv()

        assert result is False

    @patch("subprocess.run")
    def test_install_uv_exception(self, mock_run):
        """Test uv installation with exception."""
        mock_run.side_effect = Exception("Network error")

        result = self.setup.install_uv()

        assert result is False

    def test_remove_existing_venv_no_venv(self):
        """Test removing virtual environment when none exists."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False

            result = self.setup.remove_existing_venv()

            assert result is True

    def test_remove_existing_venv_success(self):
        """Test successful virtual environment removal."""
        with (
            patch("pathlib.Path.exists") as mock_exists,
            patch.object(self.setup.platform, "remove_directory") as mock_remove,
        ):
            mock_exists.return_value = True
            mock_remove.return_value = True

            result = self.setup.remove_existing_venv()

            assert result is True
            mock_remove.assert_called_once()

    def test_remove_existing_venv_failure(self):
        """Test failed virtual environment removal."""
        with (
            patch("pathlib.Path.exists") as mock_exists,
            patch.object(self.setup.platform, "remove_directory") as mock_remove,
        ):
            mock_exists.return_value = True
            mock_remove.return_value = False

            result = self.setup.remove_existing_venv()

            assert result is False

    @patch("subprocess.run")
    def test_sync_dependencies_success(self, mock_run):
        """Test successful dependency synchronization."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Dependencies synced successfully"
        mock_run.return_value = mock_result

        result = self.setup.sync_dependencies()

        assert result is True
        mock_run.assert_called_once_with(
            ["uv", "sync", "--dev"],
            capture_output=True,
            text=True,
            timeout=300,
        )

    @patch("subprocess.run")
    def test_sync_dependencies_failure(self, mock_run):
        """Test failed dependency synchronization."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Dependency sync failed"
        mock_run.return_value = mock_result

        result = self.setup.sync_dependencies()

        assert result is False

    @patch("subprocess.run")
    def test_sync_dependencies_timeout(self, mock_run):
        """Test dependency synchronization timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("uv", 300)

        result = self.setup.sync_dependencies()

        assert result is False

    @patch("subprocess.run")
    def test_sync_dependencies_exception(self, mock_run):
        """Test dependency synchronization with exception."""
        mock_run.side_effect = Exception("Sync error")

        result = self.setup.sync_dependencies()

        assert result is False

    def test_check_system_dependencies_disabled(self):
        """Test system dependency check when disabled."""
        setup = EnvironmentSetup(check_system_deps=False)

        result = setup.check_system_dependencies()

        assert result is True

    def test_check_system_dependencies_missing_required(self):
        """Test system dependency check with missing required dependencies."""
        # Need to enable system dep checking for this test
        self.setup.check_system_deps = True

        mock_dep = Mock()
        mock_dep.name = "latex"

        self.setup.dependency_checker.check_all_dependencies = Mock()
        self.setup.dependency_checker.get_missing_required_dependencies = Mock(return_value=[mock_dep])
        self.setup.dependency_checker.get_missing_optional_dependencies = Mock(return_value=[])
        self.setup.dependency_checker.print_dependency_report = Mock()

        result = self.setup.check_system_dependencies()

        assert result is False

    def test_check_system_dependencies_success_with_optional_missing(self):
        """Test system dependency check success with optional dependencies missing."""
        mock_dep = Mock()
        mock_dep.name = "r"
        mock_dep.description = "R statistical computing"

        self.setup.dependency_checker.check_all_dependencies = Mock()
        self.setup.dependency_checker.get_missing_required_dependencies = Mock(return_value=[])
        self.setup.dependency_checker.get_missing_optional_dependencies = Mock(return_value=[mock_dep])

        result = self.setup.check_system_dependencies()

        assert result is True

    def test_check_system_dependencies_all_present(self):
        """Test system dependency check with all dependencies present."""
        self.setup.dependency_checker.check_all_dependencies = Mock()
        self.setup.dependency_checker.get_missing_required_dependencies = Mock(return_value=[])
        self.setup.dependency_checker.get_missing_optional_dependencies = Mock(return_value=[])

        result = self.setup.check_system_dependencies()

        assert result is True

    @patch("subprocess.run")
    def test_validate_environment_success(self, mock_run):
        """Test successful environment validation."""
        mock_python_path = "/path/to/.venv/bin/python"
        self.setup.platform.get_venv_python_path = Mock(return_value=mock_python_path)

        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True

            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Python 3.11.0"
            mock_run.return_value = mock_result

            result = self.setup.validate_environment()

            assert result is True
            mock_run.assert_called_once_with(
                [mock_python_path, "--version"], capture_output=True, text=True, timeout=10
            )

    def test_validate_environment_no_venv_path(self):
        """Test environment validation when no venv path is found."""
        self.setup.platform.get_venv_python_path = Mock(return_value=None)

        result = self.setup.validate_environment()

        assert result is False

    def test_validate_environment_venv_not_exists(self):
        """Test environment validation when venv doesn't exist."""
        mock_python_path = "/path/to/.venv/bin/python"
        self.setup.platform.get_venv_python_path = Mock(return_value=mock_python_path)

        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False

            result = self.setup.validate_environment()

            assert result is False

    @patch("subprocess.run")
    def test_validate_environment_python_failure(self, mock_run):
        """Test environment validation when Python check fails."""
        mock_python_path = "/path/to/.venv/bin/python"
        self.setup.platform.get_venv_python_path = Mock(return_value=mock_python_path)

        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True

            mock_result = Mock()
            mock_result.returncode = 1
            mock_run.return_value = mock_result

            result = self.setup.validate_environment()

            assert result is False

    @patch("subprocess.run")
    def test_validate_environment_exception(self, mock_run):
        """Test environment validation with exception."""
        mock_python_path = "/path/to/.venv/bin/python"
        self.setup.platform.get_venv_python_path = Mock(return_value=mock_python_path)

        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True
            mock_run.side_effect = Exception("Python error")

            result = self.setup.validate_environment()

            assert result is False


class TestEnvironmentSetupCompletion:
    """Test completion message functionality."""

    def test_show_completion_message_basic(self, capsys):
        """Test basic completion message."""
        setup = EnvironmentSetup(check_system_deps=False)
        setup.show_completion_message()

        captured = capsys.readouterr()
        assert "Setup complete!" in captured.out
        assert "rxiv pdf" in captured.out
        assert "System dependencies" in captured.out

    def test_show_completion_message_with_missing_required_deps(self, capsys):
        """Test completion message with missing required dependencies."""
        setup = EnvironmentSetup(check_system_deps=True)

        mock_dep = Mock()
        mock_dep.name = "latex"
        setup.dependency_checker = Mock()
        setup.dependency_checker.get_missing_required_dependencies = Mock(return_value=[mock_dep])
        setup.dependency_checker.get_missing_optional_dependencies = Mock(return_value=[])

        setup.show_completion_message()

        captured = capsys.readouterr()
        assert "Some required dependencies are missing" in captured.out

    def test_show_completion_message_with_missing_optional_deps(self, capsys):
        """Test completion message with missing optional dependencies."""
        setup = EnvironmentSetup(check_system_deps=True)

        mock_dep = Mock()
        mock_dep.name = "r"
        setup.dependency_checker = Mock()
        setup.dependency_checker.get_missing_required_dependencies = Mock(return_value=[])
        setup.dependency_checker.get_missing_optional_dependencies = Mock(return_value=[mock_dep])

        setup.show_completion_message()

        captured = capsys.readouterr()
        assert "Some optional dependencies are missing" in captured.out

    def test_show_completion_message_all_deps_present(self, capsys):
        """Test completion message when all dependencies are present."""
        setup = EnvironmentSetup(check_system_deps=True)

        setup.dependency_checker = Mock()
        setup.dependency_checker.get_missing_required_dependencies = Mock(return_value=[])
        setup.dependency_checker.get_missing_optional_dependencies = Mock(return_value=[])

        setup.show_completion_message()

        captured = capsys.readouterr()
        assert "All system dependencies are available!" in captured.out


class TestEnvironmentSetupFullWorkflow:
    """Test the complete setup workflow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.setup = EnvironmentSetup(verbose=True, check_system_deps=True)

    def test_run_setup_system_deps_failure(self):
        """Test setup failure due to system dependencies."""
        self.setup.check_system_dependencies = Mock(return_value=False)

        result = self.setup.run_setup()

        assert result is False

    def test_run_setup_venv_removal_failure(self):
        """Test setup failure due to venv removal."""
        self.setup.reinstall = True
        self.setup.check_system_dependencies = Mock(return_value=True)
        self.setup.remove_existing_venv = Mock(return_value=False)

        result = self.setup.run_setup()

        assert result is False

    def test_run_setup_uv_install_failure(self):
        """Test setup failure due to uv installation."""
        self.setup.check_system_dependencies = Mock(return_value=True)
        self.setup.check_uv_installation = Mock(return_value=False)
        self.setup.install_uv = Mock(return_value=False)

        result = self.setup.run_setup()

        assert result is False

    def test_run_setup_uv_verification_failure(self):
        """Test setup failure due to uv verification."""
        self.setup.check_system_dependencies = Mock(return_value=True)
        self.setup.check_uv_installation = Mock(side_effect=[False, False])
        self.setup.install_uv = Mock(return_value=True)

        result = self.setup.run_setup()

        assert result is False

    def test_run_setup_dependencies_sync_failure(self):
        """Test setup failure due to dependency sync."""
        self.setup.check_system_dependencies = Mock(return_value=True)
        self.setup.check_uv_installation = Mock(return_value=True)
        self.setup.sync_dependencies = Mock(return_value=False)

        result = self.setup.run_setup()

        assert result is False

    def test_run_setup_validation_failure(self):
        """Test setup failure due to environment validation."""
        self.setup.check_system_dependencies = Mock(return_value=True)
        self.setup.check_uv_installation = Mock(return_value=True)
        self.setup.sync_dependencies = Mock(return_value=True)
        self.setup.validate_environment = Mock(return_value=False)

        result = self.setup.run_setup()

        assert result is False

    def test_run_setup_complete_success(self):
        """Test complete successful setup workflow."""
        self.setup.check_system_dependencies = Mock(return_value=True)
        self.setup.check_uv_installation = Mock(return_value=True)
        self.setup.sync_dependencies = Mock(return_value=True)
        self.setup.validate_environment = Mock(return_value=True)
        self.setup.show_completion_message = Mock()

        result = self.setup.run_setup()

        assert result is True
        self.setup.show_completion_message.assert_called_once()

    def test_run_setup_with_uv_install_required(self):
        """Test setup workflow requiring uv installation."""
        self.setup.check_system_dependencies = Mock(return_value=True)
        self.setup.check_uv_installation = Mock(side_effect=[False, True])
        self.setup.install_uv = Mock(return_value=True)
        self.setup.sync_dependencies = Mock(return_value=True)
        self.setup.validate_environment = Mock(return_value=True)
        self.setup.show_completion_message = Mock()

        result = self.setup.run_setup()

        assert result is True
        self.setup.install_uv.assert_called_once()


class TestMainFunction:
    """Test the main function and argument parsing."""

    @patch("argparse.ArgumentParser.parse_args")
    @patch("rxiv_maker.engines.operations.setup_environment.EnvironmentSetup")
    def test_main_default_args(self, mock_setup_class, mock_parse_args):
        """Test main function with default arguments."""
        # Mock argument parsing
        mock_args = Mock()
        mock_args.reinstall = False
        mock_args.check_deps_only = False
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # Mock setup instance
        mock_setup_instance = Mock()
        mock_setup_instance.run_setup.return_value = True
        mock_setup_class.return_value = mock_setup_instance

        # Import and call main
        from rxiv_maker.engines.operations.setup_environment import main

        main()

        # Verify setup was created with correct arguments
        mock_setup_class.assert_called_once_with(
            reinstall=False,
            check_system_deps=True,  # Note: inverted from check_deps_only
            verbose=False,
        )
        mock_setup_instance.run_setup.assert_called_once()

    @patch("argparse.ArgumentParser.parse_args")
    @patch("rxiv_maker.engines.operations.setup_environment.EnvironmentSetup")
    def test_main_custom_args(self, mock_setup_class, mock_parse_args):
        """Test main function with custom arguments."""
        # Mock argument parsing
        mock_args = Mock()
        mock_args.reinstall = True
        mock_args.check_deps_only = True
        mock_args.verbose = True
        mock_parse_args.return_value = mock_args

        # Mock setup instance
        mock_setup_instance = Mock()
        mock_setup_instance.run_setup.return_value = True
        mock_setup_class.return_value = mock_setup_instance

        # Import and call main
        from rxiv_maker.engines.operations.setup_environment import main

        main()

        # Verify setup was created with correct arguments
        mock_setup_class.assert_called_once_with(
            reinstall=True,
            check_system_deps=False,  # Note: inverted from check_deps_only
            verbose=True,
        )

    @patch("argparse.ArgumentParser.parse_args")
    @patch("rxiv_maker.engines.operations.setup_environment.EnvironmentSetup")
    def test_main_setup_failure(self, mock_setup_class, mock_parse_args):
        """Test main function when setup fails."""
        # Mock argument parsing
        mock_args = Mock()
        mock_args.reinstall = False
        mock_args.check_deps_only = False
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # Mock setup instance with failure
        mock_setup_instance = Mock()
        mock_setup_instance.run_setup.return_value = False
        mock_setup_class.return_value = mock_setup_instance

        # Import and call main, expecting SystemExit
        from rxiv_maker.engines.operations.setup_environment import main

        with pytest.raises(SystemExit) as exc_info:
            main()

        # Verify exit code was 1
        assert exc_info.value.code == 1
