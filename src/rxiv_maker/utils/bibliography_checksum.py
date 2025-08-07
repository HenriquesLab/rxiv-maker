#!/usr/bin/env python3
"""Bibliography checksum manager for efficient DOI validation.

This module provides checksum-based DOI validation that only re-validates
bibliography files when they actually change, not just when timestamps change.
"""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

from .cache_utils import get_cache_dir, get_legacy_cache_dir, migrate_cache_file

logger = logging.getLogger(__name__)


class BibliographyChecksumManager:
    """Manages checksums for bibliography files to enable efficient DOI validation."""

    def __init__(self, manuscript_path: str, cache_dir: str | None = None):
        """Initialize the bibliography checksum manager.

        Args:
            manuscript_path: Path to the manuscript directory
            cache_dir: Directory for cache files (if None, uses platform-standard location)
        """
        self.manuscript_path = Path(manuscript_path)
        self.manuscript_name = self.manuscript_path.name

        # Use standardized cache directory if not specified
        if cache_dir is None:
            self.cache_dir = get_cache_dir("bibliography")
        else:
            self.cache_dir = Path(cache_dir)

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache file specific to this manuscript
        self.checksum_file = self.cache_dir / f"bibliography_checksum_{self.manuscript_name}.json"
        self.bibliography_file = self.manuscript_path / "03_REFERENCES.bib"

        # Handle migration from legacy cache location
        self._migrate_legacy_cache()

        # Load existing checksum
        self._checksum_data: dict[str, Any] = self._load_checksum()

    def _migrate_legacy_cache(self) -> None:
        """Migrate cache file from legacy location if it exists."""
        if self.cache_dir == get_cache_dir("bibliography"):
            # Only migrate if using new standardized location
            legacy_dir = get_legacy_cache_dir()
            legacy_file = legacy_dir / f"bibliography_checksum_{self.manuscript_name}.json"

            if legacy_file.exists():
                try:
                    migrate_cache_file(legacy_file, self.checksum_file)
                    logger.info(f"Migrated bibliography checksum from {legacy_file} to {self.checksum_file}")
                except Exception as e:
                    logger.warning(f"Failed to migrate bibliography checksum: {e}")

    def _load_checksum(self) -> dict[str, Any]:
        """Load existing checksum from cache file."""
        if not self.checksum_file.exists():
            logger.debug(f"No existing bibliography checksum file found at {self.checksum_file}")
            return {}

        try:
            with open(self.checksum_file, encoding="utf-8") as f:
                checksum_data = json.load(f)
            logger.debug(f"Loaded bibliography checksum from {self.checksum_file}")
            return checksum_data
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load bibliography checksum from {self.checksum_file}: {e}")
            return {}

    def _save_checksum(self) -> None:
        """Save checksum to cache file."""
        try:
            with open(self.checksum_file, "w", encoding="utf-8") as f:
                json.dump(self._checksum_data, f, indent=2, sort_keys=True)
            logger.debug(f"Saved bibliography checksum to {self.checksum_file}")
        except OSError as e:
            logger.error(f"Failed to save bibliography checksum to {self.checksum_file}: {e}")

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

    def _extract_doi_entries(self, content: str) -> dict[str, str]:
        """Extract DOI entries from bibliography content.

        Args:
            content: Bibliography file content

        Returns:
            Dictionary mapping DOI strings to their context for validation
        """
        import re

        # Pattern to match DOI fields in BibTeX entries
        doi_pattern = re.compile(r'doi\s*=\s*[{"\'](.*?)[}"\']', re.IGNORECASE)

        doi_entries = {}
        for match in doi_pattern.finditer(content):
            doi = match.group(1).strip()
            if doi:
                # Get some context around the DOI for validation
                start = max(0, match.start() - 200)
                end = min(len(content), match.end() + 200)
                context = content[start:end]
                doi_entries[doi] = context

        return doi_entries

    def bibliography_has_changed(self) -> tuple[bool, str | None]:
        """Check if bibliography file has changed since last validation.

        Returns:
            Tuple of (has_changed, current_checksum)
        """
        if not self.bibliography_file.exists():
            logger.debug("Bibliography file does not exist")
            return False, None

        current_checksum = self._calculate_file_checksum(self.bibliography_file)
        if not current_checksum:
            logger.warning("Failed to calculate checksum for bibliography file")
            return True, None  # Assume changed if we can't calculate checksum

        cached_checksum = self._checksum_data.get("bibliography_checksum")

        if cached_checksum != current_checksum:
            logger.debug("Bibliography file changed")
            if cached_checksum:
                logger.debug(f"  Old checksum: {cached_checksum}")
                logger.debug(f"  New checksum: {current_checksum}")
            else:
                logger.debug(f"  New file with checksum: {current_checksum}")
            return True, current_checksum
        else:
            logger.debug("Bibliography file unchanged")
            return False, current_checksum

    def doi_entries_have_changed(self) -> tuple[bool, dict[str, str] | None]:
        """Check if DOI entries in bibliography have changed.

        Returns:
            Tuple of (have_changed, current_doi_entries)
        """
        if not self.bibliography_file.exists():
            return False, None

        try:
            with open(self.bibliography_file, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            logger.error(f"Failed to read bibliography file: {e}")
            return True, None

        current_doi_entries = self._extract_doi_entries(content)
        cached_doi_entries = self._checksum_data.get("doi_entries", {})

        if current_doi_entries != cached_doi_entries:
            logger.debug("DOI entries changed")
            logger.debug(f"  Current DOIs: {list(current_doi_entries.keys())}")
            logger.debug(f"  Cached DOIs: {list(cached_doi_entries.keys())}")
            return True, current_doi_entries
        else:
            logger.debug("DOI entries unchanged")
            return False, current_doi_entries

    def needs_validation(self) -> bool:
        """Check if bibliography needs DOI validation.

        Returns:
            True if validation is needed, False otherwise
        """
        # Check if bibliography file has changed
        bib_changed, _ = self.bibliography_has_changed()

        # Check if DOI entries have changed
        doi_changed, _ = self.doi_entries_have_changed()

        needs_validation = bib_changed or doi_changed

        if needs_validation:
            logger.info("Bibliography needs DOI validation")
        else:
            logger.info("Bibliography DOI validation is up to date")

        return needs_validation

    def update_checksum(self, validation_completed: bool = True) -> None:
        """Update checksum after validation is completed.

        Args:
            validation_completed: Whether validation was successfully completed
        """
        if not self.bibliography_file.exists():
            logger.warning("Bibliography file not found for checksum update")
            return

        current_checksum = self._calculate_file_checksum(self.bibliography_file)
        if not current_checksum:
            logger.error("Failed to calculate checksum for bibliography file")
            return

        try:
            with open(self.bibliography_file, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            logger.error(f"Failed to read bibliography file: {e}")
            return

        current_doi_entries = self._extract_doi_entries(content)

        self._checksum_data.update(
            {
                "bibliography_checksum": current_checksum,
                "doi_entries": current_doi_entries,
                "last_validation_completed": validation_completed,
                "last_validation_timestamp": int(time.time()) if validation_completed else None,
            }
        )

        self._save_checksum()
        logger.info(f"Updated bibliography checksum for {len(current_doi_entries)} DOI entries")

    def force_validation(self) -> None:
        """Force validation by clearing cached checksum."""
        logger.info("Forcing bibliography DOI validation")
        self._checksum_data.clear()
        self._save_checksum()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get statistics about the bibliography checksum cache.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "manuscript_name": self.manuscript_name,
            "cache_file": str(self.checksum_file),
            "cache_exists": self.checksum_file.exists(),
            "bibliography_file_exists": self.bibliography_file.exists(),
            "has_cached_checksum": bool(self._checksum_data.get("bibliography_checksum")),
            "cached_doi_count": len(self._checksum_data.get("doi_entries", {})),
            "last_validation_completed": self._checksum_data.get("last_validation_completed"),
            "last_validation_timestamp": self._checksum_data.get("last_validation_timestamp"),
        }

    def clear_cache(self) -> None:
        """Clear all cached checksum data."""
        self._checksum_data.clear()
        if self.checksum_file.exists():
            self.checksum_file.unlink()
        logger.info("Cleared bibliography checksum cache")


def get_bibliography_checksum_manager(
    manuscript_path: str,
) -> BibliographyChecksumManager:
    """Get a BibliographyChecksumManager instance for the given manuscript.

    Args:
        manuscript_path: Path to the manuscript directory

    Returns:
        BibliographyChecksumManager instance
    """
    return BibliographyChecksumManager(manuscript_path)
