"""Centralized logging configuration for rxiv-maker."""

import atexit
import logging
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


class RxivLogger:
    """Centralized logging configuration for rxiv-maker with Rich support."""

    _instance: Optional["RxivLogger"] = None
    _console: Console | None = None
    _log_file_path: Path | None = None
    _file_handler: logging.FileHandler | None = None

    def __new__(cls) -> "RxivLogger":
        """Create a new instance of the singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the singleton instance only once."""
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._console = Console()
        self._log_file_path: Path | None = None
        self._file_handler: logging.FileHandler | None = None
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Setup the main logger with Rich handler."""
        # Create main logger
        self.logger = logging.getLogger("rxiv_maker")
        self.logger.setLevel(logging.INFO)  # Default level

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Create Rich handler
        rich_handler = RichHandler(
            console=self._console,
            show_time=False,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
        )
        rich_handler.setFormatter(logging.Formatter("%(message)s"))

        self.logger.addHandler(rich_handler)

        # File handler will be added when log directory is set

    def set_log_directory(self, log_dir: Path) -> None:
        """Set the directory where log files should be created."""
        # Remove existing file handler if present
        if self._file_handler:
            self.logger.removeHandler(self._file_handler)
            self._file_handler.close()

        # Create log directory if it doesn't exist
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create new file handler
        self._log_file_path = log_dir / "rxiv_maker.log"
        self._file_handler = logging.FileHandler(self._log_file_path)
        self._file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self._file_handler.setFormatter(file_formatter)
        self.logger.addHandler(self._file_handler)

    def get_log_file_path(self) -> Path | None:
        """Get the current log file path."""
        return self._log_file_path

    def set_level(self, level: str) -> None:
        """Set logging level."""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        if level.upper() in level_map:
            self.logger.setLevel(level_map[level.upper()])
            # Also update Rich handler level
            for handler in self.logger.handlers:
                if isinstance(handler, RichHandler):
                    handler.setLevel(level_map[level.upper()])

    def set_quiet(self, quiet: bool = True) -> None:
        """Enable/disable quiet mode (only errors and warnings)."""
        if quiet:
            self.set_level("WARNING")
        else:
            self.set_level("INFO")

    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(f"🔧 {message}")

    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(f"ℹ️ {message}")

    def success(self, message: str) -> None:
        """Log success message."""
        self.logger.info(f"[green]✅ {message}[/green]")

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(f"[yellow]⚠️ {message}[/yellow]")

    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(f"[red]❌ {message}[/red]")

    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(f"[red bold]💥 {message}[/red bold]")

    def docker_info(self, message: str) -> None:
        """Log Docker-related info."""
        self.logger.info(f"[blue]🐳 {message}[/blue]")

    def tip(self, message: str) -> None:
        """Log helpful tip."""
        self.logger.info(f"[yellow]💡 {message}[/yellow]")

    @property
    def console(self) -> Console:
        """Get the Rich console instance."""
        if self._console is None:
            self._console = Console()
        return self._console

    def cleanup(self) -> None:
        """Clean up resources, especially file handlers for Windows compatibility."""
        if self._file_handler:
            self.logger.removeHandler(self._file_handler)
            self._file_handler.close()
            self._file_handler = None

        # Also close any other handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            if hasattr(handler, "close"):
                handler.close()


# Global logger instance
_logger_instance = RxivLogger()

# Register automatic cleanup on exit for Windows compatibility
atexit.register(_logger_instance.cleanup)


# Convenience functions
def get_logger() -> RxivLogger:
    """Get the global logger instance."""
    return _logger_instance


def debug(message: str) -> None:
    """Log debug message."""
    _logger_instance.debug(message)


def info(message: str) -> None:
    """Log info message."""
    _logger_instance.info(message)


def success(message: str) -> None:
    """Log success message."""
    _logger_instance.success(message)


def warning(message: str) -> None:
    """Log warning message."""
    _logger_instance.warning(message)


def error(message: str) -> None:
    """Log error message."""
    _logger_instance.error(message)


def critical(message: str) -> None:
    """Log critical message."""
    _logger_instance.critical(message)


def docker_info(message: str) -> None:
    """Log Docker-related info."""
    _logger_instance.docker_info(message)


def tip(message: str) -> None:
    """Log helpful tip."""
    _logger_instance.tip(message)


def set_quiet(quiet: bool = True) -> None:
    """Enable/disable quiet mode."""
    _logger_instance.set_quiet(quiet)


def set_debug(debug_mode: bool = True) -> None:
    """Enable/disable debug mode."""
    if debug_mode:
        _logger_instance.set_level("DEBUG")
    else:
        _logger_instance.set_level("INFO")


def set_log_directory(log_dir: Path) -> None:
    """Set the directory where log files should be created."""
    _logger_instance.set_log_directory(log_dir)


def get_log_file_path() -> Path | None:
    """Get the current log file path."""
    return _logger_instance.get_log_file_path()


def cleanup() -> None:
    """Clean up logging resources."""
    _logger_instance.cleanup()
