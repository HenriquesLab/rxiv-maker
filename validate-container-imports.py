#!/usr/bin/env python3

"""Container Import Validation Script.

This script validates that all critical imports work correctly in the
Docker container environment after implementing runtime dependency injection.

Usage:
    # Run inside Docker container
    python3 validate-container-imports.py

    # Or as part of container testing
    docker run --rm -v $PWD:/workspace henriqueslab/rxiv-maker-base:latest \
        python3 /workspace/validate-container-imports.py
"""

import sys
from pathlib import Path


# Colors for output
class Colors:
    GREEN = "\033[0;32m"
    RED = "\033[0;31m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"


def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.NC}")


def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.NC}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.NC}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.NC}")


def test_import(module_name, import_statement, description):
    """Test a specific import and return success status."""
    try:
        exec(import_statement)
        print_success(f"{description}: {module_name}")
        return True
    except ImportError as e:
        print_error(f"{description}: {module_name} - {e}")
        return False
    except Exception as e:
        print_error(f"{description}: {module_name} - Unexpected error: {e}")
        return False


def main():
    print("=" * 70)
    print("   Container Import Validation")
    print("=" * 70)
    print()

    # Setup Python path for workspace
    workspace_src = Path("/workspace/src")
    if workspace_src.exists():
        sys.path.insert(0, str(workspace_src))
        print_info(f"Added {workspace_src} to Python path")
    else:
        print_warning("Workspace src directory not found, using current directory")
        sys.path.insert(0, "src")

    print_info(f"Python version: {sys.version}")
    print_info(f"Python executable: {sys.executable}")
    print()

    # Test categories
    tests = []

    # 1. Essential system dependencies that were missing
    print_info("Testing essential system dependencies...")
    tests.extend(
        [
            ("platformdirs", "import platformdirs", "Platform directories"),
            ("click", "import click", "Click CLI framework"),
            ("rich", "import rich", "Rich console library"),
            ("rich.console", "from rich.console import Console", "Rich console"),
            ("packaging", "import packaging", "Python packaging"),
            ("tomli_w", "import tomli_w", "TOML writer"),
            ("typing_extensions", "import typing_extensions", "Typing extensions"),
        ]
    )

    # 2. Core scientific dependencies
    print_info("Testing core scientific dependencies...")
    tests.extend(
        [
            ("numpy", "import numpy as np", "NumPy"),
            ("pandas", "import pandas as pd", "Pandas"),
            ("matplotlib", "import matplotlib.pyplot as plt", "Matplotlib"),
            ("seaborn", "import seaborn as sns", "Seaborn"),
            ("yaml", "import yaml", "PyYAML"),
            ("requests", "import requests", "Requests"),
            ("PIL", "from PIL import Image", "Pillow"),
            ("pypdf", "import pypdf", "PyPDF"),
        ]
    )

    # 3. Rxiv-maker specific imports that were failing
    print_info("Testing rxiv-maker specific imports...")
    tests.extend(
        [
            (
                "rxiv_maker.utils.cache_utils",
                "from rxiv_maker.utils.cache_utils import get_cache_dir",
                "Cache utilities",
            ),
            (
                "rxiv_maker.utils.bibliography_cache",
                "from rxiv_maker.utils.bibliography_cache import get_bibliography_cache",
                "Bibliography cache",
            ),
            (
                "rxiv_maker.utils.advanced_cache",
                "from rxiv_maker.utils.advanced_cache import AdvancedCache",
                "Advanced cache",
            ),
            (
                "rxiv_maker.validators.doi_validator",
                "from rxiv_maker.validators.doi_validator import DOIValidator",
                "DOI validator",
            ),
            (
                "rxiv_maker.utils.platform",
                "from rxiv_maker.utils.platform import platform_detector",
                "Platform detector",
            ),
            (
                "rxiv_maker.engines.factory",
                "from rxiv_maker.engines.factory import get_container_engine",
                "Container engine factory",
            ),
            ("rxiv_maker.cli.main", "from rxiv_maker.cli.main import main", "CLI main"),
        ]
    )

    # 4. Test specific functionality that was broken
    print_info("Testing specific functionality...")
    tests.extend(
        [
            (
                "cache_dir_function",
                "from rxiv_maker.utils.cache_utils import get_cache_dir; get_cache_dir()",
                "Cache directory function",
            ),
            (
                "platform_detection",
                "from rxiv_maker.utils.platform import platform_detector; platform_detector.detect_os()",
                "Platform detection",
            ),
            (
                "doi_validation_basic",
                "from rxiv_maker.validators.doi_validator import DOIValidator; DOIValidator('/tmp')",
                "DOI validator instantiation",
            ),
        ]
    )

    # Run all tests
    successful = 0
    failed = 0

    for module, import_stmt, description in tests:
        if test_import(module, import_stmt, description):
            successful += 1
        else:
            failed += 1

    print()
    print("=" * 70)
    print("   Validation Results")
    print("=" * 70)

    total = successful + failed
    success_rate = (successful / total * 100) if total > 0 else 0

    print(f"Total tests: {total}")
    print_success(f"Successful: {successful}")
    if failed > 0:
        print_error(f"Failed: {failed}")
    else:
        print_success(f"Failed: {failed}")
    print(f"Success rate: {success_rate:.1f}%")

    print()
    if failed == 0:
        print_success("🎉 All imports validated successfully!")
        print_success("Container environment is ready for rxiv-maker!")
    else:
        print_error("❌ Some imports failed. Container environment needs attention.")
        print_info("Check the failed imports above and ensure:")
        print_info("1. Base image has all required dependencies")
        print_info("2. Runtime dependency injection completed successfully")
        print_info("3. Python path includes the workspace src directory")

    print()

    # Additional environment checks
    print_info("Additional environment checks...")

    # Check UV availability
    import subprocess

    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        print_success(f"UV package manager: {result.stdout.strip()}")
    except FileNotFoundError:
        print_error("UV package manager not found")

    # Check workspace setup
    if Path("/workspace").exists():
        workspace_files = list(Path("/workspace").glob("*"))
        print_success(f"Workspace mounted: {len(workspace_files)} items found")

        if Path("/workspace/pyproject.toml").exists():
            print_success("pyproject.toml found in workspace")
        else:
            print_warning("pyproject.toml not found in workspace")
    else:
        print_warning("Workspace not mounted to /workspace")

    # Return appropriate exit code
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
