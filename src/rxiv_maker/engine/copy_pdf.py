"""Standalone script to copy PDF with custom filename.

This script can be called from the Makefile or other build systems.
"""

import os
import sys

# Add the parent directory to the path to allow imports when run as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rxiv_maker.processors.yaml_processor import extract_yaml_metadata
from rxiv_maker.utils import copy_pdf_to_manuscript_folder, find_manuscript_md


def copy_pdf_with_custom_filename(output_dir: str = "output") -> bool:
    """Copy PDF to manuscript directory with custom filename.

    Args:
        output_dir: Output directory containing MANUSCRIPT.pdf

    Returns:
        True if successful, False otherwise
    """
    try:
        # Find and parse the manuscript markdown
        manuscript_md = find_manuscript_md()

        print(f"Reading metadata from: {manuscript_md}")
        yaml_metadata = extract_yaml_metadata(manuscript_md)

        # Copy PDF with custom filename
        result = copy_pdf_to_manuscript_folder(output_dir, yaml_metadata)

        if result:
            print("PDF copying completed successfully!")
            return True
        else:
            print("PDF copying failed!")
            return False

    except Exception as e:
        import traceback

        print(f"Error: {e}")
        print("Traceback:")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Copy PDF with custom filename")
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory containing MANUSCRIPT.pdf",
    )
    args = parser.parse_args()

    success = copy_pdf_with_custom_filename(args.output_dir)
    sys.exit(0 if success else 1)
