"""Build manager for rxiv-maker PDF generation pipeline."""

import os
import subprocess
from datetime import datetime
from pathlib import Path

from ..core.logging_config import get_logger, set_log_directory
from ..docker.manager import get_docker_manager
from ..utils.figure_checksum import get_figure_checksum_manager
from ..utils.operation_ids import create_operation
from ..utils.performance import get_performance_tracker
from ..utils.platform import platform_detector

logger = get_logger()


# Import FigureGenerator dynamically to avoid import issues
def get_figure_generator():
    """Get FigureGenerator class with lazy import."""
    try:
        from .generate_figures import FigureGenerator
    except ImportError:
        from generate_figures import FigureGenerator
    return FigureGenerator


class BuildManager:
    """Manage the complete build process."""

    def __init__(
        self,
        manuscript_path: str | None = None,
        output_dir: str = "output",
        force_figures: bool = False,
        skip_validation: bool = False,
        skip_pdf_validation: bool = False,
        verbose: bool = False,
        track_changes_tag: str | None = None,
        engine: str = "local",
    ):
        """Initialize build manager.

        Args:
            manuscript_path: Path to manuscript directory
            output_dir: Output directory for generated files
            force_figures: Force regeneration of all figures
            skip_validation: Skip manuscript validation
            skip_pdf_validation: Skip PDF validation
            verbose: Enable verbose output
            track_changes_tag: Git tag to track changes against
            engine: Execution engine ("local" or "docker")
        """
        self.manuscript_path: str = manuscript_path or os.getenv("MANUSCRIPT_PATH", "MANUSCRIPT")
        # Make output_dir absolute relative to manuscript directory
        self.manuscript_dir_path = Path(self.manuscript_path)
        if Path(output_dir).is_absolute():
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.manuscript_dir_path / output_dir
        self.force_figures = force_figures
        self.skip_validation = skip_validation
        self.skip_pdf_validation = skip_pdf_validation
        self.verbose = verbose
        self.track_changes_tag = track_changes_tag
        self.engine = engine
        self.platform = platform_detector

        # Initialize Docker manager if using docker engine
        self.docker_manager = None
        if self.engine == "docker":
            self.docker_manager = get_docker_manager(workspace_dir=Path.cwd().resolve())

        # Set up paths
        self.manuscript_dir = self.manuscript_dir_path
        self.figures_dir = self.manuscript_dir / "FIGURES"

        # Find project root (where src directory is located)
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        self.style_dir = project_root / "src" / "tex" / "style"
        self.copy_pdf_script = project_root / "src" / "rxiv_maker" / "engine" / "copy_pdf.py"
        self.analyze_word_count_script = project_root / "src" / "rxiv_maker" / "engine" / "analyze_word_count.py"
        self.pdf_validator_script = project_root / "src" / "rxiv_maker" / "validators" / "pdf_validator.py"

        self.references_bib = self.manuscript_dir / "03_REFERENCES.bib"

        # Output file names
        self.manuscript_name = Path(self.manuscript_path).name
        self.output_tex = self.output_dir / f"{self.manuscript_name}.tex"
        self.output_pdf = self.output_dir / f"{self.manuscript_name}.pdf"

        # Set up logging
        self.warnings_log = self.output_dir / "build_warnings.log"
        self.bibtex_log = self.output_dir / "bibtex_warnings.log"

        # Configure centralized logging to write to output directory
        set_log_directory(self.output_dir)

    def log(self, message: str, level: str = "INFO"):
        """Log a message with appropriate formatting."""
        if level == "INFO":
            logger.success(message)
        elif level == "WARNING":
            logger.warning(message)
            self._log_to_file(message, level)
        elif level == "ERROR":
            logger.error(message)
            self._log_to_file(message, level)
        elif level == "STEP":
            logger.debug(message)
        else:
            logger.info(message)

    def _log_to_file(self, message: str, level: str):
        """Log warnings and errors to files."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"

        try:
            with open(self.warnings_log, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception:
            pass  # Don't fail the build if logging fails

    def _log_bibtex_warnings(self):
        """Extract and log BibTeX warnings from .blg file."""
        blg_file = self.output_dir / f"{self.manuscript_name}.blg"
        if not blg_file.exists():
            return

        try:
            # Try UTF-8 first, then fall back to latin-1 for LaTeX log files
            try:
                with open(blg_file, encoding="utf-8") as f:
                    blg_content = f.read()
            except UnicodeDecodeError:
                with open(blg_file, encoding="latin-1") as f:
                    blg_content = f.read()

            # Extract warnings
            warnings = []
            for line in blg_content.split("\n"):
                if line.startswith("Warning--"):
                    warnings.append(line.replace("Warning--", "").strip())

            if warnings:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(self.bibtex_log, "w", encoding="utf-8") as f:
                    f.write(f"BibTeX Warnings Report - {timestamp}\n")
                    f.write("=" * 50 + "\n")
                    for i, warning in enumerate(warnings, 1):
                        f.write(f"{i}. {warning}\n")

                self.log(f"BibTeX warnings logged to {self.bibtex_log.name}", "INFO")
        except Exception:
            pass  # Don't fail the build if logging fails

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

        # Only create FIGURES directory if we're in a valid manuscript directory
        # that's being actively processed. Don't create FIGURES in default
        # "MANUSCRIPT" directory unless it's explicitly being used
        should_create_figures = not self.figures_dir.exists() and (
            self.manuscript_path != "MANUSCRIPT"
            or (
                self.manuscript_path == "MANUSCRIPT"
                and len([f for f in self.manuscript_dir.iterdir() if f.suffix in [".md", ".yml", ".bib"]]) > 2
            )
        )

        if should_create_figures:
            self.log("FIGURES directory not found, creating it...", "WARNING")
            try:
                self.figures_dir.mkdir(parents=True, exist_ok=True)
                self.log(f"Created FIGURES directory: {self.figures_dir}")
                self.log("💡 Add figure generation scripts (.py) or Mermaid diagrams (.mmd) to this directory")
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

        if self.engine == "docker":
            return self._validate_manuscript_docker()
        else:
            return self._validate_manuscript_local()

    def _validate_manuscript_docker(self) -> bool:
        """Run manuscript validation using Docker."""
        try:
            manuscript_path = Path(self.manuscript_path)

            # Convert to absolute path, then make relative to workspace directory
            manuscript_abs = manuscript_path.resolve()
            workspace_dir = self.docker_manager.workspace_dir

            try:
                manuscript_rel = manuscript_abs.relative_to(workspace_dir)
            except ValueError:
                # If manuscript is not within workspace, use just the name
                manuscript_rel = manuscript_path.name

            # Build validation command for Docker
            validation_cmd = [
                "python",
                "/workspace/src/rxiv_maker/commands/validate.py",
                str(manuscript_rel),
                "--detailed",
                "--check-latex",
            ]

            if self.verbose:
                validation_cmd.append("--verbose")

            result = self.docker_manager.run_command(command=validation_cmd, session_key="validation")

            if result.returncode == 0:
                self.log("Validation completed successfully")
                return True
            else:
                self.log("Validation failed", "ERROR")
                if self.verbose and result.stderr:
                    self.log(f"Validation errors: {result.stderr}", "WARNING")
                return False

        except Exception as e:
            self.log(f"Docker validation error: {e}", "ERROR")
            return False

    def _validate_manuscript_local(self) -> bool:
        """Run manuscript validation using local installation."""
        try:
            # Import and run validation directly instead of subprocess
            from .validate import validate_manuscript

            # Set up environment and working directory
            original_cwd = os.getcwd()
            manuscript_path = Path(self.manuscript_path)
            manuscript_abs_path = str(manuscript_path.resolve())

            try:
                # Change to manuscript directory for relative path resolution
                os.chdir(manuscript_path.parent)

                # Run validation with proper arguments
                result = validate_manuscript(
                    manuscript_path=manuscript_abs_path,
                    verbose=self.verbose,
                    include_info=False,
                    check_latex=True,
                    enable_doi_validation=True,
                    detailed=True,
                )

                if result:
                    self.log("Validation completed successfully")
                    return True
                else:
                    self.log("Validation failed", "ERROR")
                    return False

            finally:
                # Always restore original working directory
                os.chdir(original_cwd)

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
                engine=self.engine,
            )
            figure_gen.generate_all_figures()

            # Generate R figures if any
            r_figure_gen = FigureGenerator(
                figures_dir=str(self.figures_dir),
                output_dir=str(self.figures_dir),
                output_format="pdf",
                r_only=True,
                engine=self.engine,
            )
            r_figure_gen.generate_all_figures()

            self.log("Figure generation completed")

            # Update checksums after successful generation
            try:
                checksum_manager = get_figure_checksum_manager(self.manuscript_path)
                if self.force_figures:
                    # Force update all checksums when figures are force-generated
                    checksum_manager.force_update_all()
                else:
                    # Update checksums for all current source files
                    checksum_manager.update_checksums()
                self.log("Updated figure checksums")
            except Exception as e:
                self.log(f"Warning: Failed to update checksums: {e}", "WARNING")

            return True

        except Exception as e:
            self.log(f"Figure generation failed: {e}", "ERROR")
            return False

    def _check_figures_need_update(self) -> bool:
        """Check if figures need to be updated using checksum-based approach."""
        if not self.figures_dir.exists():
            return False

        # Use checksum manager for efficient change detection
        try:
            checksum_manager = get_figure_checksum_manager(self.manuscript_path)

            # Clean up orphaned checksums first
            checksum_manager.cleanup_orphaned_checksums()

            # Check if any files have changed
            need_update = checksum_manager.check_figures_need_update()

            if need_update:
                changed_files = checksum_manager.get_changed_files()
                self.log(f"Found {len(changed_files)} changed figure source files")
                for file_path in changed_files:
                    self.log(f"  Changed: {file_path.name}")

            # Also check if output files are missing (fallback safety check)
            if not need_update:
                need_update = self._check_missing_output_files()
                if need_update:
                    self.log("Some figure output files are missing")

            return need_update

        except Exception as e:
            self.log(f"Error checking figure checksums: {e}", "WARNING")
            # Fallback to file modification time approach
            return self._check_figures_need_update_fallback()

    def _check_missing_output_files(self) -> bool:
        """Check if any expected output files are missing."""
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

            # Check if output file exists
            if not output_file.exists():
                return True

        return False

    def _check_figures_need_update_fallback(self) -> bool:
        """Fallback method using file modification times."""
        self.log("Using fallback file modification time check", "WARNING")

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
            self.log("Style directory not found, skipping style file copying", "WARNING")
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
            # Import and call the generate_preprint function directly
            from ..processors.yaml_processor import extract_yaml_metadata
            from .generate_preprint import generate_preprint

            # Find the manuscript file and extract metadata
            manuscript_md = None
            for md_file in ["01_MAIN.md", "MAIN.md", "manuscript.md"]:
                md_path = Path(self.manuscript_path) / md_file
                if md_path.exists():
                    manuscript_md = md_path
                    break

            if not manuscript_md:
                self.log("Could not find manuscript markdown file", "ERROR")
                return False

            # Extract YAML metadata from the manuscript file
            yaml_metadata = extract_yaml_metadata(str(manuscript_md))

            # Set MANUSCRIPT_PATH env var for generate_preprint
            original_env = os.environ.get("MANUSCRIPT_PATH")
            os.environ["MANUSCRIPT_PATH"] = os.path.basename(self.manuscript_path)

            # Change to the parent directory so the relative path works
            original_cwd = os.getcwd()
            os.chdir(Path(self.manuscript_path).parent)

            try:
                # Generate the preprint
                result = generate_preprint(str(self.output_dir), yaml_metadata)

                if result:
                    self.log("LaTeX files generated successfully")
                    return True
                else:
                    self.log("LaTeX generation failed", "ERROR")
                    return False
            finally:
                # Restore environment and working directory
                os.chdir(original_cwd)
                if original_env is not None:
                    os.environ["MANUSCRIPT_PATH"] = original_env
                else:
                    os.environ.pop("MANUSCRIPT_PATH", None)

        except Exception as e:
            self.log(f"Error generating LaTeX files: {e}", "ERROR")
            return False

    def compile_pdf(self) -> bool:
        """Compile LaTeX to PDF."""
        self.log("Compiling LaTeX to PDF...", "STEP")

        if self.engine == "docker":
            return self._compile_pdf_docker()
        else:
            return self._compile_pdf_local()

    def _compile_pdf_docker(self) -> bool:
        """Compile LaTeX to PDF using Docker."""
        try:
            tex_file = self.output_dir / f"{self.manuscript_name}.tex"

            # Run LaTeX compilation with multiple passes
            results = self.docker_manager.run_latex_compilation(
                tex_file=tex_file, working_dir=self.output_dir, passes=3
            )

            # Check if PDF was generated successfully
            pdf_file = self.output_dir / f"{self.manuscript_name}.pdf"
            if pdf_file.exists():
                self.log("PDF compilation successful")
                return True
            else:
                self.log("PDF compilation failed", "ERROR")
                if self.verbose and results:
                    for i, result in enumerate(results):
                        self.log(f"Pass {i + 1} output: {result.stdout}", "WARNING")
                return False

        except Exception as e:
            self.log(f"Error compiling PDF with Docker: {e}", "ERROR")
            return False

    def _compile_pdf_local(self) -> bool:
        """Compile LaTeX to PDF using local installation."""
        # Change to output directory for compilation
        original_cwd = os.getcwd()

        try:
            os.chdir(self.output_dir)

            # Run pdflatex multiple times for proper cross-references
            tex_file = f"{self.manuscript_name}.tex"

            # First pass
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_file],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            # Run bibtex if references exist (check in current working directory)
            # which is output_dir
            output_references = Path("03_REFERENCES.bib")
            if output_references.exists():
                self.log("Running BibTeX to process bibliography...")
                bibtex_result = subprocess.run(
                    ["bibtex", self.manuscript_name],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )

                # Log BibTeX warnings and errors only
                if bibtex_result.stderr:
                    self.log(f"BibTeX errors: {bibtex_result.stderr}", "WARNING")
                elif "warning" in bibtex_result.stdout.lower():
                    # Count warnings but don't spam the output
                    warning_count = bibtex_result.stdout.lower().count("warning")
                    self.log(f"BibTeX completed with {warning_count} warning(s)", "WARNING")

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
                    # Log BibTeX warnings to file
                    try:
                        self._log_bibtex_warnings()
                    except Exception as e:
                        self.log(f"Debug: BibTeX warning logging failed: {e}", "WARNING")

            # Second pass
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_file],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            # Third pass
            result3 = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_file],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            # Check if compilation was successful
            # (PDF exists is more reliable than return code)
            # Check for PDF in current directory (we're in output_dir)
            pdf_file = Path(f"{self.manuscript_name}.pdf")

            if pdf_file.exists():
                self.log("PDF compilation successful")
                # Show warnings if any, but don't fail the build
                if result3.returncode != 0 and self.verbose:
                    self.log("LaTeX completed with warnings:", "WARNING")
                    if result3.stdout:
                        print("LaTeX output:")
                        print(result3.stdout[-2000:])  # Show last 2000 chars to avoid spam
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
            python_parts = self.platform.python_cmd.split()
            cmd = [
                python_parts[0] if python_parts else "python",
                str(self.copy_pdf_script),
                "--output-dir",
                str(self.output_dir),
            ]

            if "uv run" in self.platform.python_cmd:
                cmd = ["uv", "run", "python"] + cmd[1:]

            # Set environment variables
            env = os.environ.copy()
            env["MANUSCRIPT_PATH"] = self.manuscript_path

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                encoding="utf-8",
                errors="replace",
            )

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
            python_parts = self.platform.python_cmd.split()
            cmd = [
                python_parts[0] if python_parts else "python",
                str(self.analyze_word_count_script),
            ]

            if "uv run" in self.platform.python_cmd:
                cmd = ["uv", "run", "python"] + cmd[1:]

            # Set environment variables
            env = os.environ.copy()
            env["MANUSCRIPT_PATH"] = self.manuscript_path

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                encoding="utf-8",
                errors="replace",
            )

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

    def run_pdf_validation(self) -> bool:
        """Run PDF validation to check final output quality."""
        if self.skip_pdf_validation:
            self.log("Skipping PDF validation")
            return True

        self.log("Running PDF validation...", "STEP")

        if self.engine == "docker":
            return self._run_pdf_validation_docker()
        else:
            return self._run_pdf_validation_local()

    def _run_pdf_validation_docker(self) -> bool:
        """Run PDF validation using Docker."""
        try:
            # Convert paths to be relative to Docker workspace
            workspace_dir = self.docker_manager.workspace_dir

            # Handle manuscript path
            manuscript_path = Path(self.manuscript_path)
            manuscript_abs = manuscript_path.resolve()
            try:
                manuscript_rel = manuscript_abs.relative_to(workspace_dir)
            except ValueError:
                manuscript_rel = manuscript_path.name

            # Handle PDF path
            pdf_abs = self.output_pdf.resolve()
            try:
                pdf_rel = pdf_abs.relative_to(workspace_dir)
            except ValueError:
                # Fallback to output directory relative path
                pdf_rel = Path("output") / self.output_pdf.name

            # Build PDF validation command for Docker
            pdf_validation_cmd = [
                "python",
                "/workspace/src/rxiv_maker/validators/pdf_validator.py",
                str(manuscript_rel),
                "--pdf-path",
                f"/workspace/{pdf_rel}",
            ]

            result = self.docker_manager.run_command(command=pdf_validation_cmd, session_key="pdf_validation")

            if result.returncode == 0:
                self.log("PDF validation completed successfully")
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                self.log("PDF validation found issues", "WARNING")
                if result.stderr:
                    print(result.stderr)
                if result.stdout:
                    print(result.stdout)
                return True  # Don't fail the build on PDF validation warnings

        except Exception as e:
            self.log(f"Error running PDF validation with Docker: {e}", "WARNING")
            return True  # Don't fail the build on PDF validation errors

    def _run_pdf_validation_local(self) -> bool:
        """Run PDF validation using local installation."""
        try:
            # Use the existing PDF validation command
            python_parts = self.platform.python_cmd.split()
            cmd = [
                python_parts[0] if python_parts else "python",
                str(self.pdf_validator_script),
                self.manuscript_path,
                "--pdf-path",
                str(self.output_pdf),
            ]

            if "uv run" in self.platform.python_cmd:
                cmd = ["uv", "run", "python"] + cmd[1:]

            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

            if result.returncode == 0:
                self.log("PDF validation completed successfully")
                # Print validation output if available
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                self.log("PDF validation found issues", "WARNING")
                if result.stderr:
                    print(result.stderr)
                if result.stdout:
                    print(result.stdout)
                # Don't fail the build on PDF validation warnings
                return True

        except Exception as e:
            self.log(f"Error running PDF validation: {e}", "WARNING")
            return True  # Don't fail the build on PDF validation errors

    def run_full_build(self) -> bool:
        """Run the complete build process."""
        # Create operation context for the entire build
        with create_operation("pdf_build", manuscript=self.manuscript_path, engine=self.engine) as op:
            op.log(f"Starting build process for manuscript: {self.manuscript_path}")
            self.log(
                f"Starting build process for manuscript: {self.manuscript_path} (Operation ID: {op.operation_id})",
                "STEP",
            )

            # Track performance
            perf_tracker = get_performance_tracker()

            # Step 1: Check manuscript structure
            perf_tracker.start_operation("check_structure")
            if not self.check_manuscript_structure():
                op.log("Failed at manuscript structure check")
                return False
            perf_tracker.end_operation("check_structure")

            # Step 2: Set up output directory
            perf_tracker.start_operation("setup_output")
            if not self.setup_output_directory():
                op.log("Failed at output directory setup")
                return False
            perf_tracker.end_operation("setup_output")

            # Step 3: Generate figures (before validation to ensure figure files exist)
            perf_tracker.start_operation("generate_figures")
            if not self.generate_figures():
                op.log("Failed at figure generation")
                return False
            perf_tracker.end_operation("generate_figures")

            # Step 4: Validate manuscript (if not skipped)
            perf_tracker.start_operation("validate_manuscript")
            if not self.validate_manuscript():
                op.log("Failed at manuscript validation")
                return False
            perf_tracker.end_operation("validate_manuscript")

            # Step 5: Copy style files
            perf_tracker.start_operation("copy_files")
            if not self.copy_style_files():
                op.log("Failed at copying style files")
                return False

            # Step 6: Copy references
            if not self.copy_references():
                op.log("Failed at copying references")
                return False

            # Step 7: Copy figures
            if not self.copy_figures():
                op.log("Failed at copying figures")
                return False
            perf_tracker.end_operation("copy_files")

            # Step 8: Generate LaTeX files
            perf_tracker.start_operation("generate_tex")
            if not self.generate_tex_files():
                op.log("Failed at LaTeX generation")
                return False
            perf_tracker.end_operation("generate_tex")

            # Step 9: Compile PDF
            perf_tracker.start_operation("compile_pdf")
            if not self.compile_pdf():
                op.log("Failed at PDF compilation")
                return False
            perf_tracker.end_operation("compile_pdf")

            # Step 10: Copy PDF to manuscript directory
            if not self.copy_pdf_to_manuscript():
                op.log("Failed at copying PDF to manuscript")
                return False

            # Step 11: Run PDF validation
            self.run_pdf_validation()

            # Step 12: Run word count analysis
            self.run_word_count_analysis()

            # Success!
            op.log(f"Build completed successfully: {self.output_pdf}")
            self.log(f"Build completed successfully: {self.output_pdf} (Operation ID: {op.operation_id})")

            # Generate performance report
            perf_report = perf_tracker.get_performance_report()
            if perf_report["summary"]["regressions"] > 0:
                self.log(
                    f"Performance regressions detected: {perf_report['summary']['regressions']} operations",
                    "WARNING",
                )

            # Inform user about warning logs if they exist
            if self.warnings_log.exists():
                self.log(f"Build warnings logged to {self.warnings_log.name}", "INFO")

            return True

    def run(self) -> bool:
        """Run the build process (alias for run_full_build)."""
        return self.run_full_build()


def main():
    """Main entry point for build manager command."""
    import argparse

    parser = argparse.ArgumentParser(description="Build manager for Rxiv-Maker manuscript compilation")
    parser.add_argument("--manuscript-path", default="MANUSCRIPT", help="Path to manuscript directory")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--force-figures", action="store_true", help="Force regeneration of all figures")
    parser.add_argument("--skip-validation", action="store_true", help="Skip manuscript validation")
    parser.add_argument("--skip-pdf-validation", action="store_true", help="Skip PDF validation")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--track-changes", help="Git tag to track changes against")

    args = parser.parse_args()

    # Initialize build manager
    build_manager = BuildManager(
        manuscript_path=args.manuscript_path,
        output_dir=args.output_dir,
        force_figures=args.force_figures,
        skip_validation=args.skip_validation,
        skip_pdf_validation=args.skip_pdf_validation,
        verbose=args.verbose,
        track_changes_tag=args.track_changes,
    )

    # Run the build process
    success = build_manager.run()

    if not success:
        exit(1)


if __name__ == "__main__":
    main()
