"""Citation handling utilities for Rxiv-Maker."""

import os
import re
from pathlib import Path
from typing import Any, Optional, Tuple

# Current canonical rxiv-maker citation
CANONICAL_RXIV_CITATION = """@misc{saraiva_2025_rxivmaker,
      title={Rxiv-Maker: an automated template engine for streamlined scientific publications},
      author={Bruno M. Saraiva and António D. Brito and Guillaume Jaquemet and Ricardo Henriques},
      year={2025},
      eprint={2508.00836},
      archivePrefix={arXiv},
      primaryClass={cs.DL},
      url={https://arxiv.org/abs/2508.00836},
}"""


def extract_existing_citation(bib_content: str) -> Optional[Tuple[str, int, int]]:
    """Extract existing rxiv-maker citation from bibliography content.

    Args:
        bib_content: The bibliography file content

    Returns:
        Tuple of (citation_content, start_index, end_index) if found, None otherwise
    """
    # Pattern to match the complete citation block for saraiva_2025_rxivmaker
    pattern = r"@\w+\s*\{\s*saraiva_2025_rxivmaker\s*,.*?\n\s*\}"

    match = re.search(pattern, bib_content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(0), match.start(), match.end()
    return None


def is_citation_outdated(existing_citation: str) -> bool:
    """Check if the existing citation is outdated compared to canonical version.

    Args:
        existing_citation: The existing citation content

    Returns:
        True if citation needs updating, False if it's current
    """
    # Extract key fields for comparison
    current_authors = "Bruno M. Saraiva and António D. Brito and Guillaume Jaquemet and Ricardo Henriques"
    current_title = "Rxiv-Maker: an automated template engine for streamlined scientific publications"
    current_eprint = "2508.00836"

    # Check if citation contains all current required elements
    has_current_authors = current_authors in existing_citation
    has_current_title = current_title in existing_citation
    has_current_eprint = current_eprint in existing_citation

    # Citation is outdated if any key element is missing
    return not (has_current_authors and has_current_title and has_current_eprint)


def inject_rxiv_citation(yaml_metadata: dict[str, Any]) -> None:
    """Inject Rxiv-Maker citation into bibliography if acknowledge_rxiv_maker is true.

    Args:
        yaml_metadata: The YAML metadata dictionary.
    """
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
        print(f"Warning: Bibliography file {bib_file_path} not found. Creating new file.")
        bib_file_path.parent.mkdir(parents=True, exist_ok=True)
        bib_file_path.touch()

    # Read existing bibliography content
    try:
        with open(bib_file_path, encoding="utf-8") as f:
            bib_content = f.read()
    except Exception as e:
        print(f"Error reading bibliography file: {e}")
        return

    # Check if citation already exists and whether it needs updating
    existing_citation_info = extract_existing_citation(bib_content)

    if existing_citation_info:
        existing_citation, start_idx, end_idx = existing_citation_info

        if is_citation_outdated(existing_citation):
            # Update existing outdated citation
            try:
                # Replace the outdated citation with the current version
                updated_content = bib_content[:start_idx] + CANONICAL_RXIV_CITATION + bib_content[end_idx:]

                with open(bib_file_path, "w", encoding="utf-8") as f:
                    f.write(updated_content)

                print(f"✅ Rxiv-Maker citation updated to latest version in {bib_file_path}")
                return

            except Exception as e:
                print(f"Error updating citation in bibliography file: {e}")
                return
        else:
            # Citation exists and is up-to-date
            print("Rxiv-Maker citation already exists and is up-to-date in bibliography")
            return

    # No existing citation found, append new one
    try:
        with open(bib_file_path, "a", encoding="utf-8") as f:
            # Add newline if file doesn't end with one
            if bib_content and not bib_content.endswith("\n"):
                f.write("\n")
            f.write("\n" + CANONICAL_RXIV_CITATION)

        print(f"✅ Rxiv-Maker citation injected into {bib_file_path}")
    except Exception as e:
        print(f"Error writing to bibliography file: {e}")
