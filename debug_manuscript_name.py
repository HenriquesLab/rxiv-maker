#!/usr/bin/env python3
"""Test script to reproduce the manuscript name issue"""

import os
from pathlib import Path


def test_manuscript_name_detection():
    """Test the manuscript name detection logic"""

    # Test case 1: Guillaume's scenario
    manuscript_path = "CCT8_paper/"
    print(f"=== Testing manuscript_path: {manuscript_path!r} ===")

    # BuildManager logic
    normalized_path = manuscript_path.rstrip("/")
    manuscript_name = os.path.basename(normalized_path)
    print(f"BuildManager normalized_path: {normalized_path!r}")
    print(f"BuildManager manuscript_name: {manuscript_name!r}")

    # Simulate the environment variable setting
    os.environ["MANUSCRIPT_PATH"] = manuscript_name
    print(f"Set MANUSCRIPT_PATH env var: {os.environ['MANUSCRIPT_PATH']!r}")

    # write_manuscript_output logic
    env_manuscript_path = os.getenv("MANUSCRIPT_PATH", "MANUSCRIPT")
    env_manuscript_name = os.path.basename(env_manuscript_path)
    print(f"write_manuscript_output env_manuscript_path: {env_manuscript_path!r}")
    print(f"write_manuscript_output env_manuscript_name: {env_manuscript_name!r}")

    # Check for validation issues
    if not env_manuscript_name or env_manuscript_name in (".", ".."):
        env_manuscript_name = "MANUSCRIPT"
        print(f"Validation failed! Using fallback: {env_manuscript_name!r}")

    output_dir = "CCT8_paper/output"
    output_file = Path(output_dir) / f"{env_manuscript_name}.tex"
    print(f"Output file would be: {output_file}")
    print()


if __name__ == "__main__":
    test_manuscript_name_detection()
