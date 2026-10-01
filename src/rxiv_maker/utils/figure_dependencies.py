"""Declared Python dependencies for manuscript figure generation.

Manuscripts ship figure scripts that import packages the rxiv-maker
environment does not carry. This module reads the manuscript's declared
requirements, checks them against the running interpreter, and installs what
is missing, so a fresh clone renders without manual setup.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement

REQUIREMENTS_FILENAME = "requirements.txt"
INSTALL_TIMEOUT_SECONDS = 600


class FigureDependencyError(Exception):
    """Raised when declared figure dependencies cannot be satisfied."""


@dataclass
class FigureDependencyStatus:
    """Result of resolving a manuscript's declared figure dependencies."""

    requirements_file: Path | None = None
    declared: list[Requirement] = field(default_factory=list)
    missing: list[Requirement] = field(default_factory=list)

    @property
    def satisfied(self) -> bool:
        """Whether every declared dependency is present at a usable version."""
        return not self.missing


def find_requirements_file(manuscript_dir: Path, figures_dir: Path) -> Path | None:
    """Locate the manuscript's declared figure dependencies.

    The figures directory takes priority, then the manuscript root.

    Args:
        manuscript_dir: Manuscript root directory
        figures_dir: Figures directory

    Returns:
        Path to the requirements file, or None when the manuscript declares none
    """
    for candidate in (figures_dir / REQUIREMENTS_FILENAME, manuscript_dir / REQUIREMENTS_FILENAME):
        if candidate.is_file():
            return candidate
    return None


def config_requirements(manuscript_dir: Path) -> list[str]:
    """Read the ``figures.dependencies`` list from the manuscript config.

    Args:
        manuscript_dir: Manuscript root directory

    Returns:
        Declared requirement strings, empty when the config declares none
    """
    from ..core.managers.config_manager import ConfigManager

    try:
        config = ConfigManager(base_dir=manuscript_dir).load_config()
    except Exception:
        return []

    figures_config = config.get("figures", {})
    if not isinstance(figures_config, dict):
        return []
    declared = figures_config.get("dependencies", [])
    if isinstance(declared, str):
        return [declared]
    if isinstance(declared, list):
        return [str(entry) for entry in declared]
    return []


def parse_requirements(requirements_file: Path) -> list[Requirement]:
    """Parse a requirements file, skipping comments and pip options.

    Args:
        requirements_file: Path to the requirements file

    Returns:
        Parsed requirement specifiers
    """
    return _parse_requirement_lines(requirements_file.read_text(encoding="utf-8").splitlines())


def _parse_requirement_lines(lines: list[str]) -> list[Requirement]:
    """Parse requirement specifiers, skipping comments and pip options.

    Args:
        lines: Raw requirement lines

    Returns:
        Parsed requirement specifiers
    """
    requirements: list[Requirement] = []
    for raw_line in lines:
        line = raw_line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        try:
            requirements.append(Requirement(line))
        except InvalidRequirement:
            # Editable paths and bare URLs are pip concerns, not ours.
            continue
    return requirements


def _distribution_version(name: str) -> str | None:
    """Return an installed distribution version, or None when it is absent.

    Args:
        name: Distribution name, with either hyphen or underscore spelling

    Returns:
        Version string, or None when no matching distribution is installed
    """
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None
    except Exception:
        return None


def _installed_version(requirement: Requirement) -> tuple[bool, str | None]:
    """Look up an installed version for a requirement.

    Distribution metadata is the source of truth; an importable module without
    metadata counts as installed because the import would succeed at render time.

    Args:
        requirement: Requirement to look up

    Returns:
        Tuple of (found, version)
    """
    for name in (requirement.name, requirement.name.replace("-", "_")):
        version = _distribution_version(name)
        if version is not None:
            return True, version

    module_name = requirement.name.replace("-", "_")
    try:
        module = importlib.import_module(module_name)
    except Exception:
        return False, None
    return True, getattr(module, "__version__", None)


def check_figure_dependencies(manuscript_dir: Path, figures_dir: Path) -> FigureDependencyStatus:
    """Resolve which declared figure dependencies are missing or mismatched.

    Args:
        manuscript_dir: Manuscript root directory
        figures_dir: Figures directory

    Returns:
        Status carrying the declared and missing requirements
    """
    requirements_file = find_requirements_file(manuscript_dir, figures_dir)

    requirements = parse_requirements(requirements_file) if requirements_file else []
    config_declared = _parse_requirement_lines(config_requirements(manuscript_dir))
    requirements.extend(config_declared)

    if not requirements:
        return FigureDependencyStatus(requirements_file=requirements_file)

    if requirements_file is None and config_declared:
        declared_in = manuscript_dir / "00_CONFIG.yml"
    else:
        declared_in = requirements_file

    missing = []
    for requirement in requirements:
        found, version = _installed_version(requirement)
        if not found:
            missing.append(requirement)
            continue
        if requirement.specifier and version and not requirement.specifier.contains(version, prereleases=True):
            missing.append(requirement)

    return FigureDependencyStatus(requirements_file=declared_in, declared=requirements, missing=missing)


def install_command(requirements: list[Requirement]) -> list[str]:
    """Build the command that installs the given requirements.

    Args:
        requirements: Requirements to install

    Returns:
        Command as an argument list, run with the active interpreter
    """
    return [sys.executable, "-m", "pip", "install", *[str(requirement) for requirement in requirements]]


def install_requirements(requirements: list[Requirement]) -> tuple[bool, str]:
    """Install the given requirements into the running interpreter.

    Falls back to ``uv pip`` when the interpreter carries no pip module, which is
    the common case for uv-managed environments.

    Args:
        requirements: Requirements to install

    Returns:
        Tuple of (succeeded, combined output)
    """
    if not requirements:
        return True, ""

    attempts = [
        install_command(requirements),
        [
            "uv",
            "pip",
            "install",
            "--python",
            sys.executable,
            *[str(requirement) for requirement in requirements],
        ],
    ]

    output = ""
    for command in attempts:
        try:
            result = subprocess.run(  # nosec # Installing packages the manuscript explicitly declares
                command,
                capture_output=True,
                text=True,
                timeout=INSTALL_TIMEOUT_SECONDS,
            )
        except FileNotFoundError:
            output += f"{command[0]} not found\n"
            continue
        except subprocess.TimeoutExpired:
            output += f"{' '.join(command)} timed out\n"
            continue

        output += result.stdout + result.stderr
        if result.returncode == 0:
            return True, output

    return False, output.strip()


def ensure_figure_dependencies(
    manuscript_dir: Path, figures_dir: Path, auto_install: bool = False
) -> FigureDependencyStatus:
    """Check declared figure dependencies and install them when asked.

    Args:
        manuscript_dir: Manuscript root directory
        figures_dir: Figures directory
        auto_install: Install missing dependencies before returning

    Returns:
        Status after any installation attempt

    Raises:
        FigureDependencyError: When dependencies are missing and remain so
    """
    status = check_figure_dependencies(manuscript_dir, figures_dir)
    if status.satisfied:
        return status

    if not auto_install:
        raise FigureDependencyError(describe_missing(status))

    ok, output = install_requirements(status.missing)
    if not ok:
        raise FigureDependencyError(describe_missing(status, auto_install=True, install_output=output))

    resolved = check_figure_dependencies(manuscript_dir, figures_dir)
    if not resolved.satisfied:
        raise FigureDependencyError(describe_missing(resolved, auto_install=True, install_output=output))

    return resolved


def describe_missing(status: FigureDependencyStatus, auto_install: bool = False, install_output: str = "") -> str:
    """Build an actionable message naming the missing figure dependencies.

    Args:
        status: Dependency status carrying the missing requirements
        auto_install: Whether an installation was already attempted
        install_output: Output from a failed installation attempt

    Returns:
        Formatted message
    """
    if status.satisfied:
        return ""

    names = ", ".join(str(requirement) for requirement in status.missing)
    command = " ".join(install_command(status.missing))

    lines = [f"Figure generation needs packages that are not installed: {names}"]
    if status.requirements_file:
        lines.append(f"Declared in {status.requirements_file}.")

    if auto_install:
        lines.append("Automatic installation failed. Install them manually with:")
        lines.append(f"  {command}")
        if install_output:
            lines.append(install_output)
    else:
        lines.append("Install them with:")
        lines.append(f"  {command}")
        lines.append("Or re-run with --install-deps to let rxiv-maker install them.")

    return "\n".join(lines)
