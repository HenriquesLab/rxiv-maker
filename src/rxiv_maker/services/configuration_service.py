"""Configuration service for managing rxiv-maker settings and environment."""

from pathlib import Path
from typing import Any, Dict, Optional

from .base import BaseService, ServiceResult


class ConfigurationService(BaseService):
    """Service for configuration management and environment setup."""

    def load_manuscript_config(
        self, manuscript_path: Optional[str] = None, config_file: str = "00_CONFIG.yml"
    ) -> ServiceResult[Dict[str, Any]]:
        """Load manuscript configuration.

        Args:
            manuscript_path: Path to manuscript directory
            config_file: Configuration file name

        Returns:
            ServiceResult containing configuration data
        """
        try:
            path = Path(manuscript_path) if manuscript_path else Path.cwd()
            config_path = path / config_file

            self.log_operation("loading_config", {"config_path": str(config_path)})

            if not config_path.exists():
                return ServiceResult.error_result([f"Configuration file not found: {config_path}"])

            # Use ConfigManager to load configuration
            config_data = self.config.load_config(str(config_path))

            return ServiceResult.success_result(config_data)

        except Exception as e:
            error = self.handle_error("load_manuscript_config", e)
            return ServiceResult.error_result([str(error)])

    def validate_environment(self) -> ServiceResult[Dict[str, Any]]:
        """Validate rxiv-maker environment and dependencies.

        Returns:
            ServiceResult containing environment validation details
        """
        try:
            self.log_operation("validating_environment")

            env_data = {
                "python_version": "unknown",
                "dependencies": {},
                "cache_accessible": False,
                "latex_available": False,
            }

            # Check Python version
            import sys

            env_data["python_version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

            # Check cache accessibility
            try:
                self.cache_dir.exists()
                env_data["cache_accessible"] = True
            except Exception:
                pass

            # Check LaTeX availability (simplified)
            import shutil

            env_data["latex_available"] = shutil.which("pdflatex") is not None

            warnings = []
            if not env_data["cache_accessible"]:
                warnings.append("Cache directory not accessible")
            if not env_data["latex_available"]:
                warnings.append("LaTeX not found in PATH")

            return ServiceResult.success_result(env_data, warnings=warnings)

        except Exception as e:
            error = self.handle_error("validate_environment", e)
            return ServiceResult.error_result([str(error)])

    def health_check(self) -> ServiceResult[Dict[str, Any]]:
        """Check configuration service health."""
        try:
            health_data = {"service": "ConfigurationService", "config_manager_available": self.config is not None}

            # Test environment validation
            env_result = self.validate_environment()
            health_data["environment_check"] = env_result.success

            if self.config and env_result.success:
                return ServiceResult.success_result(health_data)
            else:
                errors = []
                if not self.config:
                    errors.append("ConfigManager not available")
                if not env_result.success:
                    errors.extend(env_result.errors)

                return ServiceResult.error_result(errors, data=health_data)

        except Exception as e:
            return ServiceResult.error_result([f"Health check failed: {str(e)}"])
