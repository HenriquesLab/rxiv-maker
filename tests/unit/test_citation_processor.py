"""Unit tests for citation processor module."""

from rxiv_maker.converters.citation_processor import (
    convert_citations_to_latex,
    extract_citations_from_text,
    process_citations_outside_tables,
)


class TestConvertCitationsToLatex:
    """Test citation conversion functionality."""

    def test_single_citation_conversion(self):
        """Test conversion of single citations."""
        text = "This is a reference to @smith2021 in the text."
        expected = r"This is a reference to \cite{smith2021} in the text."
        result = convert_citations_to_latex(text)
        assert result == expected

    def test_multiple_single_citations(self):
        """Test conversion of multiple individual citations."""
        text = "See @smith2021 and @jones2020 for details."
        expected = r"See \cite{smith2021} and \cite{jones2020} for details."
        result = convert_citations_to_latex(text)
        assert result == expected

    def test_bracketed_multiple_citations(self):
        """Test conversion of bracketed multiple citations."""
        text = "Multiple references [@smith2021;@jones2020;@brown2019]."
        expected = r"Multiple references \cite{smith2021,jones2020,brown2019}."
        result = convert_citations_to_latex(text)
        assert result == expected

    def test_bracketed_single_citation(self):
        """Test conversion of bracketed single citation."""
        text = "Single bracketed reference [@smith2021]."
        expected = r"Single bracketed reference \cite{smith2021}."
        result = convert_citations_to_latex(text)
        assert result == expected

    def test_citation_with_underscores(self):
        """Test citations containing underscores."""
        text = "Reference @first_author_2021 with underscores."
        expected = r"Reference \cite{first_author_2021} with underscores."
        result = convert_citations_to_latex(text)
        assert result == expected

    def test_citation_with_hyphens(self):
        """Test citations containing hyphens."""
        text = "Reference @first-author-2021 with hyphens."
        expected = r"Reference \cite{first-author-2021} with hyphens."
        result = convert_citations_to_latex(text)
        assert result == expected

    def test_excludes_figure_references(self):
        """Test that figure references are not converted as citations."""
        text = "See @fig:example and @smith2021."
        expected = r"See @fig:example and \cite{smith2021}."
        result = convert_citations_to_latex(text)
        assert result == expected

    def test_excludes_equation_references(self):
        """Test that equation references are not converted as citations."""
        text = "From @eq:formula and @smith2021."
        expected = r"From @eq:formula and \cite{smith2021}."
        result = convert_citations_to_latex(text)
        assert result == expected

    def test_mixed_citation_formats(self):
        """Test mixed citation formats in same text."""
        text = "Individual @smith2021, bracketed [@jones2020], and multiple [@brown2019;@davis2018]."
        expected = r"Individual \cite{smith2021}, bracketed \cite{jones2020}, and multiple \cite{brown2019,davis2018}."
        result = convert_citations_to_latex(text)
        assert result == expected

    def test_citations_with_spaces_in_brackets(self):
        """Test citations with extra spaces in brackets."""
        text = "Spaced citations [@ smith2021 ; @jones2020 ]."
        expected = r"Spaced citations \cite{smith2021,jones2020}."
        result = convert_citations_to_latex(text)
        assert result == expected

    def test_empty_citations_handled(self):
        """Test that empty citations are handled gracefully."""
        text = "Empty bracket [@;] test."
        # Should handle gracefully, maybe produce empty cite or skip
        result = convert_citations_to_latex(text)
        # Just ensure it doesn't crash
        assert isinstance(result, str)

    def test_citations_at_sentence_boundaries(self):
        """Test citations at start and end of sentences."""
        text = "@smith2021 started the research. The work concluded @jones2020."
        expected = r"\cite{smith2021} started the research. The work concluded \cite{jones2020}."
        result = convert_citations_to_latex(text)
        assert result == expected

    def test_citations_in_parentheses(self):
        """Test citations within parentheses."""
        text = "Some work (see @smith2021) was done."
        expected = r"Some work (see \cite{smith2021}) was done."
        result = convert_citations_to_latex(text)
        assert result == expected

    def test_numeric_citations(self):
        """Test citations with numeric components."""
        text = "Reference @author2021a and @author2021b."
        expected = r"Reference \cite{author2021a} and \cite{author2021b}."
        result = convert_citations_to_latex(text)
        assert result == expected


class TestProcessCitationsOutsideTables:
    """Test processing citations while protecting table content."""

    def test_citations_outside_table_processed(self):
        """Test that citations outside tables are processed."""
        content = "Text with @citation1 before table."
        protected_tables = {}
        expected = r"Text with \cite{citation1} before table."
        result = process_citations_outside_tables(content, protected_tables)
        assert result == expected

    def test_citations_preserved_in_protected_tables(self):
        """Test that citations in protected tables are preserved."""
        content = "Text with PROTECTED_TABLE_0 and @citation1."
        protected_tables = {"PROTECTED_TABLE_0": "| Header | @citation2 |\n|--------|------------|"}
        expected = r"Text with PROTECTED_TABLE_0 and \cite{citation1}."
        result = process_citations_outside_tables(content, protected_tables)
        assert result == expected
        # The protected table content should not be modified
        assert "@citation2" in protected_tables["PROTECTED_TABLE_0"]

    def test_multiple_protected_tables(self):
        """Test handling multiple protected table blocks."""
        content = "@cite1 PROTECTED_TABLE_0 @cite2 PROTECTED_TABLE_1 @cite3"
        protected_tables = {"PROTECTED_TABLE_0": "| @ref1 |", "PROTECTED_TABLE_1": "| @ref2 |"}
        expected = r"\cite{cite1} PROTECTED_TABLE_0 \cite{cite2} PROTECTED_TABLE_1 \cite{cite3}"
        result = process_citations_outside_tables(content, protected_tables)
        assert result == expected

    def test_no_protected_tables(self):
        """Test normal citation processing when no tables are protected."""
        content = "Simple text with @citation1 and @citation2."
        protected_tables = {}
        expected = r"Simple text with \cite{citation1} and \cite{citation2}."
        result = process_citations_outside_tables(content, protected_tables)
        assert result == expected

    def test_empty_content(self):
        """Test empty content handling."""
        content = ""
        protected_tables = {}
        result = process_citations_outside_tables(content, protected_tables)
        assert result == ""

    def test_content_only_protected_tables(self):
        """Test content that consists only of protected table placeholders."""
        content = "PROTECTED_TABLE_0 PROTECTED_TABLE_1"
        protected_tables = {"PROTECTED_TABLE_0": "| @ref1 |", "PROTECTED_TABLE_1": "| @ref2 |"}
        result = process_citations_outside_tables(content, protected_tables)
        assert result == content  # Should be unchanged


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_special_characters_in_text(self):
        """Test handling of special characters around citations."""
        text = "Citations: @smith2021, @jones2020! And @brown2019?"
        expected = r"Citations: \cite{smith2021}, \cite{jones2020}! And \cite{brown2019}?"
        result = convert_citations_to_latex(text)
        assert result == expected

    def test_malformed_bracketed_citations(self):
        """Test handling of malformed bracketed citations."""
        text = "Malformed [@smith2021 missing closing bracket."
        # Should not convert malformed brackets
        result = convert_citations_to_latex(text)
        # Ensure the malformed citation is handled gracefully
        assert isinstance(result, str)

    def test_at_symbol_not_citation(self):
        """Test @ symbols that are not citations."""
        text = "Email user@example.com and @invalid_citation_with_dot.com"
        # Should only convert valid citation patterns
        result = convert_citations_to_latex(text)
        # Email should be preserved, only valid citations converted
        assert "user@example.com" in result

    def test_citation_at_line_boundaries(self):
        """Test citations at line boundaries."""
        text = "Line one @smith2021\nLine two @jones2020\n"
        expected = r"Line one \cite{smith2021}" + "\n" + r"Line two \cite{jones2020}" + "\n"
        result = convert_citations_to_latex(text)
        assert result == expected

    def test_very_long_citation_key(self):
        """Test handling of very long citation keys."""
        long_key = "very_long_citation_key_" + "a" * 100
        text = f"Citation @{long_key} test."
        expected = rf"Citation \cite{{{long_key}}} test."
        result = convert_citations_to_latex(text)
        assert result == expected


class TestExtractCitationsFromText:
    """Test citation extraction from markdown text."""

    def test_extract_simple_citations(self):
        """Test extraction of simple citations."""
        text = "See @smith2021 and [@jones2020;@brown2019]."
        citations = extract_citations_from_text(text)
        # Bracketed citations are processed first, then single citations
        assert citations == ["jones2020", "brown2019", "smith2021"]

    def test_extract_citations_with_underscores(self):
        """Test extraction of citations with underscores."""
        text = "Reference @first_author_2021 and @second_author_2020."
        citations = extract_citations_from_text(text)
        assert citations == ["first_author_2021", "second_author_2020"]

    def test_extract_citations_with_triple_backticks(self):
        """Test that citations are extracted even with triple backtick code blocks.

        This is a regression test for a bug where the single-backtick protection
        regex would incorrectly match across triple-backtick blocks, causing
        citations between the blocks to be excluded from extraction.
        """
        text = """Some text with `inline code`.

```latex
\\begin{figure}
  \\includegraphics{figure.pdf}
\\end{figure}
```

The framework integrates [@schmidt_cell_2018], CellPose [@stringer_cellpose_2021],
and U-Net [@ronneberger_u-net_2015] models from [@von_chamier_democratising_2021].

```python
def example():
    pass
```

More citations: @smith2021 and @jones2020.
"""
        citations = extract_citations_from_text(text)
        # All citations should be extracted, even those between code blocks
        expected = [
            "schmidt_cell_2018",
            "stringer_cellpose_2021",
            "ronneberger_u-net_2015",
            "von_chamier_democratising_2021",
            "smith2021",
            "jones2020",
        ]
        assert citations == expected

    def test_extract_excludes_backtick_protected_citations(self):
        """Test that citations inside backticks are excluded."""
        text = "See `@example_citation` and @real_citation."
        citations = extract_citations_from_text(text)
        # Only the real citation should be extracted
        assert citations == ["real_citation"]

    def test_extract_excludes_triple_backtick_protected_citations(self):
        """Test that citations inside triple-backtick blocks are excluded."""
        text = """Citation before: @before

```markdown
Example citation: @example_in_code
```

Citation after: @after
"""
        citations = extract_citations_from_text(text)
        # Citations in code blocks should be excluded
        assert citations == ["before", "after"]

    def test_extract_excludes_figure_references(self):
        """Test that figure references are not extracted as citations."""
        text = "See @fig:example, @eq:formula, and @smith2021."
        citations = extract_citations_from_text(text)
        # Only the actual citation should be extracted
        assert citations == ["smith2021"]

    def test_extract_deduplicates_citations(self):
        """Test that duplicate citations are not included multiple times."""
        text = "First @smith2021, second @jones2020, and again @smith2021."
        citations = extract_citations_from_text(text)
        # Should preserve order of first appearance but not duplicate
        assert citations == ["smith2021", "jones2020"]
