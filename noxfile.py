"""Nox configuration for Rxiv-Maker testing using uv."""

import nox

ENGINES = ["local", "docker"]  # Add "podman" here when ready
PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12"]

# Set default sessions
nox.options.sessions = ["lint", "tests"]


@nox.session(python=PYTHON_VERSIONS)
@nox.parametrize("engine", ENGINES)
def tests(session, engine):
    """Run the test suite against a specific Python version and engine.

    Examples:
        nox -s tests(python="3.11", engine="local")
        nox -s tests(engine="docker")
    """
    # Install dependencies using uv
    session.run("uv", "pip", "install", "-e", ".", external=True)
    session.run(
        "uv",
        "pip",
        "install",
        "pytest>=7.4.0",
        "pytest-timeout>=2.4.0",
        "pytest-xdist>=3.8.0",
        external=True,
    )

    # Check if the engine command exists
    if engine != "local":
        try:
            session.run(engine, "--version", external=True, silent=True)
        except Exception:
            session.skip(f"{engine.capitalize()} is not available on this system")

    session.log(f"Running tests with engine: {engine}")

    # Pass any extra arguments to pytest, e.g., for selecting specific tests
    # nox -s tests -- -k "test_cli_version"
    session.run(
        "pytest",
        f"--engine={engine}",
        "-v",
        "--timeout=120",
        "-m",
        "not slow",
        "-n",
        "auto",  # Enable parallel execution with pytest-xdist
        "--dist=worksteal",  # Optimize work distribution
        *session.posargs,
    )


@nox.session(name="test-fast", python="3.11")
def test_fast(session):
    """Run tests with maximum parallelization and class-scoped fixtures."""
    # Install dependencies using uv
    session.run("uv", "pip", "install", "-e", ".", external=True)
    session.run(
        "uv",
        "pip",
        "install",
        "pytest>=7.4.0",
        "pytest-timeout>=2.4.0",
        "pytest-xdist>=3.8.0",
        external=True,
    )

    session.log("Running optimized test suite with maximum parallelization")

    # Run with maximum performance settings
    session.run(
        "pytest",
        "--engine=local",
        "-v",
        "--timeout=120",
        "-m",
        "not slow",
        "-n",
        "auto",  # Auto-detect CPU cores
        "--dist=worksteal",  # Optimize work distribution
        "--tb=short",  # Shorter traceback for speed
        "--no-cov",  # Disable coverage for speed
        *session.posargs,
    )


@nox.session(python="3.11")
@nox.parametrize("engine", ENGINES)
def integration(session, engine):
    """Run integration tests with specified engine (local or docker).

    Examples:
        nox -s integration(engine="docker")
        nox -s integration
    """
    # Install with uv
    session.run("uv", "pip", "install", "-e", ".", external=True)
    session.run(
        "uv",
        "pip",
        "install",
        "pytest>=7.4.0",
        "pytest-timeout>=2.4.0",
        "pytest-xdist>=3.8.0",
        "pytest-notebook>=0.10.0",
        external=True,
    )

    # Check engine availability
    if engine != "local":
        try:
            session.run(engine, "--version", external=True, silent=True)
        except Exception:
            session.skip(f"{engine.capitalize()} is not available on this system")

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


@nox.session(python="3.11")
@nox.parametrize("engine", ENGINES)
def coverage(session, engine):
    """Run tests with coverage reporting using specified engine.

    Examples:
        nox -s coverage(engine="local")
        nox -s coverage(engine="docker")
    """
    # Install with uv
    session.run("uv", "pip", "install", "-e", ".", external=True)
    session.run(
        "uv",
        "pip",
        "install",
        "pytest>=7.4.0",
        "pytest-timeout>=2.4.0",
        "pytest-xdist>=3.8.0",
        "pytest-cov>=4.0",
        "coverage[toml]>=7.0",
        "pytest-notebook>=0.10.0",
        external=True,
    )

    # Check engine availability
    if engine != "local":
        try:
            session.run(engine, "--version", external=True, silent=True)
        except Exception:
            session.skip(f"{engine.capitalize()} is not available on this system")

    session.log(f"Running coverage tests with engine: {engine}")

    session.run(
        "pytest",
        "tests/",
        f"--engine={engine}",
        "--cov=src/rxiv_maker",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v",
        "-m",
        "not slow",
        *session.posargs,
    )


@nox.session(python="3.11")
def lint(session):
    """Run linters."""
    session.run("uv", "pip", "install", "ruff>=0.8.0", external=True)
    session.run("ruff", "check", "src/", "tests/")


@nox.session(python="3.11")
def format(session):
    """Format code with ruff."""
    session.run("uv", "pip", "install", "ruff>=0.8.0", external=True)
    session.run("ruff", "format", "src/", "tests/")
    session.run("ruff", "check", "--fix", "src/", "tests/")


@nox.session(python="3.11")
def type_check(session):
    """Run type checking."""
    session.run("uv", "pip", "install", "-e", ".", external=True)
    session.run(
        "uv",
        "pip",
        "install",
        "mypy>=1.0",
        "types-PyYAML>=6.0.0",
        "types-requests",
        external=True,
    )
    session.run("mypy", "src/")


@nox.session(python=["3.11", "3.12"])
def performance(session):
    """Run performance benchmarks."""
    session.run("uv", "pip", "install", "-e", ".", external=True)
    session.run(
        "uv",
        "pip",
        "install",
        "pytest>=7.4.0",
        "pytest-benchmark>=4.0.0",
        "pytest-json-report>=1.5.0",
        external=True,
    )

    # Run benchmarks with detailed reporting
    session.run(
        "pytest",
        "tests/performance/",
        "-v",
        "--benchmark-only",
        "--benchmark-json=benchmark_results.json",
        "--benchmark-save=performance_baseline",
        "--benchmark-sort=mean",
        "--benchmark-columns=min,max,mean,stddev,median,rounds,iterations",
        *session.posargs,
    )

    # Generate performance report
    session.run(
        "python",
        "-c",
        """
import json
import sys
from pathlib import Path

if Path('benchmark_results.json').exists():
    with open('benchmark_results.json') as f:
        data = json.load(f)

    print('\\n=== PERFORMANCE BENCHMARK SUMMARY ===')
    for benchmark in data.get('benchmarks', []):
        name = benchmark['name']
        stats = benchmark['stats']
        mean_time = stats['mean']
        stddev = stats['stddev']
        print(f'{name:<50} {mean_time:.4f}s ± {stddev:.4f}s')
    print('\\n' + '='*60)
else:
    print('No benchmark results found')
        """,
        external=True,
    )


@nox.session(python="3.11")
def security(session):
    """Run security checks."""
    session.run("uv", "pip", "install", "-e", ".", external=True)
    session.run(
        "uv", "pip", "install", "bandit[toml]>=1.7.0", "safety>=2.3.0", external=True
    )

    # Run bandit security linter
    session.run("bandit", "-r", "src/", "-f", "json", "-o", "bandit-report.json")

    # Check for known vulnerabilities
    session.run("safety", "check", "--json", "--output", "safety-report.json")


# Quick test sessions for development
@nox.session(python="3.11", name="test-quick")
def test_quick(session):
    """Run a quick subset of tests for rapid development feedback."""
    session.run("uv", "pip", "install", "-e", ".", external=True)
    session.run("uv", "pip", "install", "pytest>=7.4.0", external=True)

    session.run(
        "pytest", "tests/unit/", "-v", "--tb=short", "-k", "not slow", *session.posargs
    )


# Comprehensive test session that runs everything
@nox.session(python="3.11", name="test-all")
@nox.parametrize("engine", ENGINES)
def test_all(session, engine):
    """Run all tests including slow ones with specified engine."""
    session.run("uv", "pip", "install", "-e", ".", external=True)
    session.run(
        "uv",
        "pip",
        "install",
        "pytest>=7.4.0",
        "pytest-timeout>=2.4.0",
        "pytest-notebook>=0.10.0",
        "pytest-xdist>=3.8.0",
        external=True,
    )

    # Check engine availability
    if engine != "local":
        try:
            session.run(engine, "--version", external=True, silent=True)
        except Exception:
            session.skip(f"{engine.capitalize()} is not available on this system")

    session.log(f"Running all tests with engine: {engine}")

    session.run("pytest", f"--engine={engine}", "-v", "--timeout=300", *session.posargs)
