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
        assert f"[{mapping['jones2022']}, {mapping['brown2023']}]" in result
        assert "@fig:example" in result  # Preserved
        assert "@smith2021" not in result  # Replaced
        assert "@jones2022" not in result  # Replaced
        assert "@brown2023" not in result  # Replaced
