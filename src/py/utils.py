"""Utility functions for Rxiv-Maker.

This module contains general utility functions used across the Rxiv-Maker system.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def create_output_dir(output_dir):
    """Create output directory if it doesn't exist."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    else:
        print(f"Output directory already exists: {output_dir}")


def find_manuscript_md():
    """Look for manuscript main file in the manuscript directory."""
    current_dir = Path.cwd()

    # Get manuscript path from environment variable, default to MANUSCRIPT
    manuscript_path = os.getenv("MANUSCRIPT_PATH", "MANUSCRIPT")

    # Look for main manuscript file: 01_MAIN.md
    manuscript_md = current_dir / manuscript_path / "01_MAIN.md"
    if manuscript_md.exists():
        return manuscript_md

    raise FileNotFoundError(
        f"Main manuscript file 01_MAIN.md not found in "
        f"{current_dir}/{manuscript_path}/. "
        f"Make sure MANUSCRIPT_PATH environment variable points to the "
        f"correct directory."
    )


def write_manuscript_output(output_dir, template_content):
    """Write the generated manuscript to the output directory."""
    # Get manuscript path from environment variable
    import os

    manuscript_path = os.getenv("MANUSCRIPT_PATH", "MANUSCRIPT")

    # Extract the manuscript name from the path (just the directory name)
    manuscript_name = os.path.basename(manuscript_path)

    # Generate output filename based on manuscript name
    output_file = Path(output_dir) / f"{manuscript_name}.tex"
    with open(output_file, "w") as file:
        file.write(template_content)

    print(f"Generated manuscript: {output_file}")
    return output_file


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
    """Copy generated PDF to manuscript folder with custom filename."""
    # Get manuscript path from environment variable to determine the output PDF name
    manuscript_path = os.getenv("MANUSCRIPT_PATH", "MANUSCRIPT")
    manuscript_name = os.path.basename(manuscript_path)

    output_pdf = Path(output_dir) / f"{manuscript_name}.pdf"

    if not output_pdf.exists():
        print(f"Warning: PDF not found at {output_pdf}")
        return None

    # Generate custom filename
    custom_filename = get_custom_pdf_filename(yaml_metadata)
    manuscript_pdf_path = Path.cwd() / manuscript_path / custom_filename

    try:
        shutil.copy2(output_pdf, manuscript_pdf_path)
        print(f"✅ PDF copied to manuscript folder: {manuscript_pdf_path}")
        return manuscript_pdf_path
    except Exception as e:
        print(f"Error copying PDF: {e}")
        return None


def copy_pdf_to_base(output_dir, yaml_metadata):
    """Backward compatibility function - delegates to copy_pdf_to_manuscript_folder."""
    return copy_pdf_to_manuscript_folder(output_dir, yaml_metadata)


def inject_rxiv_citation(yaml_metadata):
    """Inject Rxiv-Maker citation into bib if acknowledge_rxiv_maker is true."""
    # Check if acknowledgment is requested
    acknowledge_rxiv = yaml_metadata.get("acknowledge_rxiv_maker", False)
    if not acknowledge_rxiv:
        return

    # Get manuscript path and bibliography file
    manuscript_path = os.getenv("MANUSCRIPT_PATH", "MANUSCRIPT")
    current_dir = Path.cwd()
    bib_filename = yaml_metadata.get("bibliography", "03_REFERENCES.bib")

    # Handle .bib extension
    if not bib_filename.endswith(".bib"):
        bib_filename += ".bib"

    bib_file_path = current_dir / manuscript_path / bib_filename

    if not bib_file_path.exists():
        print(
            f"Warning: Bibliography file {bib_file_path} not found. Creating new file."
        )
        bib_file_path.parent.mkdir(parents=True, exist_ok=True)
        bib_file_path.touch()

    # Read existing bibliography content
    try:
        with open(bib_file_path, encoding="utf-8") as f:
            bib_content = f.read()
    except Exception as e:
        print(f"Error reading bibliography file: {e}")
        return

    # Check if citation already exists
    if "saraiva_2025_rxivmaker" in bib_content:
        print("Rxiv-Maker citation already exists in bibliography")
        return

    # Define the Rxiv-Maker citation
    rxiv_citation = """
@article{saraiva_2025_rxivmaker,
  author       = {Saraiva, Bruno M. and Jacquemet, Guillaume and Henriques, Ricardo},
  title        = {Rxiv-Maker: an automated template engine for streamlined scientific
                 publications},
  journal      = {Zenodo},
  publisher    = {Zenodo},
  year         = 2025,
  month        = jul,
  doi          = {10.5281/zenodo.15753534},
  url          = {https://zenodo.org/records/15753534},
  eprint       = {https://zenodo.org/records/15753534/files/2025__saraiva_et_al__rxiv.pdf}
}
"""

    # Append citation to bibliography file
    try:
        with open(bib_file_path, "a", encoding="utf-8") as f:
            # Add newline if file doesn't end with one
            if bib_content and not bib_content.endswith("\n"):
                f.write("\n")
            f.write(rxiv_citation)

        print(f"✅ Rxiv-Maker citation injected into {bib_file_path}")
    except Exception as e:
        print(f"Error writing to bibliography file: {e}")
