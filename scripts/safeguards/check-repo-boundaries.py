#!/usr/bin/env python3
"""Repository Boundary Validator for Rxiv-Maker

This script performs deep validation of repository boundaries to prevent
content contamination between the main repository and its submodules.
"""

import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check"""

    passed: bool
    message: str
    details: str | None = None


class RepositoryBoundaryValidator:
    """Validates repository boundaries and prevents content contamination"""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root.resolve()
        self.submodules_dir = self.repo_root / "submodules"
        self.errors: list[ValidationResult] = []
        self.warnings: list[ValidationResult] = []

        # Define expected file patterns for each repository type
        self.repository_signatures = {
            "main": {
                "required": ["pyproject.toml", "Makefile", "src/rxiv_maker"],
                "forbidden": ["Formula/", "bucket/", "src/extension.ts"],
                "file_types": {".py", ".md", ".yml", ".yaml", ".toml", ".txt", ".sh"},
            },
            "homebrew": {
                "required": ["Formula/rxiv-maker.rb"],
                "forbidden": ["pyproject.toml", "src/rxiv_maker/", "package.json"],
                "file_types": {".rb", ".md", ".sh", ".yml"},
            },
            "scoop": {
                "required": ["bucket/rxiv-maker.json"],
                "forbidden": ["pyproject.toml", "src/rxiv_maker/", "package.json"],
                "file_types": {".json", ".ps1", ".md", ".yml"},
            },
            "vscode": {
                "required": ["package.json", "src/extension.ts"],
                "forbidden": [
                    "pyproject.toml",
                    "src/rxiv_maker/",
                    "Formula/",
                    "bucket/",
                ],
                "file_types": {".ts", ".js", ".json", ".md", ".mjs"},
            },
        }

    def add_error(self, message: str, details: str | None = None, fix_suggestion: str | None = None):
        """Add a validation error"""
        self.errors.append(ValidationResult(False, message, details))
        logger.error(message)
        if details:
            logger.error(f"  Details: {details}")
        if fix_suggestion:
            logger.error(f"  Fix: {fix_suggestion}")

    def add_warning(self, message: str, details: str | None = None, fix_suggestion: str | None = None):
        """Add a validation warning"""
        self.warnings.append(ValidationResult(False, message, details))
        logger.warning(message)
        if details:
            logger.warning(f"  Details: {details}")
        if fix_suggestion:
            logger.warning(f"  Suggestion: {fix_suggestion}")

    def validate_vscode_package_json(self, package_json_path: Path) -> bool:
        """Validate that package.json is actually a VSCode extension"""
        try:
            with open(package_json_path) as f:
                data = json.load(f)

            # Check for VSCode extension markers
            required_fields = ["name", "displayName", "description", "engines"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                self.add_error(
                    f"VSCode package.json missing required fields: {missing_fields}",
                    f"File: {package_json_path}",
                    f"Add missing fields to package.json: {', '.join(missing_fields)}"
                )
                return False

            # Check for VSCode engine requirement
            engines = data.get("engines", {})
            if "vscode" not in engines:
                self.add_error(
                    "VSCode package.json missing 'vscode' engine requirement",
                    f"File: {package_json_path}",
                    'Add "engines": {"vscode": "^1.x.x"} to package.json'
                )
                return False

            # Check for VSCode-specific fields
            vscode_fields = ["activationEvents", "contributes", "main"]
            if not any(field in data for field in vscode_fields):
                self.add_error(
                    "VSCode package.json missing VSCode-specific configuration",
                    f"File: {package_json_path}, Expected one of: {vscode_fields}",
                    f"Add at least one of these fields: {', '.join(vscode_fields)}"
                )
                return False

            return True

        except json.JSONDecodeError as e:
            self.add_error(
                f"Invalid JSON in package.json: {e}", 
                str(package_json_path),
                "Fix JSON syntax errors using a JSON validator or linter"
            )
            return False
        except Exception as e:
            self.add_error(
                f"Error reading package.json: {e}", 
                str(package_json_path),
                "Ensure package.json file exists and is readable"
            )
            return False

    def validate_submodule_content(self, submodule_path: Path, repo_type: str) -> bool:
        """Validate content of a specific submodule"""
        signature = self.repository_signatures.get(repo_type)
        if not signature:
            self.add_error(
                f"Unknown repository type: {repo_type}",
                fix_suggestion="Check repository type configuration in validation script"
            )
            return False

        logger.info(f"Validating {repo_type} submodule: {submodule_path.name}")

        # Check required files/directories exist
        for required in signature["required"]:
            required_path = submodule_path / required
            if not required_path.exists():
                self.add_error(
                    f"{repo_type.title()} submodule missing required file/directory: {required}",
                    f"Path: {required_path}",
                    f"Run 'git submodule update --init --recursive' to restore proper content for {submodule_path.name}"
                )
                return False

        # Check forbidden files/directories don't exist
        for forbidden in signature["forbidden"]:
            forbidden_path = submodule_path / forbidden
            if forbidden_path.exists():
                self.add_error(
                    f"{repo_type.title()} submodule contains forbidden file/directory: {forbidden}",
                    f"Path: {forbidden_path} (indicates content contamination)",
                    f"Remove contamination: cd {submodule_path.name} && git rm -r {forbidden} && git commit -m 'Remove contamination'"
                )
                return False

        # Special validation for VSCode extension
        if repo_type == "vscode":
            package_json = submodule_path / "package.json"
            if package_json.exists():
                if not self.validate_vscode_package_json(package_json):
                    return False

        # Check file types are appropriate
        all_files = list(submodule_path.rglob("*"))
        inappropriate_files = []

        for file_path in all_files:
            if file_path.is_file() and not file_path.name.startswith("."):
                suffix = file_path.suffix.lower()
                if suffix and suffix not in signature["file_types"]:
                    # Allow some common files in any repo
                    common_files = {
                        ".md",
                        ".txt",
                        ".yml",
                        ".yaml",
                        ".json",
                        ".gitignore",
                    }
                    if suffix not in common_files:
                        inappropriate_files.append(
                            str(file_path.relative_to(submodule_path))
                        )

        if inappropriate_files:
            self.add_warning(
                f"{repo_type.title()} submodule contains unexpected file types",
                f"Files: {inappropriate_files[:5]}{'...' if len(inappropriate_files) > 5 else ''}",
            )

        return True

    def validate_main_repository(self) -> bool:
        """Validate main repository doesn't contain submodule content"""
        logger.info("Validating main repository boundaries")

        # Check that main repo has required structure
        signature = self.repository_signatures["main"]
        for required in signature["required"]:
            required_path = self.repo_root / required
            if not required_path.exists():
                self.add_error(
                    f"Main repository missing required file/directory: {required}",
                    f"Path: {required_path}",
                    f"Restore missing file/directory: {required}. Check if you're in the correct repository root."
                )
                return False

        # Check for contamination from submodules (excluding submodules directory)
        contamination_patterns = [
            ("Formula/*.rb", "Homebrew"),
            ("bucket/*.json", "Scoop"),
            ("src/extension.ts", "VSCode"),
            ("*.tmLanguage.json", "VSCode"),
            (".vscodeignore", "VSCode"),
        ]

        for pattern, source in contamination_patterns:
            matches = list(self.repo_root.glob(pattern))
            # Filter out matches in submodules directory
            matches = [
                m for m in matches if not str(m).startswith(str(self.submodules_dir))
            ]

            if matches:
                files_list = [str(m.relative_to(self.repo_root)) for m in matches[:3]]
                self.add_error(
                    f"Main repository contaminated with {source} files: {pattern}",
                    f"Files: {files_list}",
                    f"Remove {source} files: git rm {' '.join(files_list)} && git commit -m 'Remove {source} contamination'"
                )

        return len(self.errors) == 0

    def validate_submodules(self) -> bool:
        """Validate all submodules"""
        if not self.submodules_dir.exists():
            self.add_error(
                "Submodules directory doesn't exist",
                fix_suggestion="Initialize submodules with 'git submodule init && git submodule update'"
            )
            return False

        # Define expected submodules and their types
        expected_submodules = {
            "homebrew-rxiv-maker": "homebrew",
            "scoop-rxiv-maker": "scoop",
            "vscode-rxiv-maker": "vscode",
        }

        for submodule_name, repo_type in expected_submodules.items():
            submodule_path = self.submodules_dir / submodule_name

            if not submodule_path.exists():
                self.add_warning(
                    f"Expected submodule not found: {submodule_name}",
                    fix_suggestion=f"Initialize submodule: git submodule update --init {submodule_path}"
                )
                continue

            if not self.validate_submodule_content(submodule_path, repo_type):
                return False

        # Check for unexpected submodules
        actual_submodules = {
            p.name for p in self.submodules_dir.iterdir() if p.is_dir()
        }
        unexpected = actual_submodules - set(expected_submodules.keys())

        if unexpected:
            self.add_warning(
                f"Unexpected submodules found: {list(unexpected)}",
                fix_suggestion="Review if these submodules are needed or should be removed"
            )

        return True

    def validate_gitmodules(self) -> bool:
        """Validate .gitmodules configuration"""
        gitmodules_path = self.repo_root / ".gitmodules"

        if not gitmodules_path.exists():
            self.add_error(
                ".gitmodules file not found",
                fix_suggestion="Restore .gitmodules from git history or initialize submodules properly"
            )
            return False

        # Expected URLs - note the case differences
        expected_urls = {
            "submodules/homebrew-rxiv-maker": "https://github.com/henriqueslab/homebrew-rxiv-maker.git",
            "submodules/scoop-rxiv-maker": "https://github.com/henriqueslab/scoop-rxiv-maker.git",
            "submodules/vscode-rxiv-maker": "https://github.com/HenriquesLab/vscode-rxiv-maker.git",
        }

        try:
            with open(gitmodules_path) as f:
                content = f.read()

            for path, expected_url in expected_urls.items():
                if f"path = {path}" not in content:
                    self.add_error(
                        f"Missing submodule path in .gitmodules: {path}",
                        fix_suggestion=f"Add submodule: git submodule add {expected_url} {path}"
                    )
                    continue

                if f"url = {expected_url}" not in content:
                    self.add_error(
                        f"Incorrect URL in .gitmodules for {path}",
                        f"Expected: {expected_url}",
                        f"Fix URL: git config -f .gitmodules submodule.{path}.url {expected_url} && git submodule sync -- {path}"
                    )

        except Exception as e:
            self.add_error(
                f"Error reading .gitmodules: {e}",
                fix_suggestion="Ensure .gitmodules file exists and is readable"
            )
            return False

        return len(self.errors) == 0

    def run_validation(self) -> bool:
        """Run all validation checks"""
        logger.info(f"Starting repository boundary validation in: {self.repo_root}")

        # Run all validations
        validations = [
            ("Main repository", self.validate_main_repository),
            ("Submodules", self.validate_submodules),
            (".gitmodules", self.validate_gitmodules),
        ]

        success = True
        for name, validator in validations:
            logger.info(f"Validating {name}...")
            if not validator():
                success = False

        # Print summary
        print("\n" + "=" * 60)
        if success and not self.errors:
            print("✅ All repository boundary validations PASSED!")
            if self.warnings:
                print(f"⚠️  Found {len(self.warnings)} warnings (non-critical)")
        else:
            print("❌ Repository boundary validation FAILED!")
            print(f"   Errors: {len(self.errors)}")
            print(f"   Warnings: {len(self.warnings)}")
            print("\nThis indicates potential repository contamination.")
            print("Please review and fix the issues above before proceeding.")

        return success and not self.errors


def main():
    """Main entry point"""
    repo_root = Path(__file__).parent.parent.parent
    validator = RepositoryBoundaryValidator(repo_root)

    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
