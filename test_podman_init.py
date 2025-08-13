#!/usr/bin/env python3
"""Quick test to verify Podman init functionality works correctly."""

import subprocess
from pathlib import Path


def test_podman_init():
    """Test that rxiv init works with Podman and creates directories correctly."""
    # Start Podman container
    print("🐳 Starting Podman container...")
    result = subprocess.run(
        [
            "podman",
            "run",
            "-d",
            "--rm",
            "-v",
            f"{Path.cwd()}:/workspace",
            "-w",
            "/workspace",
            "henriqueslab/rxiv-maker-base:latest",
            "sleep",
            "infinity",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    container_id = result.stdout.strip()
    print(f"🚀 Started container: {container_id[:12]}")

    try:
        # Install rxiv-maker in container
        print("📦 Installing rxiv-maker...")
        subprocess.run(["podman", "exec", container_id, "pip", "install", "-e", "/workspace"], check=True)

        # Test init command
        print("🧪 Testing rxiv init command...")
        init_result = subprocess.run(
            [
                "podman",
                "exec",
                container_id,
                "rxiv",
                "init",
                "/workspace/TEST_MANUSCRIPT",
                "--template",
                "basic",
                "--no-interactive",
                "--force",
            ],
            capture_output=True,
            text=True,
        )

        print("Init stdout:", init_result.stdout)
        print("Init stderr:", init_result.stderr)
        print("Init return code:", init_result.returncode)

        # Check if directory was created on host
        test_dir = Path.cwd() / "TEST_MANUSCRIPT"
        print(f"📁 Checking if directory exists: {test_dir}")
        print(f"Directory exists: {test_dir.exists()}")

        if test_dir.exists():
            print("✅ SUCCESS: Directory created correctly!")
            required_files = ["00_CONFIG.yml", "01_MAIN.md", "03_REFERENCES.bib"]
            for filename in required_files:
                file_path = test_dir / filename
                print(f"  - {filename}: {'✅' if file_path.exists() else '❌'}")
        else:
            print("❌ FAILURE: Directory not created!")

    finally:
        # Clean up
        print("🧹 Cleaning up...")
        subprocess.run(["podman", "stop", container_id], check=False)

        # Remove test directory
        test_dir = Path.cwd() / "TEST_MANUSCRIPT"
        if test_dir.exists():
            import shutil

            shutil.rmtree(test_dir)
            print("🗑️  Removed test directory")


if __name__ == "__main__":
    test_podman_init()
