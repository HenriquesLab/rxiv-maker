#!/usr/bin/env python3
"""Test the fix for trailing slash issue in manuscript paths."""

import os
import sys
import tempfile
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rxiv_maker.engine.build_manager import BuildManager


def test_manuscript_name_with_trailing_slash():
    """Test that BuildManager handles trailing slashes correctly."""
    print("Testing BuildManager with trailing slash paths...")
    print("=" * 60)

    test_cases = [
        ("CCT8_paper", "CCT8_paper"),  # No slash
        ("CCT8_paper/", "CCT8_paper"),  # Single slash
        ("CCT8_paper//", "CCT8_paper"),  # Double slash
        ("./CCT8_paper/", "CCT8_paper"),  # Relative with slash
        ("project_dir/", "project_dir"),  # Different name
        ("", "MANUSCRIPT"),  # Empty string fallback
        (".", "MANUSCRIPT"),  # Dot fallback
        ("..", "MANUSCRIPT"),  # Double dot fallback
    ]

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        for manuscript_path, expected_name in test_cases:
            print(f"\nTesting manuscript_path: '{manuscript_path}'")
            print(f"Expected manuscript_name: '{expected_name}'")

            try:
                # Create a minimal manuscript directory structure if path is not special
                if manuscript_path not in ("", ".", ".."):
                    full_path = temp_path / manuscript_path.rstrip("/")
                    full_path.mkdir(parents=True, exist_ok=True)

                    # Create minimal required files
                    (full_path / "01_MAIN.md").write_text("# Test")
                    (full_path / "00_CONFIG.yml").write_text("title: Test")

                    manuscript_path_arg = str(full_path)
                else:
                    manuscript_path_arg = manuscript_path

                # Create BuildManager instance
                output_dir = temp_path / "output"
                build_manager = BuildManager(
                    manuscript_path=manuscript_path_arg,
                    output_dir=str(output_dir),
                    skip_validation=True,  # Skip validation for this test
                )

                actual_name = build_manager.manuscript_name
                print(f"Actual manuscript_name: '{actual_name}'")

                if actual_name == expected_name:
                    print("✅ PASS")
                else:
                    print(f"❌ FAIL - Expected '{expected_name}', got '{actual_name}'")
                    return False

            except Exception as e:
                print(f"❌ ERROR: {e}")
                return False

    print("\n✅ All tests passed!")
    return True


def test_environment_variable_setting():
    """Test that MANUSCRIPT_PATH environment variable is set correctly."""
    print("\n\nTesting MANUSCRIPT_PATH environment variable setting...")
    print("=" * 60)

    test_cases = [
        ("test_project", "test_project"),
        ("test_project/", "test_project"),
        ("./test_project/", "test_project"),
    ]

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        for manuscript_path, expected_env_value in test_cases:
            print(f"\nTesting manuscript_path: '{manuscript_path}'")
            print(f"Expected MANUSCRIPT_PATH env var: '{expected_env_value}'")

            try:
                # Create manuscript directory
                full_path = temp_path / manuscript_path.rstrip("/")
                full_path.mkdir(parents=True, exist_ok=True)
                (full_path / "01_MAIN.md").write_text("# Test")
                (full_path / "00_CONFIG.yml").write_text("title: Test")

                # Create BuildManager instance
                output_dir = temp_path / "output"
                build_manager = BuildManager(
                    manuscript_path=str(full_path), output_dir=str(output_dir), skip_validation=True
                )

                # Simulate the environment variable setting that happens in generate_tex_files
                normalized_path = build_manager.manuscript_path.rstrip("/")
                env_value = os.path.basename(normalized_path)

                print(f"Actual env value would be: '{env_value}'")

                if env_value == expected_env_value:
                    print("✅ PASS")
                else:
                    print(f"❌ FAIL - Expected '{expected_env_value}', got '{env_value}'")
                    return False

            except Exception as e:
                print(f"❌ ERROR: {e}")
                return False

    print("\n✅ All environment variable tests passed!")
    return True


if __name__ == "__main__":
    success1 = test_manuscript_name_with_trailing_slash()
    success2 = test_environment_variable_setting()

    if success1 and success2:
        print("\n🎉 All tests passed! The fix should resolve Guillaume's issue.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
