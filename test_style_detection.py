#!/usr/bin/env python3
"""Test script to reproduce Guillaume's issue with style files."""

import sys
import tempfile
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rxiv_maker.engine.build_manager import BuildManager


def test_style_dir_detection():
    """Test style directory detection in BuildManager."""
    print("Testing style directory detection...")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Set up a manuscript directory
        manuscript_dir = temp_path / "CCT8_paper"
        manuscript_dir.mkdir()
        (manuscript_dir / "01_MAIN.md").write_text("# Test")
        (manuscript_dir / "00_CONFIG.yml").write_text("title: Test")

        output_dir = temp_path / "output"

        # Create BuildManager (this is where style_dir detection happens)
        print(f"Creating BuildManager with manuscript_path: {manuscript_dir}")
        build_manager = BuildManager(
            manuscript_path=str(manuscript_dir), output_dir=str(output_dir), skip_validation=True
        )

        print(f"Detected style_dir: {build_manager.style_dir}")
        if build_manager.style_dir is not None:
            print(f"Style directory exists: {build_manager.style_dir.exists()}")

            if build_manager.style_dir.exists():
                cls_files = list(build_manager.style_dir.glob("*.cls"))
                print(f"Found .cls files: {[f.name for f in cls_files]}")
        else:
            print("Style directory is None")

        # Test the copy_style_files method
        print("\nTesting copy_style_files method...")
        success = build_manager.copy_style_files()
        print(f"copy_style_files returned: {success}")

        # Check what was copied to output directory
        output_dir.mkdir(exist_ok=True)
        style_files_in_output = list(output_dir.glob("*.cls")) + list(output_dir.glob("*.bst"))
        print(f"Style files copied to output: {[f.name for f in style_files_in_output]}")


if __name__ == "__main__":
    test_style_dir_detection()
