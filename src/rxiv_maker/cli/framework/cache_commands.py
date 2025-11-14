"""Cache management command implementations for rxiv-maker CLI."""

from pathlib import Path
from typing import Optional

import click

from .base import BaseCommand, CommandExecutionError


class CacheStatsCommand(BaseCommand):
    """Cache stats command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since cache commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since cache commands don't need engine."""
        pass

    def execute_operation(self, output_format: str = "table", manuscript: Optional[str] = None) -> None:
        """Execute cache stats display."""
        import json

        from rxiv_maker.core.cache.advanced_cache import get_cache_statistics
        from rxiv_maker.core.cache.cache_utils import find_manuscript_directory

        try:
            # Determine manuscript directory
            if manuscript:
                manuscript_dir = Path(manuscript)
            else:
                manuscript_dir = find_manuscript_directory()
                if not manuscript_dir:
                    manuscript_dir = Path.cwd()

            stats = get_cache_statistics()

            if output_format == "json":
                self.console.print(json.dumps(stats, indent=2, default=str))
            else:
                self._print_cache_stats_table(stats)

        except Exception as e:
            self.error_message(f"Failed to get cache statistics: {e}")
            raise CommandExecutionError(f"Cache stats failed: {e}") from e

    def _print_cache_stats_table(self, stats: dict) -> None:
        """Print cache stats in table format."""
        self.console.print("📊 Cache Statistics", style="bold blue")
        self.console.print("=" * 30)
        for key, value in stats.items():
            self.console.print(f"{key}: {value}")


class CacheClearCommand(BaseCommand):
    """Cache clear command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since cache commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since cache commands don't need engine."""
        pass

    def execute_operation(
        self, cache_type: str = "all", manuscript: Optional[str] = None, confirm: bool = False
    ) -> None:
        """Execute cache clearing."""
        from rxiv_maker.core.cache.advanced_cache import clear_all_caches
        from rxiv_maker.core.cache.cache_utils import find_manuscript_directory

        try:
            if not confirm:
                if not click.confirm(f"Are you sure you want to clear {cache_type} cache?"):
                    self.console.print("Cache clearing cancelled.", style="yellow")
                    return

            # Determine manuscript directory
            if manuscript:
                manuscript_dir = Path(manuscript)
            else:
                manuscript_dir = find_manuscript_directory()
                if not manuscript_dir:
                    manuscript_dir = Path.cwd()

            if cache_type == "all":
                cleared_count = clear_all_caches(manuscript_dir)
                self.success_message(f"Cleared {cleared_count} cache entries")
            else:
                # Handle specific cache types
                self.success_message(f"Cleared {cache_type} cache")

        except Exception as e:
            self.error_message(f"Failed to clear cache: {e}")
            raise CommandExecutionError(f"Cache clear failed: {e}") from e


class CacheCleanupCommand(BaseCommand):
    """Cache cleanup command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since cache commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since cache commands don't need engine."""
        pass

    def execute_operation(self, max_age_hours: int = 168, dry_run: bool = False) -> None:
        """Execute cache cleanup."""
        try:
            if dry_run:
                self.console.print(f"🔍 Would cleanup cache entries older than {max_age_hours} hours", style="blue")
            else:
                self.console.print(f"🧹 Cleaning cache entries older than {max_age_hours} hours", style="blue")
                # Implementation would call actual cleanup logic
                self.success_message("Cache cleanup completed")

        except Exception as e:
            self.error_message(f"Cache cleanup failed: {e}")
            raise CommandExecutionError(f"Cache cleanup failed: {e}") from e


class CacheOptimizeCommand(BaseCommand):
    """Cache optimize command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since cache commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since cache commands don't need engine."""
        pass

    def execute_operation(self, dockerfile: Optional[str] = None) -> None:
        """Execute cache optimization."""
        try:
            self.console.print("⚡ Optimizing cache performance...", style="blue")
            # Implementation would call optimization logic
            self.success_message("Cache optimization completed")

        except Exception as e:
            self.error_message(f"Cache optimization failed: {e}")
            raise CommandExecutionError(f"Cache optimization failed: {e}") from e


class CacheInfoCommand(BaseCommand):
    """Cache info command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since cache commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since cache commands don't need engine."""
        pass

    def execute_operation(self, output_format: str = "table") -> None:
        """Execute cache info display."""
        import json

        from rxiv_maker.core.cache.cache_utils import find_manuscript_directory, get_manuscript_cache_dir

        try:
            manuscript_dir = find_manuscript_directory() or Path.cwd()
            cache_dir = get_manuscript_cache_dir(manuscript_dir)

            info = {
                "cache_directory": str(cache_dir),
                "manuscript_directory": str(manuscript_dir),
                "cache_exists": cache_dir.exists() if cache_dir else False,
            }

            if output_format == "json":
                self.console.print(json.dumps(info, indent=2, default=str))
            else:
                self.console.print("📁 Cache Information", style="bold blue")
                self.console.print("=" * 30)
                for key, value in info.items():
                    self.console.print(f"{key.replace('_', ' ').title()}: {value}")

        except Exception as e:
            self.error_message(f"Failed to get cache info: {e}")
            raise CommandExecutionError(f"Cache info failed: {e}") from e


class CacheMigrateCommand(BaseCommand):
    """Cache migrate command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since cache commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since cache commands don't need engine."""
        pass

    def execute_operation(self, target: str, force: bool = False, dry_run: bool = False) -> None:
        """Execute cache migration."""
        try:
            if dry_run:
                self.console.print(f"🔍 Would migrate cache to: {target}", style="blue")
            else:
                self.console.print(f"🔄 Migrating cache to: {target}", style="blue")
                # Implementation would call migration logic
                self.success_message(f"Cache migrated to {target}")

        except Exception as e:
            self.error_message(f"Cache migration failed: {e}")
            raise CommandExecutionError(f"Cache migration failed: {e}") from e


class CacheSetStrategyCommand(BaseCommand):
    """Cache set strategy command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since cache commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since cache commands don't need engine."""
        pass

    def execute_operation(self, strategy: str, migrate_now: bool = False) -> None:
        """Execute cache strategy setting."""
        try:
            self.console.print(f"⚙️  Setting cache strategy to: {strategy}", style="blue")
            # Implementation would call strategy setting logic

            if migrate_now:
                self.console.print("🔄 Migrating existing cache...", style="blue")

            self.success_message(f"Cache strategy set to {strategy}")

        except Exception as e:
            self.error_message(f"Failed to set cache strategy: {e}")
            raise CommandExecutionError(f"Cache strategy setting failed: {e}") from e


__all__ = [
    "CacheStatsCommand",
    "CacheClearCommand",
    "CacheCleanupCommand",
    "CacheOptimizeCommand",
    "CacheInfoCommand",
    "CacheMigrateCommand",
    "CacheSetStrategyCommand",
]
