"""Secure cache utilities for rxiv-maker with comprehensive security hardening.

This module provides secure cache directory management with protection against:
- Path traversal attacks
- TOCTOU race conditions
- Symlink attacks
- Disk space exhaustion
- Permission escalation
"""

import fcntl
import hashlib
import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import platformdirs

logger = logging.getLogger(__name__)

# Security constants
MAX_CACHE_SIZE_MB = 1000  # Maximum cache size in MB
MAX_FILE_SIZE_MB = 100  # Maximum individual file size in MB
CACHE_PERMISSIONS = 0o755  # Standard cache directory permissions
FILE_PERMISSIONS = 0o644  # Standard file permissions


class SecurityError(Exception):
    """Raised when a security violation is detected."""

    pass


def _is_safe_path_component(path_component: str) -> bool:
    """Check if a path component is safe from traversal attacks.

    Args:
        path_component: Path component to validate

    Returns:
        True if the path component is safe
    """
    if not path_component:
        return False

    # Check for path traversal patterns
    dangerous_patterns = [
        "..",  # Parent directory
        "./",  # Current directory with separator
        "../",  # Parent directory with separator
        "..\\",  # Windows parent directory
        "~",  # Home directory expansion
        "//",  # Double slash
        "\\\\",  # Windows double backslash
        "\x00",  # Null byte
    ]

    for pattern in dangerous_patterns:
        if pattern in path_component:
            logger.warning(f"Dangerous pattern '{pattern}' detected in path component: {path_component}")
            return False

    # Check for absolute paths (Unix and Windows style)
    try:
        if Path(path_component).is_absolute():
            logger.warning(f"Absolute path detected: {path_component}")
            return False
        # Also check for Windows-style absolute paths on Unix systems
        if len(path_component) >= 3 and path_component[1] == ":" and path_component[2] in ["\\", "/"]:
            logger.warning(f"Windows absolute path detected: {path_component}")
            return False
    except (ValueError, OSError):
        return False

    # Check for special characters that could be problematic
    if any(char in path_component for char in ["\n", "\r", "|", ">", "<", "&", ";", "`", "$", "(", ")"]):
        logger.warning(f"Special characters detected in path component: {path_component}")
        return False

    return True


def _validate_path_within_base(path: Path, base_dir: Path) -> bool:
    """Validate that a path is within the specified base directory.

    Args:
        path: Path to validate
        base_dir: Base directory that should contain the path

    Returns:
        True if path is within base_dir
    """
    try:
        # Resolve both paths to handle symlinks and relative paths
        resolved_path = path.resolve(strict=False)
        resolved_base = base_dir.resolve(strict=False)

        # Check if path is within base directory
        resolved_path.relative_to(resolved_base)

        # Additional check for symlinks pointing outside base
        if resolved_path.is_symlink():
            target = Path(os.readlink(resolved_path))
            if target.is_absolute():
                return _validate_path_within_base(target, base_dir)

        return True
    except (ValueError, RuntimeError, OSError):
        return False


def _check_disk_space(path: Path, required_mb: int = 100) -> Tuple[bool, int]:
    """Check if sufficient disk space is available.

    Args:
        path: Path to check disk space for
        required_mb: Required space in megabytes

    Returns:
        Tuple of (has_space, available_mb)
    """
    try:
        stat = shutil.disk_usage(path if path.exists() else path.parent)
        available_mb = stat.free // (1024 * 1024)
        return available_mb >= required_mb, available_mb
    except Exception as e:
        logger.warning(f"Could not check disk space: {e}")
        return True, -1  # Assume space is available if we can't check


def _atomic_write(content: bytes, target_path: Path, mode: int = FILE_PERMISSIONS) -> None:
    """Write content to a file atomically to prevent partial writes.

    Args:
        content: Content to write
        target_path: Target file path
        mode: File permissions

    Raises:
        SecurityError: If operation would violate security constraints
        IOError: If write fails
    """
    # Create temporary file in same directory for atomic rename
    temp_fd, temp_path = tempfile.mkstemp(dir=target_path.parent, prefix=f".{target_path.stem}_", suffix=".tmp")

    try:
        # Write content with proper permissions
        with os.fdopen(temp_fd, "wb") as f:
            # Try to acquire exclusive lock
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (OSError, AttributeError):
                # Locking not available on this platform
                pass

            f.write(content)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is written to disk

        # Set permissions before rename
        os.chmod(temp_path, mode)

        # Atomic rename
        Path(temp_path).rename(target_path)

    except Exception:
        # Clean up temporary file on failure
        try:
            Path(temp_path).unlink()
        except OSError:
            pass
        raise


def get_secure_cache_dir(subfolder: Optional[str] = None) -> Path:
    """Get the standardized cache directory with security validation.

    Args:
        subfolder: Optional subfolder within the cache directory

    Returns:
        Path to the cache directory

    Raises:
        SecurityError: If path validation fails
        PermissionError: If cache directory cannot be created or accessed
    """
    cache_dir = Path(platformdirs.user_cache_dir("rxiv-maker"))

    if subfolder:
        # Validate subfolder to prevent path traversal
        if not _is_safe_path_component(subfolder):
            raise SecurityError(f"Invalid subfolder name: {subfolder}")

        # Construct path safely
        cache_dir = cache_dir / subfolder

        # Validate the final path is still within cache directory
        base_cache = Path(platformdirs.user_cache_dir("rxiv-maker")).resolve()
        if not _validate_path_within_base(cache_dir, base_cache):
            raise SecurityError(f"Subfolder would escape cache directory: {subfolder}")

    # Check disk space before creating directory
    has_space, available_mb = _check_disk_space(cache_dir.parent if not cache_dir.exists() else cache_dir)
    if not has_space:
        raise IOError(f"Insufficient disk space. Only {available_mb}MB available")

    # Ensure directory exists with secure permissions
    try:
        cache_dir.mkdir(parents=True, exist_ok=True, mode=CACHE_PERMISSIONS)

        # Verify permissions and access
        if not os.access(cache_dir, os.R_OK | os.W_OK):
            raise PermissionError(f"Insufficient permissions for cache directory: {cache_dir}")

        # Check it's not a symlink to somewhere unexpected
        if cache_dir.is_symlink():
            real_path = cache_dir.resolve()
            if not _validate_path_within_base(real_path, base_cache):
                raise SecurityError(f"Cache directory is a symlink to unsafe location: {real_path}")

    except OSError as e:
        raise PermissionError(f"Failed to create cache directory {cache_dir}: {e}") from e

    return cache_dir


def secure_migrate_cache_file(legacy_path: Path, new_path: Path, force: bool = False) -> bool:
    """Securely migrate a cache file with comprehensive validation.

    Args:
        legacy_path: Path to the legacy cache file
        new_path: Path to the new cache file location
        force: If True, overwrite existing file at new location

    Returns:
        True if migration was performed, False otherwise
    """
    # Security checks - check for symlinks first, before resolving
    if legacy_path.is_symlink():
        logger.warning(f"Refusing to migrate symlink: {legacy_path}")
        return False

    try:
        # Resolve paths safely after symlink check
        legacy_path = legacy_path.resolve(strict=True)  # Must exist
        new_path_parent = new_path.parent.resolve(strict=False)

    except (OSError, RuntimeError) as e:
        logger.warning(f"Path resolution failed: {e}")
        return False

    if not legacy_path.is_file():
        logger.warning(f"Source is not a regular file: {legacy_path}")
        return False

    # Check file size to prevent exhaustion attacks
    file_size_mb = legacy_path.stat().st_size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        logger.warning(f"File too large to migrate: {file_size_mb}MB > {MAX_FILE_SIZE_MB}MB")
        return False

    # Check destination disk space
    has_space, available_mb = _check_disk_space(new_path_parent, int(file_size_mb * 2))
    if not has_space:
        logger.error(f"Insufficient space for migration. Need {file_size_mb * 2}MB, have {available_mb}MB")
        return False

    # Don't overwrite unless forced
    if new_path.exists() and not force:
        return False

    # Create target directory with proper permissions
    try:
        new_path_parent.mkdir(parents=True, exist_ok=True, mode=CACHE_PERMISSIONS)
    except OSError as e:
        logger.error(f"Failed to create target directory: {e}")
        return False

    # Perform atomic migration
    try:
        # Read content with size limit
        content = legacy_path.read_bytes()

        # Calculate checksum for verification
        original_checksum = hashlib.sha256(content).hexdigest()

        # Write atomically
        _atomic_write(content, new_path, FILE_PERMISSIONS)

        # Verify the write was successful
        if new_path.exists():
            new_checksum = hashlib.sha256(new_path.read_bytes()).hexdigest()
            if new_checksum != original_checksum:
                logger.error("Checksum mismatch after migration")
                new_path.unlink()
                return False

            # Remove original only after successful verification
            legacy_path.unlink()
            return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        # Clean up any partial migration
        if new_path.exists():
            try:
                new_path.unlink()
            except OSError:
                pass
        return False

    return False


def secure_migrate_cache_directory(
    source_dir: Optional[Path] = None, force: bool = False, max_size_mb: int = MAX_CACHE_SIZE_MB
) -> bool:
    """Securely migrate cache directory with comprehensive validation.

    Args:
        source_dir: Source directory containing cache
        force: If True, overwrite existing files
        max_size_mb: Maximum total size to migrate in MB

    Returns:
        True if migration was performed, False otherwise
    """
    if source_dir is None:
        source_dir = Path.cwd()

    # Validate source directory
    try:
        source_dir = source_dir.resolve(strict=True)
    except (OSError, RuntimeError) as e:
        logger.error(f"Failed to resolve source directory: {e}")
        return False

    legacy_cache = source_dir / ".rxiv_cache"

    if not legacy_cache.exists() or not legacy_cache.is_dir():
        return False

    # Security check for symlinks
    if legacy_cache.is_symlink():
        logger.warning(f"Refusing to migrate symlink directory: {legacy_cache}")
        return False

    # Calculate total size and check limits
    total_size = 0
    file_count = 0

    try:
        for item in legacy_cache.rglob("*"):
            if item.is_file() and not item.is_symlink():
                total_size += item.stat().st_size
                file_count += 1

        total_size_mb = total_size / (1024 * 1024)

        if total_size_mb > max_size_mb:
            logger.error(f"Cache too large to migrate: {total_size_mb}MB > {max_size_mb}MB")
            return False

        # Check destination has enough space
        target_cache = get_secure_cache_dir()
        has_space, available_mb = _check_disk_space(target_cache, int(total_size_mb * 2))

        if not has_space:
            logger.error(f"Insufficient space for migration. Need {total_size_mb * 2}MB, have {available_mb}MB")
            return False

    except Exception as e:
        logger.error(f"Failed to analyze cache size: {e}")
        return False

    logger.info(f"Starting secure migration of {file_count} files ({total_size_mb:.1f}MB)")

    migrated_any = False
    migration_map = {
        "doi": "doi",
        "advanced": "advanced",
        "bibliography": "bibliography",
        "figures": "figures",
    }

    for legacy_subdir, new_subdir in migration_map.items():
        legacy_path = legacy_cache / legacy_subdir

        if not legacy_path.exists():
            continue

        # Validate path is within source cache
        if not _validate_path_within_base(legacy_path, legacy_cache):
            logger.warning(f"Skipping suspicious path: {legacy_path}")
            continue

        try:
            new_path = get_secure_cache_dir(new_subdir)

            # Use atomic directory migration with temporary directory
            if not new_path.exists() or force:
                temp_dir = Path(tempfile.mkdtemp(dir=new_path.parent, prefix=f".migrate_{new_subdir}_"))

                try:
                    # Copy without following symlinks
                    shutil.copytree(
                        legacy_path,
                        temp_dir / legacy_subdir,
                        symlinks=False,
                        ignore_dangling_symlinks=True,
                        dirs_exist_ok=False,
                    )

                    # Remove existing if force flag set
                    if force and new_path.exists():
                        backup_dir = new_path.with_suffix(f".backup_{int(time.time())}")
                        new_path.rename(backup_dir)

                    # Atomic rename
                    (temp_dir / legacy_subdir).rename(new_path)

                    # Set proper permissions recursively
                    for item in new_path.rglob("*"):
                        if item.is_dir():
                            os.chmod(item, CACHE_PERMISSIONS)
                        elif item.is_file():
                            os.chmod(item, FILE_PERMISSIONS)

                    logger.info(f"Successfully migrated: {legacy_path} -> {new_path}")
                    migrated_any = True

                finally:
                    # Clean up temporary directory
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            logger.error(f"Failed to migrate {legacy_path}: {e}")

    # Migrate individual files in root
    for item in legacy_cache.iterdir():
        if item.is_file() and not item.is_symlink():
            new_path = get_secure_cache_dir() / item.name
            if secure_migrate_cache_file(item, new_path, force):
                migrated_any = True

    return migrated_any


def validate_cache_security() -> dict[str, Any]:
    """Validate cache system security configuration.

    Returns:
        Dictionary with security validation results
    """
    results: Dict[str, Any] = {
        "secure": True,
        "issues": [],
        "warnings": [],
        "cache_dir": None,
        "permissions_ok": True,
        "symlinks_found": [],
        "disk_space_ok": True,
        "size_within_limits": True,
    }

    # Initialize typed lists explicitly to help mypy
    issues: List[str] = results["issues"]
    warnings: List[str] = results["warnings"]
    symlinks_found: List[Dict[str, Any]] = results["symlinks_found"]

    try:
        cache_dir = get_secure_cache_dir()
        results["cache_dir"] = str(cache_dir)

        # Check permissions
        stat_info = cache_dir.stat()
        mode = stat_info.st_mode & 0o777

        if mode & 0o022:  # Check for world/group write
            results["secure"] = False
            issues.append(f"Cache directory has insecure permissions: {oct(mode)}")
            results["permissions_ok"] = False

        # Check for symlinks
        for item in cache_dir.rglob("*"):
            if item.is_symlink():
                target = Path(os.readlink(item))
                symlinks_found.append(
                    {
                        "link": str(item),
                        "target": str(target),
                        "safe": _validate_path_within_base(target.resolve(), cache_dir),
                    }
                )

        if any(not link["safe"] for link in symlinks_found):
            results["secure"] = False
            issues.append("Unsafe symlinks detected in cache")

        # Check disk space
        has_space, available_mb = _check_disk_space(cache_dir)
        results["disk_space_ok"] = has_space

        if available_mb < 100:
            warnings.append(f"Low disk space: {available_mb}MB available")

        # Check cache size
        total_size = sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file())
        total_size_mb = total_size / (1024 * 1024)

        if total_size_mb > MAX_CACHE_SIZE_MB:
            results["size_within_limits"] = False
            warnings.append(f"Cache exceeds size limit: {total_size_mb:.1f}MB > {MAX_CACHE_SIZE_MB}MB")

    except Exception as e:
        results["secure"] = False
        issues.append(f"Security validation error: {e}")

    return results


# Export secure versions as the main functions
get_cache_dir = get_secure_cache_dir
migrate_cache_file = secure_migrate_cache_file
migrate_rxiv_cache_directory = secure_migrate_cache_directory
