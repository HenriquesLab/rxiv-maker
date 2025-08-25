"""Configuration validation and schema checking system.

This module provides comprehensive validation for:
- YAML manuscript configuration
- CLI arguments and options
- Environment variables
- System configuration
- Plugin and extension configurations
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from ..core.cache.advanced_cache import AdvancedCache
from ..core.error_codes import ErrorCode, create_validation_error

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Comprehensive configuration validator with schema validation."""

    def __init__(self, cache_enabled: bool = True):
        """Initialize configuration validator.

        Args:
            cache_enabled: Whether to cache validation results
        """
        self.cache = (
            AdvancedCache(name="config_validation", max_memory_items=50, max_disk_size_mb=5, ttl_hours=24)
            if cache_enabled
            else None
        )

        # Load validation schemas
        self.schemas = self._load_validation_schemas()

        # Known configuration patterns
        self.known_patterns = {
            "email": re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
            "orcid": re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$"),
            "doi": re.compile(r"^10\.\d{4,9}/[-._;()/:\w\[\]]+$", re.IGNORECASE),
            "url": re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE),
            "semantic_version": re.compile(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?$"),
            "iso_date": re.compile(r"^\d{4}-\d{2}-\d{2}$"),
        }

    def validate_manuscript_config(self, config_path: Path) -> Dict[str, Any]:
        """Validate manuscript YAML configuration.

        Args:
            config_path: Path to manuscript YAML file

        Returns:
            Validation results dictionary
        """
        if not config_path.exists():
            return {
                "valid": False,
                "errors": [
                    create_validation_error(
                        ErrorCode.CONFIG_FILE_ERROR,
                        f"Configuration file not found: {config_path}",
                        file_path=str(config_path),
                    )
                ],
                "warnings": [],
                "config_data": None,
            }

        # Check cache first
        cache_key = f"manuscript_config_{self._calculate_file_hash(config_path)}"
        if self.cache:
            cached_result = self.cache.get_data(cache_key)
            if cached_result:
                logger.debug("Using cached configuration validation result")
                return cached_result

        errors: List[Any] = []
        warnings: List[Any] = []
        config_data = None

        try:
            # Parse YAML
            config_data = self._parse_yaml_file(config_path)
            if config_data is None:
                errors.append(
                    create_validation_error(
                        ErrorCode.YAML_CONFIG_ERROR, "Failed to parse YAML configuration", file_path=str(config_path)
                    )
                )
                return self._create_validation_result(False, errors, warnings, None, cache_key)

            # Validate against schema
            schema_errors, schema_warnings = self._validate_against_schema(
                config_data, "manuscript_config", str(config_path)
            )
            errors.extend(schema_errors)
            warnings.extend(schema_warnings)

            # Validate specific fields
            field_errors, field_warnings = self._validate_manuscript_fields(config_data, str(config_path))
            errors.extend(field_errors)
            warnings.extend(field_warnings)

            # Cross-reference validation
            cross_errors, cross_warnings = self._validate_cross_references(
                config_data, config_path.parent, str(config_path)
            )
            errors.extend(cross_errors)
            warnings.extend(cross_warnings)

        except Exception as e:
            logger.debug(f"Error validating manuscript config: {e}")
            errors.append(
                create_validation_error(
                    ErrorCode.CONFIG_VALIDATION_ERROR,
                    f"Configuration validation failed: {e}",
                    file_path=str(config_path),
                )
            )

        result = self._create_validation_result(len(errors) == 0, errors, warnings, config_data, cache_key)

        return result

    def validate_cli_arguments(self, args_dict: Dict[str, Any], command_name: str = "unknown") -> Dict[str, Any]:
        """Validate CLI arguments and options.

        Args:
            args_dict: Dictionary of CLI arguments
            command_name: Name of the command being validated

        Returns:
            Validation results dictionary
        """
        errors = []
        warnings = []

        # Validate common argument patterns
        for arg_name, arg_value in args_dict.items():
            if arg_value is None:
                continue

            # File path validation
            if arg_name.endswith("_file") or arg_name.endswith("_path"):
                if isinstance(arg_value, (str, Path)):
                    path_errors = self._validate_file_path(str(arg_value), arg_name)
                    errors.extend(path_errors)

            # URL validation
            elif arg_name.endswith("_url") or arg_name == "url":
                if isinstance(arg_value, str):
                    url_errors = self._validate_url(arg_value, arg_name)
                    errors.extend(url_errors)

            # Email validation
            elif arg_name.endswith("_email") or arg_name == "email":
                if isinstance(arg_value, str):
                    email_errors = self._validate_email(arg_value, arg_name)
                    errors.extend(email_errors)

            # Output format validation
            elif arg_name == "output_format":
                if isinstance(arg_value, str):
                    format_errors = self._validate_output_format(arg_value, arg_name)
                    errors.extend(format_errors)

        # Command-specific validation
        if command_name in self.schemas.get("cli_commands", {}):
            schema_errors, schema_warnings = self._validate_against_schema(
                args_dict, f"cli_commands.{command_name}", context="CLI arguments"
            )
            errors.extend(schema_errors)
            warnings.extend(schema_warnings)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "command": command_name,
            "args_validated": len(args_dict),
        }

    def validate_environment_config(self) -> Dict[str, Any]:
        """Validate environment variables and system configuration.

        Returns:
            Environment validation results
        """
        errors = []
        warnings = []
        environment_info = {}

        # Check required environment variables
        required_env_vars = {
            "MANUSCRIPT_PATH": {"required": False, "type": "path"},
            "RXIV_ENGINE": {"required": False, "type": "choice", "choices": ["LOCAL", "DOCKER", "PODMAN"]},
            "DOCKER_AVAILABLE": {"required": False, "type": "boolean"},
        }

        for var_name, var_config in required_env_vars.items():
            var_value = os.environ.get(var_name)
            environment_info[var_name] = var_value

            if var_config.get("required", False) and not var_value:
                errors.append(
                    create_validation_error(
                        ErrorCode.ENVIRONMENT_ERROR,
                        f"Required environment variable {var_name} is not set",
                        context="Environment validation",
                    )
                )

            if var_value:
                # Validate type
                var_type = var_config.get("type")
                if var_type == "path":
                    path_errors = self._validate_file_path(var_value, var_name, check_exists=False)
                    errors.extend(path_errors)
                elif var_type == "choice":
                    choices = var_config.get("choices", [])
                    if isinstance(choices, list) and var_value not in choices:
                        warnings.append(
                            create_validation_error(
                                ErrorCode.INVALID_CONFIG_VALUE,
                                f"Environment variable {var_name} has unexpected value: {var_value}. Expected one of: {choices}",
                                context="Environment validation",
                            )
                        )
                elif var_type == "boolean":
                    if var_value.lower() not in ["true", "false", "1", "0", "yes", "no"]:
                        warnings.append(
                            create_validation_error(
                                ErrorCode.INVALID_CONFIG_VALUE,
                                f"Environment variable {var_name} should be a boolean value",
                                context="Environment validation",
                            )
                        )

        # System dependency checks
        system_checks = self._validate_system_dependencies()
        errors.extend(system_checks.get("errors", []))
        warnings.extend(system_checks.get("warnings", []))
        environment_info.update(system_checks.get("system_info", {}))

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "environment_info": environment_info,
            "system_checks": system_checks,
        }

    def validate_project_structure(self, project_dir: Path) -> Dict[str, Any]:
        """Validate project directory structure and required files.

        Args:
            project_dir: Project root directory

        Returns:
            Project structure validation results
        """
        errors = []
        warnings = []
        structure_info = {}

        # Required files and directories
        required_structure = {
            "files": {
                "pyproject.toml": {"required": True, "description": "Project configuration"},
                "README.md": {"required": True, "description": "Project documentation"},
                "CHANGELOG.md": {"required": False, "description": "Change log"},
            },
            "directories": {
                "src": {"required": True, "description": "Source code directory"},
                "tests": {"required": False, "description": "Test directory"},
                ".github": {"required": False, "description": "GitHub workflows"},
            },
        }

        # Check required files
        for file_name, file_config in required_structure["files"].items():
            file_path = project_dir / file_name
            exists = file_path.exists()
            structure_info[f"file_{file_name}"] = exists

            if file_config["required"] and not exists:
                errors.append(
                    create_validation_error(
                        ErrorCode.CONFIG_FILE_ERROR,
                        f"Required file missing: {file_name} - {file_config['description']}",
                        file_path=str(file_path),
                    )
                )
            elif not file_config["required"] and not exists:
                warnings.append(
                    create_validation_error(
                        ErrorCode.CONFIG_FILE_ERROR,
                        f"Optional file missing: {file_name} - {file_config['description']}",
                        file_path=str(file_path),
                    )
                )

        # Check required directories
        for dir_name, dir_config in required_structure["directories"].items():
            dir_path = project_dir / dir_name
            exists = dir_path.exists() and dir_path.is_dir()
            structure_info[f"dir_{dir_name}"] = exists

            if dir_config["required"] and not exists:
                errors.append(
                    create_validation_error(
                        ErrorCode.DIRECTORY_NOT_FOUND,
                        f"Required directory missing: {dir_name} - {dir_config['description']}",
                        file_path=str(dir_path),
                    )
                )

        # Validate pyproject.toml if it exists
        pyproject_path = project_dir / "pyproject.toml"
        if pyproject_path.exists():
            pyproject_validation = self._validate_pyproject_config(pyproject_path)
            errors.extend(pyproject_validation.get("errors", []))
            warnings.extend(pyproject_validation.get("warnings", []))
            structure_info["pyproject_validation"] = pyproject_validation.get("valid", False)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "structure_info": structure_info,
            "project_dir": str(project_dir),
        }

    def _load_validation_schemas(self) -> Dict[str, Any]:
        """Load validation schemas."""
        # Define schemas programmatically for now
        # In a full implementation, these could be loaded from JSON/YAML files

        schemas = {
            "manuscript_config": {
                "type": "object",
                "required": ["title", "authors"],
                "properties": {
                    "title": {"type": "string", "minLength": 1},
                    "authors": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["name"],
                            "properties": {
                                "name": {"type": "string", "minLength": 1},
                                "orcid": {"type": "string", "pattern": r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$"},
                                "email": {"type": "string", "format": "email"},
                                "affiliation": {"type": "string"},
                            },
                        },
                    },
                    "abstract": {"type": "string", "minLength": 50},
                    "keywords": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 10},
                    "date": {"type": "string", "format": "date"},
                    "doi": {"type": "string", "pattern": r"^10\.\d{4,9}/[-._;()/:\w\[\]]+$"},
                    "journal": {"type": "string"},
                    "volume": {"type": ["string", "number"]},
                    "pages": {"type": "string"},
                    "year": {"type": "integer", "minimum": 1900, "maximum": 2100},
                    "acknowledge_rxiv_maker": {"type": "boolean"},
                    "bibliography": {"type": "string"},
                    "style": {"type": "string", "enum": ["nature", "science", "plos", "ieee"]},
                    "language": {"type": "string", "enum": ["en", "es", "pt", "fr", "de"]},
                    "license": {"type": "string"},
                    "repository": {"type": "string", "format": "uri"},
                },
            },
            "cli_commands": {
                "pdf": {
                    "type": "object",
                    "properties": {
                        "manuscript_path": {"type": "string"},
                        "output_dir": {"type": "string"},
                        "engine": {"type": "string", "enum": ["local", "docker", "podman"]},
                        "force_figures": {"type": "boolean"},
                        "skip_validation": {"type": "boolean"},
                        "verbose": {"type": "boolean"},
                    },
                },
                "validate": {
                    "type": "object",
                    "properties": {
                        "manuscript_path": {"type": "string"},
                        "strict": {"type": "boolean"},
                        "format": {"type": "string", "enum": ["table", "json"]},
                    },
                },
            },
        }

        return schemas

    def _parse_yaml_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse YAML file safely."""
        try:
            content = file_path.read_text(encoding="utf-8")

            # Extract YAML front matter if present
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 2:
                    yaml_content = parts[1]
                else:
                    yaml_content = content
            else:
                yaml_content = content

            return yaml.safe_load(yaml_content)

        except yaml.YAMLError as e:
            logger.debug(f"YAML parsing error: {e}")
            return None
        except Exception as e:
            logger.debug(f"Error reading YAML file: {e}")
            return None

    def _validate_against_schema(
        self, data: Dict[str, Any], schema_name: str, context: str = "configuration"
    ) -> Tuple[List[Any], List[Any]]:
        """Validate data against schema."""
        errors: List[Any] = []
        warnings: List[Any] = []

        # Get schema
        schema_path = schema_name.split(".")
        schema = self.schemas
        for part in schema_path:
            if part in schema:
                schema = schema[part]
            else:
                # Schema not found - not an error, just skip validation
                return errors, warnings

        # Basic schema validation (simplified implementation)
        # In production, you'd use a proper JSON schema validator like jsonschema

        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in data:
                errors.append(
                    create_validation_error(
                        ErrorCode.MISSING_REQUIRED_FIELD, f"Required field '{field}' is missing", context=context
                    )
                )

        # Check field types and constraints
        properties = schema.get("properties", {})
        for field_name, field_value in data.items():
            if field_name in properties:
                field_schema = properties[field_name]
                field_errors = self._validate_field_against_schema(field_name, field_value, field_schema, context)
                errors.extend(field_errors)

        return errors, warnings

    def _validate_field_against_schema(
        self, field_name: str, field_value: Any, field_schema: Dict[str, Any], context: str
    ) -> List:
        """Validate individual field against its schema."""
        errors = []

        # Type validation
        expected_type = field_schema.get("type")
        if expected_type:
            type_mapping = {
                "string": str,
                "integer": int,
                "number": (int, float),
                "boolean": bool,
                "array": list,
                "object": dict,
            }

            if expected_type in type_mapping:
                expected_python_type = type_mapping[expected_type]
                if isinstance(expected_python_type, (type, tuple)) and not isinstance(
                    field_value, expected_python_type
                ):
                    errors.append(
                        create_validation_error(
                            ErrorCode.INVALID_CONFIG_VALUE,
                            f"Field '{field_name}' should be of type {expected_type}, got {type(field_value).__name__}",
                            context=context,
                        )
                    )
                    return errors  # Skip further validation if type is wrong

        # String validations
        if isinstance(field_value, str):
            # Min/max length
            min_length = field_schema.get("minLength")
            if min_length and len(field_value) < min_length:
                errors.append(
                    create_validation_error(
                        ErrorCode.INVALID_CONFIG_VALUE,
                        f"Field '{field_name}' is too short (minimum {min_length} characters)",
                        context=context,
                    )
                )

            max_length = field_schema.get("maxLength")
            if max_length and len(field_value) > max_length:
                errors.append(
                    create_validation_error(
                        ErrorCode.INVALID_CONFIG_VALUE,
                        f"Field '{field_name}' is too long (maximum {max_length} characters)",
                        context=context,
                    )
                )

            # Pattern validation
            pattern = field_schema.get("pattern")
            if pattern:
                if not re.match(pattern, field_value):
                    errors.append(
                        create_validation_error(
                            ErrorCode.INVALID_CONFIG_VALUE,
                            f"Field '{field_name}' does not match required pattern",
                            context=context,
                        )
                    )

            # Enum validation
            enum_values = field_schema.get("enum")
            if enum_values and field_value not in enum_values:
                errors.append(
                    create_validation_error(
                        ErrorCode.INVALID_CONFIG_VALUE,
                        f"Field '{field_name}' must be one of: {enum_values}",
                        context=context,
                    )
                )

            # Format validation
            format_type = field_schema.get("format")
            if format_type:
                format_errors = self._validate_string_format(field_name, field_value, format_type, context)
                errors.extend(format_errors)

        # Array validations
        elif isinstance(field_value, list):
            min_items = field_schema.get("minItems")
            if min_items and len(field_value) < min_items:
                errors.append(
                    create_validation_error(
                        ErrorCode.INVALID_CONFIG_VALUE,
                        f"Field '{field_name}' should have at least {min_items} items",
                        context=context,
                    )
                )

            max_items = field_schema.get("maxItems")
            if max_items and len(field_value) > max_items:
                errors.append(
                    create_validation_error(
                        ErrorCode.INVALID_CONFIG_VALUE,
                        f"Field '{field_name}' should have at most {max_items} items",
                        context=context,
                    )
                )

        # Number validations
        elif isinstance(field_value, (int, float)):
            minimum = field_schema.get("minimum")
            if minimum is not None and field_value < minimum:
                errors.append(
                    create_validation_error(
                        ErrorCode.INVALID_CONFIG_VALUE,
                        f"Field '{field_name}' should be at least {minimum}",
                        context=context,
                    )
                )

            maximum = field_schema.get("maximum")
            if maximum is not None and field_value > maximum:
                errors.append(
                    create_validation_error(
                        ErrorCode.INVALID_CONFIG_VALUE,
                        f"Field '{field_name}' should be at most {maximum}",
                        context=context,
                    )
                )

        return errors

    def _validate_string_format(self, field_name: str, value: str, format_type: str, context: str) -> List:
        """Validate string format."""
        errors = []

        if format_type == "email":
            if not self.known_patterns["email"].match(value):
                errors.append(
                    create_validation_error(
                        ErrorCode.INVALID_CONFIG_VALUE,
                        f"Field '{field_name}' is not a valid email address",
                        context=context,
                    )
                )

        elif format_type == "uri":
            if not self.known_patterns["url"].match(value):
                errors.append(
                    create_validation_error(
                        ErrorCode.INVALID_CONFIG_VALUE, f"Field '{field_name}' is not a valid URL", context=context
                    )
                )

        elif format_type == "date":
            if not self.known_patterns["iso_date"].match(value):
                errors.append(
                    create_validation_error(
                        ErrorCode.INVALID_CONFIG_VALUE,
                        f"Field '{field_name}' is not a valid date (YYYY-MM-DD format expected)",
                        context=context,
                    )
                )

        return errors

    def _validate_manuscript_fields(self, config_data: Dict[str, Any], context: str) -> Tuple[List, List]:
        """Validate manuscript-specific fields."""
        errors = []
        warnings = []

        # Validate ORCIDs
        authors = config_data.get("authors", [])
        for i, author in enumerate(authors):
            if not isinstance(author, dict):
                continue

            orcid = author.get("orcid")
            if orcid and not self.known_patterns["orcid"].match(orcid):
                errors.append(
                    create_validation_error(
                        ErrorCode.INVALID_CONFIG_VALUE,
                        f"Author {i + 1} has invalid ORCID format: {orcid}",
                        context=context,
                    )
                )

        # Validate DOI if present
        doi = config_data.get("doi")
        if doi and not self.known_patterns["doi"].match(doi):
            errors.append(
                create_validation_error(ErrorCode.INVALID_DOI_FORMAT, f"Invalid DOI format: {doi}", context=context)
            )

        # Check abstract length (warning for too short)
        abstract = config_data.get("abstract", "")
        if abstract and len(abstract) < 100:
            warnings.append(
                create_validation_error(
                    ErrorCode.INVALID_CONFIG_VALUE,
                    f"Abstract is quite short ({len(abstract)} characters). Consider expanding for better clarity.",
                    context=context,
                )
            )

        # Validate keywords count
        keywords = config_data.get("keywords", [])
        if keywords and len(keywords) > 10:
            warnings.append(
                create_validation_error(
                    ErrorCode.INVALID_CONFIG_VALUE,
                    f"Many keywords ({len(keywords)}). Consider reducing to improve discoverability.",
                    context=context,
                )
            )

        return errors, warnings

    def _validate_cross_references(
        self, config_data: Dict[str, Any], base_dir: Path, context: str
    ) -> Tuple[List, List]:
        """Validate cross-references to files and resources."""
        errors = []
        warnings = []

        # Check bibliography file reference
        bibliography = config_data.get("bibliography")
        if bibliography:
            bib_path = base_dir / bibliography
            if not bib_path.exists():
                errors.append(
                    create_validation_error(
                        ErrorCode.FILE_NOT_FOUND,
                        f"Bibliography file not found: {bibliography}",
                        file_path=str(bib_path),
                        context=context,
                    )
                )

        # Check for FIGURES directory if manuscript references figures
        figures_dir = base_dir / "FIGURES"
        if not figures_dir.exists():
            warnings.append(
                create_validation_error(
                    ErrorCode.DIRECTORY_NOT_FOUND,
                    "FIGURES directory not found - required if manuscript contains figures",
                    file_path=str(figures_dir),
                    context=context,
                )
            )

        return errors, warnings

    def _validate_pyproject_config(self, pyproject_path: Path) -> Dict[str, Any]:
        """Validate pyproject.toml configuration."""
        errors = []
        warnings = []

        try:
            import tomllib

            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)

            # Check required sections
            required_sections = ["project", "build-system"]
            for section in required_sections:
                if section not in pyproject_data:
                    errors.append(
                        create_validation_error(
                            ErrorCode.CONFIG_FILE_ERROR,
                            f"Required section '{section}' missing in pyproject.toml",
                            file_path=str(pyproject_path),
                        )
                    )

            # Validate project metadata
            project_data = pyproject_data.get("project", {})
            required_project_fields = ["name", "description", "authors"]

            for field in required_project_fields:
                if field not in project_data:
                    warnings.append(
                        create_validation_error(
                            ErrorCode.MISSING_REQUIRED_FIELD,
                            f"Recommended project field '{field}' missing in pyproject.toml",
                            file_path=str(pyproject_path),
                        )
                    )

            # Check dependencies format
            dependencies = project_data.get("dependencies", [])
            if dependencies and not isinstance(dependencies, list):
                errors.append(
                    create_validation_error(
                        ErrorCode.INVALID_CONFIG_VALUE,
                        "Dependencies should be a list in pyproject.toml",
                        file_path=str(pyproject_path),
                    )
                )

        except Exception as e:
            errors.append(
                create_validation_error(
                    ErrorCode.CONFIG_FILE_ERROR, f"Error validating pyproject.toml: {e}", file_path=str(pyproject_path)
                )
            )

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def _validate_file_path(self, path: str, field_name: str, check_exists: bool = True) -> List:
        """Validate file path."""
        errors = []

        try:
            path_obj = Path(path)

            # Check for path traversal attempts
            if ".." in path or path.startswith("/"):
                errors.append(
                    create_validation_error(
                        ErrorCode.INVALID_PATH,
                        f"Potentially unsafe path in '{field_name}': {path}",
                        context="CLI validation",
                    )
                )

            # Check if file exists (if requested)
            if check_exists and not path_obj.exists():
                errors.append(
                    create_validation_error(
                        ErrorCode.FILE_NOT_FOUND,
                        f"File not found for '{field_name}': {path}",
                        file_path=path,
                        context="CLI validation",
                    )
                )

        except Exception as e:
            errors.append(
                create_validation_error(
                    ErrorCode.INVALID_PATH, f"Invalid path format for '{field_name}': {e}", context="CLI validation"
                )
            )

        return errors

    def _validate_url(self, url: str, field_name: str) -> List:
        """Validate URL format."""
        errors = []

        if not self.known_patterns["url"].match(url):
            errors.append(
                create_validation_error(
                    ErrorCode.INVALID_CONFIG_VALUE,
                    f"Invalid URL format for '{field_name}': {url}",
                    context="CLI validation",
                )
            )

        return errors

    def _validate_email(self, email: str, field_name: str) -> List:
        """Validate email format."""
        errors = []

        if not self.known_patterns["email"].match(email):
            errors.append(
                create_validation_error(
                    ErrorCode.INVALID_CONFIG_VALUE,
                    f"Invalid email format for '{field_name}': {email}",
                    context="CLI validation",
                )
            )

        return errors

    def _validate_output_format(self, format_value: str, field_name: str) -> List:
        """Validate output format."""
        errors = []

        valid_formats = ["table", "json", "yaml", "csv"]
        if format_value not in valid_formats:
            errors.append(
                create_validation_error(
                    ErrorCode.INVALID_CONFIG_VALUE,
                    f"Invalid output format for '{field_name}': {format_value}. Valid options: {valid_formats}",
                    context="CLI validation",
                )
            )

        return errors

    def _validate_system_dependencies(self) -> Dict[str, Any]:
        """Validate system dependencies and environment."""
        errors: List[Any] = []
        warnings: List[Any] = []
        system_info: Dict[str, Any] = {}

        # Check Python version
        import sys

        python_version = sys.version_info
        system_info["python_version"] = f"{python_version.major}.{python_version.minor}.{python_version.micro}"

        if python_version < (3, 11):
            warnings.append(
                create_validation_error(
                    ErrorCode.PYTHON_VERSION_ERROR,
                    f"Python {python_version.major}.{python_version.minor} is below recommended version 3.11+",
                    context="System validation",
                )
            )

        # Check for Docker availability
        docker_available = self._check_docker_available()
        system_info["docker_available"] = docker_available

        if not docker_available:
            warnings.append(
                create_validation_error(
                    ErrorCode.DOCKER_NOT_AVAILABLE,
                    "Docker is not available - some features may be limited",
                    context="System validation",
                )
            )

        # Check disk space in current directory
        disk_info = self._check_disk_space()
        system_info.update(disk_info)

        if disk_info.get("free_space_gb", 0) < 1:
            warnings.append(
                create_validation_error(
                    ErrorCode.DISK_SPACE_ERROR, "Low disk space - less than 1GB available", context="System validation"
                )
            )

        return {"errors": errors, "warnings": warnings, "system_info": system_info}

    def _check_docker_available(self) -> bool:
        """Check if Docker is available."""
        try:
            import subprocess

            result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space."""
        try:
            import shutil

            total, used, free = shutil.disk_usage(".")

            return {
                "total_space_gb": total / (1024**3),
                "used_space_gb": used / (1024**3),
                "free_space_gb": free / (1024**3),
            }
        except Exception:
            return {}

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate hash of file for caching."""
        try:
            import hashlib

            return hashlib.md5(file_path.read_bytes(), usedforsecurity=False).hexdigest()[:12]
        except Exception:
            return "unknown"

    def _create_validation_result(
        self,
        is_valid: bool,
        errors: List,
        warnings: List,
        config_data: Optional[Dict[str, Any]],
        cache_key: Optional[str],
    ) -> Dict[str, Any]:
        """Create validation result dictionary and cache if needed."""
        result = {
            "valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "config_data": config_data,
            "error_count": len(errors),
            "warning_count": len(warnings),
        }

        # Cache result if cache is enabled and key is provided
        if self.cache and cache_key:
            self.cache.set(cache_key, result, content_based=False)

        return result
