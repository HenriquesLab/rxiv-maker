"""Logging utilities for installation process."""

import logging
import sys
from datetime import datetime
from pathlib import Path

from rxiv_maker.utils.unicode_safe import get_safe_icon


class InstallLogger:
    """Logger for installation process with file and console output."""

    def __init__(self, log_file: Path | None = None, verbose: bool = False):
        """Initialize the logger.

        Args:
            log_file: Path to log file (auto-generated if None)
            verbose: Enable verbose console output
        """
        self.verbose = verbose

        # Create log file if not provided
        if log_file is None:
            log_dir = Path.home() / ".rxiv-maker" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"install_{timestamp}.log"

        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.logger = logging.getLogger("rxiv_maker_install")
        self.logger.setLevel(logging.DEBUG)

        # File handler - always verbose
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Console handler - respects verbose setting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        console_formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str):
        """Log warning message."""
        warning_icon = get_safe_icon("⚠️", "[WARNING]")
        self.logger.warning(f"{warning_icon}  {message}")

    def error(self, message: str):
        """Log error message."""
        error_icon = get_safe_icon("❌", "[ERROR]")
        self.logger.error(f"{error_icon} {message}")

    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)

    def success(self, message: str):
        """Log success message."""
        success_icon = get_safe_icon("✅", "[SUCCESS]")
        self.logger.info(f"{success_icon} {message}")

    def get_log_file(self) -> Path:
        """Get the log file path."""
        return self.log_file
