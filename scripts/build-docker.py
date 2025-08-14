#!/usr/bin/env python3
"""Unified Docker Build Script for Rxiv-Maker.

This script replaces build-accelerated.sh and build-safe.sh with a single,
cross-platform Python solution.

Usage:
    python scripts/build-docker.py [--mode MODE] [--image IMAGE] [OPTIONS]

Examples:
    python scripts/build-docker.py --mode accelerated
    python scripts/build-docker.py --mode safe --max-build-time 3600
    python scripts/build-docker.py --mode balanced --verbose
"""

import argparse
import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rxiv_maker.docker.build_manager import DockerBuildManager, DockerBuildMode


def print_colored(message: str, color: str = "white") -> None:
    """Print colored message to console."""
    colors = {
        "red": "\033[0;31m",
        "green": "\033[0;32m",
        "yellow": "\033[1;33m",
        "blue": "\033[0;34m",
        "white": "\033[0m",
        "reset": "\033[0m",
    }

    color_code = colors.get(color, colors["white"])
    reset_code = colors["reset"]
    print(f"{color_code}{message}{reset_code}")


def print_build_summary(result: dict) -> None:
    """Print build result summary."""
    print("\n" + "=" * 60)
    print_colored("🐳 Docker Build Results", "blue")
    print("=" * 60)

    # Build status
    if result["success"]:
        print_colored("✅ Build Status: SUCCESS", "green")
        print_colored(f"⏱️  Build Time: {result['build_time_formatted']}", "green")
        print_colored(f"📦 Image: {result['image_name']}", "green")

        # Image info
        if result.get("image_info"):
            info = result["image_info"]
            if info.get("size") != "unknown":
                print_colored(f"💾 Size: {info['size']}", "green")
            if info.get("id") != "unknown":
                print_colored(f"🔑 ID: {info['id']}", "green")
    else:
        print_colored("❌ Build Status: FAILED", "red")
        if result.get("error"):
            print_colored(f"❌ Error: {result['error']}", "red")

        if result.get("log_file"):
            print_colored(f"📄 Log: {result['log_file']}", "yellow")

    # Verification
    verification = result.get("verification", {})
    if verification.get("enabled", False):
        if verification.get("success", False):
            print_colored("✅ Verification: PASSED", "green")
        else:
            print_colored(f"❌ Verification: FAILED - {verification.get('message', 'Unknown')}", "red")

    # Mode and prerequisites
    print_colored(f"⚙️  Mode: {result['mode']}", "blue")

    prereqs = result.get("prerequisites", {})
    warnings = prereqs.get("warnings", [])
    if warnings:
        print_colored("⚠️  Warnings:", "yellow")
        for warning in warnings:
            print_colored(f"   - {warning}", "yellow")

    # System resources
    resources = prereqs.get("system_resources", {})
    if resources:
        print_colored("📊 System Resources:", "blue")
        cpu_count = resources.get("cpu_count", "unknown")
        memory_gb = resources.get("memory_gb", "unknown")
        disk_space_gb = resources.get("disk_space_gb", "unknown")

        print(f"   CPU Cores: {cpu_count}")
        print(f"   Memory: {memory_gb:.1f}GB" if isinstance(memory_gb, (int, float)) else f"   Memory: {memory_gb}")
        if isinstance(disk_space_gb, (int, float)):
            print(f"   Disk Space: {disk_space_gb:.1f}GB")

    print("=" * 60)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Unified Docker Build Script for Rxiv-Maker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Build Modes:
  accelerated  - Speed-optimized build with aggressive caching and BuildKit
  safe         - Resource-aware build with monitoring and graceful error handling
  balanced     - Moderate caching and safety features (default)

Examples:
  %(prog)s --mode accelerated
  %(prog)s --mode safe --max-build-time 3600 --verbose
  %(prog)s --image myuser/rxiv-maker:custom --dockerfile docker/Dockerfile
        """,
    )

    # Build configuration
    parser.add_argument(
        "--mode",
        choices=[DockerBuildMode.ACCELERATED, DockerBuildMode.SAFE, DockerBuildMode.BALANCED],
        default=DockerBuildMode.BALANCED,
        help="Build mode (default: balanced)",
    )

    parser.add_argument(
        "--image",
        default="henriqueslab/rxiv-maker-base:latest",
        help="Docker image name and tag (default: henriqueslab/rxiv-maker-base:latest)",
    )

    parser.add_argument("--dockerfile", type=Path, help="Path to Dockerfile (auto-detected if not specified)")

    parser.add_argument(
        "--context", type=Path, default=Path.cwd(), help="Build context directory (default: current directory)"
    )

    # Build options
    parser.add_argument(
        "--max-build-time", type=int, default=7200, help="Maximum build time in seconds (default: 7200)"
    )

    parser.add_argument("--no-proxy", action="store_false", dest="use_proxy", help="Disable squid-deb-proxy usage")

    parser.add_argument("--no-buildkit", action="store_false", dest="use_buildkit", help="Disable Docker BuildKit")

    parser.add_argument(
        "--no-verification", action="store_false", dest="enable_verification", help="Skip build verification"
    )

    parser.add_argument(
        "--no-cleanup", action="store_false", dest="cleanup_on_success", help="Keep temporary files on success"
    )

    # Output options
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output (overrides --verbose)")

    # Check mode
    parser.add_argument("--check", action="store_true", help="Check prerequisites only (don't build)")

    args = parser.parse_args()

    # Handle quiet mode
    if args.quiet:
        args.verbose = False

    # Print header
    if not args.quiet:
        print_colored("🚀 Rxiv-Maker Docker Build Manager", "blue")
        print_colored("=" * 40, "blue")
        print(f"Mode: {args.mode}")
        print(f"Image: {args.image}")
        if args.dockerfile:
            print(f"Dockerfile: {args.dockerfile}")
        print(f"Context: {args.context}")
        print()

    try:
        # Create build manager
        manager = DockerBuildManager(
            mode=args.mode,
            image_name=args.image,
            dockerfile_path=args.dockerfile,
            build_context=args.context,
            max_build_time=args.max_build_time,
            use_proxy=args.use_proxy,
            use_buildkit=args.use_buildkit,
            enable_verification=args.enable_verification,
            cleanup_on_success=args.cleanup_on_success,
            verbose=args.verbose,
        )

        # Check prerequisites
        if args.check:
            prereqs = manager.check_prerequisites()

            print_colored("🔍 Prerequisites Check", "blue")
            print("-" * 30)

            checks = [
                ("Docker Available", prereqs["docker_available"]),
                ("BuildKit Available", prereqs["buildkit_available"]),
                ("Dockerfile Exists", prereqs["dockerfile_exists"]),
                ("Sufficient Disk Space", prereqs["disk_space_sufficient"]),
            ]

            if args.use_proxy:
                checks.append(("Proxy Available", prereqs["proxy_available"]))

            for check_name, status in checks:
                if status:
                    print_colored(f"✅ {check_name}", "green")
                else:
                    print_colored(f"❌ {check_name}", "red")

            if prereqs["warnings"]:
                print_colored("\n⚠️  Warnings:", "yellow")
                for warning in prereqs["warnings"]:
                    print_colored(f"   - {warning}", "yellow")

            if prereqs["errors"]:
                print_colored("\n❌ Errors:", "red")
                for error in prereqs["errors"]:
                    print_colored(f"   - {error}", "red")
                return 1

            print_colored("\n✅ Prerequisites check passed!", "green")
            return 0

        # Execute build
        if not args.quiet:
            print_colored("🏗️  Starting Docker build...", "blue")

        result = manager.build()

        # Print results
        if not args.quiet:
            print_build_summary(result)
        elif not result["success"]:
            # Even in quiet mode, show errors
            print_colored(f"❌ Build failed: {result.get('error', 'Unknown error')}", "red")

        # Return appropriate exit code
        return 0 if result["success"] else 1

    except KeyboardInterrupt:
        print_colored("\n❌ Build interrupted by user", "red")
        return 130
    except Exception as e:
        print_colored(f"❌ Unexpected error: {e}", "red")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
