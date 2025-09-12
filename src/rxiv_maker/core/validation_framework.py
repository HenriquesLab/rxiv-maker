"""Unified validation framework for rxiv-maker.

This module provides centralized validation patterns including:
- Common validation result aggregation
- Progress reporting integration
- Standardized error/warning/info collection
- Batch validation capabilities
- Extensible validator registry
- Performance tracking and reporting
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Type, Union

from ..core.logging_config import get_logger
from ..core.managers.file_manager import get_file_manager
from ..validators.base_validator import BaseValidator, ValidationError, ValidationLevel, ValidationResult

logger = get_logger()


@dataclass
class ValidationStats:
    """Statistics for validation performance tracking."""

    total_validators: int = 0
    successful_validators: int = 0
    failed_validators: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    total_info: int = 0
    total_execution_time: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate validation success rate."""
        if self.total_validators == 0:
            return 0.0
        return (self.successful_validators / self.total_validators) * 100

    @property
    def average_execution_time(self) -> float:
        """Calculate average execution time per validator."""
        if self.total_validators == 0:
            return 0.0
        return self.total_execution_time / self.total_validators


@dataclass
class ValidationContext:
    """Context information for validation operations."""

    manuscript_path: Path
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    skip_validators: List[str] = field(default_factory=list)
    include_warnings: bool = True
    include_info: bool = False
    stop_on_first_error: bool = False
    progress_callback: Optional[callable] = None


class ValidationProgressReporter(Protocol):
    """Protocol for validation progress reporting."""

    def start_validator(self, validator_name: str) -> None:
        """Signal start of validator execution."""
        ...

    def finish_validator(self, validator_name: str, success: bool, execution_time: float) -> None:
        """Signal completion of validator execution."""
        ...

    def report_error(self, validator_name: str, error: ValidationError) -> None:
        """Report validation error."""
        ...

    def report_warning(self, validator_name: str, warning: ValidationError) -> None:
        """Report validation warning."""
        ...


class ValidationRegistry:
    """Registry for managing available validators."""

    def __init__(self):
        """Initialize validation registry."""
        self._validators: Dict[str, Type[BaseValidator]] = {}
        self._validator_metadata: Dict[str, Dict[str, Any]] = {}
        self._load_built_in_validators()

    def _load_built_in_validators(self) -> None:
        """Load built-in validators."""
        try:
            # Try to load available validators
            from ..validators.citation_validator import CitationValidator

            self.register(
                "citations",
                CitationValidator,
                {
                    "description": "Validates citation references and bibliography entries",
                    "category": "content",
                    "priority": 1,
                },
            )
        except ImportError:
            logger.debug("CitationValidator not available")

        try:
            from ..validators.figure_validator import FigureValidator

            self.register(
                "figures",
                FigureValidator,
                {"description": "Validates figure references and files", "category": "content", "priority": 2},
            )
        except ImportError:
            logger.debug("FigureValidator not available")

        try:
            from ..validators.math_validator import MathValidator

            self.register(
                "math",
                MathValidator,
                {"description": "Validates mathematical expressions and syntax", "category": "syntax", "priority": 3},
            )
        except ImportError:
            logger.debug("MathValidator not available")

        try:
            from ..validators.reference_validator import ReferenceValidator

            self.register(
                "references",
                ReferenceValidator,
                {"description": "Validates cross-references and internal links", "category": "content", "priority": 4},
            )
        except ImportError:
            logger.debug("ReferenceValidator not available")

        try:
            from ..validators.syntax_validator import SyntaxValidator

            self.register(
                "syntax",
                SyntaxValidator,
                {"description": "Validates markdown and LaTeX syntax", "category": "syntax", "priority": 5},
            )
        except ImportError:
            logger.debug("SyntaxValidator not available")

        try:
            from ..validators.doi_validator import DOIValidator

            self.register(
                "doi",
                DOIValidator,
                {"description": "Validates DOI references and metadata", "category": "external", "priority": 6},
            )
        except ImportError:
            logger.debug("DOIValidator not available")

    def register(
        self, name: str, validator_class: Type[BaseValidator], metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a validator.

        Args:
            name: Unique validator name
            validator_class: Validator class
            metadata: Optional metadata about the validator
        """
        self._validators[name] = validator_class
        self._validator_metadata[name] = metadata or {}
        logger.debug(f"Registered validator: {name}")

    def get_validator(self, name: str) -> Optional[Type[BaseValidator]]:
        """Get validator class by name.

        Args:
            name: Validator name

        Returns:
            Validator class or None if not found
        """
        return self._validators.get(name)

    def list_validators(self) -> Dict[str, Dict[str, Any]]:
        """List all registered validators with metadata.

        Returns:
            Dictionary of validator names and their metadata
        """
        result = {}
        for name, validator_class in self._validators.items():
            metadata = self._validator_metadata[name].copy()
            metadata["class"] = validator_class.__name__
            result[name] = metadata
        return result

    def get_validators_by_category(self, category: str) -> List[str]:
        """Get validators by category.

        Args:
            category: Category name (e.g., 'content', 'syntax', 'external')

        Returns:
            List of validator names in the category
        """
        return [name for name, metadata in self._validator_metadata.items() if metadata.get("category") == category]


class ValidationAggregator:
    """Aggregates validation results from multiple validators."""

    def __init__(self, progress_reporter: Optional[ValidationProgressReporter] = None):
        """Initialize validation aggregator.

        Args:
            progress_reporter: Optional progress reporter
        """
        self.progress_reporter = progress_reporter
        self.results: List[ValidationResult] = []
        self.stats = ValidationStats()
        self.file_manager = get_file_manager()

    def add_result(self, result: ValidationResult) -> None:
        """Add a validation result.

        Args:
            result: Validation result to add
        """
        self.results.append(result)

        # Update statistics
        self.stats.total_validators += 1
        if result.has_errors:
            self.stats.failed_validators += 1
        else:
            self.stats.successful_validators += 1

        self.stats.total_errors += result.error_count
        self.stats.total_warnings += result.warning_count
        self.stats.total_info += len(result.get_errors_by_level(ValidationLevel.INFO))

        # Report progress if available
        if self.progress_reporter:
            success = not result.has_errors
            # Estimate execution time (would be better to track this properly)
            execution_time = 0.1  # Default estimate
            self.progress_reporter.finish_validator(result.validator_name, success, execution_time)

            # Report individual errors and warnings
            for error in result.get_errors_by_level(ValidationLevel.ERROR):
                self.progress_reporter.report_error(result.validator_name, error)
            for warning in result.get_errors_by_level(ValidationLevel.WARNING):
                self.progress_reporter.report_warning(result.validator_name, warning)

    def get_combined_result(self) -> ValidationResult:
        """Get combined validation result from all validators.

        Returns:
            Combined validation result
        """
        all_errors: List[ValidationError] = []
        combined_metadata: Dict[str, Any] = {
            "total_validators": len(self.results),
            "stats": self.stats,
            "individual_results": {},
        }

        for result in self.results:
            all_errors.extend(result.errors)
            combined_metadata["individual_results"][result.validator_name] = {
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "metadata": result.metadata,
            }

        return ValidationResult(validator_name="CombinedValidation", errors=all_errors, metadata=combined_metadata)

    def has_errors(self) -> bool:
        """Check if any results have errors."""
        return self.stats.total_errors > 0

    def has_warnings(self) -> bool:
        """Check if any results have warnings."""
        return self.stats.total_warnings > 0


class ValidationFramework:
    """Centralized validation framework with extensible validator support."""

    def __init__(self, registry: Optional[ValidationRegistry] = None):
        """Initialize validation framework.

        Args:
            registry: Optional validator registry (creates default if None)
        """
        self.registry = registry or ValidationRegistry()
        self.file_manager = get_file_manager()

    def validate_manuscript(
        self,
        context: ValidationContext,
        validator_names: Optional[List[str]] = None,
        progress_reporter: Optional[ValidationProgressReporter] = None,
    ) -> ValidationResult:
        """Validate manuscript using specified validators.

        Args:
            context: Validation context with manuscript path and configuration
            validator_names: List of validator names to run (runs all if None)
            progress_reporter: Optional progress reporter

        Returns:
            Combined validation result
        """
        start_time = time.time()

        # Determine which validators to run
        if validator_names is None:
            available_validators = list(self.registry.list_validators().keys())
            # Sort by priority
            validator_metadata = self.registry._validator_metadata
            available_validators.sort(key=lambda name: validator_metadata.get(name, {}).get("priority", 999))
            validator_names = available_validators

        # Filter out skipped validators
        validator_names = [name for name in validator_names if name not in context.skip_validators]

        # Create aggregator
        aggregator = ValidationAggregator(progress_reporter)

        logger.info(f"Starting validation with {len(validator_names)} validators")

        for validator_name in validator_names:
            # Check if we should stop on first error
            if context.stop_on_first_error and aggregator.has_errors():
                logger.info("Stopping validation early due to errors (stop_on_first_error=True)")
                break

            validator_class = self.registry.get_validator(validator_name)
            if validator_class is None:
                logger.warning(f"Validator '{validator_name}' not found in registry")
                continue

            # Report progress
            if progress_reporter:
                progress_reporter.start_validator(validator_name)

            # Run validator
            try:
                validator_start_time = time.time()

                # Create validator instance
                validator = validator_class(str(context.manuscript_path))

                # Run validation
                result = validator.validate()

                validator_execution_time = time.time() - validator_start_time

                # Filter results based on context settings
                if not context.include_warnings:
                    result.errors = [e for e in result.errors if e.level == ValidationLevel.ERROR]
                if not context.include_info:
                    result.errors = [e for e in result.errors if e.level != ValidationLevel.INFO]

                # Add execution time to metadata
                result.metadata["execution_time"] = validator_execution_time

                aggregator.add_result(result)

                logger.debug(f"Validator '{validator_name}' completed in {validator_execution_time:.3f}s")

            except Exception as e:
                logger.error(f"Validator '{validator_name}' failed with exception: {e}")

                # Create error result
                error_result = ValidationResult(
                    validator_name=validator_name,
                    errors=[
                        ValidationError(
                            level=ValidationLevel.ERROR,
                            message=f"Validator failed with exception: {str(e)}",
                            context=f"Exception in {validator_name}",
                            suggestion="Check validator implementation and dependencies",
                        )
                    ],
                    metadata={"exception": str(e), "validator_class": validator_class.__name__},
                )

                aggregator.add_result(error_result)

        # Update total execution time
        total_execution_time = time.time() - start_time
        aggregator.stats.total_execution_time = total_execution_time

        # Get combined result
        combined_result = aggregator.get_combined_result()
        combined_result.metadata["total_execution_time"] = total_execution_time
        combined_result.metadata["framework_stats"] = aggregator.stats

        logger.info(
            f"Validation completed in {total_execution_time:.3f}s: "
            f"{aggregator.stats.total_errors} errors, {aggregator.stats.total_warnings} warnings"
        )

        return combined_result

    def validate_single(
        self, manuscript_path: Union[str, Path], validator_name: str, config: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate using a single validator.

        Args:
            manuscript_path: Path to manuscript
            validator_name: Name of validator to run
            config: Optional configuration

        Returns:
            Validation result from single validator
        """
        context = ValidationContext(manuscript_path=Path(manuscript_path), config=config or {})

        return self.validate_manuscript(context, [validator_name])

    def list_available_validators(self) -> Dict[str, Dict[str, Any]]:
        """List all available validators with metadata."""
        return self.registry.list_validators()

    def get_validation_summary(self, result: ValidationResult) -> str:
        """Generate human-readable validation summary.

        Args:
            result: Validation result to summarize

        Returns:
            Formatted summary string
        """
        if "framework_stats" not in result.metadata:
            # Single validator result
            error_count = result.error_count
            warning_count = result.warning_count
            return (
                f"Validation Summary for {result.validator_name}:\n"
                f"  Errors: {error_count}\n"
                f"  Warnings: {warning_count}\n"
                f"  Status: {'❌ FAILED' if error_count > 0 else '✅ PASSED'}"
            )

        # Combined result with stats
        stats = result.metadata["framework_stats"]
        lines = [
            "Validation Summary:",
            f"  Total Validators: {stats.total_validators}",
            f"  Successful: {stats.successful_validators}",
            f"  Failed: {stats.failed_validators}",
            f"  Success Rate: {stats.success_rate:.1f}%",
            f"  Total Errors: {stats.total_errors}",
            f"  Total Warnings: {stats.total_warnings}",
            f"  Execution Time: {stats.total_execution_time:.3f}s",
            f"  Average Time/Validator: {stats.average_execution_time:.3f}s",
            f"  Overall Status: {'❌ FAILED' if stats.total_errors > 0 else '✅ PASSED'}",
        ]

        return "\n".join(lines)


# Global validation framework instance
_validation_framework: Optional[ValidationFramework] = None


def get_validation_framework() -> ValidationFramework:
    """Get the global validation framework instance.

    Returns:
        Global ValidationFramework instance
    """
    global _validation_framework
    if _validation_framework is None:
        _validation_framework = ValidationFramework()
    return _validation_framework


# Convenience functions
def validate_manuscript_quick(
    manuscript_path: Union[str, Path], validators: Optional[List[str]] = None, include_warnings: bool = True
) -> ValidationResult:
    """Quick validation of manuscript with common defaults.

    Args:
        manuscript_path: Path to manuscript
        validators: List of validator names (uses all if None)
        include_warnings: Whether to include warnings in result

    Returns:
        Validation result
    """
    framework = get_validation_framework()
    context = ValidationContext(manuscript_path=Path(manuscript_path), include_warnings=include_warnings)

    return framework.validate_manuscript(context, validators)


def list_available_validators() -> Dict[str, Dict[str, Any]]:
    """List all available validators."""
    return get_validation_framework().list_available_validators()


# Export public API
__all__ = [
    "ValidationFramework",
    "ValidationRegistry",
    "ValidationContext",
    "ValidationAggregator",
    "ValidationStats",
    "ValidationProgressReporter",
    "get_validation_framework",
    "validate_manuscript_quick",
    "list_available_validators",
]
