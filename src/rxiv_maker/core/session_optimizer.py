"""Session key optimization for container reuse.

This module provides optimized session key mapping to minimize container
creation while maintaining logical separation for different operation types.
"""

import logging
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SessionType(Enum):
    """Optimized session types for container reuse."""

    # General purpose session for lightweight operations
    GENERAL = "general"

    # Heavy computational session for resource-intensive operations
    HEAVY_COMPUTE = "heavy_compute"

    # Document processing session for LaTeX, PDF operations
    DOCUMENT = "document"


class SessionOptimizer:
    """Optimizes session key usage for better container reuse."""

    # Mapping from legacy session keys to optimized session types
    LEGACY_SESSION_MAPPING: Dict[str, SessionType] = {
        # Validation operations -> general (lightweight)
        "validation": SessionType.GENERAL,
        "pdf_validation": SessionType.GENERAL,
        # Python scripts -> general (most are lightweight)
        "python_execution": SessionType.GENERAL,
        # Mermaid generation -> general (network-based, lightweight)
        "mermaid_generation": SessionType.GENERAL,
        # R execution -> heavy compute (statistical processing)
        "r_execution": SessionType.HEAVY_COMPUTE,
        # LaTeX compilation -> document (complex document processing)
        "latex_compilation": SessionType.DOCUMENT,
        # Figure generation -> heavy compute (matplotlib, data processing)
        "figure_generation": SessionType.HEAVY_COMPUTE,
    }

    # Session timeout configuration per session type (in seconds)
    SESSION_TIMEOUTS: Dict[SessionType, int] = {
        SessionType.GENERAL: 1800,  # 30 minutes (frequent reuse)
        SessionType.HEAVY_COMPUTE: 2400,  # 40 minutes (expensive to recreate)
        SessionType.DOCUMENT: 1200,  # 20 minutes (moderate reuse)
    }

    @classmethod
    def get_optimized_session_key(cls, original_key: Optional[str]) -> str:
        """Get optimized session key for better container reuse.

        Args:
            original_key: Original session key (can be None)

        Returns:
            Optimized session key
        """
        if original_key is None:
            return SessionType.GENERAL.value

        # Check if it's already an optimized key
        try:
            SessionType(original_key)
            return original_key
        except ValueError:
            pass

        # Map legacy key to optimized key
        session_type = cls.LEGACY_SESSION_MAPPING.get(original_key, SessionType.GENERAL)

        logger.debug(f"Mapped session key '{original_key}' -> '{session_type.value}'")
        return session_type.value

    @classmethod
    def get_session_timeout(cls, session_key: str) -> int:
        """Get optimized timeout for session key.

        Args:
            session_key: Session key (optimized or legacy)

        Returns:
            Timeout in seconds
        """
        optimized_key = cls.get_optimized_session_key(session_key)

        try:
            session_type = SessionType(optimized_key)
            return cls.SESSION_TIMEOUTS.get(session_type, 1200)  # Default 20 minutes
        except ValueError:
            return 1200  # Default fallback

    @classmethod
    def get_session_description(cls, session_key: str) -> str:
        """Get human-readable description of session purpose.

        Args:
            session_key: Session key

        Returns:
            Description string
        """
        optimized_key = cls.get_optimized_session_key(session_key)

        descriptions = {
            SessionType.GENERAL.value: "General purpose operations (validation, Python scripts, etc.)",
            SessionType.HEAVY_COMPUTE.value: "Heavy computational tasks (R, figure generation, etc.)",
            SessionType.DOCUMENT.value: "Document processing (LaTeX, PDF operations, etc.)",
        }

        return descriptions.get(optimized_key, "Unknown session type")

    @classmethod
    def get_all_session_types(cls) -> Dict[str, Dict[str, Any]]:
        """Get all session types with their configuration.

        Returns:
            Dictionary with session type information
        """
        result = {}

        for session_type in SessionType:
            result[session_type.value] = {
                "description": cls.get_session_description(session_type.value),
                "timeout_seconds": cls.SESSION_TIMEOUTS.get(session_type, 1200),
                "legacy_keys": [
                    key for key, mapped_type in cls.LEGACY_SESSION_MAPPING.items() if mapped_type == session_type
                ],
            }

        return result

    @classmethod
    def should_use_session_reuse(cls, operation_type: str) -> bool:
        """Determine if session reuse should be used for operation type.

        Args:
            operation_type: Type of operation being performed

        Returns:
            True if session reuse should be enabled
        """
        # Always enable session reuse for our optimized system
        # The global container manager handles the reuse policy
        return True


def get_optimized_session_key(original_key: Optional[str]) -> str:
    """Convenience function to get optimized session key."""
    return SessionOptimizer.get_optimized_session_key(original_key)


def get_session_timeout(session_key: str) -> int:
    """Convenience function to get session timeout."""
    return SessionOptimizer.get_session_timeout(session_key)
