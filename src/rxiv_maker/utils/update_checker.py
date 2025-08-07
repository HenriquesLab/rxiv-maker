"""Version update checking for rxiv-maker.

This module handles checking for newer versions of rxiv-maker on PyPI
and notifying users about available updates in a non-intrusive way.
"""

import json
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

try:
    from packaging import version as pkg_version  # type: ignore
except ImportError:
    pkg_version = None  # type: ignore

from rich.console import Console

from rxiv_maker.utils.unicode_safe import get_safe_icon, safe_print

from .cache_utils import get_cache_dir, migrate_cache_file

console = Console()


class UpdateChecker:
    """Handles version checking and update notifications."""

    def __init__(self, package_name: str = "rxiv-maker", current_version: str | None = None):
        """Initialize the update checker.

        Args:
            package_name: Name of the package on PyPI
            current_version: Current version of the package
        """
        self.package_name = package_name
        self.current_version = current_version or self._get_current_version()
        self.pypi_url = f"https://pypi.org/pypi/{package_name}/json"

        # Use standardized cache directory
        self.cache_dir = get_cache_dir("updates")
        self.cache_file = self.cache_dir / "update_cache.json"

        # Handle migration from legacy location
        self._migrate_legacy_cache()

        self.check_interval = timedelta(hours=24)  # Check once per day

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _migrate_legacy_cache(self) -> None:
        """Migrate cache file from legacy location if it exists."""
        legacy_cache_dir = Path.home() / ".rxiv"
        legacy_cache_file = legacy_cache_dir / "update_cache.json"

        if legacy_cache_file.exists():
            try:
                migrate_cache_file(legacy_cache_file, self.cache_file)
                # Try to remove empty legacy directory
                try:
                    legacy_cache_dir.rmdir()
                except OSError:
                    # Directory not empty, leave it alone
                    pass
            except Exception:
                # Migration failed, continue with new location
                pass

    def _get_current_version(self) -> str:
        """Get the current version of the package."""
        try:
            from .. import __version__

            return __version__
        except ImportError:
            return "unknown"

    def should_check_for_updates(self) -> bool:
        """Determine if we should check for updates.

        Returns:
            bool: True if we should check for updates, False otherwise
        """
        # Check environment variables for opt-out
        if os.getenv("RXIV_NO_UPDATE_CHECK", "").lower() in ("1", "true", "yes"):
            return False

        if os.getenv("NO_UPDATE_NOTIFIER", ""):
            return False

        # Check configuration (will be implemented when config integration is added)
        try:
            from ..cli.config import config

            if not config.get("general.check_updates", True):
                return False
        except (ImportError, AttributeError):
            # Config not available or check_updates setting not set
            pass

        # Check if enough time has passed since last check
        cache_data = self._load_cache()
        if cache_data:
            last_check = datetime.fromisoformat(cache_data.get("last_check", ""))
            if datetime.now() - last_check < self.check_interval:
                return False

        return True

    def _load_cache(self) -> dict | None:
        """Load cached update information.

        Returns:
            Dict or None: Cached data if available and valid
        """
        try:
            if self.cache_file.exists():
                with open(self.cache_file, encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
        return None

    def _save_cache(self, data: dict) -> None:
        """Save update information to cache.

        Args:
            data: Data to cache
        """
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass  # Ignore cache write failures

    def _fetch_latest_version(self) -> str | None:
        """Fetch the latest version from PyPI.

        Returns:
            str or None: Latest version if available
        """
        try:
            with urlopen(self.pypi_url, timeout=5) as response:
                data = json.loads(response.read().decode())
                return data["info"]["version"]
        except (URLError, HTTPError, json.JSONDecodeError, KeyError):
            return None

    def _compare_versions(self, current: str, latest: str) -> bool:
        """Compare two version strings.

        Args:
            current: Current version string
            latest: Latest version string

        Returns:
            bool: True if latest is newer than current
        """
        if pkg_version is None:
            # Fallback to simple string comparison if packaging not available
            return latest != current

        try:
            return pkg_version.parse(latest) > pkg_version.parse(current)
        except pkg_version.InvalidVersion:
            # Fallback to string comparison for invalid versions
            return latest != current

    def check_for_updates_async(self) -> None:
        """Check for updates in a background thread."""
        if not self.should_check_for_updates():
            return

        def _check():
            self._check_and_cache_update()

        # Run check in background thread to avoid blocking CLI
        thread = threading.Thread(target=_check, daemon=True)
        thread.start()

    def _check_and_cache_update(self) -> None:
        """Check for updates and cache the result."""
        latest_version = self._fetch_latest_version()
        now = datetime.now()

        cache_data = {
            "last_check": now.isoformat(),
            "latest_version": latest_version,
            "current_version": self.current_version,
            "update_available": False,
        }

        if latest_version and self.current_version != "unknown":
            cache_data["update_available"] = self._compare_versions(self.current_version, latest_version)

        self._save_cache(cache_data)

    def get_update_notification(self) -> str | None:
        """Get update notification message if an update is available.

        Returns:
            str or None: Notification message if update available
        """
        cache_data = self._load_cache()
        if not cache_data or not cache_data.get("update_available"):
            return None

        current = cache_data.get("current_version", "unknown")
        latest = cache_data.get("latest_version", "unknown")

        if current == "unknown" or latest == "unknown":
            return None

        # Format the notification message with safe icons
        package_icon = get_safe_icon("📦", "[UPDATE]")
        notification_lines = [
            f"{package_icon} Update available: {self.package_name} v{current} → v{latest}",
            f"   Run: pip install --upgrade {self.package_name}",
            f"   Release notes: https://github.com/henriqueslab/rxiv-maker/releases/tag/v{latest}",
        ]

        return "\n".join(notification_lines)

    def show_update_notification(self) -> None:
        """Show update notification if available."""
        notification = self.get_update_notification()
        if notification:
            try:
                console.print(f"\n{notification}", style="blue")
            except Exception:
                # Fallback to safe print for environments with encoding issues
                safe_print(f"\n{notification}")

    def force_check(self) -> tuple[bool, str | None]:
        """Force an immediate update check.

        Returns:
            Tuple[bool, Optional[str]]: (update_available, latest_version)
        """
        latest_version = self._fetch_latest_version()

        if not latest_version:
            return False, None

        if self.current_version == "unknown":
            return False, latest_version

        update_available = self._compare_versions(self.current_version, latest_version)

        # Update cache with forced check
        cache_data = {
            "last_check": datetime.now().isoformat(),
            "latest_version": latest_version,
            "current_version": self.current_version,
            "update_available": update_available,
        }
        self._save_cache(cache_data)

        return update_available, latest_version


# Global instance for easy access
_update_checker = None


def get_update_checker() -> UpdateChecker:
    """Get the global update checker instance."""
    global _update_checker
    if _update_checker is None:
        _update_checker = UpdateChecker()
    return _update_checker


def check_for_updates_async() -> None:
    """Convenience function to check for updates asynchronously."""
    checker = get_update_checker()
    checker.check_for_updates_async()


def show_update_notification() -> None:
    """Convenience function to show update notification if available."""
    checker = get_update_checker()
    checker.show_update_notification()


def force_update_check() -> tuple[bool, str | None]:
    """Convenience function to force an update check.

    Returns:
        Tuple[bool, Optional[str]]: (update_available, latest_version)
    """
    checker = get_update_checker()
    return checker.force_check()
