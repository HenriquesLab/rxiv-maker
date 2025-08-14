"""API clients for different DOI metadata providers."""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

import requests
from crossref_commons.retrieval import get_publication_as_json

try:
    from ...utils.retry import RetryableSession, RetryStrategy
except ImportError:
    # Fallback when retry module isn't available
    RetryableSession = None  # type: ignore
    RetryStrategy = None  # type: ignore

logger = logging.getLogger(__name__)


class BaseDOIClient(ABC):
    """Base class for DOI API clients."""

    def __init__(self, timeout: int = 10, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries

        # Use enhanced RetryableSession if available, fallback to basic session
        if RetryableSession is not None:
            self.session = RetryableSession(
                max_attempts=max_retries,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                base_delay=1.0,
                max_delay=30.0,
                timeout=timeout,
                user_agent="rxiv-maker/1.0 (https://github.com/henriqueslab/rxiv-maker)",
            )
            self._use_retryable_session = True
        else:
            self.session = requests.Session()
            self.session.headers.update({"User-Agent": "rxiv-maker/1.0 (https://github.com/henriqueslab/rxiv-maker)"})
            self._use_retryable_session = False

    def _make_request(self, url: str, headers: dict[str, str] | None = None) -> dict[str, Any] | None:
        """Make HTTP request with retry logic."""
        if self._use_retryable_session:
            # Use RetryableSession's built-in retry logic
            try:
                response = self.session.get(url, headers=headers or {})
                return response.json()
            except Exception as e:
                logger.debug(f"RetryableSession request failed for {url}: {e}")
                return None
        else:
            # Fallback to old retry logic
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
                        logger.debug(f"All attempts failed for {url}: {e}")
                        return None
            return None

    @abstractmethod
    def fetch_metadata(self, doi: str) -> dict[str, Any] | None:
        """Fetch metadata for the given DOI."""
        pass


class CrossRefClient(BaseDOIClient):
    """Client for CrossRef API."""

    def fetch_metadata(self, doi: str) -> dict[str, Any] | None:
        """Fetch metadata from CrossRef API."""
        # Primary attempt: crossref-commons helper (handles polite pool / rate limiting)
        try:
            data = get_publication_as_json(doi)
            if data and isinstance(data, dict) and "message" in data:
                return data["message"]
        except Exception as e:
            logger.debug(f"CrossRef (library) fetch failed for {doi}: {e}")

        # Fallback: direct REST API call (sometimes library helper can fail silently for some DOIs)
        try:
            url = f"https://api.crossref.org/works/{doi}"
            headers = {"Accept": "application/json"}

            if self._use_retryable_session:
                # Use RetryableSession for enhanced retry logic
                resp = self.session.get(url, headers=headers)
                json_data = resp.json()
                if isinstance(json_data, dict) and "message" in json_data:
                    return json_data["message"]
                logger.debug(f"CrossRef REST response missing 'message' field for {doi}")
            else:
                # Fallback to old logic
                resp = self.session.get(url, headers=headers, timeout=self.timeout)
                if resp.status_code == 200:
                    json_data = resp.json()
                    if isinstance(json_data, dict) and "message" in json_data:
                        return json_data["message"]
                    logger.debug(f"CrossRef REST response missing 'message' field for {doi}")
                else:
                    logger.debug(f"CrossRef REST fetch non-200 ({resp.status_code}) for {doi}")
        except Exception as e:
            logger.debug(f"CrossRef REST fetch failed for {doi}: {e}")

        # If both attempts failed, log at debug level to avoid confusing users
        logger.debug(f"All CrossRef metadata fetch attempts failed for {doi} - trying other sources")
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


class DOIResolver:
    """Comprehensive DOI resolver with fallback API support.

    This resolver attempts to fetch DOI metadata from multiple sources in sequence:
    CrossRef -> DataCite -> OpenAlex -> Semantic Scholar -> Handle System -> JOSS
    """

    def __init__(
        self,
        cache=None,
        timeout: int = 10,
        max_retries: int = 3,
        enable_crossref: bool = True,
        enable_datacite: bool = True,
        enable_openalex: bool = True,
        enable_semantic_scholar: bool = True,
        enable_handle_system: bool = True,
        enable_joss: bool = True,
    ):
        """Initialize DOI resolver with fallback API configuration.

        Args:
            cache: Optional cache for storing results
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            enable_crossref: Enable CrossRef API
            enable_datacite: Enable DataCite API
            enable_openalex: Enable OpenAlex API
            enable_semantic_scholar: Enable Semantic Scholar API
            enable_handle_system: Enable Handle System API
            enable_joss: Enable JOSS API
        """
        self.cache = cache
        self.timeout = timeout
        self.max_retries = max_retries

        # Initialize API clients based on configuration
        self.crossref_client = CrossRefClient(timeout=timeout, max_retries=max_retries) if enable_crossref else None
        self.datacite_client = DataCiteClient(timeout=timeout, max_retries=max_retries) if enable_datacite else None
        self.openalex_client = OpenAlexClient(timeout=timeout, max_retries=max_retries) if enable_openalex else None
        self.semantic_scholar_client = (
            SemanticScholarClient(timeout=timeout, max_retries=max_retries) if enable_semantic_scholar else None
        )
        self.handle_system_client = (
            HandleSystemClient(timeout=timeout, max_retries=max_retries) if enable_handle_system else None
        )
        self.joss_client = JOSSClient(timeout=timeout, max_retries=max_retries) if enable_joss else None

    def resolve(self, doi: str) -> dict[str, Any] | None:
        """Resolve DOI using fallback API chain.

        Returns:
            Dictionary with 'source' and 'metadata' keys, or None if all APIs fail
        """
        # Define API chain in order of preference
        api_chain = [
            ("crossref", self.crossref_client),
            ("datacite", self.datacite_client),
            ("openalex", self.openalex_client),
            ("semantic_scholar", self.semantic_scholar_client),
            ("handle_system", self.handle_system_client),
            ("joss", self.joss_client),
        ]

        # Try each API in sequence
        for source_name, client in api_chain:
            if client is None:
                continue

            try:
                logger.debug(f"Attempting DOI resolution for {doi} using {source_name}")
                metadata = client.fetch_metadata(doi)

                if metadata is not None:
                    logger.debug(f"Successfully resolved {doi} using {source_name}")
                    return {"source": source_name, "metadata": metadata}
                else:
                    logger.debug(f"{source_name} returned no metadata for {doi}")

            except Exception as e:
                logger.debug(f"{source_name} API failed for {doi}: {e}")
                continue

        logger.debug(f"All APIs failed to resolve {doi}")
        return None

    def verify_resolution(self, doi: str) -> bool:
        """Verify that a DOI resolves correctly using any available API."""
        result = self.resolve(doi)
        return result is not None


class OpenAlexClient(BaseDOIClient):
    """Client for OpenAlex API - comprehensive academic database."""

    def fetch_metadata(self, doi: str) -> dict[str, Any] | None:
        """Fetch metadata from OpenAlex API."""
        try:
            # OpenAlex accepts DOI with or without doi: prefix
            clean_doi = doi.replace("doi:", "")
            url = f"https://api.openalex.org/works/doi:{clean_doi}"

            response_data = self._make_request(url)

            if response_data:
                return response_data
            return None

        except Exception as e:
            logger.debug(f"OpenAlex fetch failed for {doi}: {e}")
            return None

    def normalize_metadata(self, openalex_data: dict[str, Any]) -> dict[str, Any]:
        """Normalize OpenAlex metadata to common format."""
        normalized = {}

        # Extract title
        title = openalex_data.get("title")
        if title:
            normalized["title"] = title.strip()

        # Extract authors
        authorships = openalex_data.get("authorships", [])
        authors = []
        for authorship in authorships:
            author_info = authorship.get("author", {})
            display_name = author_info.get("display_name", "")
            if display_name:
                # Split display name into given and family names (basic approach)
                name_parts = display_name.split()
                if len(name_parts) > 1:
                    given_name = " ".join(name_parts[:-1])
                    family_name = name_parts[-1]
                else:
                    given_name = ""
                    family_name = display_name
                authors.append({"family": family_name, "given": given_name})
        normalized["author"] = authors

        # Extract year
        publication_year = openalex_data.get("publication_year")
        if publication_year:
            normalized["year"] = str(publication_year)

        # Extract journal/venue
        primary_location = openalex_data.get("primary_location", {})
        source = primary_location.get("source", {})
        journal_name = source.get("display_name")
        if journal_name:
            normalized["journal"] = journal_name

        # Extract publisher
        host_organization = openalex_data.get("host_organization")
        if host_organization and host_organization.get("display_name"):
            normalized["publisher"] = host_organization["display_name"]

        # Extract DOI
        doi_url = openalex_data.get("doi")
        if doi_url and doi_url.startswith("https://doi.org/"):
            normalized["DOI"] = doi_url.replace("https://doi.org/", "")

        return normalized


class SemanticScholarClient(BaseDOIClient):
    """Client for Semantic Scholar API - AI-powered research database."""

    def fetch_metadata(self, doi: str) -> dict[str, Any] | None:
        """Fetch metadata from Semantic Scholar API."""
        try:
            # Semantic Scholar accepts DOI without prefix
            clean_doi = doi.replace("doi:", "")
            url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{clean_doi}"

            # Semantic Scholar API requires specific fields to be requested
            params = {"fields": "title,authors,year,journal,doi,venue,publicationDate,publisher"}

            if self._use_retryable_session:
                # Use RetryableSession for enhanced retry logic
                try:
                    response = self.session.get(url, params=params)
                    return response.json()
                except Exception as e:
                    # Special handling for rate limiting in Semantic Scholar
                    if hasattr(e, "response") and e.response and e.response.status_code == 429:
                        logger.debug(f"Semantic Scholar rate limited for {doi}")
                    else:
                        logger.debug(f"Semantic Scholar request failed for {doi}: {e}")
                    return None
            else:
                # Fallback to old retry logic
                for attempt in range(self.max_retries):
                    try:
                        response = self.session.get(url, params=params, timeout=self.timeout)
                        if response.status_code == 200:
                            return response.json()
                        elif response.status_code == 429:  # Rate limited
                            logger.debug(f"Semantic Scholar rate limited for {doi}, attempt {attempt + 1}")
                            if attempt < self.max_retries - 1:
                                time.sleep(2**attempt)
                            continue
                        else:
                            logger.debug(f"Semantic Scholar returned {response.status_code} for {doi}")
                            return None
                    except requests.RequestException as e:
                        logger.debug(f"Semantic Scholar request failed for {doi}, attempt {attempt + 1}: {e}")
                        if attempt < self.max_retries - 1:
                            time.sleep(2**attempt)
                        else:
                            return None

                return None

        except Exception as e:
            logger.debug(f"Semantic Scholar fetch failed for {doi}: {e}")
            return None

    def normalize_metadata(self, ss_data: dict[str, Any]) -> dict[str, Any]:
        """Normalize Semantic Scholar metadata to common format."""
        normalized = {}

        # Extract title
        title = ss_data.get("title")
        if title:
            normalized["title"] = title.strip()

        # Extract authors
        authors_list = ss_data.get("authors", [])
        authors = []
        for author in authors_list:
            name = author.get("name", "")
            if name:
                # Basic name splitting (Semantic Scholar usually provides full names)
                name_parts = name.split()
                if len(name_parts) > 1:
                    given_name = " ".join(name_parts[:-1])
                    family_name = name_parts[-1]
                else:
                    given_name = ""
                    family_name = name
                authors.append({"family": family_name, "given": given_name})
        normalized["author"] = authors

        # Extract year
        year = ss_data.get("year")
        if year:
            normalized["year"] = str(year)

        # Extract journal/venue
        venue = ss_data.get("venue") or ss_data.get("journal", {}).get("name")
        if venue:
            normalized["journal"] = venue

        # Extract publisher (if available)
        journal_info = ss_data.get("journal", {})
        publisher = journal_info.get("publisher")
        if publisher:
            normalized["publisher"] = publisher

        # Extract DOI
        doi = ss_data.get("doi")
        if doi:
            normalized["DOI"] = doi

        return normalized


class HandleSystemClient(BaseDOIClient):
    """Client for Handle System direct resolution - the underlying DOI infrastructure."""

    def __init__(self, timeout: int = 15, max_retries: int = 3):
        # Handle System may need longer timeouts
        super().__init__(timeout=timeout, max_retries=max_retries)

    def fetch_metadata(self, doi: str) -> dict[str, Any] | None:
        """Fetch basic resolution metadata from Handle System."""
        try:
            # Handle System API endpoint
            clean_doi = doi.replace("doi:", "")
            url = f"https://hdl.handle.net/api/handles/{clean_doi}"

            headers = {"Accept": "application/json"}
            response_data = self._make_request(url, headers)

            if response_data and "values" in response_data:
                return response_data
            return None

        except Exception as e:
            logger.debug(f"Handle System fetch failed for {doi}: {e}")
            return None

    def normalize_metadata(self, handle_data: dict[str, Any]) -> dict[str, Any]:
        """Normalize Handle System metadata to common format."""
        normalized = {}

        # Handle System provides basic resolution info, not bibliographic metadata
        # We mainly use this for verification that the DOI exists and resolves
        values = handle_data.get("values", [])

        for value in values:
            if value.get("type") == "URL":
                url_value = value.get("data", {}).get("value")
                if url_value:
                    normalized["resolved_url"] = url_value
                    break

        # Extract DOI from handle if available
        handle = handle_data.get("handle")
        if handle:
            normalized["DOI"] = handle

        # Mark this as Handle System resolved for identification
        normalized["_source"] = "handle_system"
        normalized["_resolved"] = True

        return normalized

    def verify_resolution(self, doi: str) -> bool:
        """Verify DOI resolution via Handle System."""
        metadata = self.fetch_metadata(doi)
        return metadata is not None and metadata.get("values") is not None
