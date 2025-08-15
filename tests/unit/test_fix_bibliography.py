"""Tests for fix_bibliography.py module."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rxiv_maker.engine.fix_bibliography import BibliographyFixer


class TestBibliographyFixer:
    """Test suite for BibliographyFixer class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test method."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("rxiv_maker.engine.fix_bibliography.DOICache")
    def test_init_default(self, mock_cache):
        """Test BibliographyFixer initialization with default parameters."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        assert fixer.manuscript_path == self.manuscript_path
        assert fixer.backup is True
        assert fixer.similarity_threshold == 0.8
        mock_cache.assert_called_once()

    @patch("rxiv_maker.engine.fix_bibliography.DOICache")
    def test_init_no_backup(self, mock_cache):
        """Test BibliographyFixer initialization with backup disabled."""
        fixer = BibliographyFixer(str(self.manuscript_path), backup=False)

        assert fixer.manuscript_path == self.manuscript_path
        assert fixer.backup is False
        mock_cache.assert_called_once()

    @patch("rxiv_maker.engine.fix_bibliography.DOICache")
    def test_init_string_path(self, mock_cache):
        """Test BibliographyFixer initialization with string path."""
        path_str = "/test/path"
        fixer = BibliographyFixer(path_str)

        assert fixer.manuscript_path == Path(path_str)
        mock_cache.assert_called_once()

    @patch("rxiv_maker.engine.fix_bibliography.DOICache")
    def test_fix_bibliography_no_bib_file(self, mock_cache):
        """Test fix_bibliography when bibliography file doesn't exist."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        result = fixer.fix_bibliography()

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch("rxiv_maker.engine.fix_bibliography.DOICache")
    @patch("rxiv_maker.engine.fix_bibliography.DOIValidator")
    def test_fix_bibliography_no_issues(self, mock_validator_class, mock_cache):
        """Test fix_bibliography when no issues are found."""
        # Create bibliography file
        bib_file = self.manuscript_path / "03_REFERENCES.bib"
        bib_file.write_text("@article{test, title={Test}, year={2024}}")

        # Mock validator to return no errors
        mock_validator = MagicMock()
        mock_result = MagicMock()
        mock_result.errors = []
        mock_validator.validate.return_value = mock_result
        mock_validator_class.return_value = mock_validator

        fixer = BibliographyFixer(str(self.manuscript_path))
        result = fixer.fix_bibliography()

        assert result["success"] is True
        assert result["fixed_count"] == 0

    @patch("rxiv_maker.engine.fix_bibliography.DOICache")
    def test_parse_bibliography_simple(self, mock_cache):
        """Test parsing a simple bibliography entry."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        bib_content = """@article{test2024,
    title={Test Article},
    author={Test Author},
    year={2024}
}"""

        entries = fixer._parse_bibliography(bib_content)

        assert len(entries) == 1
        entry = entries[0]
        assert entry["type"] == "article"
        assert entry["key"] == "test2024"
        assert entry["title"] == "Test Article"
        assert entry["author"] == "Test Author"
        assert entry["year"] == "2024"

    @patch("rxiv_maker.engine.fix_bibliography.DOICache")
    def test_parse_bibliography_multiple_entries(self, mock_cache):
        """Test parsing multiple bibliography entries."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        bib_content = """@article{first2024,
    title={First Article},
    author={First Author},
    year={2024}
}

@book{second2023,
    title={Second Book},
    author={Second Author},
    year={2023}
}"""

        entries = fixer._parse_bibliography(bib_content)

        assert len(entries) == 2
        assert entries[0]["key"] == "first2024"
        assert entries[0]["type"] == "article"
        assert entries[1]["key"] == "second2023"
        assert entries[1]["type"] == "book"

    @patch("rxiv_maker.engine.fix_bibliography.DOICache")
    def test_parse_bibliography_empty(self, mock_cache):
        """Test parsing empty bibliography content."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        entries = fixer._parse_bibliography("")

        assert len(entries) == 0

    @patch("rxiv_maker.engine.fix_bibliography.DOICache")
    def test_extract_bib_fields_braces(self, mock_cache):
        """Test extracting fields with braces format."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        fields_text = """title={Test Title},
    author={Test Author},
    year={2024}"""

        fields = fixer._extract_bib_fields(fields_text)

        assert fields["title"] == "Test Title"
        assert fields["author"] == "Test Author"
        assert fields["year"] == "2024"

    @patch("rxiv_maker.engine.fix_bibliography.DOICache")
    def test_extract_bib_fields_no_braces(self, mock_cache):
        """Test extracting fields without braces format."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        fields_text = """title=Test Title,
    author=Test Author,
    year=2024"""

        fields = fixer._extract_bib_fields(fields_text)

        assert fields["title"] == "Test Title"
        assert fields["author"] == "Test Author"
        assert fields["year"] == "2024"

    @patch("rxiv_maker.engine.fix_bibliography.DOICache")
    def test_extract_bib_fields_mixed(self, mock_cache):
        """Test extracting fields with mixed format."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        fields_text = """title={Test Title},
    author=Test Author,
    year={2024}"""

        fields = fixer._extract_bib_fields(fields_text)

        assert fields["title"] == "Test Title"
        assert fields["author"] == "Test Author"
        assert fields["year"] == "2024"

    @patch("rxiv_maker.engine.fix_bibliography.DOICache")
    def test_is_fixable_error_no_title(self, mock_cache):
        """Test is_fixable_error when entry has no title."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        error = MagicMock()
        error.message = "Could not retrieve metadata"
        entry = {"key": "test"}  # No title

        result = fixer._is_fixable_error(error, entry)

        assert result is False

    @patch("rxiv_maker.engine.fix_bibliography.DOICache")
    def test_is_fixable_error_valid_error(self, mock_cache):
        """Test is_fixable_error with valid fixable error."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        error = MagicMock()
        error.message = "Could not retrieve metadata for DOI"
        entry = {"key": "test", "title": "Test Title"}

        result = fixer._is_fixable_error(error, entry)

        assert result is True

    @patch("rxiv_maker.engine.fix_bibliography.DOICache")
    def test_is_fixable_error_unfixable_error(self, mock_cache):
        """Test is_fixable_error with unfixable error."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        error = MagicMock()
        error.message = "Some other type of error"
        entry = {"key": "test", "title": "Test Title"}

        result = fixer._is_fixable_error(error, entry)

        assert result is False

    @patch("rxiv_maker.engine.fix_bibliography.DOICache")
    def test_identify_problematic_entries_no_errors(self, mock_cache):
        """Test identifying problematic entries when there are no validation errors."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        validation_result = MagicMock()
        validation_result.errors = []
        entries = [{"key": "test", "line_start": 1}]

        result = fixer._identify_problematic_entries(validation_result, entries)

        assert len(result) == 0

    @patch("rxiv_maker.engine.fix_bibliography.DOICache")
    def test_identify_problematic_entries_with_fixable_error(self, mock_cache):
        """Test identifying problematic entries with fixable errors."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        error = MagicMock()
        error.line_number = 1
        error.message = "Could not retrieve metadata"

        validation_result = MagicMock()
        validation_result.errors = [error]
        entries = [{"key": "test", "line_start": 1, "title": "Test Title"}]

        result = fixer._identify_problematic_entries(validation_result, entries)

        assert len(result) == 1
        assert result[0]["key"] == "test"
        assert result[0]["validation_error"] == error

    @patch("rxiv_maker.engine.fix_bibliography.DOICache")
    def test_attempt_fix_entry_no_title(self, mock_cache):
        """Test attempt_fix_entry when entry has no title."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        entry = {"key": "test"}  # No title

        result = fixer._attempt_fix_entry(entry)

        assert result is None

    @patch("rxiv_maker.engine.fix_bibliography.DOICache")
    @patch("rxiv_maker.engine.fix_bibliography.BibliographyFixer._search_crossref")
    def test_attempt_fix_entry_no_candidates(self, mock_search, mock_cache):
        """Test attempt_fix_entry when no candidates are found."""
        mock_search.return_value = []

        fixer = BibliographyFixer(str(self.manuscript_path))

        entry = {"key": "test", "title": "Test Title", "author": "Test Author", "year": "2024"}

        result = fixer._attempt_fix_entry(entry)

        assert result is None
        # Should try multiple search strategies
        assert mock_search.call_count >= 2
