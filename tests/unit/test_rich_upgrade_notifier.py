"""Tests for RxivUpgradeNotifier."""

from unittest.mock import Mock, patch

from rich.console import Console

from src.rxiv_maker.utils.rich_upgrade_notifier import RxivUpgradeNotifier


class TestRxivUpgradeNotifier:
    """Test RxivUpgradeNotifier functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.console = Mock(spec=Console)
        self.notifier = RxivUpgradeNotifier(self.console)

    def test_show_checking(self):
        """Test show_checking displays checking message."""
        self.notifier.show_checking()

        self.console.print.assert_called_once()
        call_args = self.console.print.call_args[0]
        assert "Checking for updates" in call_args[0]

    def test_show_version_check_update_available(self):
        """Test version check with update available."""
        self.notifier.show_version_check("1.0.0", "1.1.0", True)

        assert self.console.print.called
        # Check that output mentions update available
        call_text = str(self.console.print.call_args)
        assert "1.0.0" in call_text and "1.1.0" in call_text

    def test_show_version_check_no_update(self):
        """Test version check with no update."""
        self.notifier.show_version_check("1.0.0", "1.0.0", False)

        assert self.console.print.called
        call_text = str(self.console.print.call_args)
        assert "latest version" in call_text

    @patch("src.rxiv_maker.utils.changelog_parser.fetch_and_format_changelog")
    def test_show_update_info_with_changelog(self, mock_fetch):
        """Test update info with changelog integration."""
        mock_fetch.return_value = ("✨ Added new feature\n🐛 Fixed bug", None)

        self.notifier.show_update_info("1.0.0", "1.1.0", "https://github.com/...")

        mock_fetch.assert_called_once_with(
            current_version="1.0.0",
            latest_version="1.1.0",
            highlights_per_version=3,
        )
        assert self.console.print.called

    @patch("src.rxiv_maker.utils.changelog_parser.fetch_and_format_changelog")
    def test_show_update_info_changelog_error(self, mock_fetch):
        """Test update info when changelog unavailable."""
        mock_fetch.return_value = (None, "Network error")

        self.notifier.show_update_info("1.0.0", "1.1.0", "https://github.com/...")

        # Should show release URL as fallback
        assert self.console.print.called
        calls_text = " ".join(str(call) for call in self.console.print.call_args_list)
        assert "release notes" in calls_text.lower() or "github.com" in calls_text

    @patch("src.rxiv_maker.utils.changelog_parser.fetch_and_format_changelog")
    def test_show_update_info_breaking_changes(self, mock_fetch):
        """Test that breaking changes are highlighted prominently."""
        mock_fetch.return_value = (
            "⚠️ Breaking changes:\n• Removed old API\n✨ Added new feature",
            None,
        )

        self.notifier.show_update_info("1.0.0", "2.0.0", "https://github.com/...")

        # Verify breaking changes are printed with bold red style
        calls = self.console.print.call_args_list
        # Find calls with breaking change indicator
        breaking_calls = [c for c in calls if "⚠️" in str(c)]
        assert len(breaking_calls) > 0

    def test_show_installer_info(self):
        """Test installer info display."""
        self.notifier.show_installer_info("Homebrew", "brew update && brew upgrade rxiv-maker")

        assert self.console.print.called
        calls_text = " ".join(str(call) for call in self.console.print.call_args_list)
        assert "Homebrew" in calls_text
        assert "brew" in calls_text

    def test_show_success(self):
        """Test success message display."""
        self.notifier.show_success("1.1.0")

        assert self.console.print.called
        # Check for success indicators
        calls_text = " ".join(str(call) for call in self.console.print.call_args_list)
        assert "success" in calls_text.lower() or "✅" in calls_text
        assert "1.1.0" in calls_text

    def test_show_error_with_message(self):
        """Test error message display with error text."""
        self.notifier.show_error("Installation failed")

        assert self.console.print.called
        calls_text = " ".join(str(call) for call in self.console.print.call_args_list)
        assert "failed" in calls_text.lower() or "❌" in calls_text
        assert "Installation failed" in calls_text

    def test_show_error_without_message(self):
        """Test error message display without error text."""
        self.notifier.show_error(None)

        assert self.console.print.called
        calls_text = " ".join(str(call) for call in self.console.print.call_args_list)
        assert "failed" in calls_text.lower() or "❌" in calls_text

    def test_show_manual_instructions_homebrew(self):
        """Test manual instructions for Homebrew."""
        self.notifier.show_manual_instructions("homebrew")

        assert self.console.print.called
        calls_text = " ".join(str(call) for call in self.console.print.call_args_list)
        assert "brew" in calls_text

    def test_show_manual_instructions_pipx(self):
        """Test manual instructions for pipx."""
        self.notifier.show_manual_instructions("pipx")

        assert self.console.print.called
        calls_text = " ".join(str(call) for call in self.console.print.call_args_list)
        assert "pipx" in calls_text

    def test_show_manual_instructions_uv(self):
        """Test manual instructions for uv."""
        self.notifier.show_manual_instructions("uv")

        assert self.console.print.called
        calls_text = " ".join(str(call) for call in self.console.print.call_args_list)
        assert "uv tool" in calls_text

    def test_show_manual_instructions_pip(self):
        """Test manual instructions for pip."""
        self.notifier.show_manual_instructions("pip")

        assert self.console.print.called
        calls_text = " ".join(str(call) for call in self.console.print.call_args_list)
        assert "pip install" in calls_text

    def test_show_manual_instructions_dev(self):
        """Test manual instructions for dev installation."""
        self.notifier.show_manual_instructions("dev")

        assert self.console.print.called
        calls_text = " ".join(str(call) for call in self.console.print.call_args_list)
        assert "git pull" in calls_text

    @patch("src.rxiv_maker.utils.rich_upgrade_notifier.click.confirm")
    def test_confirm_upgrade_accepted(self, mock_confirm):
        """Test user confirms upgrade."""
        mock_confirm.return_value = True

        result = self.notifier.confirm_upgrade("1.1.0")

        assert result is True
        mock_confirm.assert_called_once()
        # Check that version is in the confirmation prompt
        call_args = mock_confirm.call_args[0]
        assert "1.1.0" in call_args[0]

    @patch("src.rxiv_maker.utils.rich_upgrade_notifier.click.confirm")
    def test_confirm_upgrade_declined(self, mock_confirm):
        """Test user declines upgrade."""
        mock_confirm.return_value = False

        result = self.notifier.confirm_upgrade("1.1.0")

        assert result is False
        mock_confirm.assert_called_once()

    @patch("src.rxiv_maker.utils.rich_upgrade_notifier.click.confirm")
    def test_confirm_upgrade_keyboard_interrupt(self, mock_confirm):
        """Test keyboard interrupt during confirmation."""
        mock_confirm.side_effect = KeyboardInterrupt()

        result = self.notifier.confirm_upgrade("1.1.0")

        assert result is False
        # Check that cancellation message was shown
        assert self.console.print.called
        calls_text = " ".join(str(call) for call in self.console.print.call_args_list)
        assert "cancel" in calls_text.lower()

    @patch("src.rxiv_maker.utils.rich_upgrade_notifier.click.confirm")
    def test_confirm_upgrade_eof_error(self, mock_confirm):
        """Test EOF error during confirmation."""
        mock_confirm.side_effect = EOFError()

        result = self.notifier.confirm_upgrade("1.1.0")

        assert result is False
        # Check that cancellation message was shown
        assert self.console.print.called
