"""Utility modules for Rxiv-Maker.

This package contains utility functions for various tasks including
email encoding/decoding and other helper functions.
"""

# Import functions from utils.py at the parent level
import sys
from pathlib import Path

from .email_encoder import (
    decode_email,
    encode_author_emails,
    encode_email,
    process_author_emails,
)


def safe_print(message: str, emoji: str = "", fallback: str = ""):
    """Print a message with emoji, falling back to ASCII on Windows console encoding errors.

    Args:
        message: The main message to print
        emoji: The emoji to prefix (e.g., "✅", "⚠️", "❌")
        fallback: ASCII fallback if emoji fails (e.g., "[OK]", "[WARN]", "[ERROR]")
    """
    try:
        if emoji:
            print(f"{emoji} {message}")
        else:
            print(message)
    except UnicodeEncodeError:
        # Fallback to ASCII characters for Windows console compatibility
        if fallback:
            print(f"{fallback} {message}")
        else:
            print(message)


try:
    from ..utils import (
        copy_pdf_to_manuscript_folder,
        create_output_dir,
        find_manuscript_md,
        get_custom_pdf_filename,
        write_manuscript_output,
    )
except ImportError:
    # If utils.py is not accessible, define minimal versions
    import os
    import shutil
    from datetime import datetime

    def find_manuscript_md():
        """Find the main manuscript markdown file.

        Returns:
            Path to the main manuscript file (01_MAIN.md).

        Raises:
            FileNotFoundError: If the manuscript file cannot be found.
        """
        current_dir = Path.cwd()
        manuscript_path = os.getenv("MANUSCRIPT_PATH", "MANUSCRIPT")
        manuscript_md = current_dir / manuscript_path / "01_MAIN.md"
        if manuscript_md.exists():
            return manuscript_md
        raise FileNotFoundError(
            f"Main manuscript file 01_MAIN.md not found in "
            f"{current_dir}/{manuscript_path}/"
        )

    def get_custom_pdf_filename(yaml_metadata):
        """Generate custom PDF filename from metadata."""
        # Get current year as fallback
        current_year = str(datetime.now().year)

        # Extract date (year only)
        date = yaml_metadata.get("date", current_year)
        year = date[:4] if isinstance(date, str) and len(date) >= 4 else current_year

        # Extract lead_author from title metadata
        title_info = yaml_metadata.get("title", {})
        if isinstance(title_info, list):
            # Find lead_author in the list
            lead_author = None
            for item in title_info:
                if isinstance(item, dict) and "lead_author" in item:
                    lead_author = item["lead_author"]
                    break
            if not lead_author:
                lead_author = "unknown"
        elif isinstance(title_info, dict):
            lead_author = title_info.get("lead_author", "unknown")
        else:
            lead_author = "unknown"

        # Clean the lead author name (remove spaces, make lowercase)
        lead_author_clean = lead_author.lower().replace(" ", "_").replace(".", "")

        # Generate filename: year__lead_author_et_al__rxiv.pdf
        filename = f"{year}__{lead_author_clean}_et_al__rxiv.pdf"

        return filename

    def copy_pdf_to_manuscript_folder(output_dir, yaml_metadata):
        """Copy the generated PDF to the manuscript folder with proper naming.

        Args:
            output_dir: Directory containing the generated PDF.
            yaml_metadata: Metadata dictionary from YAML config.
        """
        # Get manuscript path from environment variable to determine the output PDF name
        manuscript_path = os.getenv("MANUSCRIPT_PATH", "MANUSCRIPT")
        manuscript_name = os.path.basename(manuscript_path)

        output_pdf = Path(output_dir) / f"{manuscript_name}.pdf"
        if not output_pdf.exists():
            print(f"Warning: PDF not found at {output_pdf}")
            return None

        # Generate custom filename
        custom_filename = get_custom_pdf_filename(yaml_metadata)
        # Use current working directory for testability
        manuscript_pdf_path = Path.cwd() / manuscript_path / custom_filename

        try:
            shutil.copy2(output_pdf, manuscript_pdf_path)
            safe_print(
                f"PDF copied to manuscript folder: {manuscript_pdf_path}", "✅", "[OK]"
            )
            return manuscript_pdf_path
        except Exception as e:
            print(f"Error copying PDF: {e}")
            return None

    def create_output_dir(output_dir):
        """Create output directory if it doesn't exist."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        else:
            print(f"Output directory already exists: {output_dir}")

    def write_manuscript_output(output_dir, template_content):
        """Write the generated manuscript to the output directory."""
        manuscript_path = os.getenv("MANUSCRIPT_PATH", "MANUSCRIPT")
        manuscript_name = os.path.basename(manuscript_path)

        # Generate output filename based on manuscript name
        output_file = Path(output_dir) / f"{manuscript_name}.tex"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(template_content)

        safe_print(f"Manuscript written to: {output_file}", "✅", "[OK]")
        return str(output_file)


__all__ = [
    "decode_email",
    "encode_author_emails",
    "encode_email",
    "process_author_emails",
    "safe_print",
    "find_manuscript_md",
    "copy_pdf_to_manuscript_folder",
    "get_custom_pdf_filename",
    "create_output_dir",
    "write_manuscript_output",
]
