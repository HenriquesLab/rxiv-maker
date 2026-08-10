"""Tests for DOCX citation mapper."""

from rxiv_maker.exporters.docx_citation_mapper import CitationMapper


class TestCitationMapper:
    """Test citation mapping functionality."""

    def test_create_mapping_simple(self):
        """Test creating simple citation mapping."""
        mapper = CitationMapper()
        citations = ["smith2021", "jones2022", "smith2021"]
        mapping = mapper.create_mapping(citations)

        assert mapping == {"smith2021": 1, "jones2022": 2}
        assert len(mapping) == 2  # Duplicates removed

    def test_create_mapping_preserves_order(self):
        """Test that mapping preserves first-appearance order."""
        mapper = CitationMapper()
        citations = ["charlie2023", "alice2021", "bob2022", "alice2021"]
        mapping = mapper.create_mapping(citations)

        assert mapping == {"charlie2023": 1, "alice2021": 2, "bob2022": 3}

    def test_create_mapping_empty(self):
        """Test mapping with empty list."""
        mapper = CitationMapper()
        mapping = mapper.create_mapping([])

        assert mapping == {}

    def test_extract_citations_from_markdown_single(self):
        """Test extracting single citations from markdown."""
        mapper = CitationMapper()
        text = "Study by @smith2021 shows..."

        citations = mapper.extract_citations_from_markdown(text)

        assert citations == ["smith2021"]

    def test_extract_citations_from_markdown_multiple(self):
        """Test extracting multiple bracketed citations."""
        mapper = CitationMapper()
        text = "Studies [@smith2021;@jones2022;@brown2023] show..."

        citations = mapper.extract_citations_from_markdown(text)

        assert "smith2021" in citations
        assert "jones2022" in citations
        assert "brown2023" in citations

    def test_extract_citations_from_markdown_mixed(self):
        """Test extracting both single and bracketed citations."""
        mapper = CitationMapper()
        text = "Study by @smith2021 and others [@jones2022;@brown2023] show..."

        citations = mapper.extract_citations_from_markdown(text)

        assert "smith2021" in citations
        assert "jones2022" in citations
        assert "brown2023" in citations

    def test_extract_citations_excludes_figures(self):
        """Test that figure references are not extracted as citations."""
        mapper = CitationMapper()
        text = "See @fig:example and @smith2021 for details"

        citations = mapper.extract_citations_from_markdown(text)

        assert citations == ["smith2021"]
        assert "fig:example" not in citations

    def test_extract_citations_excludes_equations(self):
        """Test that equation references are not extracted as citations."""
        mapper = CitationMapper()
        text = "According to @eq:formula and @smith2021"

        citations = mapper.extract_citations_from_markdown(text)

        assert citations == ["smith2021"]
        assert "eq:formula" not in citations

    def test_replace_citations_single(self):
        """Test replacing single citation."""
        mapper = CitationMapper()
        text = "Study by @smith2021 shows..."
        mapping = {"smith2021": 1}

        result = mapper.replace_citations_in_text(text, mapping)

        assert result == "Study by [1] shows..."

    def test_replace_citations_multiple(self):
        """Test replacing multiple citations."""
        mapper = CitationMapper()
        text = "Studies [@smith2021;@jones2022] show..."
        mapping = {"smith2021": 1, "jones2022": 2}

        result = mapper.replace_citations_in_text(text, mapping)

        assert result == "Studies [1, 2] show..."

    def test_replace_citations_mixed(self):
        """Test replacing both single and multiple citations."""
        mapper = CitationMapper()
        text = "Study by @smith2021 and others [@jones2022;@brown2023] show..."
        mapping = {"smith2021": 1, "jones2022": 2, "brown2023": 3}

        result = mapper.replace_citations_in_text(text, mapping)

        assert result == "Study by [1] and others [2, 3] show..."

    def test_replace_citations_preserves_figures(self):
        """Test that figure references are preserved."""
        mapper = CitationMapper()
        text = "See @fig:example and @smith2021 for details"
        mapping = {"smith2021": 1}

        result = mapper.replace_citations_in_text(text, mapping)

        assert result == "See @fig:example and [1] for details"

    def test_replace_citations_preserves_equations(self):
        """Test that equation references are preserved."""
        mapper = CitationMapper()
        text = "According to @eq:formula and @smith2021"
        mapping = {"smith2021": 1}

        result = mapper.replace_citations_in_text(text, mapping)

        assert result == "According to @eq:formula and [1]"

    def test_replace_citations_preserves_tables(self):
        """Test that table references are preserved."""
        mapper = CitationMapper()
        text = "See @tbl:data and @smith2021"
        mapping = {"smith2021": 1}

        result = mapper.replace_citations_in_text(text, mapping)

        assert result == "See @tbl:data and [1]"

    def test_replace_citations_preserves_emails(self):
        """Test that email addresses are preserved."""
        mapper = CitationMapper()
        text = "Contact user@example.com or @smith2021"
        mapping = {"smith2021": 1}

        result = mapper.replace_citations_in_text(text, mapping)

        assert result == "Contact user@example.com or [1]"
        assert "user@example.com" in result

    def test_replace_citations_missing_key(self):
        """Test replacing citation with missing key in mapping."""
        mapper = CitationMapper()
        text = "Study by @smith2021 and @unknown2023"
        mapping = {"smith2021": 1}  # unknown2023 not in mapping

        result = mapper.replace_citations_in_text(text, mapping)

        # smith2021 should be replaced, unknown2023 preserved
        assert "[1]" in result
        assert "@unknown2023" in result

    def test_replace_citations_with_hyphens_underscores(self):
        """Test citations with hyphens and underscores."""
        mapper = CitationMapper()
        text = "See @smith-jones_2021 and @author_2022-v2"
        mapping = {"smith-jones_2021": 1, "author_2022-v2": 2}

        result = mapper.replace_citations_in_text(text, mapping)

        assert result == "See [1] and [2]"

    def test_full_workflow(self):
        """Test complete workflow: extract → create mapping → replace."""
        mapper = CitationMapper()
        text = """
        According to @smith2021, the method works. Other studies [@jones2022;@brown2023]
        confirm this. See @fig:example for visualization and @smith2021 for details.
        """

        # Step 1: Extract citations
        citations = mapper.extract_citations_from_markdown(text)
        assert "smith2021" in citations
        assert "jones2022" in citations
        assert "brown2023" in citations
        assert "fig:example" not in citations

        # Step 2: Create mapping
        mapping = mapper.create_mapping(citations)
        # All three citations should be in mapping (duplicates removed)
        assert len(mapping) == 3
        assert "smith2021" in mapping
        assert "jones2022" in mapping
        assert "brown2023" in mapping
        # Check that numbers are sequential 1,2,3 (in some order)
        assert set(mapping.values()) == {1, 2, 3}

        # Step 3: Replace in text
        result = mapper.replace_citations_in_text(text, mapping)
        # Check that all citations were replaced with numbers
        assert f"[{mapping['smith2021']}]" in result
        # If jones2022 and brown2023 are consecutive numbers, they should be formatted as a range
        jones_num = mapping["jones2022"]
        brown_num = mapping["brown2023"]
        if abs(jones_num - brown_num) == 1:
            # Consecutive numbers - should be formatted as range [X-Y]
            min_num = min(jones_num, brown_num)
            max_num = max(jones_num, brown_num)
            assert f"[{min_num}-{max_num}]" in result
        else:
            # Non-consecutive - should be comma-separated
            assert f"[{jones_num}, {brown_num}]" in result or f"[{brown_num}, {jones_num}]" in result
        assert "@fig:example" in result  # Preserved
        assert "@smith2021" not in result  # Replaced
        assert "@jones2022" not in result  # Replaced
        assert "@brown2023" not in result  # Replaced


class TestCodeSpanProtection:
    """Citation syntax shown as a code example must survive verbatim."""

    def test_inline_code_citation_not_replaced(self):
        """Backticked citation syntax stays literal in numbered style."""
        mapper = CitationMapper()
        text = "For example, you would write `[@Knuth1984]`."
        result = mapper.replace_citations_in_text(text, {"Knuth1984": 29})

        assert "`[@Knuth1984]`" in result
        assert "[29]" not in result

    def test_inline_code_protected_while_real_citation_converts(self):
        """A literal example and a real citation coexist in one paragraph."""
        mapper = CitationMapper()
        text = "Write `[@smith2021]` to cite it [@smith2021]."
        result = mapper.replace_citations_in_text(text, {"smith2021": 1})

        assert "`[@smith2021]`" in result
        assert result.count("[1]") == 1

    def test_fenced_code_block_protected(self):
        """Fenced blocks are protected as a whole."""
        mapper = CitationMapper()
        text = "Example:\n```\n[@smith2021]\n```\nReal: [@smith2021]"
        result = mapper.replace_citations_in_text(text, {"smith2021": 1})

        assert "```\n[@smith2021]\n```" in result
        assert result.count("[1]") == 1

    def test_bare_key_in_code_protected(self):
        """A bare @key inside backticks is not a citation."""
        mapper = CitationMapper()
        text = "Use `@smith2021` syntax, as in @smith2021."
        result = mapper.replace_citations_in_text(text, {"smith2021": 1})

        assert "`@smith2021`" in result
        assert "[1]" in result


class TestAuthorDateStyle:
    """Author-date rendering for journals that reject numbered citations."""

    @staticmethod
    def _entries():
        from rxiv_maker.utils.bibliography_parser import BibEntry

        def entry(key, author, year):
            return BibEntry(
                key=key,
                entry_type="article",
                fields={"author": author, "year": year, "title": "T", "journal": "J"},
                raw="",
            )

        return {
            "solo2021": entry("solo2021", "Smith, John", "2021"),
            "pair2022": entry("pair2022", "Jones, A. and Brown, B.", "2022"),
            "many2023": entry("many2023", "Alpha, A. and Beta, B. and Gamma, G.", "2023"),
            "dup2021": entry("dup2021", "Smith, John", "2021"),
        }

    def _mapping(self):
        mapper = CitationMapper(citation_style="author-date")
        keys = ["solo2021", "pair2022", "many2023", "dup2021"]
        return mapper, mapper.create_author_date_mapping(keys, self._entries())

    def test_single_surname_label(self):
        _, mapping = self._mapping()
        assert mapping["solo2021"]["paren"] == "Smith, 2021a"

    def test_two_authors_joined_with_and(self):
        _, mapping = self._mapping()
        assert mapping["pair2022"]["paren"] == "Jones and Brown, 2022"

    def test_three_plus_surnames_use_et_al(self):
        _, mapping = self._mapping()
        assert mapping["many2023"]["paren"] == "Alpha et al., 2023"

    def test_colliding_surname_date_suffixes(self):
        """Colliding author-year pairs get letter suffixes in citation order."""
        _, mapping = self._mapping()
        assert mapping["solo2021"]["paren"] == "Smith, 2021a"
        assert mapping["dup2021"]["paren"] == "Smith, 2021b"

    def test_bracketed_citation_is_parenthetical(self):
        mapper, mapping = self._mapping()
        result = mapper.replace_citations_in_text("Shown before [@many2023].", mapping)
        assert result == "Shown before (Alpha et al., 2023)."

    def test_narrative_citation_is_textual(self):
        mapper, mapping = self._mapping()
        result = mapper.replace_citations_in_text("As @many2023 showed.", mapping)
        assert result == "As Alpha et al. (2023) showed."

    def test_multiple_citations_separated_by_semicolon(self):
        mapper, mapping = self._mapping()
        result = mapper.replace_citations_in_text("[@pair2022;@many2023]", mapping)
        assert result == "(Jones and Brown, 2022; Alpha et al., 2023)"

    def test_no_numeric_brackets_emitted(self):
        """The whole point: nothing renders as [N]."""
        import re

        mapper, mapping = self._mapping()
        text = "See [@solo2021;@pair2022] and @many2023 too."
        result = mapper.replace_citations_in_text(text, mapping)
        assert not re.search(r"\[\d+", result)

    def test_code_spans_protected_in_authordate(self):
        mapper, mapping = self._mapping()
        result = mapper.replace_citations_in_text("Write `[@solo2021]` here.", mapping)
        assert "`[@solo2021]`" in result

    def test_cross_references_preserved(self):
        mapper, mapping = self._mapping()
        result = mapper.replace_citations_in_text("See @fig:one and [@solo2021].", mapping)
        assert "@fig:one" in result
