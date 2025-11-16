"""Decorators for CLI command framework.

This module provides decorators for common command patterns like
GitHub CLI requirements, interactive mode handling, and confirmation prompts.
"""

import functools
import sys
from typing import Callable, Optional

import click
from rich.console import Console

console = Console()


def requires_github_cli(func: Callable) -> Callable:
    """Decorator to ensure GitHub CLI (gh) is installed.

    Checks if the 'gh' command is available before executing the function.
    If not available, displays an error message and exits.

    Usage:
        @requires_github_cli
        def my_command():
            # Command that needs gh CLI
            pass
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from ...utils.github import check_gh_cli_installed

        if not check_gh_cli_installed():
            console.print("[red]Error: GitHub CLI (gh) is not installed[/red]")
            console.print("Install it with: brew install gh")
            console.print("Or visit: https://cli.github.com/")
            sys.exit(1)

        return func(*args, **kwargs)

    return wrapper


def requires_github_auth(func: Callable) -> Callable:
    """Decorator to ensure GitHub CLI authentication.

    Checks if the user is authenticated with GitHub CLI before executing.
    If not authenticated, displays an error message and exits.

    Usage:
        @requires_github_cli
        @requires_github_auth
        def my_command():
            # Command that needs GitHub authentication
            pass
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from ...utils.github import check_gh_auth

        if not check_gh_auth():
            console.print("[red]Error: Not authenticated with GitHub CLI[/red]")
            console.print("Run: gh auth login")
            sys.exit(1)

        return func(*args, **kwargs)

    return wrapper


def requires_github(func: Callable) -> Callable:
    """Decorator that combines GitHub CLI installation and authentication checks.

    This is a convenience decorator that applies both requires_github_cli
    and requires_github_auth in the correct order.

    Usage:
        @requires_github
        def my_command():
            # Command that needs both gh CLI and authentication
            pass
    """

    @functools.wraps(func)
    @requires_github_cli
    @requires_github_auth
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def with_manuscript_path(func: Callable) -> Callable:
    """Decorator to resolve manuscript path from environment or current directory.

    Automatically resolves the manuscript path using the same logic as BaseCommand.
    Useful for functions that need manuscript path but aren't using BaseCommand.

    The resolved path is passed as 'manuscript_path' keyword argument.

    Usage:
        @with_manuscript_path
        def my_function(manuscript_path, **kwargs):
            print(f"Manuscript path: {manuscript_path}")
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from ...core.cache.cache_utils import find_manuscript_directory
        from ...core.environment_manager import EnvironmentManager

        # Get manuscript path from kwargs, environment, or auto-detect
        manuscript_path = kwargs.get("manuscript_path")

        if manuscript_path is None:
            manuscript_path = EnvironmentManager.get_manuscript_path()

        if manuscript_path is None:
            manuscript_dir = find_manuscript_directory()
            if manuscript_dir is not None:
                manuscript_path = str(manuscript_dir)
            else:
                manuscript_path = "MANUSCRIPT"

        kwargs["manuscript_path"] = manuscript_path
        return func(*args, **kwargs)

    return wrapper


def handle_keyboard_interrupt(message: str = "Operation interrupted by user") -> Callable:
    """Decorator to handle keyboard interrupts (Ctrl+C) gracefully.

    Args:
        message: Custom message to display when interrupted

    Usage:
        @handle_keyboard_interrupt("Build interrupted")
        def build_command():
            # Long running operation
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except KeyboardInterrupt:
                console.print(f"\n⏹️  {message}", style="yellow")
                sys.exit(1)

        return wrapper

    return decorator


def confirm_destructive_action(
    message: str = "This action cannot be undone. Continue?",
    default: bool = False,
) -> Callable:
    """Decorator to require confirmation for destructive actions.

    Args:
        message: Confirmation prompt message
        default: Default response if user just presses Enter

    Usage:
        @confirm_destructive_action("Delete all cache files?")
        def clear_cache():
            # Destructive operation
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if --yes or -y flag is present to skip confirmation
            if kwargs.get("yes", False) or kwargs.get("confirm", False):
                return func(*args, **kwargs)

            if not click.confirm(message, default=default):
                console.print("Operation cancelled", style="yellow")
                return None

            return func(*args, **kwargs)

        return wrapper

    return decorator


def deprecated_command(
    replacement: str,
    version: str = "next major version",
    auto_redirect: bool = False,
) -> Callable:
    """Decorator to mark a command as deprecated.

    Args:
        replacement: The replacement command to suggest
        version: When the deprecated command will be removed
        auto_redirect: If True, automatically redirect to replacement

    Usage:
        @deprecated_command(replacement="rxiv setup", version="2.0.0")
        def install_deps():
            # Old command implementation
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            console.print(
                f"⚠️  WARNING: This command is deprecated and will be removed in {version}",
                style="bold yellow",
            )
            console.print(f"Use '{replacement}' instead.", style="yellow")

            if auto_redirect:
                console.print(f"Redirecting to '{replacement}'...", style="dim")
                console.print()
                # In auto-redirect mode, the function should handle the redirection
                return func(*args, **kwargs)
            else:
                console.print()
                return func(*args, **kwargs)

        return wrapper

    return decorator


def verbose_logging(func: Callable) -> Callable:
    """Decorator to enable verbose logging for a command.

    Checks for --verbose flag and sets up detailed logging if present.

    Usage:
        @verbose_logging
        def my_command(verbose=False):
            # Command implementation
            pass
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        verbose = kwargs.get("verbose", False)

        if verbose:
            from ...core.logging_config import get_logger, set_verbose

            set_verbose(True)
            logger = get_logger()
            logger.info(f"Executing {func.__name__} in verbose mode")

        return func(*args, **kwargs)

    return wrapper


def check_dependency(dependency: str, install_hint: Optional[str] = None) -> Callable:
    """Decorator to check for required dependencies before execution.

    Args:
        dependency: The dependency to check (e.g., 'latex', 'pandoc')
        install_hint: Optional installation hint to display

    Usage:
        @check_dependency('latex', 'Install with: apt install texlive')
        def build_pdf():
            # Command that requires LaTeX
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from ...install.utils.verification import verify_installation

            results = verify_installation(verbose=False)

            if not results.get(dependency, False):
                console.print(f"[red]Error: Required dependency '{dependency}' is not installed[/red]")
                if install_hint:
                    console.print(f"[yellow]{install_hint}[/yellow]")
                console.print("Run 'rxiv check-installation' for more information")
                sys.exit(1)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def measure_time(operation_name: Optional[str] = None) -> Callable:
    """Decorator to measure and display execution time.

    Args:
        operation_name: Name of the operation being measured

    Usage:
        @measure_time("PDF generation")
        def generate_pdf():
            # Long running operation
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            name = operation_name or func.__name__
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                # Only show timing if verbose mode is enabled
                verbose = kwargs.get("verbose", False)
                if verbose:
                    console.print(f"⏱️  {name} completed in {elapsed:.2f}s", style="dim")

                return result
            except Exception:
                elapsed = time.time() - start_time
                console.print(f"⏱️  {name} failed after {elapsed:.2f}s", style="dim red")
                raise

        return wrapper

    return decorator


__all__ = [
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
]
