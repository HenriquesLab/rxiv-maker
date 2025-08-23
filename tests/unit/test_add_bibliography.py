"""Tests for add_bibliography.py module."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rxiv_maker.engines.operations.add_bibliography import BibliographyAdder


class TestBibliographyAdder:
    """Test suite for BibliographyAdder class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test method."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("rxiv_maker.engines.operations.add_bibliography.DOICache")
    def test_init(self, mock_cache):
        """Test BibliographyAdder initialization."""
        adder = BibliographyAdder(str(self.manuscript_path))

        assert adder.manuscript_path == self.manuscript_path
        assert adder.bib_file == self.manuscript_path / "03_REFERENCES.bib"
        mock_cache.assert_called_once()

    @patch("rxiv_maker.engines.operations.add_bibliography.DOICache")
    def test_init_string_path(self, mock_cache):
        """Test BibliographyAdder initialization with string path."""
        path_str = "/test/path"
        adder = BibliographyAdder(path_str)

        assert adder.manuscript_path == Path(path_str)
        assert adder.bib_file == Path(path_str) / "03_REFERENCES.bib"
        mock_cache.assert_called_once()

    @patch("rxiv_maker.engines.operations.add_bibliography.DOICache")
    def test_doi_regex_valid(self, mock_cache):
        """Test DOI regex with valid DOIs."""
        adder = BibliographyAdder(str(self.manuscript_path))

        valid_dois = ["10.1000/123456", "10.1038/nature12373", "10.1109/5.771073"]

        for doi in valid_dois:
            assert adder.DOI_REGEX.match(doi), f"DOI {doi} should be valid"

    @patch("rxiv_maker.engines.operations.add_bibliography.DOICache")
    def test_doi_regex_invalid(self, mock_cache):
        """Test DOI regex with invalid DOIs."""
        adder = BibliographyAdder(str(self.manuscript_path))

        invalid_dois = ["not-a-doi", "10.123/too-short-prefix", "11.1000/wrong-prefix", "", "10.", "10.1000/"]

        for doi in invalid_dois:
            assert not adder.DOI_REGEX.match(doi), f"DOI {doi} should be invalid"

    @patch("rxiv_maker.engines.operations.add_bibliography.DOICache")
    @patch("rxiv_maker.engines.operations.add_bibliography.get_publication_as_json")
    def test_add_entries_no_bib_file(self, mock_get_pub, mock_cache):
        """Test add_entries when bibliography file doesn't exist - it creates one."""
        # Mock the DOI resolution
        mock_get_pub.return_value = {
            "title": ["Test Article"],
            "author": [{"given": "John", "family": "Doe"}],
            "published-print": {"date-parts": [[2024]]},
            "container-title": ["Test Journal"],
        }

        adder = BibliographyAdder(str(self.manuscript_path))

        result = adder.add_entries(["10.1000/123456"])

        assert result is True  # Creates new file and adds entry

    @patch("rxiv_maker.engines.operations.add_bibliography.DOICache")
    def test_add_entries_empty_list(self, mock_cache):
        """Test add_entries with empty DOI list."""
        # Create bibliography file
        bib_file = self.manuscript_path / "03_REFERENCES.bib"
        bib_file.write_text("% Empty bibliography")

        adder = BibliographyAdder(str(self.manuscript_path))

        result = adder.add_entries([])

        assert result is True  # Should succeed but do nothing

    @patch("rxiv_maker.engines.operations.add_bibliography.DOICache")
    def test_add_entries_invalid_doi(self, mock_cache):
        """Test add_entries with invalid DOI format."""
        # Create bibliography file
        bib_file = self.manuscript_path / "03_REFERENCES.bib"
        bib_file.write_text("% Empty bibliography")

        adder = BibliographyAdder(str(self.manuscript_path))

        result = adder.add_entries(["invalid-doi"])

        assert result is False  # Should fail due to invalid DOI
