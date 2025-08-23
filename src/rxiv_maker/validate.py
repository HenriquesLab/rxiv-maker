"""Validation facade for simplified manuscript validation.

This module provides a simplified interface to the comprehensive validation system
without requiring deep knowledge of individual validators.

Usage:
    from rxiv_maker.validate import validate, quick_validate, get_available_validators

    # Quick validation with defaults
    result = quick_validate()

    # Full validation with options
    result = validate(
        verbose=True,
        include_info=True,
        validation_level='WARNING'
    )

    # Check available validators
    validators = get_available_validators()
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Import validation components with fallbacks
try:
    from .services.manuscript_service import ManuscriptService
    from .services.validation_service import ValidationConfig, ValidationService

    VALIDATION_AVAILABLE = True
except ImportError:
    logger.debug("Validation services not available")
    VALIDATION_AVAILABLE = False

VALIDATORS_AVAILABLE = True


def validate(
    manuscript_path: Optional[str] = None,
    verbose: bool = False,
    include_info: bool = False,
    check_latex: bool = True,
    enable_doi_validation: bool = True,
    validation_level: str = "ERROR",
    stop_on_first_error: bool = False,
    include_statistics: bool = False,
) -> Dict[str, Any]:
    """Perform comprehensive manuscript validation.

    Args:
        manuscript_path: Path to manuscript directory (defaults to current directory)
        verbose: Show detailed output during validation
        include_info: Include informational messages in results
        check_latex: Parse LaTeX compilation errors if available
        enable_doi_validation: Validate DOI references against CrossRef API
        validation_level: Minimum level to report ('ERROR', 'WARNING', 'INFO')
        stop_on_first_error: Stop validation on first error encountered
        include_statistics: Include statistical information in results

    Returns:
        Dictionary containing validation results and summary

    Examples:
        >>> result = validate(verbose=True, validation_level='WARNING')
        >>> if result['success']:
        ...     print(f"Validation passed with {result['warnings']} warnings")
        >>> else:
        ...     print(f"Validation failed: {result['errors']}")
    """
    if not VALIDATION_AVAILABLE:
        return {
            "success": False,
            "available": False,
            "error": "Validation system not available",
            "message": "Install validation dependencies to use this feature",
        }

    try:
        # Create validation service
        validation_service = ValidationService()

        # Create configuration
        config = ValidationConfig(
            verbose=verbose,
            include_info=include_info,
            check_latex=check_latex,
            enable_doi_validation=enable_doi_validation,
            validation_level=validation_level,
            stop_on_first_error=stop_on_first_error,
            include_statistics=include_statistics,
        )

        # Run comprehensive validation
        service_result = validation_service.validate_manuscript_comprehensive(
            manuscript_path=manuscript_path, config=config
        )

        # Convert service result to simplified format
        result = {
            "success": service_result.success,
            "available": True,
            "errors": service_result.errors,
            "warnings": service_result.warnings,
            "metadata": service_result.metadata,
        }

        # Add validation summary details if available
        if service_result.data:
            summary = service_result.data
            result.update(
                {
                    "total_validators": summary.total_validators,
                    "successful_validators": summary.successful_validators,
                    "total_errors": summary.total_errors,
                    "total_warnings": summary.total_warnings,
                    "total_info": summary.total_info,
                    "execution_time": summary.execution_time,
                    "overall_success": summary.overall_success,
                    "has_issues": summary.has_issues,
                }
            )

            # Add detailed validator results if requested
            if verbose or include_statistics:
                result["validator_results"] = [
                    {
                        "name": vr.name,
                        "success": vr.success,
                        "errors": vr.errors,
                        "warnings": vr.warnings,
                        "info": vr.info if include_info else [],
                        "statistics": vr.statistics if include_statistics else {},
                        "execution_time": vr.execution_time,
                    }
                    for vr in summary.validator_results
                ]

        return result

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return {"success": False, "available": True, "error": str(e), "errors": [f"Validation system error: {str(e)}"]}


def quick_validate(manuscript_path: Optional[str] = None) -> Dict[str, Any]:
    """Perform quick validation with sensible defaults.

    Args:
        manuscript_path: Path to manuscript directory

    Returns:
        Simplified validation result

    Examples:
        >>> result = quick_validate()
        >>> print(f"Validation {'passed' if result['success'] else 'failed'}")
    """
    return validate(manuscript_path=manuscript_path, verbose=False, validation_level="ERROR", include_statistics=False)


def validate_structure(manuscript_path: Optional[str] = None) -> Dict[str, Any]:
    """Validate basic manuscript structure and required files.

    Args:
        manuscript_path: Path to manuscript directory

    Returns:
        Structure validation results

    Examples:
        >>> result = validate_structure()
        >>> if result['manuscript_found']:
        ...     print("Manuscript file found")
        >>> if result['missing_files']:
        ...     print(f"Missing files: {result['missing_files']}")
    """
    if not VALIDATION_AVAILABLE:
        return {"success": False, "available": False, "error": "Validation system not available"}

    try:
        manuscript_service = ManuscriptService()
        service_result = manuscript_service.validate_manuscript_structure(manuscript_path)

        if service_result.success:
            return {"success": True, "available": True, "warnings": service_result.warnings, **service_result.data}
        else:
            return {"success": False, "available": True, "errors": service_result.errors, "data": service_result.data}

    except Exception as e:
        logger.error(f"Structure validation failed: {e}")
        return {"success": False, "available": True, "error": str(e)}


def get_available_validators() -> Dict[str, Any]:
    """Get information about available validators.

    Returns:
        Dictionary containing validator availability information

    Examples:
        >>> validators = get_available_validators()
        >>> if validators['enhanced_validators']:
        ...     print("Full validation suite available")
        >>> print(f"Available: {[k for k, v in validators.items() if v]}")
    """
    if not VALIDATION_AVAILABLE:
        return {"available": False, "error": "Validation system not available"}

    try:
        validation_service = ValidationService()
        service_result = validation_service.check_validator_availability()

        if service_result.success:
            return {"available": True, **service_result.data}
        else:
            return {"available": False, "errors": service_result.errors}

    except Exception as e:
        logger.error(f"Failed to check validator availability: {e}")
        return {"available": False, "error": str(e)}


def validation_health_check() -> Dict[str, Any]:
    """Perform validation system health check.

    Returns:
        Health check results

    Examples:
        >>> health = validation_health_check()
        >>> if health['healthy']:
        ...     print("Validation system is healthy")
        >>> else:
        ...     print(f"Issues: {health['issues']}")
    """
    if not VALIDATION_AVAILABLE:
        return {"healthy": False, "available": False, "issues": ["Validation system not available"]}

    try:
        validation_service = ValidationService()
        service_result = validation_service.health_check()

        return {
            "healthy": service_result.success,
            "available": True,
            "issues": service_result.errors,
            "warnings": service_result.warnings,
            "details": service_result.data,
        }

    except Exception as e:
        logger.error(f"Validation health check failed: {e}")
        return {"healthy": False, "available": True, "issues": [str(e)]}


# Convenience aliases
validate_manuscript = validate
check_manuscript = quick_validate
check_validators = get_available_validators

__all__ = [
    "validate",
    "quick_validate",
    "validate_structure",
    "get_available_validators",
    "validation_health_check",
    # Convenience aliases
    "validate_manuscript",
    "check_manuscript",
    "check_validators",
]
