"""DOI validator for checking DOI metadata against CrossRef API."""

import concurrent.futures
import logging
import os
import re
import time
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import requests
from crossref_commons.retrieval import get_publication_as_json

try:
    from ..utils.bibliography_checksum import get_bibliography_checksum_manager
    from ..utils.doi_cache import DOICache
    from .base_validator import (
        BaseValidator,
        ValidationError,
        ValidationLevel,
        ValidationResult,
    )
except ImportError:
    # Fallback for script execution
    from ..utils.bibliography_checksum import get_bibliography_checksum_manager
    from ..utils.doi_cache import DOICache
    from .base_validator import (
        BaseValidator,
        ValidationError,
        ValidationLevel,
        ValidationResult,
    )

logger = logging.getLogger(__name__)


class DOIValidator(BaseValidator):
    """Validator for checking DOI metadata against CrossRef API."""

    # DOI format regex from CrossRef documentation
    DOI_REGEX = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)

    def __init__(
        self,
        manuscript_path: str,
        enable_online_validation: bool = True,
        cache_dir: str | None = None,
        force_validation: bool = False,
        ignore_ci_environment: bool = False,
    ):
        """Initialize DOI validator.

        Args:
            manuscript_path: Path to manuscript directory
            enable_online_validation: Whether to perform online DOI validation
            cache_dir: Custom cache directory (default: .cache)
            force_validation: Force validation even if checksum unchanged
            ignore_ci_environment: Force validation even in CI environments (for testing)
        """
        super().__init__(manuscript_path)
        self.enable_online_validation = enable_online_validation

        # Extract manuscript name from path for cache naming
        manuscript_name = Path(manuscript_path).name

        # Initialize cache with manuscript-specific naming
        if cache_dir:
            self.cache = DOICache(cache_dir=cache_dir, manuscript_name=manuscript_name)
        else:
            self.cache = DOICache(manuscript_name=manuscript_name)

        self.similarity_threshold = 0.8  # Minimum similarity for title matching
        self.force_validation = force_validation
        self.ignore_ci_environment = ignore_ci_environment

    def _is_ci_environment(self) -> bool:
        """Check if running in a CI environment.

        Returns:
            True if running in CI, False otherwise
        """
        ci_indicators = [
            "CI",
            "CONTINUOUS_INTEGRATION",
            "GITHUB_ACTIONS",
            "GITHUB_WORKFLOW",
            "RUNNER_OS",
            "TRAVIS",
            "CIRCLECI",
            "JENKINS_URL",
            "BUILDKITE",
            "GITLAB_CI",
        ]

        return any(os.getenv(indicator) for indicator in ci_indicators)

    def validate(self) -> ValidationResult:
        """Validate DOI entries in bibliography using checksum-based caching.

        Returns:
            ValidationResult with DOI validation issues
        """
        errors = []
        metadata = {
            "total_dois": 0,
            "validated_dois": 0,
            "invalid_format": 0,
            "api_failures": 0,
            "mismatched_metadata": 0,
            "checksum_cache_used": False,
        }

        # Skip DOI validation completely in CI environments to avoid API abuse policies
        if self._is_ci_environment() and not self.ignore_ci_environment:
            logger.info("CI environment detected - skipping DOI validation to avoid API rate limits")

            # Still count DOIs for metadata but mark as validated
            bib_file = Path(self.manuscript_path) / "03_REFERENCES.bib"
            if bib_file.exists():
                bib_content = self._read_file_safely(str(bib_file))
                if bib_content:
                    entries = self._extract_bib_entries(bib_content)
                    metadata["total_dois"] = sum(1 for entry in entries if "doi" in entry)
                    metadata["validated_dois"] = metadata["total_dois"]  # Mark all as validated

                    if metadata["total_dois"] > 0:
                        errors.append(
                            self._create_error(
                                ValidationLevel.INFO,
                                f"DOI validation skipped in CI environment - {metadata['total_dois']} DOIs found",
                                error_code="DOI_CI_SKIP",
                            )
                        )

            return ValidationResult(self.name, errors, metadata)

        # Find bibliography file
        bib_file = Path(self.manuscript_path) / "03_REFERENCES.bib"
        if not bib_file.exists():
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    "No bibliography file found (03_REFERENCES.bib)",
                    error_code="DOI_NO_BIB_FILE",
                )
            )
            return ValidationResult(self.name, errors, metadata)

        # Check if validation is needed using checksum manager
        # Skip checksum optimization for temporary directories (e.g., in tests)
        manuscript_path_str = str(self.manuscript_path)
        is_temp_dir = (
            manuscript_path_str.startswith("/tmp/")
            or manuscript_path_str.startswith("/var/tmp/")
            or "/var/folders/" in manuscript_path_str  # macOS temp directories
            or "temp" in manuscript_path_str.lower()
        )

        try:
            if not is_temp_dir:
                checksum_manager = get_bibliography_checksum_manager(self.manuscript_path)

                if self.force_validation:
                    logger.info("Forcing DOI validation (ignoring checksum)")
                    checksum_manager.force_validation()
                    needs_validation = True
                else:
                    needs_validation = checksum_manager.needs_validation()

                if not needs_validation:
                    logger.info("Bibliography DOI validation is up to date (checksum unchanged)")
                    metadata["checksum_cache_used"] = True
                    # Still return basic metadata about the file
                    bib_content = self._read_file_safely(str(bib_file))
                    if bib_content:
                        entries = self._extract_bib_entries(bib_content)
                        metadata["total_dois"] = sum(1 for entry in entries if "doi" in entry)
                        metadata["validated_dois"] = metadata["total_dois"]  # Assume previously validated

                    return ValidationResult(self.name, errors, metadata)

                logger.info("Bibliography has changed, performing DOI validation")
            else:
                logger.info("Temporary directory detected, skipping checksum optimization")

        except Exception as e:
            logger.warning(f"Failed to use checksum manager for DOI validation: {e}")
            # Fall back to normal validation

        # Read bibliography file
        bib_content = self._read_file_safely(str(bib_file))
        if not bib_content:
            errors.append(
                self._create_error(
                    ValidationLevel.ERROR,
                    "Could not read bibliography file",
                    file_path=str(bib_file),
                    error_code="DOI_BIB_READ_ERROR",
                )
            )
            return ValidationResult(self.name, errors, metadata)

        # Extract bibliography entries
        entries = self._extract_bib_entries(bib_content)

        # Validate each entry with DOI
        for entry in entries:
            if "doi" in entry:
                metadata["total_dois"] += 1
                try:
                    validation_errors = self._validate_doi_entry(entry, str(bib_file))
                    errors.extend(validation_errors)
                except Exception as e:
                    # If validation fails due to an exception, create an error
                    logger.error(f"Exception validating DOI {entry.get('doi', 'unknown')}: {e}")
                    validation_errors = [
                        self._create_error(
                            ValidationLevel.WARNING,
                            f"DOI validation failed due to error: {entry.get('doi', 'unknown')}",
                            file_path=str(bib_file),
                            line_number=entry.get("line_start", 1),
                            context=f"Entry: {entry.get('key', 'unknown')}\nError: {str(e)}",
                            suggestion="Check internet connection or try again later. You can disable DOI validation with --no-doi flag.",
                            error_code="DOI_VALIDATION_ERROR",
                        )
                    ]
                    errors.extend(validation_errors)

                # Update metadata based on validation results
                if any(e.error_code == "DOI_INVALID_FORMAT" for e in validation_errors):
                    metadata["invalid_format"] += 1
                elif any(e.error_code and e.error_code.startswith("DOI_API") for e in validation_errors):
                    metadata["api_failures"] += 1
                elif any(e.error_code and e.error_code.startswith("DOI_MISMATCH") for e in validation_errors):
                    metadata["mismatched_metadata"] += 1
                else:
                    metadata["validated_dois"] += 1

        # Add summary information
        if metadata["total_dois"] > 0:
            success_rate = metadata["validated_dois"] / metadata["total_dois"] * 100
            if success_rate == 100:
                errors.append(
                    self._create_error(
                        ValidationLevel.SUCCESS,
                        f"All {metadata['total_dois']} DOIs validated successfully",
                        error_code="DOI_VALIDATION_SUCCESS",
                    )
                )
            else:
                errors.append(
                    self._create_error(
                        ValidationLevel.INFO,
                        f"DOI validation: {metadata['validated_dois']}/{metadata['total_dois']} "
                        f"({success_rate:.1f}%) successfully validated",
                        error_code="DOI_VALIDATION_SUMMARY",
                    )
                )

        # Update checksum after successful validation (skip for temp directories)
        manuscript_path_str = str(self.manuscript_path)
        is_temp_dir = (
            manuscript_path_str.startswith("/tmp/")
            or manuscript_path_str.startswith("/var/tmp/")
            or "/var/folders/" in manuscript_path_str  # macOS temp directories
            or "temp" in manuscript_path_str.lower()
        )
        if not is_temp_dir:
            try:
                checksum_manager = get_bibliography_checksum_manager(self.manuscript_path)
                # Consider validation successful if we didn't encounter major errors
                validation_successful = not any(e.level == ValidationLevel.ERROR for e in errors)
                checksum_manager.update_checksum(validation_completed=validation_successful)
                if validation_successful:
                    logger.info("Updated bibliography checksum after successful DOI validation")
                else:
                    logger.warning("DOI validation had errors, but checksum updated anyway")
            except Exception as e:
                logger.warning(f"Failed to update bibliography checksum: {e}")

        return ValidationResult(self.name, errors, metadata)

    def _extract_bib_entries(self, bib_content: str) -> list[dict[str, Any]]:
        """Extract bibliography entries from BibTeX content.

        Args:
            bib_content: BibTeX file content

        Returns:
            List of bibliography entries with metadata
        """
        entries = []

        # Pattern to match BibTeX entries
        entry_pattern = re.compile(r"@(\w+)\s*\{\s*([^,\s}]+)\s*,\s*(.*?)\n\}", re.DOTALL | re.IGNORECASE)

        for match in entry_pattern.finditer(bib_content):
            entry_type = match.group(1).lower()
            entry_key = match.group(2)
            fields_text = match.group(3)

            # Extract fields from the entry
            fields = self._extract_bib_fields(fields_text)

            entry = {
                "type": entry_type,
                "key": entry_key,
                "line_start": bib_content[: match.start()].count("\n") + 1,
                **fields,
            }

            entries.append(entry)

        return entries

    def _extract_bib_fields(self, fields_text: str) -> dict[str, str]:
        """Extract field values from BibTeX entry fields.

        Args:
            fields_text: Fields section of BibTeX entry

        Returns:
            Dictionary of field names to values
        """
        fields = {}

        # Pattern to match field = {value} or field = value
        field_pattern = re.compile(r"(\w+)\s*=\s*(?:\{([^}]*)\}|([^,\n]+))", re.IGNORECASE)

        for match in field_pattern.finditer(fields_text):
            field_name = match.group(1).lower()
            field_value = match.group(2) or match.group(3)
            if field_value:
                fields[field_name] = field_value.strip()

        return fields

    def _validate_doi_entry(self, entry: dict[str, Any], bib_file: str) -> list[ValidationError]:
        """Validate a single bibliography entry with DOI.

        Args:
            entry: Bibliography entry
            bib_file: Path to bibliography file

        Returns:
            List of validation errors for this entry
        """
        errors = []
        doi = entry["doi"]
        entry_key = entry["key"]
        line_number = entry.get("line_start", 1)

        # Validate DOI format
        if not self.DOI_REGEX.match(doi):
            errors.append(
                self._create_error(
                    ValidationLevel.ERROR,
                    f"Invalid DOI format: {doi}",
                    file_path=bib_file,
                    line_number=line_number,
                    context=f"Entry: {entry_key}",
                    suggestion="DOI should follow format: 10.xxxx/yyyy",
                    error_code="DOI_INVALID_FORMAT",
                )
            )
            return errors

        # Skip online validation if disabled
        if not self.enable_online_validation:
            return errors

        # Skip DOI resolution check as it can be unreliable due to network issues
        # Instead, focus on metadata validation through registrars

        # Try to get metadata from cache first
        cached_metadata = self.cache.get(doi)
        if cached_metadata:
            logger.debug(f"Using cached metadata for DOI: {doi}")
            metadata_source = cached_metadata.get("_source", "CrossRef")

            # Handle cached failures
            if metadata_source == "NOT_FOUND":
                registrar_info = self._identify_doi_registrar(doi)
                errors.append(
                    self._create_error(
                        ValidationLevel.WARNING,
                        f"DOI not found in available registrars: {doi}",
                        file_path=bib_file,
                        line_number=line_number,
                        context=f"Entry: {entry_key}",
                        suggestion=registrar_info + " You can disable DOI validation with --no-doi flag.",
                        error_code="DOI_NOT_FOUND",
                    )
                )
                return errors

            metadata = cached_metadata
        else:
            # Try APIs in parallel for better performance
            metadata = None
            metadata_source = None

            # Try CrossRef and DataCite in parallel
            metadata, metadata_source = self._fetch_metadata_parallel(doi)

            # If all APIs failed, cache the failure and provide helpful error message
            if not metadata:
                # Cache the failure to avoid repeated API calls
                failure_metadata = {
                    "_source": "NOT_FOUND",
                    "_error": "DOI not found in CrossRef, DataCite, or JOSS",
                    "_timestamp": time.time(),
                }
                self.cache.set(doi, failure_metadata)

                registrar_info = self._identify_doi_registrar(doi)
                errors.append(
                    self._create_error(
                        ValidationLevel.WARNING,
                        f"DOI not found in available registrars: {doi}",
                        file_path=bib_file,
                        line_number=line_number,
                        context=f"Entry: {entry_key}",
                        suggestion=registrar_info + " You can disable DOI validation with --no-doi flag.",
                        error_code="DOI_NOT_FOUND",
                    )
                )
                return errors

        # Compare metadata (handle different formats from different sources)
        if metadata and metadata_source == "DataCite":
            metadata_errors = self._compare_datacite_metadata(entry, metadata, bib_file, line_number)
        elif metadata and metadata_source == "JOSS":
            metadata_errors = self._compare_joss_metadata(entry, metadata, bib_file, line_number)
        elif metadata:
            metadata_errors = self._compare_metadata(entry, metadata, bib_file, line_number)
        else:
            metadata_errors = []
        errors.extend(metadata_errors)

        return errors

    def _fetch_metadata_parallel(self, doi: str) -> tuple[dict[str, Any] | None, str | None]:
        """Fetch metadata from CrossRef and DataCite APIs in parallel.

        Args:
            doi: DOI to fetch metadata for

        Returns:
            Tuple of (metadata, source) where source is 'CrossRef' or 'DataCite'
        """
        metadata = None
        metadata_source = None

        # Use ThreadPoolExecutor for parallel API calls
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both API calls
            crossref_future = executor.submit(self._fetch_crossref_metadata, doi)
            datacite_future = executor.submit(self._fetch_datacite_metadata, doi)

            # Wait for first successful result
            for future in concurrent.futures.as_completed([crossref_future, datacite_future]):
                try:
                    result = future.result()
                    if result:
                        if future == crossref_future:
                            metadata = result
                            metadata["_source"] = "CrossRef"
                            metadata_source = "CrossRef"
                            logger.debug(f"Found DOI in CrossRef: {doi}")
                        else:
                            metadata = result
                            metadata["_source"] = "DataCite"
                            metadata_source = "DataCite"
                            logger.debug(f"Found DOI in DataCite: {doi}")

                        # Cache the successful result
                        self.cache.set(doi, metadata)
                        break

                except Exception as e:
                    # Log the error but continue waiting for other results
                    source = "CrossRef" if future == crossref_future else "DataCite"
                    logger.debug(f"{source} failed for {doi}: {e}")

        return metadata, metadata_source

    def _verify_doi_resolution(self, doi: str) -> bool:
        """Verify that a DOI resolves by making a HEAD request to the DOI URL.

        Args:
            doi: DOI to verify

        Returns:
            True if DOI resolves, False otherwise
        """
        try:
            # Make a HEAD request to check if DOI resolves
            url = f"https://doi.org/{doi}"
            headers = {"User-Agent": "rxiv-maker/1.0 (https://github.com/paxcalpt/rxiv-maker)"}

            response = requests.head(url, headers=headers, timeout=15, allow_redirects=True)

            # Consider 2xx and 3xx status codes as successful resolution
            if response.status_code < 400:
                return True

            # If HEAD fails, try GET request as some servers don't support HEAD
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True, stream=True)

            # Close the connection immediately since we only care about status
            response.close()

            return response.status_code < 400

        except requests.exceptions.Timeout:
            logger.debug(f"DOI resolution check timed out for {doi}")
            # Don't fail validation for timeout - the DOI might still be valid
            return True
        except requests.exceptions.ConnectionError:
            logger.debug(f"DOI resolution check connection failed for {doi}")
            # Don't fail validation for connection errors - might be temporary
            return True
        except Exception as e:
            logger.debug(f"DOI resolution check failed for {doi}: {e}")
            # Don't fail validation for other errors - the DOI might still be valid
            return True

    def _fetch_joss_metadata(self, doi: str) -> dict[str, Any] | None:
        """Fetch metadata from JOSS API.

        Args:
            doi: JOSS DOI to fetch metadata for

        Returns:
            Metadata dictionary or None if not found
        """
        try:
            # Extract JOSS ID from DOI (e.g., 10.21105/joss.03021 -> 03021)
            joss_id = doi.split(".")[-1]

            # JOSS API endpoint
            url = f"https://joss.theoj.org/papers/{joss_id}.json"
            headers = {
                "Accept": "application/json",
                "User-Agent": "rxiv-maker/1.0 (https://github.com/paxcalpt/rxiv-maker)",
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Normalize JOSS response to match our expected format
                return self._normalize_joss_metadata(data)
            elif response.status_code == 404:
                return None
            else:
                response.raise_for_status()

            return None

        except Exception as e:
            logger.debug(f"Error fetching JOSS metadata for {doi}: {e}")
            raise

    def _normalize_joss_metadata(self, joss_data: dict[str, Any]) -> dict[str, Any]:
        """Normalize JOSS API response to a consistent format.

        Args:
            joss_data: JOSS API response data

        Returns:
            Normalized metadata dictionary
        """
        normalized = {
            "_source": "JOSS",
            "title": [joss_data.get("title", "")],
            "author": [],
            "published-online": None,
            "container-title": ["Journal of Open Source Software"],
            "publisher": "The Open Journal",
            "doi": joss_data.get("doi", ""),
            "volume": joss_data.get("volume"),
            "issue": joss_data.get("issue"),
            "page": joss_data.get("page"),
            "year": joss_data.get("year"),
        }

        # Convert authors to CrossRef format
        if "authors" in joss_data:
            for author in joss_data["authors"]:
                if isinstance(author, dict):
                    author_dict = {}
                    if "given_name" in author:
                        author_dict["given"] = author["given_name"]
                    if "last_name" in author:
                        author_dict["family"] = author["last_name"]
                    if author_dict:
                        normalized["author"].append(author_dict)

        # Convert publication date
        if "published_at" in joss_data:
            try:
                # Parse JOSS date format
                from datetime import datetime

                pub_date = datetime.fromisoformat(joss_data["published_at"].replace("Z", "+00:00"))
                normalized["published-online"] = {"date-parts": [[pub_date.year, pub_date.month, pub_date.day]]}
            except Exception as e:
                logger.debug(f"Error parsing JOSS publication date: {e}")

        return normalized

    def _compare_joss_metadata(
        self,
        bib_entry: dict[str, Any],
        joss_metadata: dict[str, Any],
        bib_file: str,
        line_number: int,
    ) -> list[ValidationError]:
        """Compare bibliography entry with JOSS metadata.

        Args:
            bib_entry: Bibliography entry
            joss_metadata: JOSS metadata
            bib_file: Path to bibliography file
            line_number: Line number in file

        Returns:
            List of validation errors
        """
        errors = []
        entry_key = bib_entry["key"]

        # Compare title
        if "title" in bib_entry and "title" in joss_metadata:
            title_errors = self._compare_titles(
                bib_entry["title"],
                joss_metadata["title"],
                entry_key,
                bib_file,
                line_number,
            )
            errors.extend(title_errors)

        # Compare year
        if "year" in bib_entry and "year" in joss_metadata:
            bib_year_str = str(bib_entry["year"]).strip()
            joss_year = str(joss_metadata["year"])

            if bib_year_str != joss_year:
                errors.append(
                    self._create_error(
                        ValidationLevel.WARNING,
                        "Publication year mismatch (JOSS)",
                        file_path=bib_file,
                        line_number=line_number,
                        context=f"Entry: {entry_key}\nBibliography: {bib_year_str}\nJOSS: {joss_year}",
                        suggestion="Check if the publication year is correct",
                        error_code="DOI_MISMATCH_YEAR_JOSS",
                    )
                )

        # Compare authors
        if "author" in bib_entry and "author" in joss_metadata:
            joss_authors = joss_metadata["author"]
            if joss_authors:
                # Check first author
                first_author = joss_authors[0]
                first_author_family = first_author.get("family", "")

                if first_author_family and first_author_family.lower() not in bib_entry["author"].lower():
                    errors.append(
                        self._create_error(
                            ValidationLevel.INFO,
                            "First author mismatch (JOSS)",
                            file_path=bib_file,
                            line_number=line_number,
                            context=f"Entry: {entry_key}\nBibliography: {bib_entry['author']}\nJOSS first author: {first_author_family}",
                            suggestion="Check if the first author name is correct",
                            error_code="DOI_MISMATCH_AUTHOR_JOSS",
                        )
                    )

        # Add success message for JOSS validation (only if no errors)
        if not errors:
            errors.append(
                self._create_error(
                    ValidationLevel.SUCCESS,
                    f"DOI validated successfully via JOSS: {bib_entry.get('doi', '')}",
                    error_code="DOI_JOSS_SUCCESS",
                )
            )

        return errors

    def _fetch_crossref_metadata(self, doi: str) -> dict[str, Any] | None:
        """Fetch metadata from CrossRef API.

        Args:
            doi: DOI to fetch metadata for

        Returns:
            Metadata dictionary or None if not found
        """
        try:
            # Add small delay to respect rate limits
            time.sleep(0.1)

            result = get_publication_as_json(doi)

            # crossref_commons returns the message content directly, not wrapped
            if result and isinstance(result, dict):
                return result

            return None

        except Exception as e:
            logger.debug(f"Error fetching CrossRef metadata for {doi}: {e}")
            raise

    def _fetch_datacite_metadata(self, doi: str) -> dict[str, Any] | None:
        """Fetch metadata from DataCite API.

        Args:
            doi: DOI to fetch metadata for

        Returns:
            Metadata dictionary or None if not found
        """
        try:
            # Add small delay to respect rate limits
            time.sleep(0.1)

            # DataCite REST API endpoint for public access
            url = f"https://api.datacite.org/dois/{doi}"
            headers = {
                "Accept": "application/json",
                "User-Agent": "rxiv-maker/1.0 (https://github.com/paxcalpt/rxiv-maker)",
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if "data" in data and "attributes" in data["data"]:
                    # Normalize the DataCite response to match our expected format
                    attributes = data["data"]["attributes"]
                    normalized = self._normalize_datacite_metadata(attributes)
                    return normalized
            elif response.status_code == 404:
                return None
            else:
                response.raise_for_status()

            return None

        except Exception as e:
            logger.debug(f"Error fetching DataCite metadata for {doi}: {e}")
            raise

    def _normalize_datacite_metadata(self, attributes: dict[str, Any]) -> dict[str, Any]:
        """Normalize DataCite API response to a consistent format.

        Args:
            attributes: DataCite API response attributes

        Returns:
            Normalized metadata dictionary
        """
        normalized = {
            "_source": "DataCite",
            "titles": attributes.get("titles", []),
            "creators": attributes.get("creators", []),
            "publicationYear": attributes.get("publicationYear"),
            "publisher": attributes.get("publisher"),
            "subjects": attributes.get("subjects", []),
            "types": attributes.get("types", {}),
            "url": attributes.get("url"),
            "doi": attributes.get("doi"),
            "relatedIdentifiers": attributes.get("relatedIdentifiers", []),
            "fundingReferences": attributes.get("fundingReferences", []),
        }

        # Add any additional fields that might be useful
        if "container" in attributes:
            normalized["container"] = attributes["container"]

        return normalized

    def _compare_metadata(
        self,
        bib_entry: dict[str, Any],
        crossref_metadata: dict[str, Any],
        bib_file: str,
        line_number: int,
    ) -> list[ValidationError]:
        """Compare bibliography entry with CrossRef metadata.

        Args:
            bib_entry: Bibliography entry
            crossref_metadata: CrossRef metadata
            bib_file: Path to bibliography file
            line_number: Line number in file

        Returns:
            List of validation errors
        """
        errors = []
        entry_key = bib_entry["key"]

        # Compare title
        if "title" in bib_entry and "title" in crossref_metadata:
            title_errors = self._compare_titles(
                bib_entry["title"],
                crossref_metadata["title"],
                entry_key,
                bib_file,
                line_number,
            )
            errors.extend(title_errors)

        # Compare journal
        if "journal" in bib_entry and "container-title" in crossref_metadata:
            journal_errors = self._compare_journals(
                bib_entry["journal"],
                crossref_metadata["container-title"],
                entry_key,
                bib_file,
                line_number,
            )
            errors.extend(journal_errors)

        # Compare year
        if "year" in bib_entry and "published-print" in crossref_metadata:
            year_errors = self._compare_years(
                bib_entry["year"],
                crossref_metadata["published-print"],
                entry_key,
                bib_file,
                line_number,
            )
            errors.extend(year_errors)
        elif "year" in bib_entry and "published-online" in crossref_metadata:
            year_errors = self._compare_years(
                bib_entry["year"],
                crossref_metadata["published-online"],
                entry_key,
                bib_file,
                line_number,
            )
            errors.extend(year_errors)

        # Compare authors
        if "author" in bib_entry and "author" in crossref_metadata:
            author_errors = self._compare_authors(
                bib_entry["author"],
                crossref_metadata["author"],
                entry_key,
                bib_file,
                line_number,
            )
            errors.extend(author_errors)

        return errors

    def _compare_datacite_metadata(
        self,
        bib_entry: dict[str, Any],
        datacite_metadata: dict[str, Any],
        bib_file: str,
        line_number: int,
    ) -> list[ValidationError]:
        """Compare bibliography entry with DataCite metadata.

        Args:
            bib_entry: Bibliography entry
            datacite_metadata: Normalized DataCite metadata
            bib_file: Path to bibliography file
            line_number: Line number in file

        Returns:
            List of validation errors
        """
        errors = []
        entry_key = bib_entry["key"]

        # Compare title
        if "title" in bib_entry and "titles" in datacite_metadata:
            datacite_titles = datacite_metadata["titles"]
            if datacite_titles:
                # Extract the first title from DataCite format
                first_title = datacite_titles[0]
                title_text = first_title.get("title", "") if isinstance(first_title, dict) else str(first_title)

                title_errors = self._compare_titles(bib_entry["title"], [title_text], entry_key, bib_file, line_number)
                errors.extend(title_errors)

        # Compare year
        if "year" in bib_entry and "publicationYear" in datacite_metadata:
            bib_year_str = str(bib_entry["year"]).strip()
            datacite_year = str(datacite_metadata["publicationYear"])

            if bib_year_str != datacite_year:
                errors.append(
                    self._create_error(
                        ValidationLevel.WARNING,
                        "Publication year mismatch (DataCite)",
                        file_path=bib_file,
                        line_number=line_number,
                        context=f"Entry: {entry_key}\nBibliography: {bib_year_str}\nDataCite: {datacite_year}",
                        suggestion="Check if the publication year is correct",
                        error_code="DOI_MISMATCH_YEAR_DATACITE",
                    )
                )

        # Compare authors/creators
        if "author" in bib_entry and "creators" in datacite_metadata:
            datacite_creators = datacite_metadata["creators"]
            if datacite_creators:
                # Extract first creator name
                first_creator = datacite_creators[0]
                first_author_family = None

                if isinstance(first_creator, dict):
                    # Handle different creator formats
                    first_author_family = (
                        first_creator.get("familyName") or first_creator.get("family") or first_creator.get("name")
                    )
                else:
                    first_author_family = str(first_creator)

                if first_author_family and first_author_family.lower() not in bib_entry["author"].lower():
                    errors.append(
                        self._create_error(
                            ValidationLevel.INFO,
                            "First author mismatch (DataCite)",
                            file_path=bib_file,
                            line_number=line_number,
                            context=f"Entry: {entry_key}\nBibliography: {bib_entry['author']}\nDataCite first creator: {first_author_family}",
                            suggestion="Check if the first author name is correct",
                            error_code="DOI_MISMATCH_AUTHOR_DATACITE",
                        )
                    )

        # Compare publisher (if available)
        if "publisher" in bib_entry and "publisher" in datacite_metadata:
            bib_publisher = bib_entry["publisher"].lower()
            datacite_publisher = str(datacite_metadata["publisher"]).lower()

            if bib_publisher != datacite_publisher:
                errors.append(
                    self._create_error(
                        ValidationLevel.INFO,
                        "Publisher mismatch (DataCite)",
                        file_path=bib_file,
                        line_number=line_number,
                        context=f"Entry: {entry_key}\nBibliography: {bib_entry['publisher']}\nDataCite: {datacite_metadata['publisher']}",
                        suggestion="Check if the publisher name is correct",
                        error_code="DOI_MISMATCH_PUBLISHER_DATACITE",
                    )
                )

        # Add success message for DataCite validation (only if no errors)
        if not errors:
            errors.append(
                self._create_error(
                    ValidationLevel.SUCCESS,
                    f"DOI validated successfully via DataCite: {bib_entry.get('doi', '')}",
                    error_code="DOI_DATACITE_SUCCESS",
                )
            )

        return errors

    def _compare_titles(
        self,
        bib_title: str,
        crossref_title: list[str],
        entry_key: str,
        bib_file: str,
        line_number: int,
    ) -> list[ValidationError]:
        """Compare title from bibliography with CrossRef title.

        Args:
            bib_title: Title from bibliography
            crossref_title: Title from CrossRef (list)
            entry_key: Bibliography entry key
            bib_file: Path to bibliography file
            line_number: Line number in file

        Returns:
            List of validation errors
        """
        errors: list[ValidationError] = []

        if not crossref_title:
            return errors

        # Get first title from CrossRef
        crossref_title_str = crossref_title[0] if isinstance(crossref_title, list) else str(crossref_title)

        # Clean titles for comparison
        bib_clean = self._clean_title(bib_title)
        crossref_clean = self._clean_title(crossref_title_str)

        # Calculate similarity
        similarity = SequenceMatcher(None, bib_clean, crossref_clean).ratio()

        if similarity < self.similarity_threshold:
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    f"Title mismatch (similarity: {similarity:.2f})",
                    file_path=bib_file,
                    line_number=line_number,
                    context=f"Entry: {entry_key}\nBibliography: {bib_title}\nCrossRef: {crossref_title_str}",
                    suggestion="Check if the title in the bibliography matches the published title",
                    error_code="DOI_MISMATCH_TITLE",
                )
            )

        return errors

    def _compare_journals(
        self,
        bib_journal: str,
        crossref_journal: list[str],
        entry_key: str,
        bib_file: str,
        line_number: int,
    ) -> list[ValidationError]:
        """Compare journal from bibliography with CrossRef journal.

        Args:
            bib_journal: Journal from bibliography
            crossref_journal: Journal from CrossRef (list)
            entry_key: Bibliography entry key
            bib_file: Path to bibliography file
            line_number: Line number in file

        Returns:
            List of validation errors
        """
        errors: list[ValidationError] = []

        if not crossref_journal:
            return errors

        # Get first journal from CrossRef
        crossref_journal_str = crossref_journal[0] if isinstance(crossref_journal, list) else str(crossref_journal)

        # Clean journal names for comparison
        bib_clean = self._clean_journal(bib_journal)
        crossref_clean = self._clean_journal(crossref_journal_str)

        # Calculate similarity
        similarity = SequenceMatcher(None, bib_clean, crossref_clean).ratio()

        if similarity < self.similarity_threshold:
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    f"Journal name mismatch (similarity: {similarity:.2f})",
                    file_path=bib_file,
                    line_number=line_number,
                    context=f"Entry: {entry_key}\nBibliography: {bib_journal}\nCrossRef: {crossref_journal_str}",
                    suggestion="Check if the journal name matches the published journal",
                    error_code="DOI_MISMATCH_JOURNAL",
                )
            )

        return errors

    def _compare_years(
        self,
        bib_year: str,
        crossref_date: dict[str, Any],
        entry_key: str,
        bib_file: str,
        line_number: int,
    ) -> list[ValidationError]:
        """Compare year from bibliography with CrossRef publication date.

        Args:
            bib_year: Year from bibliography
            crossref_date: Date from CrossRef
            entry_key: Bibliography entry key
            bib_file: Path to bibliography file
            line_number: Line number in file

        Returns:
            List of validation errors
        """
        errors: list[ValidationError] = []

        if not crossref_date or "date-parts" not in crossref_date:
            return errors

        # Extract year from CrossRef date
        date_parts = crossref_date["date-parts"][0]
        if not date_parts:
            return errors

        crossref_year = str(date_parts[0])
        bib_year_str = str(bib_year).strip()

        if bib_year_str != crossref_year:
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    "Publication year mismatch",
                    file_path=bib_file,
                    line_number=line_number,
                    context=f"Entry: {entry_key}\nBibliography: {bib_year_str}\nCrossRef: {crossref_year}",
                    suggestion="Check if the publication year is correct",
                    error_code="DOI_MISMATCH_YEAR",
                )
            )

        return errors

    def _compare_authors(
        self,
        bib_author: str,
        crossref_authors: list[dict[str, Any]],
        entry_key: str,
        bib_file: str,
        line_number: int,
    ) -> list[ValidationError]:
        """Compare authors from bibliography with CrossRef authors.

        Args:
            bib_author: Author string from bibliography
            crossref_authors: Authors from CrossRef
            entry_key: Bibliography entry key
            bib_file: Path to bibliography file
            line_number: Line number in file

        Returns:
            List of validation errors
        """
        errors: list[ValidationError] = []

        if not crossref_authors:
            return errors

        # Extract author names from CrossRef
        crossref_names = []
        for author in crossref_authors:
            if "family" in author and "given" in author:
                crossref_names.append(f"{author['family']}, {author['given']}")
            elif "family" in author:
                crossref_names.append(author["family"])

        # Simple check: see if first author family name is in bibliography
        if crossref_names:
            first_author_family = crossref_authors[0].get("family", "")
            if first_author_family and first_author_family.lower() not in bib_author.lower():
                errors.append(
                    self._create_error(
                        ValidationLevel.INFO,
                        "First author mismatch",
                        file_path=bib_file,
                        line_number=line_number,
                        context=f"Entry: {entry_key}\nBibliography: {bib_author}\nCrossRef first author: {first_author_family}",
                        suggestion="Check if the first author name is correct",
                        error_code="DOI_MISMATCH_AUTHOR",
                    )
                )

        return errors

    def _clean_title(self, title: str) -> str:
        """Clean title for comparison.

        Args:
            title: Title to clean

        Returns:
            Cleaned title
        """
        # Remove LaTeX commands and special characters
        title = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", title)
        title = re.sub(r"[{}\\]", "", title)
        title = re.sub(r"\s+", " ", title)
        return title.strip().lower()

    def _clean_journal(self, journal: str) -> str:
        """Clean journal name for comparison.

        Args:
            journal: Journal name to clean

        Returns:
            Cleaned journal name
        """
        # Remove LaTeX commands and special characters
        # First handle commands with empty braces: \command{} -> command
        journal = re.sub(r"\\([a-zA-Z]+)\{\}", r"\1", journal)
        # Then handle commands with content: \command{content} -> content
        journal = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", journal)
        # Remove remaining special characters
        journal = re.sub(r"[{}\\&]", "", journal)
        journal = re.sub(r"\s+", " ", journal)
        return journal.strip().lower()

    def _identify_doi_registrar(self, doi: str) -> str:
        """Identify DOI registrar and provide helpful information.

        Args:
            doi: DOI string

        Returns:
            Information about the DOI registrar and validation alternatives
        """
        # Common DOI prefix patterns for different registrars
        if doi.startswith("10.21105/joss."):
            return (
                "This is a JOSS (Journal of Open Source Software) DOI. JOSS DOIs are indexed in CrossRef. "
                "Check internet connection or verify the DOI is correct."
            )
        elif doi.startswith("10.5281/zenodo"):
            return "This is a Zenodo DOI (DataCite registrar). Verify the DOI resolves at https://doi.org/" + doi
        elif doi.startswith("10.1101/"):
            return (
                "This is a bioRxiv/medRxiv preprint DOI. These may not be indexed in CrossRef depending on publication status. "
                "Check if the preprint exists at the respective platform."
            )
        elif doi.startswith("10.48550/arXiv") or "arxiv" in doi.lower():
            return (
                "This is an arXiv DOI. arXiv papers may not be indexed in CrossRef. "
                "Verify the paper exists on arXiv.org."
            )
        elif doi.startswith("10.6084/m9.figshare"):
            return "This is a Figshare DOI (DataCite registrar). Verify the DOI resolves at https://doi.org/" + doi
        elif doi.startswith("10.5194/"):
            return (
                "This is a Copernicus Publications DOI. Some may not be in CrossRef depending on the journal. "
                "Check if the publication exists on the publisher's website."
            )
        elif doi.startswith("10.1038/"):
            return (
                "This is a Nature Publishing Group DOI. It should be in CrossRef if published. "
                "Check internet connection or verify the DOI is correct."
            )
        elif doi.startswith("10.31219/osf.io"):
            return (
                "This is an OSF (Open Science Framework) preprint DOI. These are indexed by DataCite. "
                "Check if the preprint exists at https://osf.io/preprints/"
            )
        elif doi.startswith("10.12688/f1000research"):
            return (
                "This is an F1000Research DOI. These should be indexed by CrossRef. "
                "Check internet connection or verify the DOI is correct."
            )
        elif any(prefix in doi for prefix in ["10.1016/", "10.1371/", "10.1126/", "10.1073/", "10.1109/"]):
            return (
                "This is from a major publisher and should be in CrossRef if published. "
                "Check internet connection, verify the DOI is correct, or try again later."
            )
        else:
            return (
                "This DOI may be from a specialized registrar. We checked CrossRef, DataCite, and JOSS. "
                "Verify the DOI resolves at https://doi.org/" + doi
            )

    def _get_api_error_suggestion(self, error_message: str, registrar_info: str) -> str:
        """Get appropriate suggestion based on API error and DOI type.

        Args:
            error_message: The exception message
            registrar_info: Information about the DOI registrar

        Returns:
            Helpful suggestion for the user
        """
        error_lower = error_message.lower()

        if "does not exist" in error_lower or "not found" in error_lower:
            return registrar_info
        elif "timeout" in error_lower or "connection" in error_lower:
            return (
                "Network connectivity issue. Check internet connection and try again. "
                + "If the problem persists: "
                + registrar_info
            )
        elif "rate limit" in error_lower or "too many requests" in error_lower:
            return (
                "CrossRef API rate limit exceeded. Wait a moment and try again. "
                + "If this persists: "
                + registrar_info
            )
        else:
            return (
                "CrossRef API error. "
                + registrar_info
                + " "
                + "You can also disable DOI validation with --no-doi flag."
            )
