"""Centralized path management for rxiv-maker.

This module provides a unified interface for all path operations, eliminating
the scattered path logic throughout the codebase and fixing recurring issues
like trailing slash handling, cross-platform compatibility, and Docker
volume mounting.
"""

import os
from pathlib import Path
from typing import Optional, Union

from ..utils.platform import platform_detector


class PathResolutionError(Exception):
    """Exception raised when path resolution fails."""

    pass


class PathManager:
    """Centralized path management for rxiv-maker operations.

    Handles:
    - Manuscript path resolution with proper trailing slash handling
    - Cross-platform path normalization
    - Docker container path translation
    - Style directory auto-detection (dev vs installed)
    - Output directory management
    - Environment variable integration
    """

    def __init__(
        self,
        manuscript_path: Optional[Union[str, Path]] = None,
        output_dir: Optional[Union[str, Path]] = None,
        working_dir: Optional[Union[str, Path]] = None,
    ):
        """Initialize path manager.

        Args:
            manuscript_path: Path to manuscript directory. If None, uses environment
                           variable MANUSCRIPT_PATH or default "MANUSCRIPT"
            output_dir: Output directory path. If relative, resolved relative to manuscript
            working_dir: Working directory for operations. Defaults to current directory
        """
        self._manuscript_path_raw = manuscript_path
        self._output_dir_raw = output_dir
        self._working_dir = Path(working_dir or Path.cwd()).resolve()
        self._platform = platform_detector

        # Cache resolved paths
        self._manuscript_path_cache: Optional[Path] = None
        self._manuscript_name_cache: Optional[str] = None
        self._output_dir_cache: Optional[Path] = None
        self._style_dir_cache: Optional[Path] = None

    @property
    def manuscript_path(self) -> Path:
        """Get normalized manuscript path.

        Returns:
            Absolute path to manuscript directory

        Raises:
            PathResolutionError: If manuscript path cannot be resolved
        """
        if self._manuscript_path_cache is None:
            self._manuscript_path_cache = self._resolve_manuscript_path()
        return self._manuscript_path_cache

    @property
    def manuscript_name(self) -> str:
        """Get manuscript name with proper trailing slash handling.

        Fixes Issue #100 where trailing slashes caused BibTeX failures.

        Returns:
            Manuscript directory name, safe for use as filename base
        """
        if self._manuscript_name_cache is None:
            self._manuscript_name_cache = self._resolve_manuscript_name()
        return self._manuscript_name_cache

    @property
    def output_dir(self) -> Path:
        """Get output directory path.

        Returns:
            Absolute path to output directory
        """
        if self._output_dir_cache is None:
            self._output_dir_cache = self._resolve_output_dir()
        return self._output_dir_cache

    @property
    def figures_dir(self) -> Path:
        """Get figures directory relative to manuscript.

        Returns:
            Absolute path to figures directory (manuscript_path/FIGURES)
        """
        return self.manuscript_path / "FIGURES"

    @property
    def references_bib(self) -> Path:
        """Get references bibliography file path.

        Returns:
            Absolute path to 03_REFERENCES.bib file
        """
        return self.manuscript_path / "03_REFERENCES.bib"

    @property
    def main_md(self) -> Path:
        """Get main manuscript markdown file path.

        Returns:
            Absolute path to 01_MAIN.md file
        """
        return self.manuscript_path / "01_MAIN.md"

    @property
    def style_dir(self) -> Path:
        """Get style directory with automatic dev/installed detection.

        Resolves the complex style directory location logic that appears
        in multiple places throughout the codebase.

        Returns:
            Absolute path to style directory containing .cls files

        Raises:
            PathResolutionError: If no valid style directory found
        """
        if self._style_dir_cache is None:
            self._style_dir_cache = self._resolve_style_dir()
        return self._style_dir_cache

    def get_output_file_path(self, filename: str) -> Path:
        """Get path for output file in output directory.

        Args:
            filename: Name of output file

        Returns:
            Absolute path to output file
        """
        return self.output_dir / filename

    def get_manuscript_tex_path(self) -> Path:
        """Get path for generated manuscript .tex file.

        Returns:
            Absolute path to {manuscript_name}.tex in output directory
        """
        return self.get_output_file_path(f"{self.manuscript_name}.tex")

    def get_manuscript_pdf_path(self) -> Path:
        """Get path for generated manuscript .pdf file.

        Returns:
            Absolute path to {manuscript_name}.pdf in output directory
        """
        return self.get_output_file_path(f"{self.manuscript_name}.pdf")

    def to_container_path(self, host_path: Union[str, Path], workspace_mount: str = "/workspace") -> str:
        """Convert host path to container path for Docker operations.

        Args:
            host_path: Path on host system
            workspace_mount: Container mount point for workspace

        Returns:
            Path as it appears inside container
        """
        host_path = Path(host_path).resolve()

        # If path is within workspace, translate it
        try:
            relative_path = host_path.relative_to(self._working_dir)
            return str(Path(workspace_mount) / relative_path).replace("\\", "/")
        except ValueError:
            # Path is outside workspace, use absolute path
            return str(host_path).replace("\\", "/")

    def to_host_path(self, container_path: str, workspace_mount: str = "/workspace") -> Path:
        """Convert container path to host path.

        Args:
            container_path: Path as it appears inside container
            workspace_mount: Container mount point for workspace

        Returns:
            Corresponding path on host system
        """
        container_path_obj = Path(container_path)

        # If path is within workspace mount, translate it
        if str(container_path_obj).startswith(workspace_mount):
            try:
                relative_path = container_path_obj.relative_to(workspace_mount)
                return self._working_dir / relative_path
            except ValueError:
                pass

        # Return as-is for absolute paths outside workspace
        return container_path_obj

    def get_docker_volume_mounts(self, workspace_mount: str = "/workspace") -> list[str]:
        """Get Docker volume mount specifications.

        Args:
            workspace_mount: Container mount point for workspace

        Returns:
            List of volume mount strings for Docker
        """
        return [f"{self._working_dir}:{workspace_mount}"]

    def normalize_path(self, path: Union[str, Path]) -> Path:
        """Normalize path with cross-platform compatibility.

        Args:
            path: Path to normalize

        Returns:
            Normalized absolute path
        """
        path = Path(path)

        # Handle trailing slashes (fixes Issue #100)
        if isinstance(path, str):
            path = path.rstrip("/")
            path = Path(path)

        # Resolve to absolute path
        if not path.is_absolute():
            path = self._working_dir / path

        # Use absolute() instead of resolve() to avoid symlink resolution on macOS
        return path.absolute()

    def ensure_dir_exists(self, path: Union[str, Path]) -> Path:
        """Ensure directory exists, creating if necessary.

        Args:
            path: Directory path to ensure exists

        Returns:
            Absolute path to directory
        """
        path = self.normalize_path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _resolve_manuscript_path(self) -> Path:
        """Resolve manuscript path from various sources."""
        if self._manuscript_path_raw is not None:
            # Use provided path
            raw_path = str(self._manuscript_path_raw).rstrip("/")  # Fix trailing slash
            path = self.normalize_path(raw_path)
        else:
            # Check environment variable
            env_path = os.getenv("MANUSCRIPT_PATH")
            if env_path:
                raw_path = env_path.rstrip("/")  # Fix trailing slash
                path = self.normalize_path(raw_path)
            else:
                # Use default
                path = self.normalize_path("MANUSCRIPT")

        # Validate manuscript path
        if not path.exists():
            raise PathResolutionError(
                f"Manuscript directory not found: {path}. "
                f"Ensure the directory exists or set MANUSCRIPT_PATH environment variable."
            )

        if not path.is_dir():
            raise PathResolutionError(f"Manuscript path is not a directory: {path}")

        return path

    def _resolve_manuscript_name(self) -> str:
        """Resolve manuscript name with proper handling of edge cases."""
        # Check original raw path first for edge cases
        if self._manuscript_path_raw is not None:
            raw_path = str(self._manuscript_path_raw).rstrip("/")
            raw_name = os.path.basename(raw_path)
            # Check if raw input was edge case
            if not raw_name or raw_name in (".", ".."):
                return "MANUSCRIPT"

        # Get normalized path and extract basename
        path_str = str(self.manuscript_path)
        # Remove any trailing slashes (fixes Issue #100)
        normalized = path_str.rstrip("/")
        name = os.path.basename(normalized)

        # Validate name to prevent invalid filenames
        if not name or name in (".", ".."):
            return "MANUSCRIPT"

        return name

    def _resolve_output_dir(self) -> Path:
        """Resolve output directory path."""
        if self._output_dir_raw:
            output_path = Path(self._output_dir_raw)
            # If absolute, use as-is; if relative, make relative to manuscript
            if output_path.is_absolute():
                return output_path.absolute()
            else:
                return (self.manuscript_path / output_path).absolute()
        else:
            # Default to 'output' subdirectory in manuscript
            return (self.manuscript_path / "output").absolute()

    def _resolve_style_dir(self) -> Path:
        """Resolve style directory with automatic dev/installed detection."""
        # Possible style directory locations (from build_manager.py)
        possible_style_dirs = [
            # Installed package location (when installed via pip)
            Path(__file__).resolve().parent.parent / "tex" / "style",
            # Development location
            Path(__file__).resolve().parent.parent.parent.parent / "src" / "tex" / "style",
            # Alternative development location
            Path(__file__).resolve().parent.parent.parent / "tex" / "style",
        ]

        # Find first directory that exists and contains .cls files
        for style_dir in possible_style_dirs:
            if style_dir.exists() and any(style_dir.glob("*.cls")):
                return style_dir

        # If no valid directory found, raise error with helpful message
        searched_paths = "\n".join(f"  - {p}" for p in possible_style_dirs)
        raise PathResolutionError(
            f"No style directory found containing .cls files.\n"
            f"Searched locations:\n{searched_paths}\n"
            f"This may indicate a corrupted installation. Try reinstalling rxiv-maker."
        )

    def clear_cache(self) -> None:
        """Clear cached path resolutions."""
        self._manuscript_path_cache = None
        self._manuscript_name_cache = None
        self._output_dir_cache = None
        self._style_dir_cache = None

    def __repr__(self) -> str:
        """String representation for debugging."""
        try:
            return (
                f"PathManager("
                f"manuscript_path={self.manuscript_path}, "
                f"manuscript_name={self.manuscript_name}, "
                f"output_dir={self.output_dir})"
            )
        except PathResolutionError:
            return f"PathManager(unresolved, raw_manuscript_path={self._manuscript_path_raw})"
