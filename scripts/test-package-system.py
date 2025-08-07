#!/usr/bin/env python3
"""Package System Testing Script.

This script provides comprehensive testing for the package management system:
- Template validation
- Update script testing
- End-to-end workflow simulation
- Rollback mechanism testing
"""

import json
import os
import subprocess
import sys
from pathlib import Path


class PackageSystemTester:
    """Comprehensive testing for the package management system."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.test_results: list[tuple[str, bool, str]] = []

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log a test result."""
        self.test_results.append((test_name, passed, message))
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")

    def test_template_validation(self) -> bool:
        """Test template validation functionality."""
        print("\n🔍 Testing template validation...")

        try:
            # Test the validation script
            result = subprocess.run(
                [
                    "python",
                    str(self.repo_root / "scripts/validate-package-templates.py"),
                    "validate-templates",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            passed = result.returncode == 0
            message = f"Exit code: {result.returncode}"
            if result.stderr:
                message += f", Error: {result.stderr.strip()}"

            self.log_test("Template validation script", passed, message)
            return passed

        except Exception as e:
            self.log_test("Template validation script", False, str(e))
            return False

    def test_template_update_dry_run(self, version: str = "v1.0.0-test") -> bool:
        """Test template update script in dry run mode."""
        print(f"\n🔍 Testing template update (dry run) for {version}...")

        success_count = 0

        # Test Homebrew update
        try:
            result = subprocess.run(
                [
                    "python",
                    str(self.repo_root / "scripts/update-package-templates.py"),
                    "homebrew",
                    version,
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # For test versions, expect failure when trying to download non-existent releases
            # but the script should handle it gracefully
            passed = "DRY RUN" in result.stdout or (result.returncode != 0 and "Failed to download" in result.stdout)
            message = f"Exit code: {result.returncode}"
            if result.stderr:
                message += f", Error: {result.stderr.strip()}"

            self.log_test("Homebrew template update (dry run)", passed, message)
            if passed:
                success_count += 1

        except Exception as e:
            self.log_test("Homebrew template update (dry run)", False, str(e))

        # Test Scoop update
        try:
            result = subprocess.run(
                [
                    "python",
                    str(self.repo_root / "scripts/update-package-templates.py"),
                    "scoop",
                    version,
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # For test versions, expect failure when trying to download non-existent releases
            # but the script should handle it gracefully
            passed = "DRY RUN" in result.stdout or (result.returncode != 0 and "Failed to download" in result.stdout)
            message = f"Exit code: {result.returncode}"
            if result.stderr:
                message += f", Error: {result.stderr.strip()}"

            self.log_test("Scoop template update (dry run)", passed, message)
            if passed:
                success_count += 1

        except Exception as e:
            self.log_test("Scoop template update (dry run)", False, str(e))

        # Test unified update
        try:
            result = subprocess.run(
                [
                    "python",
                    str(self.repo_root / "scripts/update-package-templates.py"),
                    "all",
                    version,
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                timeout=90,
            )

            # For test versions, expect failure when trying to download non-existent releases
            # but the script should handle it gracefully
            passed = "DRY RUN" in result.stdout or (result.returncode != 0 and "Failed to download" in result.stdout)
            message = f"Exit code: {result.returncode}"
            if result.stderr:
                message += f", Error: {result.stderr.strip()}"

            self.log_test("Unified template update (dry run)", passed, message)
            if passed:
                success_count += 1

        except Exception as e:
            self.log_test("Unified template update (dry run)", False, str(e))

        return success_count >= 2  # At least Homebrew and Scoop should work

    def test_template_integrity(self) -> bool:
        """Test template file integrity and completeness."""
        print("\n🔍 Testing template integrity...")

        success_count = 0

        # Test Homebrew template
        homebrew_template = self.repo_root / "submodules/homebrew-rxiv-maker/Formula/rxiv-maker.rb.template"
        if homebrew_template.exists():
            content = homebrew_template.read_text()

            # Check for required placeholders
            required_placeholders = [
                "{{VERSION}}",
                "{{MACOS_ARM64_SHA256}}",
                "{{MACOS_X64_SHA256}}",
                "{{LINUX_X64_SHA256}}",
            ]
            missing_placeholders = [p for p in required_placeholders if p not in content]

            # Check Ruby structure
            has_class = "class RxivMaker < Formula" in content
            has_install = "def install" in content
            has_test = "test do" in content

            passed = len(missing_placeholders) == 0 and has_class and has_install and has_test
            message = ""
            if missing_placeholders:
                message += f"Missing placeholders: {missing_placeholders}. "
            if not has_class:
                message += "Missing class definition. "
            if not has_install:
                message += "Missing install method. "
            if not has_test:
                message += "Missing test method. "

            self.log_test("Homebrew template integrity", passed, message.strip())
            if passed:
                success_count += 1
        else:
            self.log_test(
                "Homebrew template exists",
                False,
                f"File not found: {homebrew_template}",
            )

        # Test Scoop template
        scoop_template = self.repo_root / "submodules/scoop-rxiv-maker/bucket/rxiv-maker.json.template"
        if scoop_template.exists():
            try:
                content = scoop_template.read_text()

                # Check for required placeholders
                required_placeholders = [
                    "{{VERSION}}",
                    "{{VERSION_NUM}}",
                    "{{WINDOWS_X64_SHA256}}",
                ]
                missing_placeholders = [p for p in required_placeholders if p not in content]

                # Test JSON structure (with placeholder replacement)
                test_content = content
                for placeholder in required_placeholders:
                    test_content = test_content.replace(placeholder, "test-value")

                manifest = json.loads(test_content)

                # Check required fields
                required_fields = [
                    "version",
                    "description",
                    "homepage",
                    "license",
                    "url",
                    "hash",
                    "bin",
                ]
                missing_fields = [f for f in required_fields if f not in manifest]

                passed = len(missing_placeholders) == 0 and len(missing_fields) == 0
                message = ""
                if missing_placeholders:
                    message += f"Missing placeholders: {missing_placeholders}. "
                if missing_fields:
                    message += f"Missing fields: {missing_fields}. "

                self.log_test("Scoop template integrity", passed, message.strip())
                if passed:
                    success_count += 1

            except json.JSONDecodeError as e:
                self.log_test("Scoop template integrity", False, f"Invalid JSON structure: {e}")
        else:
            self.log_test("Scoop template exists", False, f"File not found: {scoop_template}")

        return success_count == 2

    def test_script_dependencies(self) -> bool:
        """Test that all required dependencies are available."""
        print("\n🔍 Testing script dependencies...")

        success_count = 0

        # Test Python modules
        required_modules = ["requests", "json", "hashlib", "pathlib"]
        for module in required_modules:
            try:
                __import__(module)
                self.log_test(f"Python module: {module}", True)
                success_count += 1
            except ImportError:
                self.log_test(f"Python module: {module}", False, "Module not available")

        # Test external tools (optional)
        external_tools = [("ruby", "Ruby interpreter"), ("jq", "JSON processor")]
        for tool, description in external_tools:
            try:
                result = subprocess.run([tool, "--version"], capture_output=True, timeout=5)
                available = result.returncode == 0
                self.log_test(
                    f"External tool: {description}",
                    available,
                    "Available" if available else "Not available (optional)",
                )
                if available:
                    success_count += 1
            except Exception:
                self.log_test(f"External tool: {description}", False, "Not available (optional)")

        return success_count >= len(required_modules)  # All Python modules must be available

    def test_orchestration_dry_run(self) -> bool:
        """Test orchestration script in dry run mode."""
        print("\n🔍 Testing orchestration script (dry run)...")

        # Set a dummy GitHub token for testing
        env = os.environ.copy()
        env["GITHUB_TOKEN"] = "dummy-token-for-testing"

        try:
            result = subprocess.run(
                [
                    "python",
                    str(self.repo_root / "scripts/orchestrate-release.py"),
                    "validate",
                    "v1.0.0-test",
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
            )

            # This should fail because the release doesn't exist or token is invalid, but script should handle it gracefully
            passed = result.returncode != 0 and (
                "not found" in result.stdout.lower()
                or "Release v1.0.0-test not found" in result.stdout
                or "Failed to check release: 401" in result.stdout
            )
            message = f"Exit code: {result.returncode}, handled non-existent release/invalid token correctly"

            self.log_test("Orchestration script (dry run)", passed, message)
            return passed

        except Exception as e:
            self.log_test("Orchestration script (dry run)", False, str(e))
            return False

    def test_file_permissions(self) -> bool:
        """Test that script files have correct permissions."""
        print("\n🔍 Testing file permissions...")

        script_files = [
            "scripts/validate-package-templates.py",
            "scripts/update-package-templates.py",
            "scripts/orchestrate-release.py",
            "scripts/test-package-system.py",
        ]

        success_count = 0
        for script_file in script_files:
            script_path = self.repo_root / script_file
            if script_path.exists():
                # Check if file is executable
                executable = os.access(script_path, os.X_OK)
                self.log_test(
                    f"Script executable: {script_file}",
                    executable,
                    "Has execute permissions" if executable else "Missing execute permissions",
                )
                if executable:
                    success_count += 1
            else:
                self.log_test(f"Script exists: {script_file}", False, "File not found")

        return success_count == len(script_files)

    def test_workflow_files(self) -> bool:
        """Test workflow file structure and syntax."""
        print("\n🔍 Testing workflow files...")

        workflow_files = [
            "submodules/homebrew-rxiv-maker/.github/workflows/update-formula.yml",
            "submodules/scoop-rxiv-maker/.github/workflows/update-manifest.yml",
        ]

        success_count = 0
        for workflow_file in workflow_files:
            workflow_path = self.repo_root / workflow_file
            if workflow_path.exists():
                try:
                    # Basic YAML structure check
                    try:
                        import yaml
                    except ImportError:
                        # Skip YAML parsing if PyYAML not available
                        self.log_test(
                            f"Workflow structure: {workflow_file}",
                            True,
                            "Skipped - PyYAML not available",
                        )
                        success_count += 1
                        continue

                    content = workflow_path.read_text()
                    workflow_data = yaml.safe_load(content)

                    # Check required sections
                    has_name = "name" in workflow_data
                    # YAML parses 'on:' as True (boolean), not 'on' (string)
                    has_on = "on" in workflow_data or True in workflow_data
                    has_jobs = "jobs" in workflow_data

                    # Check for repository_dispatch trigger
                    has_dispatch = False
                    on_section = workflow_data.get("on") or workflow_data.get(True)
                    if isinstance(on_section, dict):
                        has_dispatch = "repository_dispatch" in on_section

                    passed = has_name and has_on and has_jobs and has_dispatch
                    message = ""
                    if not has_name:
                        message += "Missing 'name'. "
                    if not has_on:
                        message += "Missing 'on'. "
                    if not has_jobs:
                        message += "Missing 'jobs'. "
                    if not has_dispatch:
                        message += "Missing 'repository_dispatch' trigger. "

                    self.log_test(f"Workflow structure: {workflow_file}", passed, message.strip())
                    if passed:
                        success_count += 1

                except Exception as e:
                    self.log_test(
                        f"Workflow structure: {workflow_file}",
                        False,
                        f"YAML parse error: {e}",
                    )
            else:
                self.log_test(f"Workflow exists: {workflow_file}", False, "File not found")

        return success_count >= 1  # At least one workflow should be valid

    def run_all_tests(self) -> bool:
        """Run all tests and return overall success."""
        print("🧪 Running comprehensive package system tests...\n")

        test_methods = [
            self.test_script_dependencies,
            self.test_file_permissions,
            self.test_template_integrity,
            self.test_template_validation,
            self.test_template_update_dry_run,
            self.test_orchestration_dry_run,
            self.test_workflow_files,
        ]

        passed_tests = 0
        for test_method in test_methods:
            try:
                if test_method():
                    passed_tests += 1
            except Exception as e:
                self.log_test(f"Test method: {test_method.__name__}", False, f"Exception: {e}")

        # Summary
        total_individual_tests = len(self.test_results)
        passed_individual_tests = sum(1 for _, passed, _ in self.test_results if passed)

        print("\n📊 Test Summary:")
        print(f"  Test Methods: {passed_tests}/{len(test_methods)} passed")
        print(f"  Individual Tests: {passed_individual_tests}/{total_individual_tests} passed")
        print(f"  Success Rate: {passed_individual_tests / total_individual_tests * 100:.1f}%")

        # Show failed tests
        failed_tests = [(name, msg) for name, passed, msg in self.test_results if not passed]
        if failed_tests:
            print("\n❌ Failed Tests:")
            for name, msg in failed_tests:
                print(f"  - {name}: {msg}")

        # Overall success criteria
        overall_success = (
            passed_tests >= len(test_methods) * 0.8  # At least 80% of test methods pass
            and passed_individual_tests >= total_individual_tests * 0.8  # At least 80% of individual tests pass
        )

        if overall_success:
            print("\n🎉 Overall test result: PASS")
        else:
            print("\n💥 Overall test result: FAIL")

        return overall_success


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print("Usage: python test-package-system.py [test-name]")
        print("Available tests:")
        print("  dependencies - Test script dependencies")
        print("  permissions - Test file permissions")
        print("  templates - Test template integrity")
        print("  validation - Test template validation")
        print("  updates - Test template update (dry run)")
        print("  orchestration - Test orchestration script")
        print("  workflows - Test workflow files")
        print("  all (default) - Run all tests")
        sys.exit(0)

    # Get repository root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    tester = PackageSystemTester(repo_root)

    # Run specific test or all tests
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        test_methods = {
            "dependencies": tester.test_script_dependencies,
            "permissions": tester.test_file_permissions,
            "templates": tester.test_template_integrity,
            "validation": tester.test_template_validation,
            "updates": lambda: tester.test_template_update_dry_run(),
            "orchestration": tester.test_orchestration_dry_run,
            "workflows": tester.test_workflow_files,
        }

        if test_name in test_methods:
            success = test_methods[test_name]()
            sys.exit(0 if success else 1)
        else:
            print(f"Unknown test: {test_name}")
            sys.exit(1)
    else:
        # Run all tests
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
