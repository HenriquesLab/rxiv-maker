"""Citation handling utilities for Rxiv-Maker."""

import os
from pathlib import Path
from typing import Any


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

    # Check if citation already exists
    if "saraiva_2025_rxivmaker" in bib_content:
        print("Rxiv-Maker citation already exists in bibliography")
        return

    # Define the Rxiv-Maker citation
    rxiv_citation = """
@misc{saraiva_2025_rxivmaker,
      title={Rxiv-Maker: an automated template engine for streamlined scientific publications},
      author={Bruno M. Saraiva and Guillaume Jaquemet and Ricardo Henriques},
      year={2025},
      eprint={2508.00836},
      archivePrefix={arXiv},
      primaryClass={cs.DL},
      url={https://arxiv.org/abs/2508.00836},
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
