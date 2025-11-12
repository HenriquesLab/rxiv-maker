"""
Homebrew update checker for rxiv-maker.

Checks if a newer version is available via Homebrew.

Note: Before upgrading with Homebrew, always run 'brew update' first to fetch
the latest formulae.
"""

import re
import subprocess  # nosec B404
from typing import Optional, Tuple
from urllib.request import Request, urlopen

# Homebrew formula information
HOMEBREW_TAP = "henriqueslab/formulas"
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
        result = subprocess.run(  # nosec B603, B607
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


def check_formula_github(formula_url: str = FORMULA_URL, timeout: int = 5) -> Optional[str]:
    """Check the latest version from the GitHub formula file.

    Args:
        formula_url: URL to the formula Ruby file
        timeout: Request timeout in seconds

    Returns:
        Latest version string if found, None otherwise
    """
    try:
        req = Request(formula_url, headers={"User-Agent": "rxiv-maker"})
        with urlopen(req, timeout=timeout) as response:  # nosec B310
            if response.status != 200:
                return None

            content = response.read().decode("utf-8")

            # Parse version from formula
            # Look for: version "1.8.9"
            version_match = re.search(r'version\s+"([\d.]+)"', content)
            if version_match:
                return version_match.group(1)

            # Alternative: parse from url line
            # url "https://files.pythonhosted.org/.../rxiv_maker-1.8.9.tar.gz"
            url_match = re.search(r'url\s+"[^"]*rxiv[_-]maker[/-]([\d.]+)\.tar\.gz"', content)
            if url_match:
                return url_match.group(1)

            return None

    except Exception:
        return None


def check_homebrew_update(current_version: str) -> Optional[Tuple[bool, str]]:
    """Check if a Homebrew update is available.

    Tries brew outdated command first, falls back to GitHub formula.

    Args:
        current_version: Current installed version

    Returns:
        Tuple of (has_update, latest_version) if check succeeds, None on failure
    """
    # Try brew outdated command first (most reliable)
    brew_result = check_brew_outdated()
    if brew_result is not None:
        _current, latest = brew_result
        has_update = latest != current_version
        return (has_update, latest)

    # Fall back to checking GitHub formula
    formula_version = check_formula_github()
    if formula_version is not None:
        has_update = formula_version != current_version
        return (has_update, formula_version)

    # Both methods failed
    return None
