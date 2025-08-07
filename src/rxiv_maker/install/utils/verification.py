"""Installation verification utilities."""

import shutil
import subprocess
import sys
from typing import Any

from rxiv_maker.utils.unicode_safe import get_safe_icon

# Import existing dependency checker
try:
    from ...utils.dependency_checker import DependencyChecker
except ImportError:
    # Fallback for testing
    DependencyChecker = None  # type: ignore[misc,assignment]


def verify_installation(verbose: bool = False) -> dict[str, bool]:
    """Verify that all required components are installed and working.

    Args:
        verbose: Enable verbose output

    Returns:
        Dictionary mapping component names to installation status
    """
    results = {}

    # Check Python
    results["python"] = _check_python()

    # Check LaTeX
    results["latex"] = _check_latex()

    # Check Node.js
    results["nodejs"] = _check_nodejs()

    # Check R (optional)
    results["r"] = _check_r()

    # Check system libraries
    results["system_libs"] = _check_system_libraries()

    # Check rxiv-maker package
    results["rxiv_maker"] = _check_rxiv_maker()

    if verbose:
        _print_verification_results(results)

    return results


def check_system_dependencies() -> list[str]:
    """Check system dependencies and return list of missing components.

    Returns:
        List of missing dependency names
    """
    verification_results = verify_installation()
    missing = []

    for component, installed in verification_results.items():
        if not installed and component != "r":  # R is optional
            missing.append(component)

    return missing


def _check_python() -> bool:
    """Check if Python is available and correct version."""
    try:
        version = sys.version_info
        return version.major == 3 and version.minor >= 11
    except Exception:
        return False


def _check_latex() -> bool:
    """Check if LaTeX is available."""
    try:
        # Check for pdflatex
        result = subprocess.run(["pdflatex", "--version"], capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception:
        return False


def _check_nodejs() -> bool:
    """Check if Node.js and npm are available."""
    try:
        # Check Node.js
        node_result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10)

        # Check npm
        npm_result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=10)

        return node_result.returncode == 0 and npm_result.returncode == 0
    except Exception:
        return False


def _check_r() -> bool:
    """Check if R is available."""
    try:
        result = subprocess.run(["R", "--version"], capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception:
        return False


def _check_system_libraries() -> bool:
    """Check if required system libraries are available."""
    import importlib.util

    packages = ["matplotlib", "numpy", "PIL"]

    for package in packages:
        if importlib.util.find_spec(package) is None:
            return False

    return True


def _check_rxiv_maker() -> bool:
    """Check if rxiv-maker package is installed and working."""
    import importlib.util

    return importlib.util.find_spec("rxiv_maker") is not None


def _print_verification_results(results: dict[str, bool]) -> None:
    """Print verification results in a formatted way."""
    print("\n" + "=" * 50)
    print("INSTALLATION VERIFICATION RESULTS")
    print("=" * 50)

    for component, installed in results.items():
        if installed:
            status_icon = get_safe_icon("✅", "[INSTALLED]")
            status = f"{status_icon} INSTALLED"
        else:
            status_icon = get_safe_icon("❌", "[MISSING]")
            status = f"{status_icon} MISSING"
        component_name = component.replace("_", " ").title()
        print(f"{component_name:20} {status}")

    print("=" * 50)

    # Summary
    total = len(results)
    installed_count: int = sum(results.values())
    missing = total - installed_count

    print(f"Summary: {installed_count}/{total} components installed")

    if missing > 0:
        warning_icon = get_safe_icon("⚠️", "[WARNING]")
        print(f"{warning_icon}  {missing} components missing")
        print("Run 'python -m rxiv_maker.install.manager --repair' to fix issues")
    else:
        success_icon = get_safe_icon("✅", "[SUCCESS]")
        print(f"{success_icon} All components are installed and working!")

    print("=" * 50)


def diagnose_installation() -> dict[str, dict[str, Any]]:
    """Perform detailed diagnosis of installation issues.

    Returns:
        Dictionary with detailed diagnostic information
    """
    diagnosis = {}

    # Python diagnosis
    diagnosis["python"] = _diagnose_python()

    # LaTeX diagnosis
    diagnosis["latex"] = _diagnose_latex()

    # Node.js diagnosis
    diagnosis["nodejs"] = _diagnose_nodejs()

    # R diagnosis
    diagnosis["r"] = _diagnose_r()

    # System libraries diagnosis
    diagnosis["system_libs"] = _diagnose_system_libs()

    return diagnosis


def _diagnose_python() -> dict[str, Any]:
    """Diagnose Python installation."""
    info: dict[str, Any] = {"installed": False, "version": None, "path": None, "issues": []}

    try:
        info["installed"] = True
        info["version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        info["path"] = sys.executable

        # Check version requirement
        if sys.version_info.major != 3 or sys.version_info.minor < 11:
            info["issues"].append(f"Python 3.11+ required, found {info['version']}")
    except Exception as e:
        info["issues"].append(f"Error checking Python: {e}")

    return info


def _diagnose_latex() -> dict[str, Any]:
    """Diagnose LaTeX installation."""
    info: dict[str, Any] = {"installed": False, "version": None, "path": None, "issues": []}

    try:
        # Check pdflatex
        pdflatex_path = shutil.which("pdflatex")
        if pdflatex_path:
            info["path"] = pdflatex_path
            result = subprocess.run(["pdflatex", "--version"], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                info["installed"] = True
                # Extract version from output
                lines = result.stdout.split("\n")
                for line in lines:
                    if "pdfTeX" in line:
                        info["version"] = line.strip()
                        break
            else:
                info["issues"].append("pdflatex found but not working")
        else:
            info["issues"].append("pdflatex not found in PATH")
    except Exception as e:
        info["issues"].append(f"Error checking LaTeX: {e}")

    return info


def _diagnose_nodejs() -> dict[str, Any]:
    """Diagnose Node.js installation."""
    info: dict[str, Any] = {
        "installed": False,
        "version": None,
        "path": None,
        "npm_version": None,
        "issues": [],
    }

    try:
        # Check Node.js
        node_path = shutil.which("node")
        if node_path:
            info["path"] = node_path
            result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                info["version"] = result.stdout.strip()

                # Check npm
                npm_result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=10)

                if npm_result.returncode == 0:
                    info["npm_version"] = npm_result.stdout.strip()
                    info["installed"] = True
                else:
                    info["issues"].append("npm not working")
            else:
                info["issues"].append("node found but not working")
        else:
            info["issues"].append("node not found in PATH")
    except Exception as e:
        info["issues"].append(f"Error checking Node.js: {e}")

    return info


def _diagnose_r() -> dict[str, Any]:
    """Diagnose R installation."""
    info: dict[str, Any] = {"installed": False, "version": None, "path": None, "issues": []}

    try:
        # Check R
        r_path = shutil.which("R")
        if r_path:
            info["path"] = r_path
            result = subprocess.run(["R", "--version"], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                info["installed"] = True
                # Extract version from output
                lines = result.stdout.split("\n")
                for line in lines:
                    if "R version" in line:
                        info["version"] = line.strip()
                        break
            else:
                info["issues"].append("R found but not working")
        else:
            info["issues"].append("R not found in PATH (optional)")
    except Exception as e:
        info["issues"].append(f"Error checking R: {e}")

    return info


def _diagnose_system_libs() -> dict[str, Any]:
    """Diagnose system libraries installation."""
    info: dict[str, Any] = {"installed": False, "missing_packages": [], "issues": []}

    # Check key Python packages
    packages_to_check = ["matplotlib", "PIL", "numpy", "pandas", "scipy"]

    for package in packages_to_check:
        try:
            __import__(package)
        except ImportError:
            info["missing_packages"].append(package)

    if not info["missing_packages"]:
        info["installed"] = True
    else:
        info["issues"].append(f"Missing packages: {', '.join(info['missing_packages'])}")

    return info
