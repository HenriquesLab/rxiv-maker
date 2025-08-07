"""API clients for different DOI metadata providers."""

import logging
import time
from typing import Any

import requests
from crossref_commons.retrieval import get_publication_as_json

logger = logging.getLogger(__name__)


class BaseDOIClient:
    """Base class for DOI API clients."""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "rxiv-maker/1.0 (https://github.com/henriqueslab/rxiv-maker)"})

    def _make_request(self, url: str, headers: dict = None) -> dict[str, Any] | None:
        """Make HTTP request with retry logic."""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, headers=headers or {}, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                logger.debug(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    logger.error(f"All attempts failed for {url}: {e}")
                    return None
        return None


class CrossRefClient(BaseDOIClient):
    """Client for CrossRef API."""

    def fetch_metadata(self, doi: str) -> dict[str, Any] | None:
        """Fetch metadata from CrossRef API."""
        try:
            # Use crossref-commons library which handles rate limiting
            data = get_publication_as_json(doi)
            if data and "message" in data:
                return data["message"]
            return None
        except Exception as e:
            logger.debug(f"CrossRef fetch failed for {doi}: {e}")
            return None


class DataCiteClient(BaseDOIClient):
    """Client for DataCite API."""

    def fetch_metadata(self, doi: str) -> dict[str, Any] | None:
        """Fetch metadata from DataCite API."""
        try:
            url = f"https://api.datacite.org/dois/{doi}"
            headers = {"Accept": "application/json"}

            response_data = self._make_request(url, headers)

            if response_data and "data" in response_data:
                return response_data["data"]["attributes"]
            return None

        except Exception as e:
            logger.debug(f"DataCite fetch failed for {doi}: {e}")
            return None

    def normalize_metadata(self, attributes: dict[str, Any]) -> dict[str, Any]:
        """Normalize DataCite metadata to common format."""
        normalized = {}

        # Extract title
        titles = attributes.get("titles", [])
        if titles:
            normalized["title"] = titles[0].get("title", "")

        # Extract authors
        creators = attributes.get("creators", [])
        authors = []
        for creator in creators:
            if "name" in creator:
                authors.append({"family": creator["name"], "given": ""})
            elif "givenName" in creator and "familyName" in creator:
                authors.append({"family": creator["familyName"], "given": creator["givenName"]})
        normalized["author"] = authors

        # Extract year
        publication_year = attributes.get("publicationYear")
        if publication_year:
            normalized["year"] = str(publication_year)

        # Extract publisher
        publisher = attributes.get("publisher")
        if publisher:
            normalized["publisher"] = publisher

        # Extract DOI
        doi = attributes.get("doi")
        if doi:
            normalized["DOI"] = doi

        return normalized


class JOSSClient(BaseDOIClient):
    """Client for JOSS (Journal of Open Source Software) API."""

    def fetch_metadata(self, doi: str) -> dict[str, Any] | None:
        """Fetch metadata from JOSS API."""
        try:
            # Extract paper ID from JOSS DOI
            paper_id = self._extract_joss_paper_id(doi)
            if not paper_id:
                return None

            url = f"https://joss.theoj.org/papers/{paper_id}.json"
            return self._make_request(url)

        except Exception as e:
            logger.debug(f"JOSS fetch failed for {doi}: {e}")
            return None

    def _extract_joss_paper_id(self, doi: str) -> str | None:
        """Extract JOSS paper ID from DOI."""
        # JOSS DOIs typically look like: 10.21105/joss.01234
        if "10.21105/joss." in doi:
            return doi.split("10.21105/joss.")[1]
        return None

    def normalize_metadata(self, joss_data: dict[str, Any]) -> dict[str, Any]:
        """Normalize JOSS metadata to common format."""
        normalized = {}

        # Extract title
        title = joss_data.get("title")
        if title:
            normalized["title"] = title

        # Extract authors
        authors = joss_data.get("authors", [])
        normalized_authors = []
        for author in authors:
            given_name = author.get("given_name", "")
            last_name = author.get("last_name", "")
            normalized_authors.append({"family": last_name, "given": given_name})
        normalized["author"] = normalized_authors

        # Extract year
        published_at = joss_data.get("published_at")
        if published_at:
            # Extract year from date string like "2021-08-26"
            try:
                year = published_at.split("-")[0]
                normalized["year"] = year
            except (IndexError, ValueError):
                pass

        # Extract journal info
        normalized["journal"] = "Journal of Open Source Software"

        # Extract DOI
        doi = joss_data.get("doi")
        if doi:
            normalized["DOI"] = doi

        return normalized


class DOIResolver(BaseDOIClient):
    """Client for verifying DOI resolution."""

    def verify_resolution(self, doi: str) -> bool:
        """Verify that a DOI resolves correctly."""
        try:
            url = f"https://doi.org/{doi}"
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"DOI resolution failed for {doi}: {e}")
            return False
