#!/usr/bin/env python3
"""
Centralized logging setup for GitHub Actions scripts.

Provides both console and file logging with proper formatting.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(name: str = "github_actions", level: str = "INFO", log_file: Optional[Path] = None) -> logging.Logger:
    """
    Setup logger with console and optional file output.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for logging

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # Optional file handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


def log_step(logger: logging.Logger, step: str, status: str = "START"):
    """
    Log workflow steps with consistent formatting.

    Args:
        logger: Logger instance
        step: Description of the step
        status: Status (START, SUCCESS, FAILURE, SKIP)
    """
    status_symbols = {"START": "🚀", "SUCCESS": "✅", "FAILURE": "❌", "SKIP": "⏭️ ", "WARNING": "⚠️ "}

    symbol = status_symbols.get(status, "📍")
    logger.info(f"{symbol} {step} [{status}]")


def log_section(logger: logging.Logger, section: str):
    """
    Log major sections with visual separation.

    Args:
        logger: Logger instance
        section: Section name
    """
    separator = "=" * 60
    logger.info(f"\n{separator}")
    logger.info(f"🔧 {section}")
    logger.info(f"{separator}")
