"""Cache utilities for rxiv-maker.

Provides standardized cache directory management following platform conventions.
"""

import os
from pathlib import Path
from typing import Any, Dict, List

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


def get_legacy_rxiv_cache_dir() -> Path:
    """Get the legacy .rxiv_cache directory location (.rxiv_cache in current directory).

    Returns:
        Path to the legacy .rxiv_cache directory

    Note:
        This is used for backward compatibility and migration purposes.
    """
    return Path(".rxiv_cache")


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


def migrate_rxiv_cache_directory(source_dir: Path | None = None, force: bool = False) -> bool:
    """Migrate .rxiv_cache directory to standardized cache location.

    Args:
        source_dir: Source directory containing .rxiv_cache (if None, uses current directory)
        force: If True, overwrite existing files at new location

    Returns:
        True if migration was performed, False otherwise
    """
    import logging
    import shutil

    logger = logging.getLogger(__name__)

    if source_dir is None:
        source_dir = Path.cwd()

    legacy_rxiv_cache = source_dir / ".rxiv_cache"

    if not legacy_rxiv_cache.exists():
        return False

    migrated_any = False

    # Migrate common subdirectories
    migration_map = {
        "doi": "doi",
        "advanced": "advanced",
        "bibliography": "bibliography",
        "figures": "figures",
    }

    for legacy_subdir, new_subdir in migration_map.items():
        legacy_path = legacy_rxiv_cache / legacy_subdir
        if legacy_path.exists():
            new_path = get_cache_dir(new_subdir)

            try:
                # Migrate files recursively
                if force and new_path.exists():
                    shutil.rmtree(new_path)

                if not new_path.exists():
                    shutil.copytree(legacy_path, new_path)
                    logger.info(f"Migrated cache: {legacy_path} -> {new_path}")
                    migrated_any = True
                elif not force:
                    logger.warning(f"Skipping migration, target exists: {new_path}")

            except Exception as e:
                logger.error(f"Failed to migrate {legacy_path}: {e}")

    # Migrate any other files directly to root cache dir
    for item in legacy_rxiv_cache.iterdir():
        if item.is_file():
            new_path = get_cache_dir() / item.name
            if migrate_cache_file(item, new_path, force):
                migrated_any = True

    return migrated_any


def migrate_all_rxiv_caches(search_paths: list[Path] | None = None, force: bool = False) -> int:
    """Migrate all .rxiv_cache directories found in search paths.

    Args:
        search_paths: List of paths to search for .rxiv_cache directories
        force: If True, overwrite existing files at new location

    Returns:
        Number of cache directories migrated
    """
    import logging

    logger = logging.getLogger(__name__)

    if search_paths is None:
        # Default search paths
        search_paths = [
            Path.cwd(),
            Path.home(),
        ]

        # Add common manuscript locations
        for common_name in ["MANUSCRIPT", "EXAMPLE_MANUSCRIPT", "manuscript", "paper"]:
            potential_path = Path.cwd() / common_name
            if potential_path.exists():
                search_paths.append(potential_path)

    migrated_count = 0

    for search_path in search_paths:
        if search_path.exists() and search_path.is_dir():
            # Look for .rxiv_cache in this directory
            if migrate_rxiv_cache_directory(search_path, force):
                migrated_count += 1

            # Look for .rxiv_cache in subdirectories (one level deep)
            try:
                for subdir in search_path.iterdir():
                    if subdir.is_dir() and not subdir.name.startswith("."):
                        if migrate_rxiv_cache_directory(subdir, force):
                            migrated_count += 1
            except PermissionError:
                logger.warning(f"Permission denied accessing: {search_path}")

    if migrated_count > 0:
        logger.info(f"Successfully migrated {migrated_count} .rxiv_cache directories")

    return migrated_count


def cleanup_legacy_cache_dir() -> None:
    """Clean up empty legacy cache directory if it exists."""
    legacy_dir = get_legacy_cache_dir()

    if legacy_dir.exists() and legacy_dir.is_dir():
        import contextlib

        with contextlib.suppress(OSError):
            # Only remove if empty
            legacy_dir.rmdir()


def cleanup_legacy_rxiv_cache_dir(source_dir: Path | None = None) -> None:
    """Clean up empty legacy .rxiv_cache directory if it exists.

    Args:
        source_dir: Directory containing .rxiv_cache (if None, uses current directory)
    """
    import contextlib

    if source_dir is None:
        source_dir = Path.cwd()

    legacy_dir = source_dir / ".rxiv_cache"

    if legacy_dir.exists() and legacy_dir.is_dir():
        with contextlib.suppress(OSError):
            # Only remove if empty
            legacy_dir.rmdir()


def validate_cache_migration() -> dict[str, Any]:
    """Validate that cache migration was successful.

    Returns:
        Dictionary with validation results including status and details
    """
    import logging

    logger = logging.getLogger(__name__)

    validation_results: Dict[str, Any] = {
        "success": True,
        "standardized_cache_exists": False,
        "legacy_caches_found": [],
        "permissions_ok": True,
        "disk_space_ok": True,
        "errors": [],
        "warnings": [],
    }

    # Initialize typed lists explicitly to help mypy
    errors: List[str] = validation_results["errors"]
    warnings: List[str] = validation_results["warnings"]
    legacy_caches_found: List[Dict[str, Any]] = validation_results["legacy_caches_found"]

    try:
        # Check if standardized cache directory exists and is accessible
        cache_dir = get_cache_dir()
        validation_results["standardized_cache_exists"] = cache_dir.exists()

        if cache_dir.exists():
            # Check permissions
            if not os.access(cache_dir, os.R_OK | os.W_OK):
                validation_results["permissions_ok"] = False
                errors.append(f"No read/write access to cache directory: {cache_dir}")
                validation_results["success"] = False

            # Check disk space (warn if less than 100MB available)
            try:
                import shutil

                free_space = shutil.disk_usage(cache_dir).free
                if free_space < 100 * 1024 * 1024:  # 100MB
                    validation_results["disk_space_ok"] = False
                    warnings.append(f"Low disk space: {free_space // (1024 * 1024)}MB available")
            except Exception as e:
                warnings.append(f"Could not check disk space: {e}")

        # Check for remaining legacy cache directories
        legacy_locations = [
            (Path.cwd() / ".cache", "Current directory"),
            (Path.cwd() / ".rxiv_cache", "Current directory"),
        ]

        # Add common manuscript directories
        for manuscript_name in ["MANUSCRIPT", "EXAMPLE_MANUSCRIPT", "manuscript", "paper"]:
            manuscript_dir = Path.cwd() / manuscript_name
            if manuscript_dir.exists():
                legacy_locations.extend(
                    [
                        (manuscript_dir / ".cache", f"{manuscript_name} directory"),
                        (manuscript_dir / ".rxiv_cache", f"{manuscript_name} directory"),
                    ]
                )

        for legacy_path, location in legacy_locations:
            if legacy_path.exists():
                legacy_caches_found.append(
                    {
                        "path": str(legacy_path),
                        "location": location,
                        "size": sum(f.stat().st_size for f in legacy_path.rglob("*") if f.is_file()),
                    }
                )
                warnings.append(f"Legacy cache found at {legacy_path}")

        logger.info(f"Cache migration validation: {'PASSED' if validation_results['success'] else 'FAILED'}")

    except Exception as e:
        validation_results["success"] = False
        errors.append(f"Validation error: {e}")
        logger.error(f"Cache migration validation failed: {e}")

    return validation_results


def check_cache_health(detailed: bool = False) -> dict[str, Any]:
    """Check health of cache system.

    Args:
        detailed: If True, include detailed information about cache contents

    Returns:
        Dictionary with cache health information
    """
    import logging
    import os

    logger = logging.getLogger(__name__)

    health_info: Dict[str, Any] = {
        "healthy": True,
        "cache_directory": str(get_cache_dir()),
        "subdirectories": {},
        "total_size": 0,
        "total_files": 0,
        "errors": [],
        "recommendations": [],
    }

    # Initialize typed lists explicitly to help mypy
    errors: List[str] = health_info["errors"]
    recommendations: List[str] = health_info["recommendations"]

    try:
        cache_dir = get_cache_dir()

        if not cache_dir.exists():
            health_info["healthy"] = False
            errors.append("Cache directory does not exist")
            return health_info

        # Check permissions
        if not os.access(cache_dir, os.R_OK | os.W_OK):
            health_info["healthy"] = False
            errors.append("No read/write access to cache directory")

        # Analyze subdirectories
        common_subdirs = ["doi", "bibliography", "figures", "advanced", "updates"]

        for subdir_name in common_subdirs:
            subdir_path = cache_dir / subdir_name
            subdir_info: Dict[str, Any] = {
                "exists": subdir_path.exists(),
                "size": 0,
                "files": 0,
                "last_modified": None,
            }

            if subdir_path.exists():
                try:
                    files = list(subdir_path.rglob("*"))
                    file_files = [f for f in files if f.is_file()]

                    subdir_info["files"] = len(file_files)
                    subdir_info["size"] = sum(f.stat().st_size for f in file_files)

                    if file_files:
                        subdir_info["last_modified"] = max(f.stat().st_mtime for f in file_files)

                    health_info["total_size"] += subdir_info["size"]
                    health_info["total_files"] += subdir_info["files"]

                    if detailed:
                        subdir_info["file_list"] = [str(f.relative_to(subdir_path)) for f in file_files]

                except Exception as e:
                    errors.append(f"Error analyzing {subdir_name}: {e}")
                    subdir_info["error"] = str(e)

            health_info["subdirectories"][subdir_name] = subdir_info

        # Generate recommendations
        if health_info["total_size"] > 500 * 1024 * 1024:  # 500MB
            recommendations.append("Cache size is large (>500MB). Consider cleaning old entries.")

        if health_info["total_files"] > 10000:
            recommendations.append("Many cache files (>10k). Performance may be impacted.")

        # Check for very old files (older than 6 months)
        import time

        six_months_ago = time.time() - (6 * 30 * 24 * 3600)
        old_files = []

        try:
            for subdir_info in health_info["subdirectories"].values():
                if subdir_info.get("last_modified") and subdir_info["last_modified"] < six_months_ago:
                    old_files.append(subdir_info)

            if old_files:
                recommendations.append("Some cache files are older than 6 months. Consider cleaning.")
        except Exception:
            pass  # Not critical

        logger.debug(f"Cache health check completed. Status: {'HEALTHY' if health_info['healthy'] else 'UNHEALTHY'}")

    except Exception as e:
        health_info["healthy"] = False
        errors.append(f"Health check error: {e}")
        logger.error(f"Cache health check failed: {e}")

    return health_info


def generate_migration_report() -> str:
    """Generate a human-readable migration report.

    Returns:
        Formatted string with migration status and recommendations
    """
    validation = validate_cache_migration()
    health = check_cache_health()

    report_lines = [
        "🗂️  Cache Migration Report",
        "=" * 50,
        "",
    ]

    # Migration status
    if validation["success"]:
        report_lines.append("✅ Migration Status: SUCCESS")
    else:
        report_lines.append("❌ Migration Status: FAILED")

    report_lines.append(f"📁 Cache Directory: {health['cache_directory']}")
    report_lines.append("")

    # Errors
    if validation["errors"] or health["errors"]:
        report_lines.append("🚨 Errors:")
        for error in validation["errors"] + health["errors"]:
            report_lines.append(f"   • {error}")
        report_lines.append("")

    # Warnings
    if validation["warnings"]:
        report_lines.append("⚠️  Warnings:")
        for warning in validation["warnings"]:
            report_lines.append(f"   • {warning}")
        report_lines.append("")

    # Legacy caches found
    if validation["legacy_caches_found"]:
        report_lines.append("📦 Legacy Caches Found:")
        for legacy in validation["legacy_caches_found"]:
            size_mb = legacy["size"] / (1024 * 1024)
            report_lines.append(f"   • {legacy['path']} ({size_mb:.1f}MB) in {legacy['location']}")
        report_lines.append("")

    # Cache health
    if health["healthy"]:
        report_lines.append("🏥 Cache Health: HEALTHY")
    else:
        report_lines.append("🏥 Cache Health: UNHEALTHY")

    report_lines.append(f"📊 Total Size: {health['total_size'] / (1024 * 1024):.1f}MB")
    report_lines.append(f"📄 Total Files: {health['total_files']}")
    report_lines.append("")

    # Recommendations
    if health["recommendations"]:
        report_lines.append("💡 Recommendations:")
        for rec in health["recommendations"]:
            report_lines.append(f"   • {rec}")
        report_lines.append("")

    # Next steps
    if validation["legacy_caches_found"]:
        report_lines.extend(
            [
                "🔄 Next Steps:",
                "   • Run migration again if legacy caches contain important data",
                "   • Use 'rxiv clean --cache-only' to clean up legacy caches",
                "   • Verify functionality with new cache system",
            ]
        )
    elif not validation["success"] or not health["healthy"]:
        report_lines.extend(
            [
                "🔄 Next Steps:",
                "   • Review errors above and fix issues",
                "   • Check file permissions on cache directory",
                "   • Ensure adequate disk space is available",
            ]
        )
    else:
        report_lines.extend(
            [
                "🎉 Migration Complete!",
                "   • Cache system is working properly",
                "   • No action required",
            ]
        )

    return "\n".join(report_lines)
