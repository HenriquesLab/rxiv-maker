"""Tests for installation detection module."""

from unittest.mock import MagicMock, patch

from rxiv_maker.utils.install_detector import (
    detect_install_method,
    get_friendly_install_name,
    get_upgrade_command,
)


class TestInstallDetector:
    """Test suite for install detector."""

    def test_homebrew_detection_apple_silicon(self):
        """Test Homebrew detection on Apple Silicon Mac."""
        with patch("sys.executable", "/opt/homebrew/Cellar/rxiv-maker/1.7.8/bin/python3"):
            result = detect_install_method()
            assert result == "homebrew"

    def test_homebrew_detection_intel(self):
        """Test Homebrew detection on Intel Mac."""
        with patch("sys.executable", "/usr/local/Cellar/rxiv-maker/1.7.8/bin/python3"):
            result = detect_install_method()
            assert result == "homebrew"

    def test_pipx_detection(self):
        """Test pipx installation detection."""
        with patch(
            "sys.executable",
            "/home/user/.local/pipx/venvs/rxiv-maker/bin/python",
        ):
            result = detect_install_method()
            assert result == "pipx"

    def test_uv_detection(self):
        """Test uv tool installation detection."""
        with patch(
            "sys.executable",
            "/home/user/.local/share/uv/tools/rxiv-maker/bin/python",
        ):
            result = detect_install_method()
            assert result == "uv"

    def test_pip_detection(self):
        """Test pip installation detection."""
        # Mock both sys.executable and the package path to avoid dev detection
        mock_path = MagicMock()
        mock_path.exists.return_value = False  # No .git directory
        mock_path.glob.return_value = []  # No .egg-info files

        with patch("sys.executable", "/usr/lib/python3.11/site-packages/python"):
            with patch("pathlib.Path.exists", return_value=False):
                with patch("pathlib.Path.glob", return_value=[]):
                    result = detect_install_method()
                    assert result == "pip"

    def test_get_upgrade_command_homebrew(self):
        """Test upgrade command for Homebrew."""
        cmd = get_upgrade_command("homebrew")
        assert cmd == "brew update && brew upgrade rxiv-maker"

    def test_get_upgrade_command_pipx(self):
        """Test upgrade command for pipx."""
        cmd = get_upgrade_command("pipx")
        assert cmd == "pipx upgrade rxiv-maker"

    def test_get_upgrade_command_uv(self):
        """Test upgrade command for uv."""
        cmd = get_upgrade_command("uv")
        assert cmd == "uv tool upgrade rxiv-maker"

    def test_get_friendly_name_homebrew(self):
        """Test friendly name for Homebrew."""
        name = get_friendly_install_name("homebrew")
        assert name == "Homebrew"

    def test_get_friendly_name_pipx(self):
        """Test friendly name for pipx."""
        name = get_friendly_install_name("pipx")
        assert name == "pipx"

    def test_get_friendly_name_unknown(self):
        """Test friendly name for unknown method."""
        name = get_friendly_install_name("unknown")
        assert name == "Unknown"
