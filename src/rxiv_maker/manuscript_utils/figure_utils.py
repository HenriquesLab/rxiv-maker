"""Figure generation utilities for manuscript Python code.

This module provides functions that can be called from manuscript Python blocks
to generate figures programmatically. These functions wrap the core figure
generation functionality and make it available for use in executable manuscripts.
"""

import shutil
from pathlib import Path
from typing import List, Optional, Union

try:
    from ..core.environment_manager import EnvironmentManager
    from ..engines.operations.generate_figures import FigureGenerator
except ImportError:
    # Fallback for when running as script or in test environments
    FigureGenerator = None
    EnvironmentManager = None


class FigureGenerationError(Exception):
    """Exception raised during figure generation."""

    pass


def convert_mermaid(
    input_file: Union[str, Path], output_format: str = "png", output_dir: Optional[Union[str, Path]] = None, **kwargs
) -> List[Path]:
    """Convert a Mermaid diagram file to the specified format.

    Args:
        input_file: Path to the .mmd file to convert
        output_format: Output format ('png', 'svg', 'pdf', 'eps')
        output_dir: Output directory (defaults to FIGURES subdirectory)
        **kwargs: Additional arguments passed to the figure generator

    Returns:
        List of generated file paths

    Raises:
        FigureGenerationError: If generation fails
    """
    return _convert_single_figure(input_file, output_format, output_dir, "mermaid", **kwargs)


def convert_python_figure(
    input_file: Union[str, Path], output_format: str = "png", output_dir: Optional[Union[str, Path]] = None, **kwargs
) -> List[Path]:
    """Convert a Python figure script to the specified format.

    Args:
        input_file: Path to the .py file to execute
        output_format: Output format ('png', 'svg', 'pdf', 'eps')
        output_dir: Output directory (defaults to FIGURES subdirectory)
        **kwargs: Additional arguments passed to the figure generator

    Returns:
        List of generated file paths

    Raises:
        FigureGenerationError: If generation fails
    """
    return _convert_single_figure(input_file, output_format, output_dir, "python", **kwargs)


def convert_r_figure(
    input_file: Union[str, Path], output_format: str = "png", output_dir: Optional[Union[str, Path]] = None, **kwargs
) -> List[Path]:
    """Convert an R script to the specified format.

    Args:
        input_file: Path to the .R file to execute
        output_format: Output format ('png', 'svg', 'pdf', 'eps')
        output_dir: Output directory (defaults to FIGURES subdirectory)
        **kwargs: Additional arguments passed to the figure generator

    Returns:
        List of generated file paths

    Raises:
        FigureGenerationError: If generation fails or R not available
    """
    # Check if R is available
    if not _check_r_available():
        raise FigureGenerationError(
            "R is not available. Install R to use convert_r_figure(), or check the R installation in your PATH."
        )

    return _convert_single_figure(input_file, output_format, output_dir, "r", **kwargs)


def convert_figures_bulk(
    pattern: str,
    output_format: str = "png",
    output_dir: Optional[Union[str, Path]] = None,
    figure_types: Optional[List[str]] = None,
    **kwargs,
) -> List[Path]:
    """Convert multiple figure files matching a pattern.

    Args:
        pattern: Glob pattern to match files (e.g., '*.mmd', 'Figure_*.py')
        output_format: Output format ('png', 'svg', 'pdf', 'eps')
        output_dir: Output directory (defaults to FIGURES directory)
        figure_types: List of figure types to process (['mermaid', 'python', 'r'])
        **kwargs: Additional arguments passed to the figure generator

    Returns:
        List of all generated file paths

    Raises:
        FigureGenerationError: If generation fails
    """
    if figure_types is None:
        figure_types = ["mermaid", "python", "r"]

    figures_dir = _get_figures_directory()
    if not figures_dir.exists():
        raise FigureGenerationError(f"Figures directory not found: {figures_dir}")

    # Find all matching files
    matching_files = list(figures_dir.glob(pattern))

    if not matching_files:
        print(f"Warning: No files found matching pattern '{pattern}' in {figures_dir}")
        return []

    generated_files = []

    for file_path in matching_files:
        # Determine file type from extension
        file_type = None
        if file_path.suffix == ".mmd" and "mermaid" in figure_types:
            file_type = "mermaid"
        elif file_path.suffix == ".py" and "python" in figure_types:
            file_type = "python"
        elif file_path.suffix == ".R" and "r" in figure_types:
            file_type = "r"

        if file_type:
            try:
                result = _convert_single_figure(file_path, output_format, output_dir, file_type, **kwargs)
                generated_files.extend(result)
            except Exception as e:
                print(f"Warning: Failed to convert {file_path.name}: {e}")
                continue

    return generated_files


def _convert_single_figure(
    input_file: Union[str, Path], output_format: str, output_dir: Optional[Union[str, Path]], figure_type: str, **kwargs
) -> List[Path]:
    """Internal function to convert a single figure file.

    Args:
        input_file: Input file path
        output_format: Output format
        output_dir: Output directory
        figure_type: Type of figure ('mermaid', 'python', 'r')
        **kwargs: Additional generator arguments

    Returns:
        List of generated file paths
    """
    if FigureGenerator is None:
        raise FigureGenerationError("FigureGenerator not available")

    input_path = Path(input_file)

    # Ensure input file exists
    if not input_path.exists():
        # Try relative to figures directory
        figures_dir = _get_figures_directory()
        input_path = figures_dir / input_file

        if not input_path.exists():
            raise FigureGenerationError(f"Input file not found: {input_file}")

    # Determine output directory
    if output_dir is None:
        output_dir = _get_figures_directory()
    else:
        output_dir = Path(output_dir)

    # Initialize figure generator
    try:
        generator = FigureGenerator(
            figures_dir=str(input_path.parent),
            output_dir=str(output_dir),
            output_format=output_format,
            **kwargs,
        )
    except Exception as e:
        raise FigureGenerationError(f"Failed to initialize figure generator: {e}") from e

    # Track files before generation
    output_subdir = output_dir / input_path.stem
    files_before = set()
    if output_subdir.exists():
        files_before = set(output_subdir.rglob(f"*.{output_format}"))

    # Generate the figure
    try:
        if figure_type == "mermaid":
            generator.generate_mermaid_figure(input_path)
        elif figure_type == "python":
            generator.generate_python_figure(input_path)
        elif figure_type == "r":
            generator.generate_r_figure(input_path)
        else:
            raise FigureGenerationError(f"Unknown figure type: {figure_type}")
    except Exception as e:
        raise FigureGenerationError(f"Figure generation failed: {e}") from e

    # Find newly generated files
    files_after = set()
    if output_subdir.exists():
        files_after = set(output_subdir.rglob(f"*.{output_format}"))

    new_files = list(files_after - files_before)

    if not new_files:
        # Check if any files exist (might have been cached)
        existing_files = list(files_after)
        if existing_files:
            print(f"Using cached figure: {input_path.name}")
            return existing_files[:1]  # Return first match
        else:
            raise FigureGenerationError(f"No output files generated for {input_path.name}")

    return new_files


def _get_figures_directory() -> Path:
    """Get the figures directory for the current manuscript."""
    # Try to detect the manuscript directory structure
    current_dir = Path.cwd()

    # Look for FIGURES directory in current or parent directories
    for level in range(4):
        check_dir = current_dir
        for _ in range(level):
            check_dir = check_dir.parent
            if check_dir == check_dir.parent:  # Reached root
                break

        figures_dir = check_dir / "FIGURES"
        if figures_dir.exists():
            return figures_dir

    # Fallback to FIGURES in current directory
    return current_dir / "FIGURES"


def _check_r_available() -> bool:
    """Check if R is available in the system."""
    return shutil.which("Rscript") is not None


# Utility functions for advanced use cases


def list_available_figures(figures_dir: Optional[Union[str, Path]] = None) -> dict:
    """List all available figure source files.

    Args:
        figures_dir: Directory to search (defaults to detected FIGURES directory)

    Returns:
        Dictionary with figure types as keys and lists of files as values
    """
    if figures_dir is None:
        figures_dir = _get_figures_directory()
    else:
        figures_dir = Path(figures_dir)

    if not figures_dir.exists():
        return {}

    return {
        "mermaid": list(figures_dir.glob("*.mmd")),
        "python": list(figures_dir.glob("*.py")),
        "r": list(figures_dir.glob("*.R")),
    }


def get_figure_info(input_file: Union[str, Path]) -> dict:
    """Get information about a figure file.

    Args:
        input_file: Path to the figure source file

    Returns:
        Dictionary with file information
    """
    input_path = Path(input_file)

    if not input_path.exists():
        figures_dir = _get_figures_directory()
        input_path = figures_dir / input_file

    if not input_path.exists():
        return {"exists": False, "error": f"File not found: {input_file}"}

    info = {
        "exists": True,
        "path": str(input_path),
        "size": input_path.stat().st_size,
        "modified": input_path.stat().st_mtime,
        "type": None,
    }

    # Determine type from extension
    if input_path.suffix == ".mmd":
        info["type"] = "mermaid"
    elif input_path.suffix == ".py":
        info["type"] = "python"
    elif input_path.suffix == ".R":
        info["type"] = "r"

    return info


def clean_figure_outputs(
    input_file: Optional[Union[str, Path]] = None, output_dir: Optional[Union[str, Path]] = None
) -> int:
    """Clean generated figure outputs.

    Args:
        input_file: Specific figure to clean (cleans all if None)
        output_dir: Output directory to clean

    Returns:
        Number of files removed
    """
    if output_dir is None:
        output_dir = _get_figures_directory()
    else:
        output_dir = Path(output_dir)

    removed_count = 0

    if input_file is not None:
        # Clean specific figure outputs
        input_path = Path(input_file)
        figure_subdir = output_dir / input_path.stem

        if figure_subdir.exists() and figure_subdir.is_dir():
            for file_path in figure_subdir.iterdir():
                if file_path.is_file():
                    file_path.unlink()
                    removed_count += 1
            # Remove the subdirectory if it's empty
            try:
                figure_subdir.rmdir()
            except OSError:
                pass  # Directory not empty
    else:
        # Clean all generated figures
        if output_dir.exists():
            for item in output_dir.iterdir():
                if item.is_dir():
                    # Check if it's a figure output directory
                    has_figures = any(
                        child.suffix in [".png", ".svg", ".pdf", ".eps"] for child in item.iterdir() if child.is_file()
                    )
                    if has_figures:
                        for file_path in item.iterdir():
                            if file_path.is_file() and file_path.suffix in [".png", ".svg", ".pdf", ".eps"]:
                                file_path.unlink()
                                removed_count += 1

    return removed_count
