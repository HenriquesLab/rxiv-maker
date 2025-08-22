#!/usr/bin/env python3
"""
Docker Builder Script - Migration Notice

This script is a temporary placeholder following the Docker infrastructure migration
to a separate repository. The original Docker build functionality has been moved
as part of PR #124.

This placeholder ensures CI/CD workflows continue to function while the migration
is being completed.
"""

import argparse
import sys


def main():
    """Main entry point for the docker builder."""
    parser = argparse.ArgumentParser(description="Docker builder (migration placeholder)")
    parser.add_argument("--platforms", default="linux/amd64,linux/arm64", help="Platforms to build for")
    parser.add_argument("--push", action="store_true", help="Push to registry")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    print("🐳 Docker Builder - Migration Notice")
    print("=" * 50)
    print("Docker infrastructure has been migrated to a separate repository.")
    print("This is a temporary placeholder to maintain CI/CD functionality.")
    print("")
    print(f"Requested platforms: {args.platforms}")
    print(f"Push to registry: {args.push}")
    print(f"Debug mode: {args.debug}")
    print("")
    print("✅ Migration placeholder completed successfully")
    print("Note: Actual Docker builds are now handled by the separate Docker repository")

    return 0


if __name__ == "__main__":
    sys.exit(main())
