#!/usr/bin/env python3
"""Figure checksum manager for efficient figure regeneration.

This module provides checksum-based figure regeneration that only regenerates
figures when source files (.mmd, .py, .R) actually change, not just when
timestamps change.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from ..core.cache.cache_utils import get_cache_dir, get_legacy_cache_dir, migrate_cache_file

logger = logging.getLogger(__name__)


class FigureChecksumManager:
    """Manages checksums for figure source files to enable efficient regeneration."""

    def __init__(self, manuscript_path: str, cache_dir: str | None = None):
        """Initialize the checksum manager.

        Args:
            manuscript_path: Path to the manuscript directory
            cache_dir: Directory for cache files (if None, uses platform-standard location)
        """
        self.manuscript_path = Path(manuscript_path)
        self.manuscript_name = self.manuscript_path.name

        # Use standardized cache directory if not specified
        if cache_dir is None:
            self.cache_dir = get_cache_dir("figures")
        else:
            self.cache_dir = Path(cache_dir)

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache file specific to this manuscript
        self.checksum_file = self.cache_dir / f"figure_checksums_{self.manuscript_name}.json"
        self.figures_dir = self.manuscript_path / "FIGURES"

        # Handle migration from legacy cache location
        self._migrate_legacy_cache()

        # Load existing checksums
        self._checksums: dict[str, str] = self._load_checksums()

    def _migrate_legacy_cache(self) -> None:
        """Migrate cache file from legacy location if it exists."""
        if self.cache_dir == get_cache_dir("figures"):
            # Only migrate if using new standardized location
            legacy_dir = get_legacy_cache_dir()
            legacy_file = legacy_dir / f"figure_checksums_{self.manuscript_name}.json"

            if legacy_file.exists():
                try:
                    migrate_cache_file(legacy_file, self.checksum_file)
                    logger.info(f"Migrated figure checksums from {legacy_file} to {self.checksum_file}")
                except Exception as e:
                    logger.warning(f"Failed to migrate figure checksums: {e}")

    def _load_checksums(self) -> dict[str, str]:
        """Load existing checksums from cache file."""
        if not self.checksum_file.exists():
            logger.debug(f"No existing checksum file found at {self.checksum_file}")
            return {}

        try:
            with open(self.checksum_file, encoding="utf-8") as f:
                checksums = json.load(f)
            logger.debug(f"Loaded {len(checksums)} checksums from {self.checksum_file}")
            return checksums
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load checksums from {self.checksum_file}: {e}")
            return {}

    def _save_checksums(self) -> None:
        """Save checksums to cache file."""
        try:
            with open(self.checksum_file, "w", encoding="utf-8") as f:
                json.dump(self._checksums, f, indent=2, sort_keys=True)
            logger.debug(f"Saved {len(self._checksums)} checksums to {self.checksum_file}")
        except OSError as e:
            logger.error(f"Failed to save checksums to {self.checksum_file}: {e}")

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum for a file.

        Args:
            file_path: Path to the file

        Returns:
            SHA256 checksum as hex string
        """
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except OSError as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            return ""

    def get_figure_source_files(self) -> list[Path]:
        """Get all figure source files in the FIGURES directory.

        Returns:
            List of Path objects for .mmd, .py, and .R files
        """
        if not self.figures_dir.exists():
            return []

        source_files: list[Path] = []
        for pattern in ["*.mmd", "*.py", "*.R"]:
            source_files.extend(self.figures_dir.glob(pattern))

        return sorted(source_files)

    def get_changed_files(self) -> list[Path]:
        """Get list of figure source files that have changed.

        Returns:
            List of Path objects for files that have changed or are new
        """
        changed_files = []
        source_files = self.get_figure_source_files()

        for file_path in source_files:
            relative_path = file_path.relative_to(self.figures_dir)
            file_key = str(relative_path)

            current_checksum = self._calculate_file_checksum(file_path)
            if not current_checksum:
                continue

            cached_checksum = self._checksums.get(file_key)

            if cached_checksum != current_checksum:
                changed_files.append(file_path)
                logger.debug(f"File changed: {file_key}")
                if cached_checksum:
                    logger.debug(f"  Old checksum: {cached_checksum}")
                    logger.debug(f"  New checksum: {current_checksum}")
                else:
                    logger.debug(f"  New file with checksum: {current_checksum}")

        return changed_files

    def check_figures_need_update(self) -> bool:
        """Check if any figures need to be updated.

        Returns:
            True if any figure source files have changed, False otherwise
        """
        changed_files = self.get_changed_files()

        if changed_files:
            logger.info(f"Found {len(changed_files)} changed figure source files")
            for file_path in changed_files:
                logger.info(f"  Changed: {file_path.name}")
            return True
        else:
            logger.info("All figure source files are up to date")
            return False

    def has_file_changed(self, relative_path: str) -> bool:
        """Check if a specific file has changed based on its checksum.

        Args:
            relative_path: Relative path from figures directory

        Returns:
            True if file has changed or is new, False if unchanged
        """
        file_path = self.figures_dir / relative_path
        if not file_path.exists():
            return True  # File doesn't exist, consider it changed

        current_checksum = self._calculate_file_checksum(file_path)
        if not current_checksum:
            return True  # Can't calculate checksum, assume changed

        cached_checksum = self._checksums.get(relative_path)
        return cached_checksum != current_checksum

    def update_file_checksum(self, relative_path: str) -> None:
        """Update checksum for a specific file.

        Args:
            relative_path: Relative path from figures directory
        """
        file_path = self.figures_dir / relative_path
        if not file_path.exists():
            logger.warning(f"File not found for checksum update: {file_path}")
            return

        current_checksum = self._calculate_file_checksum(file_path)
        if current_checksum:
            self._checksums[relative_path] = current_checksum
            self._save_checksums()
            logger.debug(f"Updated checksum for {relative_path}: {current_checksum}")

    def update_checksums(self, files: list[Path] | None = None) -> None:
        """Update checksums for specified files or all source files.

        Args:
            files: Optional list of specific files to update. If None, updates all source files.
        """
        if files is None:
            files = self.get_figure_source_files()

        updated_count = 0
        for file_path in files:
            if not file_path.exists():
                logger.warning(f"File not found for checksum update: {file_path}")
                continue

            relative_path = file_path.relative_to(self.figures_dir)
            file_key = str(relative_path)

            current_checksum = self._calculate_file_checksum(file_path)
            if current_checksum:
                self._checksums[file_key] = current_checksum
                updated_count += 1
                logger.debug(f"Updated checksum for {file_key}: {current_checksum}")

        if updated_count > 0:
            self._save_checksums()
            logger.info(f"Updated checksums for {updated_count} files")

    def cleanup_orphaned_checksums(self) -> None:
        """Remove checksums for files that no longer exist."""
        if not self.figures_dir.exists():
            # If FIGURES directory doesn't exist, clear all checksums
            if self._checksums:
                self._checksums.clear()
                self._save_checksums()
                logger.info("Cleared all checksums - FIGURES directory not found")
            return

        current_files = {str(f.relative_to(self.figures_dir)) for f in self.get_figure_source_files()}
        cached_files = set(self._checksums.keys())
        orphaned_files = cached_files - current_files

        if orphaned_files:
            for file_key in orphaned_files:
                del self._checksums[file_key]
                logger.debug(f"Removed orphaned checksum for {file_key}")

            self._save_checksums()
            logger.info(f"Cleaned up {len(orphaned_files)} orphaned checksums")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get statistics about the checksum cache.

        Returns:
            Dictionary with cache statistics
        """
        source_files = self.get_figure_source_files()
        cached_files = set(self._checksums.keys())
        current_files = {str(f.relative_to(self.figures_dir)) for f in source_files}

        return {
            "manuscript_name": self.manuscript_name,
            "cache_file": str(self.checksum_file),
            "cache_exists": self.checksum_file.exists(),
            "total_cached": len(self._checksums),
            "total_source_files": len(source_files),
            "orphaned_entries": len(cached_files - current_files),
            "new_files": len(current_files - cached_files),
            "figures_dir_exists": self.figures_dir.exists(),
        }

    def force_update_all(self) -> None:
        """Force update all checksums regardless of current state."""
        logger.info("Forcing update of all figure checksums")
        self.update_checksums()

    def clear_cache(self) -> None:
        """Clear all checksums from cache."""
        self._checksums.clear()
        if self.checksum_file.exists():
            self.checksum_file.unlink()
        logger.info("Cleared all cached checksums")


def get_figure_checksum_manager(manuscript_path: str) -> FigureChecksumManager:
    """Get a FigureChecksumManager instance for the given manuscript.

    Args:
        manuscript_path: Path to the manuscript directory

    Returns:
        FigureChecksumManager instance
    """
    return FigureChecksumManager(manuscript_path)
