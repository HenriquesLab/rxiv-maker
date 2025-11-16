"""CLI command framework for rxiv-maker.

This package provides the base infrastructure and command implementations
for the rxiv-maker CLI, organized into logical modules.
"""

from ...core.path_manager import PathManager, PathResolutionError
from .base import BaseCommand, CommandExecutionError
from .cache_commands import (
    CacheCleanupCommand,
    CacheClearCommand,
    CacheInfoCommand,
    CacheMigrateCommand,
    CacheOptimizeCommand,
    CacheSetStrategyCommand,
    CacheStatsCommand,
)
from .config_commands import (
    ConfigExportCommand,
    ConfigGetCommand,
    ConfigInitCommand,
    ConfigListCommand,
    ConfigMigrateCommand,
    ConfigShowCommand,
    ConfigValidateCommand,
)
from .content_commands import (
    BibliographyAddCommand,
    BibliographyFixCommand,
    BibliographyListCommand,
    CleanCommand,
    FiguresCommand,
    ValidationCommand,
)
from .decorators import (
    check_dependency,
    confirm_destructive_action,
    deprecated_command,
    handle_keyboard_interrupt,
    measure_time,
    requires_github,
    requires_github_auth,
    requires_github_cli,
    verbose_logging,
    with_manuscript_path,
)
from .utility_commands import (
    CheckInstallationCommand,
    CompletionCommand,
    DeprecatedInstallDepsCommand,
    VersionCommand,
)
from .workflow_commands import (
    ArxivCommand,
    BuildCommand,
    InitCommand,
    SetupCommand,
    TrackChangesCommand,
)

__all__ = [
    # Base framework
    "BaseCommand",
    "CommandExecutionError",
    "PathManager",
    "PathResolutionError",
    # Decorators
    "requires_github_cli",
    "requires_github_auth",
    "requires_github",
    "with_manuscript_path",
    "handle_keyboard_interrupt",
    "confirm_destructive_action",
    "deprecated_command",
    "verbose_logging",
    "check_dependency",
    "measure_time",
    # Cache commands
    "CacheStatsCommand",
    "CacheClearCommand",
    "CacheCleanupCommand",
    "CacheOptimizeCommand",
    "CacheInfoCommand",
    "CacheMigrateCommand",
    "CacheSetStrategyCommand",
    # Config commands
    "ConfigInitCommand",
    "ConfigValidateCommand",
    "ConfigGetCommand",
    "ConfigShowCommand",
    "ConfigExportCommand",
    "ConfigMigrateCommand",
    "ConfigListCommand",
    # Content commands
    "ValidationCommand",
    "CleanCommand",
    "BibliographyFixCommand",
    "BibliographyAddCommand",
    "BibliographyListCommand",
    "FiguresCommand",
    # Workflow commands
    "InitCommand",
    "BuildCommand",
    "ArxivCommand",
    "TrackChangesCommand",
    "SetupCommand",
    # Utility commands
    "CheckInstallationCommand",
    "VersionCommand",
    "CompletionCommand",
    "DeprecatedInstallDepsCommand",
]
