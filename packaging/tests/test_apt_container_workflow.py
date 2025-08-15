#!/usr/bin/env python3
"""
Integration test suite for APT container workflow testing.

This module provides comprehensive integration tests for the rxiv-maker APT package
installation and functionality testing within Podman containers. It orchestrates
container creation, package installation, functional testing, and cleanup.

Usage:
    python -m pytest tests/integration/test_apt_container_workflow.py -v
    python tests/integration/test_apt_container_workflow.py --ubuntu-version 22.04
"""

import json
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import pytest

# Test configuration
DEFAULT_UBUNTU_VERSION = "22.04"
SUPPORTED_UBUNTU_VERSIONS = ["20.04", "22.04", "24.04"]
DEFAULT_TEST_TIMEOUT = 1800  # 30 minutes
CONTAINER_ENGINE = "podman"
PROJECT_ROOT = Path(__file__).parent.parent.parent


class ContainerTestError(Exception):
    """Custom exception for container testing errors."""

    pass


class AptContainerTester:
    """Orchestrates APT package testing in Podman containers."""

    def __init__(
        self,
        ubuntu_version: str = DEFAULT_UBUNTU_VERSION,
        container_engine: str = CONTAINER_ENGINE,
        cleanup_on_exit: bool = True,
        verbose: bool = False,
    ):
        """
        Initialize the container tester.

        Args:
            ubuntu_version: Ubuntu version to test (20.04, 22.04, 24.04)
            container_engine: Container engine to use (podman or docker)
            cleanup_on_exit: Whether to cleanup containers after tests
            verbose: Enable verbose logging
        """
        self.ubuntu_version = ubuntu_version
        self.container_engine = container_engine
        self.cleanup_on_exit = cleanup_on_exit
        self.verbose = verbose

        # Generate unique identifiers
        self.test_id = str(uuid.uuid4())[:8]
        self.container_name = f"rxiv-apt-test-{ubuntu_version}-{self.test_id}"
        self.network_name = f"rxiv-test-network-{self.test_id}"

        # Test directories
        self.temp_dir = None
        self.test_results_dir = None

        # Container state
        self.container_running = False
        self.network_created = False

    def __enter__(self):
        """Context manager entry."""
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        if self.cleanup_on_exit:
            self.cleanup()

    def setup(self):
        """Set up test environment."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp(prefix="apt-container-test-")
        self.test_results_dir = Path(self.temp_dir) / "test-results"
        self.test_results_dir.mkdir(parents=True, exist_ok=True)

        # Validate environment
        self._validate_environment()

        # Setup container infrastructure
        self._create_network()
        self._pull_ubuntu_image()

    def cleanup(self):
        """Clean up test environment."""
        if self.container_running:
            self._stop_container()

        if self.network_created:
            self._remove_network()

        # Clean up temporary directories
        if self.temp_dir and Path(self.temp_dir).exists():
            import shutil

            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _validate_environment(self):
        """Validate the test environment."""
        # Check container engine
        if not self._command_exists(self.container_engine):
            raise ContainerTestError(f"Container engine '{self.container_engine}' not found")

        # Validate Ubuntu version
        if self.ubuntu_version not in SUPPORTED_UBUNTU_VERSIONS:
            raise ContainerTestError(
                f"Unsupported Ubuntu version: {self.ubuntu_version}. Supported: {', '.join(SUPPORTED_UBUNTU_VERSIONS)}"
            )

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH."""
        return subprocess.run(["which", command], capture_output=True, check=False).returncode == 0

    def _run_command(
        self,
        cmd: List[str],
        capture_output: bool = True,
        check: bool = True,
        timeout: Optional[int] = None,
        cwd: Optional[Path] = None,
    ) -> subprocess.CompletedProcess:
        """Run a command with error handling."""
        if self.verbose:
            print(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd, capture_output=capture_output, text=True, check=check, timeout=timeout, cwd=cwd
            )

            if self.verbose and result.stdout:
                print(f"STDOUT: {result.stdout}")
            if self.verbose and result.stderr:
                print(f"STDERR: {result.stderr}")

            return result

        except subprocess.TimeoutExpired as e:
            raise ContainerTestError(f"Command timed out after {timeout}s: {' '.join(cmd)}") from e
        except subprocess.CalledProcessError as e:
            raise ContainerTestError(
                f"Command failed (exit {e.returncode}): {' '.join(cmd)}\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}"
            ) from e

    def _create_network(self):
        """Create test network."""
        try:
            # Check if network already exists
            result = self._run_command([self.container_engine, "network", "exists", self.network_name], check=False)

            if result.returncode != 0:
                # Create network
                self._run_command([self.container_engine, "network", "create", self.network_name])
                self.network_created = True

        except ContainerTestError:
            # Network creation failed - continue without dedicated network
            self.network_name = "default"

    def _remove_network(self):
        """Remove test network."""
        if self.network_created and self.network_name != "default":
            try:
                self._run_command([self.container_engine, "network", "rm", self.network_name], check=False)
            except ContainerTestError:
                pass  # Ignore cleanup errors

    def _pull_ubuntu_image(self):
        """Pull Ubuntu image."""
        image_name = f"ubuntu:{self.ubuntu_version}"
        self._run_command([self.container_engine, "pull", image_name], timeout=300)

    def create_container(self):
        """Create and start test container."""
        # Remove existing container if present
        self._run_command([self.container_engine, "rm", "-f", self.container_name], check=False)

        # Create container
        cmd = [
            self.container_engine,
            "run",
            "-d",
            "--name",
            self.container_name,
            "--network",
            self.network_name,
            "-v",
            f"{PROJECT_ROOT}:/workspace:ro",
            "-v",
            f"{self.test_results_dir}:/test-results:rw",
            f"ubuntu:{self.ubuntu_version}",
            "sleep",
            "infinity",
        ]

        self._run_command(cmd)
        self.container_running = True

        # Wait for container to be ready
        time.sleep(2)

        # Verify container is running
        result = self._run_command([self.container_engine, "container", "exists", self.container_name], check=False)

        if result.returncode != 0:
            raise ContainerTestError(f"Failed to create container: {self.container_name}")

    def _stop_container(self):
        """Stop and remove container."""
        if self.container_running:
            try:
                self._run_command([self.container_engine, "stop", self.container_name], check=False, timeout=30)

                self._run_command([self.container_engine, "rm", self.container_name], check=False)

                self.container_running = False
            except ContainerTestError:
                pass  # Ignore cleanup errors

    def exec_in_container(
        self, cmd: str, capture_output: bool = True, check: bool = True, timeout: Optional[int] = None
    ) -> subprocess.CompletedProcess:
        """Execute command in container."""
        full_cmd = [self.container_engine, "exec", self.container_name, "bash", "-c", cmd]

        return self._run_command(full_cmd, capture_output=capture_output, check=check, timeout=timeout)

    def setup_container_environment(self):
        """Set up the container base environment."""
        # Update package lists
        self.exec_in_container("apt-get update", timeout=300)

        # Install basic tools
        self.exec_in_container(
            "DEBIAN_FRONTEND=noninteractive apt-get install -y curl gnupg ca-certificates", timeout=300
        )

        # Create test user
        self.exec_in_container("useradd -m -s /bin/bash testuser")
        self.exec_in_container("echo 'testuser ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers")

    def add_apt_repository(
        self,
        repo_url: str = "https://raw.githubusercontent.com/henriqueslab/rxiv-maker/apt-repo",
        gpg_key_url: str = "https://raw.githubusercontent.com/henriqueslab/rxiv-maker/apt-repo/pubkey.gpg",
    ):
        """Add rxiv-maker APT repository to container."""
        # Add GPG key
        self.exec_in_container(
            f"curl -fsSL '{gpg_key_url}' | gpg --dearmor -o /usr/share/keyrings/rxiv-maker.gpg", timeout=60
        )

        # Add repository source
        repo_line = f"deb [arch=amd64] {repo_url} stable main"
        self.exec_in_container(f"echo '{repo_line}' > /etc/apt/sources.list.d/rxiv-maker.list")

        # Update package lists
        self.exec_in_container("apt-get update", timeout=300)

        # Verify repository is accessible
        result = self.exec_in_container("apt-cache search rxiv-maker", check=False)
        if result.returncode != 0:
            raise ContainerTestError("Repository setup failed - package not found")

    def install_package(self, package_version: Optional[str] = None):
        """Install rxiv-maker package in container."""
        if package_version:
            install_cmd = f"apt-get install -y rxiv-maker={package_version}"
        else:
            install_cmd = "apt-get install -y rxiv-maker"

        self.exec_in_container(install_cmd, timeout=600)

        # Verify installation
        result = self.exec_in_container("rxiv --version")
        if not result.stdout.strip():
            raise ContainerTestError("Package installation verification failed")

        return result.stdout.strip()

    def install_local_package(self, package_path: Path):
        """Install local .deb package in container."""
        # Copy package to container
        self._run_command(
            [self.container_engine, "cp", str(package_path), f"{self.container_name}:/tmp/rxiv-maker.deb"]
        )

        # Install with dpkg and fix dependencies
        self.exec_in_container("dpkg -i /tmp/rxiv-maker.deb || true")
        self.exec_in_container("apt-get install -f -y", timeout=600)

        # Verify installation
        result = self.exec_in_container("rxiv --version")
        if not result.stdout.strip():
            raise ContainerTestError("Local package installation verification failed")

        return result.stdout.strip()

    def test_basic_functionality(self) -> Dict[str, bool]:
        """Test basic rxiv-maker functionality."""
        tests = {}

        # Test version command
        try:
            result = self.exec_in_container("rxiv --version")
            tests["version_command"] = bool(result.stdout.strip())
        except ContainerTestError:
            tests["version_command"] = False

        # Test help command
        try:
            self.exec_in_container("rxiv --help")
            tests["help_command"] = True
        except ContainerTestError:
            tests["help_command"] = False

        # Test as regular user
        try:
            self.exec_in_container("su - testuser -c 'rxiv --version'")
            tests["user_access"] = True
        except ContainerTestError:
            tests["user_access"] = False

        # Test installation check
        try:
            self.exec_in_container("su - testuser -c 'rxiv check-installation'", timeout=120)
            tests["installation_check"] = True
        except ContainerTestError:
            tests["installation_check"] = False

        return tests

    def test_manuscript_operations(self) -> Dict[str, bool]:
        """Test manuscript operations."""
        tests = {}

        # Test manuscript initialization
        try:
            self.exec_in_container("su - testuser -c 'cd /home/testuser && rxiv init test-manuscript'")
            tests["manuscript_init"] = True
        except ContainerTestError:
            tests["manuscript_init"] = False

        # Test manuscript validation
        try:
            self.exec_in_container(
                "su - testuser -c 'cd /home/testuser/test-manuscript && rxiv validate .'", timeout=60
            )
            tests["manuscript_validation"] = True
        except ContainerTestError:
            tests["manuscript_validation"] = False

        return tests

    def test_example_manuscript(self) -> Dict[str, bool]:
        """Test with example manuscript."""
        tests = {}

        # Copy example manuscript
        try:
            self._run_command(
                [
                    self.container_engine,
                    "cp",
                    f"{PROJECT_ROOT}/EXAMPLE_MANUSCRIPT",
                    f"{self.container_name}:/home/testuser/",
                ]
            )
            self.exec_in_container("chown -R testuser:testuser /home/testuser/EXAMPLE_MANUSCRIPT")
            tests["example_copy"] = True
        except ContainerTestError:
            tests["example_copy"] = False
            return tests

        # Test validation
        try:
            self.exec_in_container(
                "su - testuser -c 'cd /home/testuser/EXAMPLE_MANUSCRIPT && rxiv validate .'", timeout=120
            )
            tests["example_validation"] = True
        except ContainerTestError:
            tests["example_validation"] = False

        return tests

    def test_security_aspects(self) -> Dict[str, bool]:
        """Test security aspects."""
        tests = {}

        # Test GPG key verification
        try:
            self.exec_in_container("gpg --list-keys --keyring /usr/share/keyrings/rxiv-maker.gpg")
            tests["gpg_key_verification"] = True
        except ContainerTestError:
            tests["gpg_key_verification"] = False

        # Test package policy
        try:
            self.exec_in_container("apt-cache policy rxiv-maker")
            tests["package_policy"] = True
        except ContainerTestError:
            tests["package_policy"] = False

        # Test file permissions (no setuid/setgid files)
        try:
            result = self.exec_in_container("find /usr -name '*rxiv*' -perm /6000", check=False)
            tests["file_permissions"] = len(result.stdout.strip()) == 0
        except ContainerTestError:
            tests["file_permissions"] = False

        return tests

    def collect_system_info(self) -> Dict:
        """Collect system information from container."""
        info = {}

        try:
            # Ubuntu version
            result = self.exec_in_container("lsb_release -d", check=False)
            if result.returncode == 0:
                info["ubuntu_version"] = result.stdout.strip().split(":", 1)[1].strip()
        except ContainerTestError:
            pass

        try:
            # Package version
            result = self.exec_in_container("rxiv --version", check=False)
            if result.returncode == 0:
                info["package_version"] = result.stdout.strip()
        except ContainerTestError:
            pass

        try:
            # Package size
            result = self.exec_in_container("dpkg-query -Wf '${Installed-Size}' rxiv-maker", check=False)
            if result.returncode == 0:
                info["package_size_kb"] = int(result.stdout.strip())
        except (ContainerTestError, ValueError):
            pass

        return info

    def generate_test_report(self, test_results: Dict) -> Path:
        """Generate comprehensive test report."""
        report_data = {
            "test_info": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "ubuntu_version": self.ubuntu_version,
                "container_name": self.container_name,
                "test_id": self.test_id,
            },
            "system_info": self.collect_system_info(),
            "test_results": test_results,
            "environment": {
                "container_engine": self.container_engine,
                "project_root": str(PROJECT_ROOT),
            },
        }

        # Write JSON report
        report_file = self.test_results_dir / f"test-report-{self.ubuntu_version}-{self.test_id}.json"
        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2)

        return report_file


# Pytest fixtures and test classes


@pytest.fixture(scope="session")
def ubuntu_version(request):
    """Get Ubuntu version from command line or use default."""
    return getattr(request.config.option, "ubuntu_version", DEFAULT_UBUNTU_VERSION)


@pytest.fixture(scope="session")
def container_tester(ubuntu_version):
    """Create container tester instance."""
    with AptContainerTester(ubuntu_version=ubuntu_version, cleanup_on_exit=True, verbose=True) as tester:
        yield tester


class TestAptContainerWorkflow:
    """Integration tests for APT container workflow."""

    def test_container_creation(self, container_tester):
        """Test container creation and basic setup."""
        # Create container
        container_tester.create_container()

        # Verify container is running
        result = container_tester.exec_in_container("echo 'Container is running'")
        assert "Container is running" in result.stdout

    def test_container_environment_setup(self, container_tester):
        """Test container environment setup."""
        container_tester.create_container()
        container_tester.setup_container_environment()

        # Verify basic tools are installed
        container_tester.exec_in_container("which curl")
        container_tester.exec_in_container("which gpg")

        # Verify test user exists
        result = container_tester.exec_in_container("id testuser")
        assert "testuser" in result.stdout

    def test_apt_repository_setup(self, container_tester):
        """Test APT repository setup."""
        container_tester.create_container()
        container_tester.setup_container_environment()
        container_tester.add_apt_repository()

        # Verify repository is accessible
        result = container_tester.exec_in_container("apt-cache search rxiv-maker")
        assert "rxiv-maker" in result.stdout

    def test_package_installation(self, container_tester):
        """Test package installation from repository."""
        container_tester.create_container()
        container_tester.setup_container_environment()
        container_tester.add_apt_repository()

        # Install package
        container_tester.install_package()
        assert version  # Should return version string

        # Verify installation
        result = container_tester.exec_in_container("which rxiv")
        assert "/usr/bin/rxiv" in result.stdout or "/usr/local/bin/rxiv" in result.stdout

    def test_basic_functionality(self, container_tester):
        """Test basic functionality after installation."""
        container_tester.create_container()
        container_tester.setup_container_environment()
        container_tester.add_apt_repository()
        container_tester.install_package()

        # Run functionality tests
        results = container_tester.test_basic_functionality()

        # Verify critical functionality
        assert results["version_command"], "Version command should work"
        assert results["help_command"], "Help command should work"
        assert results["user_access"], "Regular user should be able to run rxiv"

    def test_manuscript_operations(self, container_tester):
        """Test manuscript operations."""
        container_tester.create_container()
        container_tester.setup_container_environment()
        container_tester.add_apt_repository()
        container_tester.install_package()

        # Run manuscript tests
        results = container_tester.test_manuscript_operations()

        # Verify manuscript functionality
        assert results["manuscript_init"], "Manuscript initialization should work"
        assert results["manuscript_validation"], "Manuscript validation should work"

    def test_example_manuscript(self, container_tester):
        """Test with example manuscript."""
        container_tester.create_container()
        container_tester.setup_container_environment()
        container_tester.add_apt_repository()
        container_tester.install_package()

        # Run example manuscript tests
        results = container_tester.test_example_manuscript()

        # Verify example manuscript functionality
        assert results["example_copy"], "Example manuscript copy should work"
        assert results["example_validation"], "Example manuscript validation should work"

    def test_security_aspects(self, container_tester):
        """Test security aspects."""
        container_tester.create_container()
        container_tester.setup_container_environment()
        container_tester.add_apt_repository()
        container_tester.install_package()

        # Run security tests
        results = container_tester.test_security_aspects()

        # Verify security aspects
        assert results["gpg_key_verification"], "GPG key verification should work"
        assert results["package_policy"], "Package policy should be accessible"
        assert results["file_permissions"], "No setuid/setgid files should exist"

    @pytest.mark.slow
    def test_comprehensive_workflow(self, container_tester):
        """Test complete workflow from container creation to functionality."""
        # Full workflow test
        container_tester.create_container()
        container_tester.setup_container_environment()
        container_tester.add_apt_repository()
        container_tester.install_package()

        # Collect all test results
        all_results = {}
        all_results["basic_functionality"] = container_tester.test_basic_functionality()
        all_results["manuscript_operations"] = container_tester.test_manuscript_operations()
        all_results["example_manuscript"] = container_tester.test_example_manuscript()
        all_results["security_aspects"] = container_tester.test_security_aspects()

        # Generate report
        report_file = container_tester.generate_test_report(all_results)
        assert report_file.exists(), "Test report should be generated"

        # Verify critical functionality
        assert all_results["basic_functionality"]["version_command"]
        assert all_results["basic_functionality"]["user_access"]
        assert all_results["manuscript_operations"]["manuscript_init"]
        assert all_results["security_aspects"]["file_permissions"]


def pytest_addoption(parser):
    """Add custom pytest command line options."""
    parser.addoption(
        "--ubuntu-version",
        action="store",
        default=DEFAULT_UBUNTU_VERSION,
        help=f"Ubuntu version to test (default: {DEFAULT_UBUNTU_VERSION})",
    )


if __name__ == "__main__":
    # Direct execution support
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Run APT container integration tests")
    parser.add_argument(
        "--ubuntu-version",
        default=DEFAULT_UBUNTU_VERSION,
        choices=SUPPORTED_UBUNTU_VERSIONS,
        help="Ubuntu version to test",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--no-cleanup", action="store_true", help="Don't cleanup containers after tests")

    args = parser.parse_args()

    # Run comprehensive test
    print(f"Running comprehensive APT container test for Ubuntu {args.ubuntu_version}")

    try:
        with AptContainerTester(
            ubuntu_version=args.ubuntu_version, cleanup_on_exit=not args.no_cleanup, verbose=args.verbose
        ) as tester:
            # Run full workflow
            tester.create_container()
            print("✅ Container created")

            tester.setup_container_environment()
            print("✅ Container environment setup")

            tester.add_apt_repository()
            print("✅ APT repository added")

            version = tester.install_package()
            print(f"✅ Package installed: {version}")

            # Run all tests
            basic_results = tester.test_basic_functionality()
            manuscript_results = tester.test_manuscript_operations()
            example_results = tester.test_example_manuscript()
            security_results = tester.test_security_aspects()

            # Collect results
            all_results = {
                "basic_functionality": basic_results,
                "manuscript_operations": manuscript_results,
                "example_manuscript": example_results,
                "security_aspects": security_results,
            }

            # Generate report
            report_file = tester.generate_test_report(all_results)
            print(f"✅ Test report generated: {report_file}")

            # Check for failures
            failed_tests = []
            for category, tests in all_results.items():
                for test, result in tests.items():
                    if not result:
                        failed_tests.append(f"{category}.{test}")

            if failed_tests:
                print(f"❌ Failed tests: {', '.join(failed_tests)}")
                sys.exit(1)
            else:
                print("✅ All tests passed!")

    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(130)
    except ContainerTestError as e:
        print(f"❌ Container test error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
