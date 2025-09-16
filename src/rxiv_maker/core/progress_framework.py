"""Centralized progress and user feedback framework for rxiv-maker.

This module provides standardized progress reporting including:
- Consistent progress reporting patterns
- Nested operation support
- Console and file logging integration
- Operation timing and statistics
- User feedback management
- Cancellation support
"""

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generator, List, Optional, Protocol

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from ..core.logging_config import get_logger

logger = get_logger()


class OperationType(Enum):
    """Types of operations for progress tracking."""

    UNKNOWN = "unknown"
    BUILD = "build"
    VALIDATION = "validation"
    CLEANUP = "cleanup"
    INITIALIZATION = "initialization"
    FIGURE_GENERATION = "figure_generation"
    FILE_OPERATION = "file_operation"
    NETWORK_OPERATION = "network_operation"
    COMPUTATION = "computation"


class ProgressLevel(Enum):
    """Progress reporting levels."""

    SILENT = "silent"  # No progress output
    MINIMAL = "minimal"  # Basic progress only
    STANDARD = "standard"  # Standard progress with details
    DETAILED = "detailed"  # Detailed progress with statistics
    DEBUG = "debug"  # Debug level with extensive info


@dataclass
class OperationStats:
    """Statistics for operation tracking."""

    operation_id: str
    operation_type: OperationType
    start_time: float
    end_time: Optional[float] = None
    total_items: Optional[int] = None
    completed_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[float]:
        """Get operation duration."""
        if self.end_time is None:
            return None
        return self.end_time - self.start_time

    @property
    def items_per_second(self) -> Optional[float]:
        """Get processing rate."""
        duration = self.duration
        if duration is None or duration == 0 or self.completed_items == 0:
            return None
        return self.completed_items / duration

    @property
    def success_rate(self) -> Optional[float]:
        """Get success rate percentage."""
        total_processed = self.completed_items + self.failed_items
        if total_processed == 0:
            return None
        return (self.completed_items / total_processed) * 100


class ProgressReporter(Protocol):
    """Protocol for progress reporters."""

    def start_operation(self, operation_id: str, operation_type: OperationType, description: str) -> None:
        """Start tracking an operation."""
        ...

    def update_progress(
        self, operation_id: str, completed: int, total: Optional[int] = None, description: Optional[str] = None
    ) -> None:
        """Update operation progress."""
        ...

    def finish_operation(self, operation_id: str, success: bool, message: Optional[str] = None) -> None:
        """Finish tracking an operation."""
        ...

    def report_error(self, operation_id: str, error: str) -> None:
        """Report an operation error."""
        ...


class ConsoleProgressReporter:
    """Rich console-based progress reporter."""

    def __init__(
        self,
        console: Optional[Console] = None,
        level: ProgressLevel = ProgressLevel.STANDARD,
        show_speed: bool = True,
        show_eta: bool = True,
    ):
        """Initialize console progress reporter.

        Args:
            console: Rich console instance
            level: Progress reporting level
            show_speed: Whether to show processing speed
            show_eta: Whether to show estimated time remaining
        """
        self.console = console or Console()
        self.level = level
        self.show_speed = show_speed
        self.show_eta = show_eta
        self.operations: Dict[str, OperationStats] = {}
        self._progress: Optional[Progress] = None
        self._tasks: Dict[str, Any] = {}

    def _create_progress(self) -> Progress:
        """Create Rich progress instance based on level."""
        columns = [
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ]

        if self.level in [ProgressLevel.STANDARD, ProgressLevel.DETAILED, ProgressLevel.DEBUG]:
            columns.extend(
                [
                    BarColumn(),
                    TaskProgressColumn(),
                ]
            )

        if self.show_speed and self.level in [ProgressLevel.DETAILED, ProgressLevel.DEBUG]:
            columns.append(TextColumn("[progress.percentage]{task.speed} items/sec", justify="right"))

        if self.show_eta and self.level in [ProgressLevel.DETAILED, ProgressLevel.DEBUG]:
            columns.append(TimeRemainingColumn())

        if self.level == ProgressLevel.DEBUG:
            columns.append(TimeElapsedColumn())

        return Progress(*columns, console=self.console, transient=(self.level == ProgressLevel.MINIMAL))

    def start_operation(self, operation_id: str, operation_type: OperationType, description: str) -> None:
        """Start tracking an operation."""
        if self.level == ProgressLevel.SILENT:
            return

        # Initialize progress if needed
        if self._progress is None:
            self._progress = self._create_progress()
            self._progress.__enter__()

        # Create operation stats
        stats = OperationStats(operation_id=operation_id, operation_type=operation_type, start_time=time.time())
        self.operations[operation_id] = stats

        # Add progress task
        task_id = self._progress.add_task(description=description, total=None)
        self._tasks[operation_id] = task_id

        if self.level == ProgressLevel.DEBUG:
            self.console.print(f"[blue]Started {operation_type.value}: {operation_id}[/blue]")

        logger.debug(f"Started operation {operation_id}: {description}")

    def update_progress(
        self, operation_id: str, completed: int, total: Optional[int] = None, description: Optional[str] = None
    ) -> None:
        """Update operation progress."""
        if self.level == ProgressLevel.SILENT or self._progress is None:
            return

        if operation_id not in self.operations:
            logger.warning(f"Unknown operation ID: {operation_id}")
            return

        # Update stats
        stats = self.operations[operation_id]
        stats.completed_items = completed
        if total is not None:
            stats.total_items = total

        # Update progress task
        task_id = self._tasks.get(operation_id)
        if task_id is not None:
            updates = {"completed": completed}
            if total is not None:
                updates["total"] = total
            if description is not None:
                updates["description"] = description

            self._progress.update(task_id, **updates)

        if self.level == ProgressLevel.DEBUG:
            progress_str = f"{completed}"
            if total is not None:
                progress_str += f"/{total}"
            self.console.print(f"[dim]Progress {operation_id}: {progress_str}[/dim]")

    def finish_operation(self, operation_id: str, success: bool, message: Optional[str] = None) -> None:
        """Finish tracking an operation."""
        if self.level == ProgressLevel.SILENT:
            return

        if operation_id not in self.operations:
            logger.warning(f"Unknown operation ID: {operation_id}")
            return

        # Update stats
        stats = self.operations[operation_id]
        stats.end_time = time.time()

        # Update progress task
        task_id = self._tasks.get(operation_id)
        if task_id is not None and self._progress is not None:
            status_icon = "✅" if success else "❌"
            description = message or f"{status_icon} {stats.operation_type.value.title()}"
            self._progress.update(
                task_id, description=description, completed=stats.total_items or stats.completed_items
            )

        # Clean up progress display when operation finishes
        if self._progress is not None:
            try:
                self._progress.stop()
            except Exception as e:
                logger.debug(f"Error cleaning up progress: {e}")
            finally:
                self._progress = None
                self._tasks.clear()

        # Log completion (only for debug level to avoid redundant messages)
        duration = stats.duration
        if duration is not None:
            duration_str = f" ({duration:.2f}s)"
        else:
            duration_str = ""

        if success:
            # Only show detailed completion message in debug mode - CLI framework handles user message
            if self.level == ProgressLevel.DEBUG:
                self.console.print(
                    f"[green]Completed {stats.operation_type.value}: {operation_id}{duration_str}[/green]"
                )
        else:
            logger.error(f"Failed operation {operation_id}{duration_str}")
            if self.level == ProgressLevel.DEBUG:
                self.console.print(f"[red]Failed {stats.operation_type.value}: {operation_id}{duration_str}[/red]")

    def report_error(self, operation_id: str, error: str) -> None:
        """Report an operation error."""
        if self.level == ProgressLevel.SILENT:
            return

        if operation_id in self.operations:
            self.operations[operation_id].failed_items += 1

        # Only log once - either to logger OR to console, not both
        if self.level in [ProgressLevel.STANDARD, ProgressLevel.DETAILED, ProgressLevel.DEBUG]:
            self.console.print(f"[red]Error in {operation_id}: {error}[/red]")
        else:
            logger.error(f"Error in operation {operation_id}: {error}")

    def get_statistics(self) -> Dict[str, OperationStats]:
        """Get operation statistics."""
        return self.operations.copy()

    def show_summary(self) -> None:
        """Show operation summary."""
        if self.level == ProgressLevel.SILENT or not self.operations:
            return

        table = Table(title="Operation Summary", show_header=True)
        table.add_column("Operation", style="cyan")
        table.add_column("Type", style="blue")
        table.add_column("Duration", style="green")
        table.add_column("Items", style="yellow")
        table.add_column("Rate", style="magenta")

        for op_id, stats in self.operations.items():
            duration_str = f"{stats.duration:.2f}s" if stats.duration else "N/A"

            items_str = str(stats.completed_items)
            if stats.total_items:
                items_str += f"/{stats.total_items}"
            if stats.failed_items > 0:
                items_str += f" ({stats.failed_items} failed)"

            rate_str = "N/A"
            if stats.items_per_second:
                rate_str = f"{stats.items_per_second:.1f}/s"

            table.add_row(
                op_id[:20],  # Truncate long IDs
                stats.operation_type.value,
                duration_str,
                items_str,
                rate_str,
            )

        self.console.print(table)

    def cleanup(self) -> None:
        """Cleanup progress reporter."""
        if self._progress is not None:
            try:
                self._progress.stop()
            except Exception as e:
                logger.debug(f"Error cleaning up progress: {e}")
            finally:
                self._progress = None


class LogProgressReporter:
    """Log file-based progress reporter."""

    def __init__(self, log_file: Optional[str] = None, level: ProgressLevel = ProgressLevel.STANDARD):
        """Initialize log progress reporter.

        Args:
            log_file: Path to log file (uses default logger if None)
            level: Progress reporting level
        """
        self.log_file = log_file
        self.level = level
        self.operations: Dict[str, OperationStats] = {}

        if log_file:
            import logging

            self.logger = logging.getLogger("rxiv_progress")
            handler = logging.FileHandler(log_file)
            handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        else:
            self.logger = logger

    def start_operation(self, operation_id: str, operation_type: OperationType, description: str) -> None:
        """Start tracking an operation."""
        if self.level == ProgressLevel.SILENT:
            return

        stats = OperationStats(operation_id=operation_id, operation_type=operation_type, start_time=time.time())
        self.operations[operation_id] = stats

        self.logger.info(f"Started {operation_type.value}: {operation_id} - {description}")

    def update_progress(
        self, operation_id: str, completed: int, total: Optional[int] = None, description: Optional[str] = None
    ) -> None:
        """Update operation progress."""
        if self.level == ProgressLevel.SILENT:
            return

        if operation_id in self.operations:
            stats = self.operations[operation_id]
            stats.completed_items = completed
            if total is not None:
                stats.total_items = total

        if self.level in [ProgressLevel.DETAILED, ProgressLevel.DEBUG]:
            progress_str = f"{completed}"
            if total is not None:
                progress_str += f"/{total}"
            self.logger.debug(f"Progress {operation_id}: {progress_str}")

    def finish_operation(self, operation_id: str, success: bool, message: Optional[str] = None) -> None:
        """Finish tracking an operation."""
        if self.level == ProgressLevel.SILENT:
            return

        if operation_id in self.operations:
            stats = self.operations[operation_id]
            stats.end_time = time.time()

            duration_str = f" in {stats.duration:.2f}s" if stats.duration else ""
            status = "Completed" if success else "Failed"
            self.logger.info(f"{status} {stats.operation_type.value}: {operation_id}{duration_str}")

    def report_error(self, operation_id: str, error: str) -> None:
        """Report an operation error."""
        if self.level != ProgressLevel.SILENT:
            self.logger.error(f"Error in {operation_id}: {error}")


class ProgressManager:
    """Centralized progress management with multiple reporters."""

    def __init__(self, reporters: Optional[List[ProgressReporter]] = None):
        """Initialize progress manager.

        Args:
            reporters: List of progress reporters
        """
        self.reporters = reporters or []
        self._operation_counter = 0

    def add_reporter(self, reporter: ProgressReporter) -> None:
        """Add a progress reporter."""
        self.reporters.append(reporter)

    def start_operation(
        self, operation_type: OperationType, description: str, operation_id: Optional[str] = None
    ) -> str:
        """Start tracking an operation.

        Args:
            operation_type: Type of operation
            description: Operation description
            operation_id: Optional custom operation ID

        Returns:
            Operation ID for tracking
        """
        if operation_id is None:
            self._operation_counter += 1
            operation_id = f"{operation_type.value}_{self._operation_counter}"

        for reporter in self.reporters:
            reporter.start_operation(operation_id, operation_type, description)

        return operation_id

    def update_progress(
        self, operation_id: str, completed: int, total: Optional[int] = None, description: Optional[str] = None
    ) -> None:
        """Update operation progress."""
        for reporter in self.reporters:
            reporter.update_progress(operation_id, completed, total, description)

    def finish_operation(self, operation_id: str, success: bool, message: Optional[str] = None) -> None:
        """Finish tracking an operation."""
        for reporter in self.reporters:
            reporter.finish_operation(operation_id, success, message)

    def report_error(self, operation_id: str, error: str) -> None:
        """Report an operation error."""
        for reporter in self.reporters:
            reporter.report_error(operation_id, error)

    def cleanup(self) -> None:
        """Cleanup all reporters."""
        for reporter in self.reporters:
            if hasattr(reporter, "cleanup"):
                reporter.cleanup()


@contextmanager
def progress_operation(
    progress_manager: ProgressManager,
    operation_type: OperationType,
    description: str,
    operation_id: Optional[str] = None,
    total_items: Optional[int] = None,
) -> Generator[str, None, None]:
    """Context manager for progress operations.

    Args:
        progress_manager: Progress manager instance
        operation_type: Type of operation
        description: Operation description
        operation_id: Optional custom operation ID
        total_items: Total number of items to process

    Yields:
        Operation ID for tracking
    """
    op_id = progress_manager.start_operation(operation_type, description, operation_id)

    try:
        yield op_id
        progress_manager.finish_operation(op_id, True)
    except Exception as e:
        progress_manager.report_error(op_id, str(e))
        progress_manager.finish_operation(op_id, False, f"Failed: {str(e)}")
        raise


# Global progress manager instance
_progress_manager: Optional[ProgressManager] = None


def get_progress_manager() -> ProgressManager:
    """Get the global progress manager instance.

    Returns:
        Global ProgressManager instance
    """
    global _progress_manager
    if _progress_manager is None:
        _progress_manager = ProgressManager([ConsoleProgressReporter(level=ProgressLevel.STANDARD)])
    return _progress_manager


def setup_progress(
    console_level: ProgressLevel = ProgressLevel.STANDARD,
    log_file: Optional[str] = None,
    log_level: ProgressLevel = ProgressLevel.MINIMAL,
) -> ProgressManager:
    """Setup global progress manager with specified reporters.

    Args:
        console_level: Console progress reporting level
        log_file: Optional log file path
        log_level: Log progress reporting level

    Returns:
        Configured ProgressManager instance
    """
    global _progress_manager

    reporters = []

    # Add console reporter if not silent
    if console_level != ProgressLevel.SILENT:
        reporters.append(ConsoleProgressReporter(level=console_level))

    # Add log reporter if requested
    if log_file or log_level != ProgressLevel.SILENT:
        reporters.append(LogProgressReporter(log_file=log_file, level=log_level))

    _progress_manager = ProgressManager(reporters)
    return _progress_manager


# Convenience functions
def report_progress(operation_id: str, completed: int, total: Optional[int] = None) -> None:
    """Report progress for an operation."""
    get_progress_manager().update_progress(operation_id, completed, total)


def report_error(operation_id: str, error: str) -> None:
    """Report an error for an operation."""
    get_progress_manager().report_error(operation_id, error)


# Export public API
__all__ = [
    "ProgressManager",
    "ConsoleProgressReporter",
    "LogProgressReporter",
    "OperationType",
    "ProgressLevel",
    "OperationStats",
    "progress_operation",
    "get_progress_manager",
    "setup_progress",
    "report_progress",
    "report_error",
]
