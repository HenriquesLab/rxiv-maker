"""Regression tests for underscore-bearing citation keys inside table cells.

A citation key containing an underscore (e.g. ``Xie2016_bookdown``) cited inside a
Markdown table cell must NOT have its underscore LaTeX-escaped. If the underscore is
escaped to ``\\_`` inside a ``\\cite``/``\\citep``/``\\citet`` argument, LaTeX writes
``\\citation{Some\\protect \\T1\\textunderscore Key}`` to the .aux file, and bibtex
then aborts with "White space in argument", losing the entire bibliography.

See: underscore citation keys break bibtex when cited inside a table cell.
"""

import unittest

from rxiv_maker.converters.table_processor import (
    _format_regular_table_cell,
    convert_tables_to_latex,
)


class TestTableCitationUnderscore(unittest.TestCase):
    """Citation keys with underscores must survive table-cell processing unescaped."""

    def test_numbered_citation_key_underscore_unescaped(self):
        """``[@Some_Key]`` -> ``\\cite{Some_Key}`` (numbered style)."""
        result = _format_regular_table_cell("[@Some_Key]", citation_style="numbered")
        self.assertIn("\\cite{Some_Key}", result)
        self.assertNotIn("Some\\_Key", result)
        self.assertNotIn("textunderscore", result)

    def test_authordate_bracketed_citation_key_underscore_unescaped(self):
        """``[@Some_Key]`` -> ``\\citep{Some_Key}`` (author-date style)."""
        result = _format_regular_table_cell("[@Some_Key]", citation_style="author-date")
        self.assertIn("\\citep{Some_Key}", result)
        self.assertNotIn("Some\\_Key", result)
        self.assertNotIn("textunderscore", result)

    def test_authordate_inline_citation_key_underscore_unescaped(self):
        """``@Some_Key`` -> ``\\citet{Some_Key}`` (author-date style)."""
        result = _format_regular_table_cell("@Some_Key", citation_style="author-date")
        self.assertIn("\\citet{Some_Key}", result)
        self.assertNotIn("Some\\_Key", result)
        self.assertNotIn("textunderscore", result)

    def test_bold_plus_underscore_citation_authordate(self):
        """Real-world cell: ``**Bookdown** [@Xie2016_bookdown]`` (author-date)."""
        result = _format_regular_table_cell("**Bookdown** [@Xie2016_bookdown]", citation_style="author-date")
        self.assertIn("\\citep{Xie2016_bookdown}", result)
        self.assertNotIn("Xie2016\\_bookdown", result)

    def test_underscore_in_surrounding_text_still_escaped(self):
        """Underscores OUTSIDE the citation argument must still be escaped."""
        result = _format_regular_table_cell("see [@Some_Key] and file_name", citation_style="author-date")
        # Citation key preserved...
        self.assertIn("\\citep{Some_Key}", result)
        # ...but the plain-text underscore is escaped for LaTeX.
        self.assertIn("file\\_name", result)

    def test_full_table_authordate_citation_underscore(self):
        """End-to-end through convert_tables_to_latex with author-date style."""
        markdown = "| Tool | Ref |\n|------|-----|\n| Bookdown | [@Xie2016_bookdown] |\n"
        result = convert_tables_to_latex(markdown, citation_style="author-date")
        self.assertIn("\\citep{Xie2016_bookdown}", result)
        self.assertNotIn("Xie2016\\_bookdown", result)
        self.assertNotIn("textunderscore", result)


if __name__ == "__main__":
    unittest.main()
