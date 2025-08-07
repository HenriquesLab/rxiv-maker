"""CLI commands for configuration management and validation."""

import json
from pathlib import Path
from typing import Any, Dict

import click
import yaml

from ...config.manager import get_config_manager
from ...config.validator import ConfigValidator
from ...utils.platform import safe_console_print


@click.group(name="config")
def config_group():
    """Configuration management and validation commands."""
    pass


@config_group.command()
@click.option(
    "--template",
    type=click.Choice(["default", "minimal", "journal", "preprint"]),
    default="default",
    help="Configuration template to use",
)
@click.option("--force", is_flag=True, help="Overwrite existing configuration file")
@click.option("--output", type=click.Path(path_type=Path), help="Output path for configuration file")
def init(template: str, force: bool, output: Path = None):
    """Initialize configuration file from template."""
    try:
        config_manager = get_config_manager()

        if output:
            # Custom output path
            if output.exists() and not force:
                safe_console_print(f"❌ Configuration file already exists: {output}")
                safe_console_print("Use --force to overwrite")
                raise click.ClickException("Configuration file already exists")

            # Get template config and write to custom path
            template_config = config_manager._get_config_template(template)

            with open(output, "w", encoding="utf-8") as f:
                yaml.dump(template_config, f, default_flow_style=False, sort_keys=False)

            config_path = output
        else:
            # Use default initialization
            config_path = config_manager.init_config(template, force)

        safe_console_print(f"✅ Configuration file created: {config_path}")
        safe_console_print(f"📝 Template used: {template}")
        safe_console_print("\n💡 Next steps:")
        safe_console_print(f"   1. Edit {config_path.name} with your manuscript details")
        safe_console_print("   2. Run 'rxiv config validate' to check your configuration")
        safe_console_print("   3. Use 'rxiv pdf' to generate your manuscript")

    except ValueError as e:
        safe_console_print(f"❌ {e}")
        raise click.ClickException(str(e)) from e
    except Exception as e:
        safe_console_print(f"❌ Failed to initialize configuration: {e}")
        raise click.ClickException(f"Configuration initialization failed: {e}") from e


@config_group.command()
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file to validate",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format for validation results",
)
@click.option("--strict", is_flag=True, help="Use strict validation mode")
def validate(config_path: Path = None, output_format: str = "table", strict: bool = False):
    """Validate configuration file."""
    try:
        config_manager = get_config_manager()
        validator = ConfigValidator()

        safe_console_print("🔍 Validating configuration...")
        safe_console_print("=" * 50)

        # Validate manuscript configuration
        if config_path:
            safe_console_print(f"📄 Validating: {config_path}")
            config_validation = config_manager.validate_config(config_path)
        else:
            safe_console_print("📄 Searching for configuration file...")
            config_validation = config_manager.validate_config()

        # Validate CLI arguments (simulate current command)
        cli_validation = validator.validate_cli_arguments(
            {"config_path": str(config_path) if config_path else None, "strict": strict}, "validate"
        )

        # Validate environment
        env_validation = validator.validate_environment_config()

        # Validate project structure
        project_validation = validator.validate_project_structure(Path.cwd())

        # Combine all validation results
        all_results = {
            "configuration": config_validation,
            "cli_arguments": cli_validation,
            "environment": env_validation,
            "project_structure": project_validation,
        }

        if output_format == "json":
            safe_console_print(json.dumps(all_results, indent=2, default=str))
        else:
            _print_validation_results(all_results, strict)

        # Exit with appropriate code
        has_errors = any(not result.get("valid", True) for result in all_results.values())

        if has_errors:
            if strict:
                raise click.ClickException("Configuration validation failed (strict mode)")
            else:
                safe_console_print("\n⚠️  Validation completed with issues (non-blocking)")
        else:
            safe_console_print("\n✅ All validations passed!")

    except Exception as e:
        safe_console_print(f"❌ Validation failed: {e}")
        raise click.ClickException(f"Configuration validation failed: {e}") from e


@config_group.command()
@click.argument("key")
@click.argument("value", required=False)
@click.option("--config", "config_path", type=click.Path(path_type=Path), help="Path to configuration file")
@click.option(
    "--type",
    "value_type",
    type=click.Choice(["string", "int", "float", "bool", "json"]),
    default="string",
    help="Value type for setting values",
)
def get(key: str, value: str = None, config_path: Path = None, value_type: str = "string"):
    """Get or set configuration values."""
    try:
        config_manager = get_config_manager()

        if value is None:
            # Get value
            config_value = config_manager.get_config_value(key, config_path=config_path)

            if config_value is None:
                safe_console_print(f"❌ Configuration key '{key}' not found")
                return

            safe_console_print(f"📝 {key}: {config_value}")

            if isinstance(config_value, dict):
                safe_console_print("\n🔍 Nested configuration:")
                for nested_key, nested_value in config_value.items():
                    safe_console_print(f"   {key}.{nested_key}: {nested_value}")
        else:
            # Set value
            # Convert value to appropriate type
            if value_type == "int":
                converted_value = int(value)
            elif value_type == "float":
                converted_value = float(value)
            elif value_type == "bool":
                converted_value = value.lower() in ("true", "1", "yes", "on")
            elif value_type == "json":
                converted_value = json.loads(value)
            else:
                converted_value = value

            updated_path = config_manager.set_config_value(key, converted_value, config_path)
            safe_console_print(f"✅ Updated {key} = {converted_value}")
            safe_console_print(f"📄 Configuration file: {updated_path}")

    except Exception as e:
        safe_console_print(f"❌ Configuration operation failed: {e}")
        raise click.ClickException(f"Configuration operation failed: {e}") from e


@config_group.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format for configuration display",
)
@click.option(
    "--config", "config_path", type=click.Path(exists=True, path_type=Path), help="Path to specific configuration file"
)
@click.option("--include-defaults", is_flag=True, help="Include default values in output")
def show(output_format: str = "table", config_path: Path = None, include_defaults: bool = False):
    """Show current configuration."""
    try:
        config_manager = get_config_manager()

        if include_defaults:
            config = config_manager.load_config(config_path)
        else:
            # Load only non-default configuration
            if config_path:
                config = config_manager._load_config_file(config_path)
            else:
                existing_config = config_manager._find_existing_config()
                if existing_config:
                    config = config_manager._load_config_file(existing_config)
                else:
                    config = {}

        if not config:
            safe_console_print("❌ No configuration found")
            return

        if output_format == "json":
            safe_console_print(json.dumps(config, indent=2, ensure_ascii=False))
        elif output_format == "yaml":
            yaml.dump(config, click.get_text_stream("stdout"), default_flow_style=False)
        else:
            _print_config_table(config, include_defaults)

    except Exception as e:
        safe_console_print(f"❌ Failed to show configuration: {e}")
        raise click.ClickException(f"Failed to show configuration: {e}") from e


@config_group.command()
@click.option("--output", type=click.Path(path_type=Path), required=True, help="Output path for exported configuration")
@click.option("--format", "export_format", type=click.Choice(["yaml", "json"]), default="yaml", help="Export format")
@click.option("--include-defaults", is_flag=True, help="Include default values in export")
@click.option(
    "--config", "config_path", type=click.Path(exists=True, path_type=Path), help="Path to configuration file to export"
)
def export(output: Path, export_format: str, include_defaults: bool, config_path: Path = None):
    """Export configuration to file."""
    try:
        config_manager = get_config_manager()

        exported_path = config_manager.export_config(output, export_format, include_defaults)

        safe_console_print(f"✅ Configuration exported to: {exported_path}")
        safe_console_print(f"📊 Format: {export_format.upper()}")

        if include_defaults:
            safe_console_print("📝 Includes default values")
        else:
            safe_console_print("📝 Custom values only")

    except Exception as e:
        safe_console_print(f"❌ Export failed: {e}")
        raise click.ClickException(f"Configuration export failed: {e}") from e


@config_group.command()
@click.option("--from-version", required=True, help="Current configuration version")
@click.option("--to-version", required=True, help="Target configuration version")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file to migrate",
)
@click.option("--backup/--no-backup", default=True, help="Create backup before migration")
def migrate(from_version: str, to_version: str, config_path: Path = None, backup: bool = True):
    """Migrate configuration from one version to another."""
    try:
        config_manager = get_config_manager()

        safe_console_print(f"🔄 Migrating configuration: {from_version} → {to_version}")

        if backup:
            safe_console_print("💾 Backup will be created automatically")

        migrated_path = config_manager.migrate_config(from_version, to_version, config_path)

        safe_console_print(f"✅ Configuration migrated: {migrated_path}")
        safe_console_print("🔍 Please review the migrated configuration")
        safe_console_print("💡 Run 'rxiv config validate' to verify the migration")

    except Exception as e:
        safe_console_print(f"❌ Migration failed: {e}")
        raise click.ClickException(f"Configuration migration failed: {e}") from e


@config_group.command()
def list_files():
    """List all configuration files and their status."""
    try:
        config_manager = get_config_manager()

        safe_console_print("📁 Configuration Files")
        safe_console_print("=" * 50)

        config_files = config_manager.list_config_files()

        for i, file_info in enumerate(config_files, 1):
            path = file_info["path"]
            exists = file_info["exists"]

            if exists:
                status = "✅ Found"
                if "error" in file_info:
                    status = f"⚠️  Error: {file_info['error']}"
                else:
                    size = file_info.get("size", 0)
                    readable = file_info.get("readable", False)
                    writable = file_info.get("writable", False)

                    permissions = []
                    if readable:
                        permissions.append("R")
                    if writable:
                        permissions.append("W")
                    perm_str = "/".join(permissions) if permissions else "No access"

                    status = f"✅ Found ({size} bytes, {perm_str})"
            else:
                status = "❌ Not found"

            safe_console_print(f"\n{i}. {Path(path).name}")
            safe_console_print(f"   Path: {path}")
            safe_console_print(f"   Status: {status}")

        # Show which file would be used
        active_config = config_manager._find_existing_config()
        if active_config:
            safe_console_print(f"\n🎯 Active configuration: {active_config}")
        else:
            safe_console_print("\n❌ No active configuration found")
            safe_console_print("💡 Run 'rxiv config init' to create one")

    except Exception as e:
        safe_console_print(f"❌ Failed to list configuration files: {e}")
        raise click.ClickException(f"Failed to list configuration files: {e}") from e


def _print_validation_results(results: Dict[str, Any], strict: bool = False) -> None:
    """Print validation results in table format."""
    safe_console_print("📊 Configuration Validation Results")
    safe_console_print("=" * 60)

    total_errors = 0
    total_warnings = 0

    for section_name, section_result in results.items():
        section_valid = section_result.get("valid", True)
        section_errors = len(section_result.get("errors", []))
        section_warnings = len(section_result.get("warnings", []))

        total_errors += section_errors
        total_warnings += section_warnings

        # Section header
        status_icon = "✅" if section_valid else "❌"
        safe_console_print(f"\n{status_icon} {section_name.replace('_', ' ').title()}")
        safe_console_print("-" * 40)

        if section_errors == 0 and section_warnings == 0:
            safe_console_print("   No issues found")
        else:
            if section_errors > 0:
                safe_console_print(f"   🔴 Errors: {section_errors}")
                for error in section_result.get("errors", []):
                    safe_console_print(f"      • {error.message}")

            if section_warnings > 0:
                safe_console_print(f"   🟡 Warnings: {section_warnings}")
                for warning in section_result.get("warnings", []):
                    safe_console_print(f"      • {warning.message}")

    # Summary
    safe_console_print("\n📊 Summary")
    safe_console_print("=" * 20)
    safe_console_print(f"Total Errors: {total_errors}")
    safe_console_print(f"Total Warnings: {total_warnings}")

    if total_errors == 0 and total_warnings == 0:
        safe_console_print("🎉 Perfect configuration!")
    elif total_errors == 0:
        safe_console_print("✅ Configuration is valid (warnings are non-blocking)")
    else:
        safe_console_print("❌ Configuration has errors that need to be fixed")


def _print_config_table(config: Dict[str, Any], include_defaults: bool = False) -> None:
    """Print configuration in table format."""
    safe_console_print("📋 Current Configuration")
    safe_console_print("=" * 50)

    def print_nested_config(data: Dict[str, Any], prefix: str = "", level: int = 0) -> None:
        indent = "  " * level

        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                safe_console_print(f"{indent}📁 {key}:")
                print_nested_config(value, full_key, level + 1)
            elif isinstance(value, list):
                safe_console_print(f"{indent}📝 {key}: [{len(value)} items]")
                for i, item in enumerate(value[:3]):  # Show first 3 items
                    safe_console_print(f"{indent}   {i + 1}. {item}")
                if len(value) > 3:
                    safe_console_print(f"{indent}   ... and {len(value) - 3} more")
            else:
                safe_console_print(f"{indent}📝 {key}: {value}")

    print_nested_config(config)

    if not include_defaults:
        safe_console_print("\n💡 Use --include-defaults to see all configuration values")
