#!/usr/bin/env python3
"""Test script to reproduce the trailing slash issue in rxiv-maker."""

import os
from pathlib import Path


def test_path_handling():
    """Test how path handling works with trailing slashes."""
    # Test cases that Guillaume might encounter
    test_paths = [
        "CCT8_paper",  # No trailing slash
        "CCT8_paper/",  # With trailing slash (Guillaume's case)
        "CCT8_paper//",  # Multiple trailing slashes
        "./CCT8_paper/",  # Relative path with trailing slash
    ]

    print("Testing path handling for manuscript names:")
    print("=" * 60)

    for path in test_paths:
        print(f"\nTesting path: '{path}'")

        # Current implementation logic from build_manager.py
        manuscript_name_path = Path(path).name
        manuscript_name_basename = os.path.basename(path)

        print(f"  Path('{path}').name = '{manuscript_name_path}'")
        print(f"  os.path.basename('{path}') = '{manuscript_name_basename}'")

        # Test the validation logic from write_manuscript_output
        if not manuscript_name_basename or manuscript_name_basename in (".", ".."):
            result = "MANUSCRIPT"
            print(f"  Result after validation: '{result}' (PROBLEM!)")
        else:
            result = manuscript_name_basename
            print(f"  Result after validation: '{result}' (OK)")


def test_fix():
    """Test the proposed fix using rstrip."""
    test_paths = [
        "CCT8_paper",
        "CCT8_paper/",
        "CCT8_paper//",
        "./CCT8_paper/",
    ]

    print("\n\nTesting proposed fix (using rstrip):")
    print("=" * 60)

    for path in test_paths:
        print(f"\nTesting path: '{path}'")

        # Proposed fix: strip trailing slashes before processing
        normalized_path = path.rstrip("/")
        manuscript_name = os.path.basename(normalized_path)

        print(f"  normalized_path = '{normalized_path}'")
        print(f"  os.path.basename(normalized_path) = '{manuscript_name}'")

        # Test the validation logic
        if not manuscript_name or manuscript_name in (".", ".."):
            result = "MANUSCRIPT"
            print(f"  Result after validation: '{result}' (PROBLEM!)")
        else:
            result = manuscript_name
            print(f"  Result after validation: '{result}' (OK)")


if __name__ == "__main__":
    test_path_handling()
    test_fix()
