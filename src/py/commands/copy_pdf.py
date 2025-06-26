#!/usr/bin/env python3
"""Standalone script to copy PDF with custom filename.

This script can be called from the Makefile or other build systems.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from processors.yaml_processor import extract_yaml_metadata
from utils import copy_pdf_to_manuscript_folder, find_manuscript_md


def main():
    """Main entry point for copying PDF to manuscript directory."""
    parser = argparse.ArgumentParser(
        description="Copy PDF to base directory with custom filename"
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="output",
        help="Output directory containing MANUSCRIPT.pdf",
    )

    args = parser.parse_args()

    try:
        # Find and parse the manuscript markdown
        manuscript_md = find_manuscript_md()

        print(f"Reading metadata from: {manuscript_md}")
        yaml_metadata = extract_yaml_metadata(manuscript_md)

        # Copy PDF with custom filename
        result = copy_pdf_to_manuscript_folder(args.output_dir, yaml_metadata)

        if result:
            print("PDF copying completed successfully!")
        else:
            print("PDF copying failed!")
            return 1

    except Exception as e:
        import traceback

        print(f"Error: {e}")
        print("Traceback:")
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
