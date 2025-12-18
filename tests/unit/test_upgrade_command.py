"""Tests for the upgrade command."""

from unittest.mock import patch

from click.testing import CliRunner

from src.rxiv_maker.cli.commands.upgrade import upgrade

# Patch paths for the upgrade module
PATCH_PATH_DETECT = "src.rxiv_maker.cli.commands.upgrade.detect_install_method"
PATCH_PATH_WORKFLOW = "src.rxiv_maker.cli.commands.upgrade.handle_upgrade_workflow"


class TestUpgradeCommand:
    """Test upgrade command functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    @patch(PATCH_PATH_DETECT)
    def test_upgrade_dev_installation_warning(self, mock_detect):
        """Test that dev installations show a warning and exit."""
        mock_detect.return_value = "dev"

        result = self.runner.invoke(upgrade)

        assert result.exit_code == 0
        assert "Development installation detected" in result.output
        assert "git pull" in result.output

    @patch(PATCH_PATH_DETECT)
    @patch(PATCH_PATH_WORKFLOW)
    def test_upgrade_success(self, mock_workflow, mock_detect):
        """Test successful upgrade."""
        mock_detect.return_value = "pip"
        mock_workflow.return_value = (True, None)

        result = self.runner.invoke(upgrade, ["--yes"])

        assert result.exit_code == 0
        mock_workflow.assert_called_once()
        # Verify workflow called with correct parameters
        call_args = mock_workflow.call_args
        assert call_args[1]["package_name"] == "rxiv-maker"
        assert call_args[1]["skip_confirmation"] is True
        assert call_args[1]["check_only"] is False

    @patch(PATCH_PATH_DETECT)
    @patch(PATCH_PATH_WORKFLOW)
    def test_upgrade_check_only(self, mock_workflow, mock_detect):
        """Test --check-only flag."""
        mock_detect.return_value = "pip"
        mock_workflow.return_value = (True, None)

        result = self.runner.invoke(upgrade, ["--check-only"])

        assert result.exit_code == 0
        call_args = mock_workflow.call_args
        assert call_args[1]["check_only"] is True

    @patch(PATCH_PATH_DETECT)
    @patch(PATCH_PATH_WORKFLOW)
    def test_upgrade_without_yes_flag(self, mock_workflow, mock_detect):
        """Test upgrade without --yes flag (interactive mode)."""
        mock_detect.return_value = "pip"
        mock_workflow.return_value = (True, None)

        result = self.runner.invoke(upgrade)

        assert result.exit_code == 0
        call_args = mock_workflow.call_args
        assert call_args[1]["skip_confirmation"] is False

    @patch(PATCH_PATH_DETECT)
    @patch(PATCH_PATH_WORKFLOW)
    def test_upgrade_failure(self, mock_workflow, mock_detect):
        """Test failed upgrade."""
        mock_detect.return_value = "pip"
        mock_workflow.return_value = (False, "Network error")

        result = self.runner.invoke(upgrade, ["--yes"])

        assert result.exit_code == 1

    @patch(PATCH_PATH_DETECT)
    @patch(PATCH_PATH_WORKFLOW)
    def test_upgrade_homebrew(self, mock_workflow, mock_detect):
        """Test upgrade with Homebrew installation."""
        mock_detect.return_value = "homebrew"
        mock_workflow.return_value = (True, None)

        result = self.runner.invoke(upgrade, ["--yes"])

        assert result.exit_code == 0
        mock_workflow.assert_called_once()

    @patch(PATCH_PATH_DETECT)
    @patch(PATCH_PATH_WORKFLOW)
    def test_upgrade_uv(self, mock_workflow, mock_detect):
        """Test upgrade with uv installation."""
        mock_detect.return_value = "uv"
        mock_workflow.return_value = (True, None)

        result = self.runner.invoke(upgrade, ["--yes"])

        assert result.exit_code == 0
        mock_workflow.assert_called_once()

    @patch(PATCH_PATH_DETECT)
    @patch(PATCH_PATH_WORKFLOW)
    def test_upgrade_pipx(self, mock_workflow, mock_detect):
        """Test upgrade with pipx installation."""
        mock_detect.return_value = "pipx"
        mock_workflow.return_value = (True, None)

        result = self.runner.invoke(upgrade, ["--yes"])

        assert result.exit_code == 0
        mock_workflow.assert_called_once()

    @patch(PATCH_PATH_DETECT)
    @patch(PATCH_PATH_WORKFLOW)
    def test_upgrade_github_params(self, mock_workflow, mock_detect):
        """Test that GitHub organization and repo are passed correctly."""
        mock_detect.return_value = "pip"
        mock_workflow.return_value = (True, None)

        result = self.runner.invoke(upgrade, ["--yes"])

        assert result.exit_code == 0
        call_args = mock_workflow.call_args
        assert call_args[1]["github_org"] == "HenriquesLab"
        assert call_args[1]["github_repo"] == "rxiv-maker"
