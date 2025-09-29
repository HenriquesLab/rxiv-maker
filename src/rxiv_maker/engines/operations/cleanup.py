"""Cleanup command for Rxiv-Maker.

This script handles cross-platform cleanup operations including:
- Output directory cleanup
- Generated figure cleanup
- ArXiv file cleanup
- Temporary file cleanup
"""

import os
from pathlib import Path

from ...utils.platform import platform_detector


class CleanupManager:
    """Handle cleanup operations."""

    def __init__(
        self,
        manuscript_path: str | None = None,
        output_dir: str = "output",
        verbose: bool = False,
    ):
        """Initialize cleanup manager.

        Args:
            manuscript_path: Path to manuscript directory
            output_dir: Output directory to clean
            verbose: Enable verbose output
        """
        self.manuscript_path: str = manuscript_path or os.getenv("MANUSCRIPT_PATH") or "MANUSCRIPT"
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        self.platform = platform_detector

        # Set up paths
        self.manuscript_dir = Path(self.manuscript_path)
        self.figures_dir = self.manuscript_dir / "FIGURES"

    def log(self, message: str, level: str = "INFO"):
        """Log a message with appropriate formatting."""
        # Use safe printing to handle Windows console encoding issues
        try:
            if level == "INFO":
                print(f"✅ {message}")
            elif level == "WARNING":
                print(f"⚠️  {message}")
            elif level == "ERROR":
                print(f"❌ {message}")
            elif level == "STEP":
                print(f"🧹 {message}")
            else:
                print(message)
        except UnicodeEncodeError:
            # Fallback to ASCII characters for Windows console compatibility
            level_chars = {
                "INFO": "[OK]",
                "WARNING": "[WARN]",
                "ERROR": "[ERROR]",
                "STEP": "[CLEAN]",
            }
            char = level_chars.get(level, "")
            print(f"{char} {message}")

    def clean_output_directory(self) -> bool:
        """Clean the output directory."""
        if not self.output_dir.exists():
            self.log("Output directory doesn't exist, nothing to clean")
            return True

        self.log(f"Cleaning output directory: {self.output_dir}", "STEP")

        try:
            success = self.platform.remove_directory(self.output_dir)
            if success:
                self.log("Output directory cleaned")
                return True
            else:
                self.log("Failed to clean output directory", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error cleaning output directory: {e}", "ERROR")
            return False

    def clean_generated_figures(self) -> bool:
        """Clean generated figures from the FIGURES directory."""
        if not self.figures_dir.exists():
            self.log("FIGURES directory doesn't exist, nothing to clean")
            return True

        self.log(f"Cleaning generated figures from: {self.figures_dir}", "STEP")

        # Define patterns for generated figure files
        figure_patterns = ["*.pdf", "*.png", "*.svg", "*.eps"]

        # Define source file patterns that should NEVER be deleted
        source_patterns = ["*.py", "*.R", "*.mmd", "*.md", "*.txt", "*.yaml", "*.yml", "*.json"]

        cleaned_files = []

        try:
            # Build set of source files to preserve
            source_files = set()
            for pattern in source_patterns:
                for file in self.figures_dir.glob(pattern):
                    source_files.add(file.stem)  # Get filename without extension

            # Clean files in the main FIGURES directory
            for pattern in figure_patterns:
                for file in self.figures_dir.glob(pattern):
                    # Check if this file has a corresponding source file
                    file_stem = file.stem
                    has_source = any(file_stem == source_stem for source_stem in source_files)

                    # Only delete if it has a corresponding source file (meaning it's generated)
                    if has_source:
                        try:
                            file.unlink()
                            cleaned_files.append(str(file))
                            if self.verbose:
                                self.log(f"Removed generated file: {file.name}")
                        except Exception as e:
                            self.log(f"Failed to remove {file.name}: {e}", "WARNING")
                    elif self.verbose:
                        self.log(f"Preserved static file: {file.name}")

            # Clean files in subdirectories (figure output directories)
            for item in self.figures_dir.iterdir():
                if item.is_dir():
                    # For subdirectories, we can be more aggressive since they're usually output dirs
                    # but still check for source files in the subdirectory
                    subdir_source_files = set()
                    for pattern in source_patterns:
                        for file in item.glob(pattern):
                            subdir_source_files.add(file.stem)

                    for pattern in figure_patterns:
                        for file in item.glob(pattern):
                            # In subdirectories, if there's a source file OR it's a known output directory,
                            # we can delete the generated files
                            file_stem = file.stem
                            has_source = any(file_stem == source_stem for source_stem in subdir_source_files)

                            # For subdirectories, be more permissive about deletion
                            # since they're typically output directories
                            if has_source or item.name.lower() in ["output", "generated", "build"]:
                                try:
                                    file.unlink()
                                    cleaned_files.append(str(file))
                                    if self.verbose:
                                        self.log(f"Removed: {item.name}/{file.name}")
                                except Exception as e:
                                    self.log(
                                        f"Failed to remove {item.name}/{file.name}: {e}",
                                        "WARNING",
                                    )
                            elif self.verbose:
                                self.log(f"Preserved: {item.name}/{file.name}")

                    # Remove empty subdirectories
                    try:
                        if not any(item.iterdir()):
                            item.rmdir()
                            if self.verbose:
                                self.log(f"Removed empty directory: {item.name}")
                    except Exception as e:
                        if self.verbose:
                            self.log(
                                f"Could not remove directory {item.name}: {e}",
                                "WARNING",
                            )

            if cleaned_files:
                self.log(f"Cleaned {len(cleaned_files)} generated figure files")
            else:
                self.log("No generated figures to clean")

            return True

        except Exception as e:
            self.log(f"Error cleaning generated figures: {e}", "ERROR")
            return False

    def clean_arxiv_files(self) -> bool:
        """Clean ArXiv-related files."""
        self.log("Cleaning ArXiv files...", "STEP")

        # Files to clean
        arxiv_files = [
            Path("for_arxiv.zip"),
            Path("arxiv_submission"),
            self.output_dir / "for_arxiv.zip",
            self.output_dir / "arxiv_submission",
        ]

        # Also check for ArXiv files in manuscript directory
        if self.manuscript_dir.exists():
            for file in self.manuscript_dir.glob("*__*_et_al__for_arxiv.zip"):
                arxiv_files.append(file)

        cleaned_files = []

        for file_path in arxiv_files:
            try:
                if file_path.exists():
                    if file_path.is_file():
                        file_path.unlink()
                        cleaned_files.append(str(file_path))
                        if self.verbose:
                            self.log(f"Removed: {file_path}")
                    elif file_path.is_dir():
                        success = self.platform.remove_directory(file_path)
                        if success:
                            cleaned_files.append(str(file_path))
                            if self.verbose:
                                self.log(f"Removed directory: {file_path}")
            except Exception as e:
                self.log(f"Failed to remove {file_path}: {e}", "WARNING")

        if cleaned_files:
            self.log(f"Cleaned {len(cleaned_files)} ArXiv files")
        else:
            self.log("No ArXiv files to clean")

        return True

    def clean_temporary_files(self) -> bool:
        """Clean temporary LaTeX and other temporary files."""
        self.log("Cleaning temporary files...", "STEP")

        # Temporary file patterns
        temp_patterns = [
            "*.aux",
            "*.log",
            "*.bbl",
            "*.blg",
            "*.out",
            "*.toc",
            "*.lof",
            "*.lot",
            "*.fls",
            "*.fdb_latexmk",
            "*.synctex.gz",
            "*.nav",
            "*.snm",
            "*.vrb",
        ]

        cleaned_files = []

        # Clean from output directory
        if self.output_dir.exists():
            for pattern in temp_patterns:
                for file in self.output_dir.glob(pattern):
                    try:
                        file.unlink()
                        cleaned_files.append(str(file))
                        if self.verbose:
                            self.log(f"Removed: {file.name}")
                    except Exception as e:
                        self.log(f"Failed to remove {file.name}: {e}", "WARNING")

        # Clean from manuscript directory
        if self.manuscript_dir.exists():
            for pattern in temp_patterns:
                for file in self.manuscript_dir.glob(pattern):
                    try:
                        file.unlink()
                        cleaned_files.append(str(file))
                        if self.verbose:
                            self.log(f"Removed: {file.name}")
                    except Exception as e:
                        self.log(f"Failed to remove {file.name}: {e}", "WARNING")

        # Only clean from current directory if it's the same as manuscript directory
        # This prevents accidentally cleaning files outside the intended scope
        current_dir = Path.cwd()
        manuscript_absolute = self.manuscript_dir.resolve()
        current_absolute = current_dir.resolve()

        if current_absolute == manuscript_absolute or self.manuscript_path == ".":
            # Only clean current directory if it's explicitly the manuscript directory
            for pattern in temp_patterns:
                for file in current_dir.glob(pattern):
                    try:
                        file.unlink()
                        cleaned_files.append(str(file))
                        if self.verbose:
                            self.log(f"Removed: {file.name}")
                    except Exception as e:
                        self.log(f"Failed to remove {file.name}: {e}", "WARNING")
        elif self.verbose:
            self.log("Skipping current directory cleanup (not same as manuscript directory)")

        if cleaned_files:
            self.log(f"Cleaned {len(cleaned_files)} temporary files")
        else:
            self.log("No temporary files to clean")

        return True

    def clean_cache_files(self, cache_type: str = "all") -> bool:
        """Clean cache files.

        Args:
            cache_type: Type of cache to clean ('all', 'manuscript', 'python')
        """
        self.log("Cleaning cache files...", "STEP")

        # Import cache utilities
        from ...core.cache.cache_utils import get_manuscript_cache_dir

        cleaned_dirs = []
        all_success = True

        # Clean manuscript-local cache (.rxiv_cache directory)
        if cache_type in ["all", "manuscript"]:
            try:
                manuscript_cache_dir = get_manuscript_cache_dir()
                if manuscript_cache_dir.exists():
                    success = self.platform.remove_directory(manuscript_cache_dir)
                    if success:
                        cleaned_dirs.append(str(manuscript_cache_dir))
                        self.log(f"Removed manuscript-local cache: {manuscript_cache_dir}")
                    else:
                        self.log(f"Failed to remove manuscript-local cache: {manuscript_cache_dir}", "WARNING")
                        all_success = False
                elif cache_type == "manuscript":
                    self.log("No manuscript-local cache found to clean")
            except RuntimeError:
                # Not in manuscript directory
                if cache_type == "manuscript":
                    self.log("Cannot clean manuscript cache - not in manuscript directory", "WARNING")
                    all_success = False

        # Global cache no longer exists - skip

        # Clean Python cache directories
        if cache_type in ["all", "python"]:
            python_cache_dirs = [Path("__pycache__"), Path(".pytest_cache")]

            # Add Python cache directories recursively
            for py_dir in Path("src/py").rglob("__pycache__"):
                python_cache_dirs.append(py_dir)

            for tests_dir in Path("tests").rglob("__pycache__"):
                python_cache_dirs.append(tests_dir)

            for cache_dir in python_cache_dirs:
                try:
                    if cache_dir.exists():
                        success = self.platform.remove_directory(cache_dir)
                        if success:
                            cleaned_dirs.append(str(cache_dir))
                            if self.verbose:
                                self.log(f"Removed Python cache directory: {cache_dir}")
                except Exception as e:
                    self.log(f"Failed to remove Python cache directory {cache_dir}: {e}", "WARNING")
                    all_success = False

        if cleaned_dirs:
            self.log(f"Cleaned {len(cleaned_dirs)} cache directories")
        else:
            self.log("No cache directories to clean")

        return all_success

    def clean_standardized_cache(self, subfolder: str | None = None) -> bool:
        """Clean standardized cache directory - deprecated, only manuscript-local cache exists now."""
        self.log("Global cache no longer exists - using manuscript-local cache only", "INFO")
        return True

    def run_full_cleanup(self) -> bool:
        """Run the complete cleanup process."""
        self.log(f"Starting cleanup process for manuscript: {self.manuscript_path}", "STEP")

        all_success = True

        # Step 1: Clean output directory
        if not self.clean_output_directory():
            all_success = False

        # Step 2: Clean generated figures
        if not self.clean_generated_figures():
            all_success = False

        # Step 3: Clean ArXiv files
        if not self.clean_arxiv_files():
            all_success = False

        # Step 4: Clean temporary files
        if not self.clean_temporary_files():
            all_success = False

        # Step 5: Clean cache files
        if not self.clean_cache_files():
            all_success = False

        if all_success:
            self.log("Cleanup completed successfully")
        else:
            self.log("Cleanup completed with some warnings", "WARNING")

        return all_success


def main():
    """Main entry point for cleanup command."""
    import argparse

    parser = argparse.ArgumentParser(description="Clean up generated files and directories")
    parser.add_argument("--manuscript-path", default="MANUSCRIPT", help="Path to manuscript directory")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--figures-only", action="store_true", help="Clean only generated figures")
    parser.add_argument("--output-only", action="store_true", help="Clean only output directory")
    parser.add_argument("--arxiv-only", action="store_true", help="Clean only arXiv files")
    parser.add_argument("--temp-only", action="store_true", help="Clean only temporary files")
    parser.add_argument("--cache-only", action="store_true", help="Clean only cache files")
    parser.add_argument(
        "--cache-type",
        choices=["all", "legacy", "manuscript", "global", "python"],
        default="all",
        help="Type of cache to clean (default: all)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Initialize cleanup manager
    cleanup_manager = CleanupManager(
        manuscript_path=args.manuscript_path,
        output_dir=args.output_dir,
        verbose=args.verbose,
    )

    success = True

    # Run specific cleanup based on flags
    if args.figures_only:
        success = cleanup_manager.clean_generated_figures()
    elif args.output_only:
        success = cleanup_manager.clean_output_directory()
    elif args.arxiv_only:
        success = cleanup_manager.clean_arxiv_files()
    elif args.temp_only:
        success = cleanup_manager.clean_temporary_files()
    elif args.cache_only:
        success = cleanup_manager.clean_cache_files(cache_type=args.cache_type)
    else:
        # Run full cleanup
        success = cleanup_manager.run_full_cleanup()

    if not success:
        exit(1)


if __name__ == "__main__":
    main()
