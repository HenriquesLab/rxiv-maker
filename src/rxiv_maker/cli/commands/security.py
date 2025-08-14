"""CLI commands for security scanning and dependency management."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import click

from ...security.dependency_manager import DependencyManager
from ...security.scanner import SecurityScanner
from ...utils.platform import safe_print


@click.group(name="security")
def security_group():
    """Security scanning and dependency management commands."""
    pass


@security_group.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format for scan results",
)
@click.option(
    "--source-dir", type=click.Path(exists=True, path_type=Path), default=".", help="Source directory to scan"
)
@click.option("--cache/--no-cache", default=True, help="Enable/disable result caching")
def scan(output_format: str, source_dir: Path, cache: bool):
    """Run comprehensive security scan."""
    try:
        scanner = SecurityScanner(cache_enabled=cache)

        safe_print("🔍 Running security scan...")
        safe_print("=" * 50)

        # Scan dependencies
        safe_print("\n📦 Scanning dependencies...")
        pyproject_file = source_dir / "pyproject.toml"
        requirements_file = source_dir / "requirements.txt"

        dep_scan = scanner.scan_dependencies(
            requirements_file if requirements_file.exists() else None,
            pyproject_file if pyproject_file.exists() else None,
        )

        # Scan code security
        safe_print("\n💻 Scanning code security...")
        code_scan = scanner.scan_code_security(source_dir)

        # Combine results
        scan_results = {
            "dependency_scan": dep_scan,
            "code_scan": code_scan,
            "overall_status": _calculate_overall_status(dep_scan, code_scan),
        }

        if output_format == "json":
            safe_print(json.dumps(scan_results, indent=2))
        else:
            _print_scan_results(scan_results)

        # Exit with error code if critical issues found
        if scan_results["overall_status"]["critical_issues"] > 0:
            sys.exit(1)
        elif scan_results["overall_status"]["high_issues"] > 0:
            sys.exit(2)

    except Exception as e:
        safe_print(f"❌ Security scan failed: {e}")
        raise click.ClickException(f"Security scan failed: {e}") from e


@security_group.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format for update information",
)
@click.option("--security-only", is_flag=True, help="Show only security updates")
@click.option("--cache/--no-cache", default=True, help="Enable/disable result caching")
def check_updates(output_format: str, security_only: bool, cache: bool):
    """Check for dependency updates and security fixes."""
    try:
        current_dir = Path.cwd()
        dep_manager = DependencyManager(current_dir, cache_enabled=cache)

        safe_print("🔄 Checking for dependency updates...")
        safe_print("=" * 50)

        # Analyze current dependencies
        analysis = dep_manager.analyze_current_dependencies()
        safe_print(f"\n📊 Found {analysis['dependency_count']} dependencies")

        # Check for updates
        updates = dep_manager.check_for_updates()

        if security_only:
            # Filter to show only security updates
            filtered_updates = {
                "security_updates": updates.get("security_updates", {}),
                "security_updates_found": updates.get("security_updates_found", 0),
                "check_timestamp": updates.get("check_timestamp"),
            }
            updates = filtered_updates

        if output_format == "json":
            safe_print(json.dumps(updates, indent=2))
        else:
            _print_update_results(updates, security_only)

    except Exception as e:
        safe_print(f"❌ Update check failed: {e}")
        raise click.ClickException(f"Update check failed: {e}") from e


@security_group.command()
@click.argument("package_name")
@click.argument("target_version")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format for impact assessment",
)
def assess_update(package_name: str, target_version: str, output_format: str):
    """Assess the impact of updating a specific package."""
    try:
        current_dir = Path.cwd()
        dep_manager = DependencyManager(current_dir)

        safe_print(f"🔍 Assessing update impact: {package_name} -> {target_version}")
        safe_print("=" * 60)

        assessment = dep_manager.assess_update_impact(package_name, target_version)

        if output_format == "json":
            safe_print(json.dumps(assessment, indent=2))
        else:
            _print_impact_assessment(assessment)

    except Exception as e:
        safe_print(f"❌ Impact assessment failed: {e}")
        raise click.ClickException(f"Impact assessment failed: {e}") from e


@security_group.command()
@click.option(
    "--output", type=click.Path(path_type=Path), default="update_dependencies.sh", help="Output file for update script"
)
@click.option("--security-only", is_flag=True, help="Generate script for security updates only")
@click.option("--dry-run", is_flag=True, help="Show what would be updated without generating script")
def generate_update_script(output: Path, security_only: bool, dry_run: bool):
    """Generate script to apply dependency updates."""
    try:
        current_dir = Path.cwd()
        dep_manager = DependencyManager(current_dir)

        safe_print("📝 Generating dependency update script...")
        safe_print("=" * 50)

        # Check for updates
        updates = dep_manager.check_for_updates()

        if security_only:
            # Filter to security updates only
            updates = {
                "security_updates": updates.get("security_updates", {}),
                "updates_available": {},  # Empty regular updates
            }

        total_updates = len(updates.get("security_updates", {})) + len(updates.get("updates_available", {}))

        if total_updates == 0:
            safe_print("✅ No updates available")
            return

        # Generate update script
        script_content = dep_manager.generate_update_script(updates)

        if dry_run:
            safe_print("\n📋 Update script content:")
            safe_print("-" * 30)
            safe_print(script_content)
            safe_print("-" * 30)
            safe_print(f"\nScript would be saved to: {output}")
        else:
            # Write script to file
            output.write_text(script_content, encoding="utf-8")
            output.chmod(0o755)  # Make executable

            safe_print(f"✅ Update script generated: {output}")
            safe_print(f"📊 Total updates: {total_updates}")

            if updates.get("security_updates"):
                safe_print(f"🔒 Security updates: {len(updates['security_updates'])}")

            safe_print("\n⚠️  Review the script before executing!")
            safe_print(f"Execute with: bash {output}")

    except Exception as e:
        safe_print(f"❌ Script generation failed: {e}")
        raise click.ClickException(f"Script generation failed: {e}") from e


@security_group.command()
@click.argument("input_data")
@click.option("--context", default="user_input", help="Context description for the input")
def validate_input(input_data: str, context: str):
    """Validate input for security issues."""
    try:
        scanner = SecurityScanner(cache_enabled=False)

        safe_print(f"🔍 Validating input security: {context}")
        safe_print("=" * 50)

        issues = scanner.validate_input_security(input_data, context)

        if not issues:
            safe_print("✅ No security issues detected in input")
        else:
            safe_print(f"⚠️  Found {len(issues)} security issues:")
            for issue in issues:
                severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
                    issue.get("severity", "low"), "🔵"
                )

                safe_print(f"\n{severity_icon} {issue['type'].replace('_', ' ').title()}")
                safe_print(f"   Description: {issue['description']}")
                safe_print(f"   Recommendation: {issue['recommendation']}")

            # Exit with error code for security issues
            sys.exit(1)

    except Exception as e:
        safe_print(f"❌ Input validation failed: {e}")
        raise click.ClickException(f"Input validation failed: {e}") from e


@security_group.command()
@click.argument("file_path")
@click.option("--base-dir", type=click.Path(exists=True, path_type=Path), help="Base directory to restrict access to")
def sanitize_path(file_path: str, base_dir: Optional[Path] = None):
    """Sanitize file path to prevent traversal attacks."""
    try:
        scanner = SecurityScanner(cache_enabled=False)

        safe_print(f"🔍 Sanitizing file path: {file_path}")
        safe_print("=" * 50)

        sanitized_path, warnings = scanner.sanitize_file_path(file_path, base_dir)

        safe_print(f"Original path: {file_path}")
        safe_print(f"Sanitized path: {sanitized_path}")

        if warnings:
            safe_print("\n⚠️  Warnings:")
            for warning in warnings:
                safe_print(f"   • {warning}")
        else:
            safe_print("✅ Path sanitization completed without warnings")

    except Exception as e:
        safe_print(f"❌ Path sanitization failed: {e}")
        raise click.ClickException(f"Path sanitization failed: {e}") from e


def _calculate_overall_status(dep_scan: Dict[str, Any], code_scan: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate overall security status."""
    # Count issues by severity
    critical_issues = 0
    high_issues = 0
    medium_issues = 0
    low_issues = 0

    # Count dependency vulnerabilities
    for vuln in dep_scan.get("vulnerabilities", []):
        severity = vuln.get("severity", "low").lower()
        if severity == "critical":
            critical_issues += 1
        elif severity == "high":
            high_issues += 1
        elif severity == "medium":
            medium_issues += 1
        else:
            low_issues += 1

    # Count code security issues
    for issue in code_scan.get("issues", []):
        severity = issue.get("severity", "low").lower()
        if severity == "critical":
            critical_issues += 1
        elif severity == "high":
            high_issues += 1
        elif severity == "medium":
            medium_issues += 1
        else:
            low_issues += 1

    total_issues = critical_issues + high_issues + medium_issues + low_issues

    # Determine overall status
    if critical_issues > 0:
        status = "critical"
    elif high_issues > 0:
        status = "high_risk"
    elif medium_issues > 0:
        status = "medium_risk"
    elif low_issues > 0:
        status = "low_risk"
    else:
        status = "secure"

    return {
        "status": status,
        "total_issues": total_issues,
        "critical_issues": critical_issues,
        "high_issues": high_issues,
        "medium_issues": medium_issues,
        "low_issues": low_issues,
    }


def _print_scan_results(results: Dict[str, Any]) -> None:
    """Print security scan results in table format."""
    overall = results["overall_status"]
    dep_scan = results["dependency_scan"]
    code_scan = results["code_scan"]

    safe_print("\n📊 Security Scan Summary")
    safe_print("=" * 40)

    # Overall status
    status_icon = {"secure": "✅", "low_risk": "🟢", "medium_risk": "🟡", "high_risk": "🟠", "critical": "🔴"}.get(
        overall["status"], "❓"
    )

    safe_print(f"Overall Status: {status_icon} {overall['status'].replace('_', ' ').title()}")
    safe_print(f"Total Issues: {overall['total_issues']}")

    if overall["critical_issues"] > 0:
        safe_print(f"🔴 Critical: {overall['critical_issues']}")
    if overall["high_issues"] > 0:
        safe_print(f"🟠 High: {overall['high_issues']}")
    if overall["medium_issues"] > 0:
        safe_print(f"🟡 Medium: {overall['medium_issues']}")
    if overall["low_issues"] > 0:
        safe_print(f"🟢 Low: {overall['low_issues']}")

    # Dependency scan results
    safe_print("\n📦 Dependency Security")
    safe_print("-" * 30)
    safe_print(f"Dependencies checked: {dep_scan['dependencies_checked']}")
    safe_print(f"Vulnerabilities found: {dep_scan['vulnerabilities_found']}")

    if dep_scan["vulnerabilities"]:
        safe_print("\n🔍 Dependency Vulnerabilities:")
        for vuln in dep_scan["vulnerabilities"]:
            severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
                vuln.get("severity", "low"), "🔵"
            )
            safe_print(f"  {severity_icon} {vuln['package']} {vuln.get('version', '')}")
            safe_print(f"      {vuln['vulnerability']}")

    # Code scan results
    safe_print("\n💻 Code Security")
    safe_print("-" * 30)
    safe_print(f"Files scanned: {code_scan['files_scanned']}")
    safe_print(f"Issues found: {code_scan['security_issues']}")

    if code_scan["issues"]:
        safe_print("\n🔍 Code Security Issues:")
        for issue in code_scan["issues"]:
            severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
                issue.get("severity", "low"), "🔵"
            )
            file_name = Path(issue.get("file", "")).name
            line = issue.get("line", "")
            line_info = f":{line}" if line else ""
            safe_print(f"  {severity_icon} {file_name}{line_info}")
            safe_print(f"      {issue['description']}")


def _print_update_results(updates: Dict[str, Any], security_only: bool) -> None:
    """Print dependency update results."""
    if security_only:
        safe_print("\n🔒 Security Updates Available")
        safe_print("=" * 40)

        security_updates = updates.get("security_updates", {})
        if security_updates:
            for package, info in security_updates.items():
                safe_print(f"\n🔴 {package}")
                safe_print(f"   Current: {info.get('current_version', 'unknown')}")
                safe_print(f"   Latest: {info.get('latest_version', 'unknown')}")
                safe_print(f"   Advisory: {info.get('security_advisory', 'N/A')}")
        else:
            safe_print("✅ No security updates available")
    else:
        safe_print("\n🔄 Dependency Updates Available")
        safe_print("=" * 50)

        security_updates = updates.get("security_updates", {})
        regular_updates = updates.get("updates_available", {})

        safe_print(f"Total packages checked: {updates.get('total_packages_checked', 0)}")
        safe_print(f"Updates available: {updates.get('updates_found', 0)}")
        safe_print(f"Security updates: {updates.get('security_updates_found', 0)}")

        # Security updates first
        if security_updates:
            safe_print(f"\n🔒 Security Updates ({len(security_updates)}):")
            for package, info in security_updates.items():
                safe_print(f"  🔴 {package}: {info.get('current_version')} → {info.get('latest_version')}")

        # Regular updates grouped by type
        if regular_updates:
            # Group by update type
            major_updates = {}
            minor_updates = {}
            patch_updates = {}

            for package, info in regular_updates.items():
                if package in security_updates:
                    continue  # Skip if already shown in security section

                update_type = info.get("update_type", "unknown")
                if update_type == "major":
                    major_updates[package] = info
                elif update_type == "minor":
                    minor_updates[package] = info
                else:
                    patch_updates[package] = info

            if patch_updates:
                safe_print(f"\n🟢 Patch Updates ({len(patch_updates)}):")
                for package, info in patch_updates.items():
                    safe_print(f"  {package}: {info.get('current_version')} → {info.get('latest_version')}")

            if minor_updates:
                safe_print(f"\n🟡 Minor Updates ({len(minor_updates)}):")
                for package, info in minor_updates.items():
                    safe_print(f"  {package}: {info.get('current_version')} → {info.get('latest_version')}")

            if major_updates:
                safe_print(f"\n🟠 Major Updates ({len(major_updates)}) - Review carefully:")
                for package, info in major_updates.items():
                    safe_print(f"  {package}: {info.get('current_version')} → {info.get('latest_version')}")


def _print_impact_assessment(assessment: Dict[str, Any]) -> None:
    """Print update impact assessment."""
    package = assessment["package"]
    version = assessment["target_version"]
    risk_level = assessment["risk_level"]

    risk_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(risk_level, "❓")

    safe_print(f"\n📊 Impact Assessment: {package} → {version}")
    safe_print("=" * 50)
    safe_print(f"Risk Level: {risk_icon} {risk_level.upper()}")

    # Breaking changes
    breaking_changes = assessment.get("breaking_changes", [])
    if breaking_changes:
        safe_print(f"\n⚠️  Breaking Changes ({len(breaking_changes)}):")
        for change in breaking_changes:
            safe_print(f"  • {change}")

    # Dependency conflicts
    conflicts = assessment.get("dependency_conflicts", [])
    if conflicts:
        safe_print(f"\n⚠️  Dependency Conflicts ({len(conflicts)}):")
        for conflict in conflicts:
            safe_print(f"  • {conflict}")

    # Recommendations
    recommendations = assessment.get("recommendations", [])
    if recommendations:
        safe_print("\n💡 Recommendations:")
        for rec in recommendations:
            safe_print(f"  • {rec}")

    if not breaking_changes and not conflicts and risk_level == "low":
        safe_print("\n✅ This update appears to be safe to apply")
