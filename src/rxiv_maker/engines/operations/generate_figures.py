"""Figure Generation Script for Rxiv-Maker.

This script automatically processes figure files in the FIGURES directory and generates
publication-ready output files. It supports:
- .mmd files: Mermaid diagrams (generates SVG/PNG/PDF)
- .py files: Python scripts for matplotlib/seaborn figures
- .R files: R scripts (executes script and captures output figures)
"""

import base64
import logging
import os
import re
import sys
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore

try:
    from ...utils.retry import get_with_retry
except ImportError:
    # Fallback when retry module isn't available
    get_with_retry = None  # type: ignore

try:
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
        TimeElapsedColumn,
    )

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Add the parent directory to the path to allow imports when run as a script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import platform utilities and Docker manager with proper fallback handling
try:
    from ...core.environment_manager import EnvironmentManager
    from ...core.path_manager import PathManager

    # Docker manager import removed - now using global container manager
    from ...utils.platform import platform_detector
except ImportError:
    # Fallback for when running as script
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from rxiv_maker.core.environment_manager import EnvironmentManager  # type: ignore[no-redef]
    from rxiv_maker.core.path_manager import PathManager  # type: ignore[no-redef]

    # Docker manager import removed - now using global container manager
    from rxiv_maker.utils.platform import platform_detector  # type: ignore[no-redef]


class FigureGenerator:
    """Main class for generating figures from various source formats."""

    def __init__(
        self,
        figures_dir="FIGURES",
        output_dir="FIGURES",
        output_format="png",
        r_only=False,
        engine=None,
        enable_content_caching=True,
        manuscript_path=None,
    ):
        """Initialize the figure generator.

        Args:
            figures_dir: Directory containing source figure files
            output_dir: Directory for generated output files
            output_format: Default output format for figures
            r_only: Only process R files if True
            engine: Execution engine ("local" or "docker") - uses environment if None
            enable_content_caching: Enable content-based caching to avoid unnecessary rebuilds
            manuscript_path: Path to manuscript directory (for caching, defaults to current directory)
        """
        # Initialize path management
        try:
            # Try to use PathManager if manuscript_path can be resolved
            if manuscript_path:
                self.path_manager: Optional[PathManager] = PathManager(manuscript_path=manuscript_path)
                self.figures_dir = self.path_manager.figures_dir
            else:
                # Fallback to manual path resolution
                self.figures_dir = Path(figures_dir).resolve()
                self.path_manager = None
        except Exception:
            # Fallback to manual path resolution if PathManager fails
            self.figures_dir = Path(figures_dir).resolve()
            self.path_manager = None

        self.output_dir = Path(output_dir).resolve()
        self.output_format = output_format.lower()
        self.r_only = r_only

        # Use EnvironmentManager for engine configuration
        self.engine = engine or EnvironmentManager.get_rxiv_engine()
        self.enable_content_caching = enable_content_caching
        self.supported_formats = ["png", "svg", "pdf", "eps"]
        self.platform = platform_detector
        self.logger = logging.getLogger(__name__)
        self.verbose = EnvironmentManager.is_verbose()

        # Initialize content-based caching if enabled
        self.checksum_manager = None
        if self.enable_content_caching:
            try:
                # Import here to avoid circular dependencies
                from ...utils.figure_checksum import FigureChecksumManager

                # Use PathManager if available, otherwise use figures_dir parent
                if self.path_manager:
                    manuscript_cache_path = str(self.path_manager.manuscript_path)
                elif manuscript_path:
                    manuscript_cache_path = str(Path(manuscript_path).resolve())
                else:
                    manuscript_cache_path = str(self.figures_dir.parent)

                self.checksum_manager = FigureChecksumManager(manuscript_cache_path)
            except ImportError as e:
                print(f"Warning: Content caching disabled due to import error: {e}")
                self.enable_content_caching = False

        # Initialize container engine if using container engine (docker or podman)
        self.container_engine = None
        if self.engine in ["docker", "podman"]:
            # Use PathManager's working directory if available
            if self.path_manager:
                workspace_dir = self.path_manager._working_dir
            else:
                workspace_dir = Path.cwd().resolve()

            # Use global container manager for shared engine instances
            from ...core.global_container_manager import get_global_container_manager

            global_manager = get_global_container_manager()
            self.container_engine = global_manager.get_container_engine(
                engine_type=self.engine, workspace_dir=workspace_dir
            )

        if self.output_format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {self.output_format}. Supported: {self.supported_formats}")

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _should_regenerate_figure(self, source_file: Path, output_file: Path) -> bool:
        """Check if a figure should be regenerated based on content changes.

        Args:
            source_file: Source figure file (.mmd, .py, .R)
            output_file: Expected output file

        Returns:
            True if figure should be regenerated, False if cached version is up-to-date
        """
        # If caching is disabled, always regenerate
        if not self.enable_content_caching or self.checksum_manager is None:
            return True

        # If output file doesn't exist, must regenerate
        if not output_file.exists():
            return True

        # Check if source file content has changed
        try:
            relative_path = source_file.relative_to(self.figures_dir)
            return self.checksum_manager.has_file_changed(str(relative_path))
        except (ValueError, Exception):
            # If we can't determine, err on the side of regeneration
            return True

    def _update_figure_cache(self, source_file: Path) -> None:
        """Update the cache after successfully generating a figure.

        Args:
            source_file: Source figure file that was processed
        """
        if self.enable_content_caching and self.checksum_manager is not None:
            try:
                relative_path = source_file.relative_to(self.figures_dir)
                self.checksum_manager.update_file_checksum(str(relative_path))
            except (ValueError, Exception) as e:
                # Cache update failed, but don't fail the whole operation
                self.logger.warning(f"Failed to update checksum for {source_file.name}: {e}")

    def generate_all_figures(self, parallel: bool = True, max_workers: int = 4):
        """Generate all figures found in the figures directory.

        Args:
            parallel: Enable parallel processing of figures
            max_workers: Maximum number of worker threads for parallel processing
        """
        if not self.figures_dir.exists():
            print(f"Warning: Figures directory '{self.figures_dir}' does not exist")
            return

        # Find all figure files
        try:
            if self.r_only:
                r_files = list(self.figures_dir.glob("*.R"))
                mermaid_files = []
                python_files = []
            else:
                mermaid_files = list(self.figures_dir.glob("*.mmd"))
                python_files = list(self.figures_dir.glob("*.py"))
                r_files = list(self.figures_dir.glob("*.R"))

            total_files = len(mermaid_files) + len(python_files) + len(r_files)

            if total_files == 0:
                print("No figure files found to process")
                return

            print(f"Found {total_files} figure file(s) to process")

            # Process figures with optional parallelization
            if parallel and total_files > 1:
                self._generate_figures_parallel(mermaid_files, python_files, r_files, max_workers)
            else:
                self._generate_figures_sequential(mermaid_files, python_files, r_files)

        except Exception as e:
            self.logger.error(f"Error in figure generation: {e}")
            raise

    def _generate_figures_sequential(self, mermaid_files, python_files, r_files):
        """Generate figures sequentially with progress tracking."""
        all_files = []

        # Prepare file list with types
        if mermaid_files and not self.r_only:
            all_files.extend([(f, "mermaid", "🌊") for f in mermaid_files])
        if python_files and not self.r_only:
            all_files.extend([(f, "python", "🐍") for f in python_files])
        if r_files:
            all_files.extend([(f, "R", "📊") for f in r_files])

        if not all_files:
            return

        # Use Rich progress bar if available, fallback to simple progress
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(complete_style="green", finished_style="green"),
                TaskProgressColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                transient=True,
            ) as progress:
                task = progress.add_task("Generating figures...", total=len(all_files))

                for _i, (file_path, file_type, emoji) in enumerate(all_files):
                    progress.update(task, description=f"{emoji} Processing {file_path.name}")

                    try:
                        if file_type == "mermaid":
                            self.generate_mermaid_figure(file_path)
                        elif file_type == "python":
                            self.generate_python_figure(file_path)
                        elif file_type == "R":
                            self.generate_r_figure(file_path)

                        progress.update(task, advance=1, description=f"✅ {file_path.name} completed")
                    except Exception as e:
                        progress.update(task, advance=1, description=f"❌ {file_path.name} failed: {e}")
                        print(f"Error generating {file_path.name}: {e}")
        else:
            # Fallback to simple progress without Rich
            for i, (file_path, file_type, emoji) in enumerate(all_files):
                print(f"[{i + 1}/{len(all_files)}] {emoji} Processing {file_path.name}")

                try:
                    if file_type == "mermaid":
                        self.generate_mermaid_figure(file_path)
                    elif file_type == "python":
                        self.generate_python_figure(file_path)
                    elif file_type == "R":
                        self.generate_r_figure(file_path)

                    print(f"  ✅ Completed: {file_path.name}")
                except Exception as e:
                    print(f"  ❌ Failed: {file_path.name} - {e}")

    def _generate_figures_parallel(self, mermaid_files, python_files, r_files, max_workers):
        """Generate figures in parallel using ThreadPoolExecutor."""
        import concurrent.futures
        import threading

        print(f"Using parallel processing with {max_workers} workers")

        # Create thread-safe print function
        print_lock = threading.Lock()

        def safe_print(*args, **kwargs):
            with print_lock:
                print(*args, **kwargs)

        def process_figure(file_info):
            """Process a single figure file."""
            file_path, file_type = file_info
            try:
                safe_print(f"  [Parallel] Processing: {file_path.name}")

                if file_type == "mermaid":
                    self.generate_mermaid_figure(file_path)
                elif file_type == "python":
                    self.generate_python_figure(file_path)
                elif file_type == "r":
                    self.generate_r_figure(file_path)

                safe_print(f"  [Parallel] ✓ Completed: {file_path.name}")
                return True, file_path.name, None
            except Exception as e:
                safe_print(f"  [Parallel] ✗ Failed: {file_path.name} - {e}")
                return False, file_path.name, str(e)

        # Prepare work items
        work_items = []

        if mermaid_files and not self.r_only:
            work_items.extend([(f, "mermaid") for f in mermaid_files])

        if python_files and not self.r_only:
            work_items.extend([(f, "python") for f in python_files])

        if r_files:
            work_items.extend([(f, "r") for f in r_files])

        if not work_items:
            print("No figures to process")
            return

        safe_print(f"Processing {len(work_items)} figures in parallel...")

        # Process figures in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_file = {executor.submit(process_figure, item): item[0] for item in work_items}

            # Collect results
            completed = 0
            failed = 0

            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    success, filename, error = future.result()
                    if success:
                        completed += 1
                    else:
                        failed += 1
                except Exception as exc:
                    safe_print(f"  [Parallel] ✗ Exception for {file_path.name}: {exc}")
                    failed += 1

            safe_print(f"Parallel processing completed: {completed} successful, {failed} failed")

    def generate_mermaid_figure(self, mmd_file):
        """Generate figure from Mermaid diagram file using mermaid.ink API."""
        try:
            # Create subdirectory for this figure
            figure_dir = self.output_dir / mmd_file.stem
            figure_dir.mkdir(parents=True, exist_ok=True)

            # --- Step 1: Generate SVG using mermaid.ink API ---
            svg_output_file = figure_dir / f"{mmd_file.stem}.svg"

            # Check if figure needs regeneration
            if not self._should_regenerate_figure(mmd_file, svg_output_file):
                print(f"  ⚡ Skipping {mmd_file.name}: cached version is up-to-date")
                return

            print(f"  🎨 Generating SVG using mermaid.ink API: {figure_dir.name}/{svg_output_file.name}...")

            # Read the mermaid diagram content
            mermaid_content = mmd_file.read_text(encoding="utf-8")

            if self.engine in ["docker", "podman"]:
                # Use container engine for Mermaid processing
                if self.container_engine is None:
                    raise RuntimeError(f"{self.engine.title()} engine not initialized")
                result = self.container_engine.run_mermaid_generation(
                    input_file=mmd_file.resolve(),
                    output_file=svg_output_file.resolve(),
                    background_color="transparent",
                )

                if result.returncode != 0:
                    print(f"  ❌ Docker mermaid generation failed for {mmd_file.name}:")
                    print(f"     {result.stderr}")

                    # Generate a placeholder SVG to prevent build failures
                    print(f"  🔄 Creating placeholder SVG for {mmd_file.name}...")
                    self._create_placeholder_svg(svg_output_file, mmd_file.name, result.stderr)
                    return
            else:
                # Use mermaid.ink API approach
                success = self._generate_mermaid_with_api(mermaid_content, svg_output_file, mmd_file.name)

                if not success:
                    print(f"  🔄 Creating placeholder SVG for {mmd_file.name}...")
                    self._create_placeholder_svg(
                        svg_output_file,
                        mmd_file.name,
                        "mermaid.ink API approach failed - falling back to placeholder",
                    )
                    return

            # All formats are generated directly by _generate_mermaid_with_api()

            # Update cache after successful generation
            self._update_figure_cache(mmd_file)

        except Exception as e:
            self.logger.error(f"Error processing {mmd_file.name}: {e}")

    def _parse_mermaid_file(self, mermaid_content):
        """Parse mermaid file content, extracting config and diagram content."""
        # Check for YAML frontmatter
        if mermaid_content.strip().startswith("---"):
            parts = mermaid_content.split("---", 2)
            if len(parts) >= 3:
                # Has frontmatter - extract diagram content only
                diagram_content = parts[2].strip()
            else:
                # Malformed frontmatter - use entire content
                diagram_content = mermaid_content
        else:
            # No frontmatter - use entire content
            diagram_content = mermaid_content

        return diagram_content

    def _fix_svg_dimensions(self, svg_content):
        """Fix SVG dimensions from mermaid.ink for better compatibility.

        Mermaid.ink returns SVGs with width="100%" which some processors can't handle.
        Extract dimensions from viewBox and set explicit width/height.
        """
        try:
            # Extract viewBox dimensions using regex
            viewbox_match = re.search(r'viewBox="([^"]*)"', svg_content)
            if viewbox_match:
                viewbox = viewbox_match.group(1).split()
                if len(viewbox) >= 4:
                    width = float(viewbox[2])
                    height = float(viewbox[3])

                    # Replace width="100%" with explicit dimensions
                    svg_content = re.sub(r'width="100%"', f'width="{width}px"', svg_content)

                    # Add height if missing
                    if "height=" not in svg_content:
                        svg_content = re.sub(
                            r'(<svg[^>]*width="[^"]*")',
                            r'\1 height="' + f'{height}px"',
                            svg_content,
                        )

            return svg_content

        except Exception as e:
            print(f"     Warning: Could not fix SVG dimensions: {e}")
            return svg_content

    def _generate_mermaid_with_api(self, mermaid_content, svg_output_file, diagram_name):
        """Generate mermaid diagram in all formats using mermaid.ink API."""
        try:
            if requests is None:
                print("  ⚠️  requests library not available")
                print(f"     Creating placeholder SVG for: {diagram_name}")
                self._create_placeholder_svg(
                    svg_output_file,
                    diagram_name,
                    "requests library not available for mermaid.ink API",
                )
                return True

            print(f"  🌐 Generating all formats using mermaid.ink API: {diagram_name}")

            # Parse mermaid file content
            diagram_content = self._parse_mermaid_file(mermaid_content)

            # Encode the mermaid content for the API
            diagram_bytes = diagram_content.encode("utf-8")
            base64_string = base64.urlsafe_b64encode(diagram_bytes).decode("ascii")

            # Prepare output paths
            figure_dir = svg_output_file.parent
            stem_name = svg_output_file.stem

            # Define format endpoints
            formats = {
                "svg": f"https://mermaid.ink/svg/{base64_string}",
                "png": f"https://mermaid.ink/img/{base64_string}?type=png",
                "pdf": f"https://mermaid.ink/pdf/{base64_string}?fit",
            }

            generated_files = []

            # Generate each format
            for format_type, api_url in formats.items():
                output_file = figure_dir / f"{stem_name}.{format_type}"

                print(f"     Requesting {format_type.upper()} from mermaid.ink...")

                try:
                    # Use retry logic for network requests
                    if get_with_retry is not None:
                        response = get_with_retry(api_url, max_attempts=3, timeout=30)
                    else:
                        response = requests.get(api_url, timeout=30)
                        response.raise_for_status()

                    # Write the content
                    if format_type == "svg":
                        # For SVG, we can still apply dimension fixes if needed
                        content = self._fix_svg_dimensions(response.text)
                        with open(output_file, "w", encoding="utf-8") as f:
                            f.write(content)
                    else:
                        # For PNG and PDF, write binary content directly
                        with open(output_file, "wb") as f:
                            f.write(response.content)

                    print(f"  ✅ Created {format_type.upper()}: {output_file}")
                    generated_files.append(f"{figure_dir.name}/{output_file.name}")

                except requests.exceptions.RequestException as e:
                    print(f"  ❌ Failed to generate {format_type.upper()}: {e}")
                    # Continue with other formats
                    continue

            if generated_files:
                print(f"     Total files generated: {', '.join(generated_files)}")
                return True
            else:
                print(f"  ❌ Failed to generate any formats for {diagram_name}")
                # Create placeholder SVG as fallback
                self._create_placeholder_svg(svg_output_file, diagram_name, "All mermaid.ink API requests failed")
                return False

        except Exception as e:
            print(f"  ❌ Error in mermaid.ink API generation: {e}")
            self._create_placeholder_svg(svg_output_file, diagram_name, f"Error generating mermaid diagram: {e}")
            return False

    def generate_python_figure(self, py_file):
        """Generate figure from Python script."""
        try:
            # Create subdirectory for this figure
            figure_dir = self.output_dir / py_file.stem
            figure_dir.mkdir(parents=True, exist_ok=True)

            # Check if figure needs regeneration (check for any output file)
            output_patterns = ["*.png", "*.pdf", "*.svg", "*.eps"]
            existing_outputs = []
            for pattern in output_patterns:
                existing_outputs.extend(figure_dir.glob(pattern))

            if existing_outputs and not self._should_regenerate_figure(py_file, existing_outputs[0]):
                print(f"  ⚡ Skipping {py_file.name}: cached version is up-to-date")
                return

            print(f"  🐍 Executing {py_file.name}...")

            # Execute the Python script - use container engine if engine is docker/podman

            if self.engine in ["docker", "podman"]:
                # Use container engine execution with centralized manager
                if self.container_engine is None:
                    raise RuntimeError(f"{self.engine.title()} engine not initialized")
                env = {"RXIV_FIGURE_OUTPUT_DIR": str(figure_dir.absolute())}

                result = self.container_engine.run_python_script(
                    script_file=py_file.resolve(),
                    working_dir=figure_dir.resolve(),
                    environment=env,
                )
            else:
                # Use local Python execution
                python_cmd = self.platform.python_cmd
                if "uv run" in python_cmd:
                    # For uv run, we need to run from the project root but change to the
                    # figure directory within the script execution
                    exec_code = (
                        f"import os; "
                        f"__file__ = '{py_file.absolute()}'; "
                        f"os.chdir('{figure_dir.absolute()}'); "
                        f"exec(open('{py_file.absolute()}').read())"
                    )
                    cmd = ["uv", "run", "python", "-c", exec_code]
                    # Run from current working directory (project root) not figure_dir
                    cwd = None
                else:
                    cmd = [python_cmd, str(py_file.absolute())]
                    # For other Python commands, run from figure directory
                    cwd = str(figure_dir.absolute())

                # Set environment variable to ensure script saves to correct location
                import os

                env = os.environ.copy()
                env["RXIV_FIGURE_OUTPUT_DIR"] = str(figure_dir.absolute())

                result = self.platform.run_command(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                    env=env,
                )

            if result.stdout:
                # Print any output from the script (like success messages)
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        print(f"     {line}")

            if result.returncode != 0:
                print(f"  ❌ Error executing {py_file.name}:")
                if result.stderr:
                    print(f"     {result.stderr}")
                return

            print("     Debug: Script executed successfully, now checking for files...")

            # Check for generated files by scanning the figure subdirectory
            # Add a small delay to ensure files are fully written in CI environments
            import time

            time.sleep(0.1)

            # Force filesystem sync
            import os

            os.sync() if hasattr(os, "sync") else None

            print(f"     Debug: About to scan directory: {figure_dir.absolute()}")
            print(f"     Debug: Directory exists: {figure_dir.exists()}")
            if figure_dir.exists():
                dir_contents = list(figure_dir.iterdir())
                print(f"     Debug: Directory contents: {dir_contents}")
            else:
                print("     Debug: Directory does not exist!")

            current_files = set()
            for ext in ["png", "pdf", "svg", "eps"]:
                # Use rglob to find files recursively in subdirectories
                found_files = list(figure_dir.rglob(f"*.{ext}"))
                current_files.update(found_files)
                file_names = [f.name for f in found_files]
                print(f"     Debug: Found {len(found_files)} {ext} files: {file_names}")

            # Look for files that might have been created by this script
            base_name = py_file.stem
            potential_files = []
            for file_path in current_files:
                # Check if filename contains the base name or is a common figure pattern
                if (
                    base_name.lower() in file_path.stem.lower()
                    or file_path.stem.lower().startswith("figure")
                    or file_path.stem.lower().startswith("fig")
                ):
                    potential_files.append(file_path)

            if potential_files:
                print("  ✅ Generated figures:")
                for gen_file in sorted(potential_files):
                    # Show relative path from the original figures directory
                    # figure_dir might be a subdirectory, so we need to get the path from the root FIGURES dir
                    try:
                        # Try to get relative path from the parent figures directory
                        figures_root = figure_dir.parent if figure_dir.parent.name == "FIGURES" else figure_dir
                        while figures_root.name != "FIGURES" and figures_root.parent != figures_root:
                            figures_root = figures_root.parent
                        if figures_root.name == "FIGURES":
                            rel_path = gen_file.relative_to(figures_root)
                        else:
                            rel_path = gen_file.relative_to(figure_dir)
                        print(f"     - {rel_path}")
                    except ValueError:
                        # Fallback: just show the filename
                        print(f"     - {gen_file.name}")
            else:
                print(f"  ⚠️  No output files detected for {py_file.name}")
                print(f"     Debug: Checked {len(current_files)} total files")
                print(f"     Debug: Base name pattern: {base_name.lower()}")
                if current_files:
                    available_files = [f.name for f in current_files]
                    print(f"     Debug: Available files: {available_files}")
                return

            # Update cache after successful generation
            self._update_figure_cache(py_file)

        except Exception as e:
            self.logger.error(f"Error executing {py_file.name}: {e}")

    def generate_r_figure(self, r_file):
        """Generate figure from R script."""
        try:
            # Check if Rscript is available (only for local execution)
            if self.engine != "docker" and not self._check_rscript():
                print(f"  ⚠️  Skipping {r_file.name}: Rscript not available")
                print("     Ensure R is installed and accessible in your PATH")
                print("Check https://www.r-project.org/ for installation instructions")
                return

            # Create subdirectory for this figure
            figure_dir = self.output_dir / r_file.stem
            figure_dir.mkdir(parents=True, exist_ok=True)

            # Check if figure needs regeneration (check for any output file)
            output_patterns = ["*.png", "*.pdf", "*.svg", "*.eps"]
            existing_outputs = []
            for pattern in output_patterns:
                existing_outputs.extend(figure_dir.glob(pattern))

            if existing_outputs and not self._should_regenerate_figure(r_file, existing_outputs[0]):
                print(f"  ⚡ Skipping {r_file.name}: cached version is up-to-date")
                return

            print(f"  📊 Executing {r_file.name}...")

            # Execute the R script - use container engine if engine is docker/podman

            if self.engine in ["docker", "podman"]:
                # Use container engine execution with centralized manager
                if self.container_engine is None:
                    raise RuntimeError(f"{self.engine.title()} engine not initialized")
                env = {"RXIV_FIGURE_OUTPUT_DIR": str(figure_dir.absolute())}

                result = self.container_engine.run_r_script(
                    script_file=r_file.resolve(),
                    working_dir=figure_dir.resolve(),
                    environment=env,
                )
            else:
                # Use local R execution
                cmd = f"Rscript {str(r_file.absolute())}"

                # Set environment variable to ensure script saves to correct location
                import os

                env = os.environ.copy()
                env["RXIV_FIGURE_OUTPUT_DIR"] = str(figure_dir.absolute())

                result = self.platform.run_command(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(figure_dir.absolute()),
                    env=env,
                )

            if result.stdout:
                # Print any output from the script (like success messages)
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        print(f"     {line}")

            if result.returncode != 0:
                print(f"  ❌ Error executing {r_file.name}:")
                if result.stderr:
                    print(f"     {result.stderr}")
                return

            # Check for generated files by scanning the figure subdirectory
            current_files = set()
            for ext in ["png", "pdf", "svg", "eps"]:
                current_files.update(figure_dir.glob(f"*.{ext}"))

            # Look for files that might have been created by this script
            base_name = r_file.stem
            potential_files = []
            for file_path in current_files:
                # Check if filename contains the base name or is a common figure pattern
                if (
                    base_name.lower() in file_path.stem.lower()
                    or file_path.stem.lower().startswith("figure")
                    or file_path.stem.lower().startswith("fig")
                ):
                    potential_files.append(file_path)

            if potential_files:
                print("  ✅ Generated figures:")
                for gen_file in sorted(potential_files):
                    # Show relative path from the original figures directory
                    try:
                        # Try to get relative path from the parent figures directory
                        figures_root = figure_dir.parent if figure_dir.parent.name == "FIGURES" else figure_dir
                        while figures_root.name != "FIGURES" and figures_root.parent != figures_root:
                            figures_root = figures_root.parent

                        if figures_root.name == "FIGURES":
                            rel_path = gen_file.relative_to(figures_root)
                        else:
                            rel_path = gen_file.relative_to(figure_dir)
                        print(f"     - {rel_path}")
                    except ValueError:
                        # Fallback: just show the filename
                        print(f"     - {gen_file.name}")
            else:
                print(f"  ⚠️  No output files detected for {r_file.name}")
                return

            # Update cache after successful generation
            self._update_figure_cache(r_file)

        except Exception as e:
            print(f"  ❌ Error executing {r_file.name}: {e}")

    def _import_matplotlib(self):
        """Safely import matplotlib."""
        try:
            import matplotlib

            # Use non-interactive backend for headless operation
            matplotlib.use("Agg")
            return matplotlib
        except ImportError:
            print("  ⚠️  matplotlib not available for Python figures")
            return None

    def _import_seaborn(self):
        """Safely import seaborn."""
        try:
            import seaborn as sns

            return sns
        except ImportError:
            print("  ⚠️  seaborn not available")
            return None

    def _import_numpy(self):
        """Safely import numpy."""
        try:
            import numpy as np

            return np
        except ImportError:
            print("  ⚠️  numpy not available")
            return None

    def _import_pandas(self):
        """Safely import pandas."""
        try:
            import pandas as pd

            return pd
        except ImportError:
            print("  ⚠️  pandas not available")
            return None

    def _check_rscript(self):
        """Check if Rscript is available."""
        return self.platform.check_command_exists("Rscript")

    def _create_placeholder_svg(self, svg_path, diagram_name, error_message):
        """Create a placeholder SVG when mermaid generation fails."""
        # Truncate long error messages for readability
        if len(error_message) > 200:
            error_message = error_message[:200] + "..."

        # Escape XML special characters
        error_message = (
            error_message.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

        placeholder_svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <style>
            .title-text {{ font-family: Arial, sans-serif; font-size: 16px; font-weight: bold; fill: #d32f2f; }}
            .error-text {{ font-family: monospace; font-size: 10px; fill: #666; }}
            .note-text {{ font-family: Arial, sans-serif; font-size: 12px; fill: #1976d2; }}
            .border {{ fill: none; stroke: #d32f2f; stroke-width: 2; stroke-dasharray: 5,5; }}
        </style>
    </defs>

    <!-- Border -->
    <rect x="10" y="10" width="380" height="280" class="border"/>

    <!-- Title -->
    <text x="200" y="40" text-anchor="middle" class="title-text">
        ⚠️ Mermaid Diagram Error
    </text>

    <!-- Diagram name -->
    <text x="200" y="65" text-anchor="middle" class="note-text">
        Diagram: {diagram_name}
    </text>

    <!-- Error message -->
    <text x="30" y="100" class="error-text">Error:</text>
    <text x="30" y="115" class="error-text">{error_message}</text>

    <!-- Instructions -->
    <text x="200" y="160" text-anchor="middle" class="note-text">
        This placeholder was generated because mermaid
    </text>
    <text x="200" y="180" text-anchor="middle" class="note-text">
        diagram rendering failed. To fix this:
    </text>
    <text x="200" y="210" text-anchor="middle" class="note-text">
        1. Install Chromium: apt-get install chromium-browser
    </text>
    <text x="200" y="230" text-anchor="middle" class="note-text">
        2. Or use alternative mermaid renderer
    </text>
    <text x="200" y="250" text-anchor="middle" class="note-text">
        3. Or convert diagram to static image
    </text>
</svg>"""

        try:
            svg_path.parent.mkdir(parents=True, exist_ok=True)
            svg_path.write_text(placeholder_svg, encoding="utf-8")
            # Use a safe path display that handles temporary directories
            try:
                relative_path = svg_path.relative_to(Path.cwd())
                print(f"  ✅ Created placeholder SVG: {relative_path}")
            except ValueError:
                # Path is not relative to cwd (e.g., in temp directory)
                print(f"  ✅ Created placeholder SVG: {svg_path}")
        except Exception as e:
            print(f"  ❌ Failed to create placeholder SVG: {e}")


# CLI integration
def main():
    """Main function for CLI integration."""
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Generate figures from source files")
    parser.add_argument("--figures-dir", default="FIGURES", help="Directory with source figures")
    parser.add_argument("--output-dir", default="FIGURES", help="Output directory")
    parser.add_argument("--format", default="png", help="Output format (png, svg, pdf, eps)")
    parser.add_argument("--r-only", action="store_true", help="Process only R files")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--parallel",
        action="store_true",
        default=True,
        help="Enable parallel processing (default: True)",
    )
    parser.add_argument("--no-parallel", action="store_true", help="Disable parallel processing")
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of parallel workers (default: 4)",
    )
    parser.add_argument(
        "--engine",
        default=os.environ.get("RXIV_ENGINE", "local"),
        choices=["local", "docker"],
        help="Execution engine (local or docker, can be set via RXIV_ENGINE env var)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable content-based caching (regenerate all figures)",
    )
    parser.add_argument(
        "--manuscript-path",
        help="Path to manuscript directory (for caching, defaults to current directory)",
    )

    args = parser.parse_args()

    generator = FigureGenerator(
        figures_dir=args.figures_dir,
        output_dir=args.output_dir,
        output_format=args.format,
        r_only=args.r_only,
        engine=args.engine,
        enable_content_caching=not args.no_cache,
        manuscript_path=args.manuscript_path,
    )

    # Set verbose mode if specified
    if args.verbose:
        generator.verbose = args.verbose

    # Determine parallel processing settings
    use_parallel = args.parallel and not args.no_parallel
    max_workers = max(1, min(args.max_workers, 8))  # Limit to reasonable range

    generator.generate_all_figures(parallel=use_parallel, max_workers=max_workers)
    print("Figure generation complete!")


if __name__ == "__main__":
    main()
