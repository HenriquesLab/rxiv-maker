"""CLI commands for cache management and optimization.

This module provides commands for:
- Viewing cache statistics
- Clearing caches
- Optimizing cache performance
- Managing Docker build caches
"""

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import click

from rxiv_maker.core.cache.advanced_cache import clear_all_caches, get_cache_statistics
from rxiv_maker.core.cache.bibliography_cache import get_bibliography_cache

from ...docker.optimization import DockerBuildOptimizer
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

        # Docker build cache
        docker_optimizer = DockerBuildOptimizer()
        docker_stats = {}
        try:
            build_cache_stats = docker_optimizer.cache.get_stats()
            context_cache_stats = docker_optimizer.build_context_cache.get_stats()
            docker_stats = {"build_cache": build_cache_stats, "context_cache": context_cache_stats}
        except Exception as e:
            logger.debug(f"Could not get Docker cache stats: {e}")

        if docker_stats:
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

        if cache_type in ["all", "docker"]:
            docker_optimizer = DockerBuildOptimizer()
            docker_cleanup = docker_optimizer.cleanup_build_cache()
            cleared_counts["docker"] = docker_cleanup

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

        # Docker cache cleanup
        docker_optimizer = DockerBuildOptimizer()
        if not dry_run:
            docker_cleanup = docker_optimizer.cleanup_build_cache(max_age_hours)
            cleanup_results["docker"] = docker_cleanup
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
        docker_optimizer = DockerBuildOptimizer()

        # Get current cache statistics for analysis
        all_stats = {}

        # Bibliography cache analysis
        bib_cache = get_bibliography_cache()
        bib_stats = bib_cache.get_cache_statistics()
        all_stats["bibliography"] = bib_stats

        # Docker optimization analysis
        if dockerfile:
            docker_analysis = docker_optimizer.optimize_multi_stage_build(dockerfile)
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
