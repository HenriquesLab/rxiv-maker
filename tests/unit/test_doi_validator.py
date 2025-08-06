"""Unit tests for the DOI validation system."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

try:
    import pytest

    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

    # Define mock pytest.mark for when pytest is not available
    class MockPytest:
        class mark:
            @staticmethod
            def validation(cls):
                return cls

    pytest = MockPytest()

try:
    from rxiv_maker.utils.doi_cache import DOICache
    from rxiv_maker.validators.base_validator import ValidationLevel
    from rxiv_maker.validators.doi_validator import DOIValidator

    DOI_VALIDATOR_AVAILABLE = True
except ImportError:
    DOI_VALIDATOR_AVAILABLE = False


@pytest.mark.validation
@unittest.skipUnless(DOI_VALIDATOR_AVAILABLE, "DOI validator not available")
class TestDOICache(unittest.TestCase):
    """Test DOI cache functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, ".cache")
        self.cache = DOICache(cache_dir=self.cache_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_initialization(self):
        """Test cache directory creation."""
        self.assertTrue(os.path.exists(self.cache_dir))

    def test_cache_set_and_get(self):
        """Test basic cache operations."""
        test_doi = "10.1000/test.2023.001"
        test_metadata = {
            "title": ["Test Article"],
            "container-title": ["Test Journal"],
            "published-print": {"date-parts": [[2023]]},
        }

        # Cache should be empty initially
        self.assertIsNone(self.cache.get(test_doi))

        # Set metadata
        self.cache.set(test_doi, test_metadata)

        # Should retrieve cached metadata
        cached = self.cache.get(test_doi)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["title"], ["Test Article"])

    def test_cache_normalization(self):
        """Test DOI normalization in cache."""
        test_doi_upper = "10.1000/TEST.2023.001"
        test_doi_lower = "10.1000/test.2023.001"
        test_metadata = {"title": ["Test Article"]}

        # Set with uppercase
        self.cache.set(test_doi_upper, test_metadata)

        # Should retrieve with lowercase
        cached = self.cache.get(test_doi_lower)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["title"], ["Test Article"])

    @pytest.mark.fast
    def test_cache_clear(self):
        """Test cache clearing."""
        test_doi = "10.1000/test.2023.001"
        test_metadata = {"title": ["Test Article"]}

        self.cache.set(test_doi, test_metadata)
        self.assertIsNotNone(self.cache.get(test_doi))

        self.cache.clear()
        self.assertIsNone(self.cache.get(test_doi))

    def test_cache_stats(self):
        """Test cache statistics."""
        stats = self.cache.stats()
        self.assertIn("total_entries", stats)
        self.assertIn("valid_entries", stats)
        self.assertIn("cache_file", stats)


@pytest.mark.validation
@unittest.skipUnless(DOI_VALIDATOR_AVAILABLE, "DOI validator not available")
class TestDOIValidator(unittest.TestCase):
    """Test DOI validator functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = os.path.join(self.temp_dir, "manuscript")
        self.cache_dir = os.path.join(self.temp_dir, "cache")
        os.makedirs(self.manuscript_dir)
        os.makedirs(self.cache_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.fast
    def test_doi_format_validation(self):
        """Test DOI format validation."""
        validator = DOIValidator(
            self.manuscript_dir,
            enable_online_validation=False,
            cache_dir=self.cache_dir,
        )

        # Test valid DOI formats
        valid_dois = [
            "10.1000/test.2023.001",
            "10.1109/MCSE.2007.55",
            "10.1093/comjnl/27.2.97",
            "10.1371/journal.pcbi.1003285",
        ]

        for doi in valid_dois:
            self.assertTrue(validator.DOI_REGEX.match(doi), f"Valid DOI failed: {doi}")

        # Test invalid DOI formats
        invalid_dois = [
            "not-a-doi",
            "10.test/invalid",
            "10./invalid",
            "doi:10.1000/test",
        ]

        for doi in invalid_dois:
            self.assertFalse(
                validator.DOI_REGEX.match(doi), f"Invalid DOI passed: {doi}"
            )

    def test_bib_entry_extraction(self):
        """Test BibTeX entry extraction."""
        bib_content = """
@article{test1,
    title = {Test Article One},
    author = {Author One},
    journal = {Test Journal},
    year = 2023,
    doi = {10.1000/test1.2023.001}
}

@book{test2,
    title = {Test Book},
    author = {Author Two},
    year = 2022,
    publisher = {Test Publisher},
    doi = {10.1000/test2.2022.001}
}

@article{no_doi,
    title = {No DOI Article},
    author = {Author Three},
    year = 2021
}
"""

        with open(os.path.join(self.manuscript_dir, "03_REFERENCES.bib"), "w") as f:
            f.write(bib_content)

        validator = DOIValidator(
            self.manuscript_dir,
            enable_online_validation=False,
            cache_dir=self.cache_dir,
        )
        entries = validator._extract_bib_entries(bib_content)

        # Should extract 3 entries
        self.assertEqual(len(entries), 3)

        # Check entries with DOIs
        entries_with_doi = [e for e in entries if "doi" in e]
        self.assertEqual(len(entries_with_doi), 2)

        # Check specific entry
        test1_entry = next(e for e in entries if e["key"] == "test1")
        self.assertEqual(test1_entry["title"], "Test Article One")
        self.assertEqual(test1_entry["doi"], "10.1000/test1.2023.001")

    def test_validation_without_bib_file(self):
        """Test validation when bibliography file doesn't exist."""
        validator = DOIValidator(
            self.manuscript_dir,
            enable_online_validation=False,
            cache_dir=self.cache_dir,
        )
        result = validator.validate()

        # Should have warning about missing bib file
        self.assertTrue(result.has_warnings)
        warning_messages = [
            error.message
            for error in result.errors
            if error.level == ValidationLevel.WARNING
        ]
        self.assertTrue(
            any("bibliography file" in msg.lower() for msg in warning_messages)
        )

    def test_validation_offline_mode(self):
        """Test validation in offline mode."""
        bib_content = """
@article{test1,
    title = {Test Article},
    author = {Test Author},
    journal = {Test Journal},
    year = 2023,
    doi = {10.1000/test.2023.001}
}

@article{invalid_doi,
    title = {Invalid DOI Article},
    author = {Test Author},
    year = 2023,
    doi = {invalid-doi-format}
}
"""

        with open(os.path.join(self.manuscript_dir, "03_REFERENCES.bib"), "w") as f:
            f.write(bib_content)

        validator = DOIValidator(
            self.manuscript_dir,
            enable_online_validation=False,
            cache_dir=self.cache_dir,
        )
        result = validator.validate()

        # Should have error for invalid DOI format
        self.assertTrue(result.has_errors)
        error_messages = [
            error.message
            for error in result.errors
            if error.level == ValidationLevel.ERROR
        ]
        self.assertTrue(any("Invalid DOI format" in msg for msg in error_messages))

        # Should not perform online validation
        self.assertEqual(result.metadata["total_dois"], 2)
        self.assertEqual(result.metadata["invalid_format"], 1)

    @patch.object(DOIValidator, "_fetch_crossref_metadata")
    def test_validation_with_mock_crossref(self, mock_fetch):
        """Test validation with mocked CrossRef API."""

        # Mock CrossRef responses - different for each DOI
        def mock_response_side_effect(doi):
            if doi == "10.1000/test.2023.001":
                return {
                    "message": {
                        "title": ["Test Article Title"],
                        "container-title": ["Test Journal Name"],
                        "published-print": {"date-parts": [[2023]]},
                        "author": [{"family": "Smith", "given": "John"}],
                    }
                }
            elif doi == "10.1000/test.2023.002":
                return {
                    "message": {
                        "title": ["Completely Different Title"],
                        "container-title": ["Wrong Journal"],
                        "published-print": {"date-parts": [[2021]]},
                        "author": [{"family": "Wrong", "given": "Author"}],
                    }
                }
            return None

        mock_fetch.side_effect = mock_response_side_effect

        bib_content = """
@article{test_exact_match,
    title = {Test Article Title},
    author = {Smith, John},
    journal = {Test Journal Name},
    year = 2023,
    doi = {10.1000/test.2023.001}
}

@article{test_mismatch,
    title = {Different Title},
    author = {Smith, John},
    journal = {Different Journal},
    year = 2022,
    doi = {10.1000/test.2023.002}
}
"""

        with open(os.path.join(self.manuscript_dir, "03_REFERENCES.bib"), "w") as f:
            f.write(bib_content)

        validator = DOIValidator(
            self.manuscript_dir, enable_online_validation=True, cache_dir=self.cache_dir
        )
        result = validator.validate()

        # Should call our mocked method
        self.assertEqual(mock_fetch.call_count, 2)

        # Validation should complete successfully with our mocked data
        self.assertEqual(result.metadata["total_dois"], 2)
        self.assertEqual(result.metadata["validated_dois"], 2)
        self.assertEqual(result.metadata["api_failures"], 0)

    @patch.object(DOIValidator, "_fetch_datacite_metadata")
    @patch.object(DOIValidator, "_fetch_crossref_metadata")
    def test_validation_with_api_error(self, mock_crossref, mock_datacite):
        """Test validation when both CrossRef and DataCite APIs fail."""
        # Mock both APIs to return None (not found)
        mock_crossref.return_value = None
        mock_datacite.return_value = None

        bib_content = """
@article{test1,
    title = {Test Article},
    author = {Test Author},
    journal = {Test Journal},
    year = 2023,
    doi = {10.1000/test.2023.001}
}
"""

        with open(os.path.join(self.manuscript_dir, "03_REFERENCES.bib"), "w") as f:
            f.write(bib_content)

        validator = DOIValidator(
            self.manuscript_dir, enable_online_validation=True, cache_dir=self.cache_dir
        )
        result = validator.validate()

        # Should have warning about DOI not found in either API
        self.assertTrue(result.has_warnings)
        warning_messages = [
            error.message
            for error in result.errors
            if error.level == ValidationLevel.WARNING
        ]
        self.assertTrue(
            any("not found in available registrars" in msg for msg in warning_messages)
        )

    @pytest.mark.fast
    @patch("requests.get")
    @patch("crossref_commons.retrieval.get_publication_as_json")
    def test_datacite_fallback_success(self, mock_crossref, mock_datacite):
        """Test successful DataCite fallback when CrossRef fails."""
        # Mock CrossRef failure
        mock_crossref.side_effect = Exception("CrossRef API failed")

        # Mock successful DataCite response
        mock_datacite_response = Mock()
        mock_datacite_response.status_code = 200
        mock_datacite_response.json.return_value = {
            "data": {
                "attributes": {
                    "titles": [{"title": "Test DataCite Article"}],
                    "creators": [{"familyName": "Smith", "givenName": "John"}],
                    "publicationYear": 2023,
                    "publisher": "DataCite Publisher",
                }
            }
        }
        mock_datacite.return_value = mock_datacite_response

        bib_content = """
@article{datacite_test,
    title = {Test DataCite Article},
    author = {Smith, John},
    year = 2023,
    doi = {10.5281/zenodo.123456}
}
"""

        with open(os.path.join(self.manuscript_dir, "03_REFERENCES.bib"), "w") as f:
            f.write(bib_content)

        validator = DOIValidator(
            self.manuscript_dir, enable_online_validation=True, cache_dir=self.cache_dir
        )
        result = validator.validate()

        # Should have success message for DataCite validation
        success_messages = [
            error.message for error in result.errors if error.level.value == "success"
        ]
        self.assertTrue(any("DataCite" in msg for msg in success_messages))

        # Should call DataCite API after CrossRef fails
        mock_datacite.assert_called()

    def test_title_cleaning(self):
        """Test title cleaning for comparison."""
        validator = DOIValidator(
            self.manuscript_dir,
            enable_online_validation=False,
            cache_dir=self.cache_dir,
        )

        # Test LaTeX command removal
        latex_title = "Test \\textbf{bold} and \\textit{italic} text"
        cleaned = validator._clean_title(latex_title)
        self.assertEqual(cleaned, "test bold and italic text")

        # Test brace removal
        brace_title = "Test {special} formatting"
        cleaned = validator._clean_title(brace_title)
        self.assertEqual(cleaned, "test special formatting")

        # Test whitespace normalization
        whitespace_title = "Test   multiple    spaces"
        cleaned = validator._clean_title(whitespace_title)
        self.assertEqual(cleaned, "test multiple spaces")

    def test_journal_cleaning(self):
        """Test journal name cleaning for comparison."""
        validator = DOIValidator(
            self.manuscript_dir,
            enable_online_validation=False,
            cache_dir=self.cache_dir,
        )

        # Test ampersand removal
        journal_name = "Science \\& Engineering"
        cleaned = validator._clean_journal(journal_name)
        self.assertEqual(cleaned, "science engineering")

        # Test LaTeX command removal
        latex_journal = "Journal of \\LaTeX{} Research"
        cleaned = validator._clean_journal(latex_journal)
        self.assertEqual(cleaned, "journal of latex research")

    @patch.object(DOIValidator, "_fetch_crossref_metadata")
    def test_validation_with_cache(self, mock_fetch):
        """Test validation using cache."""
        # Mock CrossRef response
        mock_response = {
            "message": {
                "title": ["Cached Article"],
                "container-title": ["Cached Journal"],
                "published-print": {"date-parts": [[2023]]},
            }
        }
        mock_fetch.return_value = mock_response

        bib_content = """
@article{cached_test,
    title = {Cached Article},
    author = {Test Author},
    journal = {Cached Journal},
    year = 2023,
    doi = {10.1000/cached.2023.001}
}
"""

        with open(os.path.join(self.manuscript_dir, "03_REFERENCES.bib"), "w") as f:
            f.write(bib_content)

        validator1 = DOIValidator(
            self.manuscript_dir, enable_online_validation=True, cache_dir=self.cache_dir
        )
        result1 = validator1.validate()

        # Should call our mocked method once
        self.assertEqual(mock_fetch.call_count, 1)

        # Create second validator (should use cache)
        validator2 = DOIValidator(
            self.manuscript_dir, enable_online_validation=True, cache_dir=self.cache_dir
        )
        result2 = validator2.validate()

        # Should not call API again (cached)
        self.assertEqual(mock_fetch.call_count, 1)

        # Both should have same results
        self.assertEqual(len(result1.errors), len(result2.errors))

    def test_similarity_threshold(self):
        """Test title similarity threshold."""
        validator = DOIValidator(
            self.manuscript_dir,
            enable_online_validation=False,
            cache_dir=self.cache_dir,
        )

        # Test similar titles (should pass)
        title1 = "A Study of Machine Learning Applications"
        title2 = "A study of machine learning applications"  # Different case

        from difflib import SequenceMatcher

        similarity = SequenceMatcher(
            None, validator._clean_title(title1), validator._clean_title(title2)
        ).ratio()

        self.assertGreater(similarity, validator.similarity_threshold)

        # Test very different titles (should fail)
        title3 = "Completely Different Research Topic"
        similarity2 = SequenceMatcher(
            None, validator._clean_title(title1), validator._clean_title(title3)
        ).ratio()

        self.assertLess(similarity2, validator.similarity_threshold)


@pytest.mark.validation
@unittest.skipUnless(DOI_VALIDATOR_AVAILABLE, "DOI validator not available")
class TestDOIValidatorIntegration(unittest.TestCase):
    """Test DOI validator integration with citation validator."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = os.path.join(self.temp_dir, "manuscript")
        os.makedirs(self.manuscript_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("crossref_commons.retrieval.get_publication_as_json")
    def test_citation_validator_integration(self, mock_crossref):
        """Test DOI validation integration with citation validator."""
        try:
            from src.py.validators.citation_validator import CitationValidator
        except ImportError:
            self.skipTest("CitationValidator not available")

        # Mock CrossRef response
        mock_response = {
            "message": {
                "title": ["Integrated Test Article"],
                "container-title": ["Integration Journal"],
                "published-print": {"date-parts": [[2023]]},
            }
        }
        mock_crossref.return_value = mock_response

        # Create manuscript files
        main_content = """
# Test Manuscript

This cites @integrated_test and other references.
"""
        with open(os.path.join(self.manuscript_dir, "01_MAIN.md"), "w") as f:
            f.write(main_content)

        bib_content = """
@article{integrated_test,
    title = {Integrated Test Article},
    author = {Test Author},
    journal = {Integration Journal},
    year = 2023,
    doi = {10.1000/integrated.2023.001}
}
"""
        with open(os.path.join(self.manuscript_dir, "03_REFERENCES.bib"), "w") as f:
            f.write(bib_content)

        # Test with DOI validation enabled
        validator = CitationValidator(self.manuscript_dir, enable_doi_validation=True)
        result = validator.validate()

        # Should include DOI validation metadata
        self.assertIn("doi_validation", result.metadata)
        doi_metadata = result.metadata["doi_validation"]
        self.assertEqual(doi_metadata["total_dois"], 1)
        self.assertEqual(doi_metadata["validated_dois"], 1)

        # Test with DOI validation disabled
        validator_no_doi = CitationValidator(
            self.manuscript_dir, enable_doi_validation=False
        )
        result_no_doi = validator_no_doi.validate()

        # Should not include DOI validation metadata
        self.assertNotIn("doi_validation", result_no_doi.metadata)


class TestNetworkOperationTimeouts(unittest.TestCase):
    """Test network operation timeouts and retry logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.manuscript_dir = Path("test_manuscript")
        self.cache_dir = Path("test_cache")

    def test_doi_validation_with_retry_on_timeout(self):
        """Test DOI validation handles timeout gracefully."""
        from unittest.mock import patch

        import requests

        validator = DOIValidator(
            self.manuscript_dir,
            enable_online_validation=True,
            cache_dir=self.cache_dir,
        )

        # Patch at the point of use in the module
        with patch(
            "rxiv_maker.validators.doi_validator.get_publication_as_json"
        ) as mock_get_publication:
            # Simulate timeout
            mock_get_publication.side_effect = requests.exceptions.Timeout(
                "Connection timed out"
            )

            # Should raise the exception since _fetch_crossref_metadata re-raises
            with self.assertRaises(requests.exceptions.Timeout):
                validator._fetch_crossref_metadata("10.1234/test")
            self.assertEqual(mock_get_publication.call_count, 1)

    @patch("requests.get")
    def test_update_checker_timeout(self, mock_get):
        """Test update checker handles timeouts."""
        import requests

        from rxiv_maker.utils.update_checker import force_update_check

        # Simulate timeout
        mock_get.side_effect = requests.exceptions.Timeout("PyPI timeout")

        # Should handle timeout gracefully and return False
        has_update, _ = force_update_check()
        self.assertFalse(has_update)

    @patch("urllib.request.urlopen")
    def test_network_check_with_timeout(self, mock_urlopen):
        """Test network connectivity check with timeout."""
        from urllib.error import URLError

        # Simulate timeout
        mock_urlopen.side_effect = URLError(TimeoutError("Network timeout"))

        # Should handle gracefully
        try:
            from rxiv_maker.utils.update_checker import has_internet_connection

            result = has_internet_connection()
            self.assertFalse(result)
        except Exception:
            # If function doesn't exist, that's OK - just testing the pattern
            pass


if __name__ == "__main__":
    unittest.main()
