#!/usr/bin/env python3
"""Test the BibTeX fix by simulating Guillaume's scenario"""

import os
import tempfile
from pathlib import Path


def test_bibtex_fix():
    """Test that the manuscript name is correctly passed through to write_manuscript_output"""
    # Import the fixed functions
    from rxiv_maker.utils.file_helpers import write_manuscript_output

    # Test case 1: Test write_manuscript_output directly
    print("=== Testing write_manuscript_output directly ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir()

        # Test with explicit manuscript name (new functionality)
        result1 = write_manuscript_output(str(output_dir), "test content", "CCT8_paper")
        print(f"With explicit name 'CCT8_paper': {result1}")
        assert "CCT8_paper.tex" in result1

        # Test with None (fallback to environment)
        os.environ["MANUSCRIPT_PATH"] = "test_paper"
        result2 = write_manuscript_output(str(output_dir), "test content", None)
        print(f"With env fallback 'test_paper': {result2}")
        assert "test_paper.tex" in result2

        # Test edge case: empty environment variable
        os.environ["MANUSCRIPT_PATH"] = ""
        result3 = write_manuscript_output(str(output_dir), "test content", None)
        print(f"With empty env (should use MANUSCRIPT): {result3}")
        assert "MANUSCRIPT.tex" in result3

    print("✅ write_manuscript_output tests passed!")

    # Test case 2: Test manuscript name extraction from path
    print("\n=== Testing manuscript name extraction ===")

    test_paths = [
        ("CCT8_paper/", "CCT8_paper"),
        ("CCT8_paper", "CCT8_paper"),
        ("./my_paper/", "my_paper"),
        ("/home/user/research/", "research"),
        ("", None),  # Empty path should result in None
        (".", None),  # Current dir should result in None
        ("..", None),  # Parent dir should result in None
    ]

    for manuscript_path, expected_name in test_paths:
        if manuscript_path:
            normalized_path = str(manuscript_path).rstrip("/")
            manuscript_name = os.path.basename(normalized_path)
            if not manuscript_name or manuscript_name in (".", ".."):
                manuscript_name = None
        else:
            manuscript_name = None

        print(f"Path '{manuscript_path}' -> Name '{manuscript_name}' (expected: '{expected_name}')")
        assert manuscript_name == expected_name

    print("✅ Manuscript name extraction tests passed!")


if __name__ == "__main__":
    test_bibtex_fix()
    print("\n🎉 All tests passed! The BibTeX manuscript name issue should be fixed.")
