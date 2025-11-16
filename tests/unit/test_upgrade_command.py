"""Tests for the upgrade command."""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from src.rxiv_maker.cli.commands.upgrade import upgrade

# Patch path should be where the function is imported in the upgrade module
PATCH_PATH_DETECT = "src.rxiv_maker.cli.commands.upgrade.detect_install_method"
PATCH_PATH_UPDATE_CHECK = "src.rxiv_maker.cli.commands.upgrade.force_update_check"
PATCH_PATH_SUBPROCESS = "src.rxiv_maker.cli.commands.upgrade.subprocess.run"


class TestUpgradeCommand:
    """Test upgrade command functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    @patch("src.rxiv_maker.cli.commands.upgrade.detect_install_method")
    def test_upgrade_dev_installation_warning(self, mock_detect):
        """Test that dev installations show a warning and exit."""
        mock_detect.return_value = "dev"

        result = self.runner.invoke(upgrade)

        assert result.exit_code == 0
        assert "Development installation detected" in result.output
        assert "git pull" in result.output

    @patch("src.rxiv_maker.cli.commands.upgrade.detect_install_method")
    @patch("src.rxiv_maker.cli.commands.upgrade.force_update_check")
    def test_upgrade_no_update_available(self, mock_check, mock_detect):
        """Test upgrade when no update is available."""
        mock_detect.return_value = "pip"
        mock_check.return_value = (False, "1.0.0")

        result = self.runner.invoke(upgrade)

        assert result.exit_code == 0
        assert "already have the latest version" in result.output

    @patch("src.rxiv_maker.cli.commands.upgrade.detect_install_method")
    @patch("src.rxiv_maker.cli.commands.upgrade.force_update_check")
    @patch("src.rxiv_maker.cli.commands.upgrade.subprocess.run")
    def test_upgrade_pip_with_yes_flag(self, mock_run, mock_check, mock_detect):
        """Test upgrade with pip and --yes flag."""
        mock_detect.return_value = "pip"
        mock_check.return_value = (True, "1.2.0")
        mock_run.return_value = Mock(returncode=0)

        result = self.runner.invoke(upgrade, ["--yes"])

        assert result.exit_code == 0
        assert "Upgrading rxiv-maker" in result.output
        assert "Upgrade completed successfully" in result.output
        mock_run.assert_called_once()
        # Check that the command is a list containing pip upgrade
        cmd = mock_run.call_args[0][0]
        assert isinstance(cmd, list), f"Expected list, got {type(cmd)}"
        assert "pip" in cmd and "install" in cmd and "--upgrade" in cmd

    @patch("src.rxiv_maker.cli.commands.upgrade.detect_install_method")
    @patch("src.rxiv_maker.cli.commands.upgrade.force_update_check")
    @patch("src.rxiv_maker.cli.commands.upgrade.subprocess.run")
    def test_upgrade_homebrew(self, mock_run, mock_check, mock_detect):
        """Test upgrade with Homebrew."""
        mock_detect.return_value = "homebrew"
        mock_check.return_value = (True, "1.2.0")
        mock_run.return_value = Mock(returncode=0)

        result = self.runner.invoke(upgrade, ["--yes"])

        assert result.exit_code == 0
        # Homebrew calls run twice: first for 'brew update', then for 'brew upgrade'
        assert mock_run.call_count == 2
        # Check that the last command contains brew upgrade
        cmd = mock_run.call_args[0][0]
        if isinstance(cmd, list):
            assert "brew" in cmd and "upgrade" in cmd
        else:
            assert "brew" in cmd and "upgrade" in cmd

    @patch("src.rxiv_maker.cli.commands.upgrade.detect_install_method")
    @patch("src.rxiv_maker.cli.commands.upgrade.force_update_check")
    @patch("src.rxiv_maker.cli.commands.upgrade.subprocess.run")
    def test_upgrade_uv(self, mock_run, mock_check, mock_detect):
        """Test upgrade with uv."""
        mock_detect.return_value = "uv"
        mock_check.return_value = (True, "1.2.0")
        mock_run.return_value = Mock(returncode=0)

        result = self.runner.invoke(upgrade, ["--yes"])

        assert result.exit_code == 0
        mock_run.assert_called_once()
        # Check that the command contains uv tool upgrade
        cmd = mock_run.call_args[0][0]
        if isinstance(cmd, list):
            assert "uv" in cmd and "tool" in cmd and "upgrade" in cmd
        else:
            assert "uv tool upgrade" in cmd

    @patch("src.rxiv_maker.cli.commands.upgrade.detect_install_method")
    @patch("src.rxiv_maker.cli.commands.upgrade.force_update_check")
    @patch("src.rxiv_maker.cli.commands.upgrade.subprocess.run")
    def test_upgrade_pipx(self, mock_run, mock_check, mock_detect):
        """Test upgrade with pipx."""
        mock_detect.return_value = "pipx"
        mock_check.return_value = (True, "1.2.0")
        mock_run.return_value = Mock(returncode=0)

        result = self.runner.invoke(upgrade, ["--yes"])

        assert result.exit_code == 0
        mock_run.assert_called_once()
        # Check that the command contains pipx upgrade
        cmd = mock_run.call_args[0][0]
        if isinstance(cmd, list):
            assert "pipx" in cmd and "upgrade" in cmd
        else:
            assert "pipx upgrade" in cmd

    @patch("src.rxiv_maker.cli.commands.upgrade.detect_install_method")
    @patch("src.rxiv_maker.cli.commands.upgrade.force_update_check")
    def test_upgrade_check_only(self, mock_check, mock_detect):
        """Test --check-only flag."""
        mock_detect.return_value = "pip"
        mock_check.return_value = (True, "1.2.0")

        result = self.runner.invoke(upgrade, ["--check-only"])

        assert result.exit_code == 0
        assert "Update available" in result.output
        assert "pip install --upgrade" in result.output

    @patch("src.rxiv_maker.cli.commands.upgrade.detect_install_method")
    @patch("src.rxiv_maker.cli.commands.upgrade.force_update_check")
    @patch("src.rxiv_maker.cli.commands.upgrade.subprocess.run")
    @patch("src.rxiv_maker.cli.commands.upgrade.prompt_confirm")
    def test_upgrade_user_cancels(self, mock_confirm, mock_run, mock_check, mock_detect):
        """Test that user can cancel the upgrade."""
        mock_detect.return_value = "pip"
        mock_check.return_value = (True, "1.2.0")
        mock_confirm.return_value = False  # User cancels

        # Run upgrade (no input needed as we're mocking the confirmation)
        result = self.runner.invoke(upgrade)

        assert result.exit_code == 0
        assert "Upgrade cancelled" in result.output
        mock_run.assert_not_called()

    @patch("src.rxiv_maker.cli.commands.upgrade.detect_install_method")
    @patch("src.rxiv_maker.cli.commands.upgrade.force_update_check")
    @patch("src.rxiv_maker.cli.commands.upgrade.subprocess.run")
    def test_upgrade_command_failure(self, mock_run, mock_check, mock_detect):
        """Test handling of failed upgrade command."""
        mock_detect.return_value = "pip"
        mock_check.return_value = (True, "1.2.0")
        mock_run.return_value = Mock(returncode=1)

        result = self.runner.invoke(upgrade, ["--yes"])

        assert result.exit_code == 1
        # Check that the error guidance is shown (flexible matching for different output formats)
        assert "manually" in result.output or "exited with code" in result.output

    @patch("src.rxiv_maker.cli.commands.upgrade.detect_install_method")
    @patch("src.rxiv_maker.cli.commands.upgrade.force_update_check")
    def test_upgrade_check_fails(self, mock_check, mock_detect):
        """Test handling of failed update check."""
        mock_detect.return_value = "pip"
        mock_check.side_effect = Exception("Network error")

        result = self.runner.invoke(upgrade, ["--yes"])

        # Should continue with upgrade attempt despite check failure
        assert "Could not check for updates" in result.output
        assert "Proceeding with upgrade attempt" in result.output

    @patch("src.rxiv_maker.cli.commands.upgrade.detect_install_method")
    @patch("src.rxiv_maker.cli.commands.upgrade.force_update_check")
    def test_upgrade_shows_detected_method(self, mock_check, mock_detect):
        """Test that the detected installation method is shown."""
        mock_detect.return_value = "homebrew"
        mock_check.return_value = (False, "1.0.0")

        result = self.runner.invoke(upgrade)

        assert "Detected installation method: Homebrew" in result.output
