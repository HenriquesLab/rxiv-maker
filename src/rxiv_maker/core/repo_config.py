"""Global repository configuration management for rxiv-maker.

This module handles repository-level configuration stored in ~/.rxiv-maker/config
separate from manuscript-level configuration (rxiv.yml in manuscript directories).
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "repo_parent_dir": "~/manuscripts",
    "repo_default_github_org": None,
    "repo_default_editor": None,
    "repo_auto_sync": False,
}


def get_rxiv_maker_dir() -> Path:
    """Get the ~/.rxiv-maker directory path.

    Returns:
        Path to ~/.rxiv-maker directory
    """
    return Path.home() / ".rxiv-maker"


def get_repo_config_path() -> Path:
    """Get the path to the global repository configuration file.

    Returns:
        Path to ~/.rxiv-maker/config
    """
    return get_rxiv_maker_dir() / "config"


class RepoConfig:
    """Global repository configuration manager.

    Manages configuration stored in ~/.rxiv-maker/config for repository
    management features (parent directory, default GitHub org, etc.).
    """

    def __init__(self):
        """Initialize repository configuration manager."""
        self.config_path = get_repo_config_path()
        self.config_dir = get_rxiv_maker_dir()
        self._config_cache: Optional[Dict[str, Any]] = None

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """Load configuration from file or return defaults.

        Returns:
            Configuration dictionary
        """
        if self._config_cache is not None:
            return self._config_cache.copy()

        config = DEFAULT_CONFIG.copy()

        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    file_config = yaml.safe_load(f) or {}

                # Merge file config with defaults
                config.update(file_config)
                logger.debug(f"Loaded repository configuration from {self.config_path}")

            except Exception as e:
                logger.warning(f"Error loading repository configuration: {e}")

        # Cache the configuration
        self._config_cache = config.copy()

        return config

    def save(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save configuration to file.

        Args:
            config: Configuration dictionary to save (uses cached config if None)
        """
        if config is None:
            config = self._config_cache or DEFAULT_CONFIG.copy()

        try:
            # Ensure directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Write configuration
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            # Update cache
            self._config_cache = config.copy()

            logger.info(f"Saved repository configuration to {self.config_path}")

        except Exception as e:
            logger.error(f"Error saving repository configuration: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        config = self.load()
        return config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key
            value: Value to set
        """
        config = self.load()
        config[key] = value
        self.save(config)

    def reset_cache(self) -> None:
        """Reset the configuration cache."""
        self._config_cache = None

    @property
    def parent_dir(self) -> Path:
        """Get the parent directory for manuscript repositories.

        Returns:
            Path to parent directory (expanded)
        """
        parent_dir_str = self.get("repo_parent_dir", DEFAULT_CONFIG["repo_parent_dir"])
        return Path(parent_dir_str).expanduser()

    @parent_dir.setter
    def parent_dir(self, value: str) -> None:
        """Set the parent directory for manuscript repositories.

        Args:
            value: Parent directory path
        """
        self.set("repo_parent_dir", value)

    @property
    def default_github_org(self) -> Optional[str]:
        """Get the default GitHub organization.

        Returns:
            GitHub organization name or None
        """
        return self.get("repo_default_github_org")

    @default_github_org.setter
    def default_github_org(self, value: Optional[str]) -> None:
        """Set the default GitHub organization.

        Args:
            value: GitHub organization name
        """
        self.set("repo_default_github_org", value)

    @property
    def default_editor(self) -> Optional[str]:
        """Get the default editor command.

        Returns:
            Editor command or None
        """
        return self.get("repo_default_editor")

    @default_editor.setter
    def default_editor(self, value: Optional[str]) -> None:
        """Set the default editor command.

        Args:
            value: Editor command
        """
        self.set("repo_default_editor", value)

    @property
    def auto_sync(self) -> bool:
        """Get auto-sync setting.

        Returns:
            Whether auto-sync is enabled
        """
        return self.get("repo_auto_sync", False)

    @auto_sync.setter
    def auto_sync(self, value: bool) -> None:
        """Set auto-sync setting.

        Args:
            value: Whether to enable auto-sync
        """
        self.set("repo_auto_sync", value)

    def show(self) -> Dict[str, Any]:
        """Get all configuration values with expanded paths.

        Returns:
            Configuration dictionary with expanded paths
        """
        config = self.load()
        display_config = config.copy()

        # Expand paths for display
        if "repo_parent_dir" in display_config:
            display_config["repo_parent_dir_expanded"] = str(self.parent_dir)

        return display_config


# Global configuration instance
_global_repo_config: Optional[RepoConfig] = None


def get_repo_config() -> RepoConfig:
    """Get or create the global repository configuration instance.

    Returns:
        Global RepoConfig instance
    """
    global _global_repo_config

    if _global_repo_config is None:
        _global_repo_config = RepoConfig()

    return _global_repo_config
