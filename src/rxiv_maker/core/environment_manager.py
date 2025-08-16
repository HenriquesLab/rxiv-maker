"""Centralized environment variable management for rxiv-maker.

This module provides a unified interface for all environment variable operations,
eliminating inconsistent environment variable handling throughout the codebase.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union


class EnvironmentManager:
    """Centralized environment variable management for rxiv-maker.

    Provides consistent access to environment variables with proper
    validation, type conversion, and default value handling.
    """

    # Environment variable names
    MANUSCRIPT_PATH = "MANUSCRIPT_PATH"
    RXIV_ENGINE = "RXIV_ENGINE"
    RXIV_VERBOSE = "RXIV_VERBOSE"
    RXIV_NO_UPDATE_CHECK = "RXIV_NO_UPDATE_CHECK"
    FORCE_FIGURES = "FORCE_FIGURES"
    DOCKER_IMAGE = "DOCKER_IMAGE"
    DOCKER_AVAILABLE = "DOCKER_AVAILABLE"
    MERMAID_CLI_OPTIONS = "MERMAID_CLI_OPTIONS"
    PYTHONPATH = "PYTHONPATH"

    # Docker/Container related
    COLAB_GPU = "COLAB_GPU"
    COLAB_TPU_ADDR = "COLAB_TPU_ADDR"

    # CI/CD related
    CI = "CI"
    GITHUB_ACTIONS = "GITHUB_ACTIONS"

    @classmethod
    def get_manuscript_path(cls) -> Optional[str]:
        """Get manuscript path from environment with validation.

        Returns:
            Manuscript path if set and valid, None otherwise
        """
        path = os.getenv(cls.MANUSCRIPT_PATH)
        if path:
            # Normalize and validate path
            path = path.strip().rstrip("/")
            if path and path not in (".", ".."):
                return path
        return None

    @classmethod
    def set_manuscript_path(cls, path: Union[str, Path]) -> None:
        """Set manuscript path environment variable.

        Args:
            path: Path to manuscript directory
        """
        normalized_path = str(Path(path).resolve())
        os.environ[cls.MANUSCRIPT_PATH] = normalized_path

    @classmethod
    def get_rxiv_engine(cls) -> str:
        """Get execution engine with default fallback.

        Returns:
            Engine type: "local", "docker", or "podman"
        """
        engine = os.getenv(cls.RXIV_ENGINE, "local").lower().strip()
        if engine in ("docker", "podman", "local"):
            return engine
        return "local"

    @classmethod
    def set_rxiv_engine(cls, engine: str) -> None:
        """Set execution engine.

        Args:
            engine: Engine type ("local", "docker", "podman")

        Raises:
            ValueError: If engine type is invalid
        """
        engine = engine.lower().strip()
        if engine not in ("local", "docker", "podman"):
            raise ValueError(f"Invalid engine type: {engine}")
        os.environ[cls.RXIV_ENGINE] = engine

    @classmethod
    def is_verbose(cls) -> bool:
        """Check if verbose mode is enabled.

        Returns:
            True if verbose mode is enabled
        """
        return cls._get_boolean(cls.RXIV_VERBOSE, default=False)

    @classmethod
    def set_verbose(cls, enabled: bool) -> None:
        """Set verbose mode.

        Args:
            enabled: Whether to enable verbose mode
        """
        os.environ[cls.RXIV_VERBOSE] = str(enabled).lower()

    @classmethod
    def is_update_check_disabled(cls) -> bool:
        """Check if update check is disabled.

        Returns:
            True if update check is disabled
        """
        return cls._get_boolean(cls.RXIV_NO_UPDATE_CHECK, default=False)

    @classmethod
    def disable_update_check(cls, disabled: bool = True) -> None:
        """Disable update check.

        Args:
            disabled: Whether to disable update check
        """
        os.environ[cls.RXIV_NO_UPDATE_CHECK] = str(disabled).lower()

    @classmethod
    def is_force_figures(cls) -> bool:
        """Check if figure regeneration is forced.

        Returns:
            True if figures should be regenerated
        """
        return cls._get_boolean(cls.FORCE_FIGURES, default=False)

    @classmethod
    def set_force_figures(cls, enabled: bool) -> None:
        """Set force figures regeneration.

        Args:
            enabled: Whether to force figure regeneration
        """
        os.environ[cls.FORCE_FIGURES] = str(enabled).lower()

    @classmethod
    def get_docker_image(cls) -> str:
        """Get Docker image name with default.

        Returns:
            Docker image name
        """
        return os.getenv(cls.DOCKER_IMAGE, "henriqueslab/rxiv-maker-base:latest")

    @classmethod
    def set_docker_image(cls, image: str) -> None:
        """Set Docker image name.

        Args:
            image: Docker image name
        """
        os.environ[cls.DOCKER_IMAGE] = image.strip()

    @classmethod
    def is_docker_available(cls) -> bool:
        """Check if Docker is available.

        Returns:
            True if Docker is available
        """
        return cls._get_boolean(cls.DOCKER_AVAILABLE, default=False)

    @classmethod
    def set_docker_available(cls, available: bool) -> None:
        """Set Docker availability.

        Args:
            available: Whether Docker is available
        """
        os.environ[cls.DOCKER_AVAILABLE] = str(available).lower()

    @classmethod
    def get_mermaid_cli_options(cls) -> str:
        """Get Mermaid CLI options.

        Returns:
            Mermaid CLI options string
        """
        return os.getenv(cls.MERMAID_CLI_OPTIONS, "")

    @classmethod
    def set_mermaid_cli_options(cls, options: str) -> None:
        """Set Mermaid CLI options.

        Args:
            options: Mermaid CLI options
        """
        os.environ[cls.MERMAID_CLI_OPTIONS] = options

    @classmethod
    def is_google_colab(cls) -> bool:
        """Detect if running in Google Colab environment.

        Returns:
            True if running in Google Colab
        """
        # Check for Colab-specific environment variables
        colab_indicators = [cls.COLAB_GPU, cls.COLAB_TPU_ADDR]
        if any(os.getenv(var) for var in colab_indicators):
            return True

        # Check for Colab module availability
        try:
            import google.colab  # noqa: F401

            return True
        except ImportError:
            pass

        return False

    @classmethod
    def is_ci_environment(cls) -> bool:
        """Detect if running in CI/CD environment.

        Returns:
            True if running in CI/CD
        """
        ci_indicators = [cls.CI, cls.GITHUB_ACTIONS]
        return any(cls._get_boolean(var, default=False) for var in ci_indicators)

    @classmethod
    def get_pythonpath(cls) -> list[str]:
        """Get PYTHONPATH as list of directories.

        Returns:
            List of directories in PYTHONPATH
        """
        pythonpath = os.getenv(cls.PYTHONPATH, "")
        if not pythonpath:
            return []

        # Handle different path separators
        separator = ";" if os.name == "nt" else ":"
        return [p.strip() for p in pythonpath.split(separator) if p.strip()]

    @classmethod
    def add_to_pythonpath(cls, path: Union[str, Path]) -> None:
        """Add directory to PYTHONPATH.

        Args:
            path: Directory to add to PYTHONPATH
        """
        path_str = str(Path(path).resolve())
        current_paths = cls.get_pythonpath()

        if path_str not in current_paths:
            current_paths.append(path_str)
            separator = ";" if os.name == "nt" else ":"
            os.environ[cls.PYTHONPATH] = separator.join(current_paths)

    @classmethod
    def get_all_rxiv_vars(cls) -> Dict[str, str]:
        """Get all rxiv-maker related environment variables.

        Returns:
            Dictionary of rxiv-maker environment variables
        """
        rxiv_vars = [
            cls.MANUSCRIPT_PATH,
            cls.RXIV_ENGINE,
            cls.RXIV_VERBOSE,
            cls.RXIV_NO_UPDATE_CHECK,
            cls.FORCE_FIGURES,
            cls.DOCKER_IMAGE,
            cls.DOCKER_AVAILABLE,
            cls.MERMAID_CLI_OPTIONS,
        ]

        return {var: os.getenv(var, "") for var in rxiv_vars if os.getenv(var)}

    @classmethod
    def set_environment_for_subprocess(cls, additional_vars: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Get environment variables for subprocess execution.

        Args:
            additional_vars: Additional variables to include

        Returns:
            Environment dictionary for subprocess
        """
        env = os.environ.copy()

        # Add rxiv-maker variables
        rxiv_vars = cls.get_all_rxiv_vars()
        env.update(rxiv_vars)

        # Add additional variables
        if additional_vars:
            env.update(additional_vars)

        return env

    @classmethod
    def clear_rxiv_vars(cls) -> None:
        """Clear all rxiv-maker environment variables."""
        rxiv_vars = [
            cls.MANUSCRIPT_PATH,
            cls.RXIV_ENGINE,
            cls.RXIV_VERBOSE,
            cls.RXIV_NO_UPDATE_CHECK,
            cls.FORCE_FIGURES,
            cls.DOCKER_IMAGE,
            cls.DOCKER_AVAILABLE,
            cls.MERMAID_CLI_OPTIONS,
        ]

        for var in rxiv_vars:
            if var in os.environ:
                del os.environ[var]

    @classmethod
    def _get_boolean(cls, var_name: str, default: bool = False) -> bool:
        """Get boolean value from environment variable.

        Args:
            var_name: Environment variable name
            default: Default value if not set

        Returns:
            Boolean value
        """
        value = os.getenv(var_name)
        if value is None:
            return default

        # Handle various boolean representations
        value = value.lower().strip()
        if value in ("true", "1", "yes", "on", "enabled"):
            return True
        elif value in ("false", "0", "no", "off", "disabled"):
            return False
        else:
            return default

    @classmethod
    def validate_environment(cls) -> list[str]:
        """Validate current environment setup.

        Returns:
            List of validation warnings/errors
        """
        warnings = []

        # Check manuscript path
        manuscript_path = cls.get_manuscript_path()
        if manuscript_path:
            if not Path(manuscript_path).exists():
                warnings.append(f"MANUSCRIPT_PATH points to non-existent directory: {manuscript_path}")
            elif not Path(manuscript_path).is_dir():
                warnings.append(f"MANUSCRIPT_PATH is not a directory: {manuscript_path}")

        # Check engine compatibility
        engine = cls.get_rxiv_engine()
        if engine in ("docker", "podman") and not cls.is_docker_available():
            warnings.append(f"Engine set to {engine} but Docker is not available")

        # Check Colab environment
        if cls.is_google_colab():
            if engine != "local":
                warnings.append("Google Colab detected but engine is not set to 'local'")

        return warnings

    @classmethod
    def get_debug_info(cls) -> Dict[str, Any]:
        """Get debug information about environment.

        Returns:
            Dictionary with environment debug information
        """
        return {
            "rxiv_vars": cls.get_all_rxiv_vars(),
            "engine": cls.get_rxiv_engine(),
            "verbose": cls.is_verbose(),
            "docker_available": cls.is_docker_available(),
            "google_colab": cls.is_google_colab(),
            "ci_environment": cls.is_ci_environment(),
            "pythonpath_entries": len(cls.get_pythonpath()),
            "validation_warnings": cls.validate_environment(),
        }
