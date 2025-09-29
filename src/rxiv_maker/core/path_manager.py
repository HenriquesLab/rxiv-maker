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

    def get_style_file_path(self, filename: str) -> Path:
        """Get path for style file.

        Args:
            filename: Name of style file (e.g., 'rxiv_maker_style.cls')

        Returns:
            Absolute path to style file in style directory
        """
        return self.style_dir / filename

    def copy_style_files_to_output(self, style_files: list[str] = None) -> list[Path]:
        """Copy style files to output directory.

        Args:
            style_files: List of style file names. Defaults to standard rxiv-maker files.

        Returns:
            List of paths to copied files

        Raises:
            PathResolutionError: If style files cannot be found or copied
        """
        import shutil

        if style_files is None:
            style_files = ["rxiv_maker_style.cls", "rxiv_maker_style.bst"]

        copied_files = []
        missing_files = []

        for style_file in style_files:
            source_path = self.get_style_file_path(style_file)
            if source_path.exists():
                dest_path = self.get_output_file_path(style_file)
                shutil.copy2(source_path, dest_path)
                copied_files.append(dest_path)
            else:
                missing_files.append(source_path)

        if missing_files:
            missing_list = "\n".join(f"  - {p}" for p in missing_files)
            raise PathResolutionError(
                f"Style files not found:\n{missing_list}\nThis may indicate a corrupted installation."
            )

        return copied_files

    def copy_figures_to_output(self) -> list[Path]:
        """Copy figures from FIGURES directory to output directory.

        Recursively copies all figure files while preserving directory structure.
        Supports both flat files and subdirectory organization (e.g., fig1/, fig2/).

        Returns:
            List of paths to copied figure files

        Raises:
            PathResolutionError: If figures directory cannot be accessed
        """
        import shutil

        # Source figures directory in manuscript
        figures_source_dir = self.manuscript_path / "FIGURES"

        # Destination figures directory in output
        figures_dest_dir = self.output_dir / "FIGURES"

        copied_files = []

        # Check if source FIGURES directory exists
        if not figures_source_dir.exists():
            # No figures directory is not an error - just return empty list
            return copied_files

        # Create destination FIGURES directory
        figures_dest_dir.mkdir(parents=True, exist_ok=True)

        # Supported figure file extensions
        figure_extensions = {".png", ".pdf", ".jpg", ".jpeg", ".eps", ".svg", ".gif", ".tiff", ".tif"}

        def copy_figures_recursive(source_dir: Path, dest_dir: Path):
            """Recursively copy figure files while preserving directory structure."""
            for item in source_dir.iterdir():
                if item.is_file() and item.suffix.lower() in figure_extensions:
                    # Copy individual figure file
                    dest_path = dest_dir / item.name
                    shutil.copy2(item, dest_path)
                    copied_files.append(dest_path)
                elif item.is_dir():
                    # Create corresponding subdirectory and recurse
                    dest_subdir = dest_dir / item.name
                    dest_subdir.mkdir(parents=True, exist_ok=True)
                    copy_figures_recursive(item, dest_subdir)

        # Start recursive copying
        copy_figures_recursive(figures_source_dir, figures_dest_dir)

        return copied_files

    def get_config_file_path(self) -> Path:
        """Get path to configuration file (00_CONFIG.yml).

        Returns:
            Absolute path to 00_CONFIG.yml file
        """
        return self.manuscript_path / "00_CONFIG.yml"

    def get_supplementary_tex_path(self) -> Path:
        """Get path for supplementary information .tex file.

        Returns:
            Absolute path to Supplementary.tex in output directory
        """
        return self.get_output_file_path("Supplementary.tex")

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

        Raises:
            PathResolutionError: If path contains directory traversal patterns
        """
        path_str = str(path)

        # Security: Check for malicious directory traversal patterns
        if ".." in path_str:
            # Handle both Unix and Windows separators
            normalized_path = path_str.replace("\\", "/")

            # Allow only simple cases like ../manuscript-dir/file
            # Block anything that could be an attack vector
            path_parts = normalized_path.split("/")
            dot_dot_count = path_parts.count("..")

            # Check for suspicious patterns
            suspicious_conditions = [
                dot_dot_count > 1,  # Multiple .. in path
                any(
                    part in ["etc", "root", "usr", "var", "boot", "sys", "proc", "windows", "system32"]
                    for part in path_parts
                ),  # System directories in path
                normalized_path.startswith("../.."),  # Starts with multiple traversals
                "secret" in path_str.lower(),  # Contains potentially sensitive names
            ]

            if any(suspicious_conditions):
                raise PathResolutionError(f"Path traversal not allowed: {path}")

            # Additional check - resolve and verify the path doesn't escape too far up
            try:
                resolved_path = Path(path).resolve()
                # If it resolves outside of a reasonable boundary, block it
                cwd_parts = len(Path.cwd().parts)
                resolved_parts = len(resolved_path.parts)

                # If the resolved path has significantly fewer parts than CWD, it might be traversing up too far
                if resolved_parts < cwd_parts - 2:
                    raise PathResolutionError(f"Path traversal not allowed: {path}")

            except (OSError, ValueError):
                # If path resolution fails, it might be malicious
                raise PathResolutionError(f"Path traversal not allowed: {path}") from None

        path = Path(path)

        # Handle trailing slashes (fixes Issue #100)
        if isinstance(path, str):
            path = path.rstrip("/")
            path = Path(path)

        # Resolve to absolute path
        if not path.is_absolute():
            path = self._working_dir / path

        # Use absolute() instead of resolve() to avoid symlink resolution on macOS
        normalized = path.absolute()

        # Additional security check: ensure normalized path doesn't escape working directory
        # for relative paths
        if not str(path).startswith("/"):  # Only check for relative paths
            try:
                normalized.relative_to(self._working_dir)
            except ValueError:
                raise PathResolutionError(f"Path escapes working directory: {path}") from None

        return normalized

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
