"""
Homebrew update checker for rxiv-maker.

Checks if a newer version is available via Homebrew.

Note: Before upgrading with Homebrew, always run 'brew update' first to fetch
the latest formulae.
"""

import re
import subprocess
from typing import Optional, Tuple

# Homebrew formula information
FORMULA_NAME = "rxiv-maker"
FORMULA_URL = "https://raw.githubusercontent.com/henriqueslab/homebrew-formulas/main/Formula/rxiv-maker.rb"


def check_brew_outdated(package: str = FORMULA_NAME, timeout: int = 5) -> Optional[Tuple[str, str]]:
    """
    Check if package is outdated using `brew outdated` command.

    Args:
        package: Package name to check
        timeout: Command timeout in seconds

    Returns:
        Tuple of (current_version, latest_version) if outdated, None otherwise
        Returns None if brew is not installed or command fails
    """
    try:
        # Run: brew outdated --verbose <package>
        # Output format: "rxiv-maker (1.7.8) < 1.7.9"
        result = subprocess.run(
            ["brew", "outdated", "--verbose", package],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        if result.returncode != 0:
            # Package is up to date or not installed
            return None

        # Parse output: "rxiv-maker (1.7.8) < 1.7.9"
        output = result.stdout.strip()
        match = re.search(r"\(([\d.]+)\)\s*<\s*([\d.]+)", output)
        if match:
            current_version = match.group(1)
            latest_version = match.group(2)
            return (current_version, latest_version)

        return None

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        # brew not installed or command failed
        return None


def check_homebrew_update(current_version: str) -> Optional[Tuple[bool, str]]:
    """
    Check if a Homebrew update is available.

    Checks via the brew outdated command to see if a newer version is available
    in the Homebrew tap.

    Args:
        current_version: Current installed version

    Returns:
        Tuple of (has_update, latest_version) if check succeeds, None on failure
    """
    # Try brew outdated command
    brew_result = check_brew_outdated()
    if brew_result is not None:
        _current, latest = brew_result
        has_update = latest != current_version
        return (has_update, latest)

    return None
