"""Bibliography fixing tool that attempts to find and correct citation information.

This script analyzes bibliography validation issues and attempts to automatically
fix them by searching for publications using CrossRef API based on titles,
authors, and other available metadata.
"""

import logging
import os
import re
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict

import requests

# Add the parent directory to the path to allow imports when run as a script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from crossref_commons.retrieval import get_publication_as_json
except ImportError:
    get_publication_as_json = None
    print("Error: crossref_commons not available")
    print("Install with: pip install crossref-commons")
    sys.exit(1)

from rxiv_maker.core.cache.doi_cache import DOICache
from rxiv_maker.validators.doi_validator import DOIValidator

logger = logging.getLogger(__name__)


class BibliographyFixer:
    """Tool for automatically fixing bibliography issues."""

    def __init__(self, manuscript_path: str, backup: bool = True):
        """Initialize bibliography fixer.

        Args:
            manuscript_path: Path to manuscript directory
            backup: Whether to create backup before modifying
        """
        self.manuscript_path = Path(manuscript_path)
        self.backup = backup
        self.cache = DOICache()
        self.similarity_threshold = 0.8

    def fix_bibliography(self, dry_run: bool = False) -> dict[str, Any]:
        """Fix bibliography issues found by validation.

        Args:
            dry_run: If True, show what would be fixed without making changes

        Returns:
            Dictionary with fixing results and statistics
        """
        bib_file = self.manuscript_path / "03_REFERENCES.bib"
        if not bib_file.exists():
            logger.error(f"Bibliography file not found: {bib_file}")
            return {"success": False, "error": "Bibliography file not found"}

        # Run validation to identify issues
        logger.info("Running validation to identify bibliography issues...")
        doi_validator = DOIValidator(str(self.manuscript_path))
        validation_result = doi_validator.validate()

        # Parse current bibliography
        bib_content = bib_file.read_text(encoding="utf-8")
        entries = self._parse_bibliography(bib_content)

        # Identify entries that need fixing
        problematic_entries = self._identify_problematic_entries(validation_result, entries)

        if not problematic_entries:
            logger.info("No bibliography issues found that can be automatically fixed")
            return {
                "success": True,
                "fixed_count": 0,
                "total_issues": len(validation_result.errors),
            }

        logger.info(f"Found {len(problematic_entries)} entries that may be fixable")

        # Attempt to fix each problematic entry
        fixes = []
        for entry in problematic_entries:
            fix_result = self._attempt_fix_entry(entry)
            if fix_result:
                fixes.append(fix_result)

        if not fixes:
            logger.info("No automatic fixes could be found")
            return {
                "success": True,
                "fixed_count": 0,
                "attempted": len(problematic_entries),
            }

        logger.info(f"Found {len(fixes)} potential fixes")

        if dry_run:
            self._show_dry_run_results(fixes)
            return {"success": True, "dry_run": True, "potential_fixes": len(fixes)}

        # Apply fixes
        if self.backup:
            self._create_backup(bib_file)

        success_count = self._apply_fixes(bib_file, bib_content, fixes)

        return {
            "success": True,
            "fixed_count": success_count,
            "total_fixes_attempted": len(fixes),
            "backup_created": self.backup,
        }

    def _parse_bibliography(self, bib_content: str) -> list[dict[str, Any]]:
        """Parse bibliography entries from BibTeX content."""
        entries = []

        # Pattern to match BibTeX entries
        entry_pattern = re.compile(r"@(\w+)\s*\{\s*([^,\s}]+)\s*,\s*(.*?)\n\}", re.DOTALL | re.IGNORECASE)

        for match in entry_pattern.finditer(bib_content):
            entry_type = match.group(1).lower()
            entry_key = match.group(2)
            fields_text = match.group(3)

            # Extract fields from the entry
            fields = self._extract_bib_fields(fields_text)

            entry = {
                "type": entry_type,
                "key": entry_key,
                "line_start": bib_content[: match.start()].count("\n") + 1,
                "match_start": match.start(),
                "match_end": match.end(),
                "original_text": match.group(0),
                **fields,
            }

            entries.append(entry)

        return entries

    def _extract_bib_fields(self, fields_text: str) -> dict[str, str]:
        """Extract field values from BibTeX entry fields."""
        fields = {}

        # Pattern to match field = {value} or field = value
        field_pattern = re.compile(r"(\w+)\s*=\s*(?:\{([^}]*)\}|([^,\n]+))", re.IGNORECASE)

        for match in field_pattern.finditer(fields_text):
            field_name = match.group(1).lower()
            field_value = match.group(2) or match.group(3)
            if field_value:
                fields[field_name] = field_value.strip()

        return fields

    def _identify_problematic_entries(self, validation_result, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Identify entries that have issues and might be fixable."""
        problematic = []

        # Create a map of line numbers to validation errors
        error_lines = {}
        for error in validation_result.errors:
            if hasattr(error, "line_number") and error.line_number:
                error_lines[error.line_number] = error

        # Find entries that have validation errors
        for entry in entries:
            entry_line = entry.get("line_start")
            if entry_line in error_lines:
                # Check if this is a fixable issue
                error = error_lines[entry_line]
                if self._is_fixable_error(error, entry):
                    entry["validation_error"] = error
                    problematic.append(entry)

        return problematic

    def _is_fixable_error(self, error, entry: dict[str, Any]) -> bool:
        """Check if a validation error can potentially be fixed automatically."""
        # We can try to fix entries that have:
        # 1. Invalid or missing DOI but have title
        # 2. DOI metadata mismatches
        # 3. Missing metadata fields

        if not entry.get("title"):
            return False  # Need at least a title to search

        error_message = error.message.lower()

        # Fixable error types
        fixable_keywords = [
            "could not retrieve metadata",
            "doi does not exist",
            "metadata mismatch",
            "invalid doi format",
            "missing doi",
        ]

        return any(keyword in error_message for keyword in fixable_keywords)

    def _attempt_fix_entry(self, entry: dict[str, Any]) -> dict[str, Any] | None:
        """Attempt to find correct metadata for a bibliography entry."""
        title = entry.get("title", "").strip()
        author = entry.get("author", "").strip()
        year = entry.get("year", "").strip()

        if not title:
            logger.warning(f"Entry {entry['key']} has no title, cannot search")
            return None

        logger.info(f"Searching for: {title}")

        # Try multiple search strategies to find the publication
        candidates = []

        # Strategy 1: Full search with title, author, and year
        candidates = self._search_crossref(title, author, year)

        # Strategy 2: If no candidates, try title + year only
        if not candidates and year:
            logger.info(f"Trying title + year search for {entry['key']}")
            candidates = self._search_crossref(title, "", year)

        # Strategy 3: If still no candidates, try title only
        if not candidates:
            logger.info(f"Trying title-only search for {entry['key']}")
            candidates = self._search_crossref(title, "", "")

        # Strategy 4: Try simplified title (remove special characters)
        if not candidates:
            simplified_title = re.sub(r"[^\w\s]", " ", title).strip()
            if simplified_title != title:
                logger.info(f"Trying simplified title search for {entry['key']}")
                candidates = self._search_crossref(simplified_title, author, year)

        if not candidates:
            logger.warning(f"No candidates found for {entry['key']} after trying multiple search strategies")
            return None

        # Find the best match
        best_match = self._find_best_match(entry, candidates)

        if not best_match:
            logger.warning(f"No good match found for {entry['key']}")
            return None

        # Generate fixed entry
        fixed_entry = self._generate_fixed_entry(entry, best_match)

        return {
            "original_entry": entry,
            "fixed_entry": fixed_entry,
            "crossref_data": best_match,
            "confidence": self._calculate_confidence(entry, best_match),
        }

    def _search_crossref(self, title: str, author: str = "", year: str = "") -> list[dict[str, Any]]:
        """Search CrossRef for publications matching the given criteria."""
        candidates = []

        try:
            # Build search query
            query_parts = [title]
            if author:
                # Extract first author surname for search
                first_author = author.split(",")[0].split(" and ")[0]
                query_parts.append(first_author)
            if year:
                query_parts.append(year)

            query = " ".join(query_parts)

            logger.debug(f"CrossRef query: {query}")

            # Search CrossRef using the correct API
            # Use the work retrieval API with query parameters

            base_url = "https://api.crossref.org/works"
            params: Dict[str, str] = {
                "query": query,
                "rows": "20",  # Increased to find more candidates
                "sort": "relevance",
                "order": "desc",
            }

            headers = {"User-Agent": "Rxiv-Maker/1.0 (mailto:contact@example.com)"}

            response = requests.get(base_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            items = data.get("message", {}).get("items", [])

            for item in items:
                doi = item.get("DOI", "")
                if not doi:
                    continue

                # Validate DOI before accepting as candidate
                if not self._is_doi_valid(doi):
                    logger.debug(f"Skipping invalid DOI: {doi}")
                    continue

                # Extract relevant metadata
                candidate = {
                    "title": item.get("title", [""])[0] if item.get("title") else "",
                    "authors": self._extract_authors(item.get("author", [])),
                    "year": str(
                        item.get("published-print", {}).get("date-parts", [[""]])[0][0]
                        or item.get("published-online", {}).get("date-parts", [[""]])[0][0]
                        or ""
                    ),
                    "journal": item.get("container-title", [""])[0] if item.get("container-title") else "",
                    "doi": doi,
                    "volume": str(item.get("volume", "")),
                    "number": str(item.get("issue", "")),
                    "pages": item.get("page", ""),
                    "publisher": item.get("publisher", ""),
                    "type": item.get("type", "journal-article"),
                }

                candidates.append(candidate)

                # Stop after finding enough valid candidates
                if len(candidates) >= 10:
                    break

        except Exception as e:
            logger.warning(f"CrossRef search failed: {e}")

        return candidates

    def _is_doi_valid(self, doi: str) -> bool:
        """Check if a DOI is valid by testing retrieval from CrossRef."""
        if not doi:
            return False

        # Basic DOI format validation
        doi_pattern = re.compile(r"^10\.\d{4,}/[^\s]+$")
        if not doi_pattern.match(doi):
            logger.debug(f"Invalid DOI format: {doi}")
            return False

        # Check cache first
        cached_result = self.cache.get(doi)
        if cached_result is not None:
            return cached_result.get("status") == "success"

        try:
            # Test DOI validity by attempting to retrieve metadata
            from crossref_commons.retrieval import get_publication_as_json

            result = get_publication_as_json(doi)
            is_valid = result is not None and "DOI" in result

            # Cache the result
            cache_entry = {
                "status": "success" if is_valid else "failed",
                "metadata": result if is_valid else None,
                "timestamp": time.time(),
            }
            self.cache.set(doi, cache_entry)

            return is_valid

        except Exception as e:
            logger.debug(f"DOI validation failed for {doi}: {e}")

            # Cache failure result
            cache_entry = {
                "status": "failed",
                "error": str(e),
                "timestamp": time.time(),
            }
            self.cache.set(doi, cache_entry)

            return False

    def _extract_authors(self, author_list: list[dict[str, Any]]) -> str:
        """Extract author string from CrossRef author list."""
        if not author_list:
            return ""

        authors = []
        for author in author_list:
            given = author.get("given", "")
            family = author.get("family", "")
            if family:
                if given:
                    authors.append(f"{family}, {given}")
                else:
                    authors.append(family)

        return " and ".join(authors)

    def _find_best_match(self, entry: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Find the best matching candidate for the entry."""
        if not candidates:
            return None

        best_match = None
        best_score = 0.0

        entry_title = entry.get("title", "").lower().strip()
        entry_year = entry.get("year", "").strip()

        for candidate in candidates:
            score = 0.0

            # Title similarity (most important)
            candidate_title = candidate.get("title", "").lower().strip()
            if candidate_title and entry_title:
                title_similarity = SequenceMatcher(None, entry_title, candidate_title).ratio()
                score += title_similarity * 0.7

            # Year match
            candidate_year = candidate.get("year", "").strip()
            if entry_year and candidate_year and entry_year == candidate_year:
                score += 0.2

            # Author similarity (if available)
            entry_author = entry.get("author", "").lower()
            candidate_author = candidate.get("authors", "").lower()
            if entry_author and candidate_author:
                author_similarity = SequenceMatcher(None, entry_author, candidate_author).ratio()
                score += author_similarity * 0.1

            if score > best_score and score >= self.similarity_threshold:
                best_score = score
                best_match = candidate

        return best_match

    def _calculate_confidence(self, entry: dict[str, Any], crossref_data: dict[str, Any]) -> float:
        """Calculate confidence score for the match."""
        entry_title = entry.get("title", "").lower().strip()
        candidate_title = crossref_data.get("title", "").lower().strip()

        if not entry_title or not candidate_title:
            return 0.0

        return SequenceMatcher(None, entry_title, candidate_title).ratio()

    def _generate_fixed_entry(self, original: dict[str, Any], crossref_data: dict[str, Any]) -> str:
        """Generate a fixed BibTeX entry from CrossRef data."""
        entry_type = original.get("type", "article")
        entry_key = original["key"]

        # Build the fixed entry
        lines = [f"@{entry_type}{{{entry_key},"]

        # Add fields in standard order
        field_order = [
            "title",
            "author",
            "journal",
            "volume",
            "number",
            "pages",
            "year",
            "publisher",
            "doi",
        ]

        field_mapping = {
            "title": crossref_data.get("title", original.get("title", "")),
            "author": crossref_data.get("authors", original.get("author", "")),
            "journal": crossref_data.get("journal", original.get("journal", "")),
            "volume": crossref_data.get("volume", original.get("volume", "")),
            "number": crossref_data.get("number", original.get("number", "")),
            "pages": crossref_data.get("pages", original.get("pages", "")),
            "year": crossref_data.get("year", original.get("year", "")),
            "publisher": crossref_data.get("publisher", original.get("publisher", "")),
            "doi": crossref_data.get("doi", original.get("doi", "")),
        }

        for field in field_order:
            value = field_mapping.get(field, "").strip()
            if value:
                lines.append(f"    {field} = {{{value}}},")

        lines.append("}")

        return "\n".join(lines)

    def _show_dry_run_results(self, fixes: list[dict[str, Any]]):
        """Show what would be fixed in dry run mode."""
        print("\n" + "=" * 80)
        print("DRY RUN - Potential Bibliography Fixes")
        print("=" * 80)

        for i, fix in enumerate(fixes, 1):
            original = fix["original_entry"]
            confidence = fix["confidence"]
            crossref_data = fix["crossref_data"]

            print(f"\n{i}. Entry: {original['key']} (Confidence: {confidence:.1%})")
            print(f"   Original title: {original.get('title', 'N/A')}")
            print(f"   CrossRef title: {crossref_data.get('title', 'N/A')}")
            print(f"   New DOI: {crossref_data.get('doi', 'N/A')}")

            if confidence < 0.9:
                print("   ⚠️  Low confidence match")

        print(f"\nTotal potential fixes: {len(fixes)}")
        print("Run without --dry-run to apply these fixes")

    def _create_backup(self, bib_file: Path):
        """Create a backup of the bibliography file."""
        backup_file = bib_file.with_suffix(".bib.backup")
        backup_file.write_text(bib_file.read_text(encoding="utf-8"), encoding="utf-8")
        logger.info(f"Created backup: {backup_file}")

    def _apply_fixes(self, bib_file: Path, bib_content: str, fixes: list[dict[str, Any]]) -> int:
        """Apply the fixes to the bibliography file."""
        success_count = 0
        modified_content = bib_content

        # Apply fixes in reverse order to preserve positions
        fixes_sorted = sorted(fixes, key=lambda x: x["original_entry"]["match_start"], reverse=True)

        for fix in fixes_sorted:
            original = fix["original_entry"]
            fixed_entry = fix["fixed_entry"]
            confidence = fix["confidence"]

            if confidence >= 0.8:  # Only apply high-confidence fixes
                start = original["match_start"]
                end = original["match_end"]

                modified_content = modified_content[:start] + fixed_entry + modified_content[end:]

                success_count += 1
                logger.info(f"Fixed entry: {original['key']} (confidence: {confidence:.1%})")
            else:
                logger.warning(f"Skipped low-confidence fix for {original['key']}")

        # Write the modified content
        bib_file.write_text(modified_content, encoding="utf-8")
        logger.info(f"Applied {success_count} fixes to {bib_file}")

        return success_count


def main() -> int:
    """Main entry point for the fix bibliography command.

    Returns:
        0 for success, 1 for failure
    """
    import argparse

    parser = argparse.ArgumentParser(description="Fix bibliography issues automatically")
    parser.add_argument(
        "manuscript_path",
        help="Path to the manuscript directory",
        default=".",
        nargs="?",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes",
    )
    parser.add_argument("--no-backup", action="store_true", help="Don't create backup files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    try:
        fixer = BibliographyFixer(manuscript_path=args.manuscript_path, backup=not args.no_backup)

        results = fixer.fix_bibliography(dry_run=args.dry_run)

        if results["success"]:
            fixes_applied = results.get("fixes_applied", 0)
            if fixes_applied > 0:
                print(f"✅ Successfully applied {fixes_applied} bibliography fixes")
            else:
                print("✅ No fixes were needed")
            return 0
        else:
            print(f"❌ Failed to fix bibliography: {results.get('error', 'Unknown error')}")
            return 1

    except Exception as e:
        print(f"❌ Error fixing bibliography: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
