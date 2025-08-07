"""Centralized error codes for rxiv-maker."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..validators.base_validator import ValidationError


class ErrorCategory(Enum):
    """Error categories for organizational purposes."""

    VALIDATION = "validation"
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    COMPILATION = "compilation"
    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    DEPENDENCY = "dependency"
    DOCKER = "docker"
    PLATFORM = "platform"


class ErrorCode(Enum):
    """Comprehensive error codes for rxiv-maker."""

    # Validation Errors (1000-1999)
    INVALID_DOI_FORMAT = "E1001"
    DOI_NOT_RESOLVABLE = "E1002"
    METADATA_MISMATCH = "E1003"
    METADATA_UNAVAILABLE = "E1004"
    INVALID_YAML_FORMAT = "E1005"
    MISSING_REQUIRED_FIELD = "E1006"
    INVALID_REFERENCE = "E1007"
    BROKEN_LINK = "E1008"
    INVALID_MATH_SYNTAX = "E1009"
    CITATION_NOT_FOUND = "E1010"
    FIGURE_NOT_FOUND = "E1011"
    TABLE_FORMAT_ERROR = "E1012"
    BIBLIOGRAPHY_ERROR = "E1013"
    VALIDATION_TIMEOUT = "E1014"
    METADATA_VALIDATION_FAILED = "E1015"

    # Filesystem Errors (2000-2999)
    FILE_NOT_FOUND = "E2001"
    PERMISSION_DENIED = "E2002"
    DISK_SPACE_ERROR = "E2003"
    FILE_READ_ERROR = "E2004"
    FILE_WRITE_ERROR = "E2005"
    DIRECTORY_NOT_FOUND = "E2006"
    INVALID_PATH = "E2007"
    FILE_LOCK_ERROR = "E2008"
    ENCODING_ERROR = "E2009"
    BIB_PROCESSING_ERROR = "E2010"
    OUTPUT_DIRECTORY_ERROR = "E2011"

    # Network Errors (3000-3999)
    CONNECTION_TIMEOUT = "E3001"
    CONNECTION_REFUSED = "E3002"
    DNS_RESOLUTION_ERROR = "E3003"
    SSL_CERTIFICATE_ERROR = "E3004"
    HTTP_ERROR = "E3005"
    API_RATE_LIMIT = "E3006"
    AUTHENTICATION_ERROR = "E3007"
    API_UNAVAILABLE = "E3008"
    PROXY_ERROR = "E3009"
    OFFLINE_MODE_ERROR = "E3010"
    NETWORK_ERROR = "E3011"

    # Compilation Errors (4000-4999)
    LATEX_COMPILATION_ERROR = "E4001"
    BIBTEX_ERROR = "E4002"
    PDF_GENERATION_ERROR = "E4003"
    FIGURE_GENERATION_ERROR = "E4004"
    TEMPLATE_ERROR = "E4005"
    SYNTAX_ERROR = "E4006"
    PACKAGE_NOT_FOUND = "E4007"
    COMPILATION_TIMEOUT = "E4008"
    MEMORY_ERROR = "E4009"
    MERMAID_GENERATION_ERROR = "E4010"

    # Configuration Errors (5000-5999)
    CONFIG_FILE_ERROR = "E5001"
    INVALID_CONFIG_VALUE = "E5002"
    MISSING_CONFIG_FILE = "E5003"
    CONFIG_VALIDATION_ERROR = "E5004"
    ENVIRONMENT_ERROR = "E5005"
    PATH_CONFIGURATION_ERROR = "E5006"
    YAML_CONFIG_ERROR = "E5007"
    CLI_ARGUMENT_ERROR = "E5008"
    WORKFLOW_CONFIG_ERROR = "E5009"
    MANUSCRIPT_CONFIG_ERROR = "E5010"

    # Authentication Errors (6000-6999)
    API_KEY_MISSING = "E6001"
    API_KEY_INVALID = "E6002"
    TOKEN_EXPIRED = "E6003"
    UNAUTHORIZED_ACCESS = "E6004"
    CREDENTIALS_ERROR = "E6005"
    GITHUB_AUTH_ERROR = "E6006"
    DOI_API_AUTH_ERROR = "E6007"

    # Dependency Errors (7000-7999)
    MISSING_DEPENDENCY = "E7001"
    VERSION_INCOMPATIBLE = "E7002"
    INSTALLATION_ERROR = "E7003"
    PYTHON_VERSION_ERROR = "E7004"
    LATEX_NOT_FOUND = "E7005"
    NODEJS_NOT_FOUND = "E7006"
    R_NOT_FOUND = "E7007"
    PACKAGE_MANAGER_ERROR = "E7008"
    SYSTEM_LIBRARY_ERROR = "E7009"
    VIRTUAL_ENV_ERROR = "E7010"

    # Docker Errors (8000-8999)
    DOCKER_NOT_AVAILABLE = "E8001"
    DOCKER_IMAGE_ERROR = "E8002"
    DOCKER_CONTAINER_ERROR = "E8003"
    DOCKER_NETWORK_ERROR = "E8004"
    DOCKER_PERMISSION_ERROR = "E8005"
    DOCKER_BUILD_ERROR = "E8006"
    DOCKER_VOLUME_ERROR = "E8007"
    DOCKER_RESOURCE_ERROR = "E8008"
    DOCKER_TIMEOUT = "E8009"
    DOCKER_COMMAND_ERROR = "E8010"

    # Platform Errors (9000-9999)
    PLATFORM_NOT_SUPPORTED = "E9001"
    WINDOWS_SPECIFIC_ERROR = "E9002"
    MACOS_SPECIFIC_ERROR = "E9003"
    LINUX_SPECIFIC_ERROR = "E9004"
    ARCHITECTURE_ERROR = "E9005"
    PERMISSION_MODEL_ERROR = "E9006"
    PATH_SEPARATOR_ERROR = "E9007"
    SHELL_ERROR = "E9008"
    HOMEBREW_ERROR = "E9009"
    APT_ERROR = "E9010"

    @property
    def category(self) -> ErrorCategory:
        """Get the category for this error code."""
        code_num = int(self.value[1:])  # Remove 'E' prefix

        if 1000 <= code_num < 2000:
            return ErrorCategory.VALIDATION
        elif 2000 <= code_num < 3000:
            return ErrorCategory.FILESYSTEM
        elif 3000 <= code_num < 4000:
            return ErrorCategory.NETWORK
        elif 4000 <= code_num < 5000:
            return ErrorCategory.COMPILATION
        elif 5000 <= code_num < 6000:
            return ErrorCategory.CONFIGURATION
        elif 6000 <= code_num < 7000:
            return ErrorCategory.AUTHENTICATION
        elif 7000 <= code_num < 8000:
            return ErrorCategory.DEPENDENCY
        elif 8000 <= code_num < 9000:
            return ErrorCategory.DOCKER
        elif 9000 <= code_num < 10000:
            return ErrorCategory.PLATFORM
        else:
            return ErrorCategory.VALIDATION  # Default

    @property
    def description(self) -> str:
        """Get human-readable description of the error."""
        descriptions = {
            # Validation Errors
            self.INVALID_DOI_FORMAT: "DOI format is invalid - should be 10.xxxx/yyyy",
            self.DOI_NOT_RESOLVABLE: "DOI does not resolve to a valid publication",
            self.METADATA_MISMATCH: "Bibliography metadata doesn't match external source",
            self.METADATA_UNAVAILABLE: "Could not retrieve metadata for validation",
            self.INVALID_YAML_FORMAT: "YAML configuration file has invalid format",
            self.MISSING_REQUIRED_FIELD: "Required field is missing from configuration",
            self.INVALID_REFERENCE: "Reference format is invalid or malformed",
            self.BROKEN_LINK: "External link is broken or inaccessible",
            self.INVALID_MATH_SYNTAX: "Mathematical expression has invalid syntax",
            self.CITATION_NOT_FOUND: "Citation key not found in bibliography",
            self.FIGURE_NOT_FOUND: "Referenced figure file does not exist",
            self.TABLE_FORMAT_ERROR: "Table format is invalid or corrupted",
            self.BIBLIOGRAPHY_ERROR: "Bibliography file has format errors",
            self.VALIDATION_TIMEOUT: "Validation process exceeded timeout limit",
            self.METADATA_VALIDATION_FAILED: "Failed to validate metadata from external source",
            # Filesystem Errors
            self.FILE_NOT_FOUND: "Required file does not exist",
            self.PERMISSION_DENIED: "Insufficient permissions to access file or directory",
            self.DISK_SPACE_ERROR: "Insufficient disk space for operation",
            self.FILE_READ_ERROR: "Cannot read file due to encoding or format issues",
            self.FILE_WRITE_ERROR: "Cannot write to file or directory",
            self.DIRECTORY_NOT_FOUND: "Required directory does not exist",
            self.INVALID_PATH: "File or directory path is invalid",
            self.FILE_LOCK_ERROR: "File is locked by another process",
            self.ENCODING_ERROR: "File encoding is not supported or corrupted",
            self.BIB_PROCESSING_ERROR: "Failed to process bibliography file",
            self.OUTPUT_DIRECTORY_ERROR: "Cannot create or access output directory",
            # Network Errors
            self.CONNECTION_TIMEOUT: "Network connection timed out",
            self.CONNECTION_REFUSED: "Connection was refused by remote server",
            self.DNS_RESOLUTION_ERROR: "Cannot resolve domain name",
            self.SSL_CERTIFICATE_ERROR: "SSL certificate validation failed",
            self.HTTP_ERROR: "HTTP request failed with error status",
            self.API_RATE_LIMIT: "API rate limit exceeded",
            self.AUTHENTICATION_ERROR: "Authentication failed for network request",
            self.API_UNAVAILABLE: "External API service is unavailable",
            self.PROXY_ERROR: "Proxy server configuration error",
            self.OFFLINE_MODE_ERROR: "Network operation attempted in offline mode",
            # Compilation Errors
            self.LATEX_COMPILATION_ERROR: "LaTeX compilation failed",
            self.BIBTEX_ERROR: "BibTeX processing failed",
            self.PDF_GENERATION_ERROR: "PDF generation failed",
            self.FIGURE_GENERATION_ERROR: "Figure generation script failed",
            self.TEMPLATE_ERROR: "Template processing failed",
            self.SYNTAX_ERROR: "Syntax error in source content",
            self.PACKAGE_NOT_FOUND: "Required LaTeX package not found",
            self.COMPILATION_TIMEOUT: "Compilation process exceeded timeout",
            self.MEMORY_ERROR: "Insufficient memory for compilation",
            self.MERMAID_GENERATION_ERROR: "Mermaid diagram generation failed",
            # Configuration Errors
            self.CONFIG_FILE_ERROR: "Configuration file is corrupted or invalid",
            self.INVALID_CONFIG_VALUE: "Configuration value is invalid",
            self.MISSING_CONFIG_FILE: "Required configuration file not found",
            self.CONFIG_VALIDATION_ERROR: "Configuration validation failed",
            self.ENVIRONMENT_ERROR: "Environment configuration error",
            self.PATH_CONFIGURATION_ERROR: "PATH environment variable misconfiguration",
            self.YAML_CONFIG_ERROR: "YAML configuration parsing error",
            self.CLI_ARGUMENT_ERROR: "Command-line argument error",
            self.WORKFLOW_CONFIG_ERROR: "Workflow configuration error",
            self.MANUSCRIPT_CONFIG_ERROR: "Manuscript configuration error",
            # Docker Errors
            self.DOCKER_NOT_AVAILABLE: "Docker is not installed or accessible",
            self.DOCKER_IMAGE_ERROR: "Docker image pull or build failed",
            self.DOCKER_CONTAINER_ERROR: "Docker container operation failed",
            self.DOCKER_NETWORK_ERROR: "Docker networking error",
            self.DOCKER_PERMISSION_ERROR: "Insufficient Docker permissions",
            self.DOCKER_BUILD_ERROR: "Docker image build failed",
            self.DOCKER_VOLUME_ERROR: "Docker volume mount error",
            self.DOCKER_RESOURCE_ERROR: "Docker resource allocation error",
            self.DOCKER_TIMEOUT: "Docker operation timed out",
            self.DOCKER_COMMAND_ERROR: "Docker command execution failed",
        }

        return descriptions.get(self.value, "Unknown error")

    @property
    def suggested_actions(self) -> list[str]:
        """Get suggested actions to resolve this error."""
        actions = {
            # Validation Errors
            self.INVALID_DOI_FORMAT: [
                "Check DOI format follows pattern: 10.xxxx/yyyy",
                "Verify DOI was copied correctly from source",
                "Remove any extra characters or spaces",
            ],
            self.DOI_NOT_RESOLVABLE: [
                "Verify DOI is correct and not a pre-print",
                "Check network connectivity",
                "Try accessing DOI manually in browser",
            ],
            self.METADATA_MISMATCH: [
                "Review bibliography entry for accuracy",
                "Check if publication details changed",
                "Verify DOI matches the actual publication",
            ],
            # Filesystem Errors
            self.FILE_NOT_FOUND: [
                "Check file path is correct",
                "Verify file exists in expected location",
                "Check case sensitivity of filename",
            ],
            self.PERMISSION_DENIED: [
                "Check file/directory permissions",
                "Run with appropriate user privileges",
                "Verify directory is not read-only",
            ],
            # Docker Errors
            self.DOCKER_NOT_AVAILABLE: [
                "Install Docker Desktop",
                "Start Docker daemon",
                "Add user to docker group (Linux)",
            ],
            self.DOCKER_PERMISSION_ERROR: [
                "Add user to docker group",
                "Run Docker Desktop as administrator",
                "Check Docker daemon permissions",
            ],
        }

        return actions.get(self.value, ["Contact support for assistance"])


def create_validation_error(
    error_code: ErrorCode,
    message: str | None = None,
    file_path: str | None = None,
    line_number: int | None = None,
    context: str | None = None,
    suggestion: str | None = None,
) -> ValidationError:
    """Create a ValidationError with structured error code."""
    from ..validators.base_validator import ValidationError, ValidationLevel

    # Determine severity level from error code
    level = ValidationLevel.ERROR
    if error_code.category in [ErrorCategory.NETWORK, ErrorCategory.DEPENDENCY]:
        level = ValidationLevel.WARNING  # These are often recoverable
    elif error_code == ErrorCode.CITATION_NOT_FOUND and "Unused bibliography entry" in (message or ""):
        level = ValidationLevel.WARNING  # Unused entries are warnings, not errors

    # Use error description if no message provided
    final_message = message or error_code.description

    # Use suggested actions if no suggestion provided
    final_suggestion = suggestion
    if not final_suggestion and error_code.suggested_actions:
        final_suggestion = "; ".join(error_code.suggested_actions)

    return ValidationError(
        level=level,
        message=final_message,
        file_path=file_path,
        line_number=line_number,
        context=context,
        suggestion=final_suggestion,
        error_code=error_code.value,
    )
