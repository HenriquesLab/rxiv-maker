"""CLI commands for cache management and optimization.

This module provides commands for:
- Viewing cache statistics
- Clearing caches
- Optimizing cache performance
- Managing Docker build caches
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import click

from rxiv_maker.core.cache.advanced_cache import clear_all_caches, get_cache_statistics
from rxiv_maker.core.cache.bibliography_cache import get_bibliography_cache
from rxiv_maker.core.cache.cache_utils import (
    find_manuscript_directory,
    get_manuscript_cache_dir,
    get_manuscript_name,
)

# Docker optimization removed - engines deprecated
from ...utils.platform import safe_console_print

try:
    from rich.console import Console

    console: Optional[Console] = Console()
except ImportError:
    console = None

logger = logging.getLogger(__name__)


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
    help="Output format for statistics",
)
@click.option("--manuscript", help="Show statistics for specific manuscript")
def stats(output_format: str, manuscript: Optional[str] = None):
    """Show cache statistics and performance metrics."""
    try:
        # Collect all cache statistics
        all_stats = {}

        # Global advanced caches
        global_stats = get_cache_statistics()
        if global_stats:
            all_stats["global_caches"] = global_stats

        # Bibliography cache
        bib_cache = get_bibliography_cache(manuscript)
        bib_stats = bib_cache.get_cache_statistics()
        all_stats["bibliography_cache"] = bib_stats

        # Add cache configuration info
        cache_config_info = bib_cache.get_cache_config_info()
        all_stats["cache_configuration"] = cache_config_info

        # Check if cache is in fallback mode and add warning
        if hasattr(bib_cache, "_fallback_mode") and bib_cache._fallback_mode:
            all_stats["warning"] = {
                "message": "Bibliography cache is using global fallback due to manuscript-local strategy without manuscript directory",
                "recommendation": "Navigate to a manuscript directory or use 'rxiv cache set-strategy global'",
            }

        # Docker build cache (deprecated)
        docker_stats = {"note": "Docker engine deprecated - use docker-rxiv-maker for containers"}
        all_stats["docker_cache"] = docker_stats

        if output_format == "json":
            safe_console_print(console, json.dumps(all_stats, indent=2))
        else:
            _print_stats_table(all_stats)

    except Exception as e:
        safe_console_print(console, f"Error getting cache statistics: {e}")
        raise click.ClickException(f"Failed to get cache statistics: {e}") from e


@cache_group.command()
@click.option(
    "--type",
    "cache_type",
    type=click.Choice(["all", "global", "bibliography", "docker"]),
    default="all",
    help="Type of cache to clear",
)
@click.option("--manuscript", help="Clear caches for specific manuscript only")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
def clear(cache_type: str, manuscript: Optional[str] = None, confirm: bool = False):
    """Clear cache entries."""
    if not confirm:
        cache_desc = cache_type if cache_type != "all" else "all"
        manuscript_desc = f" for manuscript '{manuscript}'" if manuscript else ""

        if not click.confirm(f"Are you sure you want to clear {cache_desc} caches{manuscript_desc}?"):
            safe_console_print(console, "Cache clear cancelled.")
            return

    cleared_counts: Dict[str, Any] = {}

    try:
        if cache_type in ["all", "global"]:
            clear_all_caches()
            cleared_counts["global"] = "cleared"

        if cache_type in ["all", "bibliography"]:
            bib_cache = get_bibliography_cache(manuscript)
            bib_cache.clear_all_caches()
            cleared_counts["bibliography"] = "cleared"

            # Check if cache was in fallback mode and show warning
            if hasattr(bib_cache, "_fallback_mode") and bib_cache._fallback_mode:
                safe_console_print(
                    console,
                    "⚠️  Note: Bibliography cache was using global fallback due to manuscript-local strategy without manuscript directory",
                )

        if cache_type in ["all", "docker"]:
            # Docker cache cleanup deprecated
            cleared_counts["docker"] = {"note": "Docker engine deprecated"}

        safe_console_print(console, f"✅ Cache clear completed: {cleared_counts}")

    except Exception as e:
        safe_console_print(console, f"❌ Error clearing caches: {e}")
        raise click.ClickException(f"Failed to clear caches: {e}") from e


@cache_group.command()
@click.option("--max-age-hours", type=int, default=168, help="Maximum age in hours for cleanup (default: 168 = 1 week)")
@click.option("--dry-run", is_flag=True, help="Show what would be cleaned up without actually doing it")
def cleanup(max_age_hours: int, dry_run: bool):
    """Clean up expired cache entries."""
    try:
        cleanup_results = {}

        # Bibliography cache cleanup
        bib_cache = get_bibliography_cache()
        if not dry_run:
            bib_cleanup = bib_cache.cleanup_all_caches(max_age_hours)
            cleanup_results["bibliography"] = bib_cleanup
        else:
            # For dry run, estimate cleanup
            bib_stats = bib_cache.get_cache_statistics()
            estimated = sum(stats.get("expired_entries", 0) for stats in bib_stats.values() if isinstance(stats, dict))
            cleanup_results["bibliography"] = {"estimated_cleanup": estimated}

        # Check if cache was in fallback mode and show warning
        if hasattr(bib_cache, "_fallback_mode") and bib_cache._fallback_mode:
            safe_console_print(
                console,
                "⚠️  Note: Bibliography cache is using global fallback due to manuscript-local strategy without manuscript directory",
            )

        # Docker cache cleanup (deprecated)
        if not dry_run:
            cleanup_results["docker"] = {"note": "Docker engine deprecated"}
        else:
            cleanup_results["docker"] = {"estimated_cleanup": 0}

        action = "Would clean up" if dry_run else "Cleaned up"
        safe_console_print(console, f"✅ {action}: {cleanup_results}")

    except Exception as e:
        safe_console_print(console, f"❌ Error during cleanup: {e}")
        raise click.ClickException(f"Failed to cleanup caches: {e}") from e


@cache_group.command()
@click.option(
    "--dockerfile", type=click.Path(exists=True, path_type=Path), help="Path to Dockerfile for optimization analysis"
)
def optimize(dockerfile: Optional[Path] = None):
    """Analyze and suggest cache optimization opportunities."""
    try:
        # Docker optimization deprecated
        # For containerized builds, use docker-rxiv-maker repository

        # Get current cache statistics for analysis
        all_stats = {}

        # Bibliography cache analysis
        bib_cache = get_bibliography_cache()
        bib_stats = bib_cache.get_cache_statistics()
        all_stats["bibliography"] = bib_stats

        # Docker optimization analysis (deprecated)
        if dockerfile:
            docker_analysis = {"note": "Docker optimization deprecated - use docker-rxiv-maker for containers"}
            all_stats["docker_build_analysis"] = docker_analysis

        # Generate optimization recommendations
        recommendations = _generate_optimization_recommendations(all_stats)

        safe_console_print(console, "🔍 Cache Optimization Analysis:")
        safe_console_print(console, "=" * 50)

        for category, recs in recommendations.items():
            safe_console_print(console, f"\n📊 {category.replace('_', ' ').title()}:")
            for rec in recs:
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec.get("priority", "low"), "🔵")
                safe_console_print(console, f"  {priority_icon} {rec['description']}")

    except Exception as e:
        safe_console_print(console, f"❌ Error during optimization analysis: {e}")
        raise click.ClickException(f"Failed to analyze cache optimization: {e}") from e


def _print_stats_table(stats: Dict[str, Any]) -> None:
    """Print cache statistics in table format."""
    safe_console_print(console, "📊 Cache Statistics")
    safe_console_print(console, "=" * 60)

    for category, category_stats in stats.items():
        safe_console_print(console, f"\n🔹 {category.replace('_', ' ').title()}")
        safe_console_print(console, "-" * 40)

        if isinstance(category_stats, dict):
            for cache_name, cache_stats in category_stats.items():
                if isinstance(cache_stats, dict):
                    safe_console_print(console, f"\n  📁 {cache_name}")

                    # Key metrics to display
                    key_metrics: List[Tuple[str, str, Callable[[Any], str]]] = [
                        ("hit_rate", "Hit Rate", lambda x: f"{x:.1%}"),
                        ("memory_entries", "Memory Entries", str),
                        ("disk_size_mb", "Disk Size (MB)", lambda x: f"{x:.1f}"),
                        ("total_entries", "Total Entries", str),
                        ("memory_hits", "Memory Hits", str),
                        ("disk_hits", "Disk Hits", str),
                        ("misses", "Misses", str),
                    ]

                    for key, label, formatter in key_metrics:
                        if key in cache_stats and cache_stats[key] is not None:
                            try:
                                value = formatter(cache_stats[key])
                                safe_console_print(console, f"    {label}: {value}")
                            except (ValueError, TypeError) as e:
                                safe_console_print(console, f"    {label}: <formatting error: {e}>")


def _generate_optimization_recommendations(stats: Dict[str, Any]) -> Dict[str, list]:
    """Generate optimization recommendations based on cache statistics."""
    recommendations: Dict[str, List[Dict[str, str]]] = {"performance": [], "storage": [], "configuration": []}

    # Analyze bibliography cache performance
    if "bibliography" in stats:
        bib_stats = stats["bibliography"]

        for cache_name, cache_data in bib_stats.items():
            if not isinstance(cache_data, dict):
                continue

            hit_rate = cache_data.get("hit_rate", 0)
            if hit_rate < 0.5:
                recommendations["performance"].append(
                    {
                        "priority": "medium",
                        "description": (
                            f"Low hit rate ({hit_rate:.1%}) in {cache_name} - consider increasing cache size or TTL"
                        ),
                    }
                )

            disk_size_mb = cache_data.get("disk_size_mb", 0)
            if disk_size_mb > 100:
                recommendations["storage"].append(
                    {
                        "priority": "medium",
                        "description": (
                            f"Large {cache_name} cache ({disk_size_mb:.1f}MB) - consider cleanup or compression"
                        ),
                    }
                )

            memory_entries = cache_data.get("memory_entries", 0)
            total_entries = cache_data.get("total_entries", memory_entries) or memory_entries
            if total_entries > 0 and memory_entries < total_entries * 0.3:
                recommendations["configuration"].append(
                    {
                        "priority": "low",
                        "description": (
                            f"Low memory utilization in {cache_name} - consider increasing memory cache size"
                        ),
                    }
                )

    # Analyze Docker build optimization
    if "docker_build_analysis" in stats:
        docker_analysis = stats["docker_build_analysis"]

        for suggestion in docker_analysis.get("suggestions", []):
            category = "performance" if suggestion.get("type") == "layer_optimization" else "configuration"
            recommendations[category].append(
                {
                    "priority": suggestion.get("priority", "low"),
                    "description": f"Docker: {suggestion.get('description', 'Unknown optimization')}",
                }
            )

    # General recommendations if no specific issues found
    if all(len(recs) == 0 for recs in recommendations.values()):
        recommendations["performance"].append(
            {"priority": "low", "description": "Cache system is performing well - no immediate optimizations needed"}
        )

    return recommendations


@cache_group.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format for information",
)
def info(output_format: str):
    """Show cache location information."""
    try:
        manuscript_dir = find_manuscript_directory()
        manuscript_name = get_manuscript_name(manuscript_dir)

        if manuscript_dir is None:
            # Not in manuscript directory
            location_info = {
                "manuscript_dir": None,
                "manuscript_cache": None,
                "active_cache": "❌ No manuscript directory found",
                "status": "error",
                "message": "You must be in a manuscript directory (containing 00_CONFIG.yml) to use cache.",
            }
        else:
            cache_dir = get_manuscript_cache_dir()
            location_info = {
                "manuscript_dir": str(manuscript_dir),
                "manuscript_cache": str(cache_dir),
                "active_cache": str(cache_dir),
                "manuscript_name": manuscript_name,
                "status": "ok",
                "message": "Using manuscript-local cache",
            }

        if output_format == "json":
            safe_console_print(console, json.dumps(location_info, indent=2))
        else:
            # Simple table format output
            safe_console_print(console, "Cache Information:")
            for key, value in location_info.items():
                safe_console_print(console, f"  {key}: {value}")

    except Exception as e:
        safe_console_print(console, f"❌ Error getting cache information: {e}")
        raise click.ClickException(f"Failed to get cache information: {e}") from e


@cache_group.command()
@click.option(
    "--target",
    type=click.Choice(["manuscript-local", "global", "auto"]),
    default="auto",
    help="Target cache strategy",
)
@click.option("--force", is_flag=True, help="Force migration, overwriting existing files")
@click.option("--dry-run", is_flag=True, help="Show what would be migrated without doing it")
def migrate(target: str, force: bool, dry_run: bool):
    """Migrate cache between global and manuscript-local storage."""
    try:
        # Cache migration functionality temporarily disabled
        migration_results = {"action": "no_migration_needed", "message": "Cache migration functionality not available"}

        action_text = "Would migrate" if dry_run else "Migrated"

        if migration_results["action"] == "no_migration_needed":
            safe_console_print(
                console, f"ℹ️  No migration needed: {migration_results.get('message', 'Already using target strategy')}"
            )
        elif migration_results["migration_results"] and migration_results["migration_results"]["success"]:
            migrated_count = migration_results["migration_results"]["migrated_count"]
            safe_console_print(console, f"✅ {action_text} {migrated_count} cache files successfully")

            if migration_results["migration_results"]["migrated_files"]:
                safe_console_print(console, "\nMigrated cache types:")
                for file_info in migration_results["migration_results"]["migrated_files"]:
                    action_icon = "📋" if dry_run else "✅"
                    safe_console_print(console, f"  {action_icon} {file_info['type']}: {file_info['file_count']} files")
        else:
            error_msg = migration_results.get("migration_results", {}).get("error", "Unknown error")
            safe_console_print(console, f"❌ Migration failed: {error_msg}")

    except Exception as e:
        safe_console_print(console, f"❌ Error during migration: {e}")
        raise click.ClickException(f"Failed to migrate cache: {e}") from e


@cache_group.command()
@click.argument("strategy", type=click.Choice(["manuscript-local", "global"]))
@click.option("--migrate-now", is_flag=True, help="Automatically migrate existing cache to new strategy")
def set_strategy(strategy: str, migrate_now: bool):
    """Set cache strategy via environment variable."""
    import os

    try:
        # Set environment variable
        os.environ["RXIV_CACHE_STRATEGY"] = strategy

        safe_console_print(console, f"✅ Cache strategy set to: {strategy}")
        safe_console_print(console, "💡 To make this permanent, add to your shell profile:")
        safe_console_print(console, f"   export RXIV_CACHE_STRATEGY={strategy}")

        if migrate_now:
            safe_console_print(console, "\n🔄 Migrating existing cache...")
            # Cache migration functionality temporarily disabled
            migration_results = {"action": "no_migration_needed", "migration_results": {"success": False}}

            if migration_results["migration_results"] and migration_results["migration_results"]["success"]:
                migrated_count = migration_results["migration_results"]["migrated_count"]
                safe_console_print(console, f"✅ Migrated {migrated_count} cache files to new strategy")
            elif migration_results["action"] == "no_migration_needed":
                safe_console_print(console, "ℹ️  No cache migration needed")
            else:
                safe_console_print(console, "⚠️  Cache migration encountered issues")

    except Exception as e:
        safe_console_print(console, f"❌ Error setting cache strategy: {e}")
        raise click.ClickException(f"Failed to set cache strategy: {e}") from e


def _print_cache_info_table(cache_config: Dict[str, Any], location_info: Dict[str, Any]) -> None:
    """Print cache information in table format."""
    safe_console_print(console, "🗂️  Cache Configuration & Location Information")
    safe_console_print(console, "=" * 70)

    # Strategy information
    safe_console_print(console, f"\n🎯 Cache Strategy: {cache_config['strategy']}")
    safe_console_print(console, f"📍 Strategy Source: {cache_config['strategy_source']}")

    if cache_config.get("environment_override"):
        safe_console_print(console, f"🔧 Environment Override: {cache_config['environment_override']}")

    if cache_config.get("manuscript_config"):
        safe_console_print(console, f"📝 Manuscript Config: {cache_config['manuscript_config']}")

    # Location information
    safe_console_print(console, "\n📁 Cache Locations:")
    safe_console_print(console, "-" * 40)

    if cache_config.get("manuscript_dir"):
        safe_console_print(
            console, f"📖 Manuscript: {cache_config['manuscript_name']} ({cache_config['manuscript_dir']})"
        )
    else:
        safe_console_print(console, "📖 Manuscript: Not in manuscript directory")

    active_icon = "🎯" if location_info["is_manuscript_local"] else "🌐"
    safe_console_print(console, f"{active_icon} Active Cache: {location_info['active_cache']}")

    if location_info["manuscript_cache"]:
        status = "✅ Available" if location_info["is_manuscript_local"] else "📦 Available (not active)"
        safe_console_print(console, f"📝 Manuscript Cache: {location_info['manuscript_cache']} - {status}")

    safe_console_print(console, f"🌐 Global Cache: {location_info['global_cache']}")

    # Show warning message if present
    if location_info.get("status") == "warning" and location_info.get("message"):
        safe_console_print(console, f"\n⚠️  Warning: {location_info['message']}")

    # Environment info
    env_strategy = os.environ.get("RXIV_CACHE_STRATEGY")
    if env_strategy:
        safe_console_print(console, f"\n🔧 Environment Variable: RXIV_CACHE_STRATEGY={env_strategy}")
    else:
        safe_console_print(console, "\n🔧 Environment Variable: Not set (using default)")

    # Usage tips
    safe_console_print(console, "\n💡 Usage Tips:")
    safe_console_print(console, "   • Use 'rxiv cache migrate' to switch between strategies")
    safe_console_print(console, "   • Use 'rxiv cache set-strategy manuscript-local|global'")
    safe_console_print(console, "   • Manuscript-local: Cache travels with your project")
    safe_console_print(console, "   • Global: Cache shared across all manuscripts")
