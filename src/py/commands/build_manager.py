#!/usr/bin/env python3
"""Build manager for Rxiv-Maker.

This script orchestrates the complete build process including:
- Figure generation
- File copying
- LaTeX compilation
- PDF output management
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.platform import platform_detector


# Import FigureGenerator dynamically to avoid import issues
def get_figure_generator():
    """Get FigureGenerator class with lazy import."""
    from commands.generate_figures import FigureGenerator

    return FigureGenerator


class BuildManager:
    """Manage the complete build process."""

    def __init__(
        self,
        manuscript_path: str = None,
        output_dir: str = "output",
        force_figures: bool = False,
        skip_validation: bool = False,
        verbose: bool = False,
    ):
        """Initialize build manager.

        Args:
            manuscript_path: Path to manuscript directory
            output_dir: Output directory for generated files
            force_figures: Force regeneration of all figures
            skip_validation: Skip manuscript validation
            verbose: Enable verbose output
        """
        self.manuscript_path = manuscript_path or os.getenv(
            "MANUSCRIPT_PATH", "MANUSCRIPT"
        )
        self.output_dir = Path(output_dir)
        self.force_figures = force_figures
        self.skip_validation = skip_validation
        self.verbose = verbose
        self.platform = platform_detector

        # Set up paths
        self.manuscript_dir = Path(self.manuscript_path)
        self.figures_dir = self.manuscript_dir / "FIGURES"
        self.style_dir = Path("src/tex/style")
        self.references_bib = self.manuscript_dir / "03_REFERENCES.bib"

        # Output file names
        self.manuscript_name = Path(self.manuscript_path).name
        self.output_tex = self.output_dir / f"{self.manuscript_name}.tex"
        self.output_pdf = self.output_dir / f"{self.manuscript_name}.pdf"

    def log(self, message: str, level: str = "INFO"):
        """Log a message with appropriate formatting."""
        if level == "INFO":
            print(f"✅ {message}")
        elif level == "WARNING":
            print(f"⚠️  {message}")
        elif level == "ERROR":
            print(f"❌ {message}")
        elif level == "STEP":
            print(f"🔧 {message}")
        else:
            print(message)

    def setup_output_directory(self) -> bool:
        """Create and set up the output directory."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            (self.output_dir / "Figures").mkdir(parents=True, exist_ok=True)
            self.log(f"Output directory set up: {self.output_dir}")
            return True
        except Exception as e:
            self.log(f"Failed to create output directory: {e}", "ERROR")
            return False

    def check_manuscript_structure(self) -> bool:
        """Check if manuscript directory exists and has required structure."""
        if not self.manuscript_dir.exists():
            self.log(f"Manuscript directory not found: {self.manuscript_dir}", "ERROR")
            return False

        # Check for required files
        required_files = ["01_MAIN.md", "00_CONFIG.yml"]
        missing_files = []

        for file in required_files:
            if not (self.manuscript_dir / file).exists():
                missing_files.append(file)

        if missing_files:
            self.log(f"Missing required files: {', '.join(missing_files)}", "ERROR")
            return False

        # Create FIGURES directory if it doesn't exist
        if not self.figures_dir.exists():
            self.log("FIGURES directory not found, creating it...", "WARNING")
            try:
                self.figures_dir.mkdir(parents=True, exist_ok=True)
                self.log(f"Created FIGURES directory: {self.figures_dir}")
                self.log(
                    "💡 Add figure generation scripts (.py) or Mermaid diagrams (.mmd) to this directory"
                )
            except Exception as e:
                self.log(f"Failed to create FIGURES directory: {e}", "ERROR")
                return False

        return True

    def validate_manuscript(self) -> bool:
        """Run manuscript validation."""
        if self.skip_validation:
            self.log("Skipping manuscript validation")
            return True

        self.log("Running manuscript validation...", "STEP")

        try:
            # Use subprocess to run validation to avoid import issues
            cmd = [
                self.platform.python_cmd.split()[0],
                "src/py/commands/validate.py",
                self.manuscript_path,
            ]

            if "uv run" in self.platform.python_cmd:
                cmd = ["uv", "run", "python"] + cmd[1:]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.log("Validation completed successfully")
                if self.verbose and result.stdout:
                    print(result.stdout)
                return True
            else:
                self.log("Validation failed", "ERROR")
                if result.stderr:
                    print(result.stderr)
                return False

        except Exception as e:
            self.log(f"Validation error: {e}", "ERROR")
            return False

    def generate_figures(self) -> bool:
        """Generate figures from source files."""
        self.log("Checking figure generation...", "STEP")

        if not self.figures_dir.exists():
            self.log("No FIGURES directory found, skipping figure generation")
            return True

        # Check if we need to generate figures
        need_figures = self.force_figures or self._check_figures_need_update()

        if not need_figures:
            self.log("Figures are up to date")
            return True

        self.log("Generating figures...", "STEP")

        try:
            # Get FigureGenerator class
            FigureGenerator = get_figure_generator()

            # Generate Mermaid and Python figures
            figure_gen = FigureGenerator(
                figures_dir=str(self.figures_dir),
                output_dir=str(self.figures_dir),
                output_format="pdf",
            )
            figure_gen.generate_all_figures()

            # Generate R figures if any
            r_figure_gen = FigureGenerator(
                figures_dir=str(self.figures_dir),
                output_dir=str(self.figures_dir),
                output_format="pdf",
                r_only=True,
            )
            r_figure_gen.generate_all_figures()

            self.log("Figure generation completed")
            return True

        except Exception as e:
            self.log(f"Figure generation failed: {e}", "ERROR")
            return False

    def _check_figures_need_update(self) -> bool:
        """Check if figures need to be updated."""
        if not self.figures_dir.exists():
            return False

        # Check for source files that need processing
        source_files = (
            list(self.figures_dir.glob("*.mmd"))
            + list(self.figures_dir.glob("*.py"))
            + list(self.figures_dir.glob("*.R"))
        )

        for source_file in source_files:
            base_name = source_file.stem
            output_dir = self.figures_dir / base_name

            if source_file.suffix == ".mmd":
                output_file = output_dir / f"{base_name}.pdf"
            else:
                output_file = output_dir / f"{base_name}.png"

            # Check if output file exists and is newer than source
            if not output_file.exists():
                return True

            if source_file.stat().st_mtime > output_file.stat().st_mtime:
                return True

        return False

    def copy_style_files(self) -> bool:
        """Copy LaTeX style files to output directory."""
        self.log("Copying style files...", "STEP")

        if not self.style_dir.exists():
            self.log(
                "Style directory not found, skipping style file copying", "WARNING"
            )
            return True

        # Copy style files
        style_extensions = ["*.cls", "*.bst", "*.sty"]
        copied_files = []

        for pattern in style_extensions:
            for file in self.style_dir.glob(pattern):
                try:
                    dest = self.output_dir / file.name
                    dest.write_bytes(file.read_bytes())
                    copied_files.append(file.name)
                except Exception as e:
                    self.log(f"Failed to copy {file.name}: {e}", "WARNING")

        if copied_files:
            self.log(f"Copied style files: {', '.join(copied_files)}")
        else:
            self.log("No style files found to copy")

        return True

    def copy_references(self) -> bool:
        """Copy references bibliography file to output directory."""
        if self.references_bib.exists():
            try:
                dest = self.output_dir / "03_REFERENCES.bib"
                dest.write_bytes(self.references_bib.read_bytes())
                self.log(f"Copied references: {self.references_bib.name}")
            except Exception as e:
                self.log(f"Failed to copy references: {e}", "WARNING")

        return True

    def copy_figures(self) -> bool:
        """Copy figure files to output directory."""
        if not self.figures_dir.exists():
            return True

        self.log("Copying figure files...", "STEP")

        figures_output = self.output_dir / "Figures"
        copied_files = []

        # Copy all files from FIGURES directory
        for item in self.figures_dir.iterdir():
            if item.is_file():
                try:
                    dest = figures_output / item.name
                    dest.write_bytes(item.read_bytes())
                    copied_files.append(item.name)
                except Exception as e:
                    self.log(f"Failed to copy {item.name}: {e}", "WARNING")
            elif item.is_dir():
                # Copy figure subdirectories
                try:
                    dest_dir = figures_output / item.name
                    dest_dir.mkdir(parents=True, exist_ok=True)

                    for sub_item in item.iterdir():
                        if sub_item.is_file():
                            dest_file = dest_dir / sub_item.name
                            dest_file.write_bytes(sub_item.read_bytes())
                            copied_files.append(f"{item.name}/{sub_item.name}")
                except Exception as e:
                    self.log(f"Failed to copy directory {item.name}: {e}", "WARNING")

        if copied_files:
            self.log(f"Copied {len(copied_files)} figure files")

        return True

    def generate_tex_files(self) -> bool:
        """Generate LaTeX files from manuscript."""
        self.log("Generating LaTeX files...", "STEP")

        try:
            # Run the main generation script
            cmd = [
                self.platform.python_cmd.split()[0],  # Handle "uv run python"
                "src/py/commands/generate_preprint.py",
                "--output-dir",
                str(self.output_dir),
            ]

            if "uv run" in self.platform.python_cmd:
                cmd = ["uv", "run", "python"] + cmd[1:]

            # Set environment variables
            env = os.environ.copy()
            env["MANUSCRIPT_PATH"] = self.manuscript_path

            result = subprocess.run(cmd, capture_output=True, text=True, env=env)

            if result.returncode == 0:
                self.log("LaTeX files generated successfully")
                if self.verbose and result.stdout:
                    print(result.stdout)
                return True
            else:
                self.log(f"LaTeX generation failed: {result.stderr}", "ERROR")
                return False

        except Exception as e:
            self.log(f"Error generating LaTeX files: {e}", "ERROR")
            return False

    def compile_pdf(self) -> bool:
        """Compile LaTeX to PDF."""
        self.log("Compiling LaTeX to PDF...", "STEP")

        # Change to output directory for compilation
        original_cwd = os.getcwd()

        try:
            os.chdir(self.output_dir)

            # Run pdflatex multiple times for proper cross-references
            tex_file = f"{self.manuscript_name}.tex"

            # First pass
            result1 = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_file],
                capture_output=True,
                text=True,
            )

            # Run bibtex if references exist (check in current working directory which is output_dir)
            output_references = Path("03_REFERENCES.bib")
            if output_references.exists():
                self.log("Running BibTeX to process bibliography...")
                bibtex_result = subprocess.run(
                    ["bibtex", self.manuscript_name], capture_output=True, text=True
                )

                # Log BibTeX warnings and errors only
                if bibtex_result.stderr:
                    self.log(f"BibTeX errors: {bibtex_result.stderr}", "WARNING")
                elif "warning" in bibtex_result.stdout.lower():
                    # Count warnings but don't spam the output
                    warning_count = bibtex_result.stdout.lower().count("warning")
                    self.log(
                        f"BibTeX completed with {warning_count} warning(s)", "WARNING"
                    )

                # Check for serious bibtex errors that would prevent citation resolution
                if bibtex_result.returncode != 0:
                    self.log(
                        f"BibTeX returned error code {bibtex_result.returncode}",
                        "WARNING",
                    )
                    # Check if .bbl file was still created despite errors
                    bbl_file = Path(f"{self.manuscript_name}.bbl")
                    if not bbl_file.exists():
                        self.log(
                            "BibTeX failed to create .bbl file - citations will appear as ?",
                            "ERROR",
                        )
                        return False
                else:
                    self.log("BibTeX completed successfully")

            # Second pass
            result2 = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_file],
                capture_output=True,
                text=True,
            )

            # Third pass
            result3 = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_file],
                capture_output=True,
                text=True,
            )

            # Check if compilation was successful (PDF exists is more reliable than return code)
            # Check for PDF in current directory (we're in output_dir)
            pdf_file = Path(f"{self.manuscript_name}.pdf")

            if pdf_file.exists():
                self.log("PDF compilation successful")
                # Show warnings if any, but don't fail the build
                if result3.returncode != 0 and self.verbose:
                    self.log("LaTeX completed with warnings:", "WARNING")
                    if result3.stdout:
                        print("LaTeX output:")
                        print(
                            result3.stdout[-2000:]
                        )  # Show last 2000 chars to avoid spam
                return True
            else:
                self.log("PDF compilation failed", "ERROR")
                if self.verbose:
                    self.log(f"Looking for PDF: {pdf_file.absolute()}")
                    self.log(f"Current directory: {Path.cwd()}")
                    print("LaTeX output:")
                    print(result3.stdout)
                    print("LaTeX errors:")
                    print(result3.stderr)
                return False

        except Exception as e:
            self.log(f"Error compiling PDF: {e}", "ERROR")
            return False
        finally:
            os.chdir(original_cwd)

    def copy_pdf_to_manuscript(self) -> bool:
        """Copy generated PDF to manuscript directory with custom name."""
        try:
            # Use the existing copy_pdf command
            cmd = [
                self.platform.python_cmd.split()[0],
                "src/py/commands/copy_pdf.py",
                "--output-dir",
                str(self.output_dir),
            ]

            if "uv run" in self.platform.python_cmd:
                cmd = ["uv", "run", "python"] + cmd[1:]

            # Set environment variables
            env = os.environ.copy()
            env["MANUSCRIPT_PATH"] = self.manuscript_path

            result = subprocess.run(cmd, capture_output=True, text=True, env=env)

            if result.returncode == 0:
                self.log("PDF copied to manuscript directory")
                return True
            else:
                self.log(f"Failed to copy PDF: {result.stderr}", "ERROR")
                return False

        except Exception as e:
            self.log(f"Error copying PDF: {e}", "ERROR")
            return False

    def run_word_count_analysis(self) -> bool:
        """Run word count analysis on the manuscript."""
        try:
            # Use the existing word count analysis command
            cmd = [
                self.platform.python_cmd.split()[0],
                "src/py/commands/analyze_word_count.py",
            ]

            if "uv run" in self.platform.python_cmd:
                cmd = ["uv", "run", "python"] + cmd[1:]

            # Set environment variables
            env = os.environ.copy()
            env["MANUSCRIPT_PATH"] = self.manuscript_path

            result = subprocess.run(cmd, capture_output=True, text=True, env=env)

            if result.returncode == 0:
                # Print the word count analysis output
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                self.log(f"Word count analysis failed: {result.stderr}", "WARNING")
                return False

        except Exception as e:
            self.log(f"Error running word count analysis: {e}", "WARNING")
            return False

    def run_full_build(self) -> bool:
        """Run the complete build process."""
        self.log(
            f"Starting build process for manuscript: {self.manuscript_path}", "STEP"
        )

        # Step 1: Check manuscript structure
        if not self.check_manuscript_structure():
            return False

        # Step 2: Set up output directory
        if not self.setup_output_directory():
            return False

        # Step 3: Generate figures (before validation to ensure figure files exist)
        if not self.generate_figures():
            return False

        # Step 4: Validate manuscript (if not skipped)
        if not self.validate_manuscript():
            return False

        # Step 5: Copy style files
        if not self.copy_style_files():
            return False

        # Step 6: Copy references
        if not self.copy_references():
            return False

        # Step 7: Copy figures
        if not self.copy_figures():
            return False

        # Step 8: Generate LaTeX files
        if not self.generate_tex_files():
            return False

        # Step 9: Compile PDF
        if not self.compile_pdf():
            return False

        # Step 10: Copy PDF to manuscript directory
        if not self.copy_pdf_to_manuscript():
            return False

        # Step 11: Run word count analysis
        self.run_word_count_analysis()

        # Success!
        self.log(f"Build completed successfully: {self.output_pdf}")
        return True


def main():
    """Main entry point for build manager."""
    parser = argparse.ArgumentParser(description="Build manager for Rxiv-Maker")
    parser.add_argument(
        "--manuscript-path", default=None, help="Path to manuscript directory"
    )
    parser.add_argument(
        "--output-dir", default="output", help="Output directory for generated files"
    )
    parser.add_argument(
        "--force-figures", action="store_true", help="Force regeneration of all figures"
    )
    parser.add_argument(
        "--skip-validation", action="store_true", help="Skip manuscript validation"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    try:
        build_manager = BuildManager(
            manuscript_path=args.manuscript_path,
            output_dir=args.output_dir,
            force_figures=args.force_figures,
            skip_validation=args.skip_validation,
            verbose=args.verbose,
        )

        success = build_manager.run_full_build()

        if success:
            return 0
        else:
            print("❌ Build failed!")
            return 1

    except KeyboardInterrupt:
        print("\n❌ Build interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
