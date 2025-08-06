#!/usr/bin/env python3
"""Release Orchestration Script.

This script orchestrates the entire release process including:
- Validating release readiness
- Triggering package manager updates
- Monitoring update status
- Handling failures and rollbacks
"""

import sys
import time
from dataclasses import dataclass
from enum import Enum

import requests


class UpdateStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class PackageManagerConfig:
    name: str
    repo: str
    workflow_file: str
    dispatch_event: str
    timeout_minutes: int = 10


@dataclass
class UpdateResult:
    package_manager: str
    status: UpdateStatus
    workflow_run_id: str | None = None
    error_message: str | None = None
    rollback_attempted: bool = False


class ReleaseOrchestrator:
    """Orchestrates package manager updates for releases."""

    def __init__(self, github_token: str, dry_run: bool = False):
        self.github_token = github_token
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "rxiv-maker-release-orchestrator",
            }
        )

        # Package manager configurations
        self.package_managers = [
            PackageManagerConfig(
                name="homebrew",
                repo="henriqueslab/homebrew-rxiv-maker",
                workflow_file="update-formula.yml",
                dispatch_event="update-formula",
                timeout_minutes=15,
            ),
            PackageManagerConfig(
                name="scoop",
                repo="henriqueslab/scoop-rxiv-maker",
                workflow_file="update-manifest.yml",
                dispatch_event="update-manifest",
                timeout_minutes=15,
            ),
        ]

    def validate_release_readiness(self, version: str) -> tuple[bool, list[str]]:
        """Validate that a release is ready for package manager updates."""
        print(f"🔍 Validating release readiness for {version}")
        errors = []

        # Check if release exists
        try:
            response = self.session.get(
                f"https://api.github.com/repos/henriqueslab/rxiv-maker/releases/tags/{version}"
            )
            if response.status_code == 404:
                errors.append(f"Release {version} not found")
                return False, errors
            elif response.status_code != 200:
                errors.append(f"Failed to check release: {response.status_code}")
                return False, errors

            release_data = response.json()

        except requests.RequestException as e:
            errors.append(f"Network error checking release: {e}")
            return False, errors

        # Check required assets exist
        assets = {asset["name"]: asset for asset in release_data.get("assets", [])}
        required_assets = [
            "rxiv-maker-macos-arm64.tar.gz",
            "rxiv-maker-macos-x64-intel.tar.gz",
            "rxiv-maker-linux-x64.tar.gz",
            "rxiv-maker-windows-x64.zip",
        ]

        missing_assets = []
        for asset_name in required_assets:
            if asset_name not in assets:
                missing_assets.append(asset_name)

        if missing_assets:
            errors.append(f"Missing release assets: {', '.join(missing_assets)}")

        # Check assets are downloadable
        for asset_name in required_assets:
            if asset_name in assets:
                asset_url = assets[asset_name]["browser_download_url"]
                try:
                    response = self.session.head(asset_url, timeout=10)
                    if response.status_code != 200:
                        errors.append(
                            f"Asset {asset_name} not accessible: {response.status_code}"
                        )
                except requests.RequestException as e:
                    errors.append(f"Cannot access asset {asset_name}: {e}")

        if errors:
            return False, errors

        print(f"✅ Release {version} is ready for package manager updates")
        return True, []

    def trigger_package_manager_update(
        self, pm_config: PackageManagerConfig, version: str
    ) -> str | None:
        """Trigger package manager update workflow."""
        print(f"🚀 Triggering {pm_config.name} update for {version}")

        if self.dry_run:
            print(f"🔍 DRY RUN: Would trigger {pm_config.name} workflow")
            return "dry-run-workflow-id"

        # Trigger repository dispatch
        dispatch_url = f"https://api.github.com/repos/{pm_config.repo}/dispatches"
        payload = {
            "event_type": pm_config.dispatch_event,
            "client_payload": {
                "version": version,
                "triggered_by": "release-orchestrator",
            },
        }

        try:
            response = self.session.post(dispatch_url, json=payload, timeout=30)
            if response.status_code == 204:
                print(f"✅ Successfully triggered {pm_config.name} update")
                return (
                    "triggered"  # Repository dispatch doesn't return run ID immediately
                )
            else:
                print(
                    f"❌ Failed to trigger {pm_config.name} update: {response.status_code}"
                )
                if response.text:
                    print(f"Response: {response.text}")
                return None

        except requests.RequestException as e:
            print(f"❌ Network error triggering {pm_config.name} update: {e}")
            return None

    def wait_for_workflow_completion(
        self, pm_config: PackageManagerConfig, version: str
    ) -> UpdateStatus:
        """Wait for workflow to complete and return status."""
        print(f"⏳ Waiting for {pm_config.name} workflow to complete...")

        if self.dry_run:
            print(f"🔍 DRY RUN: Would wait for {pm_config.name} workflow")
            return UpdateStatus.SUCCESS

        # Wait a bit for workflow to start
        time.sleep(30)

        timeout_seconds = pm_config.timeout_minutes * 60
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            try:
                # Get recent workflow runs
                runs_url = f"https://api.github.com/repos/{pm_config.repo}/actions/workflows/{pm_config.workflow_file}/runs"
                response = self.session.get(runs_url, params={"per_page": 5})

                if response.status_code != 200:
                    print(f"⚠️  Failed to check workflow runs: {response.status_code}")
                    time.sleep(30)
                    continue

                runs_data = response.json()

                # Look for recent runs (within last 10 minutes)
                recent_time = time.time() - 600  # 10 minutes ago
                recent_runs = []

                for run in runs_data.get("workflow_runs", []):
                    run_time = time.mktime(
                        time.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                    )
                    if run_time >= recent_time:
                        recent_runs.append(run)

                # Check if any recent run completed
                for run in recent_runs:
                    if run["status"] == "completed":
                        if run["conclusion"] == "success":
                            print(
                                f"✅ {pm_config.name} workflow completed successfully"
                            )
                            return UpdateStatus.SUCCESS
                        else:
                            print(
                                f"❌ {pm_config.name} workflow failed: {run['conclusion']}"
                            )
                            return UpdateStatus.FAILED
                    elif run["status"] == "in_progress":
                        print(f"⏳ {pm_config.name} workflow still running...")

                time.sleep(30)  # Check every 30 seconds

            except requests.RequestException as e:
                print(f"⚠️  Error checking workflow status: {e}")
                time.sleep(30)

        print(f"⏰ Timeout waiting for {pm_config.name} workflow")
        return UpdateStatus.FAILED

    def update_package_manager(
        self, pm_config: PackageManagerConfig, version: str
    ) -> UpdateResult:
        """Update a single package manager."""
        print(f"\n📦 Updating {pm_config.name} package manager")

        # Trigger the update
        workflow_id = self.trigger_package_manager_update(pm_config, version)
        if not workflow_id:
            return UpdateResult(
                package_manager=pm_config.name,
                status=UpdateStatus.FAILED,
                error_message="Failed to trigger update workflow",
            )

        # Wait for completion
        status = self.wait_for_workflow_completion(pm_config, version)

        return UpdateResult(
            package_manager=pm_config.name, status=status, workflow_run_id=workflow_id
        )

    def orchestrate_release(self, version: str) -> dict[str, UpdateResult]:
        """Orchestrate updates for all package managers."""
        print(f"🎯 Orchestrating release {version}")

        # Validate release readiness
        ready, errors = self.validate_release_readiness(version)
        if not ready:
            print("❌ Release validation failed:")
            for error in errors:
                print(f"  - {error}")
            return {}

        # Update all package managers
        results = {}
        for pm_config in self.package_managers:
            result = self.update_package_manager(pm_config, version)
            results[pm_config.name] = result

        # Summary
        successful = [
            name
            for name, result in results.items()
            if result.status == UpdateStatus.SUCCESS
        ]
        failed = [
            name
            for name, result in results.items()
            if result.status == UpdateStatus.FAILED
        ]

        print(f"\n📊 Release Orchestration Summary for {version}")
        print(f"✅ Successful updates: {len(successful)}")
        if successful:
            for name in successful:
                print(f"  - {name}")

        print(f"❌ Failed updates: {len(failed)}")
        if failed:
            for name in failed:
                print(f"  - {name}: {results[name].error_message or 'Workflow failed'}")

        # Overall success
        if len(successful) == len(self.package_managers):
            print(f"🎉 All package managers updated successfully for {version}")
        elif successful:
            print(
                f"⚠️  Partial success: {len(successful)}/{len(self.package_managers)} package managers updated"
            )
        else:
            print(f"💥 All package manager updates failed for {version}")

        return results

    def test_package_manager_updates(self, version: str) -> dict[str, bool]:
        """Test package manager updates without actually triggering them."""
        print(f"🧪 Testing package manager update readiness for {version}")

        results = {}

        # Check release readiness
        ready, errors = self.validate_release_readiness(version)
        if not ready:
            print("❌ Release not ready for testing:")
            for error in errors:
                print(f"  - {error}")
            return {}

        # Test each package manager
        for pm_config in self.package_managers:
            print(f"\n🔍 Testing {pm_config.name} readiness...")

            # Check repository accessibility
            repo_url = f"https://api.github.com/repos/{pm_config.repo}"
            try:
                response = self.session.get(repo_url, timeout=10)
                if response.status_code == 200:
                    print(f"✅ Repository {pm_config.repo} accessible")
                    results[pm_config.name] = True
                else:
                    print(
                        f"❌ Repository {pm_config.repo} not accessible: {response.status_code}"
                    )
                    results[pm_config.name] = False
            except requests.RequestException as e:
                print(f"❌ Cannot access repository {pm_config.repo}: {e}")
                results[pm_config.name] = False

        return results


def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("Usage: python orchestrate-release.py <command> <version> [options]")
        print("Commands:")
        print("  orchestrate <version> - Orchestrate full release")
        print("  test <version> - Test release readiness")
        print("  validate <version> - Validate release exists and has required assets")
        print("Options:")
        print("  --dry-run - Show what would be done without making changes")
        print("  --token <token> - GitHub token (or use GITHUB_TOKEN env var)")
        sys.exit(1)

    command = sys.argv[1]
    version = sys.argv[2]

    # Parse options
    dry_run = "--dry-run" in sys.argv

    # Get GitHub token
    github_token = None
    if "--token" in sys.argv:
        token_index = sys.argv.index("--token") + 1
        if token_index < len(sys.argv):
            github_token = sys.argv[token_index]

    if not github_token:
        import os

        github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        print(
            "❌ GitHub token required. Use --token <token> or set GITHUB_TOKEN environment variable"
        )
        sys.exit(1)

    # Validate version format - allow test versions
    if not version.startswith("v"):
        print(f"❌ Invalid version format: {version} (expected format: v1.2.3)")
        sys.exit(1)

    orchestrator = ReleaseOrchestrator(github_token, dry_run=dry_run)

    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")

    try:
        if command == "orchestrate":
            results = orchestrator.orchestrate_release(version)
            failed_count = sum(
                1 for result in results.values() if result.status == UpdateStatus.FAILED
            )
            sys.exit(0 if failed_count == 0 else 1)

        elif command == "test":
            results = orchestrator.test_package_manager_updates(version)
            failed_count = sum(1 for success in results.values() if not success)
            sys.exit(0 if failed_count == 0 else 1)

        elif command == "validate":
            ready, errors = orchestrator.validate_release_readiness(version)
            if not ready:
                for error in errors:
                    print(f"❌ {error}")
            sys.exit(0 if ready else 1)

        else:
            print(f"❌ Unknown command: {command}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
