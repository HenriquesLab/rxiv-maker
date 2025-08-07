"""Configuration management system for Rxiv-Maker.

This module provides centralized configuration management including:
- Configuration loading and merging
- Environment-specific configurations
- Configuration templates and initialization
- Dynamic configuration updates
- Configuration migration and versioning
"""

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..core.error_codes import ErrorCode, create_validation_error
from .validator import ConfigValidator

logger = logging.getLogger(__name__)


class ConfigManager:
    """Centralized configuration management system."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            base_dir: Base directory for configuration files
        """
        self.base_dir = base_dir or Path.cwd()
        self.validator = ConfigValidator()

        # Configuration search paths (in order of priority)
        self.config_paths = [
            self.base_dir / "rxiv.yml",
            self.base_dir / "rxiv.yaml",
            self.base_dir / ".rxiv.yml",
            self.base_dir / ".rxiv.yaml",
            Path.home() / ".config" / "rxiv-maker" / "config.yml",
            Path.home() / ".rxiv" / "config.yml",
        ]

        # Default configuration
        self.default_config = self._get_default_config()

        # Loaded configuration cache
        self._loaded_config: Optional[Dict[str, Any]] = None

    def load_config(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """Load configuration from file or default locations.

        Args:
            config_path: Specific config file path (optional)

        Returns:
            Merged configuration dictionary
        """
        if self._loaded_config is not None:
            return self._loaded_config

        config = self.default_config.copy()

        if config_path:
            # Load specific config file
            if config_path.exists():
                file_config = self._load_config_file(config_path)
                if file_config:
                    config = self._merge_configs(config, file_config)
        else:
            # Search for config files in order
            for path in self.config_paths:
                if path.exists():
                    file_config = self._load_config_file(path)
                    if file_config:
                        config = self._merge_configs(config, file_config)
                        logger.debug(f"Loaded configuration from {path}")
                        break

        # Apply environment variable overrides
        config = self._apply_environment_overrides(config)

        # Cache the loaded configuration
        self._loaded_config = config

        return config

    def validate_config(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """Validate configuration file.

        Args:
            config_path: Path to config file to validate

        Returns:
            Validation results
        """
        if config_path:
            return self.validator.validate_manuscript_config(config_path)

        # Find and validate the first available config file
        for path in self.config_paths:
            if path.exists():
                return self.validator.validate_manuscript_config(path)

        return {
            "valid": False,
            "errors": [
                create_validation_error(
                    ErrorCode.CONFIG_FILE_ERROR,
                    "No configuration file found in any of the expected locations",
                    context="Configuration validation",
                )
            ],
            "warnings": [],
            "config_data": None,
        }

    def init_config(self, template_name: str = "default", force: bool = False) -> Path:
        """Initialize configuration file from template.

        Args:
            template_name: Name of template to use
            force: Whether to overwrite existing config

        Returns:
            Path to created configuration file
        """
        config_path = self.base_dir / "rxiv.yml"

        if config_path.exists() and not force:
            raise ValueError(f"Configuration file already exists: {config_path}")

        template_config = self._get_config_template(template_name)

        # Write configuration file
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(template_config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Created configuration file: {config_path}")
        return config_path

    def update_config(self, updates: Dict[str, Any], config_path: Optional[Path] = None) -> Path:
        """Update configuration with new values.

        Args:
            updates: Dictionary of configuration updates
            config_path: Path to config file (uses default if None)

        Returns:
            Path to updated configuration file
        """
        if config_path is None:
            config_path = self._find_existing_config() or (self.base_dir / "rxiv.yml")

        # Load existing config or start with default
        if config_path.exists():
            current_config = self._load_config_file(config_path)
        else:
            current_config = self._get_config_template("default")

        # Merge updates
        updated_config = self._merge_configs(current_config, updates)

        # Note: Skipping validation during update to allow flexible configuration changes
        # Users can run explicit validation when needed

        # Write updated config
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(updated_config, f, default_flow_style=False, sort_keys=False)

        # Clear cached config to force reload
        self._loaded_config = None

        logger.info(f"Updated configuration file: {config_path}")
        return config_path

    def get_config_value(self, key: str, default: Any = None, config_path: Optional[Path] = None) -> Any:
        """Get specific configuration value.

        Args:
            key: Configuration key (supports dot notation, e.g., 'style.format')
            default: Default value if key not found
            config_path: Optional specific config file

        Returns:
            Configuration value
        """
        config = self.load_config(config_path)

        # Support dot notation for nested keys
        keys = key.split(".")
        value = config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set_config_value(self, key: str, value: Any, config_path: Optional[Path] = None) -> Path:
        """Set specific configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
            config_path: Optional specific config file

        Returns:
            Path to updated configuration file
        """
        # Convert dot notation to nested dict update
        keys = key.split(".")
        updates = {}
        current = updates

        for k in keys[:-1]:
            current[k] = {}
            current = current[k]
        current[keys[-1]] = value

        return self.update_config(updates, config_path)

    def migrate_config(self, from_version: str, to_version: str, config_path: Optional[Path] = None) -> Path:
        """Migrate configuration from one version to another.

        Args:
            from_version: Current configuration version
            to_version: Target configuration version
            config_path: Path to config file

        Returns:
            Path to migrated configuration file
        """
        if config_path is None:
            config_path = self._find_existing_config()
            if not config_path:
                raise ValueError("No configuration file found to migrate")

        # Load current config
        current_config = self._load_config_file(config_path)
        if not current_config:
            raise ValueError(f"Could not load configuration from {config_path}")

        # Apply migration rules
        migrated_config = self._apply_migration_rules(current_config, from_version, to_version)

        # Backup original config
        backup_path = config_path.with_suffix(f".{from_version}.backup")
        shutil.copy2(config_path, backup_path)
        logger.info(f"Created backup: {backup_path}")

        # Write migrated config
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(migrated_config, f, default_flow_style=False, sort_keys=False)

        # Clear cached config
        self._loaded_config = None

        logger.info(f"Migrated configuration from {from_version} to {to_version}")
        return config_path

    def export_config(self, output_path: Path, format_type: str = "yaml", include_defaults: bool = False) -> Path:
        """Export configuration to file.

        Args:
            output_path: Path for exported config file
            format_type: Export format ('yaml' or 'json')
            include_defaults: Whether to include default values

        Returns:
            Path to exported configuration file
        """
        if include_defaults:
            config = self.load_config()
        else:
            # Load only non-default configuration
            config_file = self._find_existing_config()
            if config_file:
                config = self._load_config_file(config_file)
            else:
                config = {}

        # Export in requested format
        if format_type.lower() == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        else:  # YAML
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Exported configuration to {output_path}")
        return output_path

    def list_config_files(self) -> List[Dict[str, Any]]:
        """List all available configuration files.

        Returns:
            List of configuration file information
        """
        config_files = []

        for path in self.config_paths:
            if path.exists():
                try:
                    stat = path.stat()
                    config_files.append(
                        {
                            "path": str(path),
                            "exists": True,
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                            "readable": os.access(path, os.R_OK),
                            "writable": os.access(path, os.W_OK),
                        }
                    )
                except Exception as e:
                    config_files.append({"path": str(path), "exists": True, "error": str(e)})
            else:
                config_files.append({"path": str(path), "exists": False})

        return config_files

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "title": "",
            "authors": [],
            "abstract": "",
            "keywords": [],
            "style": {"format": "nature", "font_size": "12pt", "line_spacing": "double", "margins": "default"},
            "output": {"format": "pdf", "directory": "output", "filename": "manuscript"},
            "engine": {"type": "local", "docker_image": "henriqueslab/rxiv-maker-base:latest", "timeout": 300},
            "validation": {"enabled": True, "strict": False, "skip_doi_check": False},
            "figures": {"directory": "FIGURES", "generate": True, "formats": ["png", "svg"]},
            "bibliography": {"file": "03_REFERENCES.bib", "style": "nature"},
            "cache": {"enabled": True, "ttl_hours": 24, "directory": ".cache"},
            "version": "1.0",
            "acknowledge_rxiv_maker": True,
        }

    def _get_config_template(self, template_name: str) -> Dict[str, Any]:
        """Get configuration template."""
        templates = {
            "default": self._get_default_config(),
            "minimal": {
                "title": "Your Manuscript Title",
                "authors": [
                    {
                        "name": "Your Name",
                        "email": "your.email@example.com",
                        "orcid": "0000-0000-0000-0000",
                        "affiliation": "Your Institution",
                    }
                ],
                "abstract": "Your manuscript abstract goes here. Please provide a detailed summary of your research work, methodology, key findings, and conclusions. This abstract should be comprehensive enough to give readers a clear understanding of your research contribution and its significance to the field.",
                "keywords": ["keyword1", "keyword2", "keyword3"],
                "version": "1.0",
            },
            "journal": {
                **self._get_default_config(),
                "journal": {"name": "Journal Name", "volume": "", "issue": "", "pages": "", "year": 2025, "doi": ""},
                "submission": {"date": "2025-01-01", "status": "draft", "version": "1.0"},
            },
            "preprint": {
                **self._get_default_config(),
                "preprint": {"server": "bioRxiv", "doi": "", "version": "1.0"},
                "license": "CC-BY-4.0",
            },
        }

        if template_name not in templates:
            raise ValueError(f"Unknown template: {template_name}. Available: {list(templates.keys())}")

        return templates[template_name]

    def _load_config_file(self, config_path: Path) -> Optional[Dict[str, Any]]:
        """Load configuration from file."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Handle YAML front matter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 2:
                    yaml_content = parts[1]
                else:
                    yaml_content = content
            else:
                yaml_content = content

            return yaml.safe_load(yaml_content)

        except Exception as e:
            logger.debug(f"Error loading config file {config_path}: {e}")
            return None

    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def _apply_environment_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides."""
        env_overrides = {
            "RXIV_ENGINE_TYPE": ("engine", "type"),
            "RXIV_OUTPUT_DIR": ("output", "directory"),
            "RXIV_CACHE_ENABLED": ("cache", "enabled"),
            "RXIV_VALIDATION_STRICT": ("validation", "strict"),
            "MANUSCRIPT_PATH": ("manuscript", "path"),
        }

        for env_var, config_path in env_overrides.items():
            env_value = os.environ.get(env_var)
            if env_value is not None:
                # Navigate to nested config location
                current = config
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]

                # Convert environment value to appropriate type
                final_key = config_path[-1]
                if env_value.lower() in ("true", "1", "yes", "on"):
                    current[final_key] = True
                elif env_value.lower() in ("false", "0", "no", "off"):
                    current[final_key] = False
                else:
                    current[final_key] = env_value

                logger.debug(f"Applied environment override: {env_var}={env_value}")

        return config

    def _find_existing_config(self) -> Optional[Path]:
        """Find first existing configuration file."""
        for path in self.config_paths:
            if path.exists():
                return path
        return None

    def _apply_migration_rules(self, config: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
        """Apply migration rules for configuration versions."""
        # This is a simplified migration system
        # In production, you'd have more sophisticated migration rules

        migrated = config.copy()

        # Update version
        migrated["version"] = to_version

        # Example migration rules
        if from_version == "0.9" and to_version == "1.0":
            # Migrate old structure to new structure
            if "output_dir" in migrated:
                migrated.setdefault("output", {})["directory"] = migrated.pop("output_dir")

            if "engine_type" in migrated:
                migrated.setdefault("engine", {})["type"] = migrated.pop("engine_type")

        # Add any new default fields that don't exist
        default_config = self._get_default_config()
        for key, value in default_config.items():
            if key not in migrated:
                migrated[key] = value
                logger.debug(f"Added new configuration field: {key}")

        return migrated

    def reset_cache(self) -> None:
        """Reset configuration cache."""
        self._loaded_config = None
        logger.debug("Configuration cache reset")


# Global configuration manager instance
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager(base_dir: Optional[Path] = None) -> ConfigManager:
    """Get or create global configuration manager."""
    global _global_config_manager

    if _global_config_manager is None or base_dir:
        _global_config_manager = ConfigManager(base_dir)

    return _global_config_manager


def load_global_config() -> Dict[str, Any]:
    """Load global configuration."""
    return get_config_manager().load_config()
