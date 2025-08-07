"""Refactored DOI validator with improved maintainability."""

import concurrent.futures
import logging
import os
import re
from pathlib import Path
from typing import Any

from ..core.error_codes import ErrorCode, create_validation_error
from .base_validator import (
    BaseValidator,
    ValidationError,
    ValidationResult,
)
from .doi import (
    CrossRefClient,
    DataCiteClient,
    DOIResolver,
    JOSSClient,
    MetadataComparator,
)

try:
    from ..utils.bibliography_cache import get_bibliography_cache
    from ..utils.bibliography_checksum import get_bibliography_checksum_manager
    from ..utils.doi_cache import DOICache
except ImportError:
    # Fallback for script execution
    from ..utils.bibliography_cache import get_bibliography_cache
    from ..utils.bibliography_checksum import get_bibliography_checksum_manager
    from ..utils.doi_cache import DOICache

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
        """
        super().__init__(manuscript_path)

        self.enable_online_validation = enable_online_validation
        self.force_validation = force_validation
        self.ignore_ci_environment = ignore_ci_environment
        self.max_workers = max_workers

        # Initialize cache
        cache_dir = cache_dir or Path(manuscript_path).parent / "cache" / "doi"
        self.cache = DOICache(cache_dir)

        # Initialize API clients
        self.crossref_client = CrossRefClient()
        self.datacite_client = DataCiteClient()
        self.joss_client = JOSSClient()
        self.doi_resolver = DOIResolver()

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

        # Skip online validation in CI unless forced
        if self._is_ci_environment() and not self.force_validation:
            logger.info("Skipping DOI validation in CI environment (use --force-validation to override)")
            return ValidationResult(self.name, errors, metadata)

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

        # Process each bibliography file
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
        logger.info(f"Validating {len(doi_entries)} DOI entries in {bib_file.name}")

        # Validate DOI entries in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_entry = {
                executor.submit(self._validate_doi_entry, entry, str(bib_file)): entry for entry in doi_entries
            }

            for future in concurrent.futures.as_completed(future_to_entry):
                entry_errors, entry_metadata = future.result()
                errors.extend(entry_errors)
                # Merge entry metadata
                for key in metadata:
                    if key in entry_metadata:
                        metadata[key] += entry_metadata[key]

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

        # Check DOI resolution
        if not self.doi_resolver.verify_resolution(doi):
            errors.append(
                create_validation_error(
                    ErrorCode.DOI_NOT_RESOLVABLE,
                    f"DOI does not resolve: {doi}",
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
        """Validate DOI metadata against external sources."""
        errors = []
        entry_key = entry.get("entry_key", "unknown")

        # Try different metadata sources
        metadata_sources = [
            (self.crossref_client, "CrossRef"),
            (self.joss_client, "JOSS"),
            (self.datacite_client, "DataCite"),
        ]

        validation_successful = False

        for client, source_name in metadata_sources:
            try:
                external_metadata = None
                # Check advanced bibliography cache first
                cached_data = self.bib_cache.get_doi_metadata(doi, [source_name.lower()])
                if cached_data and "metadata" in cached_data:
                    external_metadata = cached_data["metadata"]
                    logger.debug(f"Using cached metadata from {source_name} for {doi}")
                else:
                    # Fallback to old cache - fix the argument signature issue
                    try:
                        cached_metadata = self.cache.get(doi)  # DOICache.get() only takes doi parameter
                    except Exception:
                        cached_metadata = None

                    if cached_metadata:
                        external_metadata = cached_metadata
                    else:
                        # Use legacy method for CrossRef for backward compatibility with tests
                        if source_name == "CrossRef":
                            external_metadata = self._fetch_crossref_metadata(doi)
                        else:
                            external_metadata = client.fetch_metadata(doi)
                        if external_metadata:
                            # Cache in both systems for compatibility
                            try:
                                self.cache.set(doi, external_metadata)  # Fix signature here too
                            except Exception:
                                pass  # Ignore cache errors
                            self.bib_cache.cache_doi_metadata(doi, external_metadata, source_name.lower())

                if external_metadata:
                    # Normalize metadata if needed
                    if hasattr(client, "normalize_metadata"):
                        external_metadata = client.normalize_metadata(external_metadata)

                    # Compare metadata
                    if source_name == "JOSS":
                        differences = self.comparator.compare_joss_metadata(entry, external_metadata)
                    elif source_name == "DataCite":
                        differences = self.comparator.compare_datacite_metadata(entry, external_metadata)
                    else:
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
                    break  # Use first successful source

            except Exception as e:
                logger.debug(f"Failed to validate {doi} against {source_name}: {e}")
                continue

        if not validation_successful:
            errors.append(
                create_validation_error(
                    ErrorCode.METADATA_UNAVAILABLE,
                    f"Could not validate metadata for DOI {doi} from any source",
                    file_path=bib_file,
                    context=f"Entry: {entry_key}",
                )
            )

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
