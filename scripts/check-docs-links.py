#!/usr/bin/env python3
"""
Documentation Link Checker for Rxiv-Maker Ecosystem

This script checks for broken internal links across rxiv-maker documentation,
helping maintain consistency across repositories.

Usage:
    python scripts/check-docs-links.py
    python scripts/check-docs-links.py --fix-relative-paths
    python scripts/check-docs-links.py --verbose

Features:
- Checks internal markdown links within the repository
- Validates cross-repository links (when possible)
- Detects common documentation inconsistencies
- Can fix common issues automatically
"""

import argparse
import re
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Dict, List, Tuple


class DocumentationLinkChecker:
    """Check and validate documentation links across the rxiv-maker ecosystem."""

    def __init__(self, base_path: str = None, verbose: bool = False):
        self.base_path = Path(base_path or ".")
        self.verbose = verbose
        self.docs_path = self.base_path / "docs"

        # Known external repositories in the ecosystem
        self.ecosystem_repos = {
            "main": "https://github.com/HenriquesLab/rxiv-maker",
            "website": "https://rxiv-maker.henriqueslab.org",
            "vscode": "https://github.com/HenriquesLab/vscode-rxiv-maker",
            "docker": "https://github.com/HenriquesLab/docker-rxiv-maker",
        }

        # Common documentation patterns
        self.link_patterns = [
            r"\[([^\]]+)\]\(([^)]+)\)",  # [text](url)
            r"\[([^\]]+)\]:\s*(\S+)",  # [text]: url
        ]

        self.issues = []
        self.processed_files = set()

    def log(self, message: str, level: str = "INFO"):
        """Log message with level."""
        if self.verbose or level in ["ERROR", "WARNING"]:
            print(f"[{level}] {message}")

    def find_markdown_files(self) -> List[Path]:
        """Find all markdown files in the repository."""
        markdown_files = []

        # Search in docs/ directory and root
        search_paths = [self.docs_path, self.base_path]

        for search_path in search_paths:
            if search_path.exists():
                markdown_files.extend(search_path.rglob("*.md"))

        # Also check README files specifically
        for readme_name in ["README.md", "CONTRIBUTING.md", "CHANGELOG.md"]:
            readme_path = self.base_path / readme_name
            if readme_path.exists() and readme_path not in markdown_files:
                markdown_files.append(readme_path)

        return sorted(set(markdown_files))

    def extract_links(self, content: str) -> List[Tuple[str, str]]:
        """Extract all markdown links from content."""
        links = []

        for pattern in self.link_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                text, url = match.groups()
                links.append((text.strip(), url.strip()))

        return links

    def is_external_url(self, url: str) -> bool:
        """Check if URL is external (http/https)."""
        return url.startswith(("http://", "https://"))

    def is_anchor_link(self, url: str) -> bool:
        """Check if URL is an anchor link."""
        return url.startswith("#")

    def resolve_relative_path(self, current_file: Path, relative_path: str) -> Path:
        """Resolve relative path from current file location."""
        if relative_path.startswith("/"):
            # Absolute path from repository root
            return self.base_path / relative_path.lstrip("/")
        else:
            # Relative path from current file
            return (current_file.parent / relative_path).resolve()

    def check_internal_link(self, current_file: Path, link_text: str, url: str) -> List[str]:
        """Check if an internal link is valid."""
        issues = []

        # Skip anchors and external links
        if self.is_anchor_link(url) or self.is_external_url(url):
            return issues

        # Parse URL to separate path and anchor
        parsed = urllib.parse.urlparse(url)
        file_path = parsed.path
        anchor = parsed.fragment

        # Resolve the target file path
        try:
            target_path = self.resolve_relative_path(current_file, file_path)

            # Check if target file exists
            if not target_path.exists():
                issues.append(f"Broken link: '{link_text}' -> '{url}' (file not found: {target_path})")
                return issues

            # If there's an anchor, check if it exists (basic check)
            if anchor and target_path.suffix == ".md":
                try:
                    with open(target_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Look for anchor in headers or explicit anchors
                    anchor_patterns = [
                        f"#{anchor}",  # Explicit anchor
                        f"# {anchor.replace('-', ' ')}",  # Header converted to anchor
                        f"## {anchor.replace('-', ' ')}",  # Subheader
                        f"### {anchor.replace('-', ' ')}",  # Sub-subheader
                    ]

                    found_anchor = any(pattern.lower() in content.lower() for pattern in anchor_patterns)
                    if not found_anchor:
                        issues.append(f"Broken anchor: '{link_text}' -> '{url}' (anchor '#{anchor}' not found)")

                except Exception as e:
                    self.log(f"Could not check anchor in {target_path}: {e}", "WARNING")

        except Exception as e:
            issues.append(f"Error resolving link: '{link_text}' -> '{url}' ({e})")

        return issues

    def check_ecosystem_links(self, link_text: str, url: str) -> List[str]:
        """Check cross-repository ecosystem links."""
        issues = []

        # Check for common broken ecosystem patterns
        if "henriqueslab" in url.lower() and "rxiv-maker" in url.lower():
            # This is likely an ecosystem link - do basic validation
            if "/blob/main/" in url and "/docs/" in url:
                # Check if it matches our expected patterns
                valid_patterns = [
                    "github.com/HenriquesLab/rxiv-maker/blob/main/",
                    "github.com/HenriquesLab/vscode-rxiv-maker/blob/main/",
                    "github.com/HenriquesLab/docker-rxiv-maker/blob/main/",
                    "rxiv-maker.henriqueslab.org/",
                ]

                if not any(pattern in url for pattern in valid_patterns):
                    issues.append(f"Potentially incorrect ecosystem link: '{link_text}' -> '{url}'")

        return issues

    def check_file(self, file_path: Path) -> Dict[str, List[str]]:
        """Check all links in a single file."""
        if file_path in self.processed_files:
            return {}

        self.processed_files.add(file_path)
        file_issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            file_issues.append(f"Could not read file: {e}")
            return {str(file_path): file_issues}

        # Extract and check all links
        links = self.extract_links(content)
        self.log(f"Checking {len(links)} links in {file_path}")

        for link_text, url in links:
            # Check internal links
            internal_issues = self.check_internal_link(file_path, link_text, url)
            file_issues.extend(internal_issues)

            # Check ecosystem links
            if self.is_external_url(url):
                ecosystem_issues = self.check_ecosystem_links(link_text, url)
                file_issues.extend(ecosystem_issues)

        return {str(file_path): file_issues} if file_issues else {}

    def generate_report(self) -> str:
        """Generate a comprehensive report of all issues found."""
        total_issues = sum(len(issues) for issues in self.issues)

        report = []
        report.append("# Documentation Link Check Report")
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total files checked: {len(self.processed_files)}")
        report.append(f"Total issues found: {total_issues}")
        report.append("")

        if total_issues == 0:
            report.append("✅ All documentation links are valid!")
            return "\\n".join(report)

        report.append("## Issues Found")
        report.append("")

        for file_path, issues in self.issues:
            if issues:
                report.append(f"### {file_path}")
                for issue in issues:
                    report.append(f"- {issue}")
                report.append("")

        report.append("## Recommendations")
        report.append("")
        report.append("1. Fix broken internal links by updating paths or creating missing files")
        report.append("2. Verify external links manually or with additional tools")
        report.append("3. Update cross-repository references to use standardized URLs")
        report.append("4. Consider using the navigation.md system for consistent linking")

        return "\\n".join(report)

    def run(self) -> bool:
        """Run the complete link checking process."""
        self.log("Starting documentation link check...")

        markdown_files = self.find_markdown_files()
        self.log(f"Found {len(markdown_files)} markdown files to check")

        total_issues = 0

        for file_path in markdown_files:
            file_results = self.check_file(file_path)
            for filepath, issues in file_results.items():
                if issues:
                    self.issues.append((filepath, issues))
                    total_issues += len(issues)

                    for issue in issues:
                        self.log(f"{filepath}: {issue}", "ERROR")

        # Generate and display report
        report = self.generate_report()

        if total_issues > 0:
            self.log(f"\\n{report}")
            return False
        else:
            self.log("✅ All documentation links are valid!")
            return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check documentation links in rxiv-maker ecosystem")
    parser.add_argument("--base-path", default=".", help="Base path of the repository")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--output", "-o", help="Write report to file")

    args = parser.parse_args()

    checker = DocumentationLinkChecker(args.base_path, args.verbose)
    success = checker.run()

    if args.output:
        report = checker.generate_report()
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report written to {args.output}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
