"""Cache utilities for rxiv-maker.

Provides manuscript-local cache directory management using .rxiv_cache.
"""

from pathlib import Path


def find_manuscript_directory(start_path: Path | None = None, max_depth: int = 5) -> Path | None:
    """Find the manuscript directory by locating 00_CONFIG.yml file.

    Walks up the directory tree from the starting path to find a directory
    containing 00_CONFIG.yml, which indicates a manuscript root.

    Args:
        start_path: Path to start searching from (defaults to current directory)
        max_depth: Maximum depth to search up the directory tree

    Returns:
        Path to manuscript directory if found, None otherwise

    Examples:
        >>> find_manuscript_directory()
        PosixPath('/path/to/manuscript')  # if 00_CONFIG.yml found

        >>> find_manuscript_directory(Path('/path/to/manuscript/subdir'))
        PosixPath('/path/to/manuscript')  # walks up to find config
    """
    current_path = (start_path or Path.cwd()).resolve()

    for _i in range(max_depth):
        config_file = current_path / "00_CONFIG.yml"
        if config_file.exists() and config_file.is_file():
            return current_path

        # Move up one directory
        parent = current_path.parent
        if parent == current_path:
            # Reached filesystem root
            break
        current_path = parent

    return None


def get_manuscript_cache_dir(subfolder: str | None = None, manuscript_dir: Path | None = None) -> Path:
    """Get the manuscript-local cache directory (.rxiv_cache in manuscript directory).

    Args:
        subfolder: Optional subfolder within the cache directory
        manuscript_dir: Manuscript directory (if None, auto-detected)

    Returns:
        Path to manuscript-local cache directory

    Raises:
        RuntimeError: If no manuscript directory is found

    Examples:
        >>> get_manuscript_cache_dir()
        PosixPath('/path/to/manuscript/.rxiv_cache')

        >>> get_manuscript_cache_dir("doi")
        PosixPath('/path/to/manuscript/.rxiv_cache/doi')
    """
    if manuscript_dir is None:
        manuscript_dir = find_manuscript_directory()

    if manuscript_dir is None:
        raise RuntimeError(
            "Cannot find manuscript directory. Make sure you're in a directory containing 00_CONFIG.yml "
            "or one of its subdirectories."
        )

    cache_dir = manuscript_dir / ".rxiv_cache"

    if subfolder:
        cache_dir = cache_dir / subfolder

    # Ensure directory exists
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        raise RuntimeError(f"Cannot create cache directory {cache_dir}: {e}") from e

    return cache_dir


def get_manuscript_name(manuscript_dir: Path | None = None) -> str | None:
    """Get the manuscript name from the manuscript directory.

    Args:
        manuscript_dir: Manuscript directory (if None, auto-detected)

    Returns:
        Manuscript directory name if found, None otherwise

    Examples:
        >>> get_manuscript_name()
        'MANUSCRIPT'  # if in /path/to/MANUSCRIPT directory
    """
    if manuscript_dir is None:
        manuscript_dir = find_manuscript_directory()

    if manuscript_dir is None:
        return None

    return manuscript_dir.name


def is_in_manuscript_directory() -> bool:
    """Check if current working directory is within a manuscript directory.

    Returns:
        True if in a manuscript directory, False otherwise

    Examples:
        >>> is_in_manuscript_directory()
        True  # if 00_CONFIG.yml found in current dir or parent dirs
    """
    return find_manuscript_directory() is not None
