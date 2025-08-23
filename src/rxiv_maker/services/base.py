"""Base service class providing common patterns and utilities."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, TypeVar

from ..core.cache import get_cache_dir
from ..core.managers.config_manager import ConfigManager
from ..utils.platform import safe_console_print, safe_print

T = TypeVar("T")


class ServiceError(Exception):
    """Base exception for service layer errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class ValidationError(ServiceError):
    """Raised when validation fails."""

    pass


class ConfigurationError(ServiceError):
    """Raised when configuration is invalid."""

    pass


class ProcessingError(ServiceError):
    """Raised when processing operations fail."""

    pass


class ServiceResult(Generic[T]):
    """Standardized service operation result."""

    def __init__(
        self,
        success: bool,
        data: Optional[T] = None,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.success = success
        self.data = data
        self.errors = errors or []
        self.warnings = warnings or []
        self.metadata = metadata or {}

    @classmethod
    def success_result(cls, data: T, warnings: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None):
        """Create a successful result."""
        return cls(True, data, warnings=warnings, metadata=metadata)

    @classmethod
    def error_result(cls, errors: List[str], data: Optional[T] = None, metadata: Optional[Dict[str, Any]] = None):
        """Create an error result."""
        return cls(False, data, errors, metadata=metadata)

    def add_warning(self, warning: str):
        """Add a warning to the result."""
        self.warnings.append(warning)

    def add_error(self, error: str):
        """Add an error to the result."""
        self.errors.append(error)
        self.success = False


class BaseService(ABC):
    """Base class for all rxiv-maker services.

    Provides common functionality including:
    - Consistent logging
    - Configuration management
    - Error handling patterns
    - Cache access
    - Validation utilities
    """

    def __init__(self, config: Optional[ConfigManager] = None, logger: Optional[logging.Logger] = None):
        """Initialize base service.

        Args:
            config: Configuration manager instance
            logger: Logger instance (creates one if not provided)
        """
        self.config = config or ConfigManager()
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._cache_dir = None

    @property
    def cache_dir(self) -> Path:
        """Get the cache directory."""
        if self._cache_dir is None:
            self._cache_dir = get_cache_dir()
        return self._cache_dir

    def safe_print(self, message: str, **kwargs):
        """Safely print messages using platform-appropriate encoding."""
        safe_print(message, **kwargs)

    def safe_console_print(self, message: str, **kwargs):
        """Safely print to console with rich formatting if available."""
        safe_console_print(message, **kwargs)

    def validate_path(
        self, path: str, must_exist: bool = True, must_be_file: bool = False, must_be_dir: bool = False
    ) -> Path:
        """Validate and normalize a path.

        Args:
            path: Path string to validate
            must_exist: Whether path must exist
            must_be_file: Whether path must be a file
            must_be_dir: Whether path must be a directory

        Returns:
            Validated Path object

        Raises:
            ValidationError: If validation fails
        """
        try:
            path_obj = Path(path).resolve()

            if must_exist and not path_obj.exists():
                raise ValidationError(f"Path does not exist: {path}")

            if must_be_file and path_obj.exists() and not path_obj.is_file():
                raise ValidationError(f"Path is not a file: {path}")

            if must_be_dir and path_obj.exists() and not path_obj.is_dir():
                raise ValidationError(f"Path is not a directory: {path}")

            return path_obj

        except OSError as e:
            raise ValidationError(f"Invalid path: {path}") from e

    def log_operation(self, operation: str, details: Optional[Dict[str, Any]] = None):
        """Log a service operation with structured details."""
        detail_str = f" ({details})" if details else ""
        self.logger.info(f"{operation}{detail_str}")

    def handle_error(self, operation: str, error: Exception) -> ServiceError:
        """Standardized error handling and logging."""
        error_msg = f"Operation '{operation}' failed: {str(error)}"
        self.logger.error(error_msg, exc_info=True)

        if isinstance(error, ServiceError):
            return error

        return ProcessingError(error_msg, {"operation": operation, "original_error": str(error)})

    @abstractmethod
    def health_check(self) -> ServiceResult[Dict[str, Any]]:
        """Check service health and return diagnostic information.

        Returns:
            ServiceResult containing health status and diagnostic data
        """
        pass
