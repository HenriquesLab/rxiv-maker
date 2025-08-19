#!/usr/bin/env python3
"""APT Repository Integration Validator.

This script validates the APT repository integration across the rxiv-maker project.
It checks for:
- Consistent APT repository URLs
- Proper workflow configuration
- Required secrets and parameters
- Documentation consistency
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Set

import requests
import yaml


class APTIntegrationValidator:
    """Validates APT repository integration."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.errors: List[str] = []
        self.warnings: List[str] = []

        # Expected configuration
        self.expected_org = "HenriquesLab"
        self.expected_repo = "apt-rxiv-maker"
        self.expected_branch = "apt-repo"
        self.expected_workflow = "publish-apt.yml"

    def log_error(self, message: str) -> None:
        """Log an error message."""
        self.errors.append(message)
        print(f"❌ ERROR: {message}")

    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")

    def log_success(self, message: str) -> None:
        """Log a success message."""
        print(f"✅ {message}")

    def validate_workflow_configuration(self) -> bool:
        """Validate the GitHub workflow configuration."""
        print("\n🔍 Validating workflow configuration...")

        workflow_file = self.repo_root / ".github" / "workflows" / "release-simple.yml"

        if not workflow_file.exists():
            self.log_error(f"Workflow file not found: {workflow_file}")
            return False

        try:
            with open(workflow_file, "r") as f:
                workflow_content = f.read()
            workflow_data = yaml.safe_load(workflow_content)
        except Exception as e:
            self.log_error(f"Failed to read workflow file: {e}")
            return False

        # Check for APT repository job
        if "apt-repository" not in workflow_data.get("jobs", {}):
            self.log_error("APT repository job not found in workflow")
            return False

        apt_job = workflow_data["jobs"]["apt-repository"]

        # Validate job dependencies
        expected_deps = ["build", "pypi"]
        actual_deps = apt_job.get("needs", [])

        for dep in expected_deps:
            if dep not in actual_deps:
                self.log_error(f"Missing dependency '{dep}' in apt-repository job")

        # Check conditional execution
        if_condition = apt_job.get("if", "")
        if "needs.pypi.result" not in if_condition:
            self.log_error("APT job missing PyPI success condition")

        if "!inputs.dry-run" not in if_condition:
            self.log_warning("APT job might run during dry-run mode")

        # Check workflow dispatch
        expected_repo_ref = f"{self.expected_org}/{self.expected_repo}"
        if expected_repo_ref not in workflow_content:
            self.log_error(f"Workflow doesn't reference {expected_repo_ref}")

        if self.expected_workflow not in workflow_content:
            self.log_error(f"Workflow doesn't reference {self.expected_workflow}")

        # Check secrets
        if "secrets.DISPATCH_PAT" not in workflow_content:
            self.log_error("Workflow missing DISPATCH_PAT secret")

        self.log_success("Workflow configuration validation complete")
        return len(self.errors) == 0

    def validate_repository_urls(self) -> bool:
        """Validate APT repository URLs across documentation."""
        print("\n🔍 Validating repository URLs...")

        files_to_check = [
            self.repo_root / "README.md",
            self.repo_root / "docs" / "quick-start" / "installation.md",
            self.repo_root / ".github" / "workflows" / "release-simple.yml",
        ]

        all_urls: Set[str] = set()
        file_urls: Dict[str, List[str]] = {}

        for file_path in files_to_check:
            if not file_path.exists():
                self.log_warning(f"File not found: {file_path}")
                continue

            try:
                with open(file_path, "r") as f:
                    content = f.read()
            except Exception as e:
                self.log_error(f"Failed to read {file_path}: {e}")
                continue

            # Extract apt-rxiv-maker URLs
            url_pattern = rf"https://[^/]*github[^/]*/{self.expected_org}/{self.expected_repo}/[^\s\)]*"
            urls = re.findall(url_pattern, content)

            file_urls[str(file_path)] = urls
            all_urls.update(urls)

        # Check for old repository references
        for file_path, urls in file_urls.items():
            for url in urls:
                if "paxcalpt" in url:
                    self.log_error(f"Found old repository reference in {file_path}: {url}")

        # Check URL consistency
        base_url_pattern = (
            f"https://raw.githubusercontent.com/{self.expected_org}/{self.expected_repo}/{self.expected_branch}"
        )

        consistent_urls = [url for url in all_urls if url.startswith(base_url_pattern)]

        if len(consistent_urls) == 0:
            self.log_error(f"No URLs found with expected pattern: {base_url_pattern}")
        else:
            self.log_success(f"Found {len(consistent_urls)} consistent URLs")

        return len(self.errors) == 0

    def validate_installation_commands(self) -> bool:
        """Validate APT installation command consistency."""
        print("\n🔍 Validating installation commands...")

        files_to_check = [self.repo_root / "README.md", self.repo_root / ".github" / "workflows" / "release-simple.yml"]

        gpg_commands: List[str] = []
        deb_lines: List[str] = []

        for file_path in files_to_check:
            if not file_path.exists():
                continue

            try:
                with open(file_path, "r") as f:
                    content = f.read()
            except Exception as e:
                self.log_error(f"Failed to read {file_path}: {e}")
                continue

            # Extract GPG commands
            gpg_pattern = r"curl -fsSL https://raw\.githubusercontent\.com/HenriquesLab/apt-rxiv-maker/apt-repo/pubkey\.gpg \| sudo gpg --dearmor -o /usr/share/keyrings/rxiv-maker\.gpg"
            gpg_matches = re.findall(gpg_pattern, content)
            gpg_commands.extend(gpg_matches)

            # Extract deb lines
            deb_pattern = r"deb \[arch=amd64 signed-by=/usr/share/keyrings/rxiv-maker\.gpg\] https://raw\.githubusercontent\.com/HenriquesLab/apt-rxiv-maker/apt-repo stable main"
            deb_matches = re.findall(deb_pattern, content)
            deb_lines.extend(deb_matches)

        # Check consistency
        if gpg_commands and not all(cmd == gpg_commands[0] for cmd in gpg_commands):
            self.log_error("GPG commands are inconsistent across files")
        elif gpg_commands:
            self.log_success(f"Found {len(gpg_commands)} consistent GPG commands")

        if deb_lines and not all(line == deb_lines[0] for line in deb_lines):
            self.log_error("Deb repository lines are inconsistent across files")
        elif deb_lines:
            self.log_success(f"Found {len(deb_lines)} consistent deb repository lines")

        return len(self.errors) == 0

    def validate_documentation_coverage(self) -> bool:
        """Validate that APT installation is properly documented."""
        print("\n🔍 Validating documentation coverage...")

        readme_file = self.repo_root / "README.md"
        install_doc = self.repo_root / "docs" / "quick-start" / "installation.md"

        has_apt_in_readme = False
        has_apt_in_install_doc = False

        # Check README
        if readme_file.exists():
            try:
                with open(readme_file, "r") as f:
                    readme_content = f.read()
                has_apt_in_readme = "apt-rxiv-maker" in readme_content
            except Exception as e:
                self.log_error(f"Failed to read README: {e}")

        # Check installation documentation
        if install_doc.exists():
            try:
                with open(install_doc, "r") as f:
                    install_content = f.read()
                has_apt_in_install_doc = "apt-rxiv-maker" in install_content
            except Exception:
                pass  # File might not exist yet

        if has_apt_in_readme:
            self.log_success("APT installation documented in README")
        else:
            self.log_error("APT installation not found in README")

        if has_apt_in_install_doc:
            self.log_success("APT installation documented in installation guide")
        else:
            self.log_warning("APT installation not found in installation guide")

        return has_apt_in_readme

    def validate_network_accessibility(self) -> bool:
        """Validate that APT repository URLs are accessible."""
        print("\n🔍 Validating network accessibility...")

        # Test pubkey.gpg accessibility
        pubkey_url = f"https://raw.githubusercontent.com/{self.expected_org}/{self.expected_repo}/{self.expected_branch}/pubkey.gpg"

        try:
            response = requests.head(pubkey_url, timeout=10)

            if response.status_code == 200:
                self.log_success("APT repository pubkey is accessible")
                return True
            elif response.status_code == 404:
                self.log_warning("APT repository pubkey not found (repository may not be set up yet)")
                return True
            else:
                self.log_warning(f"Unexpected status code {response.status_code} for pubkey URL")
                return True

        except (requests.RequestException, requests.Timeout) as e:
            self.log_warning(f"Network accessibility test failed: {e}")
            return True  # Don't fail on network issues

    def run_validation(self) -> bool:
        """Run all validation checks."""
        print("🚀 Starting APT repository integration validation...\n")

        all_checks_passed = True

        # Run all validation checks
        checks = [
            self.validate_workflow_configuration,
            self.validate_repository_urls,
            self.validate_installation_commands,
            self.validate_documentation_coverage,
            self.validate_network_accessibility,
        ]

        for check in checks:
            try:
                if not check():
                    all_checks_passed = False
            except Exception as e:
                self.log_error(f"Validation check failed with exception: {e}")
                all_checks_passed = False

        # Summary
        print("\n📊 Validation Summary:")
        print(f"   Errors: {len(self.errors)}")
        print(f"   Warnings: {len(self.warnings)}")

        if all_checks_passed and len(self.errors) == 0:
            print("\n🎉 All APT repository integration checks passed!")
            return True
        else:
            print("\n❌ APT repository integration validation failed!")
            return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Validate APT repository integration")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).parent.parent, help="Path to repository root")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    validator = APTIntegrationValidator(args.repo_root)

    try:
        success = validator.run_validation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Validation failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
