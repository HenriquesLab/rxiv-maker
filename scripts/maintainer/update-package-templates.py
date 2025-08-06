#!/usr/bin/env python3
"""Unified Package Template Update Script.

This script provides a unified way to update both Homebrew and Scoop package
manager files from templates with proper validation and error handling.
"""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import requests


class TemplateUpdater:
    """Updates package manager files from templates."""

    def __init__(self, repo_root: Path, dry_run: bool = False):
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.temp_dir: Path | None = None

    def __enter__(self):
        if not self.dry_run:
            self.temp_dir = Path(tempfile.mkdtemp())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def download_and_hash(self, url: str, retries: int = 3) -> tuple[str, Path | None]:
        """Download a file and return its SHA256 hash."""
        for attempt in range(retries):
            try:
                print(f"  📥 Downloading {url} (attempt {attempt + 1}/{retries})")
                response = requests.get(url, timeout=30)
                response.raise_for_status()

                # Calculate hash
                sha256_hash = hashlib.sha256()
                sha256_hash.update(response.content)
                hash_value = sha256_hash.hexdigest()

                # Save to temp file for validation if needed
                temp_file = None
                if self.temp_dir:
                    temp_file = self.temp_dir / Path(url).name
                    temp_file.write_bytes(response.content)

                print(f"  ✅ Downloaded and hashed: {hash_value}")
                return hash_value, temp_file

            except requests.RequestException as e:
                print(f"  ❌ Download attempt {attempt + 1} failed: {e}")
                if attempt == retries - 1:
                    raise

        return "", None

    def update_homebrew_formula(self, version: str) -> bool:
        """Update Homebrew formula from template."""
        print(f"🍺 Updating Homebrew formula for version {version}")

        template_path = (
            self.repo_root
            / "submodules/homebrew-rxiv-maker/Formula/rxiv-maker.rb.template"
        )
        output_path = (
            self.repo_root / "submodules/homebrew-rxiv-maker/Formula/rxiv-maker.rb"
        )

        if not template_path.exists():
            print(f"❌ Template not found: {template_path}")
            return False

        # Download and hash binaries
        base_url = (
            f"https://github.com/henriqueslab/rxiv-maker/releases/download/{version}"
        )
        binaries = {
            "MACOS_ARM64_SHA256": f"{base_url}/rxiv-maker-macos-arm64.tar.gz",
            "MACOS_X64_SHA256": f"{base_url}/rxiv-maker-macos-x64-intel.tar.gz",
            "LINUX_X64_SHA256": f"{base_url}/rxiv-maker-linux-x64.tar.gz",
        }

        hashes = {}
        temp_files = {}

        try:
            for placeholder, url in binaries.items():
                hash_value, temp_file = self.download_and_hash(url)
                hashes[placeholder] = hash_value
                if temp_file:
                    temp_files[placeholder] = temp_file
        except Exception as e:
            print(f"❌ Failed to download binaries: {e}")
            if self.dry_run:
                print(
                    "🔍 DRY RUN: Would have downloaded binaries and calculated checksums"
                )
                # For dry run with test versions, use dummy hashes
                for placeholder in binaries:
                    hashes[placeholder] = "a" * 64
            else:
                return False

        # Read and process template
        template_content = template_path.read_text()

        # Replace placeholders
        replacements = {
            "{{VERSION}}": version,
            "{{MACOS_ARM64_SHA256}}": hashes.get("MACOS_ARM64_SHA256", "a" * 64),
            "{{MACOS_X64_SHA256}}": hashes.get("MACOS_X64_SHA256", "a" * 64),
            "{{LINUX_X64_SHA256}}": hashes.get("LINUX_X64_SHA256", "a" * 64),
        }

        output_content = template_content
        for placeholder, value in replacements.items():
            output_content = output_content.replace(placeholder, value)

        # Validate that all placeholders were replaced
        if "{{" in output_content and "}}" in output_content:
            import re

            remaining = re.findall(r"\{\{[^}]+\}\}", output_content)
            print(f"❌ Unreplaced placeholders: {remaining}")
            return False

        if self.dry_run:
            print("🔍 DRY RUN: Would write the following content:")
            print(f"Target: {output_path}")
            print("Content preview:")
            lines = output_content.split("\n")
            for i, line in enumerate(lines[:10]):
                print(f"  {i + 1:2d}: {line}")
            if len(lines) > 10:
                print(f"  ... ({len(lines) - 10} more lines)")
            return True

        # Write output file
        output_path.write_text(output_content)
        print(f"✅ Updated Homebrew formula: {output_path}")

        # Validate Ruby syntax
        try:
            result = subprocess.run(
                ["ruby", "-c", str(output_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                print(f"❌ Ruby syntax validation failed: {result.stderr}")
                return False
            print("✅ Ruby syntax validation passed")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"⚠️  Could not validate Ruby syntax: {e}")

        return True

    def update_scoop_manifest(self, version: str) -> bool:
        """Update Scoop manifest from template."""
        print(f"🪣 Updating Scoop manifest for version {version}")

        template_path = (
            self.repo_root
            / "submodules/scoop-rxiv-maker/bucket/rxiv-maker.json.template"
        )
        output_path = (
            self.repo_root / "submodules/scoop-rxiv-maker/bucket/rxiv-maker.json"
        )

        if not template_path.exists():
            print(f"❌ Template not found: {template_path}")
            return False

        # Download and hash Windows binary
        url = f"https://github.com/henriqueslab/rxiv-maker/releases/download/{version}/rxiv-maker-windows-x64.zip"

        try:
            hash_value, temp_file = self.download_and_hash(url)
        except Exception as e:
            print(f"❌ Failed to download Windows binary: {e}")
            if self.dry_run:
                print(
                    "🔍 DRY RUN: Would have downloaded binary and calculated checksum"
                )
                # For dry run with test versions, use dummy hash
                hash_value = "a" * 64
            else:
                return False

        # Read and process template
        template_content = template_path.read_text()

        # Replace placeholders
        version_num = version.lstrip("v")
        replacements = {
            "{{VERSION}}": version,
            "{{VERSION_NUM}}": version_num,
            "{{WINDOWS_X64_SHA256}}": hash_value,
        }

        output_content = template_content
        for placeholder, value in replacements.items():
            output_content = output_content.replace(placeholder, value)

        # Validate JSON and placeholders
        try:
            manifest = json.loads(output_content)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON structure: {e}")
            return False

        if "{{" in output_content and "}}" in output_content:
            import re

            remaining = re.findall(r"\{\{[^}]+\}\}", output_content)
            print(f"❌ Unreplaced placeholders: {remaining}")
            return False

        if self.dry_run:
            print("🔍 DRY RUN: Would write the following content:")
            print(f"Target: {output_path}")
            print("Content preview:")
            print(json.dumps(manifest, indent=2)[:500] + "...")
            return True

        # Write output file with proper formatting
        output_path.write_text(json.dumps(manifest, indent=4) + "\n")
        print(f"✅ Updated Scoop manifest: {output_path}")

        return True

    def update_all(self, version: str) -> bool:
        """Update both Homebrew and Scoop packages."""
        print(f"🚀 Updating all package managers for version {version}")

        homebrew_success = self.update_homebrew_formula(version)
        scoop_success = self.update_scoop_manifest(version)

        success = homebrew_success and scoop_success

        if success:
            print(f"✅ All package managers updated successfully for {version}")
        else:
            print("❌ Some package managers failed to update")

        return success


def main():
    """Main function."""
    if len(sys.argv) < 3:
        print(
            "Usage: python update-package-templates.py <command> <version> [--dry-run]"
        )
        print("Commands:")
        print("  homebrew <version> - Update Homebrew formula")
        print("  scoop <version> - Update Scoop manifest")
        print("  all <version> - Update all package managers")
        print("Options:")
        print("  --dry-run - Show what would be done without making changes")
        sys.exit(1)

    command = sys.argv[1]
    version = sys.argv[2]
    dry_run = "--dry-run" in sys.argv

    # Validate version format - allow test versions
    if not version.startswith("v"):
        print(f"❌ Invalid version format: {version} (expected format: v1.2.3)")
        sys.exit(1)

    # Get repository root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")

    with TemplateUpdater(repo_root, dry_run=dry_run) as updater:
        if command == "homebrew":
            success = updater.update_homebrew_formula(version)
        elif command == "scoop":
            success = updater.update_scoop_manifest(version)
        elif command == "all":
            success = updater.update_all(version)
        else:
            print(f"❌ Unknown command: {command}")
            sys.exit(1)

        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
