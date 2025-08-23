"""Security scanning and vulnerability assessment module.

This module provides comprehensive security scanning capabilities including:
- Dependency vulnerability scanning
- Code security analysis
- Configuration security validation
- Input validation and sanitization
- File path traversal protection
"""

import hashlib
import logging
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from rxiv_maker.core.cache.advanced_cache import AdvancedCache

logger = logging.getLogger(__name__)


class SecurityScanner:
    """Comprehensive security scanner for Rxiv-Maker."""

    def __init__(self, cache_enabled: bool = True):
        """Initialize security scanner.

        Args:
            cache_enabled: Whether to cache scan results
        """
        self.cache = (
            AdvancedCache(
                name="security_scans",
                max_memory_items=100,
                max_disk_size_mb=10,
                ttl_hours=12,  # Security scans expire quickly
            )
            if cache_enabled
            else None
        )

        # Known safe patterns and paths
        self.safe_patterns = {
            "file_extensions": {
                ".md",
                ".txt",
                ".yml",
                ".yaml",
                ".json",
                ".toml",
                ".py",
                ".tex",
                ".bib",
                ".png",
                ".jpg",
                ".jpeg",
                ".svg",
                ".pdf",
                ".r",
                ".mmd",
            },
            "url_schemes": {"http", "https", "ftp", "ftps"},
            "allowed_domains": {
                "doi.org",
                "crossref.org",
                "datacite.org",
                "joss.theoj.org",
                "github.com",
                "arxiv.org",
                "mermaid.ink",
                "pypi.org",
                "packagemanager.rstudio.com",
            },
        }

        # Dangerous patterns to detect
        self.dangerous_patterns = {
            "shell_injection": [
                re.compile(r";\s*rm\s+-rf", re.IGNORECASE),
                re.compile(r"&&\s*rm\s+-rf", re.IGNORECASE),
                re.compile(r"\|\s*sh", re.IGNORECASE),
                re.compile(r"`[^`]*`", re.IGNORECASE),
                re.compile(r"\$\([^)]*\)", re.IGNORECASE),
            ],
            "path_traversal": [
                re.compile(r"\.\.\/", re.IGNORECASE),
                re.compile(r"\.\.\\", re.IGNORECASE),
                re.compile(r"\/\.\.\/", re.IGNORECASE),
                re.compile(r"\\\.\.\\", re.IGNORECASE),
            ],
            "sensitive_files": [
                re.compile(r"\/etc\/passwd", re.IGNORECASE),
                re.compile(r"\/etc\/shadow", re.IGNORECASE),
                re.compile(r"\.ssh\/id_rsa", re.IGNORECASE),
                re.compile(r"\.aws\/credentials", re.IGNORECASE),
            ],
        }

    def scan_dependencies(
        self, requirements_file: Optional[Path] = None, pyproject_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Scan dependencies for known vulnerabilities.

        Args:
            requirements_file: Path to requirements.txt file
            pyproject_file: Path to pyproject.toml file

        Returns:
            Dictionary with vulnerability scan results
        """
        scan_key = self._generate_dependency_scan_key(requirements_file, pyproject_file)

        # Check cache first
        if self.cache:
            cached_result = self.cache.get_data(scan_key)
            if cached_result:
                logger.debug("Using cached dependency scan results")
                return cached_result

        vulnerabilities = []
        dependencies = []

        # Extract dependencies from pyproject.toml if available
        if pyproject_file and pyproject_file.exists():
            try:
                deps = self._extract_pyproject_dependencies(pyproject_file)
                dependencies.extend(deps)
            except Exception as e:
                logger.warning(f"Failed to parse pyproject.toml: {e}")

        # Extract dependencies from requirements.txt if available
        if requirements_file and requirements_file.exists():
            try:
                deps = self._extract_requirements_dependencies(requirements_file)
                dependencies.extend(deps)
            except Exception as e:
                logger.warning(f"Failed to parse requirements.txt: {e}")

        # Check for known vulnerability patterns
        for dep_name, dep_version in dependencies:
            vuln_check = self._check_dependency_vulnerability(dep_name, dep_version)
            if vuln_check:
                vulnerabilities.append(vuln_check)

        # Run external security tools if available
        external_results = self._run_external_security_tools()

        result = {
            "dependencies_checked": len(dependencies),
            "vulnerabilities_found": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
            "external_scan_results": external_results,
            "scan_timestamp": self._get_timestamp(),
            "recommendations": self._generate_security_recommendations(vulnerabilities),
        }

        # Cache results
        if self.cache:
            self.cache.set(scan_key, result, content_based=True)

        return result

    def scan_code_security(self, source_dir: Path) -> Dict[str, Any]:
        """Scan source code for security issues.

        Args:
            source_dir: Directory containing source code

        Returns:
            Dictionary with code security scan results
        """
        scan_key = f"code_security_{source_dir.name}_{self._calculate_dir_hash(source_dir)}"

        # Check cache first
        if self.cache:
            cached_result = self.cache.get_data(scan_key)
            if cached_result:
                logger.debug("Using cached code security scan results")
                return cached_result

        security_issues = []
        files_scanned = 0

        # Scan Python files for security issues
        for py_file in source_dir.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            try:
                file_issues = self._scan_python_file_security(py_file)
                security_issues.extend(file_issues)
                files_scanned += 1
            except Exception as e:
                logger.debug(f"Error scanning {py_file}: {e}")

        # Scan configuration files
        config_files = list(source_dir.rglob("*.yml")) + list(source_dir.rglob("*.yaml"))
        for config_file in config_files:
            try:
                config_issues = self._scan_config_file_security(config_file)
                security_issues.extend(config_issues)
                files_scanned += 1
            except Exception as e:
                logger.debug(f"Error scanning config {config_file}: {e}")

        result = {
            "files_scanned": files_scanned,
            "security_issues": len(security_issues),
            "issues": security_issues,
            "scan_timestamp": self._get_timestamp(),
            "recommendations": self._generate_code_security_recommendations(security_issues),
        }

        # Cache results
        if self.cache:
            self.cache.set(scan_key, result, content_based=True)

        return result

    def validate_input_security(self, input_data: Any, context: str = "unknown") -> List[Dict[str, Any]]:
        """Validate input data for security issues.

        Args:
            input_data: Data to validate
            context: Context description for logging

        Returns:
            List of security validation issues
        """
        issues = []

        if isinstance(input_data, str):
            # Check for shell injection patterns
            for pattern in self.dangerous_patterns["shell_injection"]:
                if pattern.search(input_data):
                    issues.append(
                        {
                            "type": "shell_injection_risk",
                            "severity": "high",
                            "context": context,
                            "description": "Input contains potential shell injection patterns",
                            "pattern": pattern.pattern,
                            "recommendation": "Sanitize input or use parameterized commands",
                        }
                    )

            # Check for path traversal patterns
            for pattern in self.dangerous_patterns["path_traversal"]:
                if pattern.search(input_data):
                    issues.append(
                        {
                            "type": "path_traversal_risk",
                            "severity": "high",
                            "context": context,
                            "description": "Input contains path traversal patterns",
                            "pattern": pattern.pattern,
                            "recommendation": "Validate and normalize file paths",
                        }
                    )

            # Check for sensitive file access patterns
            for pattern in self.dangerous_patterns["sensitive_files"]:
                if pattern.search(input_data):
                    issues.append(
                        {
                            "type": "sensitive_file_access",
                            "severity": "critical",
                            "context": context,
                            "description": "Input attempts to access sensitive system files",
                            "pattern": pattern.pattern,
                            "recommendation": "Restrict file access to safe directories",
                        }
                    )

        elif isinstance(input_data, dict):
            # Recursively check dictionary values
            for key, value in input_data.items():
                sub_issues = self.validate_input_security(value, f"{context}.{key}")
                issues.extend(sub_issues)

        elif isinstance(input_data, list):
            # Check list elements
            for i, item in enumerate(input_data):
                sub_issues = self.validate_input_security(item, f"{context}[{i}]")
                issues.extend(sub_issues)

        return issues

    def sanitize_file_path(self, file_path: str, base_dir: Optional[Path] = None) -> Tuple[str, List[str]]:
        """Sanitize file path to prevent traversal attacks.

        Args:
            file_path: File path to sanitize
            base_dir: Base directory to restrict access to

        Returns:
            Tuple of (sanitized_path, warnings)
        """
        warnings = []
        original_path = file_path

        # Convert to Path object for normalization
        try:
            path = Path(file_path)

            # Resolve to absolute path to eliminate .. components
            resolved_path = path.resolve()

            # Check if base_dir restriction is needed
            if base_dir:
                base_dir = base_dir.resolve()
                try:
                    resolved_path.relative_to(base_dir)
                except ValueError:
                    warnings.append(f"Path {original_path} is outside allowed base directory")
                    # Force path to be within base directory
                    resolved_path = base_dir / path.name

            # Additional safety checks
            sanitized_str = str(resolved_path)

            # Check for dangerous patterns that survived normalization
            for pattern in self.dangerous_patterns["path_traversal"]:
                if pattern.search(sanitized_str):
                    warnings.append("Path still contains traversal patterns after sanitization")
                    break

            return sanitized_str, warnings

        except Exception as e:
            warnings.append(f"Error sanitizing path {original_path}: {e}")
            # Return safe fallback
            safe_name = re.sub(r"[^\w\-_.]", "_", Path(file_path).name)
            return safe_name, warnings

    def validate_url_security(self, url: str) -> Dict[str, Any]:
        """Validate URL for security issues.

        Args:
            url: URL to validate

        Returns:
            Dictionary with validation results
        """
        validation: Dict[str, Any] = {"url": url, "is_safe": True, "issues": [], "recommendations": []}

        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in self.safe_patterns["url_schemes"]:
                validation["is_safe"] = False
                validation["issues"].append(
                    {
                        "type": "unsafe_scheme",
                        "severity": "medium",
                        "description": f"Unsupported URL scheme: {parsed.scheme}",
                        "recommendation": "Use http or https URLs only",
                    }
                )

            # Check domain against allowed list
            if parsed.hostname:
                if not any(parsed.hostname.endswith(domain) for domain in self.safe_patterns["allowed_domains"]):
                    validation["issues"].append(
                        {
                            "type": "unverified_domain",
                            "severity": "low",
                            "description": f"Domain {parsed.hostname} is not in allowed list",
                            "recommendation": "Verify domain is trustworthy",
                        }
                    )

            # Check for suspicious URL patterns
            suspicious_patterns = [
                r"javascript:",
                r"data:",
                r"file:",
                r"ftp:",
            ]

            for pattern in suspicious_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    validation["is_safe"] = False
                    validation["issues"].append(
                        {
                            "type": "suspicious_pattern",
                            "severity": "high",
                            "description": f"URL contains suspicious pattern: {pattern}",
                            "recommendation": "Avoid URLs with active content schemes",
                        }
                    )

        except Exception as e:
            validation["is_safe"] = False
            validation["issues"].append(
                {
                    "type": "parsing_error",
                    "severity": "medium",
                    "description": f"Error parsing URL: {e}",
                    "recommendation": "Verify URL format is correct",
                }
            )

        return validation

    def _extract_pyproject_dependencies(self, pyproject_file: Path) -> List[Tuple[str, str]]:
        """Extract dependencies from pyproject.toml file."""
        dependencies = []

        try:
            import tomllib

            with open(pyproject_file, "rb") as f:
                data = tomllib.load(f)

            # Extract main dependencies
            project_deps = data.get("project", {}).get("dependencies", [])
            for dep in project_deps:
                name, version = self._parse_dependency_spec(dep)
                if name:
                    dependencies.append((name, version))

            # Extract optional dependencies
            optional_deps = data.get("project", {}).get("optional-dependencies", {})
            for group_deps in optional_deps.values():
                for dep in group_deps:
                    name, version = self._parse_dependency_spec(dep)
                    if name:
                        dependencies.append((name, version))

        except Exception as e:
            logger.debug(f"Error parsing pyproject.toml: {e}")

        return dependencies

    def _extract_requirements_dependencies(self, requirements_file: Path) -> List[Tuple[str, str]]:
        """Extract dependencies from requirements.txt file."""
        dependencies = []

        try:
            content = requirements_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    name, version = self._parse_dependency_spec(line)
                    if name:
                        dependencies.append((name, version))

        except Exception as e:
            logger.debug(f"Error parsing requirements.txt: {e}")

        return dependencies

    def _parse_dependency_spec(self, spec: str) -> Tuple[Optional[str], str]:
        """Parse dependency specification to extract name and version."""
        # Remove extras specification
        spec = re.sub(r"\[.*?\]", "", spec)

        # Common version specifiers
        version_patterns = [
            r"==([^,\s]+)",  # Exact version
            r">=([^,\s]+)",  # Minimum version
            r">([^,\s]+)",  # Greater than
            r"<=([^,\s]+)",  # Maximum version
            r"<([^,\s]+)",  # Less than
            r"~=([^,\s]+)",  # Compatible version
        ]

        name = re.split(r"[<>=~!]", spec)[0].strip()
        version = "unspecified"

        for pattern in version_patterns:
            match = re.search(pattern, spec)
            if match:
                version = match.group(1)
                break

        return name if name else None, version

    def _check_dependency_vulnerability(self, name: str, version: str) -> Optional[Dict[str, Any]]:
        """Check if a dependency has known vulnerabilities."""
        # This is a simplified check - in production you'd use a vulnerability database
        known_vulnerable = {
            "pillow": ["<8.0.0", "<9.0.0"],  # Example vulnerable versions
            "pyyaml": ["<6.0.0"],
            "requests": ["<2.28.0"],
        }

        if name.lower() in known_vulnerable:
            vulnerable_versions = known_vulnerable[name.lower()]
            # This is simplified version checking - real implementation would be more robust
            for vuln_version in vulnerable_versions:
                if version == "unspecified" or self._version_matches_pattern(version, vuln_version):
                    return {
                        "package": name,
                        "version": version,
                        "vulnerability": f"Version matches vulnerable pattern {vuln_version}",
                        "severity": "medium",
                        "recommendation": f"Update {name} to a newer version",
                    }

        return None

    def _version_matches_pattern(self, version: str, pattern: str) -> bool:
        """Simple version pattern matching."""
        # This is a very simplified implementation
        if pattern.startswith("<"):
            pattern_version = pattern[1:]
            # Simple string comparison - real implementation would use packaging.version
            return version < pattern_version
        return False

    def _run_external_security_tools(self) -> Dict[str, Any]:
        """Run external security scanning tools if available."""
        results = {}

        # Try to run bandit (Python security scanner)
        try:
            result = subprocess.run(["bandit", "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                results["bandit_available"] = True
                # Note: In production, you'd run actual bandit scan here
            else:
                results["bandit_available"] = False
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            results["bandit_available"] = False

        # Try to run safety (dependency vulnerability scanner)
        try:
            result = subprocess.run(["safety", "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                results["safety_available"] = True
            else:
                results["safety_available"] = False
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            results["safety_available"] = False

        return results

    def _scan_python_file_security(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan Python file for security issues."""
        issues = []

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            for line_num, line in enumerate(lines, 1):
                # Check for dangerous subprocess usage
                if re.search(r"subprocess\.(call|run|Popen).*shell\s*=\s*True", line):
                    issues.append(
                        {
                            "type": "shell_injection_risk",
                            "severity": "high",
                            "file": str(file_path),
                            "line": line_num,
                            "description": "Subprocess call with shell=True can be vulnerable",
                            "recommendation": "Use shell=False and pass arguments as list",
                        }
                    )

                # Check for eval usage
                if re.search(r"\beval\s*\(", line):
                    issues.append(
                        {
                            "type": "code_injection_risk",
                            "severity": "critical",
                            "file": str(file_path),
                            "line": line_num,
                            "description": "Use of eval() can execute arbitrary code",
                            "recommendation": "Avoid eval() or use ast.literal_eval() for safe evaluation",
                        }
                    )

                # Check for exec usage
                if re.search(r"\bexec\s*\(", line):
                    issues.append(
                        {
                            "type": "code_injection_risk",
                            "severity": "critical",
                            "file": str(file_path),
                            "line": line_num,
                            "description": "Use of exec() can execute arbitrary code",
                            "recommendation": "Avoid exec() or ensure input is properly validated",
                        }
                    )

                # Check for hardcoded secrets (simplified)
                secret_patterns = [  # nosec B105 - These are regex patterns for detecting secrets, not actual secrets
                    (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
                    (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
                    (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret"),
                ]

                for pattern, desc in secret_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append(
                            {
                                "type": "hardcoded_secret",
                                "severity": "medium",
                                "file": str(file_path),
                                "line": line_num,
                                "description": desc,
                                "recommendation": "Use environment variables or secure credential storage",
                            }
                        )

        except Exception as e:
            logger.debug(f"Error scanning Python file {file_path}: {e}")

        return issues

    def _scan_config_file_security(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan configuration file for security issues."""
        issues = []

        try:
            content = file_path.read_text(encoding="utf-8")

            # Check for secrets in YAML/config files
            secret_patterns = [
                (r"password:\s*[^\s\n]+", "Password in config file"),
                (r"api_key:\s*[^\s\n]+", "API key in config file"),
                (r"secret:\s*[^\s\n]+", "Secret in config file"),
                (r"token:\s*[^\s\n]+", "Token in config file"),
            ]

            lines = content.splitlines()
            for line_num, line in enumerate(lines, 1):
                for pattern, desc in secret_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append(
                            {
                                "type": "config_secret",
                                "severity": "medium",
                                "file": str(file_path),
                                "line": line_num,
                                "description": desc,
                                "recommendation": "Use environment variables for sensitive values",
                            }
                        )

        except Exception as e:
            logger.debug(f"Error scanning config file {file_path}: {e}")

        return issues

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped in security scan."""
        skip_patterns = [
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "dist",
            "build",
            ".pytest_cache",
            "tests",  # Skip test files for now
        ]

        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)

    def _generate_dependency_scan_key(self, requirements_file: Optional[Path], pyproject_file: Optional[Path]) -> str:
        """Generate cache key for dependency scan."""
        key_parts = ["dep_scan"]

        if requirements_file and requirements_file.exists():
            hash_obj = hashlib.md5(requirements_file.read_bytes(), usedforsecurity=False)
            key_parts.append(f"req_{hash_obj.hexdigest()[:8]}")

        if pyproject_file and pyproject_file.exists():
            hash_obj = hashlib.md5(pyproject_file.read_bytes(), usedforsecurity=False)
            key_parts.append(f"pyproject_{hash_obj.hexdigest()[:8]}")

        return "_".join(key_parts)

    def _calculate_dir_hash(self, directory: Path) -> str:
        """Calculate hash of directory contents."""
        hash_obj = hashlib.md5(usedforsecurity=False)

        for file_path in sorted(directory.rglob("*.py")):
            if not self._should_skip_file(file_path):
                try:
                    hash_obj.update(file_path.read_bytes())
                except Exception as e:
                    logging.warning(f"Failed to read file for hashing: {file_path}: {e}")

        return hash_obj.hexdigest()[:12]

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        import time

        return str(int(time.time()))

    def _generate_security_recommendations(self, vulnerabilities: List[Dict[str, Any]]) -> List[str]:
        """Generate security recommendations based on scan results."""
        recommendations = []

        if vulnerabilities:
            recommendations.append("Update vulnerable dependencies to secure versions")
            recommendations.append("Enable automated dependency scanning in CI/CD")
            recommendations.append("Regularly audit dependencies for new vulnerabilities")
        else:
            recommendations.append("Continue monitoring dependencies for new vulnerabilities")

        recommendations.extend(
            [
                "Use virtual environments to isolate dependencies",
                "Pin dependency versions in production",
                "Consider using dependency scanning tools like safety or pip-audit",
                "Review and validate all external inputs",
                "Use environment variables for sensitive configuration",
            ]
        )

        return recommendations

    def _generate_code_security_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate code security recommendations."""
        recommendations = []

        issue_types = {issue["type"] for issue in issues}

        if "shell_injection_risk" in issue_types:
            recommendations.append("Avoid subprocess calls with shell=True")
            recommendations.append("Use parameterized command execution")

        if "code_injection_risk" in issue_types:
            recommendations.append("Avoid eval() and exec() functions")
            recommendations.append("Use ast.literal_eval() for safe evaluation")

        if "hardcoded_secret" in issue_types or "config_secret" in issue_types:
            recommendations.append("Store secrets in environment variables")
            recommendations.append("Use secure credential management systems")
            recommendations.append("Never commit secrets to version control")

        if not issues:
            recommendations.append("Code security scan passed - continue following secure coding practices")

        recommendations.extend(
            [
                "Enable bandit security linting in development",
                "Use pre-commit hooks for security scanning",
                "Regularly review code for security issues",
                "Follow OWASP secure coding guidelines",
            ]
        )

        return recommendations
