"""File handling utilities for Rxiv-Maker."""

import os
from pathlib import Path


def create_output_dir(output_dir: str) -> None:
    """Create output directory if it doesn't exist.

    Args:
        output_dir: Path to the output directory to create.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    else:
        print(f"Output directory already exists: {output_dir}")


def find_manuscript_md() -> Path:
    """Find the main manuscript markdown file.

    Returns:
        Path to the main manuscript file (01_MAIN.md).

    Raises:
        FileNotFoundError: If the manuscript file cannot be found.
    """
    current_dir = Path.cwd()
    
    # First try the current directory (for when we're already in the manuscript dir)
    manuscript_md = current_dir / "01_MAIN.md"
    if manuscript_md.exists():
        return manuscript_md
    
    # Then try the MANUSCRIPT_PATH subdirectory (for backward compatibility)
    manuscript_path = os.getenv("MANUSCRIPT_PATH", "MANUSCRIPT")
    manuscript_md = current_dir / manuscript_path / "01_MAIN.md"
    if manuscript_md.exists():
        return manuscript_md

    raise FileNotFoundError(
        f"Main manuscript file 01_MAIN.md not found in "
        f"{current_dir}/ or {current_dir}/{manuscript_path}/. "
        f"Make sure you're in the manuscript directory or MANUSCRIPT_PATH environment variable points to the "
        f"correct directory."
    )


def write_manuscript_output(output_dir: str, template_content: str) -> str:
    """Write the generated manuscript to the output directory.

    Args:
        output_dir: Directory where the manuscript will be written.
        template_content: The processed LaTeX template content.

    Returns:
        Path to the written manuscript file.
    """
    manuscript_path = os.getenv("MANUSCRIPT_PATH", "MANUSCRIPT")
    manuscript_name = os.path.basename(manuscript_path)

    output_file = Path(output_dir) / f"{manuscript_name}.tex"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(template_content)

    print(f"Generated manuscript: {output_file}")
    return str(output_file)
