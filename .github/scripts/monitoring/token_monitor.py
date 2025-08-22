#!/usr/bin/env python3
"""
Token Rotation Monitor for rxiv-maker.

Monitors token health, expiration, and rotation needs across all services.
Replaces complex workflow-based token management with debuggable Python.
"""

import os
import sys
from datetime import datetime
from typing import Dict

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "common"))
from config import get_github_token
from logger import setup_logger


class TokenRotationMonitor:
    """Monitor and manage token rotation across all services."""

    def __init__(self, debug: bool = False):
        self.logger = setup_logger("token_monitor", debug=debug)
        self.github_token = get_github_token()
        self.token_status = {}

        # Define critical tokens and their expected sources
        self.critical_tokens = {
            "GITHUB_TOKEN": {
                "description": "GitHub API access token",
                "env_var": "GITHUB_TOKEN",
                "secret_name": "GITHUB_TOKEN",
                "rotation_days": 90,
                "check_method": "github_api",
            },
            "PYPI_TOKEN": {
                "description": "PyPI publishing token",
                "env_var": "PYPI_TOKEN",
                "secret_name": "PYPI_TOKEN",
                "rotation_days": 365,
                "check_method": "pypi_api",
            },
            "DOCKER_TOKEN": {
                "description": "Docker Hub publishing token",
                "env_var": "DOCKER_TOKEN",
                "secret_name": "DOCKER_TOKEN",
                "rotation_days": 180,
                "check_method": "docker_api",
            },
        }

    def check_token_validity(self, token_name: str, token_config: Dict) -> Dict:
        """Check if a token is valid and working."""
        self.logger.info(f"🔑 Checking token: {token_name}")

        status = {
            "token_name": token_name,
            "description": token_config["description"],
            "is_present": False,
            "is_valid": False,
            "expiration_warning": False,
            "rotation_needed": False,
            "last_checked": datetime.now().isoformat(),
            "issues": [],
        }

        try:
            # Check if token is present in environment
            token_value = os.getenv(token_config["env_var"])
            status["is_present"] = bool(token_value)

            if not token_value:
                status["issues"].append(f"Token {token_name} not found in environment")
                return status

            # Validate token based on its type
            check_method = token_config.get("check_method", "unknown")

            if check_method == "github_api":
                status["is_valid"] = self._check_github_token(token_value)
            elif check_method == "pypi_api":
                status["is_valid"] = self._check_pypi_token(token_value)
            elif check_method == "docker_api":
                status["is_valid"] = self._check_docker_token(token_value)
            else:
                self.logger.warning(f"Unknown check method for {token_name}: {check_method}")
                status["issues"].append(f"Unknown validation method: {check_method}")

            # Check for rotation needs (this is a simplified check)
            # In a real implementation, you'd check actual token creation dates
            rotation_days = token_config.get("rotation_days", 90)
            if rotation_days <= 30:  # Example: warn if rotation is due soon
                status["rotation_needed"] = True
                status["issues"].append(f"Token rotation recommended (policy: every {rotation_days} days)")

        except Exception as e:
            self.logger.error(f"❌ Error checking token {token_name}: {e}")
            status["issues"].append(f"Token validation failed: {str(e)}")

        return status

    def _check_github_token(self, token: str) -> bool:
        """Validate GitHub token by making API call."""
        try:
            import requests

            headers = {"Authorization": f"token {token}"}
            response = requests.get("https://api.github.com/user", headers=headers, timeout=10)

            if response.status_code == 200:
                self.logger.info("✅ GitHub token is valid")
                return True
            elif response.status_code == 401:
                self.logger.error("❌ GitHub token is invalid or expired")
                return False
            else:
                self.logger.warning(f"⚠️ GitHub token check returned status {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Failed to validate GitHub token: {e}")
            return False

    def _check_pypi_token(self, token: str) -> bool:
        """Validate PyPI token (simplified check)."""
        try:
            # PyPI tokens have a specific format
            if token.startswith("pypi-") and len(token) > 20:
                self.logger.info("✅ PyPI token format appears valid")
                return True
            else:
                self.logger.error("❌ PyPI token format is invalid")
                return False

        except Exception as e:
            self.logger.error(f"❌ Failed to validate PyPI token: {e}")
            return False

    def _check_docker_token(self, token: str) -> bool:
        """Validate Docker Hub token (simplified check)."""
        try:
            # Docker tokens are typically UUIDs or have specific format
            if len(token) > 10:  # Basic length check
                self.logger.info("✅ Docker token format appears valid")
                return True
            else:
                self.logger.error("❌ Docker token format is invalid")
                return False

        except Exception as e:
            self.logger.error(f"❌ Failed to validate Docker token: {e}")
            return False

    def check_repository_secrets(self, repo_path: str = "HenriquesLab/rxiv-maker") -> Dict:
        """Check if required secrets are configured in the repository."""
        self.logger.info(f"🔐 Checking repository secrets for {repo_path}")

        secrets_status = {
            "repository": repo_path,
            "secrets_configured": {},
            "missing_secrets": [],
            "last_checked": datetime.now().isoformat(),
        }

        try:
            # Note: GitHub API doesn't allow reading secret values for security
            # We can only check if secrets exist
            url = f"https://api.github.com/repos/{repo_path}/actions/secrets"
            headers = {"Authorization": f"token {self.github_token}"}

            import requests

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                configured_secrets = {secret["name"]: secret["updated_at"] for secret in data.get("secrets", [])}

                for _token_name, token_config in self.critical_tokens.items():
                    secret_name = token_config["secret_name"]
                    if secret_name in configured_secrets:
                        secrets_status["secrets_configured"][secret_name] = configured_secrets[secret_name]
                        self.logger.info(f"✅ Secret {secret_name} is configured")
                    else:
                        secrets_status["missing_secrets"].append(secret_name)
                        self.logger.warning(f"⚠️ Secret {secret_name} is missing")
            else:
                self.logger.error(f"❌ Failed to check secrets: HTTP {response.status_code}")

        except Exception as e:
            self.logger.error(f"❌ Error checking repository secrets: {e}")

        return secrets_status

    def run_token_health_check(self) -> Dict:
        """Run comprehensive token health check."""
        self.logger.info("🔑 Starting Token Health Check")
        self.logger.info("=" * 60)

        results = {
            "token_status": {},
            "repository_secrets": {},
            "summary": {
                "total_tokens": len(self.critical_tokens),
                "valid_tokens": 0,
                "invalid_tokens": 0,
                "missing_tokens": 0,
                "rotation_needed": 0,
            },
            "last_checked": datetime.now().isoformat(),
        }

        # Check each token
        for token_name, token_config in self.critical_tokens.items():
            status = self.check_token_validity(token_name, token_config)
            results["token_status"][token_name] = status

            # Update summary
            if not status["is_present"]:
                results["summary"]["missing_tokens"] += 1
            elif status["is_valid"]:
                results["summary"]["valid_tokens"] += 1
            else:
                results["summary"]["invalid_tokens"] += 1

            if status["rotation_needed"]:
                results["summary"]["rotation_needed"] += 1

        # Check repository secrets
        results["repository_secrets"] = self.check_repository_secrets()

        # Generate summary
        self._generate_token_summary(results)
        return results

    def _generate_token_summary(self, results: Dict):
        """Generate and log token health summary."""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📊 Token Health Summary")
        self.logger.info("=" * 60)

        summary = results["summary"]
        self.logger.info(f"🔑 Total Tokens: {summary['total_tokens']}")
        self.logger.info(f"✅ Valid: {summary['valid_tokens']}")
        self.logger.info(f"❌ Invalid: {summary['invalid_tokens']}")
        self.logger.info(f"🚫 Missing: {summary['missing_tokens']}")
        self.logger.info(f"🔄 Rotation Needed: {summary['rotation_needed']}")

        # Detailed status for each token
        for token_name, status in results["token_status"].items():
            if status["is_present"] and status["is_valid"]:
                emoji = "✅"
            elif status["is_present"] and not status["is_valid"]:
                emoji = "❌"
            else:
                emoji = "🚫"

            self.logger.info(f"\n{emoji} {token_name}: {status['description']}")
            if status["issues"]:
                for issue in status["issues"]:
                    self.logger.info(f"   🔍 Issue: {issue}")

        # Repository secrets summary
        secrets = results["repository_secrets"]
        if secrets.get("missing_secrets"):
            self.logger.info("\n🔐 Missing Repository Secrets:")
            for secret in secrets["missing_secrets"]:
                self.logger.info(f"   ❌ {secret}")


def main():
    """Main function for token monitoring."""
    import argparse

    parser = argparse.ArgumentParser(description="Token Rotation Monitor")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--repo", default="HenriquesLab/rxiv-maker", help="Repository to check secrets for")

    args = parser.parse_args()

    try:
        monitor = TokenRotationMonitor(debug=args.debug)
        results = monitor.run_token_health_check()

        if args.json:
            import json

            print(json.dumps(results, indent=2, default=str))

        # Exit with appropriate code
        invalid_tokens = results["summary"]["invalid_tokens"]
        missing_tokens = results["summary"]["missing_tokens"]

        if invalid_tokens > 0 or missing_tokens > 0:
            monitor.logger.error(f"❌ Token issues found: {invalid_tokens} invalid, {missing_tokens} missing")
            sys.exit(1)
        else:
            monitor.logger.info("✅ All tokens are healthy")
            sys.exit(0)

    except Exception as e:
        print(f"❌ Token monitoring failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
