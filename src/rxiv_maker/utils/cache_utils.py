"""Cache utilities for rxiv-maker.

Provides standardized cache directory management following platform conventions.
"""

from pathlib import Path

import platformdirs


def get_cache_dir(subfolder: str | None = None) -> Path:
    """Get the standardized cache directory for rxiv-maker.

    Args:
        subfolder: Optional subfolder within the cache directory

    Returns:
        Path to the cache directory

    Examples:
        >>> get_cache_dir()
        PosixPath('/home/user/.cache/rxiv-maker')  # Linux
        PosixPath('/Users/user/Library/Caches/rxiv-maker')  # macOS
        WindowsPath('C:/Users/user/AppData/Local/rxiv-maker/Cache')  # Windows

        >>> get_cache_dir("doi")
        PosixPath('/home/user/.cache/rxiv-maker/doi')  # Linux
    """
    cache_dir = Path(platformdirs.user_cache_dir("rxiv-maker"))

    if subfolder:
        cache_dir = cache_dir / subfolder

    # Ensure directory exists
    cache_dir.mkdir(parents=True, exist_ok=True)

    return cache_dir


def get_legacy_cache_dir() -> Path:
    """Get the legacy cache directory location (.cache in current directory).

    Returns:
        Path to the legacy cache directory

    Note:
        This is used for backward compatibility and migration purposes.
    """
    return Path(".cache")


def migrate_cache_file(legacy_path: Path, new_path: Path, force: bool = False) -> bool:
    """Migrate a cache file from legacy location to new standardized location.

    Args:
        legacy_path: Path to the legacy cache file
        new_path: Path to the new cache file location
        force: If True, overwrite existing file at new location

    Returns:
        True if migration was performed, False otherwise
    """
    if not legacy_path.exists():
        return False

    # Don't overwrite existing file unless forced
    if new_path.exists() and not force:
        return False

    # Ensure target directory exists
    new_path.parent.mkdir(parents=True, exist_ok=True)

    # Move the file (handle Windows behavior)
    try:
        # If forced and target exists, remove it first
        if force and new_path.exists():
            new_path.unlink()
        legacy_path.rename(new_path)
    except OSError:
        # On Windows, rename may fail even if we checked exists()
        # Use a more robust approach
        import shutil

        if force and new_path.exists():
            new_path.unlink()
        shutil.move(str(legacy_path), str(new_path))

    return True


def cleanup_legacy_cache_dir() -> None:
    """Clean up empty legacy cache directory if it exists."""
    legacy_dir = get_legacy_cache_dir()

    if legacy_dir.exists() and legacy_dir.is_dir():
        import contextlib

        with contextlib.suppress(OSError):
            # Only remove if empty
            legacy_dir.rmdir()
