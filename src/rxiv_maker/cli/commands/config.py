"""CLI commands for configuration management and validation."""

from pathlib import Path
from typing import Optional

import click

from ..framework import (
    ConfigExportCommand,
    ConfigGetCommand,
    ConfigInitCommand,
    ConfigListCommand,
    ConfigMigrateCommand,
    ConfigShowCommand,
    ConfigValidateCommand,
)


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
@click.pass_context
def init(ctx: click.Context, template: str, force: bool, output: Optional[Path] = None):
    """Initialize configuration file from template."""
    command = ConfigInitCommand()
    return command.run(
        ctx, manuscript_path=None, template=template, force=force, output=str(output) if output else None
    )


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
@click.pass_context
def validate(
    ctx: click.Context, config_path: Optional[Path] = None, output_format: str = "table", strict: bool = False
):
    """Validate configuration file."""
    command = ConfigValidateCommand()
    return command.run(
        ctx,
        manuscript_path=None,
        config_path=str(config_path) if config_path else None,
        output_format=output_format,
        strict=strict,
    )


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
@click.pass_context
def get(
    ctx: click.Context,
    key: str,
    value: Optional[str] = None,
    config_path: Optional[Path] = None,
    value_type: str = "string",
):
    """Get or set configuration values."""
    command = ConfigGetCommand()
    return command.run(
        ctx,
        manuscript_path=None,
        key=key,
        value=value,
        config_path=str(config_path) if config_path else None,
        value_type=value_type,
    )


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
@click.pass_context
def show(
    ctx: click.Context, output_format: str = "table", config_path: Optional[Path] = None, include_defaults: bool = False
):
    """Show current configuration."""
    command = ConfigShowCommand()
    return command.run(
        ctx,
        manuscript_path=None,
        output_format=output_format,
        config_path=str(config_path) if config_path else None,
        include_defaults=include_defaults,
    )


@config_group.command()
@click.option("--output", type=click.Path(path_type=Path), required=True, help="Output path for exported configuration")
@click.option("--format", "export_format", type=click.Choice(["yaml", "json"]), default="yaml", help="Export format")
@click.option("--include-defaults", is_flag=True, help="Include default values in export")
@click.option(
    "--config", "config_path", type=click.Path(exists=True, path_type=Path), help="Path to configuration file to export"
)
@click.pass_context
def export(
    ctx: click.Context, output: Path, export_format: str, include_defaults: bool, config_path: Optional[Path] = None
):
    """Export configuration to file."""
    command = ConfigExportCommand()
    return command.run(
        ctx,
        manuscript_path=None,
        output=str(output),
        export_format=export_format,
        include_defaults=include_defaults,
        config_path=str(config_path) if config_path else None,
    )


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
@click.pass_context
def migrate(
    ctx: click.Context, from_version: str, to_version: str, config_path: Optional[Path] = None, backup: bool = True
):
    """Migrate configuration from one version to another."""
    command = ConfigMigrateCommand()
    return command.run(
        ctx,
        manuscript_path=None,
        from_version=from_version,
        to_version=to_version,
        config_path=str(config_path) if config_path else None,
        backup=backup,
    )


@config_group.command()
@click.pass_context
def list_files(ctx: click.Context):
    """List all configuration files and their status."""
    command = ConfigListCommand()
    return command.run(ctx, manuscript_path=None)
