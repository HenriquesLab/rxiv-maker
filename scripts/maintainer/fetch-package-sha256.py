#!/usr/bin/env python3
"""SHA256 Fetcher for Package Managers.

This script fetches SHA256 hashes for rxiv-maker packages from PyPI
for use in package manager manifests (Homebrew, Scoop, etc.).

Usage:
    python fetch-package-sha256.py <version> [--package-type=<type>]

Examples:
    python fetch-package-sha256.py 1.4.8
    python fetch-package-sha256.py 1.4.8 --package-type=sdist
    python fetch-package-sha256.py 1.4.8 --package-type=wheel
"""

import json
import sys
import urllib.error
import urllib.request


def fetch_pypi_data(package_name: str, version: str) -> dict:
    """Fetch package data from PyPI API."""
    url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        with urllib.request.urlopen(url) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"Error: Failed to fetch data from PyPI: HTTP {e.code}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: Network error: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON response from PyPI", file=sys.stderr)
        sys.exit(1)


def find_package_files(
    data: dict, version: str, package_type: str | None = None
) -> list[dict]:
    """Find package files of specified type."""
    releases = data.get("releases", {})
    version_files = releases.get(version, [])

    if not version_files:
        print(f"Error: No files found for version {version}", file=sys.stderr)
        sys.exit(1)

    if package_type:
        # Handle wheel -> bdist_wheel mapping
        search_type = "bdist_wheel" if package_type == "wheel" else package_type
        filtered_files = [
            f for f in version_files if f.get("packagetype") == search_type
        ]
        if not filtered_files:
            available_types = list(
                {f.get("packagetype", "unknown") for f in version_files}
            )
            print(
                f"Error: No {package_type} files found for version {version}",
                file=sys.stderr,
            )
            print(f"Available types: {', '.join(available_types)}", file=sys.stderr)
            sys.exit(1)
        return filtered_files

    return version_files


def get_sha256_hash(package_files: list[dict], preferred_type: str = "sdist") -> str:
    """Get SHA256 hash, preferring sdist over wheel."""
    # Handle wheel -> bdist_wheel mapping for preferred type
    search_preferred = "bdist_wheel" if preferred_type == "wheel" else preferred_type

    # First try to find preferred type
    for file_info in package_files:
        if file_info.get("packagetype") == search_preferred:
            sha256 = file_info.get("digests", {}).get("sha256")
            if sha256:
                return sha256

    # Fall back to any available file
    for file_info in package_files:
        sha256 = file_info.get("digests", {}).get("sha256")
        if sha256:
            return sha256

    print("Error: No SHA256 hash found in any package file", file=sys.stderr)
    sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(
            "Usage: python fetch-package-sha256.py <version> [--package-type=<type>]",
            file=sys.stderr,
        )
        print("", file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  python fetch-package-sha256.py 1.4.8", file=sys.stderr)
        print(
            "  python fetch-package-sha256.py 1.4.8 --package-type=sdist",
            file=sys.stderr,
        )
        print(
            "  python fetch-package-sha256.py 1.4.8 --package-type=wheel",
            file=sys.stderr,
        )
        sys.exit(1)

    version = sys.argv[1]
    package_type = None

    # Parse package type argument
    for arg in sys.argv[2:]:
        if arg.startswith("--package-type="):
            package_type = arg.split("=", 1)[1]

    package_name = "rxiv-maker"

    try:
        # Fetch data from PyPI
        data = fetch_pypi_data(package_name, version)

        # Find package files
        package_files = find_package_files(data, version, package_type)

        # Get SHA256 hash
        sha256 = get_sha256_hash(package_files, package_type or "sdist")

        # Output only the hash (for shell script consumption)
        print(sha256)

    except KeyboardInterrupt:
        print("Error: Interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
