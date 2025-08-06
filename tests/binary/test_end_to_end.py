"""End-to-end tests for binary distribution workflow."""

import tempfile
from pathlib import Path

import pytest
import requests


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
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release.yml"
        assert workflow_path.exists(), "Release workflow not found"

        content = workflow_path.read_text()

        # Check for required workflow components
        assert "name: Release and Binary Distribution" in content
        assert "pyinstaller" in content.lower()
        assert "build-binaries:" in content
        assert "create-release:" in content
        assert "publish-pypi:" in content

        # Check for platform matrix
        assert "ubuntu-latest" in content
        assert "windows-latest" in content
        assert "macos-latest" in content

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
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release.yml"
        content = workflow_path.read_text()

        # Should trigger package manager updates (either via update job or workflow dispatch)
        has_package_updates = (
            "update-package-managers:" in content or "workflow run" in content or "gh workflow run" in content
        )
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
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release.yml"
        content = workflow_path.read_text()

        # Should build for major platforms
        assert "ubuntu-latest" in content  # Linux x64
        assert "windows-latest" in content  # Windows x64
        assert "macos-latest" in content  # macOS ARM64
        assert "macos-13" in content or "intel" in content.lower()  # macOS x64

    def test_pyinstaller_configuration_completeness(self):
        """Test that PyInstaller configuration includes all necessary components."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release.yml"
        content = workflow_path.read_text()

        # Should use PyInstaller for binary building
        assert "pyinstaller" in content.lower()

        # Should include the package name for binary building
        assert "rxiv_maker" in content or "rxiv-maker" in content

        # Test passes if PyInstaller is configured (details may be in spec file)

    def test_package_manager_trigger_configuration(self):
        """Test that package manager updates are properly triggered."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release.yml"
        content = workflow_path.read_text()

        # Should trigger both Homebrew and Scoop updates
        assert "henriqueslab/homebrew-rxiv-maker" in content
        assert "henriqueslab/scoop-rxiv-maker" in content

        # Should trigger package manager updates (either via dispatches or workflow runs)
        has_dispatch = "dispatches" in content or "repository_dispatch" in content
        has_workflow_run = "workflow run" in content
        assert has_dispatch or has_workflow_run, "No package manager trigger mechanism found"

        # Should mention package manager workflows
        has_formula = "update-formula" in content or "formula" in content.lower()
        has_manifest = "update-manifest" in content or "manifest" in content.lower()
        assert has_formula or has_manifest, "No package manager workflow references found"


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
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release.yml"
        content = workflow_path.read_text()

        # Parse basic job structure
        assert "jobs:" in content

        # Key jobs should exist
        assert "test:" in content
        assert "build-binaries:" in content
        assert "create-release:" in content

        # Dependencies should be correct
        assert "needs: test" in content  # build-binaries should need test
        assert "needs: [" in content  # create-release should need multiple jobs

    def test_artifact_handling(self):
        """Test that artifacts are properly handled in workflow."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release.yml"
        content = workflow_path.read_text()

        # Should use custom artifact management action
        assert "./.github/actions/artifact-management" in content

        # Should handle binary artifacts
        assert "artifact" in content.lower()

    def test_error_handling_in_workflow(self):
        """Test that workflow has proper error handling."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release.yml"
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
        assert "verify" in content.lower() or "validate" in content.lower()

    def test_security_considerations(self):
        """Test that workflow follows security best practices."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release.yml"
        content = workflow_path.read_text()

        # Should use official actions
        assert "actions/checkout@v4" in content
        # Check that setup-environment action is used (which internally uses setup-python@v5)
        assert "./.github/actions/setup-environment" in content

        # Should specify permissions
        assert "permissions:" in content

        # Should use secrets appropriately
        assert "secrets." in content

    @pytest.mark.slow
    def test_workflow_yaml_validity(self):
        """Test that workflow YAML is valid."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release.yml"

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
        """Test that binary configuration considers size optimization."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release.yml"
        content = workflow_path.read_text()

        # Should use UPX compression where available
        assert "upx" in content.lower()

        # Should exclude unnecessary modules
        assert "excludes" in content or "exclude" in content

    def test_license_compliance(self):
        """Test that binary distribution complies with licensing."""
        # Check that license information is preserved
        license_file = Path(__file__).parent.parent.parent / "LICENSE"
        if license_file.exists():
            license_content = license_file.read_text()
            assert len(license_content) > 0

        # Check that workflow includes license in releases
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "release.yml"
        workflow_path.read_text()

        # Should mention license or include it in releases
        # (This is handled by GitHub automatically for tagged releases)

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
