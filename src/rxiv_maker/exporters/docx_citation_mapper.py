"""Citation mapper for DOCX export.

This module maps citation keys to their in-text representation for DOCX
exports, supporting both numbered ([1]) and author-date ((Smith et al., 2021))
styles as selected by the ``citation_style`` config key.
"""

import re
from typing import Dict, List, Union

from ..converters.citation_processor import extract_citations_from_text
from ..utils.citation_range_formatter import format_citation_ranges

# An author-date label carries both rendering forms: parenthetical for
# bracketed citations and textual for narrative ones.
AuthorDateLabel = Dict[str, str]
CitationValue = Union[int, AuthorDateLabel]


def _surname(name: str) -> str:
    """Extract a surname from a single BibTeX author name."""
    name = name.strip().strip("{}").strip()
    if not name:
        return ""
    if "," in name:
        return name.split(",")[0].strip().strip("{}")
    parts = name.split()
    return parts[-1].strip("{}") if parts else ""


def _author_label(author_field: str) -> str:
    """Build the author portion of an author-date citation."""
    names = [n for n in (p.strip() for p in author_field.split(" and ")) if n]
    surnames = [s for s in (_surname(n) for n in names) if s]
    if not surnames:
        return "Anon."
    if len(surnames) == 1:
        return surnames[0]
    if len(surnames) == 2:
        return f"{surnames[0]} and {surnames[1]}"
    return f"{surnames[0]} et al."


class CitationMapper:
    """Maps citation keys to their in-text form for DOCX export."""

    def __init__(self, citation_style: str = "numbered"):
        """Initialise the mapper.

        Args:
            citation_style: Either "numbered" or "author-date"
        """
        self.citation_style = citation_style

    @staticmethod
    def _protect_code(text: str):
        """Replace fenced and inline code with placeholders.

        Citation syntax shown as a code example must survive verbatim. Fenced
        blocks are matched before inline spans so a single backtick cannot pair
        across a fence boundary.
        """
        blocks: List[str] = []

        def stash(match):
            blocks.append(match.group(0))
            return f"__DOCX_CODE_SPAN_{len(blocks) - 1}__"

        text = re.sub(r"```.*?```", stash, text, flags=re.DOTALL)
        text = re.sub(r"`[^`]+`", stash, text)
        return text, blocks

    @staticmethod
    def _restore_code(text: str, blocks: List[str]) -> str:
        """Reinstate code spans stashed by :meth:`_protect_code`."""
        for i, block in enumerate(blocks):
            text = text.replace(f"__DOCX_CODE_SPAN_{i}__", block)
        return text

    def create_author_date_mapping(self, citations: List[str], entries_by_key: Dict) -> Dict[str, AuthorDateLabel]:
        """Create citation key to author-date label mapping.

        Keys sharing an author-year pair are disambiguated with a letter suffix
        in order of first appearance, giving (Smith, 2021a) and (Smith, 2021b).

        Args:
            citations: Ordered list of citation keys (by first appearance)
            entries_by_key: Bibliography entries keyed by citation key

        Returns:
            Dict mapping each key to its parenthetical and textual forms
        """
        seen = set()
        unique = []
        for cite in citations:
            if cite not in seen:
                seen.add(cite)
                unique.append(cite)

        base: Dict[str, tuple] = {}
        for key in unique:
            entry = entries_by_key.get(key)
            if entry is None:
                continue
            author = _author_label(entry.fields.get("author", ""))
            year = entry.fields.get("year", "n.d.").strip()
            base[key] = (author, year)

        collisions: Dict[tuple, List[str]] = {}
        for key, pair in base.items():
            collisions.setdefault(pair, []).append(key)

        mapping: Dict[str, AuthorDateLabel] = {}
        for key, (author, year) in base.items():
            shared = collisions[(author, year)]
            suffix = chr(ord("a") + shared.index(key)) if len(shared) > 1 else ""
            stamped = f"{year}{suffix}"
            mapping[key] = {
                "paren": f"{author}, {stamped}",
                "text": f"{author} ({stamped})",
                "sort": f"{author} {stamped}".lower(),
            }
        return mapping

    @staticmethod
    def _format_citation_ranges(text: str) -> str:
        """Format consecutive citations as ranges.

        Uses centralized citation range formatter from utils module.

        Args:
            text: Text with numbered citations

        Returns:
            Text with consecutive citations formatted as ranges
        """
        return format_citation_ranges(text)

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

    def replace_citations_in_text(self, text: str, citation_map: Dict[str, CitationValue]) -> str:
        """Replace @key citations with their rendered in-text form.

        Handles both single citations (@key) and multiple citations ([@key1;@key2]).
        Preserves figure and equation references (@fig:, @eq:, @tbl:), and leaves
        citation syntax inside code spans untouched so tutorials can show it.

        Args:
            text: Text containing markdown citations
            citation_map: Mapping from citation keys to numbers, or to
                author-date labels when citation_style is "author-date"

        Returns:
            Text with citations replaced

        Example:
            >>> mapper = CitationMapper()
            >>> text = "Study by @smith2021 and others [@jones2022;@brown2023]"
            >>> mapping = {"smith2021": 1, "jones2022": 2, "brown2023": 3}
            >>> mapper.replace_citations_in_text(text, mapping)
            'Study by [1] and others [2, 3]'
        """
        author_date = self.citation_style == "author-date"

        # Citation syntax shown as a code example is documentation, not a
        # citation, so hide it before any substitution runs.
        text, code_blocks = self._protect_code(text)

        # Protect email addresses by temporarily replacing them
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
            rendered = [citation_map[k] for k in keys if k in citation_map]
            if not rendered:
                # If no valid citations found, return original
                return match.group(0)
            if author_date:
                return f"({'; '.join(r['paren'] for r in rendered)})"
            return f"[{', '.join(str(r) for r in rendered)}]"

        text = re.sub(r"\[@([^]]+)\]", replace_bracketed, text)

        # Handle single citations: @key (but not @fig:, @eq:, @tbl:, @stable:, @sfig:, @snote:)
        def replace_single(match):
            key = match.group(1)
            if key in citation_map:
                if author_date:
                    return citation_map[key]["text"]
                return f"[{citation_map[key]}]"
            # If key not in mapping, return original
            return match.group(0)

        text = re.sub(
            r"@(?!fig:|eq:|tbl:|table:|sfig:|stable:|snote:|svideo:)([a-zA-Z0-9_-]+)",
            replace_single,
            text,
        )

        # Restore protected email patterns
        for i, pattern in enumerate(email_patterns):
            text = text.replace(f"__EMAIL_PATTERN_{i}__", pattern)

        # Ranges are meaningless for author-date labels.
        if not author_date:
            # Format consecutive citations as ranges (e.g., [1][2][3] -> [1-3])
            text = self._format_citation_ranges(text)

        return self._restore_code(text, code_blocks)
