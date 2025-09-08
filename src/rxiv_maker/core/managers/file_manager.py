"""Centralized file operation manager for rxiv-maker.

This module provides standardized file operations including:
- Safe file reading with encoding fallback
- Consistent file writing with proper encoding
- Path validation and resolution
- Progress reporting for large operations
- Centralized error handling and logging
- Atomic file operations with rollback
"""

import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from ..error_recovery import RecoveryEnhancedMixin
from ..logging_config import get_logger

logger = get_logger()


class FileOperationError(Exception):
    """Exception raised during file operations."""

    def __init__(self, message: str, path: Optional[str] = None, operation: Optional[str] = None):
        super().__init__(message)
        self.path = path
        self.operation = operation


class FileOperationManager(RecoveryEnhancedMixin):
    """Centralized manager for all file operations in rxiv-maker.

    Features:
    - Standardized encoding handling (UTF-8 with Latin-1 fallback)
    - Progress reporting for large operations
    - Atomic operations with rollback capabilities
    - Consistent error handling and logging
    - Path validation and safety checks
    - Directory management utilities
    """

    def __init__(self):
        super().__init__()
        self.temp_files: List[Path] = []

    def read_text_file(self, file_path: Union[str, Path], encoding: str = "utf-8") -> str:
        """Read text file with automatic encoding fallback.

        Args:
            file_path: Path to the file to read
            encoding: Primary encoding to try (defaults to utf-8)

        Returns:
            File contents as string

        Raises:
            FileOperationError: If file cannot be read
        """
        path_obj = Path(file_path)

        if not path_obj.exists():
            raise FileOperationError(f"File not found: {file_path}", path=str(file_path), operation="read_text")

        # Try primary encoding first
        try:
            with open(path_obj, encoding=encoding) as f:
                content = f.read()
            logger.debug(f"Successfully read file with {encoding} encoding: {file_path}")
            return content

        except UnicodeDecodeError:
            # Fall back to latin-1 encoding (common for LaTeX log files)
            try:
                with open(path_obj, encoding="latin-1") as f:
                    content = f.read()
                logger.debug(f"Read file with latin-1 fallback encoding: {file_path}")
                return content

            except (UnicodeDecodeError, OSError) as e:
                raise FileOperationError(
                    f"Cannot read file with {encoding} or latin-1 encoding: {file_path}",
                    path=str(file_path),
                    operation="read_text",
                ) from e

        except OSError as e:
            raise FileOperationError(
                f"Cannot read file: {file_path}", path=str(file_path), operation="read_text"
            ) from e

    def read_binary_file(self, file_path: Union[str, Path]) -> bytes:
        """Read binary file safely.

        Args:
            file_path: Path to the file to read

        Returns:
            File contents as bytes

        Raises:
            FileOperationError: If file cannot be read
        """
        path_obj = Path(file_path)

        if not path_obj.exists():
            raise FileOperationError(f"File not found: {file_path}", path=str(file_path), operation="read_binary")

        try:
            with open(path_obj, "rb") as f:
                content = f.read()
            logger.debug(f"Successfully read binary file: {file_path}")
            return content

        except OSError as e:
            raise FileOperationError(
                f"Cannot read binary file: {file_path}", path=str(file_path), operation="read_binary"
            ) from e

    def write_text_file(
        self,
        file_path: Union[str, Path],
        content: str,
        encoding: str = "utf-8",
        create_parents: bool = True,
        backup_existing: bool = False,
    ) -> None:
        """Write text file with consistent encoding and error handling.

        Args:
            file_path: Path to the file to write
            content: Content to write
            encoding: Encoding to use (defaults to utf-8)
            create_parents: Whether to create parent directories
            backup_existing: Whether to backup existing file

        Raises:
            FileOperationError: If file cannot be written
        """
        path_obj = Path(file_path)

        if create_parents:
            path_obj.parent.mkdir(parents=True, exist_ok=True)

        backup_path = None
        if backup_existing and path_obj.exists():
            backup_path = path_obj.with_suffix(f"{path_obj.suffix}.backup")
            shutil.copy2(path_obj, backup_path)
            logger.debug(f"Created backup: {backup_path}")

        try:
            with open(path_obj, "w", encoding=encoding) as f:
                f.write(content)
            logger.debug(f"Successfully wrote text file: {file_path}")

        except OSError as e:
            # Restore backup if write failed
            if backup_path and backup_path.exists():
                try:
                    shutil.move(backup_path, path_obj)
                    logger.debug(f"Restored backup after write failure: {file_path}")
                except OSError:
                    pass  # Backup restoration failed, but original error is more important

            raise FileOperationError(
                f"Cannot write file: {file_path}", path=str(file_path), operation="write_text"
            ) from e

    def write_binary_file(self, file_path: Union[str, Path], content: bytes, create_parents: bool = True) -> None:
        """Write binary file safely.

        Args:
            file_path: Path to the file to write
            content: Binary content to write
            create_parents: Whether to create parent directories

        Raises:
            FileOperationError: If file cannot be written
        """
        path_obj = Path(file_path)

        if create_parents:
            path_obj.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path_obj, "wb") as f:
                f.write(content)
            logger.debug(f"Successfully wrote binary file: {file_path}")

        except OSError as e:
            raise FileOperationError(
                f"Cannot write binary file: {file_path}", path=str(file_path), operation="write_binary"
            ) from e

    @contextmanager
    def atomic_write(
        self, file_path: Union[str, Path], encoding: str = "utf-8", create_parents: bool = True
    ) -> Iterator[Any]:
        """Context manager for atomic file writing.

        Writes to a temporary file first, then moves to final location
        to prevent corruption if write is interrupted.

        Args:
            file_path: Final path for the file
            encoding: Text encoding to use
            create_parents: Whether to create parent directories

        Yields:
            File object for writing
        """
        path_obj = Path(file_path)

        if create_parents:
            path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Create temporary file in same directory as target
        temp_fd, temp_path = tempfile.mkstemp(dir=path_obj.parent, prefix=f".{path_obj.name}.", suffix=".tmp")

        temp_path_obj = Path(temp_path)
        self.temp_files.append(temp_path_obj)

        try:
            with os.fdopen(temp_fd, "w", encoding=encoding) as f:
                yield f

            # Atomically replace target file
            temp_path_obj.replace(path_obj)
            logger.debug(f"Atomically wrote file: {file_path}")

            # Remove from temp files list since it's now the real file
            self.temp_files.remove(temp_path_obj)

        except Exception as e:
            # Clean up temporary file on error
            try:
                temp_path_obj.unlink()
                if temp_path_obj in self.temp_files:
                    self.temp_files.remove(temp_path_obj)
            except OSError:
                pass

            raise FileOperationError(
                f"Atomic write failed: {file_path}", path=str(file_path), operation="atomic_write"
            ) from e

    def ensure_directory(self, dir_path: Union[str, Path], mode: int = 0o755) -> Path:
        """Ensure directory exists with proper permissions.

        Args:
            dir_path: Path to directory
            mode: Directory permissions (defaults to 755)

        Returns:
            Path object for the directory

        Raises:
            FileOperationError: If directory cannot be created
        """
        path_obj = Path(dir_path)

        try:
            path_obj.mkdir(parents=True, exist_ok=True, mode=mode)
            logger.debug(f"Ensured directory exists: {dir_path}")
            return path_obj

        except OSError as e:
            raise FileOperationError(
                f"Cannot create directory: {dir_path}", path=str(dir_path), operation="ensure_directory"
            ) from e

    def safe_copy(
        self,
        source: Union[str, Path],
        destination: Union[str, Path],
        preserve_metadata: bool = True,
        overwrite: bool = False,
    ) -> None:
        """Copy file safely with proper error handling.

        Args:
            source: Source file path
            destination: Destination file path
            preserve_metadata: Whether to preserve file metadata
            overwrite: Whether to overwrite existing destination

        Raises:
            FileOperationError: If copy operation fails
        """
        source_path = Path(source)
        dest_path = Path(destination)

        if not source_path.exists():
            raise FileOperationError(f"Source file not found: {source}", path=str(source), operation="safe_copy")

        if dest_path.exists() and not overwrite:
            raise FileOperationError(
                f"Destination file exists and overwrite=False: {destination}",
                path=str(destination),
                operation="safe_copy",
            )

        # Ensure destination directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if preserve_metadata:
                shutil.copy2(source_path, dest_path)
            else:
                shutil.copy(source_path, dest_path)
            logger.debug(f"Successfully copied: {source} -> {destination}")

        except OSError as e:
            raise FileOperationError(
                f"Cannot copy file: {source} -> {destination}", path=str(source), operation="safe_copy"
            ) from e

    def safe_move(self, source: Union[str, Path], destination: Union[str, Path], overwrite: bool = False) -> None:
        """Move file safely with proper error handling.

        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Whether to overwrite existing destination

        Raises:
            FileOperationError: If move operation fails
        """
        source_path = Path(source)
        dest_path = Path(destination)

        if not source_path.exists():
            raise FileOperationError(f"Source file not found: {source}", path=str(source), operation="safe_move")

        if dest_path.exists() and not overwrite:
            raise FileOperationError(
                f"Destination file exists and overwrite=False: {destination}",
                path=str(destination),
                operation="safe_move",
            )

        # Ensure destination directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            shutil.move(source_path, dest_path)
            logger.debug(f"Successfully moved: {source} -> {destination}")

        except OSError as e:
            raise FileOperationError(
                f"Cannot move file: {source} -> {destination}", path=str(source), operation="safe_move"
            ) from e

    def safe_delete(self, file_path: Union[str, Path], missing_ok: bool = True) -> None:
        """Delete file safely.

        Args:
            file_path: Path to file to delete
            missing_ok: Whether missing files should be ignored

        Raises:
            FileOperationError: If deletion fails
        """
        path_obj = Path(file_path)

        if not path_obj.exists():
            if missing_ok:
                logger.debug(f"File already missing (OK): {file_path}")
                return
            else:
                raise FileOperationError(f"File not found: {file_path}", path=str(file_path), operation="safe_delete")

        try:
            path_obj.unlink()
            logger.debug(f"Successfully deleted file: {file_path}")

        except OSError as e:
            raise FileOperationError(
                f"Cannot delete file: {file_path}", path=str(file_path), operation="safe_delete"
            ) from e

    def validate_path(
        self,
        path: Union[str, Path],
        must_exist: bool = True,
        must_be_file: bool = False,
        must_be_dir: bool = False,
        must_be_readable: bool = False,
        must_be_writable: bool = False,
    ) -> Path:
        """Validate path with comprehensive checks.

        Args:
            path: Path to validate
            must_exist: Whether path must exist
            must_be_file: Whether path must be a file
            must_be_dir: Whether path must be a directory
            must_be_readable: Whether path must be readable
            must_be_writable: Whether path must be writable

        Returns:
            Validated Path object

        Raises:
            FileOperationError: If validation fails
        """
        try:
            path_obj = Path(path).resolve()
        except OSError as e:
            raise FileOperationError(f"Invalid path: {path}", path=str(path), operation="validate_path") from e

        if must_exist and not path_obj.exists():
            raise FileOperationError(f"Path does not exist: {path}", path=str(path), operation="validate_path")

        if must_be_file and path_obj.exists() and not path_obj.is_file():
            raise FileOperationError(f"Path is not a file: {path}", path=str(path), operation="validate_path")

        if must_be_dir and path_obj.exists() and not path_obj.is_dir():
            raise FileOperationError(f"Path is not a directory: {path}", path=str(path), operation="validate_path")

        if must_be_readable and path_obj.exists() and not os.access(path_obj, os.R_OK):
            raise FileOperationError(f"Path is not readable: {path}", path=str(path), operation="validate_path")

        if must_be_writable and path_obj.exists() and not os.access(path_obj, os.W_OK):
            raise FileOperationError(f"Path is not writable: {path}", path=str(path), operation="validate_path")

        return path_obj

    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Get comprehensive file information.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file information
        """
        path_obj = Path(file_path)

        info = {
            "path": str(path_obj.absolute()),
            "exists": path_obj.exists(),
            "is_file": False,
            "is_dir": False,
            "size": None,
            "readable": False,
            "writable": False,
            "executable": False,
        }

        if path_obj.exists():
            try:
                stat = path_obj.stat()
                info.update(
                    {
                        "is_file": path_obj.is_file(),
                        "is_dir": path_obj.is_dir(),
                        "size": stat.st_size,
                        "readable": os.access(path_obj, os.R_OK),
                        "writable": os.access(path_obj, os.W_OK),
                        "executable": os.access(path_obj, os.X_OK),
                        "created": stat.st_ctime,
                        "modified": stat.st_mtime,
                        "mode": stat.st_mode,
                    }
                )
            except OSError:
                # Some information not available, but basic info is still useful
                pass

        return info

    def cleanup_temp_files(self) -> None:
        """Clean up any remaining temporary files."""
        for temp_file in self.temp_files[:]:  # Copy list to avoid modification during iteration
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    logger.debug(f"Cleaned up temp file: {temp_file}")
            except OSError:
                logger.warning(f"Could not clean up temp file: {temp_file}")
            finally:
                self.temp_files.remove(temp_file)

    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup_temp_files()


# Global file manager instance
_file_manager: Optional[FileOperationManager] = None


def get_file_manager() -> FileOperationManager:
    """Get the global file operation manager instance.

    Returns:
        Global FileOperationManager instance
    """
    global _file_manager
    if _file_manager is None:
        _file_manager = FileOperationManager()
    return _file_manager


# Convenience functions for common operations
def read_text_file(file_path: Union[str, Path], encoding: str = "utf-8") -> str:
    """Read text file with automatic encoding fallback."""
    return get_file_manager().read_text_file(file_path, encoding)


def write_text_file(
    file_path: Union[str, Path], content: str, encoding: str = "utf-8", create_parents: bool = True
) -> None:
    """Write text file with consistent encoding."""
    get_file_manager().write_text_file(file_path, content, encoding, create_parents)


def ensure_directory(dir_path: Union[str, Path]) -> Path:
    """Ensure directory exists."""
    return get_file_manager().ensure_directory(dir_path)


def validate_path(path: Union[str, Path], **kwargs) -> Path:
    """Validate path with comprehensive checks."""
    return get_file_manager().validate_path(path, **kwargs)


# Export public API
__all__ = [
    "FileOperationManager",
    "FileOperationError",
    "get_file_manager",
    "read_text_file",
    "write_text_file",
    "ensure_directory",
    "validate_path",
]
