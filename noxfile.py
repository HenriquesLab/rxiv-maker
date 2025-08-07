"""Nox configuration for Rxiv-Maker testing using uv."""

import nox

# Configure nox to use uv as the default backend for faster environment creation
nox.options.default_venv_backend = "uv"

# Enable environment reuse to reduce disk usage and improve performance
nox.options.reuse_existing_virtualenvs = True

# Stop on first failure for faster feedback during development
nox.options.stop_on_first_error = False

# Configuration constants
ENGINES = ["local", "docker"]  # Add "podman" here when ready
PYTHON_VERSIONS = [
    "3.11",
    "3.12",
    "3.13",
]  # Updated to match pyproject.toml requires-python >= 3.11

# Backend configurations for testing different environments
VENV_BACKENDS = ["uv", "conda", "mamba", "venv"]

# Common test dependencies - centralized to avoid repetition
TEST_DEPS = [
    "pytest>=7.4.0",
    "pytest-cov>=4.0",
    "pytest-timeout>=2.4.0",
    "pytest-xdist>=3.8.0",
]

# Set default sessions for local development workflow
nox.options.sessions = ["format", "lint", "test_local"]


# Helper Functions
def install_deps(session, extra_deps=None, backend=None):
    """Install project and test dependencies efficiently.
    
    Args:
        session: nox session
        extra_deps: additional dependencies to install
        backend: backend to use (uv, conda, mamba, venv, None for auto-detect)
    """
    extra_deps = extra_deps or []

    # Auto-detect backend if not specified
    if backend is None:
        backend = getattr(session, 'venv_backend', 'uv')

    if backend in ["conda", "mamba"]:
        # Use conda/mamba for installation
        session.conda_install("-c", "conda-forge", "pip")
        session.install("-e", ".")
        session.install(*(TEST_DEPS + extra_deps))
    elif backend == "uv":
        # Use uv (current default)
        session.run("uv", "pip", "install", "-e", ".", external=True)
        session.run("uv", "pip", "install", *(TEST_DEPS + extra_deps), external=True)
    else:
        # Use standard pip (venv backend)
        session.install("-e", ".")
        session.install(*(TEST_DEPS + extra_deps))


def check_backend_availability(session, backend):
    """Check if the specified backend is available on the system."""
    if backend in ["conda", "mamba"]:
        try:
            session.run(backend, "--version", external=True, silent=True)
        except Exception:
            session.skip(f"{backend.capitalize()} is not available on this system")


def check_engine_availability(session, engine):
    """Check if the specified engine is available on the system."""
    if engine != "local":
        try:
            session.run(engine, "--version", external=True, silent=True)
        except Exception:
            session.skip(f"{engine.capitalize()} is not available on this system")


# Local Development Sessions
@nox.session(python="3.11", reuse_venv=True)
def format(session):
    """Format code with ruff (auto-fix)."""
    session.run("uv", "pip", "install", "ruff>=0.8.0", external=True)
    session.run("ruff", "format", "src/", "tests/")
    session.run("ruff", "check", "--fix", "src/", "tests/")


@nox.session(python="3.11", reuse_venv=True)
def lint(session):
    """Run comprehensive linting checks."""
    session.run("uv", "pip", "install", "ruff>=0.8.0", external=True)
    session.run("ruff", "check", "src/", "tests/")


@nox.session(python="3.11", reuse_venv=True)
def type_check(session):
    """Run type checking with mypy."""
    install_deps(
        session,
        extra_deps=[
            "mypy>=1.0",
            "types-PyYAML>=6.0.0",
            "types-requests",
        ],
    )
    session.run("mypy", "src/")


@nox.session(python="3.11", name="test_local", reuse_venv=True)
def test_local(session):
    """Run fast unit tests for local development feedback."""
    install_deps(session)

    session.log("Running optimized test suite for local development")
    session.run(
        "pytest",
        "tests/unit/",
        "--engine=local",
        "-v",
        "--timeout=120",
        "-m",
        "not slow",
        "-n",
        "auto",  # Parallel execution
        "--dist=worksteal",  # Optimize work distribution
        "--tb=short",  # Shorter traceback for speed
        "--no-cov",  # Skip coverage for speed
        *session.posargs,
    )


# CI/Matrix Sessions - Optimized to reduce environment redundancy
@nox.session(python=PYTHON_VERSIONS, reuse_venv=True)
@nox.parametrize(
    "test_config",
    [
        ("unit", "local"),  # Unit tests only run on local (engine-agnostic)
        ("integration", "local"),  # Integration tests on both engines
        ("integration", "docker"),
    ],
)
def test_matrix(session, test_config):
    """Optimized matrix session for CI: reduced redundancy compared to full matrix.

    Examples:
        nox -s test_matrix(python="3.11", test_config="('unit', 'local')")
        nox -s test_matrix(test_config="('integration', 'docker')")
    """
    test_set, engine = test_config
    install_deps(session)

    # Check engine availability
    check_engine_availability(session, engine)

    session.log(f"Running {test_set} tests with engine: {engine}")

    # Configure test directory and timeout based on test set
    test_dir = f"tests/{test_set}/"
    timeout = 180 if test_set == "integration" else 120

    # Prepare pytest arguments
    args = [
        "pytest",
        test_dir,
        f"--engine={engine}",
        "-v",
        f"--timeout={timeout}",
        "-m",
        "not slow",
    ]

    # Add parallelization for unit tests only (integration tests may have conflicts)
    if test_set == "unit":
        args.extend(["-n", "auto", "--dist=worksteal"])
    elif test_set == "integration":
        args.extend(["-s"])  # Show output for integration tests

    # Add coverage for primary matrix cell only
    if session.python == "3.11" and engine == "local" and test_set == "unit":
        args.extend(
            [
                "--cov=src/rxiv_maker",
                f"--cov-report=xml:coverage-{session.python}-{engine}-{test_set}.xml",
                "--cov-report=term-missing",
            ]
        )

    args.extend(session.posargs)
    session.run(*args)


@nox.session(python=PYTHON_VERSIONS, reuse_venv=True)
@nox.parametrize("engine", ENGINES)
def test_ci(session, engine):
    """Primary CI session - backward compatible with existing GitHub Actions.

    NOTE: This session is kept for backward compatibility but the optimized
    test_matrix session is recommended for new workflows.

    Examples:
        nox -s test_ci(python="3.11", engine="local")
        nox -s test_ci(engine="docker")
    """
    install_deps(session)
    check_engine_availability(session, engine)

    session.log(f"Running CI test suite with engine: {engine}")

    session.run(
        "pytest",
        f"--engine={engine}",
        "-v",
        "--timeout=120",
        "-m",
        "not slow",
        "-n",
        "auto",
        "--dist=worksteal",
        *session.posargs,
    )


# Comprehensive Testing Sessions
@nox.session(python="3.11", reuse_venv=True)
@nox.parametrize("engine", ENGINES)
def test_full(session, engine):
    """Run comprehensive tests including slow tests with specified engine."""
    install_deps(session)
    check_engine_availability(session, engine)

    session.log(f"Running comprehensive test suite with engine: {engine}")

    session.run(
        "pytest",
        f"--engine={engine}",
        "-v",
        "--timeout=300",  # Longer timeout for slow tests
        *session.posargs,
    )


@nox.session(python="3.11", reuse_venv=True)
@nox.parametrize("engine", ENGINES)
def integration(session, engine):
    """Run integration tests with specified engine (backward compatible).

    Examples:
        nox -s integration(engine="docker")
        nox -s integration
    """
    install_deps(session)
    check_engine_availability(session, engine)

    session.log(f"Running integration tests with engine: {engine}")

    session.run(
        "pytest",
        "tests/integration/",
        f"--engine={engine}",
        "-v",
        "-s",
        "--timeout=180",
        "-m",
        "not slow",
        *session.posargs,
    )


# Conda/Mamba Backend Testing Sessions
@nox.session(python=PYTHON_VERSIONS, venv_backend="conda", reuse_venv=True)
@nox.parametrize("engine", ENGINES)
def test_conda(session, engine):
    """Test with conda environments across engines.
    
    Examples:
        nox -s test_conda(python="3.11", engine="local")
        nox -s test_conda(engine="docker")  # Run with all Python versions
    """
    check_backend_availability(session, "conda")
    install_deps(session, backend="conda")
    check_engine_availability(session, engine)

    session.log(f"Running tests with conda backend and {engine} engine")

    session.run(
        "pytest",
        f"--engine={engine}",
        "-v",
        "--timeout=180",
        "-m",
        "not slow",
        "-n",
        "auto" if engine == "local" else "1",  # Parallel only for local
        "--dist=worksteal" if engine == "local" else "",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS, venv_backend="mamba", reuse_venv=True)
@nox.parametrize("engine", ENGINES)
def test_mamba(session, engine):
    """Test with mamba environments across engines.
    
    Examples:
        nox -s test_mamba(python="3.11", engine="local")
        nox -s test_mamba(engine="docker")
    """
    check_backend_availability(session, "mamba")
    install_deps(session, backend="mamba")
    check_engine_availability(session, engine)

    session.log(f"Running tests with mamba backend and {engine} engine")

    session.run(
        "pytest",
        f"--engine={engine}",
        "-v",
        "--timeout=180",
        "-m",
        "not slow",
        "-n",
        "auto" if engine == "local" else "1",  # Parallel only for local
        "--dist=worksteal" if engine == "local" else "",
        *session.posargs,
    )


@nox.session(python="3.11", reuse_venv=True)
@nox.parametrize("backend", VENV_BACKENDS)
def test_cross_backend(session, backend):
    """Test across different virtual environment backends with local engine.
    
    This session tests rxiv-maker compatibility with different Python environment
    management systems to ensure consistent behavior regardless of how Python
    environments are managed.
    
    Examples:
        nox -s test_cross_backend(backend="conda")
        nox -s test_cross_backend(backend="mamba")
        nox -s test_cross_backend(backend="uv")
    """
    # Set backend for session
    if backend in ["conda", "mamba"]:
        # Need to recreate session with correct backend
        session.skip(f"Use 'nox -s test_{backend}' instead for {backend} backend testing")

    check_backend_availability(session, backend)
    install_deps(session, backend=backend)

    session.log(f"Running cross-backend tests with {backend}")

    # Focus on environment detection and platform-specific tests
    session.run(
        "pytest",
        "tests/unit/test_platform_detector.py",
        "tests/unit/test_conda_platform_detection.py",
        "-v",
        "--timeout=120",
        "-k", "conda or platform or environment",
        *session.posargs,
    )


@nox.session(python="3.11", venv_backend="conda", reuse_venv=True)
def conda_integration(session):
    """Run comprehensive conda environment integration tests.
    
    This session specifically tests conda environment detection, dependency
    installation, and build processes to ensure full conda compatibility.
    """
    check_backend_availability(session, "conda")
    install_deps(session, backend="conda")

    session.log("Running comprehensive conda integration tests")

    # Test environment detection
    session.run(
        "pytest",
        "tests/unit/test_platform_detector.py",
        "-v",
        "-k", "conda",
        *session.posargs,
    )

    # Test dependency checking with conda
    session.run(
        "pytest",
        "tests/unit/test_conda_installation_manager.py",
        "-v",
        *session.posargs,
    )

    # Test installation manager conda support
    session.run(
        "pytest",
        "tests/unit/test_install*",
        "-v",
        "-k", "conda",
        *session.posargs,
    )


# Advanced Features
@nox.session(python="3.11", reuse_venv=True)
def coverage(session):
    """Combine coverage reports from CI runs and generate final report."""
    install_deps(session, extra_deps=["coverage[toml]>=7.0"])

    session.log("Combining coverage data from parallel CI runs")

    # Combine all coverage files from matrix runs
    session.run("coverage", "combine")

    # Generate reports with failure threshold
    session.run("coverage", "report", "--fail-under=85")
    session.run("coverage", "html", "-d", "coverage_html")
    session.run("coverage", "xml", "-o", "coverage.xml")

    session.log("Coverage reports generated: coverage_html/, coverage.xml")


@nox.session(python="3.11", reuse_venv=True)
def docs(session):
    """Generate API documentation using lazydocs."""
    install_deps(session, extra_deps=["lazydocs>=0.4.8"])

    session.log("Generating API documentation")

    # Run the documentation generation
    session.run("python", "src/rxiv_maker/engine/generate_docs.py")

    session.log("API documentation generated in docs/api/ directory")


@nox.session(python="3.11", reuse_venv=True)
def security(session):
    """Run comprehensive security checks."""
    install_deps(session, extra_deps=["bandit[toml]>=1.7.0", "safety>=2.3.0"])

    session.log("Running security analysis")

    # Run bandit security linter
    session.run("bandit", "-r", "src/", "-f", "json", "-o", "bandit-report.json")

    # Check for known vulnerabilities
    session.run("safety", "check", "--json", "--output", "safety-report.json")

    session.log("Security reports generated: bandit-report.json, safety-report.json")


# Binary Testing
@nox.session(python="3.11", name="test_binary", reuse_venv=True)
def test_binary(session):
    """Test binary build process with PyInstaller."""
    import os
    import platform
    import tempfile

    session.log("Testing binary build process")

    # Install dependencies
    install_deps(session, extra_deps=["pyinstaller>=6.0"])

    # Create temporary directory for build
    with tempfile.TemporaryDirectory() as temp_dir:
        spec_file = os.path.join(temp_dir, "rxiv-maker.spec")

        # Determine binary name based on platform
        binary_name = "rxiv.exe" if platform.system() == "Windows" else "rxiv"

        # Get absolute paths
        project_root = os.getcwd()
        src_path = os.path.join(project_root, "src")
        entry_script = os.path.join(project_root, "src/rxiv_maker/rxiv_maker_cli.py")

        # Create PyInstaller spec file
        spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

# Add the src directory to Python path
src_path = r'{src_path}'
if src_path not in sys.path:
    sys.path.insert(0, src_path)

a = Analysis(
    [r'{entry_script}'],
    pathex=[src_path],
    binaries=[],
    data=[],
    hiddenimports=[
        'rxiv_maker',
        'rxiv_maker.cli',
        'rxiv_maker.engine',
        'rxiv_maker.converters',
        'rxiv_maker.processors',
        'rxiv_maker.utils',
        'rxiv_maker.validators',
        'rxiv_maker.install',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{binary_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX for testing
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""

        # Write spec file
        with open(spec_file, "w") as f:
            f.write(spec_content)

        session.log("Created PyInstaller spec file")

        # Test PyInstaller spec file compilation
        try:
            session.run(
                "pyinstaller",
                spec_file,
                "--clean",
                "--noconfirm",
                "--distpath",
                os.path.join(temp_dir, "dist"),
                "--workpath",
                os.path.join(temp_dir, "build"),
                external=True,
            )
            session.log("✅ PyInstaller spec file compiled successfully")
        except Exception as e:
            session.error(f"❌ PyInstaller compilation failed: {e}")
            return

        # Check if binary was created
        binary_path = os.path.join(temp_dir, "dist", binary_name)
        if os.path.exists(binary_path):
            session.log(f"✅ Binary created: {binary_path}")

            # Test basic binary functionality
            try:
                session.run(binary_path, "--version", external=True)
                session.log("✅ Binary --version works")
            except Exception as e:
                session.log(f"⚠️  Binary --version failed: {e}")

            try:
                session.run(binary_path, "--help", external=True)
                session.log("✅ Binary --help works")
            except Exception as e:
                session.log(f"⚠️  Binary --help failed: {e}")

        else:
            session.error(f"❌ Binary not found at {binary_path}")

    session.log("Binary build test completed")


# Legacy/Backward Compatibility Sessions - Reduced to essential only
@nox.session(python=PYTHON_VERSIONS, reuse_venv=True)
@nox.parametrize("engine", ENGINES)
def tests(session, engine):
    """Legacy session name for backward compatibility with existing workflows."""
    # Delegate to the new test_ci session
    test_ci(session, engine)


# Environment Management Sessions
@nox.session(python=False)
def clean(session):
    """Clean up nox environments to free disk space.

    This session removes old and unused nox virtual environments.
    Use with caution as this will delete all existing environments.

    Examples:
        nox -s clean                    # Interactive cleanup
        nox -s clean -- --all           # Clean all environments
        nox -s clean -- --older-than 7  # Clean environments older than 7 days
    """
    import shutil
    import time
    from pathlib import Path

    nox_dir = Path(".nox")
    if not nox_dir.exists():
        session.log("No .nox directory found - nothing to clean")
        return

    # Parse arguments
    clean_all = "--all" in session.posargs
    older_than_days = None

    for i, arg in enumerate(session.posargs):
        if arg == "--older-than" and i + 1 < len(session.posargs):
            try:
                older_than_days = int(session.posargs[i + 1])
            except ValueError:
                session.error("Invalid --older-than value. Must be a number.")

    current_time = time.time()
    total_size_before = 0
    total_size_after = 0

    # Calculate initial size
    for env_dir in nox_dir.iterdir():
        if env_dir.is_dir():
            size = sum(f.stat().st_size for f in env_dir.rglob("*") if f.is_file())
            total_size_before += size

    session.log(f"Current .nox directory size: {total_size_before / (1024**3):.2f} GB")

    environments_to_remove = []

    for env_dir in nox_dir.iterdir():
        if not env_dir.is_dir():
            continue

        env_age_days = (current_time - env_dir.stat().st_mtime) / (24 * 3600)
        size = sum(f.stat().st_size for f in env_dir.rglob("*") if f.is_file())
        size_mb = size / (1024**2)

        should_remove = False
        reason = ""

        if clean_all:
            should_remove = True
            reason = "cleaning all environments"
        elif older_than_days and env_age_days > older_than_days:
            should_remove = True
            reason = f"older than {older_than_days} days (age: {env_age_days:.1f} days)"

        if should_remove:
            environments_to_remove.append((env_dir, size, reason))
            session.log(f"Will remove: {env_dir.name} ({size_mb:.1f} MB) - {reason}")

    if not environments_to_remove:
        session.log("No environments to remove based on criteria")
        return

    # Confirm removal unless --all is specified
    if not clean_all:
        response = input(f"\nRemove {len(environments_to_remove)} environment(s)? [y/N]: ")
        if response.lower() not in ["y", "yes"]:
            session.log("Cleanup cancelled")
            return

    # Remove environments
    removed_size = 0
    for env_dir, size, _reason in environments_to_remove:
        try:
            shutil.rmtree(env_dir)
            removed_size += size
            session.log(f"✅ Removed: {env_dir.name}")
        except Exception as e:
            session.log(f"❌ Failed to remove {env_dir.name}: {e}")

    total_size_after = total_size_before - removed_size

    session.log("\n📊 Cleanup Summary:")
    session.log(f"  • Removed: {len(environments_to_remove)} environments")
    session.log(f"  • Freed space: {removed_size / (1024**3):.2f} GB")
    session.log(f"  • New .nox size: {total_size_after / (1024**3):.2f} GB")
    session.log(f"  • Space reduction: {(removed_size / total_size_before) * 100:.1f}%")


@nox.session(python=False)
def clean_all(session):
    """Clean all nox environments - equivalent to 'nox -s clean -- --all'."""
    import shutil
    from pathlib import Path

    nox_dir = Path(".nox")
    if not nox_dir.exists():
        session.log("No .nox directory found - nothing to clean")
        return

    total_size_before = 0

    # Calculate initial size
    for env_dir in nox_dir.iterdir():
        if env_dir.is_dir():
            size = sum(f.stat().st_size for f in env_dir.rglob("*") if f.is_file())
            total_size_before += size

    session.log(f"Current .nox directory size: {total_size_before / (1024**3):.2f} GB")

    environments_to_remove = []

    for env_dir in nox_dir.iterdir():
        if not env_dir.is_dir():
            continue

        size = sum(f.stat().st_size for f in env_dir.rglob("*") if f.is_file())
        size_mb = size / (1024**2)
        environments_to_remove.append((env_dir, size, "cleaning all environments"))
        session.log(f"Will remove: {env_dir.name} ({size_mb:.1f} MB)")

    if not environments_to_remove:
        session.log("No environments to remove")
        return

    # Remove environments
    removed_size = 0
    for env_dir, size, _reason in environments_to_remove:
        try:
            shutil.rmtree(env_dir)
            removed_size += size
            session.log(f"✅ Removed: {env_dir.name}")
        except Exception as e:
            session.log(f"❌ Failed to remove {env_dir.name}: {e}")

    total_size_after = total_size_before - removed_size

    session.log("\n📊 Cleanup Summary:")
    session.log(f"  • Removed: {len(environments_to_remove)} environments")
    session.log(f"  • Freed space: {removed_size / (1024**3):.2f} GB")
    session.log(f"  • New .nox size: {total_size_after / (1024**3):.2f} GB")
    session.log(f"  • Space reduction: {(removed_size / total_size_before) * 100:.1f}%")


# Removed redundant legacy sessions: test-fast, test-quick, test-all
# These created separate environments but offered no unique functionality.
# Use these alternatives:
# - Instead of test-fast or test-quick: use 'nox -s test_local'
# - Instead of test-all: use 'nox -s test_full'
