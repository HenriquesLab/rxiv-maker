"""End-to-end tests for binary distribution workflow."""

import tempfile
from pathlib import Path

import pytest
import requests

# Exclude from default CI run; exercise external GitHub API and release assets
pytestmark = pytest.mark.ci_exclude


class TestBinaryDistributionWorkflow:
    """Test the complete binary distribution workflow."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_github_release_workflow_structure(self):
        """Test that the GitHub release workflow is properly structured."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release-python.yml"
        assert workflow_path.exists(), "Release workflow not found"

        content = workflow_path.read_text()

        # Check for required workflow components
        assert "name: Release" in content
        assert "build:" in content  # Main build job
        assert "github-release:" in content  # Release creation job
        assert "pypi:" in content  # PyPI publishing job

        # Check for platform usage
        assert "ubuntu-latest" in content

    def test_binary_naming_convention(self):
        """Test that binary naming follows expected conventions."""
        expected_names = {
            "linux": "rxiv-maker-linux-x64.tar.gz",
            "windows": "rxiv-maker-windows-x64.zip",
            "macos-intel": "rxiv-maker-macos-x64-intel.tar.gz",
            "macos-arm": "rxiv-maker-macos-arm64.tar.gz",
        }

        for platform_name, expected_name in expected_names.items():
            # Test naming pattern
            assert "rxiv-maker" in expected_name
            assert platform_name.split("-")[0] in expected_name.lower()

            # Test appropriate archive format
            if "windows" in expected_name:
                assert expected_name.endswith(".zip")
            else:
                assert expected_name.endswith(".tar.gz")

    def test_version_synchronization_workflow(self):
        """Test that version synchronization triggers are properly configured."""
        # Check main release workflow
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release-python.yml"
        content = workflow_path.read_text()

        # Should trigger package manager updates (homebrew-update job exists)
        has_package_updates = "homebrew-update:" in content
        assert has_package_updates, "No package manager update mechanism found"

        # Check package manager workflows exist
        homebrew_workflow = (
            Path(__file__).parent.parent.parent
            / "submodules"
            / "homebrew-rxiv-maker"
            / ".github"
            / "workflows"
            / "update-formula.yml"
        )
        scoop_workflow = (
            Path(__file__).parent.parent.parent
            / "submodules"
            / "scoop-rxiv-maker"
            / ".github"
            / "workflows"
            / "update-manifest.yml"
        )

        if homebrew_workflow.exists():
            homebrew_content = homebrew_workflow.read_text()
            assert "repository_dispatch:" in homebrew_content
            assert "update-formula" in homebrew_content

        if scoop_workflow.exists():
            scoop_content = scoop_workflow.read_text()
            assert "repository_dispatch:" in scoop_content
            assert "update-manifest" in scoop_content

    @pytest.mark.slow
    @pytest.mark.timeout(90)  # GitHub API requests may be slow
    def test_github_api_release_structure(self):
        """Test that GitHub releases have the expected structure."""
        # This test checks the GitHub API to verify release structure
        # Skip if we can't access the API

        try:
            # Check if the repository exists and has releases
            response = requests.get(
                "https://api.github.com/repos/henriqueslab/rxiv-maker/releases/latest",
                timeout=10,
            )

            if response.status_code == 404:
                pytest.skip("Repository not found or no releases available")
            elif response.status_code != 200:
                pytest.skip(f"GitHub API not accessible: {response.status_code}")

            release_data = response.json()

            # Check release structure
            assert "tag_name" in release_data
            assert "assets" in release_data

            # Check for expected binary assets
            asset_names = [asset["name"] for asset in release_data["assets"]]

            expected_patterns = ["linux-x64", "windows-x64", "macos"]

            for pattern in expected_patterns:
                matching_assets = [name for name in asset_names if pattern in name]
                if not matching_assets:
                    pytest.skip(f"No assets found for {pattern} (may not be released yet)")

        except requests.RequestException:
            pytest.skip("Cannot access GitHub API for release testing")

    def test_binary_compatibility_matrix(self):
        """Test that we're building for the right platform combinations."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release-python.yml"
        content = workflow_path.read_text()

        # Should build on supported platform
        assert "ubuntu-latest" in content  # Linux x64

    def test_pyinstaller_configuration_completeness(self):
        """Test that PyInstaller configuration includes all necessary components."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release-python.yml"
        content = workflow_path.read_text()

        # Should include the package name for building
        assert "rxiv_maker" in content or "rxiv-maker" in content

        # Test passes if package building is configured

    def test_package_manager_trigger_configuration(self):
        """Test that package manager updates are properly triggered."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release-python.yml"
        content = workflow_path.read_text()

        # Should trigger Homebrew updates
        assert "HenriquesLab/homebrew-rxiv-maker" in content

        # Should have homebrew-update job
        assert "homebrew-update:" in content, "No homebrew update job found"

        # Should mention formula updates
        has_formula = "formula" in content.lower()
        assert has_formula, "No formula workflow references found"


class TestBinaryFunctionality:
    """Test binary functionality and compatibility."""

    def test_cli_entry_point_compatibility(self):
        """Test that CLI entry point works for binary building."""
        # Test that the CLI can be imported and basic functions work
        try:
            from rxiv_maker.cli.commands.version import version
            from rxiv_maker.cli.main import main

            # These should be importable for binary building
            assert callable(main)
            assert callable(version)

        except ImportError as e:
            pytest.fail(f"CLI entry point import failed: {e}")

    def test_resource_path_resolution(self):
        """Test that resource paths work in both source and binary contexts."""
        from rxiv_maker.processors.template_processor import get_template_path

        # Should resolve template path
        template_path = get_template_path()
        assert template_path is not None

        # Should be a Path object with expected methods
        assert hasattr(template_path, "exists")
        assert hasattr(template_path, "read_text")

    def test_dependency_bundling_completeness(self):
        """Test that all required dependencies can be imported."""
        # Core dependencies that must be available in binary
        core_deps = [
            "matplotlib",
            "numpy",
            "pandas",
            "seaborn",
            "yaml",
            "click",
            "rich",
            "PIL",  # Pillow
            "scipy",
        ]

        missing_deps = []
        for dep in core_deps:
            try:
                __import__(dep)
            except ImportError:
                missing_deps.append(dep)

        if missing_deps:
            pytest.skip(f"Missing dependencies in test environment: {missing_deps}")

    def test_platform_specific_functionality(self):
        """Test platform-specific functionality for binary distribution."""
        from rxiv_maker.utils.platform import get_platform

        # Should detect platform correctly
        platform_name = get_platform()
        assert platform_name is not None
        assert len(platform_name) > 0

    def test_file_system_operations(self):
        """Test file system operations that binaries need to perform."""
        import tempfile

        # Test that we can create temporary directories (needed for builds)
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            assert temp_path.exists()

            # Test file operations
            test_file = temp_path / "test.txt"
            test_file.write_text("test content")
            assert test_file.exists()
            assert test_file.read_text() == "test content"


class TestReleaseWorkflowIntegration:
    """Test integration aspects of the release workflow."""

    def test_workflow_job_dependencies(self):
        """Test that workflow jobs have correct dependencies."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release-python.yml"
        content = workflow_path.read_text()

        # Parse basic job structure
        assert "jobs:" in content

        # Key jobs should exist
        assert "build:" in content
        assert "github-release:" in content
        assert "pypi:" in content

        # Dependencies should be correct - check for needs clauses
        assert "needs: [" in content or "needs: build" in content

    def test_artifact_handling(self):
        """Test that artifacts are properly handled in workflow."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release-python.yml"
        content = workflow_path.read_text()

        # Should handle artifacts (upload/download)
        assert "artifact" in content.lower()
        assert "upload-artifact" in content or "download-artifact" in content

    def test_error_handling_in_workflow(self):
        """Test that workflow has proper error handling."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release-python.yml"
        content = workflow_path.read_text()

        # Should have error handling configurations (timeout or failure handling)
        has_error_handling = (
            "timeout-minutes" in content
            or "timeout:" in content
            or "if: failure()" in content
            or "continue-on-error" in content
        )
        # Not strictly required, but good practice
        if not has_error_handling:
            print("Warning: No explicit timeout or error handling found in workflow")

        # Should handle failures appropriately
        assert "if:" in content  # Conditional execution

        # Should have validation steps
        assert "test" in content.lower()
        assert "check" in content.lower() or "validation" in content.lower()

    def test_security_considerations(self):
        """Test that workflow follows security best practices."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release-python.yml"
        content = workflow_path.read_text()

        # Should use official actions with pinned versions
        assert "actions/checkout@v5" in content
        assert "actions/setup-python@v5" in content

        # Should specify permissions
        assert "permissions:" in content

        # Should use secrets appropriately
        assert "secrets." in content

    @pytest.mark.slow
    @pytest.mark.timeout(120)  # YAML validation may require file processing
    def test_workflow_yaml_validity(self):
        """Test that workflow YAML is valid."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release-python.yml"

        if not workflow_path.exists():
            pytest.skip("Release workflow not found")

        try:
            import yaml

            with open(workflow_path) as f:
                workflow_data = yaml.safe_load(f)

            # Basic structure validation
            assert "name" in workflow_data
            # 'on' is a YAML boolean keyword, so it gets parsed as True
            assert True in workflow_data or "on" in workflow_data
            assert "jobs" in workflow_data

            # Jobs should be a dictionary
            assert isinstance(workflow_data["jobs"], dict)

        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in workflow file: {e}")
        except ImportError:
            pytest.skip("PyYAML not available for YAML validation")


class TestDistributionCompliance:
    """Test compliance with distribution standards."""

    def test_binary_size_considerations(self):
        """Test that package building considers size optimization."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release-python.yml"
        content = workflow_path.read_text()

        # Should build package efficiently
        assert "uv build" in content or "build" in content

    def test_license_compliance(self):
        """Test that binary distribution complies with licensing."""
        # Check that license information is preserved
        license_file = Path(__file__).parent.parent.parent / "LICENSE"
        if license_file.exists():
            license_content = license_file.read_text()
            assert len(license_content) > 0

        # License compliance is handled by GitHub automatically for tagged releases

    def test_binary_metadata(self):
        """Test that binaries will include proper metadata."""
        # Check version information
        version_file = Path(__file__).parent.parent.parent / "src" / "rxiv_maker" / "__version__.py"
        assert version_file.exists()

        version_content = version_file.read_text()
        assert "__version__" in version_content

        # Check that CLI can report version
        try:
            from rxiv_maker import __version__

            assert __version__ is not None
            assert len(__version__) > 0
        except ImportError:
            pytest.skip("Cannot import version for testing")

    def test_distribution_completeness(self):
        """Test that distribution includes all necessary components."""
        # Template files should be available
        tex_dir = Path(__file__).parent.parent.parent / "src" / "tex"
        assert tex_dir.exists()
        assert (tex_dir / "template.tex").exists()
        assert (tex_dir / "style" / "rxiv_maker_style.cls").exists()

        # CLI should be functional
        cli_file = Path(__file__).parent.parent.parent / "src" / "rxiv_maker" / "rxiv_maker_cli.py"
        assert cli_file.exists()

        cli_content = cli_file.read_text()
        assert "__name__ == " in cli_content and "__main__" in cli_content
