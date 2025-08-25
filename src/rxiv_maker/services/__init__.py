"""Service layer for rxiv-maker business logic.

This package provides high-level business services that orchestrate
domain operations, coordinate between different components, and
encapsulate complex business rules.

Services provide:
- Clear business logic abstraction
- Consistent error handling patterns
- Reusable components across CLI and API
- Transaction-like operation coordination
- Domain-specific data transformation
"""

from .build_service import BuildService
from .configuration_service import ConfigurationService
from .manuscript_service import ManuscriptService
from .publication_service import PublicationService
from .validation_service import ValidationService

__all__ = [
    "ManuscriptService",
    "ValidationService",
    "BuildService",
    "PublicationService",
    "ConfigurationService",
]
