"""Configuration management for rxiv-maker CLI."""

import os
from pathlib import Path
from typing import Any

import click
from rich.console import Console

from rxiv_maker.utils.unicode_safe import (
    console_error,
    console_success,
    console_warning,
    safe_console_print,
)

console = Console()


class Config:
    """Configuration manager for rxiv-maker."""

    def __init__(self):
        """Initialize configuration manager."""
        self.config_dir = Path.home() / ".rxiv"
        self.config_file = self.config_dir / "config.toml"
        self.config_data: dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from file."""
        if not self.config_file.exists():
            self.create_default_config()
            return

        try:
            import tomllib

            with open(self.config_file, "rb") as f:
                self.config_data = tomllib.load(f)
        except Exception as e:
            console_warning(console, f"Error loading config: {e}. Using defaults.")
            self.config_data = self.get_default_config()

    def get_default_config(self) -> dict[str, Any]:
        """Get default configuration."""
        return {
            "general": {
                "default_engine": "local",
                "default_manuscript_path": "MANUSCRIPT",
                "default_output_dir": "output",
                "verbose": False,
                "check_updates": True,
            },
            "build": {
                "force_figures": False,
                "skip_validation": False,
                "auto_clean": False,
            },
            "validation": {
                "skip_doi": False,
                "detailed": False,
            },
            "figures": {
                "default_format": "png",
                "default_dpi": 300,
                "force_regeneration": False,
            },
            "bibliography": {
                "auto_fix": False,
                "cache_timeout": 30,  # days
            },
            "output": {
                "colors": True,
                "progress_bars": True,
                "emoji": True,
            },
        }

    def create_default_config(self) -> None:
        """Create default configuration file."""
        self.config_dir.mkdir(exist_ok=True)
        self.config_data = self.get_default_config()
        self.save_config()

    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            import tomli_w

            with open(self.config_file, "wb") as f:
                tomli_w.dump(self.config_data, f)
        except ImportError:
            # Fallback - create a basic TOML file manually
            content = self._dict_to_toml(self.config_data)
            with open(self.config_file, "w") as f:
                f.write(content)

    def _dict_to_toml(self, data: dict[str, Any], prefix: str = "") -> str:
        """Convert dictionary to TOML format (fallback implementation)."""
        lines = []

        for key, value in data.items():
            if isinstance(value, dict):
                section_name = f"{prefix}.{key}" if prefix else key
                lines.append(f"[{section_name}]")
                for subkey, subvalue in value.items():
                    lines.append(f"{subkey} = {self._format_value(subvalue)}")
                lines.append("")
            else:
                lines.append(f"{key} = {self._format_value(value)}")

        return "\n".join(lines)

    def _format_value(self, value: Any) -> str:
        """Format value for TOML output."""
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return "true" if value else "false"
        else:
            return str(value)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        # Support dot notation (e.g., "general.default_engine")
        keys = key.split(".")
        value = self.config_data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        keys = key.split(".")
        data = self.config_data

        # Navigate to the correct nested dict
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]

        # Set the value
        data[keys[-1]] = value
        self.save_config()

    def show(self) -> None:
        """Show current configuration."""
        from rich.table import Table

        table = Table(title="Rxiv-Maker Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Description", style="yellow")

        descriptions = {
            "general.default_engine": "Default execution engine (local/docker)",
            "general.default_manuscript_path": "Default manuscript directory",
            "general.default_output_dir": "Default output directory",
            "general.verbose": "Enable verbose output by default",
            "general.check_updates": "Check for package updates automatically",
            "build.force_figures": "Force figure regeneration by default",
            "build.skip_validation": "Skip validation by default",
            "build.auto_clean": "Auto-clean before building",
            "validation.skip_doi": "Skip DOI validation by default",
            "validation.detailed": "Show detailed validation by default",
            "figures.default_format": "Default figure format",
            "figures.default_dpi": "Default figure DPI",
            "figures.force_regeneration": "Force figure regeneration by default",
            "bibliography.auto_fix": "Auto-fix bibliography issues",
            "bibliography.cache_timeout": "Bibliography cache timeout (days)",
            "output.colors": "Enable colored output",
            "output.progress_bars": "Show progress bars",
            "output.emoji": "Show emoji in output",
        }

        def add_section(section_name: str, section_data: dict[str, Any]) -> None:
            for key, value in section_data.items():
                full_key = f"{section_name}.{key}"
                description = descriptions.get(full_key, "")
                table.add_row(full_key, str(value), description)

        for section_name, section_data in self.config_data.items():
            if isinstance(section_data, dict):
                add_section(section_name, section_data)

        safe_console_print(console, table)
        safe_console_print(console, f"\nConfig file: {self.config_file}", style="blue")


# Global configuration instance
config = Config()


@click.group()
def config_cmd():
    """Configuration management commands."""
    pass


@config_cmd.command()
def show():
    """Show current configuration."""
    config.show()


@config_cmd.command()
@click.argument("key")
@click.argument("value")
def set(key: str, value: str):
    """Set configuration value."""
    # Try to parse value as appropriate type
    parsed_value: Any
    if value.lower() in ("true", "false"):
        parsed_value = value.lower() == "true"
    elif value.isdigit():
        parsed_value = int(value)
    else:
        parsed_value = value

    config.set(key, parsed_value)
    console_success(console, f"Set {key} = {parsed_value}")


@config_cmd.command()
@click.argument("key")
def get(key: str):
    """Get configuration value."""
    value = config.get(key)
    if value is not None:
        safe_console_print(console, f"{key} = {value}", style="green")
    else:
        console_error(console, f"Key '{key}' not found")


@config_cmd.command()
def reset():
    """Reset configuration to defaults."""
    if click.confirm("Are you sure you want to reset all configuration to defaults?"):
        config.config_data = config.get_default_config()
        config.save_config()
        console_success(console, "Configuration reset to defaults")


@config_cmd.command()
def edit():
    """Edit configuration file in default editor."""
    editor = os.environ.get("EDITOR", "nano")
    try:
        click.edit(filename=str(config.config_file), editor=editor)
        console_success(console, "Configuration file edited")
    except Exception as e:
        console_error(console, f"Error editing config: {e}")
