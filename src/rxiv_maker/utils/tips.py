"""Tips and tricks system for Rxiv-Maker CLI.

This module provides helpful tips to users after successful operations,
including recommendations for tools like the VSCode extension.
"""

import random
import time
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from ..processors.yaml_processor import parse_yaml_simple


class TipsManager:
    """Manages display and selection of user tips.

    The tips system uses a priority-based selection algorithm:
    - Tips with priority >= HIGH_PRIORITY_THRESHOLD are considered high priority
    - High priority tips have HIGH_PRIORITY_CHANCE probability of being selected
    - Priority scale is typically 1-10, where higher numbers indicate higher priority
    - Fallback tips use DEFAULT_FALLBACK_PRIORITY
    """

    # Configuration constants
    HIGH_PRIORITY_THRESHOLD = 5
    HIGH_PRIORITY_CHANCE = 0.7  # 70% chance to select high priority tips
    DEFAULT_FALLBACK_PRIORITY = 1

    def __init__(self, tips_file: Optional[Path] = None):
        """Initialize the tips manager.

        Args:
            tips_file: Path to YAML tips file. If None, uses default location.
        """
        self.tips_file = tips_file or self._get_default_tips_file()
        self._tips_cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: Optional[float] = None
        self._user_state: Dict[str, Any] = {}

    def _get_default_tips_file(self) -> Path:
        """Get the default tips file path."""
        return Path(__file__).parent.parent / "data" / "tips.yaml"

    def _is_cache_valid(self) -> bool:
        """Check if the cached tips are still valid by comparing file modification time.

        Returns:
            bool: True if cache is valid, False if file has been modified since caching
        """
        if not self.tips_file.exists():
            return True  # If file doesn't exist, use cached fallback

        try:
            file_mtime = self.tips_file.stat().st_mtime
            return self._cache_timestamp is not None and file_mtime <= self._cache_timestamp
        except OSError:
            # If we can't check file stats, assume cache is valid to avoid repeated errors
            return True

    def _load_tips(self) -> Dict[str, Any]:
        """Load tips from YAML file with caching and invalidation."""
        # Check if cache is still valid
        if self._tips_cache is not None and self._is_cache_valid():
            return self._tips_cache

        if not self.tips_file.exists():
            # Return minimal fallback tips if file doesn't exist
            self._tips_cache = {
                "tips": [
                    {
                        "id": "vscode_extension",
                        "title": "VSCode Extension Available",
                        "message": "Install the rxiv-maker VSCode extension for enhanced productivity with syntax highlighting, snippets, and integrated commands!",
                        "category": "tools",
                        "priority": self.DEFAULT_FALLBACK_PRIORITY,
                    }
                ]
            }
            self._cache_timestamp = time.time()
            return self._tips_cache

        try:
            with open(self.tips_file, "r", encoding="utf-8") as f:
                content = f.read()

            if yaml:
                self._tips_cache = yaml.safe_load(content)
            else:
                # Fallback to simple parser
                self._tips_cache = parse_yaml_simple(content)

            # Set cache timestamp after successful load
            self._cache_timestamp = time.time()

        except FileNotFoundError:
            print(f"Warning: Tips file not found: {self.tips_file}")
            self._tips_cache = {"tips": []}
            self._cache_timestamp = time.time()
        except Exception as e:
            # Catch all other errors (YAML parsing, file reading, etc.) to prevent crashes
            print(f"Warning: Could not load tips file: {e}")
            self._tips_cache = {"tips": []}
            self._cache_timestamp = time.time()

        return self._tips_cache or {"tips": []}

    def _should_show_tip(self, frequency_setting: str = "always") -> bool:
        """Determine if a tip should be shown based on frequency setting.

        Currently always returns True - the frequency parameter is maintained for
        API compatibility but not implemented. Future versions may add frequency
        control (e.g., 'always', 'often', 'rarely', 'never').

        Args:
            frequency_setting: Frequency preference (currently ignored)
                - 'always': Show tips every time (default behavior)
                - 'often': Show tips frequently (not implemented)
                - 'rarely': Show tips occasionally (not implemented)
                - 'never': Never show tips (not implemented)

        Returns:
            bool: Currently always True to show tips
        """
        return True

    def _select_tip(self, category: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Select a tip to display.

        Args:
            category: Optional category filter

        Returns:
            Selected tip dict or None
        """
        tips_data = self._load_tips()
        tips = tips_data.get("tips", [])

        if not tips:
            return None

        # Filter by category if specified
        if category:
            tips = [tip for tip in tips if tip.get("category") == category]

        if not tips:
            return None

        # Prioritize high-priority tips
        high_priority = [tip for tip in tips if tip.get("priority", 0) >= self.HIGH_PRIORITY_THRESHOLD]
        if high_priority and random.random() < self.HIGH_PRIORITY_CHANCE:
            return random.choice(high_priority)

        return random.choice(tips)

    def get_tip(
        self, category: Optional[str] = None, frequency: str = "normal", force: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get a tip for display.

        Args:
            category: Optional category filter
            frequency: Display frequency setting
            force: Force display regardless of frequency

        Returns:
            Tip dict with title, message, etc. or None
        """
        if not force and not self._should_show_tip(frequency):
            return None

        return self._select_tip(category)

    def format_tip_for_console(self, tip: Dict[str, Any]) -> str:
        """Format a tip for rich console display.

        Args:
            tip: Tip dictionary

        Returns:
            Formatted tip string with rich markup
        """
        title = tip.get("title", "Tip")
        message = tip.get("message", "")

        # Create formatted tip with "Tips and Tricks" header and consistent styling
        formatted = "\n[bold cyan]Tips and Tricks[/bold cyan]\n"
        formatted += f"💡 [bold blue]{title}[/bold blue]\n"
        formatted += f"   [dim]{message}[/dim]"

        return formatted


def get_build_success_tip(frequency: str = "always") -> Optional[str]:
    """Get a tip to display after successful PDF build.

    Args:
        frequency: Frequency preference (currently ignored, always shows tips)

    Returns:
        Formatted tip string or None
    """
    manager = TipsManager()
    tip = manager.get_tip(category="build_success", frequency="always")

    if tip:
        return manager.format_tip_for_console(tip)

    return None


def get_general_tip(frequency: str = "always") -> Optional[str]:
    """Get a general productivity tip.

    Args:
        frequency: Frequency preference (currently ignored, always shows tips)

    Returns:
        Formatted tip string or None
    """
    manager = TipsManager()
    tip = manager.get_tip(frequency="always")

    if tip:
        return manager.format_tip_for_console(tip)

    return None
