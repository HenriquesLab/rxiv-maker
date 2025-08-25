"""Centralized validation orchestration for rxiv-maker.

This module provides unified validation management that coordinates all
validators with configurable validation levels, parallel execution,
aggregated reporting, and comprehensive error handling.
"""

import concurrent.futures
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

from ...validators.base_validator import ValidationError, ValidationLevel
from ..error_codes import ErrorCode, create_validation_error
from ..error_recovery import RecoveryEnhancedMixin
from ..logging_config import get_logger
from ..path_manager import PathManager

logger = get_logger()


class ValidationContext(Enum):
    """Different validation contexts for different scenarios."""

    FULL = "full"  # Complete validation for production
    QUICK = "quick"  # Fast validation for development
    BUILD = "build"  # Pre-build validation
    PUBLISH = "publish"  # Pre-publication validation
    DEVELOPMENT = "development"  # Development-time validation
    CI = "ci"  # CI/CD pipeline validation


class ValidationStrictness(Enum):
    """Validation strictness levels."""

    STRICT = "strict"  # All warnings become errors
    NORMAL = "normal"  # Standard validation
    LENIENT = "lenient"  # Only critical errors fail validation
    PERMISSIVE = "permissive"  # Only blocking errors fail validation


@dataclass
class ValidatorConfig:
    """Configuration for individual validators."""

    validator_name: str
    enabled: bool = True
    required: bool = True
    timeout: Optional[int] = None
    retry_count: int = 0
    parallel: bool = True
    context_filter: Set[ValidationContext] = field(default_factory=set)
    strictness_override: Optional[ValidationStrictness] = None
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result from a single validator."""

    validator_name: str
    success: bool
    duration: float
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    info: List[ValidationError] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class ValidationSummary:
    """Summary of complete validation run."""

    success: bool
    total_duration: float
    context: ValidationContext
    strictness: ValidationStrictness
    validators_run: int
    validators_passed: int
    validators_failed: int
    validators_skipped: int
    total_errors: int
    total_warnings: int
    total_info: int
    results: Dict[str, ValidationResult] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseValidator(ABC):
    """Abstract base class for validators."""

    def __init__(self, name: str):
        """Initialize validator.

        Args:
            name: Validator name
        """
        self.name = name

    @abstractmethod
    def validate(
        self, manuscript_path: Path, context: ValidationContext, strictness: ValidationStrictness, **kwargs
    ) -> ValidationResult:
        """Validate manuscript.

        Args:
            manuscript_path: Path to manuscript directory
            context: Validation context
            strictness: Validation strictness level
            **kwargs: Additional validation arguments

        Returns:
            Validation result
        """
        pass

    def get_supported_contexts(self) -> Set[ValidationContext]:
        """Get validation contexts this validator supports.

        Returns:
            Set of supported contexts
        """
        return {ValidationContext.FULL}

    def get_dependencies(self) -> List[str]:
        """Get list of validator names this validator depends on.

        Returns:
            List of dependency validator names
        """
        return []


class CitationValidatorWrapper(BaseValidator):
    """Wrapper for citation validator."""

    def __init__(self):
        super().__init__("citation")

    def validate(
        self, manuscript_path: Path, context: ValidationContext, strictness: ValidationStrictness, **kwargs
    ) -> ValidationResult:
        """Validate citations."""
        start_time = time.time()
        result = ValidationResult(validator_name=self.name, success=True, duration=0.0)

        try:
            from ...validators.citation_validator import CitationValidator

            validator = CitationValidator()
            # Use the existing validation logic
            validation_errors = validator.validate_citations(str(manuscript_path))

            # Categorize errors by level
            for error in validation_errors:
                if error.level == ValidationLevel.ERROR:
                    result.errors.append(error)
                elif error.level == ValidationLevel.WARNING:
                    result.warnings.append(error)
                else:
                    result.info.append(error)

            # Apply strictness rules
            if strictness == ValidationStrictness.STRICT:
                result.errors.extend(result.warnings)
                result.warnings = []
            elif strictness == ValidationStrictness.PERMISSIVE:
                result.warnings.extend(result.errors)
                result.errors = []

            result.success = len(result.errors) == 0

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.errors.append(
                create_validation_error(ErrorCode.CITATION_NOT_FOUND, f"Citation validation failed: {e}")
            )

        result.duration = time.time() - start_time
        return result

    def get_supported_contexts(self) -> Set[ValidationContext]:
        return {ValidationContext.FULL, ValidationContext.BUILD, ValidationContext.PUBLISH}


class DOIValidatorWrapper(BaseValidator):
    """Wrapper for DOI validator."""

    def __init__(self):
        super().__init__("doi")

    def validate(
        self, manuscript_path: Path, context: ValidationContext, strictness: ValidationStrictness, **kwargs
    ) -> ValidationResult:
        """Validate DOIs."""
        start_time = time.time()
        result = ValidationResult(validator_name=self.name, success=True, duration=0.0)

        try:
            from ...validators.doi_validator import DOIValidator

            validator = DOIValidator()
            validation_errors = validator.validate_manuscript_dois(str(manuscript_path))

            # Categorize errors by level
            for error in validation_errors:
                if error.level == ValidationLevel.ERROR:
                    result.errors.append(error)
                elif error.level == ValidationLevel.WARNING:
                    result.warnings.append(error)
                else:
                    result.info.append(error)

            # Apply strictness rules
            if strictness == ValidationStrictness.STRICT:
                result.errors.extend(result.warnings)
                result.warnings = []
            elif strictness == ValidationStrictness.PERMISSIVE:
                result.warnings.extend(result.errors)
                result.errors = []

            result.success = len(result.errors) == 0

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.errors.append(create_validation_error(ErrorCode.DOI_NOT_RESOLVABLE, f"DOI validation failed: {e}"))

        result.duration = time.time() - start_time
        return result

    def get_supported_contexts(self) -> Set[ValidationContext]:
        return {ValidationContext.FULL, ValidationContext.PUBLISH}


class FigureValidatorWrapper(BaseValidator):
    """Wrapper for figure validator."""

    def __init__(self):
        super().__init__("figure")

    def validate(
        self, manuscript_path: Path, context: ValidationContext, strictness: ValidationStrictness, **kwargs
    ) -> ValidationResult:
        """Validate figures."""
        start_time = time.time()
        result = ValidationResult(validator_name=self.name, success=True, duration=0.0)

        try:
            from ...validators.figure_validator import FigureValidator

            validator = FigureValidator()
            validation_errors = validator.validate_figures(str(manuscript_path))

            # Categorize errors by level
            for error in validation_errors:
                if error.level == ValidationLevel.ERROR:
                    result.errors.append(error)
                elif error.level == ValidationLevel.WARNING:
                    result.warnings.append(error)
                else:
                    result.info.append(error)

            # Apply strictness rules
            if strictness == ValidationStrictness.STRICT:
                result.errors.extend(result.warnings)
                result.warnings = []
            elif strictness == ValidationStrictness.PERMISSIVE:
                result.warnings.extend(result.errors)
                result.errors = []

            result.success = len(result.errors) == 0

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.errors.append(create_validation_error(ErrorCode.FIGURE_NOT_FOUND, f"Figure validation failed: {e}"))

        result.duration = time.time() - start_time
        return result

    def get_supported_contexts(self) -> Set[ValidationContext]:
        return {ValidationContext.FULL, ValidationContext.BUILD, ValidationContext.QUICK}


class MathValidatorWrapper(BaseValidator):
    """Wrapper for math validator."""

    def __init__(self):
        super().__init__("math")

    def validate(
        self, manuscript_path: Path, context: ValidationContext, strictness: ValidationStrictness, **kwargs
    ) -> ValidationResult:
        """Validate mathematical expressions."""
        start_time = time.time()
        result = ValidationResult(validator_name=self.name, success=True, duration=0.0)

        try:
            from ...validators.math_validator import MathValidator

            validator = MathValidator()
            validation_errors = validator.validate_math_expressions(str(manuscript_path))

            # Categorize errors by level
            for error in validation_errors:
                if error.level == ValidationLevel.ERROR:
                    result.errors.append(error)
                elif error.level == ValidationLevel.WARNING:
                    result.warnings.append(error)
                else:
                    result.info.append(error)

            # Apply strictness rules
            if strictness == ValidationStrictness.STRICT:
                result.errors.extend(result.warnings)
                result.warnings = []
            elif strictness == ValidationStrictness.PERMISSIVE:
                result.warnings.extend(result.errors)
                result.errors = []

            result.success = len(result.errors) == 0

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.errors.append(create_validation_error(ErrorCode.INVALID_MATH_SYNTAX, f"Math validation failed: {e}"))

        result.duration = time.time() - start_time
        return result

    def get_supported_contexts(self) -> Set[ValidationContext]:
        return {ValidationContext.FULL, ValidationContext.BUILD}


class SyntaxValidatorWrapper(BaseValidator):
    """Wrapper for syntax validator."""

    def __init__(self):
        super().__init__("syntax")

    def validate(
        self, manuscript_path: Path, context: ValidationContext, strictness: ValidationStrictness, **kwargs
    ) -> ValidationResult:
        """Validate syntax."""
        start_time = time.time()
        result = ValidationResult(validator_name=self.name, success=True, duration=0.0)

        try:
            from ...validators.syntax_validator import SyntaxValidator

            validator = SyntaxValidator()
            validation_errors = validator.validate_syntax(str(manuscript_path))

            # Categorize errors by level
            for error in validation_errors:
                if error.level == ValidationLevel.ERROR:
                    result.errors.append(error)
                elif error.level == ValidationLevel.WARNING:
                    result.warnings.append(error)
                else:
                    result.info.append(error)

            # Apply strictness rules
            if strictness == ValidationStrictness.STRICT:
                result.errors.extend(result.warnings)
                result.warnings = []
            elif strictness == ValidationStrictness.PERMISSIVE:
                result.warnings.extend(result.errors)
                result.errors = []

            result.success = len(result.errors) == 0

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.errors.append(create_validation_error(ErrorCode.SYNTAX_ERROR, f"Syntax validation failed: {e}"))

        result.duration = time.time() - start_time
        return result

    def get_supported_contexts(self) -> Set[ValidationContext]:
        return {ValidationContext.FULL, ValidationContext.BUILD, ValidationContext.QUICK}


class ValidationManager(RecoveryEnhancedMixin):
    """Centralized validation orchestration with configurable validation levels.

    Features parallel execution and comprehensive reporting.

    Features:
    - Multiple validation contexts (full, quick, build, etc.)
    - Configurable strictness levels
    - Parallel execution of independent validators
    - Dependency-aware execution order
    - Comprehensive error aggregation and reporting
    - Progress tracking and callbacks
    - Validation result caching
    """

    def __init__(
        self,
        path_manager: Optional[PathManager] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ):
        """Initialize validation manager.

        Args:
            path_manager: Path manager for file operations
            progress_callback: Optional progress reporting callback
        """
        super().__init__()
        self.path_manager = path_manager
        self.progress_callback = progress_callback

        # Registry of validators
        self.validators: Dict[str, BaseValidator] = {}
        self.validator_configs: Dict[str, ValidatorConfig] = {}

        # Validation cache
        self.cache: Dict[str, ValidationResult] = {}
        self.cache_ttl: float = 300.0  # 5 minutes

        # Register built-in validators
        self._register_builtin_validators()

        logger.debug("ValidationManager initialized")

    def _register_builtin_validators(self) -> None:
        """Register built-in validators."""
        builtin_validators = [
            CitationValidatorWrapper(),
            DOIValidatorWrapper(),
            FigureValidatorWrapper(),
            MathValidatorWrapper(),
            SyntaxValidatorWrapper(),
        ]

        for validator in builtin_validators:
            self.register_validator(validator)

    def register_validator(self, validator: BaseValidator, config: Optional[ValidatorConfig] = None) -> None:
        """Register a validator.

        Args:
            validator: Validator instance
            config: Optional validator configuration
        """
        self.validators[validator.name] = validator

        if config is None:
            config = ValidatorConfig(validator_name=validator.name)

        self.validator_configs[validator.name] = config

        logger.debug(f"Registered validator: {validator.name}")

    def configure_validator(self, validator_name: str, **config_updates) -> None:
        """Update validator configuration.

        Args:
            validator_name: Name of validator to configure
            **config_updates: Configuration updates
        """
        if validator_name not in self.validator_configs:
            raise ValueError(f"Unknown validator: {validator_name}")

        config = self.validator_configs[validator_name]

        for key, value in config_updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                config.config[key] = value

        logger.debug(f"Updated configuration for validator: {validator_name}")

    def get_context_validators(self, context: ValidationContext) -> List[str]:
        """Get validators for a specific context.

        Args:
            context: Validation context

        Returns:
            List of validator names for the context
        """
        context_validators = []

        for name, validator in self.validators.items():
            config = self.validator_configs[name]

            # Check if validator is enabled
            if not config.enabled:
                continue

            # Check context filter
            if config.context_filter and context not in config.context_filter:
                continue

            # Check if validator supports context
            if context not in validator.get_supported_contexts():
                continue

            context_validators.append(name)

        return context_validators

    def _resolve_execution_order(self, validator_names: List[str]) -> List[str]:
        """Resolve validator execution order based on dependencies.

        Args:
            validator_names: List of validator names to order

        Returns:
            Ordered list of validator names
        """
        ordered = []
        remaining = validator_names.copy()

        while remaining:
            # Find validators with satisfied dependencies
            ready = []
            for name in remaining:
                validator = self.validators[name]
                dependencies = validator.get_dependencies()

                # Check if all dependencies are satisfied
                if all(dep in ordered for dep in dependencies):
                    ready.append(name)

            if not ready:
                # Circular dependency or missing dependency
                logger.warning(f"Cannot resolve dependencies for: {remaining}")
                # Add remaining validators anyway
                ordered.extend(remaining)
                break

            # Add ready validators
            for name in ready:
                ordered.append(name)
                remaining.remove(name)

        return ordered

    def _get_cache_key(
        self, validator_name: str, manuscript_path: Path, context: ValidationContext, strictness: ValidationStrictness
    ) -> str:
        """Generate cache key for validation result.

        Args:
            validator_name: Name of validator
            manuscript_path: Path to manuscript
            context: Validation context
            strictness: Validation strictness

        Returns:
            Cache key string
        """
        # Include file modification time for cache invalidation
        try:
            mtime = manuscript_path.stat().st_mtime
        except OSError:
            mtime = time.time()

        return f"{validator_name}:{manuscript_path}:{context.value}:{strictness.value}:{mtime}"

    def _execute_validator(
        self,
        validator_name: str,
        manuscript_path: Path,
        context: ValidationContext,
        strictness: ValidationStrictness,
        **kwargs,
    ) -> ValidationResult:
        """Execute a single validator with caching.

        Args:
            validator_name: Name of validator to execute
            manuscript_path: Path to manuscript
            context: Validation context
            strictness: Validation strictness
            **kwargs: Additional validation arguments

        Returns:
            Validation result
        """
        # Check cache
        cache_key = self._get_cache_key(validator_name, manuscript_path, context, strictness)

        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            # Check if cache is still valid
            if time.time() - cached_result.duration < self.cache_ttl:
                logger.debug(f"Using cached result for validator: {validator_name}")
                return cached_result

        # Execute validator
        validator = self.validators[validator_name]
        config = self.validator_configs[validator_name]

        # Apply strictness override if configured
        effective_strictness = config.strictness_override or strictness

        try:
            # Execute with timeout if configured
            if config.timeout:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        validator.validate, manuscript_path, context, effective_strictness, **kwargs
                    )
                    result = future.result(timeout=config.timeout)
            else:
                result = validator.validate(manuscript_path, context, effective_strictness, **kwargs)

            # Cache result
            self.cache[cache_key] = result

            return result

        except concurrent.futures.TimeoutError:
            return ValidationResult(
                validator_name=validator_name,
                success=False,
                duration=config.timeout or 0,
                error_message=f"Validator {validator_name} timed out",
            )
        except Exception as e:
            return ValidationResult(
                validator_name=validator_name,
                success=False,
                duration=0.0,
                error_message=f"Validator {validator_name} failed: {e}",
            )

    def validate(
        self,
        manuscript_path: Union[str, Path],
        context: ValidationContext = ValidationContext.FULL,
        strictness: ValidationStrictness = ValidationStrictness.NORMAL,
        parallel: bool = True,
        max_workers: Optional[int] = None,
        **kwargs,
    ) -> ValidationSummary:
        """Run validation with specified context and strictness.

        Args:
            manuscript_path: Path to manuscript directory
            context: Validation context
            strictness: Validation strictness level
            parallel: Whether to run validators in parallel
            max_workers: Maximum number of parallel workers
            **kwargs: Additional validation arguments

        Returns:
            Validation summary
        """
        start_time = time.time()
        manuscript_path = Path(manuscript_path)

        logger.info(f"Starting validation with context={context.value}, strictness={strictness.value}")

        # Get validators for context
        validator_names = self.get_context_validators(context)

        if not validator_names:
            logger.warning(f"No validators available for context: {context.value}")
            return ValidationSummary(
                success=True,
                total_duration=0.0,
                context=context,
                strictness=strictness,
                validators_run=0,
                validators_passed=0,
                validators_failed=0,
                validators_skipped=0,
                total_errors=0,
                total_warnings=0,
                total_info=0,
            )

        # Resolve execution order
        ordered_validators = self._resolve_execution_order(validator_names)

        # Group validators by parallel execution capability
        parallel_validators = []
        sequential_validators = []

        for name in ordered_validators:
            config = self.validator_configs[name]
            if config.parallel and parallel:
                parallel_validators.append(name)
            else:
                sequential_validators.append(name)

        # Execute validators
        results: Dict[str, ValidationResult] = {}

        # Execute parallel validators
        if parallel_validators:
            logger.debug(f"Executing {len(parallel_validators)} validators in parallel")

            max_workers = max_workers or min(len(parallel_validators), 4)

            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_validator = {
                    executor.submit(self._execute_validator, name, manuscript_path, context, strictness, **kwargs): name
                    for name in parallel_validators
                }

                for i, future in enumerate(concurrent.futures.as_completed(future_to_validator)):
                    validator_name = future_to_validator[future]

                    if self.progress_callback:
                        self.progress_callback(f"Validating {validator_name}", i + 1, len(parallel_validators))

                    try:
                        result = future.result()
                        results[validator_name] = result
                    except Exception as e:
                        logger.error(f"Parallel validation failed for {validator_name}: {e}")
                        results[validator_name] = ValidationResult(
                            validator_name=validator_name, success=False, duration=0.0, error_message=str(e)
                        )

        # Execute sequential validators
        for i, name in enumerate(sequential_validators):
            logger.debug(f"Executing validator: {name}")

            if self.progress_callback:
                self.progress_callback(
                    f"Validating {name}",
                    len(parallel_validators) + i + 1,
                    len(parallel_validators) + len(sequential_validators),
                )

            result = self._execute_validator(name, manuscript_path, context, strictness, **kwargs)
            results[name] = result

        # Calculate summary
        total_duration = time.time() - start_time
        validators_run = len(results)
        validators_passed = sum(1 for r in results.values() if r.success)
        validators_failed = sum(1 for r in results.values() if not r.success)
        validators_skipped = len(validator_names) - validators_run

        total_errors = sum(len(r.errors) for r in results.values())
        total_warnings = sum(len(r.warnings) for r in results.values())
        total_info = sum(len(r.info) for r in results.values())

        # Overall success based on errors
        overall_success = total_errors == 0

        summary = ValidationSummary(
            success=overall_success,
            total_duration=total_duration,
            context=context,
            strictness=strictness,
            validators_run=validators_run,
            validators_passed=validators_passed,
            validators_failed=validators_failed,
            validators_skipped=validators_skipped,
            total_errors=total_errors,
            total_warnings=total_warnings,
            total_info=total_info,
            results=results,
        )

        logger.info(
            f"Validation completed: {validators_passed}/{validators_run} passed, "
            f"{total_errors} errors, {total_warnings} warnings ({total_duration:.1f}s)"
        )

        return summary

    def quick_validate(self, manuscript_path: Union[str, Path], **kwargs) -> ValidationSummary:
        """Run quick validation for development."""
        return self.validate(
            manuscript_path, context=ValidationContext.QUICK, strictness=ValidationStrictness.LENIENT, **kwargs
        )

    def build_validate(self, manuscript_path: Union[str, Path], **kwargs) -> ValidationSummary:
        """Run build-time validation."""
        return self.validate(
            manuscript_path, context=ValidationContext.BUILD, strictness=ValidationStrictness.NORMAL, **kwargs
        )

    def publish_validate(self, manuscript_path: Union[str, Path], **kwargs) -> ValidationSummary:
        """Run publication-ready validation."""
        return self.validate(
            manuscript_path, context=ValidationContext.PUBLISH, strictness=ValidationStrictness.STRICT, **kwargs
        )

    def clear_cache(self) -> None:
        """Clear validation result cache."""
        self.cache.clear()
        logger.debug("Validation cache cleared")


# Global validation manager instance
_validation_manager: Optional[ValidationManager] = None


def get_validation_manager() -> ValidationManager:
    """Get the global validation manager instance.

    Returns:
        Global validation manager
    """
    global _validation_manager
    if _validation_manager is None:
        _validation_manager = ValidationManager()
    return _validation_manager


# Convenience functions
def validate_manuscript(
    manuscript_path: Union[str, Path],
    context: ValidationContext = ValidationContext.FULL,
    strictness: ValidationStrictness = ValidationStrictness.NORMAL,
    **kwargs,
) -> ValidationSummary:
    """Validate manuscript with specified parameters."""
    return get_validation_manager().validate(manuscript_path, context=context, strictness=strictness, **kwargs)


def quick_validate(manuscript_path: Union[str, Path], **kwargs) -> ValidationSummary:
    """Run quick validation for development."""
    return get_validation_manager().quick_validate(manuscript_path, **kwargs)


def build_validate(manuscript_path: Union[str, Path], **kwargs) -> ValidationSummary:
    """Run build-time validation."""
    return get_validation_manager().build_validate(manuscript_path, **kwargs)


def publish_validate(manuscript_path: Union[str, Path], **kwargs) -> ValidationSummary:
    """Run publication-ready validation."""
    return get_validation_manager().publish_validate(manuscript_path, **kwargs)
