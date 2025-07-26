"""Tests for the Rxiv-Maker Colab notebook."""

from pathlib import Path

import pytest


@pytest.mark.slow
@pytest.mark.notebook
@pytest.mark.skip(reason="nb_regression fixture not available")
def test_colab_notebook_execution(nb_regression):
    """Test that the Colab notebook executes without errors.

    This test validates that the notebook can be executed from start to finish
    without errors. It uses pytest-notebook's regression testing to ensure
    the notebook produces consistent outputs.

    Note: This test is marked as 'slow' because notebook execution can take
    significant time, especially with LaTeX compilation.
    """
    notebook_path = (
        Path(__file__).parent.parent.parent / "notebooks" / "rxiv_maker_colab.ipynb"
    )

    # Ensure notebook exists
    assert notebook_path.exists(), f"Notebook not found at {notebook_path}"

    # Execute notebook and compare outputs
    nb_regression.check(
        notebook_path,
        # Skip cells that require user interaction (file uploads)
        # and cells that depend on external services
        skip_cells=[
            # Cell with file upload widgets
            "files.upload()",
            # Cells that download files (would fail in test environment)
            "files.download(",
        ],
        # Set timeout for long-running cells (LaTeX compilation)
        timeout=300,  # 5 minutes
        # Allow some variance in outputs (timestamps, paths, etc.)
        diff_ignore=[
            "/notebooks/outputs/",  # Ignore output file paths
            "Created ZIP archive:",  # Ignore timestamp-based filenames
            "Archive size:",  # File sizes may vary
        ],
    )


@pytest.mark.notebook
def test_notebook_metadata_cells():
    """Test that the notebook has proper metadata and structure."""
    notebook_path = (
        Path(__file__).parent.parent.parent / "notebooks" / "rxiv_maker_colab.ipynb"
    )

    # Basic existence check
    assert notebook_path.exists(), f"Notebook not found at {notebook_path}"

    # Check file is not empty
    assert notebook_path.stat().st_size > 0, "Notebook file is empty"


@pytest.mark.notebook
@pytest.mark.unit
def test_notebook_has_required_sections():
    """Test that the notebook contains all required sections."""
    import json

    notebook_path = (
        Path(__file__).parent.parent.parent / "notebooks" / "rxiv_maker_colab.ipynb"
    )

    with open(notebook_path) as f:
        notebook = json.load(f)

    # Check that notebook has cells
    assert "cells" in notebook, "Notebook has no cells"
    assert len(notebook["cells"]) > 0, "Notebook is empty"

    # Look for key sections in markdown cells
    markdown_cells = [
        cell["source"] for cell in notebook["cells"] if cell["cell_type"] == "markdown"
    ]

    markdown_text = " ".join([" ".join(cell) for cell in markdown_cells])

    # Check for essential sections
    required_sections = [
        "Docker Setup and Installation",
        "Clone Rxiv-Maker Repository",
        "Generate PDF Article",
        "Preview and Download",
        "Troubleshooting",
    ]

    for section in required_sections:
        assert section in markdown_text, (
            f"Required section '{section}' not found in notebook"
        )


@pytest.mark.notebook
@pytest.mark.unit
def test_notebook_python_syntax():
    """Test that all Python code cells have valid syntax."""
    import ast
    import json

    notebook_path = (
        Path(__file__).parent.parent.parent / "notebooks" / "rxiv_maker_colab.ipynb"
    )

    with open(notebook_path) as f:
        notebook = json.load(f)

    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]

    for i, cell in enumerate(code_cells):
        source = "".join(cell["source"])

        # Skip cells that are commented out or contain shell commands
        if source.strip().startswith("#") or source.strip().startswith("!"):
            continue

        # Skip cells with magic commands or special syntax
        if any(line.strip().startswith(("%", "!", "?")) for line in source.split("\n")):
            continue

        try:
            # Try to parse the Python code
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"Syntax error in code cell {i}: {e}\nCell content:\n{source}")
