#!/usr/bin/env python3
"""Package Template Validation Script.

This script validates both package manager templates and their generated files
to ensure they meet the required standards and contain all necessary placeholders.
"""

import hashlib
import json
import re
import sys
from pathlib import Path


class PackageValidator:
    """Validates package manager templates and generated files."""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate_homebrew_template(self, template_path: Path) -> bool:
        """Validate Homebrew formula template."""
        if not template_path.exists():
            self.errors.append(f"Homebrew template not found: {template_path}")
            return False

        content = template_path.read_text()

        # Required placeholders
        required_placeholders = [
            "{{VERSION}}",
            "{{MACOS_ARM64_SHA256}}",
            "{{MACOS_X64_SHA256}}",
            "{{LINUX_X64_SHA256}}",
        ]

        # Check for required placeholders
        for placeholder in required_placeholders:
            if placeholder not in content:
                self.errors.append(
                    f"Missing required placeholder in Homebrew template: {placeholder}"
                )

        # Check Ruby syntax basics
        if not content.strip().startswith("class RxivMaker < Formula"):
            self.errors.append(
                "Homebrew template must start with 'class RxivMaker < Formula'"
            )

        if not content.strip().endswith("end"):
            self.errors.append("Homebrew template must end with 'end'")

        # Check for required sections
        required_sections = ["desc ", "homepage ", "license ", "def install", "test do"]
        for section in required_sections:
            if section not in content:
                self.errors.append(
                    f"Missing required section in Homebrew template: {section}"
                )

        return len(self.errors) == 0

    def validate_scoop_template(self, template_path: Path) -> bool:
        """Validate Scoop manifest template."""
        if not template_path.exists():
            self.errors.append(f"Scoop template not found: {template_path}")
            return False

        content = template_path.read_text()

        # Check if it's valid JSON structure (with placeholders)
        try:
            # Replace placeholders with dummy values for JSON validation
            test_content = content
            placeholders = {
                "{{VERSION_NUM}}": "1.0.0",
                "{{VERSION}}": "v1.0.0",
                "{{WINDOWS_X64_SHA256}}": "a" * 64,
            }

            for placeholder, value in placeholders.items():
                test_content = test_content.replace(placeholder, value)

            json.loads(test_content)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON structure in Scoop template: {e}")
            return False

        # Required placeholders
        required_placeholders = [
            "{{VERSION_NUM}}",
            "{{VERSION}}",
            "{{WINDOWS_X64_SHA256}}",
        ]

        # Check for required placeholders
        for placeholder in required_placeholders:
            if placeholder not in content:
                self.errors.append(
                    f"Missing required placeholder in Scoop template: {placeholder}"
                )

        # Parse as JSON to validate structure
        temp_json = json.loads(test_content)

        # Required fields
        required_fields = [
            "version",
            "description",
            "homepage",
            "license",
            "url",
            "hash",
            "bin",
        ]
        for field in required_fields:
            if field not in temp_json:
                self.errors.append(f"Missing required field in Scoop template: {field}")

        # Check autoupdate configuration
        if "autoupdate" not in temp_json:
            self.warnings.append("Missing autoupdate configuration in Scoop template")
        elif "url" not in temp_json["autoupdate"]:
            self.warnings.append("Missing autoupdate URL in Scoop template")

        return len(self.errors) == 0

    def validate_generated_homebrew(
        self, formula_path: Path, version: str, checksums: dict[str, str]
    ) -> bool:
        """Validate generated Homebrew formula."""
        if not formula_path.exists():
            self.errors.append(f"Generated Homebrew formula not found: {formula_path}")
            return False

        content = formula_path.read_text()

        # Check that placeholders have been replaced
        if "{{" in content and "}}" in content:
            placeholders_found = re.findall(r"\{\{[^}]+\}\}", content)
            self.errors.append(
                f"Unreplaced placeholders in generated formula: {placeholders_found}"
            )

        # Check version is present
        if version not in content:
            self.errors.append(f"Version {version} not found in generated formula")

        # Check checksums are present and valid (64 char hex strings)
        for platform, checksum in checksums.items():
            if checksum not in content:
                self.errors.append(
                    f"Checksum for {platform} not found in generated formula"
                )
            elif not re.match(r"^[a-f0-9]{64}$", checksum):
                self.errors.append(
                    f"Invalid checksum format for {platform}: {checksum}"
                )

        return len(self.errors) == 0

    def validate_generated_scoop(
        self, manifest_path: Path, version: str, checksum: str
    ) -> bool:
        """Validate generated Scoop manifest."""
        if not manifest_path.exists():
            self.errors.append(f"Generated Scoop manifest not found: {manifest_path}")
            return False

        try:
            content = manifest_path.read_text()
            manifest = json.loads(content)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in generated Scoop manifest: {e}")
            return False

        # Check that placeholders have been replaced
        content_str = json.dumps(manifest)
        if "{{" in content_str and "}}" in content_str:
            placeholders_found = re.findall(r"\{\{[^}]+\}\}", content_str)
            self.errors.append(
                f"Unreplaced placeholders in generated manifest: {placeholders_found}"
            )

        # Check version
        expected_version = version.lstrip("v")
        if manifest.get("version") != expected_version:
            self.errors.append(
                f"Version mismatch: expected {expected_version}, got {manifest.get('version')}"
            )

        # Check checksum
        if manifest.get("hash") != checksum:
            self.errors.append(
                f"Checksum mismatch: expected {checksum}, got {manifest.get('hash')}"
            )

        # Validate checksum format
        if not re.match(r"^[a-f0-9]{64}$", checksum):
            self.errors.append(f"Invalid checksum format: {checksum}")

        return len(self.errors) == 0

    def validate_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """Validate that a file matches the expected SHA256 checksum."""
        if not file_path.exists():
            self.errors.append(f"File not found for checksum validation: {file_path}")
            return False

        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)

        actual_checksum = sha256_hash.hexdigest()
        if actual_checksum != expected_checksum:
            self.errors.append(
                f"Checksum mismatch for {file_path}: expected {expected_checksum}, got {actual_checksum}"
            )
            return False

        return True

    def get_summary(self) -> tuple[int, int, list[str], list[str]]:
        """Get validation summary."""
        return len(self.errors), len(self.warnings), self.errors, self.warnings


def main():
    """Main validation function."""
    if len(sys.argv) < 2:
        print("Usage: python validate-package-templates.py <command> [args...]")
        print("Commands:")
        print("  validate-templates - Validate template files")
        print("  validate-generated <version> - Validate generated files")
        print("  validate-checksum <file> <expected_hash> - Validate file checksum")
        sys.exit(1)

    validator = PackageValidator()
    command = sys.argv[1]

    if command == "validate-templates":
        # Get script directory and find templates
        script_dir = Path(__file__).parent
        repo_root = script_dir.parent

        homebrew_template = (
            repo_root / "submodules/homebrew-rxiv-maker/Formula/rxiv-maker.rb.template"
        )
        scoop_template = (
            repo_root / "submodules/scoop-rxiv-maker/bucket/rxiv-maker.json.template"
        )

        print("🔍 Validating package templates...")

        homebrew_valid = validator.validate_homebrew_template(homebrew_template)
        scoop_valid = validator.validate_scoop_template(scoop_template)

        error_count, warning_count, errors, warnings = validator.get_summary()

        print("\n📊 Validation Results:")
        print(f"  ✅ Homebrew template: {'Valid' if homebrew_valid else 'Invalid'}")
        print(f"  ✅ Scoop template: {'Valid' if scoop_valid else 'Invalid'}")
        print(f"  🚨 Errors: {error_count}")
        print(f"  ⚠️  Warnings: {warning_count}")

        if errors:
            print("\n🚨 Errors:")
            for error in errors:
                print(f"  - {error}")

        if warnings:
            print("\n⚠️  Warnings:")
            for warning in warnings:
                print(f"  - {warning}")

        sys.exit(0 if error_count == 0 else 1)

    elif command == "validate-checksum":
        if len(sys.argv) != 4:
            print("Usage: validate-checksum <file> <expected_hash>")
            sys.exit(1)

        file_path = Path(sys.argv[2])
        expected_hash = sys.argv[3]

        valid = validator.validate_checksum(file_path, expected_hash)
        error_count, _, errors, _ = validator.get_summary()

        if valid:
            print(f"✅ Checksum validation passed for {file_path}")
        else:
            print(f"❌ Checksum validation failed for {file_path}")
            for error in errors:
                print(f"  - {error}")

        sys.exit(0 if valid else 1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
