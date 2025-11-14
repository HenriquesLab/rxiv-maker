"""Centralized CLI command framework for rxiv-maker.

This module provides a base class and common patterns for CLI commands,
reducing duplication and ensuring consistent error handling, progress reporting,
and path management across all commands.

All command implementations have been organized into specialized modules:
- framework.base: BaseCommand and CommandExecutionError
- framework.cache_commands: Cache management commands
- framework.config_commands: Configuration management commands
- framework.content_commands: Content and bibliography commands
- framework.workflow_commands: Workflow commands (init, build, arxiv, etc.)
- framework.utility_commands: Utility commands (version, check-installation, etc.)
"""

import click

# Import all command classes from specialized modules
from .framework import (
    ArxivCommand,
    BaseCommand,
    BibliographyAddCommand,
    BibliographyFixCommand,
    BibliographyListCommand,
    BuildCommand,
    CacheCleanupCommand,
    CacheClearCommand,
    CacheInfoCommand,
    CacheMigrateCommand,
    CacheOptimizeCommand,
    CacheSetStrategyCommand,
    CacheStatsCommand,
    CheckInstallationCommand,
    CleanCommand,
    CommandExecutionError,
    CompletionCommand,
    ConfigExportCommand,
    ConfigGetCommand,
    ConfigInitCommand,
    ConfigListCommand,
    ConfigMigrateCommand,
    ConfigShowCommand,
    ConfigValidateCommand,
    DeprecatedInstallDepsCommand,
    FiguresCommand,
    InitCommand,
    SetupCommand,
    TrackChangesCommand,
    ValidationCommand,
    VersionCommand,
)


def create_command_from_framework(command_class, add_manuscript_arg=True, **click_options):
    """Decorator factory to create Click commands from framework classes.

    Args:
        command_class: BaseCommand subclass
        add_manuscript_arg: Whether to add manuscript_path argument
        **click_options: Additional Click command options

    Returns:
        Click command decorator
    """

    def decorator(func):
        def wrapper(ctx, manuscript_path=None, **kwargs):
            command = command_class()
            return command.run(ctx, manuscript_path, **kwargs)

        # Apply Click decorators
        wrapper = click.pass_context(wrapper)
        if add_manuscript_arg:
            wrapper = click.argument("manuscript_path", type=click.Path(exists=True, file_okay=False), required=False)(
                wrapper
            )

        for option, config in click_options.items():
            wrapper = click.option(option, **config)(wrapper)

        return click.command()(wrapper)

    return decorator


# Example usage - replace existing command definitions:
# @create_command_from_framework(
#     ValidationCommand,
#     **{
#         "--detailed/-d": {"is_flag": True, "help": "Show detailed validation report"},
#         "--no-doi": {"is_flag": True, "help": "Skip DOI validation"}
#     }
# )
# def validate(ctx, manuscript_path, detailed, no_doi):
#     """Validate manuscript structure and content."""
#     pass


# Export the framework components
__all__ = [
    "BaseCommand",
    "CommandExecutionError",
    "ValidationCommand",
    "CleanCommand",
    "InitCommand",
    "CheckInstallationCommand",
    "BuildCommand",
    "VersionCommand",
    "CompletionCommand",
    "DeprecatedInstallDepsCommand",
    "ArxivCommand",
    "TrackChangesCommand",
    "BibliographyFixCommand",
    "BibliographyAddCommand",
    "BibliographyListCommand",
    "SetupCommand",
    "ConfigInitCommand",
    "ConfigValidateCommand",
    "ConfigGetCommand",
    "ConfigShowCommand",
    "ConfigExportCommand",
    "ConfigMigrateCommand",
    "ConfigListCommand",
    "FiguresCommand",
    "CacheStatsCommand",
    "CacheClearCommand",
    "CacheCleanupCommand",
    "CacheOptimizeCommand",
    "CacheInfoCommand",
    "CacheMigrateCommand",
    "CacheSetStrategyCommand",
    "create_command_from_framework",
]
