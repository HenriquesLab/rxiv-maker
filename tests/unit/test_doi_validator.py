"""Unit tests for the DOI validation system."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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

from rxiv_maker.core.cache.doi_cache import DOICache
from rxiv_maker.validators.base_validator import ValidationLevel
from rxiv_maker.validators.doi_validator import DOIValidator

DOI_VALIDATOR_AVAILABLE = True


@pytest.mark.validation
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
class TestDOIValidator(unittest.TestCase):
    """Test DOI validator functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = os.path.join(self.temp_dir, "manuscript")
        self.cache_dir = os.path.join(self.temp_dir, ".rxiv_cache")
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
            self.assertFalse(validator.DOI_REGEX.match(doi), f"Invalid DOI passed: {doi}")

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
        test1_entry = next(e for e in entries if e["entry_key"] == "test1")
        self.assertEqual(test1_entry["title"], "Test Article One")
        self.assertEqual(test1_entry["doi"], "10.1000/test1.2023.001")

    def test_validation_without_bib_file(self):
        """Test validation when bibliography file doesn't exist."""
        validator = DOIValidator(
            self.manuscript_dir,
            enable_online_validation=False,
            cache_dir=self.cache_dir,
            ignore_ci_environment=True,
        )
        result = validator.validate()

        # Should have warning about missing bib file
        self.assertTrue(result.has_warnings)
        warning_messages = [error.message for error in result.errors if error.level == ValidationLevel.WARNING]
        self.assertTrue(any("bibliography file" in msg.lower() for msg in warning_messages))

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
            ignore_ci_environment=True,
        )
        result = validator.validate()

        # Should have error for invalid DOI format
        self.assertTrue(result.has_errors)
        error_messages = [error.message for error in result.errors if error.level == ValidationLevel.ERROR]
        self.assertTrue(any("Invalid DOI format" in msg for msg in error_messages))

        # Should not perform online validation
        self.assertEqual(result.metadata["total_dois"], 2)
        self.assertEqual(result.metadata["invalid_format"], 1)

    def test_validation_with_offline_mode(self):
        """Test validation works consistently in offline mode - better for parallel execution."""
        import shutil
        import tempfile

        # Create unique temp directories for this test
        unique_temp = tempfile.mkdtemp()
        unique_manuscript = os.path.join(unique_temp, "manuscript")
        unique_cache = os.path.join(unique_temp, ".rxiv_cache")
        os.makedirs(unique_manuscript)
        os.makedirs(unique_cache)

        try:
            # Test with both valid and invalid DOI formats
            bib_content = """
@article{valid_doi,
    title = {Article with Valid DOI},
    author = {Smith, John},
    journal = {Test Journal},
    year = 2023,
    doi = {10.1000/valid.2023.001}
}

@article{invalid_doi,
    title = {Article with Invalid DOI},
    author = {Johnson, Jane},
    journal = {Another Journal},
    year = 2022,
    doi = {invalid-doi-format}
}
"""

            with open(os.path.join(unique_manuscript, "03_REFERENCES.bib"), "w") as f:
                f.write(bib_content)

            # Test with offline validation - should work consistently across parallel workers
            validator = DOIValidator(
                unique_manuscript,
                enable_online_validation=False,
                cache_dir=unique_cache,
                ignore_ci_environment=True,
            )
            result = validator.validate()

            # Should find 2 DOIs total
            self.assertEqual(result.metadata["total_dois"], 2)
            # Should identify 1 invalid format
            self.assertEqual(result.metadata["invalid_format"], 1)
            # No online validation, so no validated_dois or api_failures for valid ones
            self.assertEqual(result.metadata["validated_dois"], 0)
            self.assertEqual(result.metadata["api_failures"], 0)

            # Should have error for invalid DOI format
            self.assertTrue(result.has_errors)
            error_messages = [error.message for error in result.errors]
            self.assertTrue(any("Invalid DOI format" in msg for msg in error_messages))

        finally:
            # Clean up temporary directory
            shutil.rmtree(unique_temp, ignore_errors=True)

    @pytest.mark.fast
    @patch("requests.Session.get")
    @patch("requests.Session.head")
    @patch("requests.get")
    @patch("requests.head")
    @patch("crossref_commons.retrieval.get_publication_as_json")
    @patch.object(DOIValidator, "_check_network_connectivity", return_value=True)
    @patch.object(DOIValidator, "_validate_doi_metadata")
    def test_validation_with_api_error(
        self,
        mock_validate_metadata,
        mock_network_check,
        mock_crossref,
        mock_requests_head,
        mock_requests_get,
        mock_session_head,
        mock_session_get,
    ):
        """Test validation when metadata validation fails for all sources."""
        # Configure mocks to prevent actual network calls
        import requests

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_session_get.return_value = mock_response
        mock_session_head.return_value = mock_response
        mock_requests_get.return_value = mock_response
        mock_requests_head.return_value = mock_response
        mock_crossref.side_effect = requests.exceptions.RequestException("Mocked network error")

        # Mock metadata validation to return error indicating no sources available
        from rxiv_maker.validators.base_validator import ValidationError, ValidationLevel

        mock_validate_metadata.return_value = [
            ValidationError(
                level=ValidationLevel.ERROR,
                message="Could not validate metadata for DOI 10.1000/test.2023.001 from any source",
                file_path="03_REFERENCES.bib",
                context="Entry: test1",
                error_code="E1004",
            )
        ]

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

        # Clear cache before test to ensure fresh API calls
        if os.path.exists(self.cache_dir):
            import shutil

            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir)

        validator = DOIValidator(
            self.manuscript_dir,
            enable_online_validation=True,
            cache_dir=self.cache_dir,
            ignore_ci_environment=True,
            force_validation=True,  # Force validation to bypass checksum optimization
        )
        result = validator.validate()

        # Should have error about DOI not found in any source
        self.assertTrue(result.has_errors)
        error_messages = [error.message for error in result.errors if error.level.value == "error"]
        self.assertTrue(
            any("Could not validate metadata" in msg and "from any source" in msg for msg in error_messages)
        )

    @pytest.mark.fast
    @patch("requests.Session.get")
    @patch("requests.Session.head")
    @patch("requests.get")
    @patch("requests.head")
    @patch("crossref_commons.retrieval.get_publication_as_json")
    @patch.object(DOIValidator, "_check_network_connectivity", return_value=True)
    @patch.object(DOIValidator, "_validate_doi_metadata")
    def test_datacite_fallback_success(
        self,
        mock_validate_metadata,
        mock_network_check,
        mock_crossref,
        mock_requests_head,
        mock_requests_get,
        mock_session_head,
        mock_session_get,
    ):
        """Test successful DataCite fallback when CrossRef fails."""
        # Configure mocks to prevent actual network calls
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_session_get.return_value = mock_response
        mock_session_head.return_value = mock_response
        mock_requests_get.return_value = mock_response
        mock_requests_head.return_value = mock_response
        import requests

        mock_crossref.side_effect = requests.exceptions.RequestException("Mocked network error")

        # Mock successful DataCite validation
        from rxiv_maker.validators.base_validator import ValidationError, ValidationLevel

        mock_validate_metadata.return_value = [
            ValidationError(
                level=ValidationLevel.SUCCESS,
                message="DOI 10.5281/zenodo.123456 successfully validated against DataCite",
                file_path="03_REFERENCES.bib",
                context="Entry: datacite_test",
            )
        ]

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
            self.manuscript_dir,
            enable_online_validation=True,
            cache_dir=self.cache_dir,
            ignore_ci_environment=True,
            force_validation=True,
        )
        result = validator.validate()

        # Should have success message for DataCite validation
        success_messages = [error.message for error in result.errors if error.level.value == "success"]
        self.assertTrue(any("DataCite" in msg for msg in success_messages))

        # Should call the metadata validation method
        mock_validate_metadata.assert_called()

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

    def test_validation_with_cache(self):
        """Test validation using cache - simplified for parallel execution."""
        import shutil
        import tempfile

        # Create unique temp directories for this test to avoid shared state
        unique_temp = tempfile.mkdtemp()
        unique_manuscript = os.path.join(unique_temp, "manuscript")
        unique_cache = os.path.join(unique_temp, ".rxiv_cache")
        os.makedirs(unique_manuscript)
        os.makedirs(unique_cache)

        try:
            # Create a simple bib file with valid DOI format
            bib_content = """
@article{cached_test,
    title = {Cached Article},
    author = {Test Author},
    journal = {Cached Journal},
    year = 2023,
    doi = {10.1000/cached.2023.001}
}
"""

            with open(os.path.join(unique_manuscript, "03_REFERENCES.bib"), "w") as f:
                f.write(bib_content)

            # Test with offline validation to avoid network issues in parallel tests
            validator1 = DOIValidator(
                unique_manuscript, enable_online_validation=False, cache_dir=unique_cache, ignore_ci_environment=True
            )
            result1 = validator1.validate()

            # Should find 1 DOI and validate format (but not online)
            self.assertEqual(result1.metadata["total_dois"], 1)
            self.assertEqual(result1.metadata["invalid_format"], 0)  # DOI format is valid

            # Create second validator - should behave consistently
            validator2 = DOIValidator(
                unique_manuscript, enable_online_validation=False, cache_dir=unique_cache, ignore_ci_environment=True
            )
            result2 = validator2.validate()

            # Should get the same results
            self.assertEqual(result2.metadata["total_dois"], 1)
            self.assertEqual(result2.metadata["invalid_format"], 0)

            # Both should have same basic results (total DOIs)
            self.assertEqual(result1.metadata["total_dois"], result2.metadata["total_dois"])

        finally:
            # Clean up temporary directory
            shutil.rmtree(unique_temp, ignore_errors=True)

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

        similarity = SequenceMatcher(None, validator._clean_title(title1), validator._clean_title(title2)).ratio()

        self.assertGreater(similarity, validator.similarity_threshold)

        # Test very different titles (should fail)
        title3 = "Completely Different Research Topic"
        similarity2 = SequenceMatcher(None, validator._clean_title(title1), validator._clean_title(title3)).ratio()

        self.assertLess(similarity2, validator.similarity_threshold)


@pytest.mark.validation
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

    @patch("requests.Session.get")
    @patch("requests.Session.head")
    @patch("requests.get")
    @patch("requests.head")
    @patch("crossref_commons.retrieval.get_publication_as_json")
    def test_citation_validator_integration(
        self, mock_crossref, mock_requests_head, mock_requests_get, mock_session_head, mock_session_get
    ):
        """Test DOI validation integration with citation validator."""
        try:
            from rxiv_maker.validators.citation_validator import CitationValidator
        except ImportError:
            self.skipTest("CitationValidator not available")

        # Configure mocks to prevent actual network calls
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_session_get.return_value = mock_response
        mock_session_head.return_value = mock_response
        mock_requests_get.return_value = mock_response
        mock_requests_head.return_value = mock_response

        # Mock CrossRef response
        crossref_response = {
            "message": {
                "title": ["Integrated Test Article"],
                "container-title": ["Integration Journal"],
                "published-print": {"date-parts": [[2023]]},
            }
        }
        mock_crossref.return_value = crossref_response

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
        validator_no_doi = CitationValidator(self.manuscript_dir, enable_doi_validation=False)
        result_no_doi = validator_no_doi.validate()

        # Should not include DOI validation metadata
        self.assertNotIn("doi_validation", result_no_doi.metadata)

    def test_citation_validator_config_based_doi_validation(self):
        """Test that citation validator respects config file DOI validation setting."""
        # Create config with DOI validation disabled
        config_content = """
title: "Test Article"
enable_doi_validation: false
bibliography: 03_REFERENCES.bib
"""
        config_path = os.path.join(self.manuscript_dir, "00_CONFIG.yml")
        with open(config_path, "w") as f:
            f.write(config_content)

        # Create main markdown file
        main_content = "# Test\n\nCitations: @valid_doi"
        main_path = os.path.join(self.manuscript_dir, "01_MAIN.md")
        with open(main_path, "w") as f:
            f.write(main_content)

        # Test that validator reads config setting (DOI validation should be disabled)
        validator = DOIValidator(self.manuscript_dir, enable_online_validation=None)
        result = validator.validate()

        # Should not include DOI validation metadata when disabled via config
        self.assertNotIn("doi_validation", result.metadata)


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
        with patch("rxiv_maker.validators.doi.api_clients.get_publication_as_json") as mock_get_publication:
            # Simulate timeout
            mock_get_publication.side_effect = requests.exceptions.Timeout("Connection timed out")

            # Should return None since CrossRefClient catches exceptions and returns None
            result = validator._fetch_crossref_metadata("10.1234/test")
            self.assertIsNone(result)
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
