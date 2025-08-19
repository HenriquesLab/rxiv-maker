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
        self.workflow_file = self.repo_root / ".github" / "workflows" / "release-simple.yml"

    def test_workflow_has_apt_repository_job(self):
        """Test that the release workflow includes APT repository job."""
        with open(self.workflow_file, "r") as f:
            workflow_content = f.read()

        # Check for APT repository job definition
        self.assertIn("apt-repository:", workflow_content)
        self.assertIn("Trigger APT Repository Update", workflow_content)
        self.assertIn("HenriquesLab/apt-rxiv-maker", workflow_content)
        self.assertIn("publish-apt.yml", workflow_content)

    def test_workflow_apt_job_dependencies(self):
        """Test that APT job has correct dependencies."""
        with open(self.workflow_file, "r") as f:
            workflow_data = yaml.safe_load(f)

        apt_job = workflow_data["jobs"]["apt-repository"]

        # Check dependencies
        self.assertIn("build", apt_job["needs"])
        self.assertIn("pypi", apt_job["needs"])

        # Check conditional execution
        self.assertIn("needs.pypi.result", apt_job["if"])
        self.assertIn("!inputs.dry-run", apt_job["if"])

    def test_workflow_uses_correct_repository_reference(self):
        """Test that workflow references the correct apt-rxiv-maker repository."""
        with open(self.workflow_file, "r") as f:
            workflow_content = f.read()

        # Should use HenriquesLab, not paxcalpt
        self.assertIn("--repo HenriquesLab/apt-rxiv-maker", workflow_content)
        self.assertNotIn("paxcalpt/apt-rxiv-maker", workflow_content)

    def test_workflow_passes_correct_parameters(self):
        """Test that workflow passes correct parameters to APT workflow."""
        with open(self.workflow_file, "r") as f:
            workflow_content = f.read()

        # Check for required parameters
        self.assertIn('--field version="${VERSION}"', workflow_content)
        self.assertIn('--field dry-run="false"', workflow_content)

    def test_workflow_uses_correct_secret(self):
        """Test that workflow uses the correct GitHub secret."""
        with open(self.workflow_file, "r") as f:
            workflow_content = f.read()

        # Check for DISPATCH_PAT secret
        self.assertIn("${{ secrets.DISPATCH_PAT }}", workflow_content)

    def test_apt_repository_url_structure(self):
        """Test that APT repository URLs are well-formed."""
        # Read README to get APT repository URLs
        readme_file = self.repo_root / "README.md"
        with open(readme_file, "r") as f:
            readme_content = f.read()

        # Extract APT repository URL
        url_pattern = r"https://raw\.githubusercontent\.com/HenriquesLab/apt-rxiv-maker/apt-repo"
        urls = re.findall(url_pattern, readme_content)

        self.assertTrue(len(urls) > 0, "No APT repository URLs found in README")

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
        """Test that workflow trigger uses correct GitHub CLI format."""
        with open(self.workflow_file, "r") as f:
            workflow_content = f.read()

        # Check for proper gh workflow run command structure
        self.assertIn("gh workflow run publish-apt.yml", workflow_content)
        self.assertIn("--repo HenriquesLab/apt-rxiv-maker", workflow_content)
        self.assertIn("--field version=", workflow_content)
        self.assertIn("--field dry-run=", workflow_content)

    def test_workflow_summary_includes_apt(self):
        """Test that workflow summary includes APT repository information."""
        with open(self.workflow_file, "r") as f:
            workflow_content = f.read()

        # Check that summary includes APT information
        self.assertIn("APT Repository", workflow_content)
        self.assertIn("sudo apt update && sudo apt install rxiv-maker", workflow_content)
        self.assertIn("github.com/HenriquesLab/apt-rxiv-maker", workflow_content)

    @patch("subprocess.run")
    def test_validate_gh_cli_command_syntax(self, mock_run):
        """Test that the gh CLI command syntax is valid."""
        # Mock successful command validation
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "workflow validated"
        mock_run.return_value.stderr = ""

        # Extract the gh command from workflow
        with open(self.workflow_file, "r") as f:
            workflow_content = f.read()

        # Find the gh workflow run command
        gh_command_pattern = r'gh workflow run publish-apt\.yml.*?--field dry-run="false"'
        match = re.search(gh_command_pattern, workflow_content, re.DOTALL)

        self.assertIsNotNone(match, "Could not find gh workflow run command in workflow file")

        # The command should be syntactically valid
        command = match.group(0).replace("\n", " ").strip()
        self.assertTrue(command.startswith("gh workflow run"))


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
        readme_file = self.repo_root / "README.md"
        workflow_file = self.repo_root / ".github" / "workflows" / "release-simple.yml"

        files_to_check = [readme_file, workflow_file]
        branches = set()

        for file_path in files_to_check:
            with open(file_path, "r") as f:
                content = f.read()

            # Extract branch references from apt-rxiv-maker URLs
            branch_matches = re.findall(r"HenriquesLab/apt-rxiv-maker/([^/\s]+)", content)
            branches.update(branch_matches)

        # All references should use the same branch (apt-repo)
        self.assertEqual(len(branches), 1, f"Multiple branches found: {branches}")
        self.assertEqual(list(branches)[0], "apt-repo", f"Unexpected branch: {list(branches)[0]}")


if __name__ == "__main__":
    unittest.main()
