"""Unit tests for the DOI validation fallback system.

This module tests the multi-source DOI validation fallback system that
attempts to validate DOIs through multiple APIs in cascading order:
CrossRef -> DataCite -> OpenAlex -> Semantic Scholar -> Handle System -> JOSS
"""

import unittest
from unittest.mock import Mock, patch

try:
    import pytest

    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

    class MockPytest:
        class mark:
            @staticmethod
            def validation(cls):
                return cls

            @staticmethod
            def slow(cls):
                return cls

    pytest = MockPytest()

from rxiv_maker.validators.doi import (
    BaseDOIClient,
    CrossRefClient,
    DataCiteClient,
    DOIResolver,
    HandleSystemClient,
    JOSSClient,
    OpenAlexClient,
    SemanticScholarClient,
)

DOI_CLIENTS_AVAILABLE = True


@pytest.mark.validation
class TestDOIClientIndividual(unittest.TestCase):
    """Test individual DOI client implementations."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_doi = "10.1000/test.2023.001"
        self.test_metadata = {
            "title": ["Test Article"],
            "container-title": ["Test Journal"],
            "published-print": {"date-parts": [[2023]]},
            "author": [{"given": "John", "family": "Smith"}],
        }

    def test_base_client_abstract_methods(self):
        """Test that BaseDOIClient is properly abstract."""
        with self.assertRaises(TypeError):
            BaseDOIClient()

    @patch("rxiv_maker.validators.doi.api_clients.get_publication_as_json")
    def test_crossref_client_primary_success(self, mock_get_publication):
        """Test CrossRef client successful primary fetch."""
        mock_get_publication.return_value = {"message": self.test_metadata}

        client = CrossRefClient(timeout=5)
        result = client.fetch_metadata(self.test_doi)

        self.assertIsNotNone(result)
        self.assertEqual(result["title"], ["Test Article"])
        mock_get_publication.assert_called_once_with(self.test_doi)

    @patch("rxiv_maker.validators.doi.api_clients.get_publication_as_json")
    def test_crossref_client_fallback_to_rest_api(self, mock_get_publication):
        """Test CrossRef client falls back to REST API when library fails."""
        # Primary method fails
        mock_get_publication.side_effect = Exception("Library fetch failed")

        # Mock the session.get method for the fallback
        client = CrossRefClient(timeout=5)

        # Create a mock response for the fallback API call
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": self.test_metadata}

        # Mock the session.get method
        with patch.object(client.session, "get", return_value=mock_response):
            result = client.fetch_metadata(self.test_doi)

        self.assertIsNotNone(result)
        self.assertEqual(result["title"], ["Test Article"])
        mock_get_publication.assert_called_once_with(self.test_doi)

    @patch.object(DataCiteClient, "_make_request")
    def test_datacite_client_success(self, mock_make_request):
        """Test DataCite client successful fetch."""
        datacite_attributes = {
            "titles": [{"title": "DataCite Test Article"}],
            "creators": [{"name": "Smith, John"}],
            "publicationYear": 2023,
            "publisher": "DataCite Publisher",
        }
        # DataCite API response format
        mock_make_request.return_value = {"data": {"attributes": datacite_attributes}}

        client = DataCiteClient(timeout=5)
        result = client.fetch_metadata(self.test_doi)

        self.assertIsNotNone(result)
        # DataCite client returns just the attributes, not the full response
        self.assertEqual(result["titles"][0]["title"], "DataCite Test Article")

    @patch.object(OpenAlexClient, "_make_request")
    def test_openalex_client_success(self, mock_make_request):
        """Test OpenAlex client successful fetch."""
        openalex_metadata = {
            "title": "OpenAlex Test Article",
            "display_name": "OpenAlex Test Article",
            "publication_year": 2023,
            "authorships": [{"author": {"display_name": "John Smith"}}],
            "host_venue": {"display_name": "OpenAlex Journal"},
        }
        mock_make_request.return_value = openalex_metadata

        client = OpenAlexClient(timeout=5)
        result = client.fetch_metadata(self.test_doi)

        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "OpenAlex Test Article")

    def test_semantic_scholar_client_success(self):
        """Test Semantic Scholar client successful fetch."""
        semantic_metadata = {
            "title": "Semantic Scholar Test Article",
            "authors": [{"name": "John Smith"}],
            "year": 2023,
            "venue": "Semantic Scholar Journal",
        }

        client = SemanticScholarClient(timeout=5)

        # Create a mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = semantic_metadata

        # Mock the session.get method directly on the client instance
        with patch.object(client.session, "get", return_value=mock_response):
            result = client.fetch_metadata(self.test_doi)

        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Semantic Scholar Test Article")

    @patch.object(HandleSystemClient, "_make_request")
    def test_handle_system_client_success(self, mock_make_request):
        """Test Handle System client successful fetch."""
        handle_metadata = {
            "handle": self.test_doi,
            "values": [
                {"type": "URL", "data": {"value": "https://example.com/article"}},
                {"type": "TITLE", "data": {"value": "Handle System Test Article"}},
            ],
        }
        mock_make_request.return_value = handle_metadata

        client = HandleSystemClient(timeout=5)
        result = client.fetch_metadata(self.test_doi)

        self.assertIsNotNone(result)
        self.assertEqual(result["handle"], self.test_doi)

    @patch.object(JOSSClient, "_make_request")
    def test_joss_client_success(self, mock_make_request):
        """Test JOSS client successful fetch."""
        joss_doi = "10.21105/joss.01234"  # Valid JOSS DOI format
        joss_metadata = {
            "title": "JOSS Test Article",
            "authors": [{"given_name": "John", "last_name": "Smith"}],
            "published_at": "2023-01-01",
            "state": "published",
        }
        mock_make_request.return_value = joss_metadata

        client = JOSSClient(timeout=5)
        result = client.fetch_metadata(joss_doi)

        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "JOSS Test Article")


@pytest.mark.validation
class TestDOIResolverFallbackChain(unittest.TestCase):
    """Test DOI resolver fallback chain behavior."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_doi = "10.1000/test.2023.001"
        self.crossref_metadata = {
            "title": ["CrossRef Article"],
            "container-title": ["CrossRef Journal"],
            "published-print": {"date-parts": [[2023]]},
        }
        self.datacite_metadata = {
            "data": {"attributes": {"titles": [{"title": "DataCite Article"}], "publicationYear": 2023}}
        }

    def test_doi_resolver_initialization(self):
        """Test DOI resolver initializes with all clients."""
        resolver = DOIResolver(
            enable_crossref=True,
            enable_datacite=True,
            enable_openalex=True,
            enable_semantic_scholar=True,
            enable_handle_system=True,
            enable_joss=True,
            timeout=5,
        )

        self.assertIsInstance(resolver.crossref_client, CrossRefClient)
        self.assertIsInstance(resolver.datacite_client, DataCiteClient)
        self.assertIsInstance(resolver.openalex_client, OpenAlexClient)
        self.assertIsInstance(resolver.semantic_scholar_client, SemanticScholarClient)
        self.assertIsInstance(resolver.handle_system_client, HandleSystemClient)
        self.assertIsInstance(resolver.joss_client, JOSSClient)

    @patch.object(CrossRefClient, "fetch_metadata")
    def test_fallback_chain_crossref_success_no_fallback(self, mock_crossref):
        """Test that when CrossRef succeeds, no fallback APIs are called."""
        mock_crossref.return_value = self.crossref_metadata

        resolver = DOIResolver(enable_crossref=True, enable_datacite=True, timeout=5)

        with patch.object(resolver.datacite_client, "fetch_metadata") as mock_datacite:
            result = resolver.resolve(self.test_doi)

            self.assertIsNotNone(result)
            self.assertEqual(result["source"], "crossref")
            self.assertEqual(result["metadata"]["title"], ["CrossRef Article"])

            # Verify fallback wasn't called
            mock_crossref.assert_called_once_with(self.test_doi)
            mock_datacite.assert_not_called()

    @patch.object(CrossRefClient, "fetch_metadata")
    @patch.object(DataCiteClient, "fetch_metadata")
    def test_fallback_chain_crossref_fails_datacite_succeeds(self, mock_datacite, mock_crossref):
        """Test fallback from CrossRef to DataCite when CrossRef fails."""
        mock_crossref.return_value = None  # CrossRef fails
        mock_datacite.return_value = self.datacite_metadata  # DataCite succeeds

        resolver = DOIResolver(enable_crossref=True, enable_datacite=True, timeout=5)

        result = resolver.resolve(self.test_doi)

        self.assertIsNotNone(result)
        self.assertEqual(result["source"], "datacite")
        self.assertEqual(result["metadata"]["data"]["attributes"]["titles"][0]["title"], "DataCite Article")

        # Verify both were called in order
        mock_crossref.assert_called_once_with(self.test_doi)
        mock_datacite.assert_called_once_with(self.test_doi)

    @patch.object(CrossRefClient, "fetch_metadata")
    @patch.object(DataCiteClient, "fetch_metadata")
    @patch.object(OpenAlexClient, "fetch_metadata")
    def test_fallback_chain_multiple_failures_then_success(self, mock_openalex, mock_datacite, mock_crossref):
        """Test fallback through multiple failed APIs until one succeeds."""
        openalex_metadata = {"title": "OpenAlex Article", "publication_year": 2023}

        mock_crossref.return_value = None  # CrossRef fails
        mock_datacite.return_value = None  # DataCite fails
        mock_openalex.return_value = openalex_metadata  # OpenAlex succeeds

        resolver = DOIResolver(enable_crossref=True, enable_datacite=True, enable_openalex=True, timeout=5)

        result = resolver.resolve(self.test_doi)

        self.assertIsNotNone(result)
        self.assertEqual(result["source"], "openalex")
        self.assertEqual(result["metadata"]["title"], "OpenAlex Article")

        # Verify all were called in order
        mock_crossref.assert_called_once_with(self.test_doi)
        mock_datacite.assert_called_once_with(self.test_doi)
        mock_openalex.assert_called_once_with(self.test_doi)

    @patch.object(CrossRefClient, "fetch_metadata")
    @patch.object(DataCiteClient, "fetch_metadata")
    @patch.object(OpenAlexClient, "fetch_metadata")
    @patch.object(SemanticScholarClient, "fetch_metadata")
    @patch.object(HandleSystemClient, "fetch_metadata")
    @patch.object(JOSSClient, "fetch_metadata")
    def test_fallback_chain_all_apis_fail(
        self, mock_joss, mock_handle, mock_semantic, mock_openalex, mock_datacite, mock_crossref
    ):
        """Test behavior when all APIs fail."""
        # All APIs return None (failure)
        mock_crossref.return_value = None
        mock_datacite.return_value = None
        mock_openalex.return_value = None
        mock_semantic.return_value = None
        mock_handle.return_value = None
        mock_joss.return_value = None

        resolver = DOIResolver(
            enable_crossref=True,
            enable_datacite=True,
            enable_openalex=True,
            enable_semantic_scholar=True,
            enable_handle_system=True,
            enable_joss=True,
            timeout=5,
        )

        result = resolver.resolve(self.test_doi)

        self.assertIsNone(result)

        # Verify all were called in order
        mock_crossref.assert_called_once_with(self.test_doi)
        mock_datacite.assert_called_once_with(self.test_doi)
        mock_openalex.assert_called_once_with(self.test_doi)
        mock_semantic.assert_called_once_with(self.test_doi)
        mock_handle.assert_called_once_with(self.test_doi)
        mock_joss.assert_called_once_with(self.test_doi)

    def test_selective_api_enabling(self):
        """Test that only enabled APIs are used in fallback chain."""
        resolver = DOIResolver(
            enable_crossref=True,
            enable_datacite=False,  # Disabled
            enable_openalex=True,
            enable_semantic_scholar=False,  # Disabled
            enable_handle_system=False,  # Disabled
            enable_joss=False,  # Disabled
            timeout=5,
        )

        # Should only have CrossRef and OpenAlex clients
        self.assertIsNotNone(resolver.crossref_client)
        self.assertIsNone(resolver.datacite_client)
        self.assertIsNotNone(resolver.openalex_client)
        self.assertIsNone(resolver.semantic_scholar_client)
        self.assertIsNone(resolver.handle_system_client)
        self.assertIsNone(resolver.joss_client)


@pytest.mark.validation
class TestDOIClientErrorHandling(unittest.TestCase):
    """Test error handling in DOI client fallback scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_doi = "10.1000/test.2023.001"

    @patch.object(CrossRefClient, "_make_request")
    def test_network_timeout_handling(self, mock_make_request):
        """Test handling of network timeouts."""
        import requests

        mock_make_request.side_effect = requests.exceptions.Timeout("Request timed out")

        client = CrossRefClient(timeout=5)
        result = client.fetch_metadata(self.test_doi)

        self.assertIsNone(result)

    @patch.object(CrossRefClient, "_make_request")
    def test_http_error_handling(self, mock_make_request):
        """Test handling of HTTP errors (404, 500, etc.)."""
        import requests

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_make_request.side_effect = requests.exceptions.HTTPError("404 Not Found")

        client = CrossRefClient(timeout=5)
        result = client.fetch_metadata(self.test_doi)

        self.assertIsNone(result)

    @patch.object(DataCiteClient, "_make_request")
    def test_json_decode_error_handling(self, mock_make_request):
        """Test handling of invalid JSON responses."""
        import json

        mock_make_request.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        client = DataCiteClient(timeout=5)
        result = client.fetch_metadata(self.test_doi)

        self.assertIsNone(result)

    @patch.object(OpenAlexClient, "_make_request")
    def test_unexpected_response_format_handling(self, mock_make_request):
        """Test handling of unexpected response formats."""
        # Return valid JSON but unexpected structure
        mock_make_request.return_value = {"unexpected": "format", "no_title": True}

        client = OpenAlexClient(timeout=5)
        result = client.fetch_metadata(self.test_doi)

        # Should return the response even if format is unexpected
        # (validation happens at a higher level)
        self.assertIsNotNone(result)
        self.assertEqual(result["unexpected"], "format")


@pytest.mark.validation
class TestDOIFallbackPerformance(unittest.TestCase):
    """Test performance characteristics of the DOI fallback system."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_doi = "10.1000/test.2023.001"

    @patch.object(CrossRefClient, "fetch_metadata")
    @patch.object(DataCiteClient, "fetch_metadata")
    def test_fallback_timeout_progression(self, mock_datacite, mock_crossref):
        """Test that fallback doesn't take excessively long."""
        import time

        def slow_crossref_call(doi):
            time.sleep(0.1)  # Simulate slow response
            return None

        def fast_datacite_call(doi):
            return {"data": {"attributes": {"titles": [{"title": "Fast Response"}]}}}

        mock_crossref.side_effect = slow_crossref_call
        mock_datacite.side_effect = fast_datacite_call

        resolver = DOIResolver(
            enable_crossref=True,
            enable_datacite=True,
            timeout=1,  # Short timeout
        )

        start_time = time.time()
        result = resolver.resolve(self.test_doi)
        end_time = time.time()

        # Should complete quickly even with slow primary API
        self.assertLess(end_time - start_time, 2.0)  # Should be under 2 seconds
        self.assertIsNotNone(result)
        self.assertEqual(result["source"], "datacite")

    def test_concurrent_doi_resolution_performance(self):
        """Test performance with multiple DOIs resolved concurrently."""
        import concurrent.futures
        import time

        test_dois = [f"10.1000/test.2023.{i:03d}" for i in range(5)]

        resolver = DOIResolver(enable_crossref=True, enable_datacite=True, timeout=5)

        with patch.object(resolver.crossref_client, "fetch_metadata") as mock_crossref:
            # Mock slow CrossRef that eventually succeeds
            def slow_success(doi):
                time.sleep(0.05)  # Small delay
                return {"title": [f"Article for {doi}"]}

            mock_crossref.side_effect = slow_success

            start_time = time.time()

            # Resolve multiple DOIs concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(resolver.resolve, doi) for doi in test_dois]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]

            end_time = time.time()

            # Should complete all 5 DOIs faster than sequential execution
            self.assertLess(end_time - start_time, 1.0)  # Should be under 1 second for concurrent
            self.assertEqual(len(results), 5)
            self.assertTrue(all(result is not None for result in results))


if __name__ == "__main__":
    unittest.main()
