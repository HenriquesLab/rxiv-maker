"""Centralized dependency management for rxiv-maker.

This module provides a unified interface for checking, validating, and managing
all system and software dependencies required by rxiv-maker operations.
"""

import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

from ..logging_config import get_logger
from .install_manager import InstallManager, InstallMode

logger = get_logger()


class DependencyType(Enum):
    """Types of dependencies."""

    SYSTEM_BINARY = "system_binary"  # System executables (pdflatex, etc.)
    PYTHON_PACKAGE = "python_package"  # Python modules/packages
    R_PACKAGE = "r_package"  # R packages
    FONT = "font"  # System fonts
    ENVIRONMENT_VAR = "environment_var"  # Environment variables
    UBUNTU_PACKAGE = "ubuntu_package"  # Ubuntu/Debian packages via apt


class DependencyStatus(Enum):
    """Dependency status states."""

    AVAILABLE = "available"
    MISSING = "missing"
    VERSION_MISMATCH = "version_mismatch"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class DependencySpec:
    """Specification for a dependency."""

    name: str
    type: DependencyType
    required: bool = True
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    alternatives: List[str] = field(default_factory=list)
    check_command: Optional[List[str]] = None
    install_hint: Optional[str] = None
    platforms: Set[str] = field(default_factory=lambda: {"Windows", "Darwin", "Linux"})
    contexts: Set[str] = field(default_factory=set)  # When this dependency is needed


@dataclass
class DependencyResult:
    """Result of dependency check."""

    spec: DependencySpec
    status: DependencyStatus
    version: Optional[str] = None
    error_message: Optional[str] = None
    available_alternative: Optional[str] = None
    resolution_hint: Optional[str] = None


class DependencyChecker(ABC):
    """Abstract base class for dependency checkers."""

    @abstractmethod
    def check(self, spec: DependencySpec) -> DependencyResult:
        """Check if dependency is available.

        Args:
            spec: Dependency specification

        Returns:
            Result of dependency check
        """
        pass


class SystemBinaryChecker(DependencyChecker):
    """Checker for system binaries and executables."""

    def check(self, spec: DependencySpec) -> DependencyResult:
        """Check system binary availability."""
        # Try main binary first
        for binary_name in [spec.name] + spec.alternatives:
            if shutil.which(binary_name):
                version = self._get_version(binary_name, spec.check_command)
                status = self._check_version_compatibility(version, spec)

                return DependencyResult(
                    spec=spec,
                    status=status,
                    version=version,
                    available_alternative=binary_name if binary_name != spec.name else None,
                )

        # Not found
        resolution_hint = spec.install_hint or f"Install {spec.name}"
        if spec.alternatives:
            resolution_hint += f" or alternatives: {', '.join(spec.alternatives)}"

        return DependencyResult(spec=spec, status=DependencyStatus.MISSING, resolution_hint=resolution_hint)

    def _get_version(self, binary_name: str, check_command: Optional[List[str]]) -> Optional[str]:
        """Get version string for binary."""
        if not check_command:
            # Try common version flags
            for flag in ["--version", "-V", "-version", "version"]:
                try:
                    result = subprocess.run([binary_name, flag], capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        return result.stdout.strip().split("\n")[0]
                except Exception:
                    continue
        else:
            try:
                cmd = check_command.copy()
                cmd[0] = binary_name  # Replace placeholder with actual binary
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip().split("\n")[0]
            except Exception:
                pass

        return None

    def _check_version_compatibility(self, version: Optional[str], spec: DependencySpec) -> DependencyStatus:
        """Check if version meets requirements."""
        if not version:
            return DependencyStatus.AVAILABLE

        if not (spec.min_version or spec.max_version):
            return DependencyStatus.AVAILABLE

        # TODO: Implement proper semantic version comparison
        # For now, just return AVAILABLE
        return DependencyStatus.AVAILABLE


class PythonPackageChecker(DependencyChecker):
    """Checker for Python packages."""

    def check(self, spec: DependencySpec) -> DependencyResult:
        """Check Python package availability."""
        try:
            __import__(spec.name)
            # Try to get version
            version = self._get_package_version(spec.name)

            return DependencyResult(spec=spec, status=DependencyStatus.AVAILABLE, version=version)
        except ImportError as e:
            return DependencyResult(
                spec=spec,
                status=DependencyStatus.MISSING,
                error_message=str(e),
                resolution_hint=f"pip install {spec.name}",
            )

    def _get_package_version(self, package_name: str) -> Optional[str]:
        """Get package version."""
        try:
            import importlib.metadata

            return importlib.metadata.version(package_name)
        except Exception:
            try:
                module = __import__(package_name)
                return getattr(module, "__version__", None)
            except Exception:
                return None


class EnvironmentVarChecker(DependencyChecker):
    """Checker for environment variables."""

    def check(self, spec: DependencySpec) -> DependencyResult:
        """Check environment variable availability."""
        import os

        value = os.environ.get(spec.name)
        if value:
            return DependencyResult(spec=spec, status=DependencyStatus.AVAILABLE, version=value)
        else:
            return DependencyResult(
                spec=spec, status=DependencyStatus.MISSING, resolution_hint=f"Set environment variable {spec.name}"
            )


class UbuntuPackageChecker(DependencyChecker):
    """Checker for Ubuntu/Debian packages."""

    def check(self, spec: DependencySpec) -> DependencyResult:
        """Check Ubuntu package availability."""
        try:
            # Use dpkg-query to check if package is installed
            result = subprocess.run(
                ["dpkg-query", "-W", "-f=${Status}", spec.name], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0 and "install ok installed" in result.stdout:
                # Get version if possible
                version_result = subprocess.run(
                    ["dpkg-query", "-W", "-f=${Version}", spec.name], capture_output=True, text=True, timeout=10
                )
                version = version_result.stdout.strip() if version_result.returncode == 0 else None

                return DependencyResult(spec=spec, status=DependencyStatus.AVAILABLE, version=version)
            else:
                return DependencyResult(
                    spec=spec, status=DependencyStatus.MISSING, resolution_hint=f"sudo apt install {spec.name}"
                )
        except subprocess.TimeoutExpired:
            return DependencyResult(
                spec=spec, status=DependencyStatus.ERROR, error_message="Timeout checking package status"
            )
        except Exception as e:
            return DependencyResult(spec=spec, status=DependencyStatus.ERROR, error_message=str(e))


class DependencyManager:
    """Centralized dependency management for rxiv-maker.

    Features:
    - Unified dependency checking across all types
    - Context-aware dependency resolution (build, figures, validation, etc.)
    - Parallel dependency checking
    - Integration with InstallManager for missing dependencies
    - Caching of dependency results
    - Automatic fallback to alternatives
    """

    def __init__(self):
        """Initialize dependency manager."""
        # Dependency checkers by type
        self.checkers: Dict[DependencyType, DependencyChecker] = {
            DependencyType.SYSTEM_BINARY: SystemBinaryChecker(),
            DependencyType.PYTHON_PACKAGE: PythonPackageChecker(),
            DependencyType.ENVIRONMENT_VAR: EnvironmentVarChecker(),
            DependencyType.UBUNTU_PACKAGE: UbuntuPackageChecker(),
        }

        # Dependency registry
        self.dependencies: Dict[str, DependencySpec] = {}

        # Result cache
        self._result_cache: Dict[str, DependencyResult] = {}

        # Register built-in dependencies
        self._register_builtin_dependencies()

        logger.debug("DependencyManager initialized")

    def _register_builtin_dependencies(self) -> None:
        """Register built-in rxiv-maker dependencies."""
        # LaTeX dependencies
        self.register_dependency(
            DependencySpec(
                name="pdflatex",
                type=DependencyType.SYSTEM_BINARY,
                required=True,
                contexts={"build", "pdf"},
                install_hint="Install LaTeX distribution (TeX Live, MiKTeX, or BasicTeX)",
            )
        )

        self.register_dependency(
            DependencySpec(
                name="bibtex",
                type=DependencyType.SYSTEM_BINARY,
                required=True,
                contexts={"build", "pdf"},
                install_hint="Usually included with LaTeX distribution",
            )
        )

        # Figure generation dependencies
        self.register_dependency(
            DependencySpec(
                name="python",
                type=DependencyType.SYSTEM_BINARY,
                required=True,
                alternatives=["python3"],
                contexts={"figures", "build"},
                install_hint="Install Python 3.8 or later",
            )
        )

        self.register_dependency(
            DependencySpec(
                name="Rscript",
                type=DependencyType.SYSTEM_BINARY,
                required=False,
                contexts={"figures"},
                install_hint="Install R statistical software",
            )
        )

        # Python packages
        for pkg in ["click", "rich", "jinja2", "pyyaml", "pathlib"]:
            self.register_dependency(
                DependencySpec(
                    name=pkg,
                    type=DependencyType.PYTHON_PACKAGE,
                    required=True,
                    contexts={"build", "figures", "validate"},
                    install_hint=f"pip install {pkg}",
                )
            )

        # Optional Python packages
        for pkg in ["matplotlib", "numpy", "pandas"]:
            self.register_dependency(
                DependencySpec(
                    name=pkg,
                    type=DependencyType.PYTHON_PACKAGE,
                    required=False,
                    contexts={"figures"},
                    install_hint=f"pip install {pkg}",
                )
            )

        # System packages
        # Core system utilities
        for pkg in ["curl", "wget", "unzip", "ca-certificates", "software-properties-common", "gnupg", "lsb-release"]:
            self.register_dependency(
                DependencySpec(
                    name=pkg,
                    type=DependencyType.UBUNTU_PACKAGE,
                    required=False,
                    contexts={"system"},
                    platforms={"Linux"},
                    install_hint=f"sudo apt install {pkg}",
                )
            )

        # Build toolchain (only needed for building from source, not for using rxiv-maker)
        for pkg in ["build-essential", "make", "cmake", "pkg-config", "gcc", "g++", "gfortran"]:
            self.register_dependency(
                DependencySpec(
                    name=pkg,
                    type=DependencyType.UBUNTU_PACKAGE,
                    required=False,
                    contexts={"development", "build-from-source"},  # Not needed for basic PDF generation
                    platforms={"Linux"},
                    install_hint=f"sudo apt install {pkg}",
                )
            )

        # Development libraries (only needed for building from source, not for using rxiv-maker)
        dev_libs = [
            "libjpeg-dev",
            "libpng-dev",
            "libtiff5-dev",
            "python3-dev",
            "libffi-dev",
            "libcurl4-openssl-dev",
            "libssl-dev",
            "libxml2-dev",
            "libfontconfig1-dev",
            "libfreetype6-dev",
            "libharfbuzz-dev",
            "libfribidi-dev",
        ]
        for pkg in dev_libs:
            self.register_dependency(
                DependencySpec(
                    name=pkg,
                    type=DependencyType.UBUNTU_PACKAGE,
                    required=False,
                    contexts={"development", "build-from-source"},  # Not needed for basic PDF generation
                    platforms={"Linux"},
                    install_hint=f"sudo apt install {pkg}",
                )
            )

        # Essential fonts for LaTeX compilation
        font_packages = [
            "fonts-liberation",
            "fonts-dejavu-core",
            "fonts-lmodern",
            "fonts-texgyre",
            "fonts-dejavu",
            "fonts-liberation2",
            "fonts-noto-core",
            "fontconfig",
            "fontconfig-config",
        ]
        for pkg in font_packages:
            self.register_dependency(
                DependencySpec(
                    name=pkg,
                    type=DependencyType.UBUNTU_PACKAGE,
                    required=True,
                    contexts={"pdf", "build"},
                    platforms={"Linux"},
                    install_hint=f"sudo apt install {pkg}",
                )
            )

        # Essential LaTeX packages (required for basic PDF generation)
        essential_latex = [
            "texlive-latex-base",
            "texlive-latex-recommended",
            "texlive-fonts-recommended",
            "texlive-fonts-extra",
            "texlive-latex-extra",
            "texlive-science",
        ]
        for pkg in essential_latex:
            self.register_dependency(
                DependencySpec(
                    name=pkg,
                    type=DependencyType.UBUNTU_PACKAGE,
                    required=True,
                    contexts={"pdf", "build"},
                    platforms={"Linux"},
                    install_hint=f"sudo apt install {pkg}",
                )
            )

        # Additional LaTeX packages (useful but not strictly required)
        additional_latex = [
            "texlive-pictures",
            "texlive-bibtex-extra",
            "biber",
            "texlive-lang-english",
            "texlive-plain-generic",
            "texlive-xetex",
            "texlive-luatex",
            "texlive-extra-utils",
            "latexdiff",
        ]
        for pkg in additional_latex:
            self.register_dependency(
                DependencySpec(
                    name=pkg,
                    type=DependencyType.UBUNTU_PACKAGE,
                    required=False,  # Useful but not absolutely required for basic PDF
                    contexts={"pdf", "build", "advanced-latex"},
                    platforms={"Linux"},
                    install_hint=f"sudo apt install {pkg}",
                )
            )

        # R and essential R packages (optional - only needed for R figures)
        r_packages = [
            "r-base",
            "r-base-dev",
            "r-cran-ggplot2",
            "r-cran-dplyr",
            "r-cran-scales",
            "r-cran-readr",
            "r-cran-tidyr",
            "r-cran-svglite",
            "r-cran-cli",
            "r-cran-rlang",
            "r-cran-lifecycle",
            "r-cran-vctrs",
            "r-cran-magrittr",
            "r-cran-stringi",
            "r-cran-stringr",
            "r-cran-httr",
            "r-cran-jsonlite",
            "r-cran-xml2",
            "r-cran-lubridate",
            "r-cran-rvest",
            "r-cran-systemfonts",
            "r-cran-ragg",
        ]
        for pkg in r_packages:
            self.register_dependency(
                DependencySpec(
                    name=pkg,
                    type=DependencyType.UBUNTU_PACKAGE,
                    required=False,  # R is optional
                    contexts={"r-figures", "r"},  # Only needed for R-based figure generation
                    platforms={"Linux"},
                    install_hint=f"sudo apt install {pkg}",
                )
            )

    def register_dependency(self, spec: DependencySpec) -> None:
        """Register a dependency specification.

        Args:
            spec: Dependency specification
        """
        self.dependencies[spec.name] = spec
        logger.debug(f"Registered dependency: {spec.name} ({spec.type.value})")

    def check_dependency(self, name: str, use_cache: bool = True) -> DependencyResult:
        """Check a single dependency.

        Args:
            name: Dependency name
            use_cache: Whether to use cached results

        Returns:
            Dependency check result
        """
        # Check cache first
        if use_cache and name in self._result_cache:
            return self._result_cache[name]

        spec = self.dependencies.get(name)
        if not spec:
            return DependencyResult(
                spec=DependencySpec(name=name, type=DependencyType.SYSTEM_BINARY),
                status=DependencyStatus.UNKNOWN,
                error_message=f"Unknown dependency: {name}",
            )

        # Check current platform
        import platform

        current_platform = platform.system()
        if spec.platforms and current_platform not in spec.platforms:
            result = DependencyResult(
                spec=spec,
                status=DependencyStatus.AVAILABLE,  # Skip on unsupported platforms
                version="skipped",
                resolution_hint=f"Not required on {current_platform}",
            )
            self._result_cache[name] = result
            return result

        # Use appropriate checker
        checker = self.checkers.get(spec.type)
        if not checker:
            result = DependencyResult(
                spec=spec, status=DependencyStatus.ERROR, error_message=f"No checker for dependency type: {spec.type}"
            )
            self._result_cache[name] = result
            return result

        # Perform check
        try:
            result = checker.check(spec)
            self._result_cache[name] = result
            logger.debug(f"Dependency {name}: {result.status.value}")
            return result
        except Exception as e:
            result = DependencyResult(spec=spec, status=DependencyStatus.ERROR, error_message=str(e))
            self._result_cache[name] = result
            return result

    def check_context_dependencies(
        self, context: str, required_only: bool = False, parallel: bool = True
    ) -> Dict[str, DependencyResult]:
        """Check dependencies for a specific context.

        Args:
            context: Context to check (e.g., "build", "figures")
            required_only: Only check required dependencies
            parallel: Check dependencies in parallel

        Returns:
            Dictionary mapping dependency names to results
        """
        # Find dependencies for context
        context_deps = []
        for name, spec in self.dependencies.items():
            if not spec.contexts or context in spec.contexts:
                if not required_only or spec.required:
                    context_deps.append(name)

        logger.info(f"Checking {len(context_deps)} dependencies for context '{context}'")

        # Check dependencies
        results = {}
        if parallel and len(context_deps) > 1:
            # TODO: Implement parallel checking using ThreadPoolExecutor
            for name in context_deps:
                results[name] = self.check_dependency(name)
        else:
            for name in context_deps:
                results[name] = self.check_dependency(name)

        return results

    def get_missing_dependencies(
        self, context: Optional[str] = None, required_only: bool = True
    ) -> List[DependencyResult]:
        """Get list of missing dependencies.

        Args:
            context: Optional context filter
            required_only: Only check required dependencies

        Returns:
            List of missing dependency results
        """
        if context:
            results = self.check_context_dependencies(context, required_only)
        else:
            # Check all dependencies
            results = {}
            for name in self.dependencies:
                spec = self.dependencies[name]
                if not required_only or spec.required:
                    results[name] = self.check_dependency(name)

        return [
            result for result in results.values() if result.status in (DependencyStatus.MISSING, DependencyStatus.ERROR)
        ]

    def generate_installation_report(self, context: Optional[str] = None) -> str:
        """Generate human-readable installation report.

        Args:
            context: Optional context filter

        Returns:
            Formatted installation report
        """
        missing = self.get_missing_dependencies(context)

        if not missing:
            return "✅ All dependencies are available!"

        report = ["❌ Missing dependencies found:", ""]

        # Group by type
        by_type: Dict[DependencyType, List[DependencyResult]] = {}
        for result in missing:
            dep_type = result.spec.type
            if dep_type not in by_type:
                by_type[dep_type] = []
            by_type[dep_type].append(result)

        for dep_type, results in by_type.items():
            report.append(f"**{dep_type.value.replace('_', ' ').title()}:**")
            for result in results:
                status_icon = "❌" if result.spec.required else "⚠️"
                report.append(f"  {status_icon} {result.spec.name}")
                if result.resolution_hint:
                    report.append(f"     → {result.resolution_hint}")
            report.append("")

        return "\n".join(report)

    def install_missing_dependencies(
        self, context: Optional[str] = None, interactive: bool = True, mode: InstallMode = InstallMode.FULL
    ) -> bool:
        """Install missing dependencies using InstallManager.

        Args:
            context: Optional context filter
            interactive: Allow interactive prompts
            mode: Installation mode

        Returns:
            True if installation succeeded
        """
        missing = self.get_missing_dependencies(context)

        if not missing:
            logger.info("No missing dependencies to install")
            return True

        logger.info(f"Installing {len(missing)} missing dependencies")

        # Use InstallManager for system-level installation
        install_manager = InstallManager(
            mode=mode,
            interactive=interactive,
            verbose=logger.logger.getEffectiveLevel() <= 10,  # DEBUG level
        )

        return install_manager.install()

    def clear_cache(self) -> None:
        """Clear dependency result cache."""
        self._result_cache.clear()
        logger.debug("Dependency cache cleared")


# Global dependency manager instance
_dependency_manager: Optional[DependencyManager] = None


def get_dependency_manager() -> DependencyManager:
    """Get the global dependency manager instance.

    Returns:
        Global dependency manager
    """
    global _dependency_manager
    if _dependency_manager is None:
        _dependency_manager = DependencyManager()
    return _dependency_manager


# Convenience functions
def check_dependencies(context: str, required_only: bool = True) -> bool:
    """Check if all dependencies for a context are available.

    Args:
        context: Context to check
        required_only: Only check required dependencies

    Returns:
        True if all dependencies are available
    """
    manager = get_dependency_manager()
    missing = manager.get_missing_dependencies(context, required_only)
    return len(missing) == 0


def ensure_dependencies(context: str, auto_install: bool = False) -> bool:
    """Ensure dependencies for a context are available.

    Args:
        context: Context to check
        auto_install: Automatically install missing dependencies

    Returns:
        True if dependencies are available or were installed successfully
    """
    manager = get_dependency_manager()

    if check_dependencies(context):
        return True

    if auto_install:
        return manager.install_missing_dependencies(context)
    else:
        report = manager.generate_installation_report(context)
        logger.error(f"Missing dependencies for {context}:\n{report}")
        return False
