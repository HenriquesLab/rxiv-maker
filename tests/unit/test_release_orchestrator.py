"""Tests for the release orchestrator."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Add the GitHub scripts path to sys.path
github_scripts_path = Path(__file__).parent.parent.parent / ".github" / "scripts" / "release"
sys.path.insert(0, str(github_scripts_path.parent / "common"))
sys.path.insert(0, str(github_scripts_path))

from orchestrator import ReleaseOrchestrator  # noqa: E402


class TestReleaseOrchestratorChangelogValidation:
    """Test the _validate_changelog method of ReleaseOrchestrator."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock environment variables and dependencies
        self.mock_env = {
            "GITHUB_REPOSITORY": "test/repo",
            "GITHUB_TOKEN": "fake_token",
        }

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("builtins.open", new_callable=mock_open, read_data="## [v1.2.3] - 2025-10-29\n### Added\n- New feature\n")
    @patch("pathlib.Path.exists")
    def test_validate_changelog_with_v_prefix_success(
        self, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test successful CHANGELOG validation with 'v' prefix."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3"
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should not raise exception
        orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("builtins.open", new_callable=mock_open, read_data="## [1.2.3] - 2025-10-29\n### Added\n- New feature\n")
    @patch("pathlib.Path.exists")
    def test_validate_changelog_without_v_prefix_success(
        self, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test successful CHANGELOG validation without 'v' prefix."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3"  # Version includes 'v' but CHANGELOG doesn't
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should not raise exception
        orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("pathlib.Path.exists")
    def test_validate_changelog_file_not_found(self, mock_exists, mock_config_loader, mock_github_token, mock_version):
        """Test CHANGELOG validation when file doesn't exist."""
        # Setup
        mock_exists.return_value = False
        mock_version.return_value = "v1.2.3"
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should raise ValueError
        with pytest.raises(ValueError, match="CHANGELOG.md not found in repository root"):
            orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("builtins.open", new_callable=mock_open, read_data="## [v1.0.0] - 2025-01-01\n### Added\n- Old feature\n")
    @patch("pathlib.Path.exists")
    def test_validate_changelog_version_not_found(
        self, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test CHANGELOG validation when version entry is missing."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3"  # Different version than in CHANGELOG
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should raise ValueError with helpful message
        with pytest.raises(ValueError) as exc_info:
            orchestrator._validate_changelog()

        assert "No CHANGELOG entry found for version v1.2.3" in str(exc_info.value)
        assert "Please add a CHANGELOG entry before creating a release" in str(exc_info.value)

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_validate_changelog_encoding_error(
        self, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test CHANGELOG validation handles encoding errors gracefully."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3"
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")

        # Mock file read to raise UnicodeDecodeError
        mock_file.return_value.__enter__.return_value.read.side_effect = UnicodeDecodeError(
            "utf-8", b"", 0, 1, "invalid start byte"
        )

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should raise ValueError with meaningful error message
        with pytest.raises(ValueError, match="Failed to read CHANGELOG.md: encoding error"):
            orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="## [v1.2.3]\n### Fixed\n- Bug fix\n## [v1.2.2]\n### Added\n- Feature\n",
    )
    @patch("pathlib.Path.exists")
    def test_validate_changelog_multiple_versions_present(
        self, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test CHANGELOG validation with multiple version entries."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3"
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should succeed when target version is present
        orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="## [v1.2.3-beta.1] - 2025-10-29\n### Added\n- Beta feature\n",
    )
    @patch("pathlib.Path.exists")
    def test_validate_changelog_prerelease_version(
        self, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test CHANGELOG validation with prerelease version."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3-beta.1"
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should succeed with prerelease version
        orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("builtins.open", new_callable=mock_open, read_data="## [  v1.2.3  ] - 2025-10-29\n### Added\n- Feature\n")
    @patch("pathlib.Path.exists")
    def test_validate_changelog_with_whitespace(
        self, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test CHANGELOG validation doesn't handle extra whitespace (should fail)."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3"
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should fail because whitespace is not stripped
        with pytest.raises(ValueError, match="No CHANGELOG entry found"):
            orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("builtins.open", new_callable=mock_open, read_data="")
    @patch("pathlib.Path.exists")
    def test_validate_changelog_empty_file(
        self, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test CHANGELOG validation with empty file."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3"
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should fail with empty CHANGELOG
        with pytest.raises(ValueError, match="No CHANGELOG entry found"):
            orchestrator._validate_changelog()
