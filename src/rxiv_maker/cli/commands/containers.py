"""Container management commands for RXIV-Maker."""

import logging
import os
from pathlib import Path

import rich_click as click
from rich.console import Console
from rich.table import Table

from ...core.global_container_manager import get_global_container_manager
from ...core.session_optimizer import SessionOptimizer

logger = logging.getLogger(__name__)
console = Console()


@click.group(name="containers")
def containers_cmd():
    """Manage Docker/Podman container sessions and behavior."""
    pass


@containers_cmd.command("status")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed container and session information")
def status_cmd(verbose: bool):
    """Show status of active container sessions."""
    try:
        global_manager = get_global_container_manager()
        stats = global_manager.get_engine_stats()

        console.print("\n[bold blue]Container Engine Status[/bold blue]")
        console.print(f"📦 Cached engines: {stats['cached_engines']}")

        # Show session configuration
        config = stats["session_config"]
        console.print(f"⚙️  Container mode: [green]{config['mode']}[/green]")
        console.print(f"⏱️  Session timeout: {config['session_timeout']}s")
        console.print(f"🔢 Max sessions: {config['max_sessions']}")

        if stats["engines"]:
            table = Table(title="Active Container Engines")
            table.add_column("Engine", style="cyan")
            table.add_column("Workspace", style="magenta")
            table.add_column("Sessions", style="green")
            table.add_column("Active", style="yellow")

            for engine_info in stats["engines"]:
                if "error" not in engine_info:
                    sessions_info = engine_info["sessions"]
                    workspace = (
                        engine_info["cache_key"].split(":", 1)[1] if ":" in engine_info["cache_key"] else "Unknown"
                    )
                    table.add_row(
                        engine_info["engine_name"],
                        str(Path(workspace).name),
                        str(sessions_info["total_sessions"]),
                        str(sessions_info["active_sessions"]),
                    )
                else:
                    table.add_row(engine_info["engine_name"], "Error", "Error", engine_info["error"])

            console.print(table)

            # Show session details if verbose
            if verbose:
                for engine_info in stats["engines"]:
                    if "error" not in engine_info and engine_info["sessions"]["session_details"]:
                        console.print(f"\n[bold]{engine_info['engine_name']} Sessions:[/bold]")
                        session_table = Table()
                        session_table.add_column("Session Key", style="cyan")
                        session_table.add_column("Container ID", style="green")
                        session_table.add_column("Age (s)", style="yellow")
                        session_table.add_column("Active", style="magenta")

                        for session in engine_info["sessions"]["session_details"]:
                            session_table.add_row(
                                session["key"],
                                session["container_id"],
                                f"{session['age_seconds']:.0f}",
                                "✅" if session["active"] else "❌",
                            )

                        console.print(session_table)
        else:
            console.print("📭 No active container engines")

    except Exception as e:
        console.print(f"[red]Error getting container status: {e}[/red]")
        if verbose:
            logger.exception("Container status error")


@containers_cmd.command("cleanup")
@click.option(
    "--engine", "-e", type=click.Choice(["docker", "podman"]), help="Clean up specific engine type (default: all)"
)
@click.option("--force", "-f", is_flag=True, help="Force cleanup without confirmation")
def cleanup_cmd(engine: str, force: bool):
    """Clean up container sessions and free resources."""
    try:
        global_manager = get_global_container_manager()

        if not force:
            stats = global_manager.get_engine_stats()
            total_sessions = sum(
                engine_info["sessions"]["total_sessions"]
                for engine_info in stats["engines"]
                if "error" not in engine_info
            )

            if total_sessions == 0:
                console.print("🎉 No active container sessions to clean up")
                return

            console.print(f"⚠️  This will clean up {total_sessions} active container sessions")
            if not click.confirm("Continue with cleanup?"):
                console.print("Cleanup cancelled")
                return

        if engine:
            cleanup_count = global_manager.force_cleanup_sessions(engine)
            console.print(f"🧹 Cleaned up {cleanup_count} {engine} sessions")
        else:
            cleanup_count = global_manager.cleanup_all_engines()
            console.print(f"🧹 Cleaned up {cleanup_count} container engines")

    except Exception as e:
        console.print(f"[red]Error during cleanup: {e}[/red]")
        logger.exception("Container cleanup error")


@containers_cmd.command("config")
def config_cmd():
    """Show container configuration and session optimization settings."""
    console.print("\n[bold blue]Container Configuration[/bold blue]")

    # Show environment variables
    env_vars = [
        ("RXIV_CONTAINER_MODE", "Container behavior mode", "reuse"),
        ("RXIV_SESSION_TIMEOUT", "Session timeout (seconds)", "1200"),
        ("RXIV_MAX_SESSIONS", "Maximum concurrent sessions", "3"),
        ("RXIV_DOCKER_MEMORY", "Memory limit per container", "2g"),
        ("RXIV_DOCKER_CPU", "CPU limit per container", "2.0"),
        ("RXIV_ENABLE_WARMUP", "Enable container warmup", "true"),
    ]

    env_table = Table(title="Environment Variables")
    env_table.add_column("Variable", style="cyan")
    env_table.add_column("Description", style="white")
    env_table.add_column("Current Value", style="green")
    env_table.add_column("Default", style="yellow")

    for var_name, description, default_val in env_vars:
        current_val = os.environ.get(var_name, default_val)
        env_table.add_row(var_name, description, current_val, default_val)

    console.print(env_table)

    # Show session optimization mapping
    console.print("\n[bold blue]Session Key Optimization[/bold blue]")
    session_types = SessionOptimizer.get_all_session_types()

    session_table = Table(title="Optimized Session Types")
    session_table.add_column("Session Type", style="cyan")
    session_table.add_column("Description", style="white")
    session_table.add_column("Timeout", style="yellow")
    session_table.add_column("Legacy Keys", style="magenta")

    for session_type, info in session_types.items():
        legacy_keys = ", ".join(info["legacy_keys"]) if info["legacy_keys"] else "None"
        session_table.add_row(session_type, info["description"], f"{info['timeout_seconds']}s", legacy_keys)

    console.print(session_table)

    # Show usage tips
    console.print("\n[bold green]Container Mode Options:[/bold green]")
    console.print("• [cyan]reuse[/cyan] (default): Maximize container reuse for better performance")
    console.print("• [cyan]minimal[/cyan]: Aggressive cleanup, minimal resource usage")
    console.print("• [cyan]isolated[/cyan]: Each operation gets fresh container")

    console.print("\n[bold green]Example Usage:[/bold green]")
    console.print("export RXIV_CONTAINER_MODE=minimal")
    console.print("export RXIV_SESSION_TIMEOUT=600  # 10 minutes")
    console.print("export RXIV_MAX_SESSIONS=2")


@containers_cmd.command("warmup")
@click.option("--engine", "-e", type=click.Choice(["docker", "podman"]), help="Warm up specific engine type")
def warmup_cmd(engine: str):
    """Pre-warm container engines for faster operations."""
    try:
        console.print("🔥 Warming up container engines...")

        global_manager = get_global_container_manager()
        container_engine = global_manager.get_container_engine(engine_type=engine)

        console.print(f"✅ {container_engine.engine_name.title()} engine warmed up and ready")

    except Exception as e:
        console.print(f"[red]Error warming up containers: {e}[/red]")
        logger.exception("Container warmup error")


# Add the containers command group to the main CLI
def register_containers_commands(main_cli):
    """Register container commands with the main CLI."""
    main_cli.add_command(containers_cmd)
