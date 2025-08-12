"""Metadata comparison utilities for DOI validation."""

import logging
from difflib import SequenceMatcher
from typing import Any

logger = logging.getLogger(__name__)


class MetadataComparator:
    """Utility class for comparing metadata between bibliography and external sources."""

    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold

    def compare_metadata(
        self, bib_entry: dict[str, Any], external_metadata: dict[str, Any], source: str = "external"
    ) -> list[str]:
        """Compare bibliography entry with external metadata."""
        differences = []

        # Compare title
        title_diff = self._compare_titles(bib_entry.get("title", ""), external_metadata.get("title", ""))
        if title_diff:
            differences.append(f"Title mismatch ({source}): {title_diff}")

        # Compare authors
        author_diff = self._compare_authors(bib_entry.get("author", []), external_metadata.get("author", []))
        if author_diff:
            differences.append(f"Author mismatch ({source}): {author_diff}")

        # Compare journal
        journal_diff = self._compare_journals(
            bib_entry.get("journal", ""),
            external_metadata.get("container-title", [""])[0]
            if "container-title" in external_metadata
            else external_metadata.get("journal", ""),
        )
        if journal_diff:
            differences.append(f"Journal mismatch ({source}): {journal_diff}")

        # Compare year
        year_diff = self._compare_years(
            bib_entry.get("year", ""),
            str(
                external_metadata.get("published-print", {}).get("date-parts", [[None]])[0][0]
                or external_metadata.get("published-online", {}).get("date-parts", [[None]])[0][0]
                or external_metadata.get("year", "")
            ),
        )
        if year_diff:
            differences.append(f"Year mismatch ({source}): {year_diff}")

        return differences

    def _compare_titles(self, bib_title: str, external_title: str) -> str | None:
        """Compare titles with fuzzy matching."""
        if not bib_title or not external_title:
            return None

        # Clean and normalize titles
        bib_clean = self._clean_title(bib_title)
        ext_clean = self._clean_title(external_title)

        # Calculate similarity
        similarity = SequenceMatcher(None, bib_clean.lower(), ext_clean.lower()).ratio()

        if similarity < self.similarity_threshold:
            return f"'{bib_title}' vs '{external_title}' (similarity: {similarity:.2f})"

        return None

    def _compare_authors(self, bib_authors: list | str, external_authors: list) -> str | None:
        """Compare author lists."""
        if not bib_authors or not external_authors:
            return None

        # Convert string author to list if needed
        if isinstance(bib_authors, str):
            bib_authors = [{"family": name.strip(), "given": ""} for name in bib_authors.split(" and ")]

        # Extract author names for comparison
        bib_names = set()
        for author in bib_authors:
            if isinstance(author, dict):
                family = author.get("family", "")
                given = author.get("given", "")
                bib_names.add(f"{family}, {given}".strip(", "))
            elif isinstance(author, str):
                bib_names.add(author.strip())

        ext_names = set()
        for author in external_authors:
            if isinstance(author, dict):
                family = author.get("family", "")
                given = author.get("given", "")
                ext_names.add(f"{family}, {given}".strip(", "))

        # Check for significant overlap
        intersection = bib_names.intersection(ext_names)
        total_unique = len(bib_names.union(ext_names))

        if total_unique > 0:
            overlap_ratio = len(intersection) / total_unique
            if overlap_ratio < 0.3:  # Less than 30% overlap
                return f"Bibliography: {', '.join(sorted(bib_names))} vs External: {', '.join(sorted(ext_names))}"

        return None

    def _compare_journals(self, bib_journal: str, external_journal: str) -> str | None:
        """Compare journal names."""
        if not bib_journal or not external_journal:
            return None

        # Clean journal names
        bib_clean = self._clean_journal_name(bib_journal)
        ext_clean = self._clean_journal_name(external_journal)

        # Calculate similarity
        similarity = SequenceMatcher(None, bib_clean.lower(), ext_clean.lower()).ratio()

        if similarity < self.similarity_threshold:
            return f"'{bib_journal}' vs '{external_journal}' (similarity: {similarity:.2f})"

        return None

    def _compare_years(self, bib_year: str, external_year: str) -> str | None:
        """Compare publication years."""
        if not bib_year or not external_year:
            return None

        # Extract numeric year
        try:
            bib_year_num = int(str(bib_year).strip())
            ext_year_num = int(str(external_year).strip())

            if abs(bib_year_num - ext_year_num) > 1:  # Allow 1 year difference
                return f"'{bib_year}' vs '{external_year}'"
        except (ValueError, TypeError):
            # If conversion fails, do string comparison
            if str(bib_year).strip() != str(external_year).strip():
                return f"'{bib_year}' vs '{external_year}'"

        return None

    def _clean_title(self, title: str) -> str:
        """Clean title for comparison."""
        import re

        # Remove LaTeX commands and special characters
        cleaned = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", title)  # Remove LaTeX commands
        cleaned = re.sub(r"[{}$\\]", "", cleaned)  # Remove LaTeX special chars
        cleaned = re.sub(r"[^\w\s-]", " ", cleaned)  # Remove punctuation except hyphens
        cleaned = re.sub(r"\s+", " ", cleaned)  # Normalize whitespace

        return cleaned.strip()

    def _clean_journal_name(self, journal: str) -> str:
        """Clean journal name for comparison."""
        import re

        # Common journal name normalizations
        cleaned = journal.strip()
        cleaned = re.sub(r"\b(The|A|An)\s+", "", cleaned, flags=re.IGNORECASE)  # Remove articles
        cleaned = re.sub(r"[^\w\s&]", " ", cleaned)  # Remove punctuation except &
        cleaned = re.sub(r"\s+", " ", cleaned)  # Normalize whitespace

        return cleaned.strip()

    def compare_joss_metadata(self, bib_entry: dict[str, Any], joss_metadata: dict[str, Any]) -> list[str]:
        """Compare bibliography entry with JOSS metadata."""
        differences = []

        # Compare title
        title_diff = self._compare_titles(bib_entry.get("title", ""), joss_metadata.get("title", ""))
        if title_diff:
            differences.append(f"Title mismatch (JOSS): {title_diff}")

        # Compare authors
        bib_authors = bib_entry.get("author", [])
        joss_authors = joss_metadata.get("author", [])

        author_diff = self._compare_authors(bib_authors, joss_authors)
        if author_diff:
            differences.append(f"Author mismatch (JOSS): {author_diff}")

        # Compare year
        year_diff = self._compare_years(bib_entry.get("year", ""), joss_metadata.get("year", ""))
        if year_diff:
            differences.append(f"Year mismatch (JOSS): {year_diff}")

        return differences

    def compare_datacite_metadata(self, bib_entry: dict[str, Any], datacite_metadata: dict[str, Any]) -> list[str]:
        """Compare bibliography entry with DataCite metadata."""
        differences = []

        # Compare title
        title_diff = self._compare_titles(bib_entry.get("title", ""), datacite_metadata.get("title", ""))
        if title_diff:
            differences.append(f"Title mismatch (DataCite): {title_diff}")

        # Compare authors
        author_diff = self._compare_authors(bib_entry.get("author", []), datacite_metadata.get("author", []))
        if author_diff:
            differences.append(f"Author mismatch (DataCite): {author_diff}")

        # Compare publisher vs journal with relaxed matching
        # DataCite often returns the parent publisher while bib has specific journal name
        journal_diff = self._compare_publisher_journal(
            bib_entry.get("journal", ""), datacite_metadata.get("publisher", "")
        )
        if journal_diff:
            differences.append(f"Publisher/Journal mismatch (DataCite): {journal_diff}")

        # Compare year
        year_diff = self._compare_years(bib_entry.get("year", ""), datacite_metadata.get("year", ""))
        if year_diff:
            differences.append(f"Year mismatch (DataCite): {year_diff}")

        return differences

    def _compare_publisher_journal(self, bib_journal: str, datacite_publisher: str) -> str | None:
        """Compare journal name against publisher with relaxed matching for common patterns."""
        if not bib_journal or not datacite_publisher:
            return None

        # Clean names for comparison
        bib_clean = self._clean_journal_name(bib_journal).lower()
        pub_clean = self._clean_journal_name(datacite_publisher).lower()

        # Check for known publisher-journal relationships that should not be flagged
        publisher_journal_mappings = {
            # Common publishers and their journal patterns
            "springer": ["springer", "nature", "bmr", "biomed"],
            "ieee": ["ieee", "computer", "engineering", "science"],
            "acm": ["acm", "computing", "machine", "computer"],
            "elsevier": ["elsevier", "science", "cell", "lancet"],
            "oxford": ["oxford", "oup", "journal", "university"],
            "cambridge": ["cambridge", "university", "press"],
            "wiley": ["wiley", "journal", "science"],
            "plos": ["plos", "public", "library", "science", "one", "computational", "biology"],
            "mit": ["mit", "press", "quantitative", "science"],
            "open journal": ["joss", "open", "source", "software"],
        }

        # Check if this looks like a publisher-journal relationship
        for publisher_key, journal_patterns in publisher_journal_mappings.items():
            if publisher_key in pub_clean:
                # If publisher matches and journal contains related terms, it's probably valid
                if any(pattern in bib_clean for pattern in journal_patterns):
                    return None  # Don't report this as a mismatch

        # Use more relaxed similarity threshold for publisher-journal comparisons (0.4 instead of 0.8)
        from difflib import SequenceMatcher

        similarity = SequenceMatcher(None, bib_clean, pub_clean).ratio()
        if similarity < 0.4:  # Much more relaxed for publisher/journal mismatches
            return f"'{bib_journal}' vs '{datacite_publisher}' (similarity: {similarity:.2f})"

        return None
