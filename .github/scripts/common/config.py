#!/usr/bin/env python3
"""
Configuration management for GitHub Actions scripts.

Loads and validates configuration from YAML files and environment variables.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class ReleaseConfig:
    """Configuration for release workflows."""

    package_name: str
    pypi_timeout: int = 300  # 5 minutes
    pypi_check_interval: int = 30  # seconds
    github_timeout: int = 120  # 2 minutes
    homebrew_repo: str = "homebrew-rxiv-maker"
    apt_repo: str = "apt-rxiv-maker"
    cross_repo_timeout: int = 600  # 10 minutes

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.package_name:
            raise ValueError("package_name is required")
        if self.pypi_timeout <= 0:
            raise ValueError("pypi_timeout must be positive")


@dataclass
class MonitoringConfig:
    """Configuration for monitoring workflows."""

    check_interval: int = 3600  # 1 hour
    alert_threshold: int = 3  # failures before alerting
    repositories: list = None

    def __post_init__(self):
        if self.repositories is None:
            self.repositories = ["rxiv-maker", "docker-rxiv-maker"]


class ConfigLoader:
    """Loads and manages configuration from files and environment."""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize config loader.

        Args:
            config_dir: Directory containing config files. Defaults to .github/config
        """
        if config_dir is None:
            # Find .github/config relative to this script
            script_dir = Path(__file__).parent
            config_dir = script_dir.parent / "config"

        self.config_dir = Path(config_dir)

    def load_release_config(self) -> ReleaseConfig:
        """Load release configuration."""
        config_file = self.config_dir / "release_config.yaml"

        # Default configuration
        config_data = {
            "package_name": "rxiv-maker",
            "pypi_timeout": 300,
            "pypi_check_interval": 30,
            "github_timeout": 120,
            "homebrew_repo": "homebrew-rxiv-maker",
            "apt_repo": "apt-rxiv-maker",
            "cross_repo_timeout": 600,
        }

        # Load from file if it exists
        if config_file.exists():
            with open(config_file, "r") as f:
                file_config = yaml.safe_load(f) or {}
            config_data.update(file_config)

        # Override with environment variables
        env_overrides = {
            "package_name": os.getenv("PACKAGE_NAME"),
            "pypi_timeout": self._get_env_int("PYPI_TIMEOUT"),
            "github_timeout": self._get_env_int("GITHUB_TIMEOUT"),
            "homebrew_repo": os.getenv("HOMEBREW_REPO"),
            "apt_repo": os.getenv("APT_REPO"),
        }

        for key, value in env_overrides.items():
            if value is not None:
                config_data[key] = value

        return ReleaseConfig(**config_data)

    def load_monitoring_config(self) -> MonitoringConfig:
        """Load monitoring configuration."""
        config_file = self.config_dir / "monitoring_config.yaml"

        # Default configuration
        config_data = {
            "check_interval": 3600,
            "alert_threshold": 3,
            "repositories": ["rxiv-maker", "docker-rxiv-maker"],
        }

        # Load from file if it exists
        if config_file.exists():
            with open(config_file, "r") as f:
                file_config = yaml.safe_load(f) or {}
            config_data.update(file_config)

        return MonitoringConfig(**config_data)

    def _get_env_int(self, key: str) -> Optional[int]:
        """Get integer from environment variable."""
        value = os.getenv(key)
        if value is not None:
            try:
                return int(value)
            except ValueError:
                pass
        return None


def get_github_token() -> str:
    """Get GitHub token from environment."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    return token


def get_pypi_token() -> str:
    """Get PyPI token from environment."""
    token = os.getenv("PYPI_TOKEN")
    if not token:
        raise ValueError("PYPI_TOKEN environment variable is required")
    return token


def get_pypi_token_optional() -> str:
    """Get PyPI token from environment (optional for OIDC fallback)."""
    return os.getenv("PYPI_TOKEN", "")


def get_current_version() -> str:
    """Extract current version from git tag or environment."""
    # Try environment first (set by GitHub Actions)
    version = os.getenv("GITHUB_REF_NAME")
    if version and version.startswith("v"):
        return version

    # Try git tag
    try:
        import subprocess

        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match", "HEAD"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        pass

    raise ValueError("Could not determine current version from git tag or GITHUB_REF_NAME")
