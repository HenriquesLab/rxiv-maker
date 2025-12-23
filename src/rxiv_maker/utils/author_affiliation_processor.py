"""Author and affiliation processing utilities for manuscript processing.

This module provides centralized author and affiliation mapping logic used by both
DOCX export and LaTeX/PDF generation to ensure consistent handling across formats.

The processor handles:
- Building affiliation shortname → number mappings in order of first appearance
- Looking up full affiliation details from metadata
- Categorizing authors (co-first, corresponding)
- Mapping author affiliations to sequential numbers

Examples:
    >>> processor = AuthorAffiliationProcessor()
    >>> metadata = {
    ...     "authors": [{"name": "Alice", "affiliations": ["MIT"], "co_first_author": True}],
    ...     "affiliations": [{"shortname": "MIT", "full_name": "MIT", "location": "Cambridge"}]
    ... }
    >>> result = processor.process(metadata)
    >>> result["affiliation_map"]
    {'MIT': 1}
    >>> result["cofirst_authors"]
    [{'name': 'Alice', 'affiliations': ['MIT'], 'co_first_author': True}]
"""

from typing import Any, Dict, List


class AuthorAffiliationProcessor:
    """Process author and affiliation metadata for manuscript generation."""

    def process(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process author and affiliation metadata.

        Extracts and organizes author/affiliation data for use by format-specific
        renderers (DOCX, LaTeX, etc.).

        Args:
            metadata: YAML metadata containing authors and affiliations

        Returns:
            Dict containing:
                - affiliation_map: Dict[str, int] mapping shortnames to numbers
                - ordered_affiliations: List[Tuple[int, str, str]] of (number, shortname, full_text)
                - authors: List[Dict] of author metadata
                - cofirst_authors: List[Dict] of co-first authors
                - corresponding_authors: List[Dict] of corresponding authors

        Examples:
            >>> processor = AuthorAffiliationProcessor()
            >>> metadata = {
            ...     "authors": [
            ...         {"name": "Alice", "affiliations": ["MIT"], "co_first_author": True},
            ...         {"name": "Bob", "affiliations": ["MIT", "Harvard"], "corresponding_author": True}
            ...     ],
            ...     "affiliations": [
            ...         {"shortname": "MIT", "full_name": "Massachusetts Institute of Technology", "location": "Cambridge, MA"},
            ...         {"shortname": "Harvard", "full_name": "Harvard University", "location": "Cambridge, MA"}
            ...     ]
            ... }
            >>> result = processor.process(metadata)
            >>> result["affiliation_map"]
            {'MIT': 1, 'Harvard': 2}
            >>> len(result["cofirst_authors"])
            1
            >>> len(result["corresponding_authors"])
            1
        """
        authors = metadata.get("authors", [])
        affiliations = metadata.get("affiliations", [])

        # Build affiliation details lookup
        affiliation_details = {a.get("shortname"): a for a in affiliations if isinstance(a, dict)}

        # Build affiliation map in order of first appearance
        affiliation_map = {}
        ordered_affiliations = []

        for author in authors:
            if isinstance(author, dict):
                author_affiliations = author.get("affiliations", [])
                for affil_shortname in author_affiliations:
                    if affil_shortname not in affiliation_map:
                        # Assign next number
                        affil_num = len(affiliation_map) + 1
                        affiliation_map[affil_shortname] = affil_num

                        # Look up full details
                        affil_info = affiliation_details.get(affil_shortname, {})
                        full_name = affil_info.get("full_name", affil_shortname)
                        location = affil_info.get("location", "")

                        # Format: "Full Name, Location" or just "Full Name"
                        full_text = f"{full_name}, {location}" if location else full_name

                        ordered_affiliations.append((affil_num, affil_shortname, full_text))

        # Categorize authors
        cofirst_authors = [a for a in authors if isinstance(a, dict) and a.get("co_first_author", False)]
        corresponding_authors = [a for a in authors if isinstance(a, dict) and a.get("corresponding_author", False)]

        return {
            "affiliation_map": affiliation_map,
            "ordered_affiliations": ordered_affiliations,
            "authors": authors,
            "cofirst_authors": cofirst_authors,
            "corresponding_authors": corresponding_authors,
        }

    def get_author_affiliation_numbers(self, author: Dict[str, Any], affiliation_map: Dict[str, int]) -> List[int]:
        """Get sorted affiliation numbers for an author.

        Args:
            author: Author metadata dict
            affiliation_map: Mapping from shortname to number

        Returns:
            Sorted list of affiliation numbers for this author

        Examples:
            >>> processor = AuthorAffiliationProcessor()
            >>> author = {"name": "Alice", "affiliations": ["Harvard", "MIT"]}
            >>> affil_map = {"MIT": 1, "Harvard": 2}
            >>> processor.get_author_affiliation_numbers(author, affil_map)
            [1, 2]
        """
        author_affiliations = author.get("affiliations", [])
        affil_numbers = [affiliation_map[a] for a in author_affiliations if a in affiliation_map]
        return sorted(affil_numbers)
