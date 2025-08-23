"""Manuscript processing service for rxiv-maker."""

from pathlib import Path
from typing import Any, Dict, Optional

from ..processors.template_processor import generate_supplementary_tex, get_template_path, process_template_replacements
from ..processors.yaml_processor import extract_yaml_metadata, get_doi_validation_setting
from ..utils import create_output_dir, find_manuscript_md, write_manuscript_output
from .base import BaseService, ServiceResult


class ManuscriptMetadata:
    """Structured representation of manuscript metadata."""

    def __init__(self, raw_metadata: Dict[str, Any], manuscript_path: Path):
        self.raw = raw_metadata
        self.manuscript_path = manuscript_path

        # Extract common fields with defaults
        self.title = raw_metadata.get("title", "Untitled Manuscript")
        self.authors = raw_metadata.get("authors", [])
        self.doi_validation_enabled = get_doi_validation_setting(raw_metadata)
        self.acknowledge_rxiv = raw_metadata.get("acknowledge_rxiv_maker", False)

    @property
    def has_authors(self) -> bool:
        """Check if manuscript has authors defined."""
        return bool(self.authors)

    @property
    def author_count(self) -> int:
        """Get number of authors."""
        return len(self.authors) if isinstance(self.authors, list) else 0

    def get_field(self, key: str, default: Any = None) -> Any:
        """Get a metadata field with fallback to default."""
        return self.raw.get(key, default)


class ManuscriptService(BaseService):
    """Service for manuscript discovery, metadata extraction, and processing."""

    def discover_manuscript(self, manuscript_path: Optional[str] = None) -> ServiceResult[Path]:
        """Discover manuscript file in the given path.

        Args:
            manuscript_path: Optional path to search for manuscript

        Returns:
            ServiceResult containing Path to discovered manuscript
        """
        try:
            self.log_operation("discovering_manuscript", {"path": manuscript_path})

            manuscript_file = find_manuscript_md(manuscript_path)

            if not manuscript_file or not manuscript_file.exists():
                return ServiceResult.error_result(
                    [f"No manuscript.md found in {manuscript_path or 'current directory'}"]
                )

            self.log_operation("manuscript_discovered", {"file": str(manuscript_file)})
            return ServiceResult.success_result(manuscript_file)

        except Exception as e:
            error = self.handle_error("discover_manuscript", e)
            return ServiceResult.error_result([str(error)])

    def extract_metadata(self, manuscript_path: Optional[str] = None) -> ServiceResult[ManuscriptMetadata]:
        """Extract and validate manuscript metadata.

        Args:
            manuscript_path: Optional path to manuscript directory

        Returns:
            ServiceResult containing ManuscriptMetadata
        """
        try:
            # First discover the manuscript
            manuscript_result = self.discover_manuscript(manuscript_path)
            if not manuscript_result.success:
                return ServiceResult.error_result(manuscript_result.errors)

            manuscript_file = manuscript_result.data
            self.log_operation("extracting_metadata", {"manuscript": str(manuscript_file)})

            # Extract raw metadata
            raw_metadata = extract_yaml_metadata(str(manuscript_file))

            # Create structured metadata object
            metadata = ManuscriptMetadata(raw_metadata, manuscript_file)

            # Validate essential fields
            warnings = []
            if not metadata.has_authors:
                warnings.append("No authors defined in manuscript metadata")

            if not metadata.title or metadata.title == "Untitled Manuscript":
                warnings.append("No title defined in manuscript metadata")

            self.log_operation(
                "metadata_extracted",
                {
                    "title": metadata.title,
                    "author_count": metadata.author_count,
                    "doi_validation": metadata.doi_validation_enabled,
                },
            )

            return ServiceResult.success_result(metadata, warnings=warnings)

        except Exception as e:
            error = self.handle_error("extract_metadata", e)
            return ServiceResult.error_result([str(error)])

    def validate_manuscript_structure(self, manuscript_path: Optional[str] = None) -> ServiceResult[Dict[str, Any]]:
        """Validate basic manuscript structure and required files.

        Args:
            manuscript_path: Optional path to manuscript directory

        Returns:
            ServiceResult with validation details
        """
        try:
            path = Path(manuscript_path) if manuscript_path else Path.cwd()
            self.validate_path(str(path), must_exist=True, must_be_dir=True)

            self.log_operation("validating_structure", {"path": str(path)})

            validation_details = {
                "manuscript_found": False,
                "config_found": False,
                "figures_dir_found": False,
                "output_dir_found": False,
                "required_files": [],
                "missing_files": [],
                "recommendations": [],
            }

            # Check for manuscript file
            manuscript_result = self.discover_manuscript(manuscript_path)
            validation_details["manuscript_found"] = manuscript_result.success
            if manuscript_result.success:
                validation_details["required_files"].append(str(manuscript_result.data))
            else:
                validation_details["missing_files"].append("manuscript.md")

            # Check for common files and directories
            common_files = [
                ("00_CONFIG.yml", "config_found"),
                ("FIGURES/", "figures_dir_found"),
                ("output/", "output_dir_found"),
            ]

            for file_path, key in common_files:
                full_path = path / file_path
                found = full_path.exists()
                validation_details[key] = found

                if found:
                    validation_details["required_files"].append(str(full_path))
                elif file_path != "output/":  # Output dir is optional
                    validation_details["missing_files"].append(file_path)

            # Generate recommendations
            if not validation_details["config_found"]:
                validation_details["recommendations"].append("Create 00_CONFIG.yml with manuscript metadata")

            if not validation_details["figures_dir_found"]:
                validation_details["recommendations"].append("Create FIGURES/ directory for manuscript figures")

            errors = []
            warnings = []

            if not validation_details["manuscript_found"]:
                errors.append("No manuscript.md file found")

            if validation_details["missing_files"]:
                warnings.extend([f"Missing recommended file: {f}" for f in validation_details["missing_files"]])

            result = ServiceResult.success_result(validation_details, warnings=warnings)
            if errors:
                result.errors.extend(errors)
                result.success = False

            return result

        except Exception as e:
            error = self.handle_error("validate_manuscript_structure", e)
            return ServiceResult.error_result([str(error)])

    def generate_preprint(self, output_dir: str, manuscript_path: Optional[str] = None) -> ServiceResult[Path]:
        """Generate LaTeX preprint from manuscript.

        Args:
            output_dir: Directory to write output files
            manuscript_path: Optional path to manuscript

        Returns:
            ServiceResult containing path to generated LaTeX file
        """
        try:
            self.log_operation("generating_preprint", {"output_dir": output_dir, "manuscript_path": manuscript_path})

            # Extract metadata
            metadata_result = self.extract_metadata(manuscript_path)
            if not metadata_result.success:
                return ServiceResult.error_result(metadata_result.errors)

            metadata = metadata_result.data

            # Ensure output directory exists
            create_output_dir(output_dir)
            self.validate_path(output_dir, must_exist=True, must_be_dir=True)

            # Load template
            template_path = get_template_path()
            with open(template_path, encoding="utf-8") as f:
                template_content = f.read()

            # Process template with metadata
            processed_content = process_template_replacements(
                template_content, metadata.raw, str(metadata.manuscript_path)
            )

            # Write output
            output_file = write_manuscript_output(output_dir, processed_content)

            # Generate supplementary materials
            generate_supplementary_tex(output_dir, metadata.raw)

            self.log_operation("preprint_generated", {"output_file": str(output_file)})

            warnings = metadata_result.warnings
            return ServiceResult.success_result(Path(output_file), warnings=warnings)

        except Exception as e:
            error = self.handle_error("generate_preprint", e)
            return ServiceResult.error_result([str(error)])

    def health_check(self) -> ServiceResult[Dict[str, Any]]:
        """Check manuscript service health."""
        try:
            health_data = {
                "service": "ManuscriptService",
                "template_available": False,
                "current_dir_accessible": False,
                "cache_accessible": False,
            }

            # Check template availability
            try:
                template_path = get_template_path()
                health_data["template_available"] = Path(template_path).exists()
            except Exception:
                pass

            # Check current directory access
            try:
                Path.cwd().exists()
                health_data["current_dir_accessible"] = True
            except Exception:
                pass

            # Check cache access
            try:
                self.cache_dir.exists()
                health_data["cache_accessible"] = True
            except Exception:
                pass

            # Determine overall health
            critical_checks = ["template_available", "current_dir_accessible"]
            all_critical_pass = all(health_data[check] for check in critical_checks)

            if all_critical_pass:
                return ServiceResult.success_result(health_data)
            else:
                failed_checks = [check for check in critical_checks if not health_data[check]]
                return ServiceResult.error_result(
                    [f"Critical health check failed: {check}" for check in failed_checks], data=health_data
                )

        except Exception as e:
            return ServiceResult.error_result([f"Health check failed: {str(e)}"])
