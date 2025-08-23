"""Dependency management and security update system.

This module provides functionality for:
- Automated dependency updates
- Security vulnerability tracking
- Dependency compatibility validation
- Update impact assessment
"""

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

from rxiv_maker.core.cache.advanced_cache import AdvancedCache

try:
    from ..utils.retry import get_with_retry
except ImportError:
    # Fallback when retry module isn't available
    get_with_retry = None  # type: ignore

logger = logging.getLogger(__name__)


class DependencyManager:
    """Manages dependency updates and security monitoring."""

    def __init__(self, project_dir: Path, cache_enabled: bool = True):
        """Initialize dependency manager.

        Args:
            project_dir: Project root directory
            cache_enabled: Whether to cache API responses
        """
        self.project_dir = project_dir
        self.pyproject_file = project_dir / "pyproject.toml"
        self.requirements_file = project_dir / "requirements.txt"

        self.cache = (
            AdvancedCache(
                name="dependency_updates",
                max_memory_items=200,
                max_disk_size_mb=20,
                ttl_hours=6,  # Cache for 6 hours
            )
            if cache_enabled
            else None
        )

        # PyPI and security API endpoints
        self.pypi_api_base = "https://pypi.org/pypi"
        self.security_apis = [
            "https://api.osv.dev/v1/query",  # OSV Database
            "https://pyup.io/api/v1/safety",  # Safety DB (if available)
        ]

    def analyze_current_dependencies(self) -> Dict[str, Any]:
        """Analyze current project dependencies."""
        dependencies = {}

        # Parse pyproject.toml
        if self.pyproject_file.exists():
            try:
                pyproject_deps = self._parse_pyproject_dependencies()
                dependencies.update(pyproject_deps)
            except Exception as e:
                logger.warning(f"Failed to parse pyproject.toml: {e}")

        # Parse requirements.txt if it exists
        if self.requirements_file.exists():
            try:
                req_deps = self._parse_requirements_dependencies()
                # Merge with pyproject dependencies, pyproject takes precedence
                for name, spec in req_deps.items():
                    if name not in dependencies:
                        dependencies[name] = spec
            except Exception as e:
                logger.warning(f"Failed to parse requirements.txt: {e}")

        # Get current installed versions
        installed_versions = self._get_installed_versions(list(dependencies.keys()))

        return {
            "declared_dependencies": dependencies,
            "installed_versions": installed_versions,
            "dependency_count": len(dependencies),
            "analysis_timestamp": self._get_timestamp(),
        }

    def check_for_updates(self, dependencies: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Check for available dependency updates.

        Args:
            dependencies: Dependencies to check, or None to use project dependencies

        Returns:
            Dictionary with update information
        """
        if dependencies is None:
            analysis = self.analyze_current_dependencies()
            dependencies = analysis["declared_dependencies"]

        updates_available = {}
        security_updates = {}
        errors = []

        for package_name, current_spec in dependencies.items():
            try:
                # Get latest version from PyPI
                latest_info = self._get_latest_package_info(package_name)
                if not latest_info:
                    continue

                latest_version = latest_info["info"]["version"]
                current_version = self._extract_version_from_spec(current_spec)

                # Check if update is available
                if current_version and self._version_is_newer(latest_version, current_version):
                    update_info = {
                        "package": package_name,
                        "current_version": current_version,
                        "current_spec": current_spec,
                        "latest_version": latest_version,
                        "update_type": self._classify_update_type(current_version, latest_version),
                        "release_date": latest_info["info"].get("last_serial"),
                        "summary": latest_info["info"].get("summary", ""),
                    }

                    updates_available[package_name] = update_info

                    # Check if this is a security update
                    security_info = self._check_security_update(package_name, current_version, latest_version)
                    if security_info:
                        security_updates[package_name] = security_info

            except Exception as e:
                errors.append({"package": package_name, "error": str(e), "type": "update_check_failed"})
                logger.debug(f"Error checking updates for {package_name}: {e}")

        return {
            "updates_available": updates_available,
            "security_updates": security_updates,
            "total_packages_checked": len(dependencies),
            "updates_found": len(updates_available),
            "security_updates_found": len(security_updates),
            "errors": errors,
            "check_timestamp": self._get_timestamp(),
        }

    def assess_update_impact(self, package_name: str, target_version: str) -> Dict[str, Any]:
        """Assess the impact of updating a specific package.

        Args:
            package_name: Name of package to update
            target_version: Target version to update to

        Returns:
            Impact assessment results
        """
        impact_assessment: Dict[str, Any] = {
            "package": package_name,
            "target_version": target_version,
            "breaking_changes": [],
            "compatibility_issues": [],
            "dependency_conflicts": [],
            "recommendations": [],
            "risk_level": "unknown",
        }

        try:
            # Get package information
            package_info = self._get_package_version_info(package_name, target_version)
            if not package_info:
                impact_assessment["risk_level"] = "high"
                impact_assessment["recommendations"].append("Package version not found - verify version exists")
                return impact_assessment

            # Check for breaking changes in changelog/release notes
            breaking_changes = self._detect_breaking_changes(package_info)
            impact_assessment["breaking_changes"] = breaking_changes

            # Check dependency compatibility
            dependency_conflicts = self._check_dependency_conflicts(package_name, target_version)
            impact_assessment["dependency_conflicts"] = dependency_conflicts

            # Assess overall risk
            risk_level = self._calculate_risk_level(breaking_changes, dependency_conflicts)
            impact_assessment["risk_level"] = risk_level

            # Generate recommendations
            recommendations = self._generate_update_recommendations(
                package_name, target_version, risk_level, breaking_changes, dependency_conflicts
            )
            impact_assessment["recommendations"] = recommendations

        except Exception as e:
            logger.debug(f"Error assessing update impact for {package_name}: {e}")
            impact_assessment["error"] = str(e)
            impact_assessment["risk_level"] = "high"

        return impact_assessment

    def generate_update_script(self, updates: Dict[str, Any]) -> str:
        """Generate script to apply dependency updates.

        Args:
            updates: Updates to apply (from check_for_updates)

        Returns:
            Shell script content for applying updates
        """
        script_lines = [
            "#!/bin/bash",
            "# Automated dependency update script generated by Rxiv-Maker",
            "# Review this script before executing!",
            "",
            "set -e  # Exit on error",
            "",
            "echo 'Starting dependency updates...'",
            "",
        ]

        # Security updates first (high priority)
        security_updates = updates.get("security_updates", {})
        if security_updates:
            script_lines.extend(["echo 'Applying security updates (high priority)...'", ""])

            for package_name, update_info in security_updates.items():
                target_version = update_info.get("latest_version")
                script_lines.append(f"echo 'Updating {package_name} to {target_version} (security fix)'")
                script_lines.append(f"pip install '{package_name}=={target_version}'")
                script_lines.append("")

        # Regular updates
        regular_updates = updates.get("updates_available", {})
        regular_updates = {k: v for k, v in regular_updates.items() if k not in security_updates}

        if regular_updates:
            script_lines.extend(["echo 'Applying regular updates...'", ""])

            # Group by update type for better control
            major_updates = {}
            minor_updates = {}
            patch_updates = {}

            for package_name, update_info in regular_updates.items():
                update_type = update_info.get("update_type", "unknown")
                if update_type == "major":
                    major_updates[package_name] = update_info
                elif update_type == "minor":
                    minor_updates[package_name] = update_info
                else:
                    patch_updates[package_name] = update_info

            # Apply patch updates first (safest)
            if patch_updates:
                script_lines.append("echo 'Applying patch updates...'")
                for package_name, update_info in patch_updates.items():
                    target_version = update_info.get("latest_version")
                    script_lines.append(f"pip install '{package_name}=={target_version}'")
                script_lines.append("")

            # Apply minor updates
            if minor_updates:
                script_lines.extend(
                    [
                        "echo 'Applying minor updates (review recommended)...'",
                        "read -p 'Continue with minor updates? (y/N) ' -n 1 -r",
                        "echo",
                        "if [[ $REPLY =~ ^[Yy]$ ]]; then",
                    ]
                )
                for package_name, update_info in minor_updates.items():
                    target_version = update_info.get("latest_version")
                    script_lines.append(f"    pip install '{package_name}=={target_version}'")
                script_lines.extend(["fi", ""])

            # Apply major updates with extra caution
            if major_updates:
                script_lines.extend(
                    [
                        "echo 'Major updates available (manual review strongly recommended):'",
                    ]
                )
                for package_name, update_info in major_updates.items():
                    current_version = update_info.get("current_version")
                    target_version = update_info.get("latest_version")
                    script_lines.append(f"echo '  {package_name}: {current_version} -> {target_version}'")

                script_lines.extend(
                    [
                        "echo 'Please review breaking changes before applying major updates.'",
                        "echo 'Uncomment the following lines after review:'",
                    ]
                )

                for package_name, update_info in major_updates.items():
                    target_version = update_info.get("latest_version")
                    script_lines.append(f"# pip install '{package_name}=={target_version}'")
                script_lines.append("")

        script_lines.extend(
            ["echo 'Dependency updates completed!'", "echo 'Remember to test your application after updates.'", ""]
        )

        return "\n".join(script_lines)

    def _parse_pyproject_dependencies(self) -> Dict[str, str]:
        """Parse dependencies from pyproject.toml file."""
        dependencies = {}

        try:
            import tomllib

            with open(self.pyproject_file, "rb") as f:
                data = tomllib.load(f)

            # Main dependencies
            project_deps = data.get("project", {}).get("dependencies", [])
            for dep in project_deps:
                name, spec = self._parse_dependency_spec(dep)
                if name:
                    dependencies[name] = spec

            # Optional dependencies
            optional_deps = data.get("project", {}).get("optional-dependencies", {})
            for group_name, group_deps in optional_deps.items():
                for dep in group_deps:
                    name, spec = self._parse_dependency_spec(dep)
                    if name and name not in dependencies:  # Don't override main deps
                        dependencies[f"{name}[{group_name}]"] = spec

        except Exception as e:
            logger.debug(f"Error parsing pyproject.toml: {e}")

        return dependencies

    def _parse_requirements_dependencies(self) -> Dict[str, str]:
        """Parse dependencies from requirements.txt file."""
        dependencies = {}

        try:
            content = self.requirements_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    name, spec = self._parse_dependency_spec(line)
                    if name:
                        dependencies[name] = spec

        except Exception as e:
            logger.debug(f"Error parsing requirements.txt: {e}")

        return dependencies

    def _parse_dependency_spec(self, spec: str) -> Tuple[Optional[str], str]:
        """Parse dependency specification."""
        # Remove comments
        spec = spec.split("#")[0].strip()
        if not spec:
            return None, ""

        # Remove extras specification
        clean_spec = re.sub(r"\[.*?\]", "", spec)

        # Extract package name (first part before version specifier)
        name_match = re.match(r"^([a-zA-Z0-9\-_.]+)", clean_spec)
        if not name_match:
            return None, ""

        name = name_match.group(1).lower().replace("_", "-")
        return name, spec

    def _get_installed_versions(self, package_names: List[str]) -> Dict[str, str]:
        """Get currently installed versions of packages."""
        installed = {}

        try:
            result = subprocess.run(["pip", "list", "--format=json"], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                pip_list = json.loads(result.stdout)
                pip_packages = {pkg["name"].lower(): pkg["version"] for pkg in pip_list}

                for name in package_names:
                    normalized_name = name.lower().replace("_", "-")
                    if normalized_name in pip_packages:
                        installed[name] = pip_packages[normalized_name]

        except Exception as e:
            logger.debug(f"Error getting installed versions: {e}")

        return installed

    def _get_latest_package_info(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Get latest package information from PyPI."""
        if self.cache:
            cache_key = f"pypi_info_{package_name}"
            cached_info = self.cache.get_data(cache_key)
            if cached_info:
                return cached_info

        try:
            normalized_name = package_name.lower().replace("_", "-")
            url = f"{self.pypi_api_base}/{normalized_name}/json"

            # Use retry logic for network requests
            if get_with_retry is not None:
                response = get_with_retry(url, max_attempts=3, timeout=10)
            else:
                response = requests.get(url, timeout=10)
                response.raise_for_status()

            package_info = response.json()

            if self.cache:
                self.cache.set(cache_key, package_info, content_based=False)

            return package_info

        except Exception as e:
            logger.debug(f"Error getting PyPI info for {package_name}: {e}")
            return None

    def _get_package_version_info(self, package_name: str, version: str) -> Optional[Dict[str, Any]]:
        """Get specific version information for a package."""
        if self.cache:
            cache_key = f"pypi_version_{package_name}_{version}"
            cached_info = self.cache.get_data(cache_key)
            if cached_info:
                return cached_info

        try:
            normalized_name = package_name.lower().replace("_", "-")
            url = f"{self.pypi_api_base}/{normalized_name}/{version}/json"

            # Use retry logic for network requests
            if get_with_retry is not None:
                response = get_with_retry(url, max_attempts=3, timeout=10)
            else:
                response = requests.get(url, timeout=10)
                response.raise_for_status()

            version_info = response.json()

            if self.cache:
                self.cache.set(cache_key, version_info, content_based=False)

            return version_info

        except Exception as e:
            logger.debug(f"Error getting PyPI version info for {package_name}=={version}: {e}")
            return None

    def _extract_version_from_spec(self, spec: str) -> Optional[str]:
        """Extract version from dependency specification."""
        version_patterns = [
            r"==([^\s,]+)",  # Exact version
            r">=([^\s,]+)",  # Minimum version (use this as current)
            r">([^\s,]+)",  # Greater than
        ]

        for pattern in version_patterns:
            match = re.search(pattern, spec)
            if match:
                return match.group(1)

        return None

    def _version_is_newer(self, version1: str, version2: str) -> bool:
        """Check if version1 is newer than version2."""
        try:
            from packaging.version import parse as parse_version

            return parse_version(version1) > parse_version(version2)
        except ImportError:
            # Fallback to simple string comparison
            return version1 != version2
        except Exception as e:
            # Log version comparison failure for debugging
            logger.debug(f"Failed to compare versions {version1} and {version2}: {e}")
            return False

    def _classify_update_type(self, current_version: str, latest_version: str) -> str:
        """Classify update type (major, minor, patch)."""
        try:
            from packaging.version import parse as parse_version

            current = parse_version(current_version)
            latest = parse_version(latest_version)

            if current.major != latest.major:
                return "major"
            elif current.minor != latest.minor:
                return "minor"
            elif current.micro != latest.micro:
                return "patch"
            else:
                return "unknown"

        except ImportError:
            # Fallback logic
            current_parts = current_version.split(".")
            latest_parts = latest_version.split(".")

            if len(current_parts) >= 1 and len(latest_parts) >= 1:
                if current_parts[0] != latest_parts[0]:
                    return "major"
                elif len(current_parts) >= 2 and len(latest_parts) >= 2:
                    if current_parts[1] != latest_parts[1]:
                        return "minor"
                    else:
                        return "patch"

            return "unknown"
        except Exception as e:
            # Log version classification failure for debugging
            logger.debug(f"Failed to classify update type for {current_version} -> {latest_version}: {e}")
            return "unknown"

    def _check_security_update(
        self, package_name: str, current_version: str, latest_version: str
    ) -> Optional[Dict[str, Any]]:
        """Check if update contains security fixes."""
        # This is a simplified implementation
        # In production, you'd query security databases like OSV or Safety DB

        # For now, just flag certain packages that commonly have security updates
        security_sensitive_packages = {
            "pillow",
            "pyyaml",
            "requests",
            "urllib3",
            "cryptography",
            "django",
            "flask",
            "sqlalchemy",
            "lxml",
            "jinja2",
        }

        if package_name.lower() in security_sensitive_packages:
            # In a real implementation, query actual security databases
            return {
                "package": package_name,
                "current_version": current_version,
                "latest_version": latest_version,
                "security_advisory": "Potential security update - verify with security databases",
                "recommendation": "Update promptly and test thoroughly",
                "severity": "medium",  # Would be determined by actual advisory
            }

        return None

    def _detect_breaking_changes(self, package_info: Dict[str, Any]) -> List[str]:
        """Detect potential breaking changes from package information."""
        breaking_changes = []

        # Check for breaking change indicators in description or release notes
        description = package_info.get("info", {}).get("description", "").lower()
        summary = package_info.get("info", {}).get("summary", "").lower()

        breaking_indicators = [
            "breaking change",
            "breaking changes",
            "backwards incompatible",
            "incompatible change",
            "major refactor",
            "api change",
            "api changes",
        ]

        text_to_check = f"{description} {summary}"
        for indicator in breaking_indicators:
            if indicator in text_to_check:
                breaking_changes.append(f"Potential breaking change indicated: {indicator}")

        return breaking_changes

    def _check_dependency_conflicts(self, package_name: str, target_version: str) -> List[str]:
        """Check for potential dependency conflicts."""
        conflicts: List[str] = []

        try:
            # Get dependencies of target version
            version_info = self._get_package_version_info(package_name, target_version)
            if not version_info:
                return conflicts

            requires_dist = version_info.get("info", {}).get("requires_dist", [])
            if not requires_dist:
                return conflicts

            # Parse requirements and check against current environment
            for requirement in requires_dist:
                # This is a simplified check - real implementation would be more thorough
                if "python_version" in requirement:
                    conflicts.append(f"Python version requirement: {requirement}")

                # Check for version constraints that might conflict
                if ">=" in requirement and "<" in requirement:
                    conflicts.append(f"Strict version requirement: {requirement}")

        except Exception as e:
            logger.debug(f"Error checking conflicts for {package_name}: {e}")

        return conflicts

    def _calculate_risk_level(self, breaking_changes: List[str], dependency_conflicts: List[str]) -> str:
        """Calculate overall risk level of update."""
        if breaking_changes or dependency_conflicts:
            return "high"
        else:
            return "low"

    def _generate_update_recommendations(
        self,
        package_name: str,
        target_version: str,
        risk_level: str,
        breaking_changes: List[str],
        dependency_conflicts: List[str],
    ) -> List[str]:
        """Generate update recommendations."""
        recommendations = []

        if risk_level == "high":
            recommendations.append("Review changelog and migration guide before updating")
            recommendations.append("Test thoroughly in development environment")
            recommendations.append("Consider updating in a separate branch")

            if breaking_changes:
                recommendations.append("Review breaking changes and update code accordingly")

            if dependency_conflicts:
                recommendations.append("Resolve dependency conflicts before updating")
        else:
            recommendations.append("Low risk update - safe to apply")
            recommendations.append("Test basic functionality after update")

        recommendations.extend(
            [
                f"Backup current environment before updating {package_name}",
                "Monitor application logs after update for issues",
                "Consider pinning version after successful update",
            ]
        )

        return recommendations

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        import time

        return str(int(time.time()))
