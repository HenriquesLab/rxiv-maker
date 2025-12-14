"""Unified configuration management system for rxiv-maker.

This module provides a single, unified interface for managing both:
1. Manuscript-level configuration (00_CONFIG.yml, rxiv.yml in manuscript directories)
2. Repository-level configuration (~/.rxiv-maker/config for global settings)

The UnifiedConfigManager provides scoped access to configuration values,
automatically routing requests to the appropriate configuration system
based on the scope (manuscript vs repository).
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..repo_config import RepoConfig
from .config_manager import ConfigManager

logger = logging.getLogger(__name__)


class ConfigScope(Enum):
    """Configuration scope enumeration."""

    MANUSCRIPT = "manuscript"  # Manuscript-specific config (00_CONFIG.yml, rxiv.yml)
    REPOSITORY = "repository"  # Global repository config (~/.rxiv-maker/config)
    AUTO = "auto"  # Automatically determine scope based on key


# Configuration key to scope mapping
CONFIG_SCOPE_MAP = {
    # Manuscript-level keys
    "title": ConfigScope.MANUSCRIPT,
    "authors": ConfigScope.MANUSCRIPT,
    "abstract": ConfigScope.MANUSCRIPT,
    "keywords": ConfigScope.MANUSCRIPT,
    "style": ConfigScope.MANUSCRIPT,
    "output": ConfigScope.MANUSCRIPT,
    "figures": ConfigScope.MANUSCRIPT,
    "bibliography": ConfigScope.MANUSCRIPT,
    "bibliography_author_format": ConfigScope.MANUSCRIPT,
    "validation": ConfigScope.MANUSCRIPT,
    "cache": ConfigScope.MANUSCRIPT,
    "acknowledge_rxiv_maker": ConfigScope.MANUSCRIPT,
    "version": ConfigScope.MANUSCRIPT,
    # Repository-level keys
    "repo_parent_dir": ConfigScope.REPOSITORY,
    "repo_default_github_org": ConfigScope.REPOSITORY,
    "repo_default_editor": ConfigScope.REPOSITORY,
    "repo_auto_sync": ConfigScope.REPOSITORY,
}


class UnifiedConfigManager:
    """Unified configuration manager for both manuscript and repository configs.

    This class provides a single interface for managing configuration at both
    the manuscript level (00_CONFIG.yml in manuscript directories) and the
    repository level (~/.rxiv-maker/config for global settings).

    Usage:
        # Get unified config manager
        config = UnifiedConfigManager()

        # Get manuscript-level config value
        title = config.get("title", scope=ConfigScope.MANUSCRIPT)

        # Get repository-level config value
        parent_dir = config.get("repo_parent_dir", scope=ConfigScope.REPOSITORY)

        # Auto-detect scope based on key
        value = config.get("title")  # Automatically uses MANUSCRIPT scope

        # Set values
        config.set("title", "My Paper", scope=ConfigScope.MANUSCRIPT)
        config.set("repo_parent_dir", "~/papers", scope=ConfigScope.REPOSITORY)
    """

    def __init__(self, manuscript_path: Optional[Union[str, Path]] = None):
        """Initialize unified configuration manager.

        Args:
            manuscript_path: Path to manuscript directory (for manuscript config)
        """
        self.manuscript_path = Path(manuscript_path) if manuscript_path else Path.cwd()

        # Initialize both configuration managers
        self.manuscript_config = ConfigManager(base_dir=self.manuscript_path)
        self.repo_config = RepoConfig()

    def get(
        self,
        key: str,
        default: Any = None,
        scope: ConfigScope = ConfigScope.AUTO,
    ) -> Any:
        """Get a configuration value from the appropriate scope.

        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key not found
            scope: Configuration scope (auto-detects if AUTO)

        Returns:
            Configuration value or default if not found
        """
        # Auto-detect scope if needed
        if scope == ConfigScope.AUTO:
            scope = self._detect_scope(key)

        # Route to appropriate config manager
        if scope == ConfigScope.MANUSCRIPT:
            return self._get_manuscript_value(key, default)
        elif scope == ConfigScope.REPOSITORY:
            return self._get_repository_value(key, default)
        else:
            logger.warning(f"Unknown scope for key '{key}', using manuscript scope")
            return self._get_manuscript_value(key, default)

    def set(
        self,
        key: str,
        value: Any,
        scope: ConfigScope = ConfigScope.AUTO,
    ) -> None:
        """Set a configuration value in the appropriate scope.

        Args:
            key: Configuration key (supports dot notation for nested keys)
            value: Value to set
            scope: Configuration scope (auto-detects if AUTO)
        """
        # Auto-detect scope if needed
        if scope == ConfigScope.AUTO:
            scope = self._detect_scope(key)

        # Route to appropriate config manager
        if scope == ConfigScope.MANUSCRIPT:
            self._set_manuscript_value(key, value)
        elif scope == ConfigScope.REPOSITORY:
            self._set_repository_value(key, value)
        else:
            logger.warning(f"Unknown scope for key '{key}', using manuscript scope")
            self._set_manuscript_value(key, value)

    def get_all(self, scope: ConfigScope) -> Dict[str, Any]:
        """Get all configuration values for a specific scope.

        Args:
            scope: Configuration scope

        Returns:
            Dictionary of all configuration values in the scope
        """
        if scope == ConfigScope.MANUSCRIPT:
            return self.manuscript_config.load_config()
        elif scope == ConfigScope.REPOSITORY:
            return self.repo_config.load()
        else:
            raise ValueError(f"Invalid scope: {scope}")

    def validate(self, scope: ConfigScope = ConfigScope.MANUSCRIPT) -> Dict[str, Any]:
        """Validate configuration for a specific scope.

        Args:
            scope: Configuration scope to validate

        Returns:
            Validation results dictionary
        """
        if scope == ConfigScope.MANUSCRIPT:
            return self.manuscript_config.validate_config()
        else:
            # Repository config doesn't have complex validation yet
            return {"valid": True, "errors": [], "warnings": []}

    def reset_cache(self, scope: Optional[ConfigScope] = None) -> None:
        """Reset configuration cache.

        Args:
            scope: Specific scope to reset, or all if None
        """
        if scope is None or scope == ConfigScope.MANUSCRIPT:
            self.manuscript_config._loaded_config = None

        if scope is None or scope == ConfigScope.REPOSITORY:
            self.repo_config.reset_cache()

    def list_config_files(self) -> List[Dict[str, Any]]:
        """List all configuration files with their locations and status.

        Returns:
            List of dictionaries with file information
        """
        files = []

        # Repository config
        repo_config_path = self.repo_config.config_path
        files.append(
            {
                "type": "repository",
                "path": str(repo_config_path),
                "exists": repo_config_path.exists(),
                "scope": ConfigScope.REPOSITORY,
            }
        )

        # Manuscript config (check for multiple possible names)
        manuscript_config_paths = [
            self.manuscript_path / "00_CONFIG.yml",
            self.manuscript_path / "rxiv.yml",
            self.manuscript_path / "rxiv.yaml",
            self.manuscript_path / ".rxiv.yml",
            self.manuscript_path / ".rxiv.yaml",
        ]

        for config_path in manuscript_config_paths:
            if config_path.exists():
                files.append(
                    {
                        "type": "manuscript",
                        "path": str(config_path),
                        "exists": True,
                        "scope": ConfigScope.MANUSCRIPT,
                    }
                )
                break  # Only report first found manuscript config
        else:
            # If no manuscript config found, report default location
            files.append(
                {
                    "type": "manuscript",
                    "path": str(self.manuscript_path / "00_CONFIG.yml"),
                    "exists": False,
                    "scope": ConfigScope.MANUSCRIPT,
                }
            )

        return files

    def _detect_scope(self, key: str) -> ConfigScope:
        """Detect the appropriate scope for a configuration key.

        Args:
            key: Configuration key

        Returns:
            Detected ConfigScope
        """
        # Extract base key (before any dots)
        base_key = key.split(".")[0]

        # Check known mappings
        if base_key in CONFIG_SCOPE_MAP:
            return CONFIG_SCOPE_MAP[base_key]

        # Default to manuscript scope for unknown keys
        logger.debug(f"Unknown key '{key}', defaulting to manuscript scope")
        return ConfigScope.MANUSCRIPT

    def _get_manuscript_value(self, key: str, default: Any = None) -> Any:
        """Get value from manuscript configuration.

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        config = self.manuscript_config.load_config()
        return self._get_nested_value(config, key, default)

    def _set_manuscript_value(self, key: str, value: Any) -> None:
        """Set value in manuscript configuration.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        # For manuscript config, we need to handle this through ConfigManager
        # This is a simplified implementation - full implementation would
        # need to load, modify, and save the config file
        logger.warning("Direct manuscript config setting not fully implemented yet")
        # TODO: Implement proper manuscript config setting

    def _get_repository_value(self, key: str, default: Any = None) -> Any:
        """Get value from repository configuration.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.repo_config.get(key, default)

    def _set_repository_value(self, key: str, value: Any) -> None:
        """Set value in repository configuration.

        Args:
            key: Configuration key
            value: Value to set
        """
        self.repo_config.set(key, value)

    def _get_nested_value(self, config: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Get nested configuration value using dot notation.

        Args:
            config: Configuration dictionary
            key: Key with dot notation (e.g., 'style.format')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any) -> None:
        """Set nested configuration value using dot notation.

        Args:
            config: Configuration dictionary
            key: Key with dot notation (e.g., 'style.format')
            value: Value to set
        """
        keys = key.split(".")
        current = config

        # Navigate to the parent of the final key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Set the final value
        current[keys[-1]] = value


def get_unified_config_manager(manuscript_path: Optional[Union[str, Path]] = None) -> UnifiedConfigManager:
    """Get a singleton instance of UnifiedConfigManager.

    Args:
        manuscript_path: Path to manuscript directory

    Returns:
        UnifiedConfigManager instance
    """
    # For now, create a new instance each time
    # In the future, could implement singleton pattern with path-based caching
    return UnifiedConfigManager(manuscript_path=manuscript_path)


__all__ = [
    "UnifiedConfigManager",
    "ConfigScope",
    "get_unified_config_manager",
    "CONFIG_SCOPE_MAP",
]
