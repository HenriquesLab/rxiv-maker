"""PDF handling utilities for Rxiv-Maker."""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from .platform import safe_print


def get_custom_pdf_filename(yaml_metadata: dict[str, Any]) -> str:
    """Generate custom PDF filename from metadata.

    Args:
        yaml_metadata: The YAML metadata dictionary.

    Returns:
        Custom PDF filename in format: year__lead_author_et_al__rxiv.pdf
    """
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


def copy_pdf_to_manuscript_folder(output_dir: str, yaml_metadata: dict[str, Any]) -> Path | None:
    """Copy the generated PDF to the manuscript folder with proper naming.

    Args:
        output_dir: Directory containing the generated PDF.
        yaml_metadata: Metadata dictionary from YAML config.

    Returns:
        Path to the copied PDF file, or None if copy failed.
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
    # Use absolute path resolution to avoid nested directories
    manuscript_pdf_path = Path(manuscript_path).resolve() / custom_filename

    try:
        shutil.copy2(output_pdf, manuscript_pdf_path)
        safe_print(f"PDF copied to manuscript folder: {manuscript_pdf_path}", "✅", "[OK]")
        return manuscript_pdf_path
    except Exception as e:
        print(f"Error copying PDF: {e}")
        return None


def copy_pdf_to_base(output_dir: str, yaml_metadata: dict[str, Any]) -> Path | None:
    """Backward compatibility function - delegates to copy_pdf_to_manuscript_folder.

    Args:
        output_dir: Directory containing the generated PDF.
        yaml_metadata: Metadata dictionary from YAML config.

    Returns:
        Path to the copied PDF file, or None if copy failed.
    """
    return copy_pdf_to_manuscript_folder(output_dir, yaml_metadata)
