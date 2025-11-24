"""Inline DOI resolution utility for automatic bibliography generation.

This module provides functionality to:
- Detect DOIs and DOI URLs in markdown text
- Fetch metadata and generate bibliography entries
- Replace inline DOIs with proper citation keys
- Update markdown files in-place
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple

from ..engines.operations.add_bibliography import BibliographyAdder
from .url_to_doi import normalize_doi_input

logger = logging.getLogger(__name__)


class DOIResolver:
    """Resolver for inline DOIs in markdown files."""

    # DOI regex pattern from CrossRef documentation
    # DOIs can contain: letters, numbers, hyphens, underscores, periods, semicolons, parentheses, slashes, colons
    # But typically don't END with punctuation like ) . , ;
    DOI_PATTERN = re.compile(
        r"(?:https?://)?(?:dx\.)?doi\.org/(10\.\d{4,9}/[-._:;()/A-Z0-9]+[A-Z0-9])|"  # DOI URLs - must end with alphanumeric
        r"(?<![}\w@])(10\.\d{4,9}/[-._:;()/A-Z0-9]+[A-Z0-9])(?=[\s.,;)\]}]|$)",  # Bare DOIs - must end with alphanumeric, can be followed by punctuation
        re.IGNORECASE,
    )

    def __init__(self, manuscript_path: str):
        """Initialize DOI resolver.

        Args:
            manuscript_path: Path to manuscript directory
        """
        self.manuscript_path = Path(manuscript_path)
        self.bibliography_adder = BibliographyAdder(manuscript_path)
        self.resolved_dois: Dict[str, str] = {}  # DOI -> citation_key mapping
        self.failed_dois: List[str] = []

    def detect_dois_in_text(self, text: str) -> List[Tuple[str, int, int]]:
        """Detect DOIs in markdown text.

        Args:
            text: Markdown text to scan

        Returns:
            List of tuples containing (doi, start_pos, end_pos)
        """
        dois: List[Tuple[str, int, int]] = []

        for match in self.DOI_PATTERN.finditer(text):
            # Extract DOI from match groups
            doi = match.group(1) or match.group(2)
            if doi:
                # Normalize to standard DOI format (remove URL prefix if present)
                try:
                    normalized_doi = normalize_doi_input(doi)
                    dois.append((normalized_doi, match.start(), match.end()))
                except ValueError:
                    logger.debug(f"Skipping invalid DOI format: {doi}")
                    continue

        return dois

    def resolve_dois(self, dois: List[str], warn_on_failure: bool = True) -> Dict[str, str]:
        """Resolve DOIs to citation keys by fetching metadata and adding to bibliography.

        Args:
            dois: List of DOIs to resolve
            warn_on_failure: Whether to log warnings for failed resolutions

        Returns:
            Dictionary mapping DOIs to citation keys
        """
        doi_to_key: Dict[str, str] = {}

        # Get existing entries to find citation keys
        existing_entries = self.bibliography_adder._get_existing_entries()

        for doi in dois:
            try:
                # Check if DOI already exists in bibliography
                if doi in existing_entries:
                    citation_key = existing_entries[doi]
                    doi_to_key[doi] = citation_key
                    logger.debug(f"DOI {doi} already in bibliography with key: {citation_key}")
                    continue

                # Add new entry
                success = self.bibliography_adder.add_entries([doi], overwrite=False)

                if success:
                    # Fetch the citation key for the newly added entry
                    updated_entries = self.bibliography_adder._get_existing_entries()
                    if doi in updated_entries:
                        citation_key = updated_entries[doi]
                        doi_to_key[doi] = citation_key
                        logger.info(f"Resolved DOI {doi} to citation key: {citation_key}")
                    else:
                        if warn_on_failure:
                            logger.warning(f"DOI {doi} was added but citation key not found")
                        self.failed_dois.append(doi)
                else:
                    if warn_on_failure:
                        logger.warning(f"Failed to resolve DOI: {doi}")
                    self.failed_dois.append(doi)

            except Exception as e:
                if warn_on_failure:
                    logger.warning(f"Error resolving DOI {doi}: {e}")
                self.failed_dois.append(doi)

        self.resolved_dois.update(doi_to_key)
        return doi_to_key

    def replace_dois_with_citations(self, text: str, doi_to_key: Dict[str, str]) -> str:
        """Replace inline DOIs with citation keys in markdown text.

        Args:
            text: Original markdown text
            doi_to_key: Dictionary mapping DOIs to citation keys

        Returns:
            Updated markdown text with DOIs replaced by citations
        """
        # Sort DOIs by length (longest first) to handle overlapping matches
        sorted_replacements = sorted(doi_to_key.items(), key=lambda x: len(x[0]), reverse=True)

        result = text
        for doi, citation_key in sorted_replacements:
            # Create citation reference
            citation = f"@{citation_key}"

            # Replace various forms of the DOI
            escaped_doi = re.escape(doi)

            # Patterns in order of specificity (most specific first)
            patterns = [
                # DOI URL inside parentheses: (https://doi.org/10.xxx) -> @key
                (rf"\(https?://(?:dx\.)?doi\.org/{escaped_doi}\)", citation),
                # Bare DOI inside parentheses: (10.xxx) -> @key
                (rf"\({escaped_doi}\)", citation),
                # DOI URL not in parentheses: https://doi.org/10.xxx -> @key
                (rf"https?://(?:dx\.)?doi\.org/{escaped_doi}", citation),
                # Bare DOI not in parentheses: 10.xxx -> @key
                (rf"(?<!\w){escaped_doi}(?![}}@])", citation),
            ]

            for pattern, replacement in patterns:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result

    def process_markdown_file(self, markdown_path: Path, update_file: bool = True) -> Dict[str, any]:
        """Process a markdown file to resolve inline DOIs.

        Args:
            markdown_path: Path to markdown file
            update_file: Whether to update the file in-place

        Returns:
            Dictionary containing resolution results
        """
        if not markdown_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

        # Read markdown content
        original_text = markdown_path.read_text(encoding="utf-8")

        # Detect DOIs
        detected_dois = self.detect_dois_in_text(original_text)
        unique_dois = list({doi for doi, _, _ in detected_dois})

        if not unique_dois:
            return {
                "file": str(markdown_path),
                "dois_found": 0,
                "dois_resolved": 0,
                "dois_failed": 0,
                "updated": False,
            }

        logger.info(f"Found {len(unique_dois)} unique DOI(s) in {markdown_path.name}")

        # Resolve DOIs to citation keys
        doi_to_key = self.resolve_dois(unique_dois, warn_on_failure=True)

        # Replace DOIs with citations
        if doi_to_key:
            updated_text = self.replace_dois_with_citations(original_text, doi_to_key)

            # Update file if requested and text changed
            if update_file and updated_text != original_text:
                markdown_path.write_text(updated_text, encoding="utf-8")
                logger.info(f"Updated {markdown_path.name} with {len(doi_to_key)} citation(s)")
                updated = True
            else:
                updated = False
        else:
            updated_text = original_text
            updated = False

        return {
            "file": str(markdown_path),
            "dois_found": len(unique_dois),
            "dois_resolved": len(doi_to_key),
            "dois_failed": len(self.failed_dois),
            "updated": updated,
            "resolved_dois": doi_to_key,
            "failed_dois": self.failed_dois.copy(),
        }

    def process_manuscript(self, update_files: bool = True) -> Dict[str, any]:
        """Process all markdown files in manuscript directory.

        Args:
            update_files: Whether to update files in-place

        Returns:
            Dictionary containing overall resolution results
        """
        # Find all markdown files in manuscript
        markdown_files = [
            self.manuscript_path / "01_MAIN.md",
            self.manuscript_path / "02_SUPPLEMENTARY_INFO.md",
        ]

        results = {
            "total_dois_found": 0,
            "total_dois_resolved": 0,
            "total_dois_failed": 0,
            "files_updated": 0,
            "files": [],
        }

        for md_file in markdown_files:
            if not md_file.exists():
                continue

            try:
                file_result = self.process_markdown_file(md_file, update_files)
                results["files"].append(file_result)
                results["total_dois_found"] += file_result["dois_found"]
                results["total_dois_resolved"] += file_result["dois_resolved"]
                results["total_dois_failed"] += file_result["dois_failed"]
                if file_result["updated"]:
                    results["files_updated"] += 1
            except Exception as e:
                logger.error(f"Error processing {md_file.name}: {e}")
                continue

        return results


def resolve_inline_dois(manuscript_path: str, update_files: bool = True) -> Dict[str, any]:
    """Convenience function to resolve inline DOIs in a manuscript.

    Args:
        manuscript_path: Path to manuscript directory
        update_files: Whether to update markdown files in-place

    Returns:
        Dictionary containing resolution results
    """
    resolver = DOIResolver(manuscript_path)
    return resolver.process_manuscript(update_files)
