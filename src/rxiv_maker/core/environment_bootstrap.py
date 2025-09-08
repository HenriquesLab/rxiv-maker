"""Environment bootstrapping and context management for rxiv-maker.

This module provides centralized environment setup including:
- One-line setup for common patterns (logging, paths, config)
- Context managers for transactional operations
- Environment validation and health checks
- Dependency verification
- Session management and cleanup
"""

import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Optional, Protocol

from ..core.environment_manager import EnvironmentManager
from ..core.logging_config import get_logger
from ..core.managers.config_manager import ConfigManager
from ..core.managers.file_manager import get_file_manager
from ..core.path_manager import PathManager, PathResolutionError

logger = get_logger()


class EnvironmentContext(Protocol):
    """Protocol for environment context objects."""

    config: ConfigManager
    path_manager: PathManager
    file_manager: Any
    logger: Any
    verbose: bool


class RxivEnvironmentContext:
    """Complete environment context for rxiv-maker operations."""

    def __init__(
        self,
        manuscript_path: Optional[str] = None,
        output_dir: str = "output",
        verbose: Optional[bool] = None,
        config: Optional[ConfigManager] = None,
    ):
        """Initialize environment context.

        Args:
            manuscript_path: Path to manuscript directory
            output_dir: Output directory name
            verbose: Verbose mode (auto-detected if None)
            config: Optional existing config manager
        """
        # Set up logging first
        if verbose is None:
            verbose = EnvironmentManager.is_verbose()
        self.verbose = verbose

        # Configure logging based on verbosity
        # Note: Actual logging level configuration would need access to setup_logging
        # For now, just set the verbose flag

        self.logger = get_logger()

        # Initialize managers
        self.config = config or ConfigManager()
        self.file_manager = get_file_manager()

        # Set up path management
        if manuscript_path is None:
            manuscript_path = EnvironmentManager.get_manuscript_path() or "MANUSCRIPT"

        try:
            self.path_manager = PathManager(manuscript_path=manuscript_path, output_dir=output_dir)
        except PathResolutionError as e:
            self.logger.error(f"Path resolution failed: {e}")
            raise EnvironmentError(f"Failed to resolve manuscript path: {e}") from e

        # Store environment info
        self.manuscript_path = self.path_manager.manuscript_path
        self.output_dir = self.path_manager.output_dir

        self.logger.debug(f"Environment initialized: manuscript={self.manuscript_path}, output={self.output_dir}")

    def validate_environment(self) -> Dict[str, Any]:
        """Validate the current environment setup.

        Returns:
            Dictionary with validation results
        """
        validation = {"valid": True, "issues": [], "warnings": [], "info": {}}

        # Check manuscript path
        if not self.manuscript_path.exists():
            validation["issues"].append(f"Manuscript directory does not exist: {self.manuscript_path}")
            validation["valid"] = False
        else:
            validation["info"]["manuscript_path"] = str(self.manuscript_path)

        # Check output directory can be created
        try:
            self.file_manager.ensure_directory(self.output_dir)
            validation["info"]["output_dir"] = str(self.output_dir)
        except Exception as e:
            validation["issues"].append(f"Cannot create output directory: {e}")
            validation["valid"] = False

        # Check permissions
        if self.manuscript_path.exists():
            try:
                info = self.file_manager.get_file_info(self.manuscript_path)
                if not info["readable"]:
                    validation["issues"].append("Manuscript directory is not readable")
                    validation["valid"] = False
                if not info["writable"]:
                    validation["warnings"].append("Manuscript directory is not writable (may affect some operations)")
            except Exception as e:
                validation["warnings"].append(f"Could not check manuscript directory permissions: {e}")

        # Check config validity
        try:
            health = self.config.health_check()
            if not health.success:
                validation["warnings"].extend(health.errors)
        except Exception as e:
            validation["warnings"].append(f"Config health check failed: {e}")

        return validation

    def get_context_info(self) -> Dict[str, Any]:
        """Get comprehensive context information.

        Returns:
            Dictionary with context details
        """
        return {
            "manuscript_path": str(self.manuscript_path),
            "output_dir": str(self.output_dir),
            "verbose": self.verbose,
            "working_directory": str(Path.cwd()),
            "environment_vars": {
                "MANUSCRIPT_PATH": os.getenv("MANUSCRIPT_PATH"),
                "RXIV_VERBOSE": os.getenv("RXIV_VERBOSE"),
                "RXIV_CONFIG_PATH": os.getenv("RXIV_CONFIG_PATH"),
            },
            "managers": {
                "config": self.config.__class__.__name__,
                "path_manager": self.path_manager.__class__.__name__,
                "file_manager": self.file_manager.__class__.__name__,
            },
        }


class EnvironmentBootstrap:
    """Bootstrap environment setup with common patterns."""

    @staticmethod
    def quick_setup(manuscript_path: Optional[str] = None, verbose: Optional[bool] = None) -> RxivEnvironmentContext:
        """Quick environment setup with sensible defaults.

        Args:
            manuscript_path: Path to manuscript directory
            verbose: Verbose mode (auto-detected if None)

        Returns:
            Configured environment context
        """
        return RxivEnvironmentContext(manuscript_path=manuscript_path, verbose=verbose)

    @staticmethod
    def setup_for_command(
        manuscript_path: Optional[str] = None,
        output_dir: str = "output",
        verbose: Optional[bool] = None,
        validate: bool = True,
    ) -> RxivEnvironmentContext:
        """Setup environment for CLI command execution.

        Args:
            manuscript_path: Path to manuscript directory
            output_dir: Output directory name
            verbose: Verbose mode (auto-detected if None)
            validate: Whether to validate environment

        Returns:
            Configured environment context

        Raises:
            EnvironmentError: If environment validation fails
        """
        context = RxivEnvironmentContext(manuscript_path=manuscript_path, output_dir=output_dir, verbose=verbose)

        if validate:
            validation = context.validate_environment()
            if not validation["valid"]:
                issues = "; ".join(validation["issues"])
                raise EnvironmentError(f"Environment validation failed: {issues}")

            # Log warnings
            for warning in validation["warnings"]:
                context.logger.warning(warning)

        return context

    @staticmethod
    def setup_for_testing(
        temp_dir: Optional[Path] = None, manuscript_name: str = "test_manuscript"
    ) -> RxivEnvironmentContext:
        """Setup environment for testing.

        Args:
            temp_dir: Temporary directory for testing
            manuscript_name: Name for test manuscript directory

        Returns:
            Configured test environment context
        """
        if temp_dir is None:
            import tempfile

            temp_dir = Path(tempfile.mkdtemp())

        manuscript_path = temp_dir / manuscript_name
        manuscript_path.mkdir(parents=True, exist_ok=True)

        return RxivEnvironmentContext(
            manuscript_path=str(manuscript_path), output_dir=str(temp_dir / "output"), verbose=False
        )


@contextmanager
def rxiv_environment(
    manuscript_path: Optional[str] = None,
    output_dir: str = "output",
    verbose: Optional[bool] = None,
    validate: bool = True,
    cleanup: bool = False,
) -> Generator[RxivEnvironmentContext, None, None]:
    """Context manager for rxiv environment setup and cleanup.

    Args:
        manuscript_path: Path to manuscript directory
        output_dir: Output directory name
        verbose: Verbose mode (auto-detected if None)
        validate: Whether to validate environment
        cleanup: Whether to cleanup temporary files on exit

    Yields:
        Configured environment context

    Raises:
        EnvironmentError: If environment setup or validation fails
    """
    context = None
    try:
        context = EnvironmentBootstrap.setup_for_command(
            manuscript_path=manuscript_path, output_dir=output_dir, verbose=verbose, validate=validate
        )

        context.logger.debug("Environment context entered")
        yield context

    except Exception as e:
        if context:
            context.logger.error(f"Environment context error: {e}")
        raise
    finally:
        if context:
            context.logger.debug("Environment context exiting")
            if cleanup:
                try:
                    context.file_manager.cleanup_temp_files()
                except Exception as e:
                    context.logger.warning(f"Cleanup failed: {e}")


@contextmanager
def transactional_operation(
    context: RxivEnvironmentContext, operation_name: str, backup_files: Optional[list] = None
) -> Generator[None, None, None]:
    """Context manager for transactional operations with rollback.

    Args:
        context: Environment context
        operation_name: Name of the operation for logging
        backup_files: List of files to backup before operation

    Yields:
        None
    """
    backups = {}

    try:
        context.logger.info(f"Starting transactional operation: {operation_name}")

        # Create backups if requested
        if backup_files:
            for file_path in backup_files:
                if Path(file_path).exists():
                    backup_path = f"{file_path}.backup_{operation_name}"
                    context.file_manager.safe_copy(file_path, backup_path)
                    backups[file_path] = backup_path
                    context.logger.debug(f"Created backup: {backup_path}")

        yield

        # Operation succeeded, clean up backups
        for backup_path in backups.values():
            try:
                context.file_manager.safe_delete(backup_path)
            except Exception as e:
                context.logger.warning(f"Could not remove backup {backup_path}: {e}")

        context.logger.info(f"Completed transactional operation: {operation_name}")

    except Exception as e:
        context.logger.error(f"Transactional operation failed: {operation_name}: {e}")

        # Restore backups
        for original_path, backup_path in backups.items():
            try:
                if Path(backup_path).exists():
                    context.file_manager.safe_copy(backup_path, original_path, overwrite=True)
                    context.logger.info(f"Restored backup: {original_path}")
            except Exception as restore_error:
                context.logger.error(f"Failed to restore backup {backup_path}: {restore_error}")

        raise


def diagnose_environment() -> Dict[str, Any]:
    """Diagnose environment setup issues.

    Returns:
        Dictionary with diagnostic information
    """
    diagnosis = {
        "python": {
            "version": sys.version,
            "executable": sys.executable,
            "path": sys.path[:3],  # First few entries
        },
        "working_directory": str(Path.cwd()),
        "environment_vars": {
            "MANUSCRIPT_PATH": os.getenv("MANUSCRIPT_PATH"),
            "RXIV_VERBOSE": os.getenv("RXIV_VERBOSE"),
            "PATH": os.getenv("PATH", "")[:200] + "..." if len(os.getenv("PATH", "")) > 200 else os.getenv("PATH", ""),
        },
        "permissions": {},
        "paths": {},
    }

    # Check common paths
    common_paths = [Path.cwd(), Path.cwd() / "MANUSCRIPT", Path.cwd() / "output"]

    for path in common_paths:
        diagnosis["paths"][str(path)] = {
            "exists": path.exists(),
            "is_dir": path.is_dir() if path.exists() else None,
            "readable": path.exists() and os.access(path, os.R_OK),
            "writable": path.exists() and os.access(path, os.W_OK),
        }

    # Check permissions in current directory
    cwd = Path.cwd()
    diagnosis["permissions"] = {
        "cwd_readable": os.access(cwd, os.R_OK),
        "cwd_writable": os.access(cwd, os.W_OK),
        "cwd_executable": os.access(cwd, os.X_OK),
    }

    return diagnosis


# Convenience functions
def setup_quick(manuscript_path: Optional[str] = None) -> RxivEnvironmentContext:
    """Quick setup with defaults."""
    return EnvironmentBootstrap.quick_setup(manuscript_path)


def setup_verbose(manuscript_path: Optional[str] = None) -> RxivEnvironmentContext:
    """Setup with verbose logging."""
    return EnvironmentBootstrap.quick_setup(manuscript_path, verbose=True)


# Export public API
__all__ = [
    "EnvironmentBootstrap",
    "RxivEnvironmentContext",
    "rxiv_environment",
    "transactional_operation",
    "diagnose_environment",
    "setup_quick",
    "setup_verbose",
]
