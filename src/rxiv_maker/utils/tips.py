"""Tips and tricks system for Rxiv-Maker CLI.

This module provides helpful tips to users after successful operations,
including recommendations for tools like the VSCode extension.
"""

import random
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from ..processors.yaml_processor import parse_yaml_simple


class TipsManager:
    """Manages display and selection of user tips."""

    def __init__(self, tips_file: Optional[Path] = None):
        """Initialize the tips manager.

        Args:
            tips_file: Path to YAML tips file. If None, uses default location.
        """
        self.tips_file = tips_file or self._get_default_tips_file()
        self._tips_cache: Optional[Dict[str, Any]] = None
        self._user_state: Dict[str, Any] = {}

    def _get_default_tips_file(self) -> Path:
        """Get the default tips file path."""
        return Path(__file__).parent.parent / "data" / "tips.yaml"

    def _load_tips(self) -> Dict[str, Any]:
        """Load tips from YAML file with caching."""
        if self._tips_cache is not None:
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
                        "priority": 1,
                    }
                ]
            }
            return self._tips_cache

        try:
            with open(self.tips_file, "r", encoding="utf-8") as f:
                content = f.read()

            if yaml:
                self._tips_cache = yaml.safe_load(content)
            else:
                # Fallback to simple parser
                self._tips_cache = parse_yaml_simple(content)

        except Exception as e:
            # Return fallback on any error
            print(f"Warning: Could not load tips file: {e}")
            self._tips_cache = {"tips": []}

        return self._tips_cache or {"tips": []}

    def _should_show_tip(self, frequency_setting: str = "always") -> bool:
        """Always show tips - frequency setting maintained for API compatibility.

        Args:
            frequency_setting: Ignored - always returns True

        Returns:
            bool: Always True to show tips
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
        high_priority = [tip for tip in tips if tip.get("priority", 0) >= 5]
        if high_priority and random.random() < 0.7:  # 70% chance for high priority
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

        # Create formatted tip with consistent styling
        formatted = f"\n💡 [bold blue]{title}[/bold blue]\n"
        formatted += f"   [dim]{message}[/dim]"

        return formatted


def get_build_success_tip(frequency: str = "always") -> Optional[str]:
    """Get a tip to display after successful PDF build.

    Args:
        frequency: Ignored - always shows tips

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
        frequency: Ignored - always shows tips

    Returns:
        Formatted tip string or None
    """
    manager = TipsManager()
    tip = manager.get_tip(frequency="always")

    if tip:
        return manager.format_tip_for_console(tip)

    return None
