"""Base command framework for rxiv-maker CLI.

This module provides the foundational base class and utilities for all CLI commands.
"""

import sys
from abc import ABC, abstractmethod
from typing import Any, Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...core.environment_manager import EnvironmentManager
from ...core.logging_config import get_logger
from ...core.path_manager import PathManager, PathResolutionError

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
        self.engine = "local"  # Only local engine is supported

        # Resolve manuscript path
        try:
            if manuscript_path is None:
                # First check environment variable
                manuscript_path = EnvironmentManager.get_manuscript_path()

                # If no environment variable, check if we're already in a manuscript directory
                if manuscript_path is None:
                    from rxiv_maker.core.cache.cache_utils import find_manuscript_directory

                    manuscript_dir = find_manuscript_directory()
                    if manuscript_dir is not None:
                        manuscript_path = str(manuscript_dir)
                        if self.verbose:
                            self.console.print(f"🔍 Detected manuscript directory: {manuscript_path}", style="green")
                    else:
                        # Fall back to default MANUSCRIPT subdirectory
                        manuscript_path = "MANUSCRIPT"
                        if self.verbose:
                            self.console.print("📁 Using default MANUSCRIPT subdirectory", style="yellow")

            # Use PathManager for path validation and resolution
            self.path_manager = PathManager(manuscript_path=manuscript_path, output_dir="output")

            if self.verbose:
                self.console.print(f"📁 Using manuscript path: {self.path_manager.manuscript_path}", style="blue")

        except PathResolutionError as e:
            self.console.print(f"❌ Path resolution error: {e}", style="red")
            self.console.print(f"💡 Run 'rxiv init {manuscript_path}' to create a new manuscript", style="yellow")
            raise CommandExecutionError(f"Path resolution failed: {e}") from e

    def check_engine_support(self) -> None:
        """Check if the requested engine is supported.

        Raises:
            CommandExecutionError: If unsupported engine is requested
        """
        # Engine is always local now, no need to check
        return

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
        Path resolution and error handling are handled by the framework.

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
        3. Operation execution
        4. Error handling and exit codes

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

            # Check engine support
            self.check_engine_support()

            # Execute the main operation
            return self.execute_operation(**kwargs)

        except CommandExecutionError as e:
            # Print error message to stderr before exiting
            error_console = Console(stderr=True)
            error_console.print(f"❌ Error: {e}", style="red")
            sys.exit(e.exit_code)
        except KeyboardInterrupt:
            self.handle_keyboard_interrupt(operation_name)
        except Exception as e:
            self.handle_unexpected_error(e, operation_name)
