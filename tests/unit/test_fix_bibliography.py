"""Tests for fix_bibliography.py module."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rxiv_maker.engines.operations.fix_bibliography import BibliographyFixer


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

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_init_default(self, mock_cache):
        """Test BibliographyFixer initialization with default parameters."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        assert fixer.manuscript_path == self.manuscript_path
        assert fixer.backup is True
        assert fixer.similarity_threshold == 0.8
        mock_cache.assert_called_once()

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_init_no_backup(self, mock_cache):
        """Test BibliographyFixer initialization with backup disabled."""
        fixer = BibliographyFixer(str(self.manuscript_path), backup=False)

        assert fixer.manuscript_path == self.manuscript_path
        assert fixer.backup is False
        mock_cache.assert_called_once()

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_init_string_path(self, mock_cache):
        """Test BibliographyFixer initialization with string path."""
        path_str = "/test/path"
        fixer = BibliographyFixer(path_str)

        assert fixer.manuscript_path == Path(path_str)
        mock_cache.assert_called_once()

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_fix_bibliography_no_bib_file(self, mock_cache):
        """Test fix_bibliography when bibliography file doesn't exist."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        result = fixer.fix_bibliography()

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    @patch("rxiv_maker.engines.operations.fix_bibliography.DOIValidator")
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

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
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

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
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

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_parse_bibliography_empty(self, mock_cache):
        """Test parsing empty bibliography content."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        entries = fixer._parse_bibliography("")

        assert len(entries) == 0

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
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

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
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

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
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

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_is_fixable_error_no_title(self, mock_cache):
        """Test is_fixable_error when entry has no title."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        error = MagicMock()
        error.message = "Could not retrieve metadata"
        entry = {"key": "test"}  # No title

        result = fixer._is_fixable_error(error, entry)

        assert result is False

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_is_fixable_error_valid_error(self, mock_cache):
        """Test is_fixable_error with valid fixable error."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        error = MagicMock()
        error.message = "Could not retrieve metadata for DOI"
        entry = {"key": "test", "title": "Test Title"}

        result = fixer._is_fixable_error(error, entry)

        assert result is True

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_is_fixable_error_unfixable_error(self, mock_cache):
        """Test is_fixable_error with unfixable error."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        error = MagicMock()
        error.message = "Some other type of error"
        entry = {"key": "test", "title": "Test Title"}

        result = fixer._is_fixable_error(error, entry)

        assert result is False

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_identify_problematic_entries_no_errors(self, mock_cache):
        """Test identifying problematic entries when there are no validation errors."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        validation_result = MagicMock()
        validation_result.errors = []
        entries = [{"key": "test", "line_start": 1}]

        result = fixer._identify_problematic_entries(validation_result, entries)

        assert len(result) == 0

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
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

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_attempt_fix_entry_no_title(self, mock_cache):
        """Test attempt_fix_entry when entry has no title."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        entry = {"key": "test"}  # No title

        result = fixer._attempt_fix_entry(entry)

        assert result is None

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    @patch("rxiv_maker.engines.operations.fix_bibliography.BibliographyFixer._search_crossref")
    def test_attempt_fix_entry_no_candidates(self, mock_search, mock_cache):
        """Test attempt_fix_entry when no candidates are found."""
        mock_search.return_value = []

        fixer = BibliographyFixer(str(self.manuscript_path))

        entry = {"key": "test", "title": "Test Title", "author": "Test Author", "year": "2024"}

        result = fixer._attempt_fix_entry(entry)

        assert result is None
        # Should try multiple search strategies
        assert mock_search.call_count >= 2


class TestBibliographyFixerCrossRef:
    """Test CrossRef integration functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test method."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    @patch("rxiv_maker.engines.operations.fix_bibliography.requests.get")
    def test_search_crossref_successful(self, mock_get, mock_cache):
        """Test successful CrossRef API search."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "items": [
                    {
                        "DOI": "10.1000/test",
                        "title": ["Test Article"],
                        "author": [{"given": "John", "family": "Doe"}],
                        "published-print": {"date-parts": [[2024]]},
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        # Mock DOI validation to return True
        with patch.object(BibliographyFixer, "_is_doi_valid", return_value=True):
            fixer = BibliographyFixer(str(self.manuscript_path))
            results = fixer._search_crossref("Test Article", "John Doe", "2024")

        assert len(results) == 1
        assert results[0]["doi"] == "10.1000/test"
        assert results[0]["title"] == "Test Article"
        assert results[0]["authors"] == "Doe, John"

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    @patch("rxiv_maker.engines.operations.fix_bibliography.requests.get")
    def test_search_crossref_timeout(self, mock_get, mock_cache):
        """Test CrossRef API search with timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        fixer = BibliographyFixer(str(self.manuscript_path))
        results = fixer._search_crossref("Test Article")

        assert results == []

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    @patch("rxiv_maker.engines.operations.fix_bibliography.requests.get")
    def test_search_crossref_api_error(self, mock_get, mock_cache):
        """Test CrossRef API search with API error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        fixer = BibliographyFixer(str(self.manuscript_path))
        results = fixer._search_crossref("Test Article")

        assert results == []

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    @patch("rxiv_maker.engines.operations.fix_bibliography.requests.get")
    def test_search_crossref_empty_response(self, mock_get, mock_cache):
        """Test CrossRef API search with empty response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"items": []}}
        mock_get.return_value = mock_response

        fixer = BibliographyFixer(str(self.manuscript_path))
        results = fixer._search_crossref("Nonexistent Article")

        assert results == []


class TestBibliographyFixerMatching:
    """Test publication matching and confidence calculation."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test method."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_find_best_match_perfect_match(self, mock_cache):
        """Test finding best match with perfect title match."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        entry = {"title": "Test Article", "author": "John Doe", "year": "2024"}
        # Use the actual format returned by _search_crossref
        candidates = [
            {
                "title": "Test Article",
                "authors": "Doe, John",
                "year": "2024",
                "doi": "10.1000/test",
            }
        ]

        result = fixer._find_best_match(entry, candidates)

        assert result is not None
        assert result["doi"] == "10.1000/test"

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_find_best_match_no_match(self, mock_cache):
        """Test finding best match when no good match exists."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        entry = {"title": "Test Article", "author": "John Doe", "year": "2024"}
        # Use the actual format returned by _search_crossref
        candidates = [
            {
                "title": "Completely Different Title",
                "authors": "Smith, Jane",
                "year": "2020",
                "doi": "10.1000/different",
            }
        ]

        result = fixer._find_best_match(entry, candidates)

        assert result is None

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_calculate_confidence_high(self, mock_cache):
        """Test confidence calculation with high similarity."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        entry = {"title": "Machine Learning in Biology", "author": "John Doe"}
        # Use actual format from _search_crossref
        crossref_data = {
            "title": "Machine Learning in Biology",
            "authors": "Doe, John",
        }

        confidence = fixer._calculate_confidence(entry, crossref_data)

        assert confidence > 0.8

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_calculate_confidence_low(self, mock_cache):
        """Test confidence calculation with low similarity."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        entry = {"title": "Machine Learning", "author": "John Doe"}
        # Use actual format from _search_crossref
        crossref_data = {
            "title": "Quantum Physics",
            "authors": "Smith, Jane",
        }

        confidence = fixer._calculate_confidence(entry, crossref_data)

        assert confidence < 0.5

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_extract_authors_single(self, mock_cache):
        """Test extracting authors with single author."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        author_list = [{"given": "John", "family": "Doe"}]

        result = fixer._extract_authors(author_list)

        assert result == "Doe, John"

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_extract_authors_multiple(self, mock_cache):
        """Test extracting authors with multiple authors."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        author_list = [
            {"given": "John", "family": "Doe"},
            {"given": "Jane", "family": "Smith"},
            {"given": "Bob", "family": "Johnson"},
        ]

        result = fixer._extract_authors(author_list)

        assert result == "Doe, John and Smith, Jane and Johnson, Bob"

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_extract_authors_missing_fields(self, mock_cache):
        """Test extracting authors with missing given/family names."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        author_list = [{"family": "Doe"}, {"given": "Jane"}]

        result = fixer._extract_authors(author_list)

        # Only family names are processed - given names without family are ignored
        assert result == "Doe"


class TestBibliographyFixerGeneration:
    """Test bibliography entry generation."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test method."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_generate_fixed_entry_complete(self, mock_cache):
        """Test generating fixed bibliography entry with complete data."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        original = {
            "type": "article",
            "key": "doe2024",
            "title": "Test Article",
        }

        crossref_data = {
            "doi": "10.1000/test",
            "title": "Test Article Title",
            "authors": "Doe, John",
            "year": "2024",
            "journal": "Journal of Testing",
            "volume": "42",
            "number": "1",
            "pages": "1-10",
        }

        result = fixer._generate_fixed_entry(original, crossref_data)

        assert "@article{doe2024," in result
        assert "title = {Test Article Title}" in result
        assert "author = {Doe, John}" in result
        assert "year = {2024}" in result
        assert "journal = {Journal of Testing}" in result
        assert "volume = {42}" in result
        assert "doi = {10.1000/test}" in result

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_generate_fixed_entry_minimal(self, mock_cache):
        """Test generating fixed bibliography entry with minimal data."""
        fixer = BibliographyFixer(str(self.manuscript_path))

        original = {
            "type": "article",
            "key": "minimal2024",
        }

        crossref_data = {
            "doi": "10.1000/minimal",
            "title": "Minimal Article",
        }

        result = fixer._generate_fixed_entry(original, crossref_data)

        assert "@article{minimal2024," in result
        assert "title = {Minimal Article}" in result
        assert "doi = {10.1000/minimal}" in result


class TestBibliographyFixerFileOperations:
    """Test file backup and modification operations."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test method."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_create_backup(self, mock_cache):
        """Test creating backup of bibliography file."""
        # Create test bibliography file
        bib_file = self.manuscript_path / "03_REFERENCES.bib"
        bib_content = "@article{test, title={Test}}"
        bib_file.write_text(bib_content)

        fixer = BibliographyFixer(str(self.manuscript_path))
        fixer._create_backup(bib_file)

        # Check backup was created
        backup_file = self.manuscript_path / "03_REFERENCES.bib.backup"
        assert backup_file.exists()

        # Check backup content matches original
        backup_content = backup_file.read_text()
        assert backup_content == bib_content

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_apply_fixes_single(self, mock_cache):
        """Test applying single fix to bibliography file."""
        bib_content = """@article{test2024,
    title={Old Title},
    author={Old Author},
    year={2024}
}"""

        fixes = [
            {
                "original_entry": {
                    "key": "test2024",
                    "match_start": 0,
                    "match_end": len(bib_content),
                    "original_text": bib_content,
                },
                "fixed_entry": "@article{test2024,\n    title = {New Title},\n    author = {New Author},\n    year = {2024},\n    doi = {10.1000/new}\n}",
                "confidence": 0.9,
            }
        ]

        fixer = BibliographyFixer(str(self.manuscript_path))

        # Create temporary file for testing
        bib_file = self.manuscript_path / "03_REFERENCES.bib"
        bib_file.write_text(bib_content)

        success_count = fixer._apply_fixes(bib_file, bib_content, fixes)

        assert success_count == 1

        # Check file was updated
        updated_content = bib_file.read_text()
        assert "New Title" in updated_content
        assert "doi = {10.1000/new}" in updated_content

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    def test_apply_fixes_multiple(self, mock_cache):
        """Test applying multiple fixes to bibliography file."""
        bib_content = """@article{first2024,
    title={First Title},
    year={2024}
}

@article{second2024,
    title={Second Title},
    year={2024}
}"""

        # Create fixes for both entries
        first_entry = "@article{first2024,\n    title={First Title},\n    year={2024}\n}"
        second_entry = "@article{second2024,\n    title={Second Title},\n    year={2024}\n}"

        fixes = [
            {
                "original_entry": {
                    "key": "first2024",
                    "match_start": 0,
                    "match_end": len(first_entry),
                    "original_text": first_entry,
                },
                "fixed_entry": "@article{first2024,\n    title = {Fixed First Title},\n    year = {2024},\n    doi = {10.1000/first}\n}",
                "confidence": 0.9,
            },
            {
                "original_entry": {
                    "key": "second2024",
                    "match_start": bib_content.find(second_entry),
                    "match_end": bib_content.find(second_entry) + len(second_entry),
                    "original_text": second_entry,
                },
                "fixed_entry": "@article{second2024,\n    title = {Fixed Second Title},\n    year = {2024},\n    doi = {10.1000/second}\n}",
                "confidence": 0.9,
            },
        ]

        fixer = BibliographyFixer(str(self.manuscript_path))

        # Create temporary file for testing
        bib_file = self.manuscript_path / "03_REFERENCES.bib"
        bib_file.write_text(bib_content)

        success_count = fixer._apply_fixes(bib_file, bib_content, fixes)

        assert success_count == 2

        # Check file was updated
        updated_content = bib_file.read_text()
        assert "Fixed First Title" in updated_content
        assert "Fixed Second Title" in updated_content


class TestBibliographyFixerDOIValidation:
    """Test DOI validation functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test method."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    @patch("crossref_commons.retrieval.get_publication_as_json")
    def test_is_doi_valid_success(self, mock_get_pub, mock_cache):
        """Test DOI validation with valid DOI."""
        # Mock cache to return None (not cached)
        mock_cache_instance = MagicMock()
        mock_cache_instance.get.return_value = None
        mock_cache.return_value = mock_cache_instance

        # Mock successful publication retrieval
        mock_get_pub.return_value = {"DOI": "10.1000/test", "title": "Test"}

        fixer = BibliographyFixer(str(self.manuscript_path))
        result = fixer._is_doi_valid("10.1000/test")

        assert result is True

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    @patch("crossref_commons.retrieval.get_publication_as_json")
    def test_is_doi_valid_not_found(self, mock_get_pub, mock_cache):
        """Test DOI validation with invalid DOI."""
        # Mock cache to return None (not cached)
        mock_cache_instance = MagicMock()
        mock_cache_instance.get.return_value = None
        mock_cache.return_value = mock_cache_instance

        # Mock failed publication retrieval
        mock_get_pub.side_effect = Exception("DOI not found")

        fixer = BibliographyFixer(str(self.manuscript_path))
        result = fixer._is_doi_valid("10.1000/invalid")

        assert result is False

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    @patch("crossref_commons.retrieval.get_publication_as_json")
    def test_is_doi_valid_timeout(self, mock_get_pub, mock_cache):
        """Test DOI validation with timeout."""
        # Mock cache to return None (not cached)
        mock_cache_instance = MagicMock()
        mock_cache_instance.get.return_value = None
        mock_cache.return_value = mock_cache_instance

        mock_get_pub.side_effect = requests.exceptions.Timeout("Request timed out")

        fixer = BibliographyFixer(str(self.manuscript_path))
        result = fixer._is_doi_valid("10.1000/timeout")

        assert result is False

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    @patch("crossref_commons.retrieval.get_publication_as_json")
    def test_is_doi_valid_connection_error(self, mock_get_pub, mock_cache):
        """Test DOI validation with connection error."""
        # Mock cache to return None (not cached)
        mock_cache_instance = MagicMock()
        mock_cache_instance.get.return_value = None
        mock_cache.return_value = mock_cache_instance

        mock_get_pub.side_effect = requests.exceptions.ConnectionError("Connection failed")

        fixer = BibliographyFixer(str(self.manuscript_path))
        result = fixer._is_doi_valid("10.1000/connection")

        assert result is False


class TestBibliographyFixerIntegration:
    """Test complete workflow integration."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test method."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    @patch("rxiv_maker.engines.operations.fix_bibliography.DOIValidator")
    @patch("rxiv_maker.engines.operations.fix_bibliography.BibliographyFixer._search_crossref")
    @patch("rxiv_maker.engines.operations.fix_bibliography.BibliographyFixer._is_doi_valid")
    def test_fix_bibliography_complete_workflow(self, mock_doi_valid, mock_search, mock_validator_class, mock_cache):
        """Test complete bibliography fixing workflow."""
        # Create bibliography file with problematic entry
        bib_file = self.manuscript_path / "03_REFERENCES.bib"
        bib_content = """@article{broken2024,
    title={Broken Article},
    author={Unknown Author},
    year={2024}
}"""
        bib_file.write_text(bib_content)

        # Mock validation to return errors
        mock_validator = MagicMock()
        mock_error = MagicMock()
        mock_error.line_number = 1
        mock_error.message = "Could not retrieve metadata for DOI"
        mock_result = MagicMock()
        mock_result.errors = [mock_error]
        mock_validator.validate.return_value = mock_result
        mock_validator_class.return_value = mock_validator

        # Mock CrossRef search to return candidate
        mock_search.return_value = [
            {
                "doi": "10.1000/fixed",
                "title": "Broken Article",
                "authors": "Author, Known",
                "year": "2024",
                "journal": "Test Journal",
            }
        ]

        # Mock DOI validation
        mock_doi_valid.return_value = True

        fixer = BibliographyFixer(str(self.manuscript_path))
        result = fixer.fix_bibliography()

        assert result["success"] is True
        assert result["fixed_count"] == 1

        # Check that file was updated
        updated_content = bib_file.read_text()
        assert "10.1000/fixed" in updated_content
        assert "Author, Known" in updated_content

    @patch("rxiv_maker.engines.operations.fix_bibliography.DOICache")
    @patch("rxiv_maker.engines.operations.fix_bibliography.DOIValidator")
    def test_fix_bibliography_dry_run(self, mock_validator_class, mock_cache):
        """Test bibliography fixing in dry run mode."""
        # Create bibliography file
        bib_file = self.manuscript_path / "03_REFERENCES.bib"
        bib_content = "@article{test, title={Test}}"
        bib_file.write_text(bib_content)

        # Mock validation to return an error so dry run actually runs
        mock_validator = MagicMock()
        mock_error = MagicMock()
        mock_error.line_number = 1
        mock_error.message = "Could not retrieve metadata for DOI"
        mock_result = MagicMock()
        mock_result.errors = [mock_error]
        mock_validator.validate.return_value = mock_result
        mock_validator_class.return_value = mock_validator

        # Mock both identify_problematic_entries and attempt_fix_entry to simulate fixable entries
        with (
            patch.object(
                BibliographyFixer,
                "_identify_problematic_entries",
                return_value=[{"key": "test", "title": "Test", "validation_error": mock_error}],
            ),
            patch.object(
                BibliographyFixer,
                "_attempt_fix_entry",
                return_value={
                    "original_entry": {"key": "test", "match_start": 0, "match_end": 10, "title": "Test"},
                    "fixed_entry": "@article{test, title={Fixed Test}}",
                    "confidence": 0.9,
                    "crossref_data": {"title": "Fixed Test", "doi": "10.1000/fixed"},
                },
            ),
        ):
            fixer = BibliographyFixer(str(self.manuscript_path))
            result = fixer.fix_bibliography(dry_run=True)

        assert result["success"] is True
        assert "dry_run" in result
        assert result["dry_run"] is True

        # Check file was not modified
        final_content = bib_file.read_text()
        assert final_content == bib_content
