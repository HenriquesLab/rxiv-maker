"""Tests for URL to DOI extraction utilities."""

import pytest

from rxiv_maker.utils.url_to_doi import extract_doi_from_url, normalize_doi_input


class TestExtractDoiFromUrl:
    """Test URL to DOI extraction."""

    def test_direct_doi_passthrough(self):
        """Test that DOIs are passed through unchanged."""
        doi = "10.1038/nature12373"
        assert extract_doi_from_url(doi) == doi

    def test_doi_org_urls(self):
        """Test DOI.org URLs."""
        assert extract_doi_from_url("https://doi.org/10.1038/nature12373") == "10.1038/nature12373"
        assert extract_doi_from_url("https://dx.doi.org/10.1126/science.1234567") == "10.1126/science.1234567"
        assert extract_doi_from_url("http://doi.org/10.1371/journal.pone.0123456") == "10.1371/journal.pone.0123456"

    def test_nature_articles(self):
        """Test Nature article URLs."""
        assert (
            extract_doi_from_url("https://www.nature.com/articles/d41586-022-00563-z") == "10.1038/d41586-022-00563-z"
        )
        assert extract_doi_from_url("https://nature.com/articles/nature12373") == "10.1038/nature12373"

    def test_plos_articles(self):
        """Test PLOS article URLs."""
        assert (
            extract_doi_from_url("https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0123456")
            == "10.1371/journal.pone.0123456"
        )

    def test_arxiv_papers(self):
        """Test arXiv paper URLs."""
        assert extract_doi_from_url("https://arxiv.org/abs/1234.5678") == "10.48550/arXiv.1234.5678"
        assert extract_doi_from_url("https://arxiv.org/abs/2301.12345v2") == "10.48550/arXiv.2301.12345v2"

    def test_biorxiv_papers(self):
        """Test bioRxiv paper URLs."""
        assert (
            extract_doi_from_url("https://www.biorxiv.org/content/10.1101/2023.01.01.522473v1")
            == "10.1101/2023.01.01.522473v1"
        )

    def test_invalid_urls(self):
        """Test that invalid URLs return None."""
        assert extract_doi_from_url("https://www.google.com") is None
        assert extract_doi_from_url("not a url") is None
        assert extract_doi_from_url("") is None
        assert extract_doi_from_url(None) is None

    def test_malformed_urls(self):
        """Test that malformed URLs are handled gracefully."""
        assert extract_doi_from_url("http://") is None
        assert extract_doi_from_url("://invalid") is None


class TestNormalizeDoiInput:
    """Test DOI input normalization."""

    def test_valid_doi_passthrough(self):
        """Test that valid DOIs are passed through unchanged."""
        doi = "10.1038/nature12373"
        assert normalize_doi_input(doi) == doi

    def test_url_to_doi_conversion(self):
        """Test that URLs are converted to DOIs."""
        assert normalize_doi_input("https://doi.org/10.1038/nature12373") == "10.1038/nature12373"
        assert normalize_doi_input("https://www.nature.com/articles/d41586-022-00563-z") == "10.1038/d41586-022-00563-z"

    def test_invalid_input_raises_error(self):
        """Test that invalid input raises appropriate errors."""
        with pytest.raises(ValueError, match="Empty input provided"):
            normalize_doi_input("")

        with pytest.raises(ValueError, match="Could not extract a valid DOI from URL"):
            normalize_doi_input("https://www.google.com")

        with pytest.raises(ValueError, match="Invalid DOI format"):
            normalize_doi_input("invalid doi")

    def test_detailed_error_messages(self):
        """Test that error messages are helpful."""
        # URL that doesn't contain a DOI
        with pytest.raises(ValueError) as exc_info:
            normalize_doi_input("https://www.example.com")
        assert "Could not extract a valid DOI from URL" in str(exc_info.value)

        # Invalid DOI format
        with pytest.raises(ValueError) as exc_info:
            normalize_doi_input("not-a-doi")
        assert "Invalid DOI format" in str(exc_info.value)
        assert "DOIs should start with '10.' or be a valid URL containing a DOI" in str(exc_info.value)
