"""Validation service for comprehensive manuscript validation."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseService, ServiceResult
from .manuscript_service import ManuscriptService

# Import validators with fallback
try:
    from ..validators.citation_validator import CitationValidator
    from ..validators.doi_validator import DOIValidator
    from ..validators.figure_validator import FigureValidator
    from ..validators.latex_error_parser import LaTeXErrorParser
    from ..validators.math_validator import MathValidator
    from ..validators.pdf_validator import PDFValidator
    from ..validators.reference_validator import ReferenceValidator
    from ..validators.syntax_validator import SyntaxValidator

    VALIDATORS_AVAILABLE = True
except ImportError:
    VALIDATORS_AVAILABLE = False


@dataclass
class ValidationConfig:
    """Configuration for validation operations."""

    verbose: bool = False
    include_info: bool = False
    check_latex: bool = True
    enable_doi_validation: bool = True
    validation_level: str = "ERROR"  # ERROR, WARNING, INFO
    stop_on_first_error: bool = False
    include_statistics: bool = False

    def __post_init__(self):
        """Validate configuration after initialization."""
        valid_levels = ["ERROR", "WARNING", "INFO"]
        if self.validation_level not in valid_levels:
            raise ValueError(f"validation_level must be one of {valid_levels}")


@dataclass
class ValidatorResult:
    """Result from a single validator."""

    name: str
    success: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0


@dataclass
class ValidationSummary:
    """Summary of all validation results."""

    total_validators: int
    successful_validators: int
    total_errors: int
    total_warnings: int
    total_info: int
    execution_time: float
    validator_results: List[ValidatorResult] = field(default_factory=list)

    @property
    def overall_success(self) -> bool:
        """Check if validation passed overall."""
        return self.total_errors == 0

    @property
    def has_issues(self) -> bool:
        """Check if there are any issues (errors or warnings)."""
        return self.total_errors > 0 or self.total_warnings > 0


class ValidationService(BaseService):
    """Service for comprehensive manuscript validation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manuscript_service = ManuscriptService(self.config, self.logger)

    def check_validator_availability(self) -> ServiceResult[Dict[str, bool]]:
        """Check which validators are available."""
        availability = {
            "enhanced_validators": VALIDATORS_AVAILABLE,
            "citation_validator": False,
            "figure_validator": False,
            "math_validator": False,
            "reference_validator": False,
            "syntax_validator": False,
            "doi_validator": False,
            "pdf_validator": False,
            "latex_parser": False,
        }

        if VALIDATORS_AVAILABLE:
            validators = [
                ("citation_validator", CitationValidator),
                ("figure_validator", FigureValidator),
                ("math_validator", MathValidator),
                ("reference_validator", ReferenceValidator),
                ("syntax_validator", SyntaxValidator),
                ("doi_validator", DOIValidator),
                ("pdf_validator", PDFValidator),
                ("latex_parser", LaTeXErrorParser),
            ]

            for name, validator_class in validators:
                try:
                    # Try to instantiate the validator
                    validator_class()
                    availability[name] = True
                except Exception as e:
                    self.logger.debug(f"Validator {name} not available: {e}")
                    availability[name] = False

        return ServiceResult.success_result(availability)

    def validate_manuscript_comprehensive(
        self, manuscript_path: Optional[str] = None, config: Optional[ValidationConfig] = None
    ) -> ServiceResult[ValidationSummary]:
        """Perform comprehensive manuscript validation.

        Args:
            manuscript_path: Path to manuscript directory
            config: Validation configuration

        Returns:
            ServiceResult containing ValidationSummary
        """
        if not VALIDATORS_AVAILABLE:
            return ServiceResult.error_result(
                ["Enhanced validators not available", "Install validation dependencies to use comprehensive validation"]
            )

        config = config or ValidationConfig()

        try:
            import time

            start_time = time.time()

            self.log_operation("starting_comprehensive_validation", {"path": manuscript_path, "config": vars(config)})

            # Validate manuscript structure first
            structure_result = self.manuscript_service.validate_manuscript_structure(manuscript_path)
            if not structure_result.success:
                return ServiceResult.error_result(structure_result.errors)

            # Get manuscript metadata for validation configuration
            metadata_result = self.manuscript_service.extract_metadata(manuscript_path)
            if not metadata_result.success:
                return ServiceResult.error_result(metadata_result.errors)

            metadata = metadata_result.data

            # Override DOI validation from metadata if specified
            if hasattr(metadata, "doi_validation_enabled"):
                config.enable_doi_validation = metadata.doi_validation_enabled

            # Define validators to run
            validator_specs = [
                ("Citations", CitationValidator),
                ("Cross-references", ReferenceValidator),
                ("Figures", FigureValidator),
                ("Mathematics", MathValidator),
                ("Syntax", SyntaxValidator),
            ]

            # Add DOI validator if enabled
            if config.enable_doi_validation:
                validator_specs.append(("DOI References", DOIValidator))

            # Run all validators
            validator_results = []
            total_errors = 0
            total_warnings = 0
            total_info = 0

            manuscript_path_obj = Path(manuscript_path) if manuscript_path else Path.cwd()

            for validator_name, validator_class in validator_specs:
                if config.stop_on_first_error and total_errors > 0:
                    break

                result = self._run_single_validator(validator_name, validator_class, manuscript_path_obj, config)

                validator_results.append(result)
                total_errors += len(result.errors)
                total_warnings += len(result.warnings)
                total_info += len(result.info)

                if config.verbose:
                    self._print_validator_result(result, config)

            # Check for LaTeX errors if enabled
            if config.check_latex:
                latex_result = self._check_latex_errors(manuscript_path_obj, config)
                if latex_result:
                    validator_results.append(latex_result)
                    total_errors += len(latex_result.errors)
                    total_warnings += len(latex_result.warnings)

            execution_time = time.time() - start_time

            summary = ValidationSummary(
                total_validators=len(validator_results),
                successful_validators=sum(1 for r in validator_results if r.success),
                total_errors=total_errors,
                total_warnings=total_warnings,
                total_info=total_info,
                execution_time=execution_time,
                validator_results=validator_results,
            )

            self.log_operation(
                "validation_completed",
                {
                    "total_validators": summary.total_validators,
                    "errors": summary.total_errors,
                    "warnings": summary.total_warnings,
                    "success": summary.overall_success,
                    "execution_time": execution_time,
                },
            )

            if summary.overall_success:
                return ServiceResult.success_result(
                    summary,
                    warnings=[f"Validation completed with {total_warnings} warnings"] if total_warnings > 0 else None,
                )
            else:
                return ServiceResult.error_result([f"Validation failed with {total_errors} errors"], data=summary)

        except Exception as e:
            error = self.handle_error("validate_manuscript_comprehensive", e)
            return ServiceResult.error_result([str(error)])

    def _run_single_validator(
        self, validator_name: str, validator_class: type, manuscript_path: Path, config: ValidationConfig
    ) -> ValidatorResult:
        """Run a single validator and return structured results."""
        import time

        start_time = time.time()
        result = ValidatorResult(name=validator_name, success=True)

        try:
            # Instantiate validator
            validator = validator_class()

            # Run validation (this is a simplified interface - actual implementation
            # would need to adapt to each validator's specific API)
            if hasattr(validator, "validate"):
                validation_result = validator.validate(str(manuscript_path))

                # Extract results (this would need to be adapted per validator)
                if hasattr(validation_result, "errors"):
                    result.errors = validation_result.errors or []
                if hasattr(validation_result, "warnings"):
                    result.warnings = validation_result.warnings or []
                if hasattr(validation_result, "info"):
                    result.info = validation_result.info or []
                if hasattr(validation_result, "statistics") and config.include_statistics:
                    result.statistics = validation_result.statistics or {}

            result.success = len(result.errors) == 0

        except Exception as e:
            result.success = False
            result.errors = [f"Validator {validator_name} failed: {str(e)}"]
            self.logger.error(f"Validator {validator_name} failed", exc_info=True)

        result.execution_time = time.time() - start_time
        return result

    def _check_latex_errors(self, manuscript_path: Path, config: ValidationConfig) -> Optional[ValidatorResult]:
        """Check for LaTeX compilation errors."""
        try:
            latex_parser = LaTeXErrorParser()
            result = ValidatorResult(name="LaTeX Compilation", success=True)

            # Look for common LaTeX log files
            log_files = [manuscript_path / "output" / "*.log", manuscript_path / "*.log"]

            errors_found = []
            for pattern in log_files:
                for log_file in manuscript_path.glob(pattern.name):
                    if log_file.exists():
                        try:
                            parsed_errors = latex_parser.parse_log_file(str(log_file))
                            errors_found.extend(parsed_errors)
                        except Exception as e:
                            self.logger.debug(f"Error parsing LaTeX log {log_file}: {e}")

            if errors_found:
                result.errors = [str(error) for error in errors_found]
                result.success = False

            return result if errors_found or config.verbose else None

        except Exception as e:
            self.logger.debug(f"LaTeX error checking failed: {e}")
            return None

    def _print_validator_result(self, result: ValidatorResult, config: ValidationConfig):
        """Print validator result with appropriate formatting."""
        if result.success:
            self.safe_console_print(f"✅ {result.name}: Passed")
        else:
            self.safe_console_print(f"❌ {result.name}: Failed ({len(result.errors)} errors)")

        if result.errors and (config.validation_level in ["ERROR", "WARNING", "INFO"]):
            for error in result.errors:
                self.safe_console_print(f"   Error: {error}")

        if result.warnings and (config.validation_level in ["WARNING", "INFO"]):
            for warning in result.warnings:
                self.safe_console_print(f"   Warning: {warning}")

        if result.info and config.include_info:
            for info in result.info:
                self.safe_console_print(f"   Info: {info}")

        if result.statistics and config.include_statistics:
            for key, value in result.statistics.items():
                self.safe_console_print(f"   {key}: {value}")

    def health_check(self) -> ServiceResult[Dict[str, Any]]:
        """Check validation service health."""
        try:
            # Check validator availability
            availability_result = self.check_validator_availability()
            if not availability_result.success:
                return availability_result

            availability = availability_result.data

            health_data = {
                "service": "ValidationService",
                "validators_available": availability["enhanced_validators"],
                "validator_details": availability,
                "manuscript_service_healthy": False,
            }

            # Check manuscript service health
            ms_health = self.manuscript_service.health_check()
            health_data["manuscript_service_healthy"] = ms_health.success

            # Determine overall health
            if availability["enhanced_validators"] and ms_health.success:
                return ServiceResult.success_result(health_data)
            else:
                errors = []
                if not availability["enhanced_validators"]:
                    errors.append("Enhanced validators not available")
                if not ms_health.success:
                    errors.extend(ms_health.errors)

                return ServiceResult.error_result(errors, data=health_data)

        except Exception as e:
            return ServiceResult.error_result([f"Health check failed: {str(e)}"])
