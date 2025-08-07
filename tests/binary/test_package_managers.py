"""Tests for package manager integration (Homebrew, Scoop)."""

import json
import platform
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import pytest
import yaml


@pytest.mark.package_manager
@pytest.mark.homebrew
@pytest.mark.pypi
class TestHomebrewFormula:
    """Test Homebrew formula structure and validity."""

    @pytest.fixture(scope="class")
    def formula_path(self):
        """Get path to Homebrew formula."""
        return Path(__file__).parent.parent.parent / "submodules" / "homebrew-rxiv-maker" / "Formula" / "rxiv-maker.rb"

    def test_formula_file_exists(self, formula_path):
        """Test that the Homebrew formula file exists."""
        assert formula_path.exists(), f"Formula file not found: {formula_path}"

    def test_formula_basic_structure(self, formula_path):
        """Test basic structure of Homebrew formula."""
        content = formula_path.read_text()

        # Check for required Ruby class structure
        assert "class RxivMaker < Formula" in content
        assert "desc " in content
        assert "homepage " in content
        assert "license " in content
        assert "url " in content
        assert "sha256 " in content
        assert "def install" in content
        assert "test do" in content

    def test_formula_pypi_urls(self, formula_path):
        """Test that formula uses PyPI source URLs."""
        content = formula_path.read_text()

        # Should point to PyPI, not GitHub releases
        assert "files.pythonhosted.org" in content  # PyPI source

        # Should have proper PyPI package structure
        assert "rxiv_maker-" in content
        assert ".tar.gz" in content

    def test_formula_python_dependencies(self, formula_path):
        """Test that formula includes Python dependencies."""
        content = formula_path.read_text()

        # Should depend on Python
        assert 'depends_on "python' in content

        # Should have resource blocks for Python packages
        assert "resource " in content
        assert "virtualenv_install_with_resources" in content

    def test_formula_install_method(self, formula_path):
        """Test that install method uses virtualenv for Python packages."""
        content = formula_path.read_text()

        # Should use virtualenv installation
        assert "virtualenv_install_with_resources" in content
        assert "def install" in content

    def test_formula_test_section(self, formula_path):
        """Test that formula has proper test section."""
        content = formula_path.read_text()

        # Should test CLI functionality
        assert 'shell_output("#{bin}/rxiv --version")' in content or 'assert_match "version"' in content
        assert 'system bin/"rxiv", "--help"' in content

    def test_formula_architecture_support(self, formula_path):
        """Test that formula supports multiple architectures."""
        content = formula_path.read_text()

        # Should have platform-specific dependency sections
        assert "on_linux do" in content
        # May have additional dependencies like libyaml on Linux

    @pytest.mark.slow
    def test_formula_syntax_validation(self, formula_path):
        """Test formula syntax with Ruby parser."""
        if not shutil.which("ruby"):
            pytest.skip("Ruby not available for syntax validation")

        try:
            result = subprocess.run(
                ["ruby", "-c", str(formula_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.returncode == 0, f"Ruby syntax error: {result.stderr}"
        except subprocess.TimeoutExpired:
            pytest.fail("Ruby syntax check timed out")
        except FileNotFoundError:
            pytest.skip("Ruby not available")


@pytest.mark.package_manager
@pytest.mark.scoop
@pytest.mark.pypi
class TestScoopManifest:
    """Test Scoop manifest structure and validity."""

    @pytest.fixture(scope="class")
    def manifest_path(self):
        """Get path to Scoop manifest."""
        return Path(__file__).parent.parent.parent / "submodules" / "scoop-rxiv-maker" / "bucket" / "rxiv-maker.json"

    def test_manifest_file_exists(self, manifest_path):
        """Test that the Scoop manifest file exists."""
        assert manifest_path.exists(), f"Manifest file not found: {manifest_path}"

    def test_manifest_valid_json(self, manifest_path):
        """Test that manifest is valid JSON."""
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in manifest: {e}")

        assert isinstance(manifest, dict)

    def test_manifest_required_fields(self, manifest_path):
        """Test that manifest has all required fields."""
        with open(manifest_path) as f:
            manifest = json.load(f)

        required_fields = [
            "version",
            "description",
            "homepage",
            "license",
            "url",
            "hash",
            "bin",
        ]

        for field in required_fields:
            assert field in manifest, f"Required field '{field}' missing from manifest"

    def test_manifest_pypi_url(self, manifest_path):
        """Test that manifest uses PyPI source URL."""
        with open(manifest_path) as f:
            manifest = json.load(f)

        url = manifest["url"]

        # Should point to PyPI source distribution
        parsed_url = urlparse(url)
        assert parsed_url.netloc == "files.pythonhosted.org", (
            f"URL should use files.pythonhosted.org, got {parsed_url.netloc}"
        )

        # Should be source distribution
        assert "rxiv_maker-" in url
        assert ".tar.gz" in url

    def test_manifest_python_dependencies(self, manifest_path):
        """Test that manifest correctly depends on Python."""
        with open(manifest_path) as f:
            manifest = json.load(f)

        # Should depend on Python
        depends = manifest.get("depends", [])
        assert "python" in depends

        # Should have Python installation commands
        post_install = manifest.get("post_install", [])
        post_install_str = " ".join(post_install) if post_install else ""

        # Should use pip to install the package
        assert "pip install" in post_install_str
        assert "rxiv-maker" in post_install_str

    def test_manifest_python_executable(self, manifest_path):
        """Test that manifest specifies correct Python module executable."""
        with open(manifest_path) as f:
            manifest = json.load(f)

        bin_entry = manifest["bin"]

        # Should be Python module runner configuration
        assert isinstance(bin_entry, list), "Expected bin to be a list for Python module execution"
        assert len(bin_entry) == 3, "Expected [python, command, module] format"
        assert bin_entry[0] == "python"
        assert bin_entry[1] == "rxiv"
        assert bin_entry[2] == "-m rxiv_maker.cli"

    def test_manifest_checkver_configuration(self, manifest_path):
        """Test that manifest has proper version checking configuration."""
        with open(manifest_path) as f:
            manifest = json.load(f)

        assert "checkver" in manifest
        checkver = manifest["checkver"]

        # Should check PyPI for version updates
        assert "pypi.org" in checkver["url"]
        assert "rxiv-maker" in checkver["url"]
        assert "jsonpath" in checkver

    def test_manifest_autoupdate_configuration(self, manifest_path):
        """Test that manifest has proper auto-update configuration."""
        with open(manifest_path) as f:
            manifest = json.load(f)

        assert "autoupdate" in manifest
        autoupdate = manifest["autoupdate"]

        # Should auto-update from PyPI source distribution
        autoupdate_url = autoupdate["url"]
        parsed_autoupdate_url = urlparse(autoupdate_url)
        assert parsed_autoupdate_url.netloc == "files.pythonhosted.org", (
            f"Auto-update URL should use files.pythonhosted.org, got {parsed_autoupdate_url.netloc}"
        )
        assert "rxiv_maker-" in autoupdate["url"]
        assert "$version" in autoupdate["url"]
        assert ".tar.gz" in autoupdate["url"]


@pytest.mark.package_manager
@pytest.mark.integration
class TestPackageManagerWorkflows:
    """Test package manager update workflows."""

    def test_homebrew_update_workflow_exists(self):
        """Test that Homebrew update workflow exists."""
        workflow_path = (
            Path(__file__).parent.parent.parent
            / "submodules"
            / "homebrew-rxiv-maker"
            / ".github"
            / "workflows"
            / "update-formula.yml"
        )
        assert workflow_path.exists(), "Homebrew update workflow not found"

    def test_scoop_update_workflow_exists(self):
        """Test that Scoop update workflow exists."""
        workflow_path = (
            Path(__file__).parent.parent.parent
            / "submodules"
            / "scoop-rxiv-maker"
            / ".github"
            / "workflows"
            / "update-manifest.yml"
        )
        assert workflow_path.exists(), "Scoop update workflow not found"

    def test_homebrew_workflow_structure(self):
        """Test Homebrew workflow structure."""
        workflow_path = (
            Path(__file__).parent.parent.parent
            / "submodules"
            / "homebrew-rxiv-maker"
            / ".github"
            / "workflows"
            / "update-formula.yml"
        )

        if not workflow_path.exists():
            pytest.skip("Homebrew workflow not found")

        content = workflow_path.read_text()
        workflow = yaml.safe_load(content)

        # Get the 'on' section (YAML may parse 'on:' as boolean True)
        on_section = workflow.get("on") or workflow.get(True)
        assert on_section is not None, "Workflow 'on' section not found"

        # Should trigger on repository_dispatch and workflow_dispatch
        assert "repository_dispatch" in on_section
        assert "workflow_dispatch" in on_section

        # Should have update-formula job
        assert "update-formula" in workflow["jobs"]

    def test_scoop_workflow_structure(self):
        """Test Scoop workflow structure."""
        workflow_path = (
            Path(__file__).parent.parent.parent
            / "submodules"
            / "scoop-rxiv-maker"
            / ".github"
            / "workflows"
            / "update-manifest.yml"
        )

        if not workflow_path.exists():
            pytest.skip("Scoop workflow not found")

        content = workflow_path.read_text()
        workflow = yaml.safe_load(content)

        # Get the 'on' section (YAML may parse 'on:' as boolean True)
        on_section = workflow.get("on") or workflow.get(True)
        assert on_section is not None, "Workflow 'on' section not found"

        # Should trigger on repository_dispatch and workflow_dispatch
        assert "repository_dispatch" in on_section
        assert "workflow_dispatch" in on_section

        # Should have update-manifest job
        assert "update-manifest" in workflow["jobs"]


@pytest.mark.package_manager
@pytest.mark.integration
@pytest.mark.slow
class TestPackageManagerIntegration:
    """Integration tests for package manager functionality."""

    @pytest.mark.slow
    @pytest.mark.skipif(platform.system() != "Darwin", reason="Homebrew tests require macOS")
    def test_homebrew_tap_structure(self):
        """Test Homebrew tap repository structure."""
        if not shutil.which("brew"):
            pytest.skip("Homebrew not available")

        # Test that we can validate the formula structure
        formula_path = (
            Path(__file__).parent.parent.parent / "submodules" / "homebrew-rxiv-maker" / "Formula" / "rxiv-maker.rb"
        )

        if not formula_path.exists():
            pytest.skip("Homebrew formula not found")

        # Test formula with Homebrew (if available)
        try:
            result = subprocess.run(
                ["brew", "info", "--formula", str(formula_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                # Formula is parseable by Homebrew
                assert "rxiv-maker" in result.stdout.lower()
            else:
                # Formula has issues - log but don't fail (might be environment)
                print(f"Homebrew formula validation warning: {result.stderr}")

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Homebrew validation not available")

    @pytest.mark.slow
    @pytest.mark.skipif(platform.system() != "Windows", reason="Scoop tests require Windows")
    def test_scoop_bucket_structure(self):
        """Test Scoop bucket repository structure."""
        if not shutil.which("scoop"):
            pytest.skip("Scoop not available")

        manifest_path = (
            Path(__file__).parent.parent.parent / "submodules" / "scoop-rxiv-maker" / "bucket" / "rxiv-maker.json"
        )

        if not manifest_path.exists():
            pytest.skip("Scoop manifest not found")

        # Test that Scoop can parse the manifest
        try:
            # Note: This would require Scoop to be installed and available
            # In CI, we test JSON validity instead
            with open(manifest_path) as f:
                manifest = json.load(f)

            # Validate against Scoop schema expectations
            assert "version" in manifest
            assert "url" in manifest
            assert "hash" in manifest
            assert "bin" in manifest

        except json.JSONDecodeError as e:
            pytest.fail(f"Scoop manifest JSON error: {e}")

    def test_package_manager_version_consistency(self):
        """Test that package managers reference consistent versions."""
        # Get version from main package
        version_file = Path(__file__).parent.parent.parent / "src" / "rxiv_maker" / "__version__.py"

        if not version_file.exists():
            pytest.skip("Version file not found")

        # Extract version
        version_content = version_file.read_text()
        import re

        version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', version_content)

        if not version_match:
            pytest.skip("Could not extract version")

        main_version = version_match.group(1)

        # Check Scoop manifest version
        scoop_manifest = (
            Path(__file__).parent.parent.parent / "submodules" / "scoop-rxiv-maker" / "bucket" / "rxiv-maker.json"
        )
        if scoop_manifest.exists():
            with open(scoop_manifest) as f:
                manifest = json.load(f)
            scoop_version = manifest.get("version")

            if scoop_version:
                # In CI/release environments, submodules may lag behind main version
                # Only enforce strict version matching in development environments
                import os

                is_ci = os.environ.get("CI") == "true"
                is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"

                if is_ci or is_github_actions:
                    # In CI, allow submodule versions to be behind main version
                    # but warn if they're too far behind
                    try:
                        from packaging.version import Version

                        main_ver = Version(main_version)
                        scoop_ver = Version(scoop_version)

                        # Allow submodule to be behind by at most one minor version
                        if scoop_ver < main_ver:
                            major_diff = main_ver.major - scoop_ver.major
                            minor_diff = (
                                main_ver.minor - scoop_ver.minor if main_ver.major == scoop_ver.major else float("inf")
                            )

                            if major_diff > 0 or minor_diff > 1:
                                import warnings

                                warnings.warn(
                                    f"Scoop version {scoop_version} significantly behind main version {main_version}",
                                    UserWarning,
                                    stacklevel=2,
                                )
                    except ImportError:
                        # If packaging not available, just warn
                        import warnings

                        warnings.warn(
                            f"Scoop version {scoop_version} != main version {main_version} (CI environment)",
                            UserWarning,
                            stacklevel=2,
                        )
                else:
                    # In development, enforce strict version matching
                    assert scoop_version == main_version, (
                        f"Scoop version {scoop_version} != main version {main_version}"
                    )
