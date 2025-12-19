"""Unit tests for DOCX DOI resolution functionality."""

from unittest.mock import Mock, patch

import pytest

from rxiv_maker.exporters.docx_exporter import DocxExporter
from rxiv_maker.utils.bibliography_parser import BibEntry


@pytest.mark.unit
class TestDOIResolution:
    """Test DOI resolution in DOCX exporter."""

    def test_clean_title_removes_latex_commands(self):
        """Test that _clean_title_for_search removes LaTeX commands."""
        # Create a minimal exporter just to access the method
        with patch("rxiv_maker.exporters.docx_exporter.PathManager"):
            with patch("rxiv_maker.exporters.docx_exporter.ConfigManager"):
                exporter = DocxExporter("dummy_path", resolve_dois=False)

        # Test various LaTeX commands
        test_cases = [
            # (input, expected_output)
            (r"\textit{Italic Text}", "Italic Text"),
            (r"\textbf{Bold Text}", "Bold Text"),
            (r"{Braced Text}", "Braced Text"),
            (r"The \LaTeX System", "The System"),  # Whitespace normalized
            (r"Test & Symbol", "Test Symbol"),  # Whitespace normalized
            (r"Multiple  \t\n  Spaces", "Multiple Spaces"),
            (r"\emph{Emphasized} and \textsc{SmallCaps}", "Emphasized and SmallCaps"),
        ]

        for input_title, expected in test_cases:
            result = exporter._clean_title_for_search(input_title)
            assert result == expected, f"Failed for input: {input_title}"

    def test_clean_title_normalizes_whitespace(self):
        """Test that _clean_title_for_search normalizes whitespace."""
        with patch("rxiv_maker.exporters.docx_exporter.PathManager"):
            with patch("rxiv_maker.exporters.docx_exporter.ConfigManager"):
                exporter = DocxExporter("dummy_path", resolve_dois=False)

        title = "Title   with    irregular\n\nwhitespace"
        result = exporter._clean_title_for_search(title)

        assert result == "Title with irregular whitespace"

    @patch("requests.get")
    def test_resolve_doi_success(self, mock_get):
        """Test successful DOI resolution from CrossRef."""
        with patch("rxiv_maker.exporters.docx_exporter.PathManager"):
            with patch("rxiv_maker.exporters.docx_exporter.ConfigManager"):
                exporter = DocxExporter("dummy_path", resolve_dois=True)

        # Create a mock bibliography entry
        entry = BibEntry(
            key="testkey2023",
            entry_type="article",
            fields={
                "title": "Test Article Title",
                "author": "John Doe",
                "year": "2023",
            },
        )

        # Mock CrossRef API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "items": [
                    {
                        "title": ["Test Article Title"],
                        "DOI": "10.1234/test.2023",
                        "published": {"date-parts": [[2023, 5, 15]]},
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        # Test DOI resolution
        doi = exporter._resolve_doi_from_metadata(entry)

        assert doi == "10.1234/test.2023"
        assert mock_get.called

    @patch("requests.get")
    def test_resolve_doi_no_title(self, mock_get):
        """Test DOI resolution fails gracefully when title is missing."""
        with patch("rxiv_maker.exporters.docx_exporter.PathManager"):
            with patch("rxiv_maker.exporters.docx_exporter.ConfigManager"):
                exporter = DocxExporter("dummy_path", resolve_dois=True)

        # Entry without title
        entry = BibEntry(
            key="testkey2023",
            entry_type="article",
            fields={"author": "John Doe", "year": "2023"},
        )

        doi = exporter._resolve_doi_from_metadata(entry)

        assert doi is None
        assert not mock_get.called  # Should not make API call

    @patch("requests.get")
    def test_resolve_doi_year_mismatch(self, mock_get):
        """Test DOI resolution skips results with mismatched year."""
        with patch("rxiv_maker.exporters.docx_exporter.PathManager"):
            with patch("rxiv_maker.exporters.docx_exporter.ConfigManager"):
                exporter = DocxExporter("dummy_path", resolve_dois=True)

        entry = BibEntry(
            key="testkey2023",
            entry_type="article",
            fields={
                "title": "Test Article Title",
                "year": "2023",
            },
        )

        # Mock response with different year
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "items": [
                    {
                        "title": ["Test Article Title"],
                        "DOI": "10.1234/test.2022",
                        "published": {"date-parts": [[2022, 5, 15]]},  # Wrong year
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        doi = exporter._resolve_doi_from_metadata(entry)

        # Should reject because year doesn't match
        assert doi is None

    @patch("requests.get")
    def test_resolve_doi_timeout(self, mock_get):
        """Test DOI resolution handles API timeout gracefully."""
        import requests

        with patch("rxiv_maker.exporters.docx_exporter.PathManager"):
            with patch("rxiv_maker.exporters.docx_exporter.ConfigManager"):
                exporter = DocxExporter("dummy_path", resolve_dois=True)

        entry = BibEntry(
            key="testkey2023",
            entry_type="article",
            fields={"title": "Test Article Title", "year": "2023"},
        )

        # Simulate timeout
        mock_get.side_effect = requests.exceptions.Timeout()

        doi = exporter._resolve_doi_from_metadata(entry)

        assert doi is None  # Should return None, not crash

    @patch("requests.get")
    def test_resolve_doi_connection_error(self, mock_get):
        """Test DOI resolution handles connection error gracefully."""
        import requests

        with patch("rxiv_maker.exporters.docx_exporter.PathManager"):
            with patch("rxiv_maker.exporters.docx_exporter.ConfigManager"):
                exporter = DocxExporter("dummy_path", resolve_dois=True)

        entry = BibEntry(
            key="testkey2023",
            entry_type="article",
            fields={"title": "Test Article Title"},
        )

        # Simulate connection error
        mock_get.side_effect = requests.exceptions.ConnectionError()

        doi = exporter._resolve_doi_from_metadata(entry)

        assert doi is None  # Should return None, not crash

    @patch("requests.get")
    def test_resolve_doi_no_results(self, mock_get):
        """Test DOI resolution when CrossRef returns no results."""
        with patch("rxiv_maker.exporters.docx_exporter.PathManager"):
            with patch("rxiv_maker.exporters.docx_exporter.ConfigManager"):
                exporter = DocxExporter("dummy_path", resolve_dois=True)

        entry = BibEntry(
            key="testkey2023",
            entry_type="article",
            fields={"title": "Nonexistent Article Title"},
        )

        # Mock empty response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"items": []}}
        mock_get.return_value = mock_response

        doi = exporter._resolve_doi_from_metadata(entry)

        assert doi is None

    @patch("requests.get")
    def test_resolve_doi_api_error(self, mock_get):
        """Test DOI resolution handles API error status codes."""
        with patch("rxiv_maker.exporters.docx_exporter.PathManager"):
            with patch("rxiv_maker.exporters.docx_exporter.ConfigManager"):
                exporter = DocxExporter("dummy_path", resolve_dois=True)

        entry = BibEntry(
            key="testkey2023",
            entry_type="article",
            fields={"title": "Test Article Title"},
        )

        # Mock API error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        doi = exporter._resolve_doi_from_metadata(entry)

        assert doi is None  # Should handle error gracefully

    def test_resolve_dois_disabled_by_default(self):
        """Test that DOI resolution is disabled by default."""
        with patch("rxiv_maker.exporters.docx_exporter.PathManager"):
            with patch("rxiv_maker.exporters.docx_exporter.ConfigManager"):
                exporter = DocxExporter("dummy_path")

        assert exporter.resolve_dois is False

    def test_resolve_dois_enabled_with_flag(self):
        """Test that DOI resolution can be enabled via flag."""
        with patch("rxiv_maker.exporters.docx_exporter.PathManager"):
            with patch("rxiv_maker.exporters.docx_exporter.ConfigManager"):
                exporter = DocxExporter("dummy_path", resolve_dois=True)

        assert exporter.resolve_dois is True
