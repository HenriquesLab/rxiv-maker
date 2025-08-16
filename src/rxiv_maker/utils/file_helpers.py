"""File handling utilities for Rxiv-Maker."""

import os
from pathlib import Path


# Lazy import to avoid circular dependencies
def _get_path_manager():
    """Get PathManager with lazy import."""
    try:
        from ..core.path_manager import PathManager

        return PathManager
    except ImportError:
        # For backwards compatibility during migration
        return None


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


def find_manuscript_md(manuscript_path: str | None = None) -> Path:
    """Find the main manuscript markdown file.

    Args:
        manuscript_path: Optional path to the manuscript directory. If not provided,
                        uses current directory or MANUSCRIPT_PATH environment variable.

    Returns:
        Path to the main manuscript file (01_MAIN.md).

    Raises:
        FileNotFoundError: If the manuscript file cannot be found.
    """
    # Try to use PathManager for centralized logic
    PathManager = _get_path_manager()
    if PathManager is not None:
        try:
            # Use EnvironmentManager for environment variable handling
            from ..core.environment_manager import EnvironmentManager

            # Handle explicit manuscript_path or environment variable
            if manuscript_path is not None:
                # Explicit path provided
                path_manager = PathManager(manuscript_path=manuscript_path, output_dir="output")
                manuscript_md = path_manager.manuscript_path / "01_MAIN.md"

                if manuscript_md.exists():
                    return manuscript_md

                raise FileNotFoundError(
                    f"Main manuscript file 01_MAIN.md not found in {path_manager.manuscript_path}/. "
                    f"Make sure you specify the correct manuscript directory."
                )
            else:
                # Check environment variable
                env_path = EnvironmentManager.get_manuscript_path()
                if env_path:
                    # Environment variable is set
                    path_manager = PathManager(manuscript_path=env_path, output_dir="output")
                    manuscript_md = path_manager.manuscript_path / "01_MAIN.md"

                    if manuscript_md.exists():
                        return manuscript_md

                    raise FileNotFoundError(
                        f"Main manuscript file 01_MAIN.md not found in {path_manager.manuscript_path}/. "
                        f"Make sure you specify the correct manuscript directory."
                    )
                # If no environment variable, fall back to legacy logic
        except Exception:
            # Fall back to legacy logic if PathManager fails
            pass

    # Legacy logic for backward compatibility
    if manuscript_path:
        # If manuscript_path is provided, look directly in that directory
        manuscript_dir = Path(manuscript_path)
        manuscript_md = manuscript_dir / "01_MAIN.md"
        if manuscript_md.exists():
            return manuscript_md

        raise FileNotFoundError(
            f"Main manuscript file 01_MAIN.md not found in {manuscript_dir}/. "
            f"Make sure you specify the correct manuscript directory."
        )

    # Original logic for backward compatibility
    current_dir = Path.cwd()

    # First try the current directory (for when we're already in the manuscript dir)
    manuscript_md = current_dir / "01_MAIN.md"
    if manuscript_md.exists():
        return manuscript_md

    # Then try the MANUSCRIPT_PATH subdirectory (for backward compatibility)
    env_manuscript_path = os.getenv("MANUSCRIPT_PATH", "MANUSCRIPT")
    manuscript_md = current_dir / env_manuscript_path / "01_MAIN.md"
    if manuscript_md.exists():
        return manuscript_md

    raise FileNotFoundError(
        f"Main manuscript file 01_MAIN.md not found in "
        f"{current_dir}/ or {current_dir}/{env_manuscript_path}/. "
        f"Make sure you're in the manuscript directory or MANUSCRIPT_PATH environment variable points to the "
        f"correct directory."
    )


def write_manuscript_output(output_dir: str, template_content: str, manuscript_name: str | None = None) -> str:
    """Write the generated manuscript to the output directory.

    Args:
        output_dir: Directory where the manuscript will be written.
        template_content: The processed LaTeX template content.
        manuscript_name: Name for the manuscript file (optional, defaults to MANUSCRIPT_PATH env var).

    Returns:
        Path to the written manuscript file.
    """
    # Try to use PathManager for centralized manuscript name logic
    if manuscript_name is None:
        PathManager = _get_path_manager()
        if PathManager is not None:
            try:
                from ..core.environment_manager import EnvironmentManager

                # Get manuscript path from environment
                manuscript_path = EnvironmentManager.get_manuscript_path() or "MANUSCRIPT"

                # Use PathManager to get normalized manuscript name
                path_manager = PathManager(manuscript_path=manuscript_path, output_dir=output_dir)
                manuscript_name = path_manager.manuscript_name
            except Exception:
                # Fall back to legacy logic if PathManager fails
                pass

        # Legacy logic for backward compatibility
        if manuscript_name is None:
            manuscript_path = os.getenv("MANUSCRIPT_PATH", "MANUSCRIPT")
            manuscript_name = os.path.basename(manuscript_path)

    # Validate manuscript name to prevent invalid filenames (regardless of source)
    if not manuscript_name or manuscript_name in (".", ".."):
        manuscript_name = "MANUSCRIPT"

    output_file = Path(output_dir) / f"{manuscript_name}.tex"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(template_content)

    print(f"Generated manuscript: {output_file}")
    return str(output_file)
