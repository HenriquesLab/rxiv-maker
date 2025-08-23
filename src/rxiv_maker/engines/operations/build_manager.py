"""Build manager for rxiv-maker PDF generation pipeline."""

import os
import subprocess
from datetime import datetime
from pathlib import Path

from ...core.environment_manager import EnvironmentManager
from ...core.global_container_manager import get_global_container_manager
from ...core.logging_config import get_logger, set_log_directory
from ...core.path_manager import PathManager
from ...core.session_optimizer import get_optimized_session_key
from ...utils.figure_checksum import get_figure_checksum_manager
from ...utils.operation_ids import create_operation
from ...utils.performance import get_performance_tracker

logger = get_logger()


# Import FigureGenerator dynamically to avoid import issues
def get_figure_generator():
    """Get FigureGenerator class with lazy import."""
    try:
        from .generate_figures import FigureGenerator  # type: ignore[misc]

        return FigureGenerator
    except ImportError:
        from generate_figures import FigureGenerator  # type: ignore[no-redef]

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
        # Initialize centralized path management
        self.path_manager = PathManager(manuscript_path=manuscript_path, output_dir=output_dir)

        # Store configuration
        self.force_figures = force_figures or EnvironmentManager.is_force_figures()
        self.skip_validation = skip_validation
        self.skip_pdf_validation = skip_pdf_validation
        self.verbose = verbose or EnvironmentManager.is_verbose()
        self.track_changes_tag = track_changes_tag
        self.engine = engine or EnvironmentManager.get_rxiv_engine()

        # Initialize container engine if using container engine
        self.container_engine = None
        if self.engine in ["docker", "podman"]:
            try:
                # Use global container manager for shared engine instances
                global_manager = get_global_container_manager()
                self.container_engine = global_manager.get_container_engine(
                    engine_type=self.engine, workspace_dir=self.path_manager._working_dir
                )
                logger.debug(f"Using shared container engine: {self.container_engine.engine_name}")
            except RuntimeError as e:
                # Container engine not available, will fall back to local execution
                logger.warning(f"{self.engine.title()} engine not available: {e}")
                self.container_engine = None

        # Provide legacy interface for backward compatibility
        self.manuscript_path = str(self.path_manager.manuscript_path)
        self.manuscript_dir = self.path_manager.manuscript_path
        self.manuscript_dir_path = self.path_manager.manuscript_path
        self.output_dir = self.path_manager.output_dir
        self.figures_dir = self.path_manager.figures_dir
        self.style_dir = self.path_manager.style_dir
        self.references_bib = self.path_manager.references_bib
        self.manuscript_name = self.path_manager.manuscript_name
        self.output_tex = self.path_manager.get_manuscript_tex_path()
        self.output_pdf = self.path_manager.get_manuscript_pdf_path()

        logger.debug("PathManager initialized:")
        logger.debug(f"  Manuscript path: {self.manuscript_path}")
        logger.debug(f"  Manuscript name: {self.manuscript_name}")
        logger.debug(f"  Output directory: {self.output_dir}")
        logger.debug(f"  Figures directory: {self.figures_dir}")
        logger.debug(f"  Style directory: {self.style_dir}")
        logger.debug(f"  Output TEX: {self.output_tex}")
        logger.debug(f"  Output PDF: {self.output_pdf}")

        # Set up logging
        self.warnings_log = self.path_manager.get_output_file_path("build_warnings.log")
        self.bibtex_log = self.path_manager.get_output_file_path("bibtex_warnings.log")

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
        except Exception as e:
            # Log failure to write to file, but don't fail the build
            logger.debug(f"Failed to write to warnings log file {self.warnings_log}: {e}")

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
        except Exception as e:
            # Log BibTeX warning extraction failure, but don't fail the build
            logger.debug(f"Failed to extract BibTeX warnings from {blg_file}: {e}")

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

        if self.engine in ["docker", "podman"] and self.container_engine is not None:
            return self._validate_manuscript_container()
        else:
            if self.engine in ["docker", "podman"] and self.container_engine is None:
                self.log(f"{self.engine.title()} engine not available, using local validation", "WARNING")
            return self._validate_manuscript_local()

    def _validate_manuscript_container(self) -> bool:
        """Run manuscript validation using container engine."""
        try:
            if self.container_engine is None:
                raise RuntimeError("Container engine not initialized")

            # Use PathManager for container path translation
            manuscript_container_path = self.path_manager.to_container_path(self.path_manager.manuscript_path)

            # Build validation command for container using installed CLI
            validation_cmd = ["rxiv", "validate", manuscript_container_path, "--detailed"]

            if self.verbose:
                validation_cmd.append("--verbose")

            from ...core.session_optimizer import get_optimized_session_key

            result = self.container_engine.run_command(
                command=validation_cmd, session_key=get_optimized_session_key("validation")
            )

            if result.returncode == 0:
                self.log("Container validation completed successfully")
                return True
            else:
                self.log("Container validation failed, falling back to local validation", "WARNING")
                if self.verbose and result.stderr:
                    self.log(f"Container validation errors: {result.stderr}", "WARNING")
                return self._validate_manuscript_local()

        except Exception as e:
            self.log(f"{self.engine.title()} validation error: {e}", "WARNING")
            self.log("Falling back to local validation", "WARNING")
            return self._validate_manuscript_local()

    def _validate_manuscript_local(self) -> bool:
        """Run manuscript validation using local installation."""
        try:
            # Import and run validation directly instead of subprocess
            from .validate import validate_manuscript

            # Set up environment and working directory using PathManager
            original_cwd = os.getcwd()
            manuscript_abs_path = str(self.path_manager.manuscript_path)

            try:
                # Change to manuscript directory for relative path resolution
                os.chdir(self.path_manager.manuscript_path.parent)

                # Set environment variables using EnvironmentManager
                original_env = EnvironmentManager.get_manuscript_path()
                EnvironmentManager.set_manuscript_path(self.path_manager.manuscript_name)

                try:
                    # Run validation with proper arguments
                    # DOI validation setting will be read from config automatically
                    result = validate_manuscript(
                        manuscript_path=manuscript_abs_path,
                        verbose=self.verbose,
                        include_info=False,
                        check_latex=True,
                        enable_doi_validation=None,  # Read from config
                        detailed=True,
                    )

                    if result:
                        self.log("Validation completed successfully")
                        return True
                    else:
                        self.log("Validation failed", "ERROR")
                        return False

                finally:
                    # Restore environment variable using EnvironmentManager
                    if original_env is not None:
                        EnvironmentManager.set_manuscript_path(original_env)
                    else:
                        os.environ.pop("MANUSCRIPT_PATH", None)

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
            FigureGeneratorClass = get_figure_generator()

            # Generate Mermaid and Python figures
            figure_gen = FigureGeneratorClass(
                figures_dir=str(self.figures_dir),
                output_dir=str(self.figures_dir),
                output_format="pdf",
                engine=self.engine,
            )
            figure_gen.generate_all_figures()

            # Generate R figures if any
            r_figure_gen = FigureGeneratorClass(
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

        if self.style_dir is None or not self.style_dir.exists():
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
        figures_output.mkdir(parents=True, exist_ok=True)
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
            from ...processors.yaml_processor import extract_yaml_metadata
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

            # Inject Rxiv-Maker citation if requested
            from ...utils import inject_rxiv_citation

            inject_rxiv_citation(yaml_metadata)

            # Set environment variables using EnvironmentManager
            original_env = EnvironmentManager.get_manuscript_path()
            EnvironmentManager.set_manuscript_path(self.path_manager.manuscript_name)

            # Change to the parent directory so the relative path works
            original_cwd = os.getcwd()
            # Use PathManager for directory navigation
            manuscript_path_obj = self.path_manager.manuscript_path
            if manuscript_path_obj.is_dir():
                # If manuscript_path is a directory, go to its parent
                target_dir = manuscript_path_obj.parent
            else:
                # If manuscript_path is a file, go to its directory's parent
                target_dir = manuscript_path_obj.parent.parent
            os.chdir(target_dir)

            try:
                # Generate the preprint with explicit manuscript path
                result = generate_preprint(str(self.output_dir), yaml_metadata, self.manuscript_path)

                if result:
                    self.log("LaTeX files generated successfully")
                    return True
                else:
                    self.log("LaTeX generation failed", "ERROR")
                    return False
            finally:
                # Restore environment and working directory using EnvironmentManager
                os.chdir(original_cwd)
                if original_env is not None:
                    EnvironmentManager.set_manuscript_path(original_env)
                else:
                    # Clear the environment variable
                    if EnvironmentManager.MANUSCRIPT_PATH in os.environ:
                        del os.environ[EnvironmentManager.MANUSCRIPT_PATH]

        except Exception as e:
            self.log(f"Error generating LaTeX files: {e}", "ERROR")
            return False

    def compile_pdf(self) -> bool:
        """Compile LaTeX to PDF."""
        self.log("Compiling LaTeX to PDF...", "STEP")

        if self.engine in ["docker", "podman"]:
            return self._compile_pdf_container()
        else:
            return self._compile_pdf_local()

    def _compile_pdf_container(self) -> bool:
        """Compile LaTeX to PDF using container engine."""
        try:
            tex_file = self.output_dir / f"{self.manuscript_name}.tex"

            # Execute multi-pass LaTeX compilation (3 passes for bibliography and cross-references)
            if self.container_engine is None:
                raise RuntimeError("Container engine not initialized")
            results = self.container_engine.run_latex_compilation(
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
            self.log(f"Error compiling PDF with {self.engine}: {e}", "ERROR")
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
            from ...processors.yaml_processor import extract_yaml_metadata
            from ...utils import copy_pdf_to_manuscript_folder, find_manuscript_md

            # Find and parse the manuscript markdown using the known manuscript path
            manuscript_md = find_manuscript_md(self.manuscript_path)
            self.log(f"Reading metadata from: {manuscript_md}")

            yaml_metadata = extract_yaml_metadata(manuscript_md)

            # Copy PDF with custom filename using full output_dir path and manuscript path
            result = copy_pdf_to_manuscript_folder(str(self.output_dir), yaml_metadata, self.manuscript_path)

            if result:
                self.log("PDF copied to manuscript directory")
                return True
            else:
                self.log("❌ Failed to copy PDF to manuscript directory", level="ERROR")
                return False

        except Exception as e:
            self.log(f"Error copying PDF: {e}", "ERROR")
            import traceback

            self.log(f"Traceback: {traceback.format_exc()}", "ERROR")
            return False

    def run_word_count_analysis(self) -> bool:
        """Run word count analysis on the manuscript."""
        try:
            from ...converters.md2tex import extract_content_sections
            from ...utils import find_manuscript_md

            # Find the manuscript markdown file using the known manuscript path
            manuscript_md = find_manuscript_md(self.manuscript_path)
            if not manuscript_md:
                self.log("Could not find manuscript markdown file for word count analysis", "WARNING")
                return False

            self.log(f"Analyzing word count for: {manuscript_md}")

            # Extract content sections from markdown
            content_sections = extract_content_sections(str(manuscript_md))

            # Analyze word counts and provide warnings
            self._analyze_section_word_counts(content_sections)

            self.log("Word count analysis completed")
            return True

        except Exception as e:
            self.log(f"Error running word count analysis: {e}", "WARNING")
            import traceback

            self.log(f"Traceback: {traceback.format_exc()}", "WARNING")
            return False

    def _analyze_section_word_counts(self, content_sections):
        """Analyze word counts for each section and provide warnings."""
        import re

        section_guidelines = {
            "abstract": {"ideal": 150, "max_warning": 250, "description": "Abstract"},
            "main": {"ideal": 1500, "max_warning": 3000, "description": "Main content"},
            "methods": {"ideal": 1000, "max_warning": 3000, "description": "Methods"},
            "results": {"ideal": 800, "max_warning": 2000, "description": "Results"},
            "discussion": {"ideal": 600, "max_warning": 1500, "description": "Discussion"},
            "conclusion": {"ideal": 200, "max_warning": 500, "description": "Conclusion"},
            "funding": {"ideal": 50, "max_warning": 150, "description": "Funding"},
            "acknowledgements": {"ideal": 100, "max_warning": 300, "description": "Acknowledgements"},
        }

        def count_words_in_text(text):
            """Count words in text, excluding LaTeX commands."""
            # Remove LaTeX commands (backslash followed by word characters)
            text_no_latex = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", "", text)
            text_no_latex = re.sub(r"\\[a-zA-Z]+", "", text_no_latex)
            # Remove remaining LaTeX markup
            text_no_latex = re.sub(r"[{}\\]", " ", text_no_latex)
            # Split by whitespace and count non-empty words
            words = [word for word in text_no_latex.split() if word.strip()]
            return len(words)

        total_words = 0
        for section_name, section_content in content_sections.items():
            if section_name in section_guidelines:
                word_count = count_words_in_text(section_content)
                total_words += word_count

                guidelines = section_guidelines[section_name]
                status = "✅" if word_count <= guidelines["max_warning"] else "⚠️"

                self.log(
                    f"{status} {guidelines['description']}: {word_count} words "
                    f"(ideal: {guidelines['ideal']}, warning: {guidelines['max_warning']})"
                )

        self.log(f"📊 Total manuscript word count: {total_words} words")

    def run_pdf_validation(self) -> bool:
        """Run PDF validation to check final output quality."""
        if self.skip_pdf_validation:
            self.log("Skipping PDF validation")
            return True

        self.log("Running PDF validation...", "STEP")

        if self.engine in ["docker", "podman"]:
            return self._run_pdf_validation_container()
        else:
            return self._run_pdf_validation_local()

    def _run_pdf_validation_container(self) -> bool:
        """Run PDF validation using container engine."""
        try:
            # Convert paths to be relative to container workspace
            if self.container_engine is None:
                raise RuntimeError("Container engine not initialized")

            # Use PathManager for container path translation
            manuscript_container_path = self.path_manager.to_container_path(self.path_manager.manuscript_path)
            pdf_container_path = self.path_manager.to_container_path(self.path_manager.get_manuscript_pdf_path())

            # Build PDF validation command for container
            pdf_validation_cmd = [
                "python",
                "/workspace/src/rxiv_maker/validators/pdf_validator.py",
                manuscript_container_path,
                "--pdf-path",
                pdf_container_path,
            ]

            if self.container_engine is None:
                raise RuntimeError("Container engine not initialized")
            result = self.container_engine.run_command(
                command=pdf_validation_cmd, session_key=get_optimized_session_key("pdf_validation")
            )

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
            self.log(f"Error running PDF validation with {self.engine}: {e}", "WARNING")
            return True  # Don't fail the build on PDF validation errors

    def _run_pdf_validation_local(self) -> bool:
        """Run PDF validation using local installation."""
        try:
            # Import and call the validate_pdf function directly
            from ...validators.pdf_validator import validate_pdf

            # Call the PDF validation function directly
            result = validate_pdf(self.manuscript_path, str(self.output_pdf))

            # Print validation results
            if result.errors:
                print(f"\nPDF Validation Results for {self.manuscript_path}")
                print("=" * 60)
                for error in result.errors:
                    level_str = error.level.name
                    print(f"[{level_str}] {error.message}")
                    if error.context:
                        print(f"  Context: {error.context}")
                    if error.suggestion:
                        print(f"  Suggestion: {error.suggestion}")
                print()

            # Show key statistics
            if result.metadata:
                total_pages = result.metadata.get("total_pages", "unknown")
                total_words = result.metadata.get("total_words", "unknown")
                citations_found = result.metadata.get("citations_found", 0)
                figure_references = result.metadata.get("figure_references", 0)

                print(
                    f"📄 {total_pages} pages, {total_words} words, {citations_found} citations, {figure_references} figure references"
                )
                if result.errors:
                    print("💡 Check the generated PDF visually to confirm all content appears correctly")

            print()

            self.log("PDF validation completed successfully")
            return True

        except Exception as e:
            self.log(f"Error running PDF validation: {e}", "WARNING")
            return True  # Don't fail the build on PDF validation errors

    def run_full_build(self, progress_callback=None) -> bool:
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
            current_step = 0
            total_steps = 10 if self.skip_validation else 11

            # Step 1: Check manuscript structure
            current_step += 1
            if progress_callback:
                progress_callback("Checking manuscript structure", current_step, total_steps)
            perf_tracker.start_operation("check_structure")
            if not self.check_manuscript_structure():
                op.log("Failed at manuscript structure check")
                return False
            perf_tracker.end_operation("check_structure")

            # Step 2: Set up output directory
            current_step += 1
            if progress_callback:
                progress_callback("Setting up output directory", current_step, total_steps)
            perf_tracker.start_operation("setup_output")
            if not self.setup_output_directory():
                op.log("Failed at output directory setup")
                return False
            perf_tracker.end_operation("setup_output")

            # Step 3: Generate figures (before validation to ensure figure files exist)
            current_step += 1
            if progress_callback:
                progress_callback("Generating figures", current_step, total_steps)
            perf_tracker.start_operation("generate_figures")
            if not self.generate_figures():
                op.log("Failed at figure generation")
                return False
            perf_tracker.end_operation("generate_figures")

            # Step 4: Validate manuscript (if not skipped)
            if not self.skip_validation:
                current_step += 1
                if progress_callback:
                    progress_callback("Validating manuscript", current_step, total_steps)
                perf_tracker.start_operation("validate_manuscript")
                if not self.validate_manuscript():
                    op.log("Failed at manuscript validation")
                    return False
                perf_tracker.end_operation("validate_manuscript")

            # Step 5: Copy style files
            current_step += 1
            if progress_callback:
                progress_callback("Copying style files", current_step, total_steps)
            perf_tracker.start_operation("copy_files")
            if not self.copy_style_files():
                op.log("Failed at copying style files")
                return False

            # Step 6: Copy references
            current_step += 1
            if progress_callback:
                progress_callback("Copying references", current_step, total_steps)
            if not self.copy_references():
                op.log("Failed at copying references")
                return False

            # Step 7: Copy figures
            current_step += 1
            if progress_callback:
                progress_callback("Copying figures", current_step, total_steps)
            if not self.copy_figures():
                op.log("Failed at copying figures")
                return False
            perf_tracker.end_operation("copy_files")

            # Step 8: Generate LaTeX files
            current_step += 1
            if progress_callback:
                progress_callback("Generating LaTeX files", current_step, total_steps)
            perf_tracker.start_operation("generate_tex")
            if not self.generate_tex_files():
                op.log("Failed at LaTeX generation")
                return False
            perf_tracker.end_operation("generate_tex")

            # Step 9: Compile PDF
            current_step += 1
            if progress_callback:
                progress_callback("Compiling PDF", current_step, total_steps)
            perf_tracker.start_operation("compile_pdf")
            if not self.compile_pdf():
                op.log("Failed at PDF compilation")
                return False
            perf_tracker.end_operation("compile_pdf")

            # Step 10: Copy PDF to manuscript directory
            current_step += 1
            if progress_callback:
                progress_callback("Finalizing build", current_step, total_steps)
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
