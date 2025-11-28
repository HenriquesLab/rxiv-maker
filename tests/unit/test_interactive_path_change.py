"""Unit tests for prompt_confirm_with_path_change function."""

import os
from pathlib import Path
from unittest.mock import patch

from rxiv_maker.cli.interactive import prompt_confirm_with_path_change


class TestPromptConfirmWithPathChange:
    """Test suite for prompt_confirm_with_path_change function."""

    def test_proceed_with_current_path(self):
        """Test user selects 'Yes, proceed' with current path."""
        current_path = Path("/test/path")

        with patch("rxiv_maker.cli.interactive.prompt_choice") as mock_choice:
            mock_choice.return_value = 0  # Select "Yes, proceed"

            proceed, final_path = prompt_confirm_with_path_change(
                current_path=current_path,
                action_description="Test action",
            )

            assert proceed is True
            assert final_path == current_path
            mock_choice.assert_called_once()

    def test_cancel_operation(self):
        """Test user selects 'Cancel'."""
        current_path = Path("/test/path")

        with patch("rxiv_maker.cli.interactive.prompt_choice") as mock_choice:
            mock_choice.return_value = 2  # Select "Cancel"

            proceed, final_path = prompt_confirm_with_path_change(
                current_path=current_path,
                action_description="Test action",
            )

            assert proceed is False
            assert final_path is None
            mock_choice.assert_called_once()

    def test_keyboard_interrupt_at_menu(self):
        """Test Ctrl+C at main menu cancels operation."""
        current_path = Path("/test/path")

        with patch("rxiv_maker.cli.interactive.prompt_choice") as mock_choice:
            mock_choice.side_effect = KeyboardInterrupt()

            proceed, final_path = prompt_confirm_with_path_change(
                current_path=current_path,
                action_description="Test action",
            )

            assert proceed is False
            assert final_path is None

    def test_change_to_existing_directory(self, tmp_path):
        """Test changing to an existing directory with write permission."""
        current_path = Path("/test/current")
        new_path = tmp_path / "new_dir"
        new_path.mkdir()

        with (
            patch("rxiv_maker.cli.interactive.prompt_choice") as mock_choice,
            patch("rxiv_maker.cli.interactive.prompt_path") as mock_path,
            patch("os.access") as mock_access,
        ):
            # First call: select "Change path", second call: select "Yes, proceed"
            mock_choice.side_effect = [1, 0]
            mock_path.return_value = new_path
            mock_access.return_value = True  # Has write permission

            proceed, final_path = prompt_confirm_with_path_change(
                current_path=current_path,
                action_description="Test action",
            )

            assert proceed is True
            assert final_path == new_path
            assert mock_choice.call_count == 2
            mock_path.assert_called_once()
            mock_access.assert_called_once_with(new_path, os.W_OK)

    def test_change_to_nonexistent_directory_create(self, tmp_path):
        """Test changing to non-existent directory and creating it."""
        current_path = Path("/test/current")
        new_path = tmp_path / "new_dir" / "subdir"

        with (
            patch("rxiv_maker.cli.interactive.prompt_choice") as mock_choice,
            patch("rxiv_maker.cli.interactive.prompt_path") as mock_path,
            patch("rxiv_maker.cli.interactive.prompt_confirm") as mock_confirm,
            patch("os.access") as mock_access,
        ):
            # First call: select "Change path", second call: select "Yes, proceed"
            mock_choice.side_effect = [1, 0]
            mock_path.return_value = new_path
            mock_confirm.return_value = True  # Confirm directory creation
            mock_access.return_value = True  # Has write permission

            proceed, final_path = prompt_confirm_with_path_change(
                current_path=current_path,
                action_description="Test action",
            )

            assert proceed is True
            assert final_path == new_path
            assert new_path.exists()  # Directory was created
            mock_confirm.assert_called_once()

    def test_change_to_nonexistent_directory_decline_creation(self):
        """Test changing to non-existent directory but declining creation."""
        current_path = Path("/test/current")
        new_path = Path("/test/nonexistent")

        with (
            patch("rxiv_maker.cli.interactive.prompt_choice") as mock_choice,
            patch("rxiv_maker.cli.interactive.prompt_path") as mock_path,
            patch("rxiv_maker.cli.interactive.prompt_confirm") as mock_confirm,
        ):
            # First call: select "Change path"
            # Second call: select "Cancel" (after declining creation)
            mock_choice.side_effect = [1, 2]
            mock_path.return_value = new_path
            mock_confirm.return_value = False  # Decline directory creation

            proceed, final_path = prompt_confirm_with_path_change(
                current_path=current_path,
                action_description="Test action",
            )

            assert proceed is False
            assert final_path is None
            assert mock_choice.call_count == 2
            mock_confirm.assert_called_once()

    def test_permission_denied_on_existing_directory(self, tmp_path):
        """Test permission denied on existing directory."""
        current_path = Path("/test/current")
        new_path = tmp_path / "restricted"
        new_path.mkdir()

        with (
            patch("rxiv_maker.cli.interactive.prompt_choice") as mock_choice,
            patch("rxiv_maker.cli.interactive.prompt_path") as mock_path,
            patch("os.access") as mock_access,
        ):
            # First call: select "Change path"
            # Second call: select "Cancel" (after permission error)
            mock_choice.side_effect = [1, 2]
            mock_path.return_value = new_path
            mock_access.return_value = False  # No write permission

            proceed, final_path = prompt_confirm_with_path_change(
                current_path=current_path,
                action_description="Test action",
            )

            assert proceed is False
            assert final_path is None
            assert mock_choice.call_count == 2
            mock_access.assert_called_once_with(new_path, os.W_OK)

    def test_directory_creation_permission_error(self):
        """Test handling PermissionError during directory creation."""
        current_path = Path("/test/current")
        new_path = Path("/test/restricted/new")

        with (
            patch("rxiv_maker.cli.interactive.prompt_choice") as mock_choice,
            patch("rxiv_maker.cli.interactive.prompt_path") as mock_path,
            patch("rxiv_maker.cli.interactive.prompt_confirm") as mock_confirm,
        ):
            # First call: select "Change path"
            # Second call: select "Cancel" (after creation error)
            mock_choice.side_effect = [1, 2]
            mock_path.return_value = new_path
            mock_confirm.return_value = True  # Confirm directory creation

            # Mock Path.mkdir to raise PermissionError
            with patch.object(Path, "mkdir") as mock_mkdir:
                mock_mkdir.side_effect = PermissionError("Permission denied")

                proceed, final_path = prompt_confirm_with_path_change(
                    current_path=current_path,
                    action_description="Test action",
                )

                assert proceed is False
                assert final_path is None
                mock_mkdir.assert_called_once()

    def test_directory_creation_generic_error(self):
        """Test handling generic Exception during directory creation."""
        current_path = Path("/test/current")
        new_path = Path("/test/error/new")

        with (
            patch("rxiv_maker.cli.interactive.prompt_choice") as mock_choice,
            patch("rxiv_maker.cli.interactive.prompt_path") as mock_path,
            patch("rxiv_maker.cli.interactive.prompt_confirm") as mock_confirm,
        ):
            # First call: select "Change path"
            # Second call: select "Cancel" (after creation error)
            mock_choice.side_effect = [1, 2]
            mock_path.return_value = new_path
            mock_confirm.return_value = True  # Confirm directory creation

            # Mock Path.mkdir to raise generic Exception
            with patch.object(Path, "mkdir") as mock_mkdir:
                mock_mkdir.side_effect = Exception("Disk full")

                proceed, final_path = prompt_confirm_with_path_change(
                    current_path=current_path,
                    action_description="Test action",
                )

                assert proceed is False
                assert final_path is None
                mock_mkdir.assert_called_once()

    def test_keyboard_interrupt_during_path_input(self):
        """Test Ctrl+C during path input goes back to menu."""
        current_path = Path("/test/current")

        with (
            patch("rxiv_maker.cli.interactive.prompt_choice") as mock_choice,
            patch("rxiv_maker.cli.interactive.prompt_path") as mock_path,
        ):
            # First call: select "Change path", second call: select "Cancel"
            mock_choice.side_effect = [1, 2]
            mock_path.side_effect = KeyboardInterrupt()

            proceed, final_path = prompt_confirm_with_path_change(
                current_path=current_path,
                action_description="Test action",
            )

            assert proceed is False
            assert final_path is None
            assert mock_choice.call_count == 2

    def test_multiple_path_changes(self, tmp_path):
        """Test changing path multiple times before confirming."""
        current_path = Path("/test/current")
        first_new_path = tmp_path / "first"
        second_new_path = tmp_path / "second"
        first_new_path.mkdir()
        second_new_path.mkdir()

        with (
            patch("rxiv_maker.cli.interactive.prompt_choice") as mock_choice,
            patch("rxiv_maker.cli.interactive.prompt_path") as mock_path,
            patch("os.access") as mock_access,
        ):
            # Select "Change path" twice, then "Yes, proceed"
            mock_choice.side_effect = [1, 1, 0]
            mock_path.side_effect = [first_new_path, second_new_path]
            mock_access.return_value = True  # Has write permission

            proceed, final_path = prompt_confirm_with_path_change(
                current_path=current_path,
                action_description="Test action",
            )

            assert proceed is True
            assert final_path == second_new_path
            assert mock_choice.call_count == 3
            assert mock_path.call_count == 2

    def test_action_description_in_menu(self):
        """Test that action_description is used in menu text."""
        current_path = Path("/test/path")
        action_description = "Clone repositories"

        with patch("rxiv_maker.cli.interactive.prompt_choice") as mock_choice:
            mock_choice.return_value = 0  # Select "Yes, proceed"

            prompt_confirm_with_path_change(
                current_path=current_path,
                action_description=action_description,
            )

            # Verify the action description was used in the choices
            call_args = mock_choice.call_args
            choices = call_args[0][0]  # First positional argument
            assert any(action_description.lower() in choice.lower() for choice in choices)

    def test_default_action_description(self):
        """Test default action_description parameter."""
        current_path = Path("/test/path")

        with patch("rxiv_maker.cli.interactive.prompt_choice") as mock_choice:
            mock_choice.return_value = 0  # Select "Yes, proceed"

            prompt_confirm_with_path_change(current_path=current_path)

            # Verify the default action description is used
            call_args = mock_choice.call_args
            choices = call_args[0][0]
            assert any("clone repositories" in choice.lower() for choice in choices)

    def test_path_displayed_correctly(self, tmp_path):
        """Test that the current path is displayed correctly in the menu."""
        current_path = tmp_path / "manuscripts"
        current_path.mkdir()

        with (
            patch("rxiv_maker.cli.interactive.prompt_choice") as mock_choice,
            patch("rxiv_maker.cli.interactive.console") as mock_console,
        ):
            mock_choice.return_value = 0  # Select "Yes, proceed"

            prompt_confirm_with_path_change(
                current_path=current_path,
                action_description="Test action",
            )

            # Verify console.print was called with the path
            mock_console.print.assert_called()
            print_calls = [str(call) for call in mock_console.print.call_args_list]
            assert any(str(current_path) in str(call) for call in print_calls)

    def test_path_updated_message_shown(self, tmp_path):
        """Test that path change confirmation message is shown."""
        current_path = Path("/test/current")
        new_path = tmp_path / "new_dir"
        new_path.mkdir()

        with (
            patch("rxiv_maker.cli.interactive.prompt_choice") as mock_choice,
            patch("rxiv_maker.cli.interactive.prompt_path") as mock_path,
            patch("os.access") as mock_access,
            patch("rxiv_maker.cli.interactive.console") as mock_console,
        ):
            # First call: select "Change path", second call: select "Yes, proceed"
            mock_choice.side_effect = [1, 0]
            mock_path.return_value = new_path
            mock_access.return_value = True

            prompt_confirm_with_path_change(
                current_path=current_path,
                action_description="Test action",
            )

            # Verify success message was shown
            print_calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("✓" in str(call) and "Path changed" in str(call) for call in print_calls)
