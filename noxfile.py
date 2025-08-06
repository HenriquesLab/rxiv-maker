"""Nox configuration for Rxiv-Maker testing using uv."""

import nox

# Configure nox to use uv as the default backend for faster environment creation
nox.options.default_venv_backend = "uv"

# Configuration constants
ENGINES = ["local", "docker"]  # Add "podman" here when ready
PYTHON_VERSIONS = [
    "3.11",
    "3.12",
    "3.13",
]  # Updated to match pyproject.toml requires-python >= 3.11

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
def install_deps(session, extra_deps=None):
    """Install project and test dependencies efficiently."""
    extra_deps = extra_deps or []
    session.run("uv", "pip", "install", "-e", ".", external=True)
    session.run("uv", "pip", "install", *(TEST_DEPS + extra_deps), external=True)


def check_engine_availability(session, engine):
    """Check if the specified engine is available on the system."""
    if engine != "local":
        try:
            session.run(engine, "--version", external=True, silent=True)
        except Exception:
            session.skip(f"{engine.capitalize()} is not available on this system")


# Local Development Sessions
@nox.session(python="3.11")
def format(session):
    """Format code with ruff (auto-fix)."""
    session.run("uv", "pip", "install", "ruff>=0.8.0", external=True)
    session.run("ruff", "format", "src/", "tests/")
    session.run("ruff", "check", "--fix", "src/", "tests/")


@nox.session(python="3.11")
def lint(session):
    """Run comprehensive linting checks."""
    session.run("uv", "pip", "install", "ruff>=0.8.0", external=True)
    session.run("ruff", "check", "src/", "tests/")


@nox.session(python="3.11")
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


@nox.session(python="3.11", name="test_local")
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


# CI/Matrix Sessions
@nox.session(python=PYTHON_VERSIONS)
@nox.parametrize("engine", ENGINES)
@nox.parametrize("test_set", ["unit", "integration"])
def test_matrix(session, engine, test_set):
    """Matrix session for CI: runs unit and integration tests across engines and Python versions.

    Examples:
        nox -s test_matrix(python="3.11", engine="local", test_set="unit")
        nox -s test_matrix(engine="docker", test_set="integration")
    """
    install_deps(session)

    # Skip redundant runs - unit tests are engine-agnostic except for local
    if engine != "local" and test_set == "unit":
        session.skip("Unit tests run only for 'local' engine to avoid redundancy.")

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


@nox.session(python=PYTHON_VERSIONS)
@nox.parametrize("engine", ENGINES)
def test_ci(session, engine):
    """Primary CI session - backward compatible with existing GitHub Actions.

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
@nox.session(python="3.11")
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


@nox.session(python="3.11")
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


# Advanced Features
@nox.session(python="3.11")
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


@nox.session(python="3.11")
def docs(session):
    """Generate API documentation using lazydocs."""
    install_deps(session, extra_deps=["lazydocs>=0.4.8"])

    session.log("Generating API documentation")

    # Run the documentation generation
    session.run("python", "src/rxiv_maker/engine/generate_docs.py")

    session.log("API documentation generated in docs/api/ directory")


@nox.session(python="3.11")
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
@nox.session(python="3.11", name="test_binary")
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


# Legacy/Backward Compatibility Sessions
@nox.session(python=PYTHON_VERSIONS)
@nox.parametrize("engine", ENGINES)
def tests(session, engine):
    """Legacy session name for backward compatibility with existing workflows."""
    # Delegate to the new test_ci session
    test_ci(session, engine)


@nox.session(python="3.11", name="test-fast")
def test_fast(session):
    """Legacy session name for backward compatibility."""
    # Delegate to the new test_local session
    test_local(session)


@nox.session(python="3.11", name="test-quick")
def test_quick(session):
    """Legacy session name for backward compatibility."""
    # Delegate to the new test_local session
    test_local(session)


@nox.session(python="3.11", name="test-all")
@nox.parametrize("engine", ENGINES)
def test_all(session, engine):
    """Legacy session name for backward compatibility."""
    # Delegate to the new test_full session
    test_full(session, engine)
