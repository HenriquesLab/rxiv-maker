"""Configuration management command implementations for rxiv-maker CLI."""

from pathlib import Path
from typing import Optional

import click

from .base import BaseCommand, CommandExecutionError


class ConfigInitCommand(BaseCommand):
    """Config init command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since config commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since config commands don't need engine."""
        pass

    def execute_operation(self, template: str = "default", force: bool = False, output: Optional[str] = None) -> None:
        """Execute config initialization."""
        import yaml

        from rxiv_maker.core.managers.config_manager import get_config_manager

        try:
            config_manager = get_config_manager()

            if output:
                output_path = Path(output)
                # Custom output path
                if output_path.exists() and not force:
                    self.error_message(f"Configuration file already exists: {output_path}")
                    self.console.print("Use --force to overwrite", style="yellow")
                    raise CommandExecutionError("Configuration file already exists")

                # Get template config and write to custom path
                template_config = config_manager._get_config_template(template)

                with open(output_path, "w", encoding="utf-8") as f:
                    yaml.dump(template_config, f, default_flow_style=False, sort_keys=False)

                config_path = output_path
            else:
                # Use default initialization
                config_path = config_manager.init_config(template, force)

            self.success_message(f"Configuration initialized: {config_path}")
            self.console.print(f"📋 Template: {template}", style="blue")
            self.console.print("💡 Run 'rxiv config validate' to check your configuration", style="dim")

        except ValueError as e:
            self.error_message(str(e))
            raise CommandExecutionError(str(e)) from e
        except Exception as e:
            self.error_message(f"Failed to initialize configuration: {e}")
            raise CommandExecutionError(f"Configuration initialization failed: {e}") from e


class ConfigValidateCommand(BaseCommand):
    """Config validate command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since config commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since config commands don't need engine."""
        pass

    def execute_operation(
        self, config_path: Optional[str] = None, output_format: str = "table", strict: bool = False
    ) -> None:
        """Execute config validation."""
        import json

        from rxiv_maker.config.validator import ConfigValidator
        from rxiv_maker.core.managers.config_manager import get_config_manager

        try:
            config_manager = get_config_manager()
            validator = ConfigValidator()

            self.console.print("🔍 Validating configuration...", style="blue")
            self.console.print("=" * 50)

            config_path_obj = Path(config_path) if config_path else None

            # Validate manuscript configuration
            if config_path_obj:
                self.console.print(f"📄 Validating: {config_path_obj}")
                config_validation = config_manager.validate_config(config_path_obj)
            else:
                self.console.print("📄 Searching for configuration file...")
                config_validation = config_manager.validate_config()

            # Validate CLI arguments
            cli_validation = validator.validate_cli_arguments(
                {"config_path": str(config_path_obj) if config_path_obj else None, "strict": strict}, "validate"
            )

            # Validate environment and project structure
            env_validation = validator.validate_environment_config()
            project_validation = validator.validate_project_structure(Path.cwd())

            # Combine all validation results
            all_results = {
                "configuration": config_validation,
                "cli_arguments": cli_validation,
                "environment": env_validation,
                "project_structure": project_validation,
            }

            if output_format == "json":
                self.console.print(json.dumps(all_results, indent=2, default=str))
            else:
                self._print_validation_results(all_results, strict)

            # Check for errors
            has_errors = any(not result.get("valid", True) for result in all_results.values())

            if has_errors:
                if strict:
                    raise CommandExecutionError("Configuration validation failed (strict mode)")
                else:
                    self.console.print("⚠️  Configuration has warnings/errors", style="yellow")
            else:
                self.success_message("Configuration validation passed!")

        except Exception as e:
            self.error_message(f"Configuration validation failed: {e}")
            raise CommandExecutionError(f"Validation failed: {e}") from e

    def _print_validation_results(self, results: dict, strict: bool) -> None:
        """Print validation results in table format."""
        for category, result in results.items():
            valid = result.get("valid", True)
            status = "✅ Valid" if valid else "❌ Invalid"
            self.console.print(f"{category.title()}: {status}")


class ConfigGetCommand(BaseCommand):
    """Config get/set command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since config commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since config commands don't need engine."""
        pass

    def execute_operation(
        self, key: str, value: Optional[str] = None, config_path: Optional[str] = None, value_type: str = "string"
    ) -> None:
        """Execute config get/set operation."""
        from rxiv_maker.core.managers.config_manager import get_config_manager

        try:
            config_manager = get_config_manager()
            config_path_obj = Path(config_path) if config_path else None

            if value is None:
                # Get value
                config_value = config_manager.get_config_value(key, config_path=config_path_obj)

                if config_value is None:
                    self.error_message(f"Configuration key '{key}' not found")
                    return

                self.console.print(f"📝 {key}: {config_value}", style="green")

                if isinstance(config_value, dict):
                    self.console.print("\n🔍 Nested configuration:", style="blue")
                    for nested_key, nested_value in config_value.items():
                        self.console.print(f"   {key}.{nested_key}: {nested_value}")
            else:
                # Set value with type conversion
                converted_value = self._convert_value(value, value_type)
                updated_path = config_manager.set_config_value(key, converted_value, config_path_obj)

                self.success_message(f"Updated {key} = {converted_value}")
                self.console.print(f"📄 Configuration file: {updated_path}", style="blue")

        except Exception as e:
            self.error_message(f"Configuration operation failed: {e}")
            raise CommandExecutionError(f"Configuration operation failed: {e}") from e

    def _convert_value(self, value: str, value_type: str):
        """Convert string value to appropriate type."""
        import json

        if value_type == "int":
            return int(value)
        elif value_type == "float":
            return float(value)
        elif value_type == "bool":
            return value.lower() in ("true", "1", "yes", "on")
        elif value_type == "json":
            return json.loads(value)
        else:
            return value


class ConfigShowCommand(BaseCommand):
    """Config show command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since config commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since config commands don't need engine."""
        pass

    def execute_operation(
        self, output_format: str = "table", config_path: Optional[str] = None, include_defaults: bool = False
    ) -> None:
        """Execute config show operation."""
        import json

        import click
        import yaml

        from rxiv_maker.core.managers.config_manager import get_config_manager

        try:
            config_manager = get_config_manager()
            config_path_obj = Path(config_path) if config_path else None

            config = config_manager.get_config(config_path_obj, include_defaults=include_defaults)

            if output_format == "json":
                self.console.print(json.dumps(config, indent=2, default=str))
            elif output_format == "yaml":
                yaml.dump(config, click.get_text_stream("stdout"), default_flow_style=False)
            else:
                self._print_config_table(config, include_defaults)

        except Exception as e:
            self.error_message(f"Failed to show configuration: {e}")
            raise CommandExecutionError(f"Failed to show configuration: {e}") from e

    def _print_config_table(self, config: dict, include_defaults: bool) -> None:
        """Print config in table format."""
        for key, value in config.items():
            self.console.print(f"{key}: {value}")


class ConfigExportCommand(BaseCommand):
    """Config export command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since config commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since config commands don't need engine."""
        pass

    def execute_operation(
        self,
        output: str,
        export_format: str = "yaml",
        include_defaults: bool = False,
        config_path: Optional[str] = None,
    ) -> None:
        """Execute config export operation."""
        from rxiv_maker.core.managers.config_manager import get_config_manager

        try:
            config_manager = get_config_manager()
            output_path = Path(output)
            config_path_obj = Path(config_path) if config_path else None

            exported_path = config_manager.export_config(output_path, export_format, include_defaults, config_path_obj)

            self.success_message(f"Configuration exported to: {exported_path}")
            self.console.print(f"📊 Format: {export_format.upper()}", style="blue")

            if include_defaults:
                self.console.print("📝 Includes default values", style="dim")
            else:
                self.console.print("📝 Custom values only", style="dim")

        except Exception as e:
            self.error_message(f"Export failed: {e}")
            raise CommandExecutionError(f"Configuration export failed: {e}") from e


class ConfigMigrateCommand(BaseCommand):
    """Config migrate command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since config commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since config commands don't need engine."""
        pass

    def execute_operation(
        self, from_version: str, to_version: str, config_path: Optional[str] = None, backup: bool = True
    ) -> None:
        """Execute config migration operation."""
        from rxiv_maker.core.managers.config_manager import get_config_manager

        try:
            config_manager = get_config_manager()
            config_path_obj = Path(config_path) if config_path else None

            self.console.print(f"🔄 Migrating configuration: {from_version} → {to_version}", style="blue")

            if backup:
                self.console.print("💾 Backup will be created automatically", style="dim")

            migrated_path = config_manager.migrate_config(from_version, to_version, config_path_obj)

            self.success_message(f"Configuration migrated: {migrated_path}")
            self.console.print("🔍 Please review the migrated configuration", style="yellow")
            self.console.print("💡 Run 'rxiv config validate' to verify the migration", style="dim")

        except Exception as e:
            self.error_message(f"Migration failed: {e}")
            raise CommandExecutionError(f"Configuration migration failed: {e}") from e


class ConfigListCommand(BaseCommand):
    """Config list command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since config commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since config commands don't need engine."""
        pass

    def execute_operation(self) -> None:
        """Execute config list operation."""
        from rich.table import Table

        from rxiv_maker.core.repo_config import get_repo_config
        from rxiv_maker.core.repository import RepositoryManager

        try:
            files = []

            # Check for global repository config first
            repo_config = get_repo_config()
            repo_config_path = repo_config.config_path
            # Add .yaml extension for display (actual file has no extension)
            repo_config_display = f"{repo_config_path}.yaml"
            if repo_config_path.exists():
                stat = repo_config_path.stat()
                files.append(
                    {
                        "path": repo_config_display,
                        "exists": True,
                        "size": stat.st_size,
                        "type": "Repository",
                        "repo_name": "-",
                    }
                )
            else:
                files.append(
                    {
                        "path": repo_config_display,
                        "exists": False,
                        "size": 0,
                        "type": "Repository",
                        "repo_name": "-",
                    }
                )

            # Discover all manuscript repositories
            repo_manager = RepositoryManager()
            try:
                parent_dir = repo_config.parent_dir
                if parent_dir.exists():
                    repos = repo_manager.discover_repositories(parent_dir)

                    # Add config file for each repository
                    for repo in repos:
                        manuscript_config = repo.manuscript_dir / "00_CONFIG.yml"
                        if manuscript_config.exists():
                            stat = manuscript_config.stat()
                            files.append(
                                {
                                    "path": str(manuscript_config),
                                    "exists": True,
                                    "size": stat.st_size,
                                    "type": "Manuscript",
                                    "repo_name": repo.name,
                                }
                            )
                        else:
                            files.append(
                                {
                                    "path": str(manuscript_config),
                                    "exists": False,
                                    "size": 0,
                                    "type": "Manuscript",
                                    "repo_name": repo.name,
                                }
                            )
            except Exception:
                # If no parent dir configured or error, just show current directory
                manuscript_config = Path.cwd() / "00_CONFIG.yml"
                if manuscript_config.exists():
                    stat = manuscript_config.stat()
                    files.append(
                        {
                            "path": str(manuscript_config),
                            "exists": True,
                            "size": stat.st_size,
                            "type": "Manuscript",
                            "repo_name": "current",
                        }
                    )
                else:
                    files.append(
                        {
                            "path": str(manuscript_config),
                            "exists": False,
                            "size": 0,
                            "type": "Manuscript",
                            "repo_name": "current",
                        }
                    )

            table = Table(title="Configuration Files", expand=True)
            table.add_column("Type", style="yellow", no_wrap=True)
            table.add_column("Repo", style="magenta", no_wrap=True)
            table.add_column("Path", style="cyan", overflow="fold")
            table.add_column("Exists", justify="center", no_wrap=True)
            table.add_column("Size", no_wrap=True)

            for file_info in files:
                exists = "✓" if file_info["exists"] else "✗"
                size = f"{file_info.get('size', 0)} bytes" if file_info["exists"] else "-"
                table.add_row(file_info["type"], file_info["repo_name"], file_info["path"], exists, size)

            self.console.print(table)
            self.console.print()
            self.console.print(
                f"[dim]Found {len([f for f in files if f['type'] == 'Manuscript'])} manuscript config(s)[/dim]"
            )
            self.console.print("[dim]Manuscript configs: */MANUSCRIPT/00_CONFIG.yml in each repository[/dim]")
            self.console.print("[dim]Repository config: ~/.rxiv-maker/config for global settings[/dim]")
            self.console.print()

        except Exception as e:
            self.error_message(f"Failed to list configuration files: {e}")
            raise CommandExecutionError(f"Failed to list configuration files: {e}") from e


__all__ = [
    "ConfigInitCommand",
    "ConfigValidateCommand",
    "ConfigGetCommand",
    "ConfigShowCommand",
    "ConfigExportCommand",
    "ConfigMigrateCommand",
    "ConfigListCommand",
]
