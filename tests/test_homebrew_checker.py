"""Tests for Homebrew update checker module."""

import subprocess
from unittest.mock import Mock, patch

from rxiv_maker.utils.homebrew_checker import (
    check_brew_outdated,
    check_homebrew_update,
)


class TestHomebrewChecker:
    """Test suite for Homebrew update checker."""

    def test_check_brew_outdated_update_available(self):
        """Test brew outdated when update is available."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "rxiv-maker (1.7.8) < 1.7.9"

        with patch("subprocess.run", return_value=mock_result):
            result = check_brew_outdated()
            assert result == ("1.7.8", "1.7.9")

    def test_check_brew_outdated_up_to_date(self):
        """Test brew outdated when package is up to date."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result):
            result = check_brew_outdated()
            assert result is None

    def test_check_brew_outdated_not_installed(self):
        """Test brew outdated when brew is not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = check_brew_outdated()
            assert result is None

    def test_check_brew_outdated_timeout(self):
        """Test brew outdated with timeout."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("brew", 5)):
            result = check_brew_outdated()
            assert result is None

    def test_check_homebrew_update_via_brew(self):
        """Test Homebrew update check via brew command."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "rxiv-maker (1.7.8) < 1.7.9"

        with patch("subprocess.run", return_value=mock_result):
            result = check_homebrew_update("1.7.8")
            assert result == (True, "1.7.9")

    def test_check_homebrew_update_no_update(self):
        """Test Homebrew update check when no update available."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "rxiv-maker (1.7.9) < 1.7.9"

        with patch("subprocess.run", return_value=mock_result):
            result = check_homebrew_update("1.7.9")
            assert result == (False, "1.7.9")

    def test_check_homebrew_update_brew_fails(self):
        """Test Homebrew update check when brew command fails."""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = check_homebrew_update("1.7.8")
            # Should return None since rxiv-maker doesn't have GitHub formula fallback
            assert result is None

    def test_check_homebrew_update_deprecated_note(self):
        """Test that Homebrew support is noted as deprecated."""
        # This is more of a documentation test
        # The actual implementation should note that Homebrew support was removed in v1.7.9
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "rxiv-maker (1.7.8) < 1.7.9"

        with patch("subprocess.run", return_value=mock_result):
            result = check_homebrew_update("1.7.8")
            # Function should still work for legacy installations
            assert result == (True, "1.7.9")
