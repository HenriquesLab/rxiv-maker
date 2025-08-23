"""Refactored DOI validator with improved maintainability."""

import concurrent.futures
import logging
import os
import re
from pathlib import Path
from typing import Any, List, Tuple

from ..core.error_codes import ErrorCode, create_validation_error
from .base_validator import (
    BaseValidator,
    ValidationError,
    ValidationResult,
)
from .doi import (
    BaseDOIClient,
    CrossRefClient,
    DataCiteClient,
    DOIResolver,
    HandleSystemClient,
    JOSSClient,
    MetadataComparator,
    OpenAlexClient,
    SemanticScholarClient,
)

try:
    from rxiv_maker.core.cache.bibliography_cache import get_bibliography_cache
    from rxiv_maker.core.cache.doi_cache import DOICache

    from ..utils.bibliography_checksum import get_bibliography_checksum_manager
except ImportError:
    # Fallback for script execution
    from rxiv_maker.core.cache.bibliography_cache import get_bibliography_cache
    from rxiv_maker.core.cache.doi_cache import DOICache

    from ..utils.bibliography_checksum import get_bibliography_checksum_manager

logger = logging.getLogger(__name__)


class DOIValidator(BaseValidator):
    """Refactored DOI validator with improved maintainability."""

    # DOI format regex from CrossRef documentation
    DOI_REGEX = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)

    def __init__(
        self,
        manuscript_path: str,
        enable_online_validation: bool = True,
        cache_dir: str | None = None,
        force_validation: bool = False,
        ignore_ci_environment: bool = False,
        max_workers: int = 4,
        similarity_threshold: float = 0.8,
        enable_fallback_apis: bool = True,
        enable_openalex: bool = True,
        enable_semantic_scholar: bool = True,
        enable_handle_system: bool = True,
        fallback_timeout: int = 10,
        enable_performance_optimizations: bool = True,
    ):
        """Initialize DOI validator.

        Args:
            manuscript_path: Path to manuscript directory
            enable_online_validation: Whether to perform online DOI validation
            cache_dir: Directory for caching DOI metadata
            force_validation: Force validation even in CI environments
            ignore_ci_environment: Ignore CI environment detection
            max_workers: Maximum number of parallel workers for DOI validation
            similarity_threshold: Minimum similarity threshold for metadata comparison
            enable_fallback_apis: Whether to use fallback APIs when primary APIs fail
            enable_openalex: Whether to enable OpenAlex as a fallback API
            enable_semantic_scholar: Whether to enable Semantic Scholar as a fallback API
            enable_handle_system: Whether to enable Handle System as a fallback resolver
            fallback_timeout: Timeout in seconds for fallback API requests
            enable_performance_optimizations: Whether to enable parallel file processing and other optimizations
        """
        super().__init__(manuscript_path)

        self.enable_online_validation = enable_online_validation
        self.force_validation = force_validation
        self.ignore_ci_environment = ignore_ci_environment
        self.max_workers = max_workers
        self.enable_performance_optimizations = enable_performance_optimizations

        # Fallback configuration
        self.enable_fallback_apis = enable_fallback_apis
        self.enable_openalex = enable_openalex
        self.enable_semantic_scholar = enable_semantic_scholar
        self.enable_handle_system = enable_handle_system
        self.fallback_timeout = fallback_timeout

        # Initialize cache with error handling for temporary directories
        try:
            # Use standardized cache directory if not explicitly provided
            self.cache = DOICache(cache_dir)
        except Exception as cache_error:
            logger.warning(f"Failed to initialize DOI cache: {cache_error}. Using memory-only cache.")
            # Create a temporary cache directory as fallback
            import tempfile

            temp_cache_dir = tempfile.mkdtemp(prefix="rxiv_doi_cache_")
            self.cache = DOICache(temp_cache_dir)

        # Initialize API clients
        self.crossref_client = CrossRefClient()
        self.datacite_client = DataCiteClient()
        self.joss_client = JOSSClient()
        self.doi_resolver = DOIResolver(cache=self.cache)

        # Initialize fallback API clients with configuration
        if self.enable_fallback_apis:
            self.openalex_client = OpenAlexClient(timeout=self.fallback_timeout) if self.enable_openalex else None
            self.semantic_scholar_client = (
                SemanticScholarClient(timeout=self.fallback_timeout) if self.enable_semantic_scholar else None
            )
            self.handle_system_client = (
                HandleSystemClient(timeout=self.fallback_timeout) if self.enable_handle_system else None
            )
        else:
            self.openalex_client = None
            self.semantic_scholar_client = None
            self.handle_system_client = None

        # Initialize metadata comparator
        self.comparator = MetadataComparator(similarity_threshold=similarity_threshold)

        # Store similarity threshold for backward compatibility
        self.similarity_threshold = similarity_threshold

        # Initialize bibliography checksum manager
        self.checksum_manager = get_bibliography_checksum_manager(self.manuscript_path)

        # Initialize advanced bibliography cache
        self.bib_cache = get_bibliography_cache(Path(manuscript_path).name)

    def _is_ci_environment(self) -> bool:
        """Check if running in CI environment."""
        if self.ignore_ci_environment:
            return False

        ci_indicators = [
            "CI",
            "CONTINUOUS_INTEGRATION",
            "GITHUB_ACTIONS",
            "TRAVIS",
            "CIRCLECI",
            "JENKINS_URL",
            "BUILDKITE",
        ]
        return any(os.environ.get(indicator) for indicator in ci_indicators)

    def _check_network_connectivity(self) -> bool:
        """Check if network connectivity is available for DOI validation."""
        try:
            # Try a quick HEAD request to a reliable service with short timeout
            import requests

            response = requests.head("https://httpbin.org/status/200", timeout=3)
            return response.status_code == 200
        except Exception:
            # Try an alternative service
            try:
                response = requests.head("https://doi.org", timeout=3)
                return response.status_code in [200, 301, 302]
            except Exception:
                logger.debug("Network connectivity check failed")
                return False

    def validate(self) -> ValidationResult:
        """Validate DOIs in bibliography files."""
        errors = []
        metadata = {
            "total_dois": 0,
            "validated_dois": 0,
            "invalid_format": 0,
            "api_failures": 0,
            "successful_validations": 0,
        }

        # Disable online validation in CI unless forced, but still do format validation
        if self._is_ci_environment() and not self.force_validation:
            logger.info("Disabling online DOI validation in CI environment (use --force-validation to override)")
            self.enable_online_validation = False

        # Check network connectivity before attempting online validation
        if self.enable_online_validation and not self._check_network_connectivity():
            logger.warning("Network connectivity unavailable, skipping online DOI validation")
            self.enable_online_validation = False

        if not self.enable_online_validation:
            logger.info("Online DOI validation is disabled")
            # Still validate DOI format even when online validation is disabled
            bib_files = list(Path(self.manuscript_path).glob("*.bib"))
            if not bib_files:
                logger.warning("No .bib files found")
                from .base_validator import ValidationError, ValidationLevel

                errors.append(
                    ValidationError(
                        level=ValidationLevel.WARNING,
                        message="No bibliography files found in manuscript directory",
                        file_path=str(Path(self.manuscript_path)),
                    )
                )
                return ValidationResult(self.name, errors, metadata)
            for bib_file in bib_files:
                try:
                    file_errors, file_metadata = self._validate_bib_file_format_only(bib_file)
                    errors.extend(file_errors)
                    # Merge metadata
                    for key in metadata:
                        if key in file_metadata:
                            metadata[key] += file_metadata[key]
                except Exception as e:
                    logger.error(f"Failed to process {bib_file}: {e}")
                    errors.append(
                        create_validation_error(
                            ErrorCode.BIB_PROCESSING_ERROR,
                            f"Failed to process bibliography file: {e}",
                            file_path=str(bib_file),
                        )
                    )
                    metadata["api_failures"] += 1
            return ValidationResult(self.name, errors, metadata)

        # Find bibliography files
        bib_files = list(Path(self.manuscript_path).glob("*.bib"))
        if not bib_files:
            logger.warning("No .bib files found")
            from .base_validator import ValidationError, ValidationLevel

            errors.append(
                ValidationError(
                    level=ValidationLevel.WARNING,
                    message="No bibliography files found in manuscript directory",
                    file_path=str(Path(self.manuscript_path)),
                )
            )
            return ValidationResult(self.name, errors, metadata)

        # Process bibliography files in parallel for better performance (if optimizations enabled)
        if len(bib_files) > 1 and self.enable_performance_optimizations:
            logger.info(f"Processing {len(bib_files)} bibliography files in parallel")
            # Use parallel processing for multiple files
            file_workers = min(len(bib_files), self.max_workers)
            with concurrent.futures.ThreadPoolExecutor(max_workers=file_workers) as file_executor:
                future_to_file = {
                    file_executor.submit(self._validate_bib_file_safe, bib_file): bib_file for bib_file in bib_files
                }

                for future in concurrent.futures.as_completed(future_to_file):
                    bib_file = future_to_file[future]
                    try:
                        file_errors, file_metadata = future.result()
                        errors.extend(file_errors)
                        # Merge metadata
                        for key in metadata:
                            if key in file_metadata:
                                metadata[key] += file_metadata[key]
                    except Exception as e:
                        logger.error(f"Failed to process {bib_file}: {e}")
                        errors.append(
                            create_validation_error(
                                ErrorCode.BIB_PROCESSING_ERROR,
                                f"Failed to process bibliography file: {e}",
                                file_path=str(bib_file),
                            )
                        )
                        metadata["api_failures"] += 1
        else:
            # Single file - use existing sequential processing
            for bib_file in bib_files:
                try:
                    file_errors, file_metadata = self._validate_bib_file(bib_file)
                    errors.extend(file_errors)
                    # Merge metadata
                    for key in metadata:
                        if key in file_metadata:
                            metadata[key] += file_metadata[key]
                except Exception as e:
                    logger.error(f"Failed to process {bib_file}: {e}")
                    errors.append(
                        create_validation_error(
                            ErrorCode.BIB_PROCESSING_ERROR,
                            f"Failed to process bibliography file: {e}",
                            file_path=str(bib_file),
                        )
                    )
                    metadata["api_failures"] += 1

        return ValidationResult(self.name, errors, metadata)

    def _validate_bib_file_safe(self, bib_file: Path) -> tuple[list[ValidationError], dict]:
        """Thread-safe wrapper for bibliography file validation.

        This method provides exception safety for parallel file processing.
        """
        try:
            return self._validate_bib_file(bib_file)
        except Exception as e:
            logger.error(f"Exception in parallel processing of {bib_file}: {e}")
            error = create_validation_error(
                ErrorCode.BIB_PROCESSING_ERROR,
                f"Failed to process bibliography file during parallel validation: {e}",
                file_path=str(bib_file),
            )
            metadata = {
                "total_dois": 0,
                "validated_dois": 0,
                "invalid_format": 0,
                "api_failures": 1,
                "successful_validations": 0,
            }
            return [error], metadata

    def _validate_bib_file(self, bib_file: Path) -> tuple[list[ValidationError], dict]:
        """Validate DOIs in a single bibliography file."""
        errors = []
        metadata = {
            "total_dois": 0,
            "validated_dois": 0,
            "invalid_format": 0,
            "api_failures": 0,
            "successful_validations": 0,
        }

        try:
            content = bib_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = bib_file.read_text(encoding="latin1")
            except Exception as e:
                return [
                    create_validation_error(
                        ErrorCode.FILE_READ_ERROR, f"Cannot read bibliography file: {e}", file_path=str(bib_file)
                    )
                ], metadata

        # Check if file has changed using checksum
        # Skip cache check if force_validation is enabled or if we're in a test environment
        is_test_environment = any("test" in arg for arg in __import__("sys").argv)
        if (
            not self.force_validation
            and not is_test_environment
            and not self.checksum_manager.bibliography_has_changed()[0]
        ):
            logger.info(f"Bibliography file {bib_file.name} unchanged, using cached validation")
            return [], metadata

        # Extract bibliography entries
        entries = self._extract_bib_entries(content)
        if not entries:
            logger.warning(f"No bibliography entries found in {bib_file.name}")
            return [], metadata

        # Validate entries with DOIs
        doi_entries = [entry for entry in entries if "doi" in entry]
        if not doi_entries:
            logger.info(f"No DOI entries found in {bib_file.name}")
            return [], metadata

        metadata["total_dois"] = len(doi_entries)
        logger.info(
            f"Validating {len(doi_entries)} DOI entries in {bib_file.name} using resilient validation with fallback sources"
        )

        # Optimize DOI validation with batching for large sets
        if len(doi_entries) > 20:
            logger.info(f"Processing {len(doi_entries)} DOI entries with batch optimization")

        # Validate DOI entries in parallel with enhanced performance monitoring
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_entry = {
                executor.submit(self._validate_doi_entry, entry, str(bib_file)): entry for entry in doi_entries
            }

            # Process results as they complete for better user feedback
            completed_count = 0
            for future in concurrent.futures.as_completed(future_to_entry):
                entry_errors, entry_metadata = future.result()
                errors.extend(entry_errors)
                # Merge entry metadata
                for key in metadata:
                    if key in entry_metadata:
                        metadata[key] += entry_metadata[key]

                completed_count += 1
                if len(doi_entries) > 10 and completed_count % 10 == 0:
                    logger.info(f"Validated {completed_count}/{len(doi_entries)} DOIs...")

        # Update checksum after successful validation
        self.checksum_manager.update_checksum(validation_completed=True)

        return errors, metadata

    def _validate_bib_file_format_only(self, bib_file: Path) -> tuple[list[ValidationError], dict]:
        """Validate DOI formats in a bibliography file without online validation."""
        errors = []
        metadata = {
            "total_dois": 0,
            "validated_dois": 0,
            "invalid_format": 0,
            "api_failures": 0,
            "successful_validations": 0,
        }

        try:
            content = bib_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = bib_file.read_text(encoding="latin1")
            except Exception as e:
                return [
                    create_validation_error(
                        ErrorCode.FILE_READ_ERROR, f"Cannot read bibliography file: {e}", file_path=str(bib_file)
                    )
                ], metadata

        # Extract bibliography entries
        entries = self._extract_bib_entries(content)
        if not entries:
            logger.warning(f"No bibliography entries found in {bib_file.name}")
            return [], metadata

        # Validate entries with DOIs
        doi_entries = [entry for entry in entries if "doi" in entry]
        if not doi_entries:
            logger.info(f"No DOI entries found in {bib_file.name}")
            return [], metadata

        metadata["total_dois"] = len(doi_entries)

        # Only validate DOI format, not metadata
        for entry in doi_entries:
            doi = entry.get("doi", "").strip()
            entry_key = entry.get("entry_key", "unknown")

            if not doi:
                continue

            # Validate DOI format
            if not self.DOI_REGEX.match(doi):
                metadata["invalid_format"] += 1
                errors.append(
                    create_validation_error(
                        ErrorCode.INVALID_DOI_FORMAT,
                        f"Invalid DOI format: {doi}",
                        file_path=str(bib_file),
                        context=f"Entry: {entry_key}",
                    )
                )

        return errors, metadata

    def _extract_bib_entries(self, bib_content: str) -> list[dict[str, Any]]:
        """Extract bibliography entries from BibTeX content."""
        entries = []

        # Find all @entry{...} blocks
        pattern = r"@(\w+)\s*\{\s*([^,]+)\s*,\s*((?:[^{}]*\{[^{}]*\}[^{}]*|[^{}])*)\s*\}"
        matches = re.finditer(pattern, bib_content, re.MULTILINE | re.DOTALL)

        for match in matches:
            entry_type = match.group(1).lower()
            entry_key = match.group(2).strip()
            fields_text = match.group(3)

            # Extract fields
            fields = self._extract_bib_fields(fields_text)
            fields["entry_type"] = entry_type
            fields["entry_key"] = entry_key

            entries.append(fields)

        return entries

    def _extract_bib_fields(self, fields_text: str) -> dict[str, str]:
        """Extract fields from BibTeX entry."""
        fields = {}

        # Pattern to match field = {value} or field = "value"
        field_pattern = r'(\w+)\s*=\s*[{"]([^}"]*)[}"]'
        field_matches = re.findall(field_pattern, fields_text, re.MULTILINE)

        for field_name, field_value in field_matches:
            fields[field_name.lower().strip()] = field_value.strip()

        return fields

    def _validate_doi_entry(self, entry: dict[str, Any], bib_file: str) -> tuple[list[ValidationError], dict]:
        """Validate a single DOI entry."""
        errors = []
        metadata = {
            "total_dois": 0,
            "validated_dois": 0,
            "invalid_format": 0,
            "api_failures": 0,
            "successful_validations": 0,
        }

        doi = entry.get("doi", "").strip()
        entry_key = entry.get("entry_key", "unknown")

        if not doi:
            return [], metadata

        # Validate DOI format
        if not self.DOI_REGEX.match(doi):
            metadata["invalid_format"] += 1
            errors.append(
                create_validation_error(
                    ErrorCode.INVALID_DOI_FORMAT,
                    f"Invalid DOI format: {doi}",
                    file_path=bib_file,
                    context=f"Entry: {entry_key}",
                )
            )
            return errors, metadata

        # Check DOI resolution with fallback
        doi_resolves = False
        resolution_errors = []

        # Try primary DOI resolver first
        try:
            doi_resolves = self.doi_resolver.verify_resolution(doi)
            if doi_resolves:
                logger.debug(f"DOI {doi} resolved via primary resolver")
        except Exception as e:
            resolution_errors.append(f"Primary resolver: {str(e)}")
            logger.debug(f"Primary DOI resolver failed for {doi}: {e}")

        # If primary resolver fails, try Handle System as fallback (if enabled)
        if not doi_resolves and self.enable_fallback_apis and self.handle_system_client:
            try:
                doi_resolves = self.handle_system_client.verify_resolution(doi)
                if doi_resolves:
                    logger.debug(f"DOI {doi} resolved via Handle System fallback")
            except Exception as e:
                resolution_errors.append(f"Handle System: {str(e)}")
                logger.debug(f"Handle System resolver failed for {doi}: {e}")

        if not doi_resolves:
            error_detail = "; ".join(resolution_errors) if resolution_errors else "Unknown error"
            errors.append(
                create_validation_error(
                    ErrorCode.DOI_NOT_RESOLVABLE,
                    f"DOI does not resolve: {doi} ({error_detail})",
                    file_path=bib_file,
                    context=f"Entry: {entry_key}",
                )
            )

        # Fetch and compare metadata
        try:
            metadata_errors = self._validate_doi_metadata(entry, doi, bib_file)
            errors.extend(metadata_errors)

            # Check if validation was successful (no errors or only success messages)
            has_errors = any(error.level.value == "error" for error in metadata_errors)
            if not has_errors:
                metadata["validated_dois"] += 1
                if any(error.level.value == "success" for error in metadata_errors):
                    metadata["successful_validations"] += 1
            else:
                metadata["api_failures"] += 1
        except Exception as e:
            logger.debug(f"Metadata validation failed for {doi}: {e}")
            metadata["api_failures"] += 1
            errors.append(
                create_validation_error(
                    ErrorCode.METADATA_VALIDATION_FAILED,
                    f"Could not validate metadata for DOI {doi}: {e}",
                    file_path=bib_file,
                    context=f"Entry: {entry_key}",
                )
            )

        return errors, metadata

    def _validate_doi_metadata(self, entry: dict[str, Any], doi: str, bib_file: str) -> list[ValidationError]:
        """Validate DOI metadata against external sources with cascading fallback."""
        errors = []
        entry_key = entry.get("entry_key", "unknown")

        # Define cascading fallback priority order
        # Primary sources (existing)
        primary_sources = [
            (self.crossref_client, "CrossRef"),
            (self.joss_client, "JOSS"),  # For JOSS DOIs
            (self.datacite_client, "DataCite"),
        ]

        # Fallback sources (new resilient alternatives) - only if enabled
        fallback_sources: List[Tuple[BaseDOIClient, str]] = []
        if self.enable_fallback_apis:
            if self.openalex_client:
                fallback_sources.append((self.openalex_client, "OpenAlex"))
            if self.semantic_scholar_client:
                fallback_sources.append((self.semantic_scholar_client, "SemanticScholar"))
            if self.handle_system_client:
                fallback_sources.append((self.handle_system_client, "HandleSystem"))

        # Combine all sources in priority order
        all_sources = primary_sources + fallback_sources

        validation_successful = False
        api_failures = []

        for client, source_name in all_sources:
            try:
                external_metadata = None

                # Check for recent API failures first (negative caching)
                try:
                    cached_failure = self.cache.get_api_failure(doi, source_name)
                    if cached_failure:
                        logger.debug(
                            f"Skipping {source_name} for {doi} due to recent failure: {cached_failure.get('error_message', 'Unknown error')}"
                        )
                        api_failures.append(f"{source_name}: {cached_failure.get('error_message', 'Recent failure')}")
                        continue
                except Exception as cache_read_error:
                    logger.debug(f"Error reading failure cache for {source_name}: {cache_read_error}")

                # Check advanced bibliography cache first
                cached_data = self.bib_cache.get_doi_metadata(doi, [source_name.lower()])
                if cached_data and "metadata" in cached_data:
                    external_metadata = cached_data["metadata"]
                    logger.debug(f"Using cached metadata from {source_name} for {doi}")
                else:
                    # Try extended cache for primary sources during outages
                    if source_name in ["CrossRef", "DataCite"]:
                        cached_metadata = self.cache.get_with_extended_cache(doi)
                        if cached_metadata:
                            external_metadata = cached_metadata
                            logger.debug(f"Using extended cache for {source_name}: {doi}")
                        else:
                            # Fallback to regular cache
                            try:
                                cached_metadata = self.cache.get(doi)
                                if cached_metadata:
                                    external_metadata = cached_metadata
                                    logger.debug(f"Using regular cache for {source_name}: {doi}")
                            except Exception:
                                cached_metadata = None

                    if not external_metadata:
                        # Fetch fresh metadata from API
                        logger.debug(f"Attempting to fetch metadata from {source_name} for {doi}")

                        if source_name == "CrossRef":
                            # Use legacy method for CrossRef for backward compatibility
                            external_metadata = self._fetch_crossref_metadata(doi)
                        else:
                            external_metadata = client.fetch_metadata(doi)

                        if external_metadata:
                            # Cache successful results with improved error handling
                            try:
                                if source_name in ["CrossRef", "DataCite"]:
                                    self.cache.set(doi, external_metadata)
                                logger.debug(f"Successfully cached metadata from {source_name} for {doi}")
                            except Exception as cache_error:
                                logger.debug(f"Failed to cache metadata in DOI cache from {source_name}: {cache_error}")

                            try:
                                self.bib_cache.cache_doi_metadata(doi, external_metadata, source_name.lower())
                                logger.debug(f"Successfully cached in bibliography cache from {source_name} for {doi}")
                            except Exception as bib_cache_error:
                                logger.debug(
                                    f"Failed to cache in bibliography cache from {source_name}: {bib_cache_error}"
                                )

                if external_metadata:
                    # Normalize metadata if needed
                    if hasattr(client, "normalize_metadata"):
                        external_metadata = client.normalize_metadata(external_metadata)

                    # Handle System provides minimal metadata, mainly for resolution verification
                    if source_name == "HandleSystem":
                        if external_metadata.get("_resolved"):
                            # Successfully resolved via Handle System
                            from ..validators.base_validator import ValidationError, ValidationLevel

                            errors.append(
                                ValidationError(
                                    level=ValidationLevel.SUCCESS,
                                    message=f"DOI {doi} successfully resolved via {source_name}",
                                    file_path=bib_file,
                                    context=f"Entry: {entry_key}",
                                )
                            )
                            validation_successful = True
                            logger.info(f"DOI {doi} validated successfully via {source_name} (resolution only)")
                            break
                    else:
                        # Compare metadata for full validation sources
                        if source_name == "JOSS":
                            differences = self.comparator.compare_joss_metadata(entry, external_metadata)
                        elif source_name == "DataCite":
                            differences = self.comparator.compare_datacite_metadata(entry, external_metadata)
                        else:
                            # For OpenAlex, SemanticScholar, and CrossRef
                            differences = self.comparator.compare_metadata(entry, external_metadata, source_name)

                        if differences:
                            for diff in differences:
                                errors.append(
                                    create_validation_error(
                                        ErrorCode.METADATA_MISMATCH,
                                        diff,
                                        file_path=bib_file,
                                        context=f"Entry: {entry_key}, DOI: {doi}",
                                        suggestion=f"Verify bibliography entry against {source_name} data",
                                    )
                                )
                        else:
                            # Add success message when validation passes
                            from ..validators.base_validator import ValidationError, ValidationLevel

                            errors.append(
                                ValidationError(
                                    level=ValidationLevel.SUCCESS,
                                    message=f"DOI {doi} successfully validated against {source_name}",
                                    file_path=bib_file,
                                    context=f"Entry: {entry_key}",
                                )
                            )

                        validation_successful = True
                        logger.info(f"DOI {doi} validated successfully via {source_name}")
                        break  # Use first successful source

            except Exception as e:
                error_message = str(e)
                api_failures.append(f"{source_name}: {error_message}")

                # Cache API failures for negative caching with error handling
                try:
                    self.cache.set_api_failure(doi, source_name, error_message)
                except Exception as cache_write_error:
                    logger.debug(f"Failed to cache API failure for {source_name}: {cache_write_error}")

                logger.debug(f"Unable to validate {doi} via {source_name}: {e} (trying next source)")
                continue

        if not validation_successful:
            # Provide detailed information about what was tried
            failure_detail = "; ".join(api_failures) if api_failures else "All APIs unavailable"

            errors.append(
                create_validation_error(
                    ErrorCode.METADATA_UNAVAILABLE,
                    f"Could not validate metadata for DOI {doi} from any source ({failure_detail})",
                    file_path=bib_file,
                    context=f"Entry: {entry_key}",
                    suggestion="Check network connectivity and try again later, or verify DOI manually",
                )
            )
            logger.warning(f"All validation attempts failed for {doi}: {failure_detail}")

        return errors

    # Legacy methods for backward compatibility with tests
    def _clean_title(self, title: str) -> str:
        """Clean title for comparison (backward compatibility)."""
        return self.comparator._clean_title(title).lower()

    def _clean_journal(self, journal: str) -> str:
        """Clean journal name for comparison (backward compatibility)."""
        import re

        # Match original implementation exactly
        journal = re.sub(r"[{}\\&]", "", journal)
        journal = re.sub(r"\s+", " ", journal)
        return journal.strip().lower()

    def _fetch_crossref_metadata(self, doi: str):
        """Fetch metadata from CrossRef (backward compatibility)."""
        return self.crossref_client.fetch_metadata(doi)
