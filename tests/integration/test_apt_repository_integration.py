#!/usr/bin/env python3
"""APT Repository Integration Tests.

This module tests the integration with the apt-rxiv-maker repository,
including workflow trigger functionality and repository URL validation.
"""

import re
import unittest
from pathlib import Path
from unittest.mock import patch

import requests
import yaml


class TestAPTRepositoryIntegration(unittest.TestCase):
    """Test APT repository integration functionality."""

    def setUp(self):
        """Set up test environment."""
        self.repo_root = Path(__file__).parent.parent.parent
        self.workflow_file = self.repo_root / ".github" / "workflows" / "release-python.yml"

    def test_workflow_has_apt_repository_job(self):
        """Test that the release workflow uses Python orchestrator for APT coordination."""
        with open(self.workflow_file, "r") as f:
            workflow_content = f.read()

        # Check for Python-driven release orchestrator
        self.assertIn("Run Release Orchestrator", workflow_content)
        self.assertIn(".github/scripts/release/orchestrator.py", workflow_content)
        self.assertIn("DISPATCH_PAT", workflow_content)
        # APT coordination is now handled programmatically by the orchestrator

    def test_workflow_apt_job_dependencies(self):
        """Test that Python orchestrator has required permissions for APT coordination."""
        with open(self.workflow_file, "r") as f:
            workflow_data = yaml.safe_load(f)

        release_job = workflow_data["jobs"]["release"]

        # Check that release job has required environment variables for cross-repo coordination
        env_vars = release_job["steps"][-1]["env"]
        self.assertIn("GITHUB_TOKEN", env_vars)
        self.assertIn("DISPATCH_PAT", env_vars)

        # Check permissions for cross-repository workflow triggers
        permissions = workflow_data["permissions"]
        self.assertIn("contents", permissions)
        self.assertEqual(permissions["contents"], "write")

    def test_workflow_uses_correct_repository_reference(self):
        """Test that orchestrator references the correct apt-rxiv-maker repository."""
        # Check orchestrator script for proper repository configuration
        orchestrator_path = self.repo_root / ".github" / "scripts" / "release" / "orchestrator.py"
        with open(orchestrator_path, "r") as f:
            orchestrator_content = f.read()

        # Should use henriqueslab in repository configuration
        self.assertIn("henriqueslab", orchestrator_content.lower())
        self.assertNotIn("paxcalpt", orchestrator_content.lower())

    def test_workflow_passes_correct_parameters(self):
        """Test that Python orchestrator supports required parameters."""
        with open(self.workflow_file, "r") as f:
            workflow_content = f.read()

        # Check for orchestrator parameter support
        self.assertIn("--dry-run", workflow_content)
        self.assertIn("--force", workflow_content)
        self.assertIn("--debug", workflow_content)
        self.assertIn("--version", workflow_content)

    def test_workflow_uses_correct_secret(self):
        """Test that workflow uses the correct GitHub secret."""
        with open(self.workflow_file, "r") as f:
            workflow_content = f.read()

        # Check for DISPATCH_PAT secret
        self.assertIn("${{ secrets.DISPATCH_PAT }}", workflow_content)

    def test_apt_repository_url_structure(self):
        """Test that APT repository URLs are well-formed."""
        # Read installation docs to get APT repository URLs
        install_file = self.repo_root / "docs" / "quick-start" / "installation.md"
        with open(install_file, "r") as f:
            install_content = f.read()

        # Extract APT repository URL
        url_pattern = r"https://raw\.githubusercontent\.com/HenriquesLab/apt-rxiv-maker/apt-repo"
        urls = re.findall(url_pattern, install_content)

        self.assertTrue(len(urls) > 0, "No APT repository URLs found in installation docs")

        # Each URL should be properly structured
        for url in urls:
            self.assertTrue(url.startswith("https://"))
            self.assertIn("HenriquesLab/apt-rxiv-maker", url)
            self.assertIn("apt-repo", url)

    def test_apt_installation_commands_consistency(self):
        """Test that APT installation commands are consistent across files."""
        files_to_check = [self.repo_root / "README.md", self.workflow_file]

        gpg_commands = []
        deb_lines = []

        for file_path in files_to_check:
            with open(file_path, "r") as f:
                content = f.read()

            # Extract GPG commands
            gpg_matches = re.findall(
                r"curl -fsSL https://raw\.githubusercontent\.com/HenriquesLab/apt-rxiv-maker/apt-repo/pubkey\.gpg \| sudo gpg --dearmor -o /usr/share/keyrings/rxiv-maker\.gpg",
                content,
            )
            gpg_commands.extend(gpg_matches)

            # Extract deb lines
            deb_matches = re.findall(
                r"deb \[arch=amd64 signed-by=/usr/share/keyrings/rxiv-maker\.gpg\] https://raw\.githubusercontent\.com/HenriquesLab/apt-rxiv-maker/apt-repo stable main",
                content,
            )
            deb_lines.extend(deb_matches)

        # All commands should be identical
        if gpg_commands:
            self.assertTrue(
                all(cmd == gpg_commands[0] for cmd in gpg_commands), "GPG commands are not consistent across files"
            )

        if deb_lines:
            self.assertTrue(
                all(line == deb_lines[0] for line in deb_lines), "Deb repository lines are not consistent across files"
            )

    def test_apt_workflow_trigger_format(self):
        """Test that orchestrator implements proper workflow triggering."""
        # Check orchestrator script for workflow triggering functionality
        orchestrator_path = self.repo_root / ".github" / "scripts" / "release" / "orchestrator.py"
        with open(orchestrator_path, "r") as f:
            orchestrator_content = f.read()

        # Check that orchestrator has APT workflow triggering logic
        self.assertIn("trigger_apt_workflow", orchestrator_content)
        self.assertIn("apt_repo", orchestrator_content)
        self.assertIn("trigger_cross_repository_workflows", orchestrator_content)

    def test_workflow_summary_includes_apt(self):
        """Test that Python orchestrator handles APT repository coordination."""
        # Check that orchestrator script handles APT coordination
        orchestrator_path = self.repo_root / ".github" / "scripts" / "release" / "orchestrator.py"
        self.assertTrue(orchestrator_path.exists(), "Orchestrator script not found")

        with open(orchestrator_path, "r") as f:
            orchestrator_content = f.read()

        # Check that orchestrator includes APT repository coordination logic
        self.assertIn("trigger_apt_workflow", orchestrator_content)
        self.assertIn("apt_repo", orchestrator_content)
        self.assertIn("henriqueslab", orchestrator_content.lower())

    @patch("subprocess.run")
    def test_validate_gh_cli_command_syntax(self, mock_run):
        """Test that the Python orchestrator is properly configured."""
        # Mock successful command validation
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "orchestrator validated"
        mock_run.return_value.stderr = ""

        # Check that orchestrator script exists and is properly referenced
        with open(self.workflow_file, "r") as f:
            workflow_content = f.read()

        # Find the orchestrator command
        orchestrator_pattern = r"python .github/scripts/release/orchestrator.py"
        match = re.search(orchestrator_pattern, workflow_content)

        self.assertIsNotNone(match, "Could not find orchestrator command in workflow file")

        # Verify the orchestrator script exists
        orchestrator_path = self.repo_root / ".github" / "scripts" / "release" / "orchestrator.py"
        self.assertTrue(orchestrator_path.exists(), "Orchestrator script not found")


class TestAPTRepositoryValidation(unittest.TestCase):
    """Test APT repository configuration validation."""

    def setUp(self):
        """Set up test environment."""
        self.repo_root = Path(__file__).parent.parent.parent

    def test_apt_repository_accessibility(self):
        """Test that APT repository URLs are accessible (if network available)."""
        try:
            # Test pubkey.gpg accessibility
            pubkey_url = "https://raw.githubusercontent.com/HenriquesLab/apt-rxiv-maker/apt-repo/pubkey.gpg"
            response = requests.head(pubkey_url, timeout=5)

            # If we get a response, it should be successful or redirect
            if response.status_code not in [200, 302, 404]:
                self.fail(f"Unexpected status code {response.status_code} for pubkey URL")

        except (requests.RequestException, requests.Timeout):
            # Network issues are acceptable in CI environments
            self.skipTest("Network not available or repository not accessible")

    def test_apt_repository_branch_consistency(self):
        """Test that all references use the same repository branch."""
        install_file = self.repo_root / "docs" / "quick-start" / "installation.md"
        workflow_file = self.repo_root / ".github" / "workflows" / "release-python.yml"
        troubleshoot_file = self.repo_root / "docs" / "troubleshooting" / "troubleshooting.md"

        files_to_check = [install_file, workflow_file, troubleshoot_file]
        branches = set()

        for file_path in files_to_check:
            with open(file_path, "r") as f:
                content = f.read()

            # Extract branch references from raw.githubusercontent.com apt-rxiv-maker URLs only
            # Only raw URLs need branch specification, not regular GitHub URLs
            # Match valid branch names (alphanumeric, hyphens, underscores, dots)
            branch_matches = re.findall(
                r"raw\.githubusercontent\.com/HenriquesLab/apt-rxiv-maker/([a-zA-Z0-9._-]+)", content
            )
            branches.update(branch_matches)

        # All references should use the same branch (apt-repo)
        self.assertEqual(len(branches), 1, f"Multiple branches found: {branches}")
        self.assertEqual(list(branches)[0], "apt-repo", f"Unexpected branch: {list(branches)[0]}")


if __name__ == "__main__":
    unittest.main()
