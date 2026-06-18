r"""Label extraction utilities for manuscript processing.

This module provides centralized label extraction for figures, tables, equations,
and supplementary elements. Used by both DOCX export and LaTeX processing to
create consistent numbering across formats.

Examples:
    >>> extractor = LabelExtractor()
    >>> content = "![Figure](img.png)\\n{#fig:results}"
    >>> fig_map = extractor.extract_figure_labels(content)
    >>> fig_map
    {'results': 1}
r
"""

import re
from typing import Dict, Tuple


class LabelExtractor:
    r"""Extract and map reference labels from markdown content."""

    @staticmethod
    def extract_figure_labels(content: str) -> Dict[str, int]:
        r"""Extract main figure labels and create number mapping.

        Finds patterns like: ![...](...)\\n{#fig:label}

        Args:
            content: Markdown content to scan

        Returns:
            Dict mapping label names to sequential numbers

        Examples:
            >>> extractor = LabelExtractor()
            >>> content = "![](a.png)\\n{#fig:first}\\n\\n![](b.png)\\n{#fig:second}"
            >>> extractor.extract_figure_labels(content)
            {'first': 1, 'second': 2}
        r
        """
        # Pattern: Image markdown followed by {#fig:label}
        # Allow hyphens and underscores in label names
        labels = re.findall(r"!\[[^\]]*\]\([^)]+\)\s*\n\s*\{#fig:([\w-]+)", content)
        return {label: i + 1 for i, label in enumerate(labels)}

    @staticmethod
    def extract_supplementary_figure_labels(content: str) -> Dict[str, int]:
        r"""Extract supplementary figure labels and create number mapping.

        Finds patterns like: ![...](...)\\n{#sfig:label}

        Args:
            content: Markdown content to scan

        Returns:
            Dict mapping label names to sequential numbers

        Examples:
            >>> extractor = LabelExtractor()
            >>> content = "![](s1.png)\\n{#sfig:methods}\\n\\n![](s2.png)\\n{#sfig:data}"
            >>> extractor.extract_supplementary_figure_labels(content)
            {'methods': 1, 'data': 2}
        r
        """
        # Pattern: Image markdown followed by {#sfig:label}
        labels = re.findall(r"!\[[^\]]*\]\([^)]+\)\s*\n\s*\{#sfig:([\w-]+)", content)
        return {label: i + 1 for i, label in enumerate(labels)}

    @staticmethod
    def extract_supplementary_table_labels(content: str) -> Dict[str, int]:
        r"""Extract supplementary table labels and create number mapping.

        Finds both markdown format {#stable:label} and LaTeX format \\label{stable:label},
        numbering every label in document order (deduplicated). Mixed documents - markdown
        tables alongside a {{tex}} table carrying its own \\label - are numbered correctly.

        Args:
            content: Markdown/LaTeX content to scan

        Returns:
            Dict mapping label names to sequential numbers

        Examples:
            >>> extractor = LabelExtractor()
            >>> content = "{#stable:params}\\n\\n{#stable:results}"
            >>> extractor.extract_supplementary_table_labels(content)
            {'params': 1, 'results': 2}
        r
        """
        # Number every supplementary-table label in document order, accepting both the
        # markdown form ({#stable:label}) and the LaTeX form (\label{stable:label}).
        # A manuscript may mix the two - e.g. markdown tables alongside a {{tex}} table
        # that carries its own \label - so we must not pick one form to the exclusion of
        # the other (an earlier "prefer LaTeX, else markdown" rule misnumbered such
        # mixed documents). Deduplication keeps the first occurrence, so a table labelled
        # in both forms is counted once, at the position it first appears.
        labels = [
            m.group(1) or m.group(2) for m in re.finditer(r"\\label\{stable:([\w-]+)\}|\{#stable:([\w-]+)\}", content)
        ]
        seen = set()
        unique_labels = [label for label in labels if not (label in seen or seen.add(label))]

        return {label: i + 1 for i, label in enumerate(unique_labels)}

    @staticmethod
    def extract_supplementary_note_labels(content: str) -> Dict[str, int]:
        r"""Extract supplementary note labels and create number mapping.

        Finds patterns like: {#snote:label}

        Args:
            content: Markdown content to scan

        Returns:
            Dict mapping label names to sequential numbers

        Examples:
            >>> extractor = LabelExtractor()
            >>> content = "{#snote:methods}\\n\\n{#snote:analysis}"
            >>> extractor.extract_supplementary_note_labels(content)
            {'methods': 1, 'analysis': 2}
        r
        """
        labels = re.findall(r"\{#snote:([\w-]+)\}", content)
        return {label: i + 1 for i, label in enumerate(labels)}

    @staticmethod
    def extract_supplementary_video_labels(content: str) -> Dict[str, int]:
        r"""Extract supplementary video labels and create number mapping.

        Finds patterns like: {#svideo:label ...attrs}

        Args:
            content: Markdown content to scan

        Returns:
            Dict mapping label names to sequential numbers
        """
        labels = re.findall(r"\{#svideo:([\w-]+)", content)
        return {label: i + 1 for i, label in enumerate(labels)}

    @staticmethod
    def extract_equation_labels(content: str) -> Dict[str, int]:
        r"""Extract equation labels and create number mapping.

        Finds patterns like: {#eq:label}

        Args:
            content: Markdown content to scan

        Returns:
            Dict mapping label names to sequential numbers

        Examples:
            >>> extractor = LabelExtractor()
            >>> content = "{#eq:energy}\\n\\n{#eq:momentum}"
            >>> extractor.extract_equation_labels(content)
            {'energy': 1, 'momentum': 2}
        r
        """
        labels = re.findall(r"\{#eq:([\w-]+)\}", content)
        return {label: i + 1 for i, label in enumerate(labels)}

    @staticmethod
    def extract_all_labels(
        main_content: str, si_content: str = ""
    ) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, int], Dict[str, int], Dict[str, int]]:
        r"""Extract all label types from content.

        Convenience method to extract all label types at once. Supplementary
        elements are extracted from SI content if provided, otherwise from main content.

        Args:
            main_content: Main manuscript content
            si_content: Supplementary information content (optional)

        Returns:
            Tuple of (figure_map, sfig_map, stable_map, snote_map, eq_map)

        Examples:
            >>> extractor = LabelExtractor()
            >>> main = "![](fig.png)\\n{#fig:main}\\n{#eq:formula}"
            >>> si = "![](sfig.png)\\n{#sfig:extra}"
            >>> fig, sfig, stable, snote, eq = extractor.extract_all_labels(main, si)
            >>> (fig, sfig, eq)
            ({'main': 1}, {'extra': 1}, {'formula': 1})
        r
        """
        extractor = LabelExtractor()

        # Main figures and equations from main content
        figure_map = extractor.extract_figure_labels(main_content)
        equation_map = extractor.extract_equation_labels(main_content)

        # Supplementary elements from SI content if provided, else main content
        content_for_si = si_content if si_content else main_content

        sfig_map = extractor.extract_supplementary_figure_labels(content_for_si)
        stable_map = extractor.extract_supplementary_table_labels(content_for_si)
        snote_map = extractor.extract_supplementary_note_labels(content_for_si)

        return figure_map, sfig_map, stable_map, snote_map, equation_map
