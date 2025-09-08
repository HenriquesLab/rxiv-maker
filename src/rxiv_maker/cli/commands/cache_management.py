"""CLI commands for cache management and optimization.

This module provides commands for:
- Viewing cache statistics
- Clearing caches
- Optimizing cache performance
- Managing Docker build caches
"""

from pathlib import Path
from typing import Optional

import click

from ..framework import (
    CacheCleanupCommand,
    CacheClearCommand,
    CacheInfoCommand,
    CacheMigrateCommand,
    CacheOptimizeCommand,
    CacheSetStrategyCommand,
    CacheStatsCommand,
)


@click.group(name="cache")
def cache_group():
    """Cache management and optimization commands."""
    pass


@cache_group.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format for cache statistics",
)
@click.option(
    "--manuscript",
    type=click.Path(exists=True, file_okay=False),
    help="Manuscript directory to analyze (default: current directory)",
)
@click.pass_context
def stats(ctx: click.Context, output_format: str, manuscript: Optional[str] = None):
    """Show cache statistics and performance metrics."""
    command = CacheStatsCommand()
    return command.run(ctx, manuscript_path=manuscript, output_format=output_format)


@cache_group.command()
@click.option(
    "--type",
    "cache_type",
    type=click.Choice(["all", "bibliography", "figures", "system", "builds"]),
    default="all",
    help="Type of cache to clear",
)
@click.option(
    "--manuscript",
    type=click.Path(exists=True, file_okay=False),
    help="Manuscript directory (default: current directory)",
)
@click.option("--confirm", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def clear(ctx: click.Context, cache_type: str, manuscript: Optional[str] = None, confirm: bool = False):
    """Clear cache entries."""
    command = CacheClearCommand()
    return command.run(ctx, manuscript_path=manuscript, cache_type=cache_type, confirm=confirm)


@cache_group.command()
@click.option("--max-age-hours", default=168, help="Maximum age in hours for cache entries (default: 168 = 1 week)")
@click.option("--dry-run", is_flag=True, help="Show what would be cleaned without actually doing it")
@click.pass_context
def cleanup(ctx: click.Context, max_age_hours: int, dry_run: bool):
    """Clean up expired cache entries."""
    command = CacheCleanupCommand()
    return command.run(ctx, manuscript_path=None, max_age_hours=max_age_hours, dry_run=dry_run)


@cache_group.command()
@click.option(
    "--dockerfile",
    type=click.Path(exists=True, path_type=Path),
    help="Dockerfile to analyze (deprecated - Docker engine removed)",
)
@click.pass_context
def optimize(ctx: click.Context, dockerfile: Optional[Path] = None):
    """Analyze and suggest cache optimization opportunities."""
    command = CacheOptimizeCommand()
    return command.run(ctx, manuscript_path=None, dockerfile=str(dockerfile) if dockerfile else None)


@cache_group.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format for cache information",
)
@click.pass_context
def info(ctx: click.Context, output_format: str):
    """Show cache location information."""
    command = CacheInfoCommand()
    return command.run(ctx, manuscript_path=None, output_format=output_format)


@cache_group.command()
@click.option(
    "--target",
    type=click.Choice(["global", "local"]),
    required=True,
    help="Target cache location (global or manuscript-local)",
)
@click.option("--force", is_flag=True, help="Force migration without confirmation")
@click.option("--dry-run", is_flag=True, help="Show what would be migrated without actually doing it")
@click.pass_context
def migrate(ctx: click.Context, target: str, force: bool, dry_run: bool):
    """Migrate cache between global and manuscript-local storage."""
    command = CacheMigrateCommand()
    return command.run(ctx, manuscript_path=None, target=target, force=force, dry_run=dry_run)


@cache_group.command()
@click.option(
    "--strategy",
    type=click.Choice(["global", "local", "hybrid"]),
    required=True,
    help="Cache strategy to set (global, local, or hybrid)",
)
@click.option("--migrate-now", is_flag=True, help="Immediately migrate existing cache to new strategy")
@click.pass_context
def set_strategy(ctx: click.Context, strategy: str, migrate_now: bool):
    """Set cache strategy via environment variable."""
    command = CacheSetStrategyCommand()
    return command.run(ctx, manuscript_path=None, strategy=strategy, migrate_now=migrate_now)
