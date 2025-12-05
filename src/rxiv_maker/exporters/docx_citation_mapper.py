"""Citation mapper for DOCX export.

This module provides functionality to map citation keys to sequential numbers
for numbered citation format in DOCX exports.
"""

import re
from typing import Dict, List

from ..converters.citation_processor import extract_citations_from_text


class CitationMapper:
    """Maps citation keys to sequential numbers for DOCX export."""

    def create_mapping(self, citations: List[str]) -> Dict[str, int]:
        """Create citation key → number mapping.

        Args:
            citations: Ordered list of citation keys (by first appearance)

        Returns:
            Dict mapping citation keys to sequential numbers starting from 1

        Example:
            >>> mapper = CitationMapper()
            >>> mapping = mapper.create_mapping(["smith2021", "jones2022", "smith2021"])
            >>> mapping
            {'smith2021': 1, 'jones2022': 2}
        """
        # Deduplicate while preserving order (first appearance)
        seen = set()
        unique_citations = []
        for cite in citations:
            if cite not in seen:
                seen.add(cite)
                unique_citations.append(cite)

        # Create numbered mapping starting from 1
        return {key: idx + 1 for idx, key in enumerate(unique_citations)}

    def extract_citations_from_markdown(self, text: str) -> List[str]:
        """Extract citations from markdown text in order of first appearance.

        Uses existing citation_processor infrastructure to ensure consistency
        with LaTeX citation extraction.

        Args:
            text: Markdown text containing citations

        Returns:
            List of citation keys in order of first appearance

        Example:
            >>> mapper = CitationMapper()
            >>> text = "Study by @smith2021 and others [@jones2022;@brown2023]"
            >>> mapper.extract_citations_from_markdown(text)
            ['smith2021', 'jones2022', 'brown2023']
        """
        return extract_citations_from_text(text)

    def replace_citations_in_text(self, text: str, citation_map: Dict[str, int]) -> str:
        """Replace @key citations with [number] format in text.

        Handles both single citations (@key) and multiple citations ([@key1;@key2]).
        Preserves figure and equation references (@fig:, @eq:, @tbl:).

        Args:
            text: Text containing markdown citations
            citation_map: Mapping from citation keys to numbers

        Returns:
            Text with citations replaced by numbers

        Example:
            >>> mapper = CitationMapper()
            >>> text = "Study by @smith2021 and others [@jones2022;@brown2023]"
            >>> mapping = {"smith2021": 1, "jones2022": 2, "brown2023": 3}
            >>> mapper.replace_citations_in_text(text, mapping)
            'Study by [1] and others [2, 3]'
        """
        # First, protect email addresses by temporarily replacing them
        email_patterns = []

        def protect_email(match):
            email_patterns.append(match.group(0))
            return f"__EMAIL_PATTERN_{len(email_patterns) - 1}__"

        # Match email-like patterns: word@word.word or @word.word (domain patterns)
        text = re.sub(r"(\w+@[\w.-]+\.\w+|@[\w.-]+\.\w+)", protect_email, text)

        # Handle multiple bracketed citations: [@cite1;@cite2;@cite3]
        def replace_bracketed(match):
            cite_text = match.group(1)
            # Split by semicolon and extract keys
            keys = [k.strip().lstrip("@").strip() for k in cite_text.split(";")]
            # Map to numbers
            numbers = [str(citation_map[k]) for k in keys if k in citation_map]
            if numbers:
                return f"[{', '.join(numbers)}]"
            # If no valid citations found, return original
            return match.group(0)

        text = re.sub(r"\[@([^]]+)\]", replace_bracketed, text)

        # Handle single citations: @key (but not @fig:, @eq:, @tbl:, @stable:, @sfig:, @snote:)
        def replace_single(match):
            key = match.group(1)
            if key in citation_map:
                return f"[{citation_map[key]}]"
            # If key not in mapping, return original
            return match.group(0)

        text = re.sub(
            r"@(?!fig:|eq:|tbl:|table:|sfig:|stable:|snote:)([a-zA-Z0-9_-]+)",
            replace_single,
            text,
        )

        # Restore protected email patterns
        for i, pattern in enumerate(email_patterns):
            text = text.replace(f"__EMAIL_PATTERN_{i}__", pattern)

        return text
