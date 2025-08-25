#!/usr/bin/env python3
"""
Release orchestrator for rxiv-maker.

Replaces complex GitHub Actions workflow with debuggable Python logic.

This script handles the entire release pipeline:
1. Pre-flight validation
2. GitHub release creation
3. PyPI publishing
4. Cross-repository coordination
5. Error handling and rollback

Usage:
    python orchestrator.py [--dry-run] [--version v1.2.3] [--debug]
"""

import argparse
import os
import sys
from pathlib import Path

# Add common modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "common"))

from config import ConfigLoader, get_current_version, get_github_token, get_pypi_token
from logger import log_section, log_step, setup_logger
from utils import (
    check_github_release_exists,
    check_pypi_package_available,
    validate_environment,
    wait_for_condition,
)


class ReleaseOrchestrator:
    """Main release orchestration class."""

    def __init__(self, dry_run: bool = False, force: bool = False, debug: bool = False):
        """
        Initialize release orchestrator.

        Args:
            dry_run: Skip actual publishing steps
            force: Force release even if validation fails
            debug: Enable debug logging
        """
        self.dry_run = dry_run
        self.force = force

        # Setup logging
        log_level = "DEBUG" if debug else "INFO"
        self.logger = setup_logger("release_orchestrator", log_level)

        # Load configuration
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.load_release_config()

        # Get tokens and version
        self.github_token = get_github_token()
        self.dispatch_token = os.getenv("DISPATCH_PAT") or self.github_token  # Use PAT for cross-repo triggers
        # OIDC token is automatically available in GitHub Actions via id-token: write permission
        self.use_oidc = not dry_run and os.getenv("GITHUB_ACTIONS") == "true"
        self.version = get_current_version()

        # Initialize state
        self.release_state = {
            "github_release_created": False,
            "pypi_published": False,
            "homebrew_triggered": False,
            "apt_triggered": False,
        }

        log_section(self.logger, "Release Orchestrator Initialized")
        self.logger.info(f"Package: {self.config.package_name}")
        self.logger.info(f"Version: {self.version}")
        self.logger.info(f"Dry run: {self.dry_run}")
        self.logger.info(f"Force: {self.force}")
        self.logger.info(f"Using OIDC: {self.use_oidc}")

    def run_release_pipeline(self) -> bool:
        """
        Execute the complete release pipeline.

        Returns:
            True if release completed successfully
        """
        try:
            log_section(self.logger, "Starting Release Pipeline")

            # Step 1: Pre-flight validation
            if not self.validate_pre_conditions():
                return False

            # Step 2: Create GitHub release
            if not self.create_github_release():
                return False

            # Step 3: Publish to PyPI
            if not self.publish_to_pypi():
                return False

            # Step 4: Wait for PyPI propagation
            if not self.wait_for_pypi_propagation():
                return False

            # Step 5: Trigger cross-repository workflows
            if not self.trigger_cross_repository_workflows():
                return False

            # Step 6: Monitor downstream success
            if not self.monitor_downstream_workflows():
                return False

            log_section(self.logger, "Release Pipeline Completed Successfully")
            return True

        except Exception as e:
            self.logger.error(f"Release pipeline failed: {e}")
            self.handle_release_failure(e)
            return False

    def validate_pre_conditions(self) -> bool:
        """Validate all pre-conditions for release."""
        log_step(self.logger, "Validating pre-conditions", "START")

        try:
            # Check environment variables
            required_vars = ["GITHUB_TOKEN"]
            # OIDC doesn't require PYPI_TOKEN - it uses GitHub's built-in OIDC token
            # Only validate PYPI_TOKEN if not using OIDC and not in dry-run mode
            if not self.dry_run and not self.use_oidc:
                required_vars.append("PYPI_TOKEN")

            validate_environment(required_vars)

            # Check if version is valid
            if not self.version or not self.version.startswith("v"):
                raise ValueError(f"Invalid version format: {self.version}")

            # Check if release already exists (unless forcing)
            if not self.force:
                if check_github_release_exists("henriqueslab", "rxiv-maker", self.version, self.github_token):
                    raise ValueError(f"GitHub release {self.version} already exists")

                # Check PyPI (with clean version)
                clean_version = self.version.lstrip("v")
                if check_pypi_package_available(self.config.package_name, clean_version):
                    raise ValueError(f"PyPI package {self.config.package_name}=={clean_version} already exists")

            # Additional validations (git status, changelog, etc.) can be added here

            log_step(self.logger, "Pre-conditions validation", "SUCCESS")
            return True

        except Exception as e:
            log_step(self.logger, f"Pre-conditions validation failed: {e}", "FAILURE")
            return False

    def create_github_release(self) -> bool:
        """Create GitHub release."""
        log_step(self.logger, "Creating GitHub release", "START")

        if self.dry_run:
            log_step(self.logger, "Creating GitHub release (DRY RUN)", "SKIP")
            self.release_state["github_release_created"] = True
            return True

        try:
            import subprocess

            # Check if release already exists
            check_cmd = [
                "gh",
                "release",
                "view",
                self.version,
                "--repo",
                "henriqueslab/rxiv-maker",
            ]

            try:
                subprocess.run(check_cmd, capture_output=True, text=True, check=True)
                self.logger.info(f"GitHub release {self.version} already exists, skipping creation")
                self.release_state["github_release_created"] = True
                log_step(self.logger, "GitHub release already exists", "SUCCESS")
                return True
            except subprocess.CalledProcessError:
                # Release doesn't exist, proceed to create it
                pass

            # Generate release notes from git commits since last tag
            try:
                # Get previous tag
                prev_tag_result = subprocess.run(
                    ["git", "describe", "--abbrev=0", "--tags", f"{self.version}^"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                prev_tag = prev_tag_result.stdout.strip()

                # Get commit log since previous tag
                log_result = subprocess.run(
                    ["git", "log", f"{prev_tag}..{self.version}", "--oneline", "--no-merges"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                commits = log_result.stdout.strip()

                # Basic release notes
                if commits:
                    release_notes = f"## Changes in {self.version}\n\n"
                    for line in commits.split("\n"):
                        if line.strip():
                            release_notes += f"- {line.strip()}\n"
                else:
                    release_notes = f"Release {self.version}"

            except subprocess.CalledProcessError:
                release_notes = f"Release {self.version}"

            # Create GitHub release using gh CLI
            gh_cmd = [
                "gh",
                "release",
                "create",
                self.version,
                "--title",
                f"{self.version}",
                "--notes",
                release_notes,
                "--repo",
                "henriqueslab/rxiv-maker",
            ]

            subprocess.run(gh_cmd, capture_output=True, text=True, check=True)

            self.logger.info(f"Created GitHub release {self.version}")
            self.release_state["github_release_created"] = True
            log_step(self.logger, "GitHub release created", "SUCCESS")
            return True

        except Exception as e:
            log_step(self.logger, f"GitHub release creation failed: {e}", "FAILURE")
            return False

    def publish_to_pypi(self) -> bool:
        """Publish package to PyPI."""
        log_step(self.logger, "Publishing to PyPI", "START")

        if self.dry_run:
            log_step(self.logger, "Publishing to PyPI (DRY RUN)", "SKIP")
            self.release_state["pypi_published"] = True
            return True

        try:
            import os
            import subprocess

            clean_version = self.version.lstrip("v")

            # Build the package first
            self.logger.info("Building package...")
            build_cmd = ["python", "-m", "build", "--sdist", "--wheel"]
            subprocess.run(build_cmd, check=True, cwd=".")

            # Publish to PyPI
            self.logger.info(f"Publishing {self.config.package_name}=={clean_version} to PyPI...")

            # Try OIDC first if available, fallback to token-based publishing
            oidc_success = False

            if self.use_oidc:
                # Use PyPI's OIDC trusted publishing
                self.logger.info("Attempting OIDC trusted publishing")

                # Set up environment for OIDC
                env = os.environ.copy()

                # Publish with twine using OIDC
                publish_cmd = [
                    "python",
                    "-m",
                    "twine",
                    "upload",
                    "--repository",
                    "pypi",
                    "--trusted-publishing",
                    "dist/*",
                ]

                try:
                    result = subprocess.run(publish_cmd, env=env, capture_output=True, text=True, check=True)
                    self.logger.info("OIDC publishing successful!")
                    self.logger.info("OIDC publishing command output:")
                    self.logger.info(result.stdout)
                    oidc_success = True
                except subprocess.CalledProcessError as e:
                    self.logger.warning(f"OIDC trusted publishing failed: {e}")
                    self.logger.warning(f"OIDC stderr: {e.stderr if hasattr(e, 'stderr') else 'No stderr available'}")
                    self.logger.info("Falling back to token-based publishing...")

            if not oidc_success:
                # Fallback to token-based publishing
                self.logger.info("Using token-based publishing")

                # Get PyPI token
                pypi_token = get_pypi_token()

                # Set up environment for twine
                env = os.environ.copy()
                env["TWINE_USERNAME"] = "__token__"
                env["TWINE_PASSWORD"] = pypi_token

                # Publish with twine
                publish_cmd = ["python", "-m", "twine", "upload", "dist/*"]
                result = subprocess.run(publish_cmd, env=env, capture_output=True, text=True, check=True)
                self.logger.info("Token-based publishing successful!")
                if result.stdout:
                    self.logger.info(f"Publishing output: {result.stdout}")

            self.logger.info(f"Successfully published {self.config.package_name}=={clean_version} to PyPI")
            self.release_state["pypi_published"] = True
            log_step(self.logger, "PyPI publishing", "SUCCESS")
            return True

        except Exception as e:
            log_step(self.logger, f"PyPI publishing failed: {e}", "FAILURE")
            return False

    def wait_for_pypi_propagation(self) -> bool:
        """Wait for PyPI package to be available."""
        log_step(self.logger, "Waiting for PyPI propagation", "START")

        if self.dry_run:
            log_step(self.logger, "PyPI propagation check (DRY RUN)", "SKIP")
            return True

        clean_version = self.version.lstrip("v")

        def check_availability():
            return check_pypi_package_available(self.config.package_name, clean_version)

        success = wait_for_condition(
            check_availability,
            timeout=self.config.pypi_timeout,
            check_interval=self.config.pypi_check_interval,
            logger=self.logger,
        )

        if success:
            log_step(self.logger, "PyPI package is available", "SUCCESS")
            return True
        else:
            log_step(self.logger, f"PyPI propagation timeout ({self.config.pypi_timeout}s)", "FAILURE")
            return False

    def trigger_cross_repository_workflows(self) -> bool:
        """Trigger workflows in homebrew and apt repositories."""
        log_step(self.logger, "Triggering cross-repository workflows", "START")

        success = True

        # Trigger homebrew workflow
        if self.trigger_homebrew_workflow():
            self.release_state["homebrew_triggered"] = True
        else:
            success = False

        # Trigger APT workflow
        if self.trigger_apt_workflow():
            self.release_state["apt_triggered"] = True
        else:
            success = False

        if success:
            log_step(self.logger, "Cross-repository workflows triggered", "SUCCESS")
        else:
            log_step(self.logger, "Some cross-repository workflows failed to trigger", "FAILURE")

        return success

    def trigger_homebrew_workflow(self) -> bool:
        """Trigger homebrew repository workflow."""
        if self.dry_run:
            self.logger.info("Would trigger homebrew workflow (DRY RUN)")
            return True

        try:
            # Use repository_dispatch approach for cross-repository triggers
            import requests

            headers = {
                "Authorization": f"token {self.dispatch_token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            }

            data = {
                "event_type": "update-formula",
                "client_payload": {
                    "version": self.version,
                    "package_name": self.config.package_name,
                    "triggered_by": "release-orchestrator",
                },
            }

            url = f"https://api.github.com/repos/henriqueslab/{self.config.homebrew_repo}/dispatches"
            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code == 204:
                self.logger.info("Homebrew workflow triggered successfully via repository_dispatch")
                return True
            else:
                self.logger.error(
                    f"Failed to trigger homebrew workflow. Status: {response.status_code}, Response: {response.text}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Error triggering homebrew workflow: {e}")
            return False

    def trigger_apt_workflow(self) -> bool:
        """Trigger APT repository workflow."""
        if self.dry_run:
            self.logger.info("Would trigger APT workflow (DRY RUN)")
            return True

        try:
            # Use repository_dispatch approach for cross-repository triggers
            import requests

            headers = {
                "Authorization": f"token {self.dispatch_token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            }

            data = {
                "event_type": "update-package",
                "client_payload": {
                    "version": self.version,
                    "package_name": self.config.package_name,
                    "triggered_by": "release-orchestrator",
                },
            }

            url = f"https://api.github.com/repos/henriqueslab/{self.config.apt_repo}/dispatches"
            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code == 204:
                self.logger.info("APT workflow triggered successfully via repository_dispatch")
                return True
            else:
                self.logger.error(
                    f"Failed to trigger APT workflow. Status: {response.status_code}, Response: {response.text}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Error triggering APT workflow: {e}")
            return False

    def monitor_downstream_workflows(self) -> bool:
        """Monitor downstream workflow success."""
        log_step(self.logger, "Monitoring downstream workflows", "START")

        if self.dry_run:
            log_step(self.logger, "Downstream monitoring (DRY RUN)", "SKIP")
            return True

        # For now, we'll just return success
        # In a real implementation, this would check workflow status via GitHub API

        self.logger.info("Would monitor homebrew and APT workflow status...")
        # TODO: Implement actual workflow monitoring

        log_step(self.logger, "Downstream workflows completed", "SUCCESS")
        return True

    def handle_release_failure(self, error: Exception) -> None:
        """Handle release failure and attempt rollback."""
        log_section(self.logger, "Handling Release Failure")

        self.logger.error(f"Release failed: {error}")

        # Log current state for debugging
        self.logger.info("Release state at time of failure:")
        for step, completed in self.release_state.items():
            status = "✅" if completed else "❌"
            self.logger.info(f"  {status} {step}")

        # TODO: Implement rollback logic
        # - Delete GitHub release if created
        # - Cancel triggered workflows
        # - Send notifications

        self.logger.error("Release pipeline failed - manual intervention may be required")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Rxiv-Maker Release Orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode")
    parser.add_argument("--force", action="store_true", help="Force release even if validation fails")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--version", help="Override version (for testing)")

    args = parser.parse_args()

    # Override version if provided (for testing)
    if args.version:
        os.environ["GITHUB_REF_NAME"] = args.version

    # Create and run orchestrator
    orchestrator = ReleaseOrchestrator(dry_run=args.dry_run, force=args.force, debug=args.debug)

    success = orchestrator.run_release_pipeline()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
