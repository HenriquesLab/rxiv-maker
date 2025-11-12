"""Tests for update checker functionality."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import URLError

from src.rxiv_maker.utils.update_checker import UpdateChecker, get_update_checker


class TestUpdateChecker:
    """Test UpdateChecker class."""

    def setup_method(self):
        """Set up test environment."""
        self.package_name = "test-package"
        self.current_version = "1.0.0"

    def test_init(self):
        """Test UpdateChecker initialization."""
        checker = UpdateChecker(self.package_name, self.current_version)
        assert checker.package_name == self.package_name
        assert checker.current_version == self.current_version
        assert checker.pypi_url == f"https://pypi.org/pypi/{self.package_name}/json"

    def test_should_check_for_updates_env_var_opt_out(self):
        """Test opt-out via environment variable."""
        checker = UpdateChecker(self.package_name, self.current_version)

        with patch.dict("os.environ", {"RXIV_NO_UPDATE_CHECK": "1"}):
            assert not checker.should_check_for_updates()

        with patch.dict("os.environ", {"NO_UPDATE_NOTIFIER": "1"}):
            assert not checker.should_check_for_updates()

    def test_should_check_for_updates_time_interval(self):
        """Test time interval checking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / ".rxiv"
            cache_dir.mkdir()
            cache_file = cache_dir / "update_cache.json"

            checker = UpdateChecker(self.package_name, self.current_version)
            checker.cache_dir = cache_dir
            checker.cache_file = cache_file

            # No cache file - should check
            assert checker.should_check_for_updates()

            # Recent check - should not check
            recent_cache = {
                "last_check": datetime.now().isoformat(),
                "latest_version": "1.1.0",
                "update_available": True,
            }
            with open(cache_file, "w") as f:
                json.dump(recent_cache, f)

            assert not checker.should_check_for_updates()

            # Old check - should check
            old_cache = {
                "last_check": (datetime.now() - timedelta(days=2)).isoformat(),
                "latest_version": "1.1.0",
                "update_available": True,
            }
            with open(cache_file, "w") as f:
                json.dump(old_cache, f)

            assert checker.should_check_for_updates()

    def test_load_cache_valid(self):
        """Test loading valid cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / ".rxiv"
            cache_dir.mkdir()
            cache_file = cache_dir / "update_cache.json"

            checker = UpdateChecker(self.package_name, self.current_version)
            checker.cache_dir = cache_dir
            checker.cache_file = cache_file

            test_data = {"test": "data"}
            with open(cache_file, "w") as f:
                json.dump(test_data, f)

            result = checker._load_cache()
            assert result == test_data

    def test_load_cache_invalid(self):
        """Test loading invalid cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / ".rxiv"
            cache_dir.mkdir()
            cache_file = cache_dir / "update_cache.json"

            checker = UpdateChecker(self.package_name, self.current_version)
            checker.cache_dir = cache_dir
            checker.cache_file = cache_file

            # Invalid JSON
            with open(cache_file, "w") as f:
                f.write("invalid json")

            result = checker._load_cache()
            assert result is None

            # Non-existent file
            cache_file.unlink()
            result = checker._load_cache()
            assert result is None

    def test_save_cache(self):
        """Test saving cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / ".rxiv"
            cache_dir.mkdir()
            cache_file = cache_dir / "update_cache.json"

            checker = UpdateChecker(self.package_name, self.current_version)
            checker.cache_dir = cache_dir
            checker.cache_file = cache_file

            test_data = {"test": "data"}
            checker._save_cache(test_data)

            with open(cache_file) as f:
                result = json.load(f)

            assert result == test_data

    @patch("src.rxiv_maker.utils.update_checker.urlopen")
    def test_fetch_latest_version_success(self, mock_urlopen):
        """Test successful version fetching."""
        mock_response = Mock()
        mock_response.read.return_value = b'{"info": {"version": "1.2.0"}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        checker = UpdateChecker(self.package_name, self.current_version)
        result = checker._fetch_latest_version()

        assert result == "1.2.0"
        mock_urlopen.assert_called_once_with(checker.pypi_url, timeout=5)

    @patch("src.rxiv_maker.utils.update_checker.urlopen")
    def test_fetch_latest_version_failure(self, mock_urlopen):
        """Test failed version fetching."""
        mock_urlopen.side_effect = URLError("Network error")

        checker = UpdateChecker(self.package_name, self.current_version)
        result = checker._fetch_latest_version()

        assert result is None

    def test_compare_versions_with_packaging(self):
        """Test version comparison with packaging library."""
        checker = UpdateChecker(self.package_name, self.current_version)

        # Newer version
        assert checker._compare_versions("1.0.0", "1.1.0")
        assert checker._compare_versions("1.0.0", "2.0.0")

        # Same version
        assert not checker._compare_versions("1.0.0", "1.0.0")

        # Older version
        assert not checker._compare_versions("1.1.0", "1.0.0")

    def test_compare_versions_fallback(self):
        """Test version comparison fallback."""
        checker = UpdateChecker(self.package_name, self.current_version)

        with patch("src.rxiv_maker.utils.update_checker.pkg_version", None):
            # Should fall back to string comparison
            assert checker._compare_versions("1.0.0", "1.1.0")  # Different = newer
            assert not checker._compare_versions("1.0.0", "1.0.0")  # Same = not newer

    @patch("src.rxiv_maker.utils.update_checker.detect_install_method")
    def test_get_update_notification_available(self, mock_detect):
        """Test update notification when update is available."""
        mock_detect.return_value = "pip"

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / ".rxiv"
            cache_dir.mkdir()
            cache_file = cache_dir / "update_cache.json"

            checker = UpdateChecker(self.package_name, self.current_version)
            checker.cache_dir = cache_dir
            checker.cache_file = cache_file

            cache_data = {
                "last_check": datetime.now().isoformat(),
                "latest_version": "1.2.0",
                "current_version": "1.0.0",
                "update_available": True,
            }
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)

            notification = checker.get_update_notification()
            assert notification is not None
            assert "v1.0.0 → v1.2.0" in notification
            assert "pip install --upgrade" in notification
            assert "release notes" in notification.lower()

    def test_get_update_notification_not_available(self):
        """Test update notification when no update is available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / ".rxiv"
            cache_dir.mkdir()
            cache_file = cache_dir / "update_cache.json"

            checker = UpdateChecker(self.package_name, self.current_version)
            checker.cache_dir = cache_dir
            checker.cache_file = cache_file

            cache_data = {
                "last_check": datetime.now().isoformat(),
                "latest_version": "1.0.0",
                "current_version": "1.0.0",
                "update_available": False,
            }
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)

            notification = checker.get_update_notification()
            assert notification is None

    @patch("src.rxiv_maker.utils.update_checker.urlopen")
    def test_force_check(self, mock_urlopen):
        """Test force check functionality."""
        mock_response = Mock()
        mock_response.read.return_value = b'{"info": {"version": "1.2.0"}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / ".rxiv"
            cache_dir.mkdir()

            checker = UpdateChecker(self.package_name, self.current_version)
            checker.cache_dir = cache_dir
            checker.cache_file = cache_dir / "update_cache.json"

            update_available, latest_version = checker.force_check()

            assert update_available
            assert latest_version == "1.2.0"

            # Check that cache was updated
            cache_data = checker._load_cache()
            assert cache_data["update_available"]
            assert cache_data["latest_version"] == "1.2.0"

    def test_check_for_updates_async(self):
        """Test async update checking."""
        checker = UpdateChecker(self.package_name, self.current_version)

        with patch.object(checker, "should_check_for_updates", return_value=False):
            # Should not start thread if checking is disabled
            with patch("threading.Thread") as mock_thread:
                checker.check_for_updates_async()
                mock_thread.assert_not_called()

        with patch.object(checker, "should_check_for_updates", return_value=True):
            # Should start thread if checking is enabled
            with patch("threading.Thread") as mock_thread:
                checker.check_for_updates_async()
                mock_thread.assert_called_once()
                mock_thread.return_value.start.assert_called_once()


class TestGlobalFunctions:
    """Test global convenience functions."""

    def test_get_update_checker_singleton(self):
        """Test that get_update_checker returns singleton."""
        checker1 = get_update_checker()
        checker2 = get_update_checker()
        assert checker1 is checker2

    @patch("src.rxiv_maker.utils.update_checker.get_update_checker")
    def test_check_for_updates_async(self, mock_get_checker):
        """Test global check_for_updates_async function."""
        mock_checker = Mock()
        mock_get_checker.return_value = mock_checker

        from src.rxiv_maker.utils.update_checker import check_for_updates_async

        check_for_updates_async()

        mock_checker.check_for_updates_async.assert_called_once()

    @patch("src.rxiv_maker.utils.update_checker.get_update_checker")
    def test_show_update_notification(self, mock_get_checker):
        """Test global show_update_notification function."""
        mock_checker = Mock()
        mock_get_checker.return_value = mock_checker

        from src.rxiv_maker.utils.update_checker import show_update_notification

        show_update_notification()

        mock_checker.show_update_notification.assert_called_once()

    @patch("src.rxiv_maker.utils.update_checker.get_update_checker")
    def test_force_update_check(self, mock_get_checker):
        """Test global force_update_check function."""
        mock_checker = Mock()
        mock_checker.force_check.return_value = (True, "1.2.0")
        mock_get_checker.return_value = mock_checker

        from src.rxiv_maker.utils.update_checker import force_update_check

        result = force_update_check()

        assert result == (True, "1.2.0")
        mock_checker.force_check.assert_called_once()


class TestInstallDetectionIntegration:
    """Test installation detection integration with update notifications."""

    def setup_method(self):
        """Set up test environment."""
        self.package_name = "test-package"
        self.current_version = "1.0.0"

    @patch("src.rxiv_maker.utils.update_checker.detect_install_method")
    def test_update_notification_pip(self, mock_detect):
        """Test update notification for pip installation."""
        mock_detect.return_value = "pip"

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / ".rxiv"
            cache_dir.mkdir()
            cache_file = cache_dir / "update_cache.json"

            checker = UpdateChecker(self.package_name, self.current_version)
            checker.cache_dir = cache_dir
            checker.cache_file = cache_file

            cache_data = {
                "last_check": datetime.now().isoformat(),
                "latest_version": "1.2.0",
                "current_version": "1.0.0",
                "update_available": True,
            }
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)

            notification = checker.get_update_notification()
            assert notification is not None
            assert "pip install --upgrade" in notification
            assert "Installed via: pip" in notification

    @patch("src.rxiv_maker.utils.update_checker.detect_install_method")
    def test_update_notification_homebrew(self, mock_detect):
        """Test update notification for Homebrew installation."""
        mock_detect.return_value = "homebrew"

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / ".rxiv"
            cache_dir.mkdir()
            cache_file = cache_dir / "update_cache.json"

            checker = UpdateChecker(self.package_name, self.current_version)
            checker.cache_dir = cache_dir
            checker.cache_file = cache_file

            cache_data = {
                "last_check": datetime.now().isoformat(),
                "latest_version": "1.2.0",
                "current_version": "1.0.0",
                "update_available": True,
            }
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)

            notification = checker.get_update_notification()
            assert notification is not None
            assert "brew update && brew upgrade" in notification
            assert "Installed via: Homebrew" in notification

    @patch("src.rxiv_maker.utils.update_checker.detect_install_method")
    def test_update_notification_uv(self, mock_detect):
        """Test update notification for uv installation."""
        mock_detect.return_value = "uv"

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / ".rxiv"
            cache_dir.mkdir()
            cache_file = cache_dir / "update_cache.json"

            checker = UpdateChecker(self.package_name, self.current_version)
            checker.cache_dir = cache_dir
            checker.cache_file = cache_file

            cache_data = {
                "last_check": datetime.now().isoformat(),
                "latest_version": "1.2.0",
                "current_version": "1.0.0",
                "update_available": True,
            }
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)

            notification = checker.get_update_notification()
            assert notification is not None
            assert "uv tool upgrade" in notification
            assert "Installed via: uv tool" in notification

    @patch("src.rxiv_maker.utils.update_checker.detect_install_method")
    def test_update_notification_pipx(self, mock_detect):
        """Test update notification for pipx installation."""
        mock_detect.return_value = "pipx"

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / ".rxiv"
            cache_dir.mkdir()
            cache_file = cache_dir / "update_cache.json"

            checker = UpdateChecker(self.package_name, self.current_version)
            checker.cache_dir = cache_dir
            checker.cache_file = cache_file

            cache_data = {
                "last_check": datetime.now().isoformat(),
                "latest_version": "1.2.0",
                "current_version": "1.0.0",
                "update_available": True,
            }
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)

            notification = checker.get_update_notification()
            assert notification is not None
            assert "pipx upgrade" in notification
            assert "Installed via: pipx" in notification

    @patch("src.rxiv_maker.utils.update_checker.detect_install_method")
    @patch("src.rxiv_maker.utils.update_checker.check_homebrew_update")
    def test_homebrew_preferred_check(self, mock_homebrew_check, mock_detect):
        """Test that Homebrew update checker is used for Homebrew installations."""
        mock_detect.return_value = "homebrew"
        mock_homebrew_check.return_value = (True, "1.2.0")

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / ".rxiv"
            cache_dir.mkdir()

            checker = UpdateChecker(self.package_name, self.current_version)
            checker.cache_dir = cache_dir
            checker.cache_file = cache_dir / "update_cache.json"

            checker._check_and_cache_update()

            # Verify Homebrew checker was called
            mock_homebrew_check.assert_called_once_with(self.current_version)

            # Verify cache was updated with Homebrew results
            cache_data = checker._load_cache()
            assert cache_data["update_available"]
            assert cache_data["latest_version"] == "1.2.0"

    @patch("src.rxiv_maker.utils.update_checker.detect_install_method")
    @patch("src.rxiv_maker.utils.update_checker.check_homebrew_update")
    @patch("src.rxiv_maker.utils.update_checker.UpdateChecker._fetch_latest_version")
    def test_fallback_to_pypi_for_non_homebrew(self, mock_fetch, mock_homebrew_check, mock_detect):
        """Test that PyPI is used for non-Homebrew installations."""
        mock_detect.return_value = "pip"
        mock_fetch.return_value = "1.2.0"

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / ".rxiv"
            cache_dir.mkdir()

            checker = UpdateChecker(self.package_name, self.current_version)
            checker.cache_dir = cache_dir
            checker.cache_file = cache_dir / "update_cache.json"

            checker._check_and_cache_update()

            # Verify Homebrew checker was NOT called
            mock_homebrew_check.assert_not_called()

            # Verify PyPI was called
            mock_fetch.assert_called_once()

            # Verify cache was updated
            cache_data = checker._load_cache()
            assert cache_data["latest_version"] == "1.2.0"
