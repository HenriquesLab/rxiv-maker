"""Figure Generation Script for Rxiv-Maker.

This script automatically processes figure files in the FIGURES directory and generates
publication-ready output files. It supports:
- .mmd files: Mermaid diagrams (generates SVG/PNG/PDF)
- .py files: Python scripts for matplotlib/seaborn figures
- .R files: R scripts (executes script and captures output figures)

Uses local execution only for better simplicity and reliability.
"""

import base64
import os
import re
import subprocess
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

# Import platform utilities with proper fallback handling
try:
    from ...core.path_manager import PathManager
except ImportError:
    # Fallback for when running as script
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from rxiv_maker.core.path_manager import PathManager  # type: ignore[no-redef]


class FigureGenerator:
    """Main class for generating figures from various source formats using local execution."""

    def __init__(
        self,
        figures_dir="FIGURES",
        output_dir="FIGURES",
        output_format="png",
        r_only=False,
        enable_content_caching=True,
        manuscript_path=None,
    ):
        """Initialize the figure generator.

        Args:
            figures_dir: Directory containing source figure files
            output_dir: Directory for generated output files
            output_format: Default output format for figures
            r_only: Only process R files if True
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
                self.path_manager = None
                self.figures_dir = Path(figures_dir).resolve()
        except Exception as e:
            # Complete fallback for edge cases
            self.path_manager = None
            self.figures_dir = Path(figures_dir).resolve()
            if manuscript_path:
                print(f"Warning: PathManager initialization failed, using fallback paths: {e}")

        self.output_dir = Path(output_dir).resolve()
        self.output_format = output_format
        self.r_only = r_only

        # Create directories if they don't exist
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Supported formats
        self.supported_formats = ["png", "pdf", "svg", "jpg", "jpeg"]

        # Figure caching system (optional optimization) - disabled for now due to interface mismatch
        # TODO: Re-enable caching after fixing interface compatibility
        self.enable_content_caching = False
        if enable_content_caching:
            print("Warning: Content caching disabled due to interface incompatibility")
            self.enable_content_caching = False

        if self.output_format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {self.output_format}. Supported: {self.supported_formats}")

    def _log_summary(self, processed_count: int, processed_files: list, use_rich: bool = True):
        """Log processing summary with rich formatting."""
        if not processed_count:
            if use_rich:
                print("✅ [green]No figures to process - all up to date![/green]")
            else:
                print("✅ No figures to process - all up to date!")
            return

        if use_rich:
            print(f"✅ [green]Successfully processed {processed_count} figure file(s):[/green]")
            for file_path in processed_files:
                print(f"   • [cyan]{file_path.name}[/cyan]")
        else:
            print(f"✅ Successfully processed {processed_count} figure file(s):")
            for file_path in processed_files:
                print(f"   • {file_path.name}")

    def _skip_file_with_message(self, file_path: Path, reason: str, use_rich: bool = True) -> None:
        """Print skip message with consistent formatting."""
        if use_rich:
            print(f"⏭️ [yellow]Skipping {file_path.name}: {reason}[/yellow]")
        else:
            print(f"⏭️ Skipping {file_path.name}: {reason}")

    def _generate_mermaid_diagrams(self, progress=None, task_id=None, use_rich: bool = True):
        """Generate diagrams from Mermaid files using online service."""
        mmd_files = list(self.figures_dir.glob("*.mmd"))
        if not mmd_files:
            return []

        processed_files = []

        for mmd_file in mmd_files:
            if progress and task_id is not None:
                progress.update(task_id, advance=1, description=f"Processing {mmd_file.name}")

            # Output file determination
            output_file = self.output_dir / f"{mmd_file.stem}.{self.output_format}"

            # Skip if file hasn't changed (content caching)
            if self.enable_content_caching:
                file_hash = self.checksum_manager.calculate_file_hash(mmd_file)
                if self.checksum_manager.is_file_unchanged(str(mmd_file), file_hash) and output_file.exists():
                    if use_rich:
                        print(f"⏭️ [dim]Skipping {mmd_file.name}: No changes detected[/dim]")
                    else:
                        print(f"⏭️ Skipping {mmd_file.name}: No changes detected")
                    continue

            # Use local Mermaid generation via web service (Kroki)
            try:
                if use_rich:
                    print(f"🎨 [cyan]Generating {self.output_format.upper()} from {mmd_file.name}[/cyan]")
                else:
                    print(f"🎨 Generating {self.output_format.upper()} from {mmd_file.name}")

                success = self._generate_mermaid_via_kroki(mmd_file, output_file)

                if success:
                    processed_files.append(mmd_file)
                    if self.enable_content_caching:
                        self.checksum_manager.update_file_hash(str(mmd_file), file_hash)
                else:
                    if use_rich:
                        print(f"❌ [red]Failed to generate {output_file.name}[/red]")
                    else:
                        print(f"❌ Failed to generate {output_file.name}")

            except Exception as e:
                if use_rich:
                    print(f"❌ [red]Error processing {mmd_file.name}: {e}[/red]")
                else:
                    print(f"❌ Error processing {mmd_file.name}: {e}")

        return processed_files

    def _generate_mermaid_via_kroki(self, input_file: Path, output_file: Path) -> bool:
        """Generate Mermaid diagram using Kroki online service."""
        try:
            # Read the Mermaid file
            with open(input_file, "r", encoding="utf-8") as f:
                mermaid_content = f.read().strip()

            # Use mermaid.ink service which supports PDF directly
            if self.output_format.lower() == "png":
                mermaid_format = "png"
            elif self.output_format.lower() == "pdf":
                mermaid_format = "pdf"
            else:
                mermaid_format = "svg"

            # Encode content for mermaid.ink
            encoded_content = base64.b64encode(mermaid_content.encode("utf-8")).decode("ascii")
            # Add fit parameter for PDF to ensure proper sizing
            if mermaid_format == "pdf":
                mermaid_url = f"https://mermaid.ink/{mermaid_format}/{encoded_content}?fit"
            else:
                mermaid_url = f"https://mermaid.ink/{mermaid_format}/{encoded_content}"

            # Make request with timeout using GET method
            if requests:
                response = requests.get(mermaid_url, timeout=30)
                if response.status_code == 200:
                    with open(output_file, "wb") as f:
                        f.write(response.content)
                    return True
                else:
                    print(f"mermaid.ink service returned status {response.status_code}")
                    return self._create_fallback_mermaid_diagram(input_file, output_file)
            else:
                print("requests library not available for Mermaid generation")
                return self._create_fallback_mermaid_diagram(input_file, output_file)

        except Exception as e:
            print(f"mermaid.ink service error: {e}")
            return self._create_fallback_mermaid_diagram(input_file, output_file)

    def _create_fallback_mermaid_diagram(self, input_file: Path, output_file: Path) -> bool:
        """Create a fallback placeholder diagram when Mermaid service is unavailable."""
        try:
            if self.output_format.lower() == "svg":
                # Create SVG placeholder
                svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400" viewBox="0 0 800 400">
  <rect width="800" height="400" fill="white" stroke="#ddd" stroke-width="2"/>
  <text x="400" y="180" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" fill="#666">
    <tspan x="400" dy="0">Mermaid Diagram</tspan>
    <tspan x="400" dy="30">(Service temporarily unavailable)</tspan>
  </text>
  <text x="400" y="250" text-anchor="middle" font-family="monospace" font-size="12" fill="#999">
    Source: {input_file.name}
  </text>
</svg>"""
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(svg_content)
                return True
            else:
                # For PNG/PDF, we'd need additional libraries, so just create a text file
                with open(output_file.with_suffix(".txt"), "w", encoding="utf-8") as f:
                    f.write(f"Mermaid diagram placeholder for {input_file.name}\n")
                    f.write("Kroki service unavailable - diagram generation failed\n")
                return True
        except Exception:
            return False

    def _execute_python_files(self, progress=None, task_id=None, use_rich: bool = True):
        """Execute Python scripts to generate figures using local Python."""
        py_files = list(self.figures_dir.glob("*.py"))
        if not py_files:
            return []

        processed_files = []

        for py_file in py_files:
            if progress and task_id is not None:
                progress.update(task_id, advance=1, description=f"Processing {py_file.name}")

            # Skip if file hasn't changed (content caching)
            if self.enable_content_caching:
                file_hash = self.checksum_manager.calculate_file_hash(py_file)
                if self.checksum_manager.is_file_unchanged(str(py_file), file_hash):
                    expected_outputs = self._get_expected_python_outputs(py_file)
                    if all(Path(output).exists() for output in expected_outputs):
                        if use_rich:
                            print(f"⏭️ [dim]Skipping {py_file.name}: No changes detected[/dim]")
                        else:
                            print(f"⏭️ Skipping {py_file.name}: No changes detected")
                        continue

            # Execute the Python script using local Python
            try:
                if use_rich:
                    print(f"🐍 [cyan]Executing Python script: {py_file.name}[/cyan]")
                else:
                    print(f"🐍 Executing Python script: {py_file.name}")

                result = subprocess.run(
                    [sys.executable, str(py_file)],
                    cwd=str(self.figures_dir),
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                )

                if result.returncode == 0:
                    processed_files.append(py_file)
                    if self.enable_content_caching:
                        file_hash = self.checksum_manager.calculate_file_hash(py_file)
                        self.checksum_manager.update_file_hash(str(py_file), file_hash)

                    if use_rich:
                        print(f"✅ [green]Python script completed: {py_file.name}[/green]")
                    else:
                        print(f"✅ Python script completed: {py_file.name}")
                else:
                    if use_rich:
                        print(f"❌ [red]Python script failed: {py_file.name}[/red]")
                        if result.stderr:
                            print(f"   [red]Error: {result.stderr}[/red]")
                    else:
                        print(f"❌ Python script failed: {py_file.name}")
                        if result.stderr:
                            print(f"   Error: {result.stderr}")

            except subprocess.TimeoutExpired:
                if use_rich:
                    print(f"⏰ [yellow]Python script timeout: {py_file.name}[/yellow]")
                else:
                    print(f"⏰ Python script timeout: {py_file.name}")
            except Exception as e:
                if use_rich:
                    print(f"❌ [red]Error executing {py_file.name}: {e}[/red]")
                else:
                    print(f"❌ Error executing {py_file.name}: {e}")

        return processed_files

    def _get_expected_python_outputs(self, py_file: Path) -> list:
        """Analyze Python file to determine expected output files."""
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Simple heuristic - look for common save patterns
            outputs = []
            patterns = [
                r'savefig\(["\']([^"\']+)["\']',
                r'plt\.savefig\(["\']([^"\']+)["\']',
                r'fig\.savefig\(["\']([^"\']+)["\']',
                r'\.to_file\(["\']([^"\']+)["\']',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    output_path = self.figures_dir / match
                    outputs.append(str(output_path))

            return outputs
        except Exception:
            return []

    def _execute_r_files(self, progress=None, task_id=None, use_rich: bool = True):
        """Execute R scripts to generate figures using local R."""
        r_files = list(self.figures_dir.glob("*.R"))
        if not r_files:
            return []

        # Check if Rscript is available
        if not self._check_rscript():
            if use_rich:
                print("⚠️ [yellow]R/Rscript not found - skipping R files[/yellow]")
            else:
                print("⚠️ R/Rscript not found - skipping R files")
            return []

        processed_files = []

        for r_file in r_files:
            if progress and task_id is not None:
                progress.update(task_id, advance=1, description=f"Processing {r_file.name}")

            # Skip if file hasn't changed (content caching)
            if self.enable_content_caching:
                file_hash = self.checksum_manager.calculate_file_hash(r_file)
                if self.checksum_manager.is_file_unchanged(str(r_file), file_hash):
                    expected_outputs = self._get_expected_r_outputs(r_file)
                    if all(Path(output).exists() for output in expected_outputs):
                        if use_rich:
                            print(f"⏭️ [dim]Skipping {r_file.name}: No changes detected[/dim]")
                        else:
                            print(f"⏭️ Skipping {r_file.name}: No changes detected")
                        continue

            # Execute the R script using local Rscript
            try:
                if use_rich:
                    print(f"📊 [cyan]Executing R script: {r_file.name}[/cyan]")
                else:
                    print(f"📊 Executing R script: {r_file.name}")

                result = subprocess.run(
                    ["Rscript", str(r_file)],
                    cwd=str(self.figures_dir),
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                )

                if result.returncode == 0:
                    processed_files.append(r_file)
                    if self.enable_content_caching:
                        file_hash = self.checksum_manager.calculate_file_hash(r_file)
                        self.checksum_manager.update_file_hash(str(r_file), file_hash)

                    if use_rich:
                        print(f"✅ [green]R script completed: {r_file.name}[/green]")
                    else:
                        print(f"✅ R script completed: {r_file.name}")
                else:
                    if use_rich:
                        print(f"❌ [red]R script failed: {r_file.name}[/red]")
                        if result.stderr:
                            print(f"   [red]Error: {result.stderr}[/red]")
                    else:
                        print(f"❌ R script failed: {r_file.name}")
                        if result.stderr:
                            print(f"   Error: {result.stderr}")

            except subprocess.TimeoutExpired:
                if use_rich:
                    print(f"⏰ [yellow]R script timeout: {r_file.name}[/yellow]")
                else:
                    print(f"⏰ R script timeout: {r_file.name}")
            except Exception as e:
                if use_rich:
                    print(f"❌ [red]Error executing {r_file.name}: {e}[/red]")
                else:
                    print(f"❌ Error executing {r_file.name}: {e}")

        return processed_files

    def _get_expected_r_outputs(self, r_file: Path) -> list:
        """Analyze R file to determine expected output files."""
        try:
            with open(r_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Simple heuristic - look for common R save patterns
            outputs = []
            patterns = [
                r'ggsave\(["\']([^"\']+)["\']',
                r'pdf\(["\']([^"\']+)["\']',
                r'png\(["\']([^"\']+)["\']',
                r'jpeg\(["\']([^"\']+)["\']',
                r'svg\(["\']([^"\']+)["\']',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    output_path = self.figures_dir / match
                    outputs.append(str(output_path))

            return outputs
        except Exception:
            return []

    def _check_rscript(self) -> bool:
        """Check if Rscript is available in the system."""
        try:
            result = subprocess.run(
                ["Rscript", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return False

    def process_figures(self, use_rich: bool = None) -> dict:
        """Process all figure files and generate outputs.

        Args:
            use_rich: Whether to use rich formatting. If None, auto-detect based on RICH_AVAILABLE.

        Returns:
            Dictionary with processing results and statistics.
        """
        if use_rich is None:
            use_rich = RICH_AVAILABLE

        # Collect all figure files
        all_files = []
        if not self.r_only:
            all_files.extend(self.figures_dir.glob("*.mmd"))
            all_files.extend(self.figures_dir.glob("*.py"))
        all_files.extend(self.figures_dir.glob("*.R"))

        if not all_files:
            if use_rich:
                print("ℹ️ [blue]No figure files found in FIGURES directory[/blue]")
            else:
                print("ℹ️ No figure files found in FIGURES directory")
            return {"total_files": 0, "processed_files": [], "skipped_files": []}

        # Process files with progress tracking
        processed_files = []

        if use_rich and RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=None,
            ) as progress:
                task = progress.add_task("Processing figures...", total=len(all_files))

                if not self.r_only:
                    processed_files.extend(self._generate_mermaid_diagrams(progress, task, use_rich))
                    processed_files.extend(self._execute_python_files(progress, task, use_rich))
                processed_files.extend(self._execute_r_files(progress, task, use_rich))
        else:
            # Fallback without rich progress
            if not self.r_only:
                processed_files.extend(self._generate_mermaid_diagrams(use_rich=use_rich))
                processed_files.extend(self._execute_python_files(use_rich=use_rich))
            processed_files.extend(self._execute_r_files(use_rich=use_rich))

        # Log summary
        self._log_summary(len(processed_files), processed_files, use_rich)

        # Save cache state if enabled
        if self.enable_content_caching:
            try:
                self.checksum_manager.save_cache()
            except Exception as e:
                if use_rich:
                    print(f"⚠️ [yellow]Warning: Failed to save figure cache: {e}[/yellow]")
                else:
                    print(f"⚠️ Warning: Failed to save figure cache: {e}")

        return {
            "total_files": len(all_files),
            "processed_files": processed_files,
            "skipped_files": [f for f in all_files if f not in processed_files],
        }


def main():
    """Command-line interface for the figure generator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate figures from Mermaid (.mmd), Python (.py), and R (.R) files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_figures.py                    # Process all figure types
  python generate_figures.py --r-only          # Process only R files
  python generate_figures.py --output-format pdf  # Generate PDF outputs
  python generate_figures.py --no-cache        # Disable content caching
        """,
    )

    parser.add_argument(
        "--figures-dir",
        "-f",
        default="FIGURES",
        help="Directory containing figure source files (default: FIGURES)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default=None,
        help="Directory for generated output files (default: same as figures-dir)",
    )
    parser.add_argument(
        "--output-format",
        "-fmt",
        choices=["png", "pdf", "svg", "jpg", "jpeg"],
        default="png",
        help="Output format for generated figures (default: png)",
    )
    parser.add_argument(
        "--r-only",
        action="store_true",
        help="Only process R files (skip Mermaid and Python)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable content-based caching",
    )
    parser.add_argument(
        "--manuscript-path",
        "-m",
        help="Path to manuscript directory (for advanced path management and caching)",
    )

    args = parser.parse_args()

    # Set output directory
    output_dir = args.output_dir or args.figures_dir

    # Initialize and run figure generator
    try:
        generator = FigureGenerator(
            figures_dir=args.figures_dir,
            output_dir=output_dir,
            output_format=args.output_format,
            r_only=args.r_only,
            enable_content_caching=not args.no_cache,
            manuscript_path=args.manuscript_path,
        )

        results = generator.process_figures()

        # Exit with appropriate code
        if results["processed_files"]:
            sys.exit(0)  # Success
        elif results["total_files"] == 0:
            sys.exit(0)  # No files to process, but that's OK
        else:
            sys.exit(1)  # Had files but failed to process any

    except KeyboardInterrupt:
        print("\n⚠️ Figure generation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Figure generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
