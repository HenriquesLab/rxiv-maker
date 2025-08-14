"""Advanced bibliography processing cache for improved performance.

This module provides sophisticated caching for bibliography operations:
- DOI metadata with multi-source fallbacks
- Bibliography parsing and validation results
- Citation network analysis
- Cross-reference resolution
"""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .advanced_cache import AdvancedCache, cached_function

logger = logging.getLogger(__name__)


class BibliographyCache:
    """Advanced caching system for bibliography processing operations."""

    def __init__(self, manuscript_name: Optional[str] = None):
        """Initialize bibliography cache.

        Args:
            manuscript_name: Optional manuscript name for scoped caching
        """
        cache_suffix = f"_{manuscript_name}" if manuscript_name else ""

        # Specialized caches for different operations
        self.doi_metadata_cache = AdvancedCache(
            name=f"doi_metadata{cache_suffix}",
            max_memory_items=500,
            max_disk_size_mb=50,
            ttl_hours=168,  # 1 week
        )

        self.bibliography_cache = AdvancedCache(
            name=f"bibliography{cache_suffix}", max_memory_items=100, max_disk_size_mb=20, ttl_hours=24
        )

        self.validation_cache = AdvancedCache(
            name=f"bib_validation{cache_suffix}", max_memory_items=200, max_disk_size_mb=30, ttl_hours=48
        )

        self.citation_network_cache = AdvancedCache(
            name=f"citation_network{cache_suffix}", max_memory_items=50, max_disk_size_mb=15, ttl_hours=72
        )

    def cache_doi_metadata(
        self,
        doi: str,
        metadata: Dict[str, Any],
        source: str = "crossref",
        validation_status: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Cache DOI metadata with source information.

        Args:
            doi: DOI identifier
            metadata: Metadata from external source
            source: Source name (crossref, datacite, joss, etc.)
            validation_status: Optional validation results
        """
        cache_key = self._generate_doi_key(doi, source)

        cache_data = {
            "doi": doi.lower().strip(),
            "source": source,
            "metadata": metadata,
            "validation_status": validation_status,
            "cached_at": time.time(),
        }

        self.doi_metadata_cache.set(
            cache_key,
            cache_data,
            metadata={"doi": doi, "source": source},
            content_based=False,  # DOI is already a unique key
        )

        logger.debug(f"Cached DOI metadata: {doi} from {source}")

    def get_doi_metadata(self, doi: str, preferred_sources: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Get cached DOI metadata, trying multiple sources.

        Args:
            doi: DOI identifier
            preferred_sources: Ordered list of preferred sources

        Returns:
            Cached metadata if found, None otherwise
        """
        preferred_sources = preferred_sources or ["crossref", "joss", "datacite"]

        for source in preferred_sources:
            cache_key = self._generate_doi_key(doi, source)
            cached_data = self.doi_metadata_cache.get_data(cache_key)

            if cached_data:
                logger.debug(f"DOI cache hit: {doi} from {source}")
                return cached_data

        logger.debug(f"DOI cache miss: {doi}")
        return None

    def cache_bibliography_parsing(
        self, file_path: str, content_hash: str, parsed_entries: List[Dict[str, Any]], parsing_metadata: Dict[str, Any]
    ) -> None:
        """Cache bibliography file parsing results.

        Args:
            file_path: Path to bibliography file
            content_hash: Hash of file content for invalidation
            parsed_entries: Parsed bibliography entries
            parsing_metadata: Metadata about parsing process
        """
        cache_key = f"bib_parse_{Path(file_path).name}_{content_hash}"

        cache_data = {
            "file_path": file_path,
            "content_hash": content_hash,
            "entries": parsed_entries,
            "metadata": parsing_metadata,
            "entry_count": len(parsed_entries),
            "parsed_at": time.time(),
        }

        self.bibliography_cache.set(
            cache_key,
            cache_data,
            metadata={"file_path": file_path, "entry_count": len(parsed_entries)},
            content_based=False,  # Using content_hash already
        )

        logger.debug(f"Cached bibliography parsing: {file_path} ({len(parsed_entries)} entries)")

    def get_bibliography_parsing(self, file_path: str, content_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached bibliography parsing results.

        Args:
            file_path: Path to bibliography file
            content_hash: Hash of current file content

        Returns:
            Cached parsing results if found and valid, None otherwise
        """
        cache_key = f"bib_parse_{Path(file_path).name}_{content_hash}"
        cached_data = self.bibliography_cache.get_data(cache_key)

        if cached_data and cached_data.get("content_hash") == content_hash:
            logger.debug(f"Bibliography parsing cache hit: {file_path}")
            return cached_data

        logger.debug(f"Bibliography parsing cache miss: {file_path}")
        return None

    def cache_validation_results(
        self, validation_key: str, results: List[Dict[str, Any]], summary: Dict[str, Any]
    ) -> None:
        """Cache bibliography validation results.

        Args:
            validation_key: Unique key for validation run
            results: Validation error/warning results
            summary: Summary statistics
        """
        cache_data = {
            "validation_key": validation_key,
            "results": results,
            "summary": summary,
            "validated_at": time.time(),
        }

        self.validation_cache.set(
            validation_key, cache_data, metadata={"error_count": len(results), "summary": summary}, content_based=True
        )

        logger.debug(f"Cached validation results: {validation_key} ({len(results)} issues)")

    def get_validation_results(self, validation_key: str) -> Optional[Dict[str, Any]]:
        """Get cached validation results.

        Args:
            validation_key: Unique key for validation run

        Returns:
            Cached validation results if found, None otherwise
        """
        cached_data = self.validation_cache.get_data(validation_key)

        if cached_data:
            logger.debug(f"Validation cache hit: {validation_key}")
            return cached_data

        logger.debug(f"Validation cache miss: {validation_key}")
        return None

    def cache_citation_network(
        self, citations: Dict[str, List[str]], bibliography_keys: Set[str], network_analysis: Dict[str, Any]
    ) -> None:
        """Cache citation network analysis results.

        Args:
            citations: Citation usage mapping
            bibliography_keys: Set of available bibliography keys
            network_analysis: Analysis results (unused entries, statistics, etc.)
        """
        # Create deterministic key from citation data
        citations_key = self._generate_citations_key(citations, bibliography_keys)

        cache_data = {
            "citations": citations,
            "bibliography_keys": list(bibliography_keys),
            "network_analysis": network_analysis,
            "analyzed_at": time.time(),
        }

        self.citation_network_cache.set(
            citations_key,
            cache_data,
            metadata={"citation_count": len(citations), "bibliography_count": len(bibliography_keys)},
            content_based=False,  # Using custom key generation
        )

        logger.debug(f"Cached citation network: {len(citations)} citations, {len(bibliography_keys)} bib entries")

    def get_citation_network(
        self, citations: Dict[str, List[str]], bibliography_keys: Set[str]
    ) -> Optional[Dict[str, Any]]:
        """Get cached citation network analysis.

        Args:
            citations: Current citation usage mapping
            bibliography_keys: Current bibliography keys

        Returns:
            Cached network analysis if found, None otherwise
        """
        citations_key = self._generate_citations_key(citations, bibliography_keys)
        cached_data = self.citation_network_cache.get_data(citations_key)

        if cached_data:
            logger.debug("Citation network cache hit")
            return cached_data

        logger.debug("Citation network cache miss")
        return None

    def _generate_doi_key(self, doi: str, source: str) -> str:
        """Generate cache key for DOI metadata."""
        normalized_doi = doi.lower().strip()
        return f"doi_{source}_{hashlib.md5(normalized_doi.encode(), usedforsecurity=False).hexdigest()[:12]}"

    def _generate_citations_key(self, citations: Dict[str, List[str]], bibliography_keys: Set[str]) -> str:
        """Generate deterministic key for citation network."""
        # Create sorted representation for consistent hashing
        citation_data = {
            "citations": {k: sorted(v) for k, v in sorted(citations.items())},
            "bibliography": sorted(bibliography_keys),
        }

        json_str = json.dumps(citation_data, sort_keys=True)
        return f"network_{hashlib.md5(json_str.encode(), usedforsecurity=False).hexdigest()[:16]}"

    def bulk_cache_doi_metadata(self, metadata_list: List[Tuple[str, Dict[str, Any], str]]) -> int:
        """Bulk cache multiple DOI metadata entries for efficiency.

        Args:
            metadata_list: List of (doi, metadata, source) tuples

        Returns:
            Number of entries cached
        """
        cached_count = 0

        for doi, metadata, source in metadata_list:
            try:
                self.cache_doi_metadata(doi, metadata, source)
                cached_count += 1
            except Exception as e:
                logger.warning(f"Failed to cache DOI {doi}: {e}")

        return cached_count

    def invalidate_doi(self, doi: str, source: Optional[str] = None) -> int:
        """Invalidate cached DOI metadata.

        Args:
            doi: DOI to invalidate
            source: Optional specific source to invalidate

        Returns:
            Number of entries invalidated
        """
        invalidated = 0

        if source:
            # Invalidate specific source
            cache_key = self._generate_doi_key(doi, source)
            if self.doi_metadata_cache.delete(cache_key):
                invalidated += 1
        else:
            # Invalidate all sources for this DOI
            sources = ["crossref", "datacite", "joss"]
            for src in sources:
                cache_key = self._generate_doi_key(doi, src)
                if self.doi_metadata_cache.delete(cache_key):
                    invalidated += 1

        return invalidated

    def get_cache_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get comprehensive cache statistics."""
        return {
            "doi_metadata": self.doi_metadata_cache.get_stats(),
            "bibliography": self.bibliography_cache.get_stats(),
            "validation": self.validation_cache.get_stats(),
            "citation_network": self.citation_network_cache.get_stats(),
        }

    def cleanup_all_caches(self, max_age_hours: int = 168) -> Dict[str, int]:
        """Clean up all bibliography caches.

        Args:
            max_age_hours: Maximum age in hours for cleanup

        Returns:
            Dictionary with cleanup counts per cache
        """
        cleanup_results = {}

        # Update TTL temporarily for cleanup
        caches = [
            ("doi_metadata", self.doi_metadata_cache),
            ("bibliography", self.bibliography_cache),
            ("validation", self.validation_cache),
            ("citation_network", self.citation_network_cache),
        ]

        for cache_name, cache in caches:
            original_ttl = cache.ttl_seconds
            try:
                cache.ttl_seconds = max_age_hours * 3600
                cleanup_results[cache_name] = cache._cleanup_expired()
            finally:
                cache.ttl_seconds = original_ttl

        return cleanup_results

    def clear_all_caches(self) -> None:
        """Clear all bibliography caches."""
        self.doi_metadata_cache.clear()
        self.bibliography_cache.clear()
        self.validation_cache.clear()
        self.citation_network_cache.clear()

        logger.info("Cleared all bibliography caches")


# Global bibliography cache instance
_global_bibliography_cache: Optional[BibliographyCache] = None


def get_bibliography_cache(manuscript_name: Optional[str] = None) -> BibliographyCache:
    """Get or create global bibliography cache instance."""
    global _global_bibliography_cache

    if _global_bibliography_cache is None or manuscript_name:
        _global_bibliography_cache = BibliographyCache(manuscript_name)

    return _global_bibliography_cache


# Cached function decorators for common bibliography operations
@cached_function(cache_name="bib_parsing", ttl_hours=24, content_based=True, compression=True)
def cached_parse_bibliography(file_path: str, content: str) -> List[Dict[str, Any]]:
    """Cached bibliography parsing function.

    This is a placeholder - actual parsing logic should be implemented
    in the calling code and use this caching mechanism.
    """
    logger.warning(f"Bibliography parsing not yet implemented for {file_path}")
    # Return empty list as safe placeholder
    return []


@cached_function(
    cache_name="doi_validation",
    ttl_hours=168,  # 1 week
    content_based=True,
    compression=True,
)
def cached_validate_doi(doi: str, validation_options: Dict[str, Any]) -> Dict[str, Any]:
    """Cached DOI validation function.

    This is a placeholder - actual validation logic should be implemented
    in the calling code and use this caching mechanism.
    """
    logger.warning(f"DOI validation not yet implemented for {doi}")
    # Return empty dict as safe placeholder
    return {"valid": False, "message": "DOI validation not yet implemented"}


@cached_function(cache_name="citation_analysis", ttl_hours=48, content_based=True, compression=True)
def cached_analyze_citations(manuscript_content: str, bibliography_keys: List[str]) -> Dict[str, Any]:
    """Cached citation analysis function.

    This is a placeholder - actual analysis logic should be implemented
    in the calling code and use this caching mechanism.
    """
    logger.warning(f"Citation analysis not yet implemented for {len(bibliography_keys)} bibliography keys")
    # Return empty analysis as safe placeholder
    return {"citations": [], "missing": [], "unused": []}
