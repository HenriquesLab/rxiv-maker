#!/usr/bin/env python3
"""
Cross-Repository Health Monitor for rxiv-maker ecosystem.

Monitors health across all repositories: main, homebrew-tap, scoop-bucket, apt-repository.
Replaces complex workflow coordination with debuggable Python.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aiohttp

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "common"))
from config import get_github_token
from logger import setup_logger


class CrossRepoHealthMonitor:
    """Monitor health across all rxiv-maker repositories."""

    def __init__(self, debug: bool = False):
        self.logger = setup_logger("cross_repo_health", debug=debug)
        self.github_token = get_github_token()
        self.repositories = {
            "main": "HenriquesLab/rxiv-maker",
            "homebrew": "HenriquesLab/homebrew-rxiv-maker",
            "scoop": "HenriquesLab/scoop-rxiv-maker",
            "apt": "HenriquesLab/apt-rxiv-maker",
        }
        self.health_status = {}

    async def check_repository_health(self, session: aiohttp.ClientSession, repo_name: str, repo_path: str) -> Dict:
        """Check health of a single repository."""
        self.logger.info(f"🔍 Checking health of {repo_name}: {repo_path}")

        health = {
            "repository": repo_path,
            "status": "unknown",
            "checks": {},
            "issues": [],
            "last_updated": None,
            "workflow_status": "unknown",
        }

        try:
            # Check repository accessibility
            repo_info = await self._check_repo_accessibility(session, repo_path)
            health["checks"]["accessibility"] = "pass" if repo_info else "fail"

            if repo_info:
                health["last_updated"] = repo_info.get("updated_at")

                # Check recent commits
                commits_ok = await self._check_recent_activity(session, repo_path)
                health["checks"]["recent_activity"] = "pass" if commits_ok else "warn"

                # Check workflow status
                workflow_status = await self._check_workflow_status(session, repo_path)
                health["checks"]["workflows"] = workflow_status
                health["workflow_status"] = workflow_status

                # Check for open issues
                issues = await self._check_critical_issues(session, repo_path)
                health["checks"]["critical_issues"] = "pass" if len(issues) == 0 else "warn"
                health["issues"] = issues

                # Determine overall status
                if all(check in ["pass", "warn"] for check in health["checks"].values()):
                    health["status"] = (
                        "healthy" if all(check == "pass" for check in health["checks"].values()) else "warning"
                    )
                else:
                    health["status"] = "failing"
            else:
                health["status"] = "inaccessible"
                health["issues"].append("Repository is not accessible")

        except Exception as e:
            self.logger.error(f"❌ Error checking {repo_name}: {e}")
            health["status"] = "error"
            health["issues"].append(f"Health check failed: {str(e)}")

        return health

    async def _check_repo_accessibility(self, session: aiohttp.ClientSession, repo_path: str) -> Optional[Dict]:
        """Check if repository is accessible."""
        try:
            url = f"https://api.github.com/repos/{repo_path}"
            headers = {"Authorization": f"token {self.github_token}"}

            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.warning(f"Repository {repo_path} returned status {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"Failed to check accessibility for {repo_path}: {e}")
            return None

    async def _check_recent_activity(self, session: aiohttp.ClientSession, repo_path: str) -> bool:
        """Check if repository has recent activity (commits in last 30 days)."""
        try:
            since_date = (datetime.now() - timedelta(days=30)).isoformat()
            url = f"https://api.github.com/repos/{repo_path}/commits?since={since_date}&per_page=1"
            headers = {"Authorization": f"token {self.github_token}"}

            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    commits = await response.json()
                    return len(commits) > 0
                return False

        except Exception as e:
            self.logger.error(f"Failed to check recent activity for {repo_path}: {e}")
            return False

    async def _check_workflow_status(self, session: aiohttp.ClientSession, repo_path: str) -> str:
        """Check status of recent workflow runs."""
        try:
            url = f"https://api.github.com/repos/{repo_path}/actions/runs?per_page=5"
            headers = {"Authorization": f"token {self.github_token}"}

            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    runs = data.get("workflow_runs", [])

                    if not runs:
                        return "no_runs"

                    # Check if any recent runs failed
                    recent_failures = [run for run in runs if run["conclusion"] == "failure"]
                    if recent_failures:
                        return "failing"

                    # Check if all recent runs succeeded
                    recent_successes = [run for run in runs if run["conclusion"] == "success"]
                    if recent_successes:
                        return "pass"

                    return "pending"
                else:
                    return "unknown"

        except Exception as e:
            self.logger.error(f"Failed to check workflow status for {repo_path}: {e}")
            return "error"

    async def _check_critical_issues(self, session: aiohttp.ClientSession, repo_path: str) -> List[Dict]:
        """Check for critical open issues."""
        try:
            url = f"https://api.github.com/repos/{repo_path}/issues?labels=bug,critical&state=open&per_page=10"
            headers = {"Authorization": f"token {self.github_token}"}

            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    issues = await response.json()
                    return [
                        {
                            "number": issue["number"],
                            "title": issue["title"],
                            "url": issue["html_url"],
                            "created_at": issue["created_at"],
                        }
                        for issue in issues
                    ]
                return []

        except Exception as e:
            self.logger.error(f"Failed to check critical issues for {repo_path}: {e}")
            return []

    async def run_health_check(self) -> Dict:
        """Run health check across all repositories."""
        self.logger.info("🏥 Starting Cross-Repository Health Check")
        self.logger.info("=" * 60)

        async with aiohttp.ClientSession() as session:
            tasks = []
            for repo_name, repo_path in self.repositories.items():
                task = self.check_repository_health(session, repo_name, repo_path)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for i, (repo_name, repo_path) in enumerate(self.repositories.items()):
                result = results[i]
                if isinstance(result, Exception):
                    self.logger.error(f"❌ Health check failed for {repo_name}: {result}")
                    self.health_status[repo_name] = {
                        "repository": repo_path,
                        "status": "error",
                        "issues": [f"Health check exception: {str(result)}"],
                    }
                else:
                    self.health_status[repo_name] = result

        # Generate summary
        self._generate_health_summary()
        return self.health_status

    def _generate_health_summary(self):
        """Generate and log health summary."""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📊 Cross-Repository Health Summary")
        self.logger.info("=" * 60)

        total_repos = len(self.health_status)
        healthy_repos = sum(1 for health in self.health_status.values() if health["status"] == "healthy")
        warning_repos = sum(1 for health in self.health_status.values() if health["status"] == "warning")
        failing_repos = sum(
            1 for health in self.health_status.values() if health["status"] in ["failing", "error", "inaccessible"]
        )

        self.logger.info(f"🏥 Total Repositories: {total_repos}")
        self.logger.info(f"✅ Healthy: {healthy_repos}")
        self.logger.info(f"⚠️  Warning: {warning_repos}")
        self.logger.info(f"❌ Failing: {failing_repos}")

        # Detailed status for each repo
        for repo_name, health in self.health_status.items():
            status_emoji = {"healthy": "✅", "warning": "⚠️", "failing": "❌", "error": "💥", "inaccessible": "🚫"}.get(
                health["status"], "❓"
            )

            self.logger.info(f"\n{status_emoji} {repo_name.upper()}: {health['status']}")
            if health.get("checks"):
                for check_name, check_status in health["checks"].items():
                    check_emoji = "✅" if check_status == "pass" else "⚠️" if check_status == "warn" else "❌"
                    self.logger.info(f"   {check_emoji} {check_name}: {check_status}")

            if health.get("issues"):
                for issue in health["issues"]:
                    self.logger.info(f"   🔍 Issue: {issue}")


def main():
    """Main function for cross-repository health monitoring."""
    import argparse

    parser = argparse.ArgumentParser(description="Cross-Repository Health Monitor")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    try:
        monitor = CrossRepoHealthMonitor(debug=args.debug)
        health_status = asyncio.run(monitor.run_health_check())

        if args.json:
            import json

            print(json.dumps(health_status, indent=2, default=str))

        # Exit with appropriate code
        failing_repos = sum(
            1 for health in health_status.values() if health["status"] in ["failing", "error", "inaccessible"]
        )

        if failing_repos > 0:
            monitor.logger.error(f"❌ {failing_repos} repositories are failing")
            sys.exit(1)
        else:
            monitor.logger.info("✅ All repositories are healthy or have minor warnings")
            sys.exit(0)

    except Exception as e:
        print(f"❌ Cross-repository health check failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
