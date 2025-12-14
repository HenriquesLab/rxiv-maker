"""Unit tests for author name formatter utilities."""

import pytest

from rxiv_maker.utils.author_name_formatter import (
    extract_initials,
    format_author_list,
    format_author_name,
    parse_author_name,
)


class TestExtractInitials:
    """Test initial extraction from given names."""

    def test_extract_initials_full_names(self):
        """Test extracting initials from full given names."""
        assert extract_initials("John") == "J."
        assert extract_initials("John Alan") == "J.A."
        assert extract_initials("John Paul Robert") == "J.P.R."
        assert extract_initials("Mary Jane") == "M.J."

    def test_extract_initials_already_initialized(self):
        """Test extracting initials from already-initialized names."""
        assert extract_initials("J.") == "J."
        assert extract_initials("J. A.") == "J.A."
        assert extract_initials("J.A.") == "J.A."
        assert extract_initials("J. P. R.") == "J.P.R."

    def test_extract_initials_hyphenated(self):
        """Test extracting initials from hyphenated names."""
        assert extract_initials("Jean-Paul") == "J.-P."
        assert extract_initials("Mary-Jane") == "M.-J."
        assert extract_initials("Anne-Marie") == "A.-M."

    def test_extract_initials_mixed_case(self):
        """Test extracting initials handles case properly."""
        assert extract_initials("john") == "J."
        assert extract_initials("john alan") == "J.A."
        assert extract_initials("JOHN ALAN") == "J.A."

    def test_extract_initials_empty(self):
        """Test extracting initials from empty/whitespace strings."""
        assert extract_initials("") == ""
        assert extract_initials("   ") == ""
        assert extract_initials(None) == ""  # type: ignore


class TestParseAuthorName:
    """Test author name parsing into components."""

    def test_parse_lastname_firstname_format(self):
        """Test parsing 'LastName, FirstName' format."""
        result = parse_author_name("Smith, John")
        assert result["first"] == "John"
        assert result["last"] == "Smith"
        assert result["middle"] == ""
        assert result["suffix"] == ""

    def test_parse_lastname_firstname_middle_format(self):
        """Test parsing 'LastName, FirstName MiddleName' format."""
        result = parse_author_name("Smith, John Alan")
        assert result["first"] == "John"
        assert result["middle"] == "Alan"
        assert result["last"] == "Smith"
        assert result["suffix"] == ""

    def test_parse_firstname_lastname_format(self):
        """Test parsing 'FirstName LastName' format."""
        result = parse_author_name("John Smith")
        assert result["first"] == "John"
        assert result["last"] == "Smith"
        assert result["middle"] == ""

    def test_parse_firstname_middle_lastname_format(self):
        """Test parsing 'FirstName MiddleName LastName' format."""
        result = parse_author_name("John Alan Smith")
        assert result["first"] == "John"
        assert result["middle"] == "Alan"
        assert result["last"] == "Smith"

    def test_parse_with_suffix(self):
        """Test parsing names with suffixes."""
        result = parse_author_name("Smith, John Jr.")
        assert result["first"] == "John"
        assert result["last"] == "Smith"
        assert result["suffix"] == "Jr."

        result = parse_author_name("John Smith Jr.")
        assert result["first"] == "John"
        assert result["last"] == "Smith"
        assert result["suffix"] == "Jr."

        result = parse_author_name("Smith, John III")
        assert result["suffix"] == "III"

    def test_parse_with_von_prefix(self):
        """Test parsing names with von/van prefixes."""
        result = parse_author_name("von Neumann, John")
        assert result["first"] == "John"
        assert result["last"] == "von Neumann"
        assert result["von"] == "von"

        result = parse_author_name("John von Neumann")
        assert result["first"] == "John"
        assert result["last"] == "von Neumann"
        assert result["von"] == "von"

        result = parse_author_name("van Gogh, Vincent")
        assert result["von"] == "van"
        assert result["last"] == "van Gogh"

    def test_parse_single_name(self):
        """Test parsing single names (mononyms)."""
        result = parse_author_name("Plato")
        assert result["first"] == ""
        assert result["last"] == "Plato"
        assert result["middle"] == ""

    def test_parse_multiple_middle_names(self):
        """Test parsing names with multiple middle names."""
        result = parse_author_name("Smith, John Paul Robert")
        assert result["first"] == "John"
        assert result["middle"] == "Paul Robert"
        assert result["last"] == "Smith"

    def test_parse_empty_string(self):
        """Test parsing empty/whitespace strings."""
        result = parse_author_name("")
        assert result["first"] == ""
        assert result["last"] == ""

        result = parse_author_name("   ")
        assert result["first"] == ""
        assert result["last"] == ""

    def test_parse_with_initials(self):
        """Test parsing names that include initials."""
        result = parse_author_name("Smith, J.A.")
        assert result["first"] == "J.A."
        assert result["last"] == "Smith"

        result = parse_author_name("J.A. Smith")
        assert result["first"] == "J.A."
        assert result["last"] == "Smith"


class TestFormatAuthorName:
    """Test author name formatting to different styles."""

    @pytest.fixture
    def standard_author(self):
        """Standard author with first, middle, and last names."""
        return {
            "first": "John",
            "middle": "A.",
            "last": "Smith",
            "suffix": "",
            "von": "",
        }

    @pytest.fixture
    def author_with_suffix(self):
        """Author with suffix."""
        return {
            "first": "John",
            "middle": "",
            "last": "Smith",
            "suffix": "Jr.",
            "von": "",
        }

    @pytest.fixture
    def author_with_von(self):
        """Author with von prefix."""
        return {
            "first": "John",
            "middle": "",
            "last": "von Neumann",
            "suffix": "",
            "von": "von",
        }

    def test_format_lastname_initials(self, standard_author):
        """Test formatting to 'LastName, Initials' format."""
        result = format_author_name(standard_author, "lastname_initials")
        assert result == "Smith, J.A."

    def test_format_lastname_firstname(self, standard_author):
        """Test formatting to 'LastName, FirstName' format."""
        result = format_author_name(standard_author, "lastname_firstname")
        assert result == "Smith, John A."

    def test_format_firstname_lastname(self, standard_author):
        """Test formatting to 'FirstName LastName' format."""
        result = format_author_name(standard_author, "firstname_lastname")
        assert result == "John A. Smith"

    def test_format_with_suffix_lastname_initials(self, author_with_suffix):
        """Test formatting with suffix in lastname_initials format."""
        result = format_author_name(author_with_suffix, "lastname_initials")
        assert result == "Smith, J., Jr."

    def test_format_with_suffix_lastname_firstname(self, author_with_suffix):
        """Test formatting with suffix in lastname_firstname format."""
        result = format_author_name(author_with_suffix, "lastname_firstname")
        assert result == "Smith, John, Jr."

    def test_format_with_suffix_firstname_lastname(self, author_with_suffix):
        """Test formatting with suffix in firstname_lastname format."""
        result = format_author_name(author_with_suffix, "firstname_lastname")
        assert result == "John Smith Jr."

    def test_format_single_name(self):
        """Test formatting single names (mononyms)."""
        author = {"first": "", "middle": "", "last": "Plato", "suffix": "", "von": ""}
        assert format_author_name(author, "lastname_initials") == "Plato"
        assert format_author_name(author, "lastname_firstname") == "Plato"
        assert format_author_name(author, "firstname_lastname") == "Plato"

    def test_format_no_middle_name(self):
        """Test formatting names without middle names."""
        author = {"first": "John", "middle": "", "last": "Smith", "suffix": "", "von": ""}
        assert format_author_name(author, "lastname_initials") == "Smith, J."
        assert format_author_name(author, "lastname_firstname") == "Smith, John"
        assert format_author_name(author, "firstname_lastname") == "John Smith"

    def test_format_with_von_prefix(self, author_with_von):
        """Test formatting names with von prefix."""
        result = format_author_name(author_with_von, "lastname_initials")
        assert result == "von Neumann, J."

        result = format_author_name(author_with_von, "lastname_firstname")
        assert result == "von Neumann, John"

        result = format_author_name(author_with_von, "firstname_lastname")
        assert result == "John von Neumann"

    def test_format_invalid_format_type(self, standard_author):
        """Test that invalid format types default to lastname_firstname."""
        result = format_author_name(standard_author, "invalid_format")
        assert result == "Smith, John A."

    def test_format_multiple_middle_names(self):
        """Test formatting with multiple middle names."""
        author = {
            "first": "John",
            "middle": "Paul Robert",
            "last": "Smith",
            "suffix": "",
            "von": "",
        }
        result = format_author_name(author, "lastname_initials")
        assert result == "Smith, J.P.R."

        result = format_author_name(author, "lastname_firstname")
        assert result == "Smith, John Paul Robert"


class TestFormatAuthorList:
    """Test formatting lists of multiple authors."""

    def test_format_single_author(self):
        """Test formatting a single author."""
        result = format_author_list("Smith, John A.", "lastname_initials")
        assert result == "Smith, J.A."

    def test_format_two_authors(self):
        """Test formatting two authors."""
        result = format_author_list("Smith, John and Jones, Mary", "lastname_initials")
        assert result == "Smith, J. and Jones, M."

        result = format_author_list("Smith, John and Jones, Mary", "firstname_lastname")
        assert result == "John Smith and Mary Jones"

    def test_format_multiple_authors(self):
        """Test formatting three or more authors."""
        authors = "Smith, John A. and Jones, Mary B. and Brown, James C."
        result = format_author_list(authors, "lastname_initials")
        assert result == "Smith, J.A. and Jones, M.B. and Brown, J.C."

    def test_format_authors_with_various_formats(self):
        """Test formatting authors in mixed input formats."""
        authors = "Smith, John A. and Mary Jones"
        result = format_author_list(authors, "lastname_firstname")
        # Both should be formatted consistently
        assert "Smith, John A." in result
        assert "Jones, Mary" in result

    def test_format_empty_string(self):
        """Test formatting empty author string."""
        assert format_author_list("", "lastname_initials") == ""
        assert format_author_list("   ", "lastname_initials") == ""

    def test_format_with_suffixes(self):
        """Test formatting authors with suffixes."""
        authors = "Smith, John Jr. and Jones, Mary Sr."
        result = format_author_list(authors, "lastname_initials")
        assert "Smith, J., Jr." in result
        assert "Jones, M., Sr." in result

    def test_format_with_von_prefix(self):
        """Test formatting authors with von/van prefixes."""
        authors = "von Neumann, John and van Gogh, Vincent"
        result = format_author_list(authors, "lastname_initials")
        assert "von Neumann, J." in result
        assert "van Gogh, V." in result

    def test_format_preserves_and_separator(self):
        """Test that 'and' separator is preserved in output."""
        authors = "Smith, John and Jones, Mary"
        result = format_author_list(authors, "lastname_initials")
        assert " and " in result
        # Should have exactly one " and "
        assert result.count(" and ") == 1

    def test_format_handles_extra_whitespace(self):
        """Test formatting handles extra whitespace around 'and'."""
        authors = "Smith, John  and  Jones, Mary"
        result = format_author_list(authors, "lastname_initials")
        assert " and " in result

    def test_format_all_three_formats(self):
        """Test all three format types produce expected output."""
        authors = "Smith, John A. and Jones, Mary B."

        result_li = format_author_list(authors, "lastname_initials")
        assert result_li == "Smith, J.A. and Jones, M.B."

        result_lf = format_author_list(authors, "lastname_firstname")
        assert result_lf == "Smith, John A. and Jones, Mary B."

        result_fl = format_author_list(authors, "firstname_lastname")
        assert result_fl == "John A. Smith and Mary B. Jones"

    def test_format_complex_names(self):
        """Test formatting complex real-world author names."""
        # Real-world example with multiple middle names, von prefix
        authors = "von Neumann, John and Smith, John Paul Robert and Garcia-Lopez, Maria"
        result = format_author_list(authors, "lastname_initials")
        assert "von Neumann, J." in result
        assert "Smith, J.P.R." in result
        # Note: Hyphenated last names treated as single unit
        assert "Garcia-Lopez, M." in result

    def test_format_single_names(self):
        """Test formatting mononyms in author lists."""
        authors = "Plato and Aristotle"
        result = format_author_list(authors, "lastname_initials")
        assert result == "Plato and Aristotle"
