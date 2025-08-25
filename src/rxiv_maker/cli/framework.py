"""Centralized CLI command framework for rxiv-maker.

This module provides a base class and common patterns for CLI commands,
reducing duplication and ensuring consistent error handling, progress reporting,
and path management across all commands.
"""

import sys
from abc import ABC, abstractmethod
from typing import Any, Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.environment_manager import EnvironmentManager
from ..core.logging_config import get_logger
from ..core.path_manager import PathManager, PathResolutionError

logger = get_logger()


class CommandExecutionError(Exception):
    """Exception raised during command execution."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


class BaseCommand(ABC):
    """Base class for rxiv-maker CLI commands.

    Features:
    - Consistent path resolution and validation
    - Standardized error handling and exit codes
    - Progress reporting utilities
    - Environment variable integration
    - Docker readiness checking
    - Common logging and console patterns
    """

    def __init__(self, console: Optional[Console] = None):
        """Initialize base command.

        Args:
            console: Rich console instance (creates new if None)
        """
        self.console = console or Console()
        self.path_manager: Optional[PathManager] = None
        self.verbose = False
        self.engine = "LOCAL"

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Setup common command options and path resolution.

        Args:
            ctx: Click context containing command options
            manuscript_path: Optional manuscript path override

        Raises:
            CommandExecutionError: If path resolution fails
        """
        # Extract common options from context
        self.verbose = ctx.obj.get("verbose", False) or EnvironmentManager.is_verbose()
        self.engine = ctx.obj.get("engine") or EnvironmentManager.get_rxiv_engine()

        # Resolve manuscript path
        try:
            if manuscript_path is None:
                manuscript_path = EnvironmentManager.get_manuscript_path() or "MANUSCRIPT"

            # Use PathManager for path validation and resolution
            self.path_manager = PathManager(manuscript_path=manuscript_path, output_dir="output")

            if self.verbose:
                self.console.print(f"📁 Using manuscript path: {self.path_manager.manuscript_path}", style="blue")

        except PathResolutionError as e:
            self.console.print(f"❌ Path resolution error: {e}", style="red")
            self.console.print(f"💡 Run 'rxiv init {manuscript_path}' to create a new manuscript", style="yellow")
            raise CommandExecutionError(f"Path resolution failed: {e}") from e

    def check_docker_readiness(self) -> None:
        """Check Docker availability when using docker engine.

        Raises:
            CommandExecutionError: If Docker is not available
        """
        if self.engine == "docker":
            try:
                from rxiv_maker.docker.manager import get_docker_manager

                if self.verbose:
                    self.console.print("🔧 Checking Docker availability...", style="blue")

                # Use PathManager workspace directory for consistency
                if self.path_manager is None:
                    raise CommandExecutionError("Path manager not initialized")
                docker_manager = get_docker_manager(workspace_dir=self.path_manager._working_dir)

                if not docker_manager.check_docker_available():
                    self.console.print("❌ Docker is not available. Please ensure Docker is running.", style="red")
                    raise CommandExecutionError("Docker is not available")

                if self.verbose:
                    self.console.print("🔧 Docker is ready!", style="green")

            except ImportError as e:
                self.console.print(f"❌ Docker manager import error: {e}", style="red")
                raise CommandExecutionError(f"Docker setup error: {e}") from e
            except Exception as e:
                self.console.print(f"❌ Docker setup error: {e}", style="red")
                raise CommandExecutionError(f"Docker setup error: {e}") from e

    def create_progress(self, transient: bool = True) -> Progress:
        """Create a standardized progress reporter.

        Args:
            transient: Whether progress should disappear when done

        Returns:
            Configured Rich Progress instance
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=transient,
        )

    def handle_keyboard_interrupt(self, operation_name: str) -> None:
        """Handle keyboard interrupt with consistent messaging.

        Args:
            operation_name: Name of the operation being interrupted
        """
        self.console.print(f"\n⏹️  {operation_name} interrupted by user", style="yellow")
        sys.exit(1)

    def handle_unexpected_error(self, error: Exception, operation_name: str) -> None:
        """Handle unexpected errors with consistent formatting.

        Args:
            error: The exception that occurred
            operation_name: Name of the operation that failed
        """
        self.console.print(f"❌ Unexpected error during {operation_name}: {error}", style="red")
        if self.verbose:
            self.console.print_exception()
        sys.exit(1)

    def success_message(self, message: str, details: Optional[str] = None) -> None:
        """Display success message with optional details.

        Args:
            message: Success message
            details: Optional additional details
        """
        self.console.print(f"✅ {message}", style="green")
        if details:
            self.console.print(f"📁 {details}", style="blue")

    def error_message(self, message: str, suggestion: Optional[str] = None) -> None:
        """Display error message with optional suggestion.

        Args:
            message: Error message
            suggestion: Optional suggestion for resolution
        """
        self.console.print(f"❌ {message}", style="red")
        if suggestion:
            self.console.print(f"💡 {suggestion}", style="yellow")

    @abstractmethod
    def execute_operation(self, **kwargs) -> Any:
        """Execute the main command operation.

        This method should contain the core logic for the command.
        Path resolution, Docker checking, and error handling are handled
        by the framework.

        Args:
            **kwargs: Command-specific arguments

        Returns:
            Command result (command-specific)

        Raises:
            CommandExecutionError: If operation fails
        """
        pass

    def run(self, ctx: click.Context, manuscript_path: Optional[str] = None, **kwargs) -> Any:
        """Main command execution framework.

        This method handles:
        1. Common option setup
        2. Path resolution
        3. Docker readiness (if needed)
        4. Operation execution
        5. Error handling and exit codes

        Args:
            ctx: Click context
            manuscript_path: Optional manuscript path
            **kwargs: Command-specific arguments

        Returns:
            Command result
        """
        operation_name = self.__class__.__name__.replace("Command", "").lower()

        try:
            # Setup common options and path resolution
            self.setup_common_options(ctx, manuscript_path)

            # Check Docker if needed
            if self.engine == "docker":
                self.check_docker_readiness()

            # Execute the main operation
            return self.execute_operation(**kwargs)

        except CommandExecutionError as e:
            sys.exit(e.exit_code)
        except KeyboardInterrupt:
            self.handle_keyboard_interrupt(operation_name)
        except Exception as e:
            self.handle_unexpected_error(e, operation_name)


class ValidationCommand(BaseCommand):
    """Validation command implementation using the framework."""

    def execute_operation(self, detailed: bool = False, no_doi: bool = False) -> bool:
        """Execute manuscript validation.

        Args:
            detailed: Show detailed validation report
            no_doi: Skip DOI validation

        Returns:
            True if validation passed, False otherwise
        """
        with self.create_progress() as progress:
            task = progress.add_task("Running validation...", total=None)

            # Import and run validation directly
            from rxiv_maker.engines.operations.validate import validate_manuscript

            # Determine DOI validation setting
            enable_doi_validation = None if not no_doi else False

            # Run validation using PathManager
            if self.path_manager is None:
                raise CommandExecutionError("Path manager not initialized")
            validation_passed = validate_manuscript(
                manuscript_path=str(self.path_manager.manuscript_path),
                detailed=detailed,
                verbose=self.verbose,
                include_info=False,
                check_latex=True,
                enable_doi_validation=enable_doi_validation,
            )

            if validation_passed:
                progress.update(task, description="✅ Validation completed")
                self.success_message("Validation passed!")
            else:
                progress.update(task, description="❌ Validation failed")
                self.error_message(
                    "Validation failed. See details above.",
                    "Run with --detailed for more information or use 'rxiv pdf --skip-validation' to build anyway",
                )
                raise CommandExecutionError("Validation failed")

            return validation_passed


class FiguresCommand(BaseCommand):
    """Figures command implementation using the framework."""

    def execute_operation(self, force: bool = False, figures_dir: Optional[str] = None) -> None:
        """Execute figure generation.

        Args:
            force: Force regeneration of all figures
            figures_dir: Custom figures directory path
        """
        # Set figures directory using PathManager
        if figures_dir is None:
            if self.path_manager is None:
                raise CommandExecutionError("Path manager not initialized")
            figures_dir = str(self.path_manager.manuscript_path / "FIGURES")

        with self.create_progress() as progress:
            task = progress.add_task("Generating figures...", total=None)

            try:
                if self.verbose:
                    self.console.print("📦 Importing FigureGenerator class...", style="blue")

                from rxiv_maker.engines.operations.generate_figures import FigureGenerator

                if self.verbose:
                    self.console.print("📦 Successfully imported FigureGenerator!", style="green")

                # Create FigureGenerator
                if self.path_manager is None:
                    raise CommandExecutionError("Path manager not initialized")
                generator = FigureGenerator(
                    figures_dir=figures_dir,
                    output_dir=figures_dir,
                    output_format="png",
                    r_only=False,
                    engine=self.engine,
                    enable_content_caching=not force,
                    manuscript_path=str(self.path_manager.manuscript_path),
                )

                if self.verbose:
                    mode_msg = "force mode - ignoring cache" if force else "normal mode"
                    self.console.print(f"🎨 Starting figure generation ({mode_msg})...", style="blue")

                generator.generate_all_figures()

                progress.update(task, description="✅ Figure generation completed")
                self.success_message("Figures generated successfully!", f"Figures directory: {figures_dir}")

            except Exception as e:
                progress.update(task, description="❌ Figure generation failed")
                self.error_message(f"Figure generation failed: {e}", "Check your figure scripts for errors")
                raise CommandExecutionError(f"Figure generation failed: {e}") from e


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
    "FiguresCommand",
    "create_command_from_framework",
]
