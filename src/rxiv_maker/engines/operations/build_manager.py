"""Build manager for rxiv-maker PDF generation pipeline using local execution only."""

import os
import subprocess
from pathlib import Path

from ...core.environment_manager import EnvironmentManager
from ...core.logging_config import get_logger, set_log_directory
from ...core.path_manager import PathManager
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
    """Manage the complete build process using local execution only."""

    def __init__(
        self,
        manuscript_path: str | None = None,
        output_dir: str = "output",
        force_figures: bool = False,
        skip_validation: bool = False,
        skip_pdf_validation: bool = False,
        clear_output: bool = True,
        verbose: bool = False,
        track_changes_tag: str | None = None,
    ):
        """Initialize build manager.

        Args:
            manuscript_path: Path to manuscript directory
            output_dir: Output directory for generated files
            force_figures: Force regeneration of all figures
            skip_validation: Skip manuscript validation
            skip_pdf_validation: Skip PDF validation
            clear_output: Clear output directory before build (default: True)
            verbose: Enable verbose output
            track_changes_tag: Git tag to track changes against
        """
        # Initialize centralized path management
        self.path_manager = PathManager(manuscript_path=manuscript_path, output_dir=output_dir)

        # Store configuration
        self.force_figures = force_figures or EnvironmentManager.is_force_figures()
        self.skip_validation = skip_validation
        self.skip_pdf_validation = skip_pdf_validation
        self.clear_output = clear_output
        self.verbose = verbose or EnvironmentManager.is_verbose()
        self.track_changes_tag = track_changes_tag

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
        logger.debug(f"  Manuscript: {self.manuscript_dir}")
        logger.debug(f"  Output: {self.output_dir}")
        logger.debug(f"  Figures: {self.figures_dir}")

        # Initialize performance tracking
        self.performance_tracker = get_performance_tracker()
        if self.performance_tracker:
            self.performance_tracker.start_operation("pdf_build")
            logger.debug("Performance tracking initialized")

        # Configure logging directory
        if self.output_dir:
            set_log_directory(Path(self.output_dir))

    def log(self, message: str, level: str = "INFO"):
        """Log message with consistent formatting."""
        if level == "STEP":
            # Step messages always show
            print(f"📝 {message}")
            logger.info(f"STEP: {message}")
        elif level == "INFO":
            # Info messages show in verbose mode
            if self.verbose:
                print(f"ℹ️ {message}")
            logger.info(message)
        elif level == "WARNING":
            # Warning messages always show
            print(f"⚠️ {message}")
            logger.warning(message)
        elif level == "ERROR":
            # Error messages always show
            print(f"❌ {message}")
            logger.error(message)
        elif level == "SUCCESS":
            # Success messages always show
            print(f"✅ {message}")
            logger.info(f"SUCCESS: {message}")
        else:
            # Default to info
            if self.verbose:
                print(f"ℹ️ {message}")
            logger.info(message)

    def setup_output_directory(self):
        """Set up the output directory."""
        if self.clear_output and self.output_dir.exists():
            self.log("Clearing output directory...", "STEP")
            import shutil

            shutil.rmtree(self.output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log(f"Output directory ready: {self.output_dir}")

    def validate_manuscript(self) -> bool:
        """Run manuscript validation using local execution."""
        if self.skip_validation:
            self.log("Skipping manuscript validation (--skip-validation enabled)")
            return True

        self.log("Running manuscript validation...", "STEP")
        return self._validate_manuscript_local()

    def _validate_manuscript_local(self) -> bool:
        """Run manuscript validation using local installation."""
        try:
            # Import and run validation directly instead of subprocess
            from ..operations.validate import validate_manuscript

            self.log("Running validation with enhanced details...")
            validation_result = validate_manuscript(
                manuscript_path=str(self.path_manager.manuscript_path),
                detailed=False,  # Use brief output for build process
                verbose=False,  # Reduce noise during build
                enable_doi_validation=False,  # Disable DOI validation during build due to cache issues
                check_latex=False,  # Skip LaTeX validation during build - it runs before compilation
            )

            if validation_result:
                self.log("Local validation completed successfully")
                return True
            else:
                self.log("Local validation failed", "ERROR")
                return False

        except Exception as e:
            self.log(f"Local validation error: {e}", "ERROR")
            return False

    def generate_figures(self):
        """Generate figures from source files using local execution."""
        if not self.figures_dir.exists():
            self.log("No FIGURES directory found, skipping figure generation")
            return

        self.log("Generating figures...", "STEP")

        try:
            # Use performance tracking if available
            if self.performance_tracker:
                self.performance_tracker.start_operation("figure_generation")

            FigureGeneratorClass = get_figure_generator()

            # Generate all figures (mermaid, python, etc.)
            figure_gen = FigureGeneratorClass(
                figures_dir=str(self.figures_dir),
                output_dir=str(self.figures_dir),
                output_format="pdf",
                manuscript_path=str(self.manuscript_path),
            )
            figure_gen.process_figures()

            # Generate R figures if any
            r_figure_gen = FigureGeneratorClass(
                figures_dir=str(self.figures_dir),
                output_dir=str(self.figures_dir),
                output_format="pdf",
                r_only=True,
                manuscript_path=str(self.manuscript_path),
            )
            r_figure_gen.process_figures()

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
                self.log(f"Warning: Could not update figure checksums: {e}", "WARNING")

            # End performance tracking
            if self.performance_tracker:
                self.performance_tracker.end_operation("figure_generation")

        except Exception as e:
            self.log(f"Figure generation failed: {e}", "ERROR")
            if self.performance_tracker:
                self.performance_tracker.end_operation("figure_generation", metadata={"error": str(e)})
            raise

    def generate_manuscript_tex(self):
        """Generate the LaTeX manuscript file."""
        self.log("Generating LaTeX manuscript...", "STEP")

        try:
            # Use performance tracking if available
            if self.performance_tracker:
                self.performance_tracker.start_operation("manuscript_generation")

            from ...processors.yaml_processor import extract_yaml_metadata
            from ...utils.file_helpers import find_manuscript_md
            from ..operations.generate_preprint import generate_preprint

            # Extract YAML metadata from the manuscript
            manuscript_md = find_manuscript_md(str(self.path_manager.manuscript_path))
            yaml_metadata = extract_yaml_metadata(str(manuscript_md))

            # Generate the manuscript using local execution
            manuscript_output = generate_preprint(
                output_dir=str(self.output_dir),
                yaml_metadata=yaml_metadata,
                manuscript_path=str(self.path_manager.manuscript_path),
            )

            success = manuscript_output is not None

            if success:
                # Update the actual tex file path based on what was generated
                from pathlib import Path

                self.output_tex = Path(manuscript_output)
                self.output_pdf = self.output_tex.with_suffix(".pdf")
                self.log("LaTeX manuscript generated successfully")
            else:
                raise RuntimeError("Manuscript generation failed")

            # End performance tracking
            if self.performance_tracker:
                self.performance_tracker.end_operation("manuscript_generation")

        except Exception as e:
            self.log(f"Manuscript generation failed: {e}", "ERROR")
            if self.performance_tracker:
                self.performance_tracker.end_operation("manuscript_generation", metadata={"error": str(e)})
            raise

    def compile_latex(self) -> bool:
        """Compile LaTeX to PDF using local LaTeX installation."""
        self.log("Compiling LaTeX to PDF...", "STEP")

        try:
            # Use performance tracking if available
            if self.performance_tracker:
                self.performance_tracker.start_operation("latex_compilation")

            # Use local LaTeX compilation
            success = self._compile_latex_local()

            # End performance tracking
            if self.performance_tracker:
                operation_result = "success" if success else "failed"
                self.performance_tracker.end_operation("latex_compilation", metadata={"result": operation_result})

            return success

        except Exception as e:
            self.log(f"LaTeX compilation failed: {e}", "ERROR")
            if self.performance_tracker:
                self.performance_tracker.end_operation("latex_compilation", metadata={"error": str(e)})
            return False

    def _compile_latex_local(self) -> bool:
        """Compile LaTeX using local pdflatex installation."""
        tex_file = self.output_tex
        pdf_file = self.output_pdf

        if not tex_file.exists():
            self.log(f"LaTeX file not found: {tex_file}", "ERROR")
            return False

        try:
            # Change to output directory for compilation
            original_cwd = os.getcwd()
            os.chdir(str(self.output_dir))

            try:
                # First pass - main compilation
                self.log("Running pdflatex (first pass)...")
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", tex_file.name],
                    capture_output=True,
                    text=True,
                    cwd=str(self.output_dir),
                    timeout=300,
                )

                if result.returncode != 0:
                    self.log("First pdflatex pass had warnings/errors", "WARNING")
                    if result.stdout and self.verbose:
                        self.log(f"pdflatex stdout: {result.stdout[:500]}...")
                    if result.stderr and self.verbose:
                        self.log(f"pdflatex stderr: {result.stderr[:500]}...")
                    # Continue processing - LaTeX can still generate PDF despite warnings

                # Check if bibliography exists and run bibtex
                aux_file = tex_file.with_suffix(".aux")

                if self.references_bib.exists() and aux_file.exists():
                    self.log("Running bibtex...")
                    bibtex_result = subprocess.run(
                        ["bibtex", tex_file.stem],
                        capture_output=True,
                        text=True,
                        cwd=str(self.output_dir),
                        timeout=60,
                    )

                    if bibtex_result.returncode == 0:
                        self.log("Bibtex completed successfully")

                        # Second pass - after bibtex
                        self.log("Running pdflatex (second pass)...")
                        result = subprocess.run(
                            ["pdflatex", "-interaction=nonstopmode", tex_file.name],
                            capture_output=True,
                            text=True,
                            cwd=str(self.output_dir),
                            timeout=300,
                        )

                        if result.returncode != 0:
                            self.log("Second pdflatex pass failed", "WARNING")
                            if self.verbose:
                                self.log(f"Second pass stderr: {result.stderr[:200]}...")
                    else:
                        self.log("Bibtex failed, continuing with single pass", "WARNING")

                # Third pass - final compilation
                self.log("Running pdflatex (final pass)...")
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", tex_file.name],
                    capture_output=True,
                    text=True,
                    cwd=str(self.output_dir),
                    timeout=300,
                )

                # Check if PDF was generated successfully regardless of return code
                if pdf_file.exists():
                    self.log(f"PDF generated successfully: {pdf_file}")
                    if result.returncode != 0:
                        self.log("PDF generated despite LaTeX warnings/errors", "WARNING")
                        if result.stderr and self.verbose:
                            self.log(f"Final pass stderr: {result.stderr[:500]}...")
                    return True
                else:
                    self.log("PDF generation failed - no output file created", "ERROR")
                    if result.stderr:
                        self.log(f"Final pass stderr: {result.stderr[:500]}...")
                    return False

            finally:
                # Always restore original directory
                os.chdir(original_cwd)

        except subprocess.TimeoutExpired:
            self.log("LaTeX compilation timeout", "ERROR")
            return False
        except FileNotFoundError:
            self.log("pdflatex not found - please install LaTeX", "ERROR")
            return False
        except Exception as e:
            self.log(f"LaTeX compilation error: {e}", "ERROR")
            return False

    def validate_pdf(self) -> bool:
        """Validate the generated PDF."""
        if self.skip_pdf_validation:
            self.log("Skipping PDF validation (--skip-pdf-validation enabled)")
            return True

        pdf_file = self.output_pdf
        if not pdf_file.exists():
            self.log("PDF file not found for validation", "ERROR")
            return False

        self.log("Validating PDF...", "STEP")

        try:
            # Use local PDF validation
            from ..operations.validate_pdf import validate_pdf_output

            # validate_pdf_output returns 0 for success, 1 for errors
            exit_code = validate_pdf_output(
                manuscript_path=str(self.manuscript_dir), pdf_path=str(pdf_file), verbose=self.verbose
            )
            is_valid = exit_code == 0

            if is_valid:
                self.log("PDF validation successful")
                return True
            else:
                self.log("PDF validation failed", "ERROR")
                return False

        except Exception as e:
            self.log(f"PDF validation error: {e}", "ERROR")
            return False

    def copy_final_pdf(self):
        """Copy the final PDF to manuscript directory with proper naming."""
        try:
            source_pdf = self.output_pdf
            if not source_pdf.exists():
                self.log("Source PDF not found, skipping copy", "WARNING")
                return

            # Extract YAML metadata to generate proper filename
            from ...processors.yaml_processor import extract_yaml_metadata
            from ...utils.file_helpers import find_manuscript_md
            from ...utils.pdf_utils import get_custom_pdf_filename

            manuscript_md = find_manuscript_md(str(self.path_manager.manuscript_path))
            yaml_metadata = extract_yaml_metadata(str(manuscript_md))

            # Generate PDF name in format: YEAR__lastname_et_al__rxiv.pdf
            final_pdf_name = get_custom_pdf_filename(yaml_metadata)
            final_pdf_path = self.path_manager.manuscript_path / final_pdf_name

            # Copy the PDF
            import shutil

            shutil.copy2(source_pdf, final_pdf_path)

            self.log(f"PDF copied to: {final_pdf_path}", "SUCCESS")

        except Exception as e:
            self.log(f"Failed to copy final PDF: {e}", "WARNING")

    def copy_style_files(self):
        """Copy LaTeX style files to output directory using centralized PathManager."""
        self.log("Copying style files...", "STEP")

        try:
            # Use centralized path manager method for style file copying
            copied_files = self.path_manager.copy_style_files_to_output()

            for copied_file in copied_files:
                self.log(f"Copied {copied_file.name} to output directory")

        except Exception as e:
            self.log(f"Failed to copy style files: {e}", "ERROR")
            raise

    def build(self) -> bool:
        """Execute the complete build process."""
        with create_operation("pdf_build", manuscript=self.manuscript_path) as op:
            try:
                # Start overall performance tracking
                if self.performance_tracker:
                    self.performance_tracker.start_operation("complete_build")

                self.log("Starting PDF build process...", "STEP")
                self.log(f"📁 Manuscript: {self.manuscript_dir}")
                self.log(f"📁 Output: {self.output_dir}")

                # Step 1: Setup
                self.setup_output_directory()

                # Step 2: Validation
                if not self.validate_manuscript():
                    self.log("Build failed: Manuscript validation failed", "ERROR")
                    op.add_metadata("validation_passed", False)
                    return False
                op.add_metadata("validation_passed", True)

                # Step 3: Generate figures
                self.generate_figures()

                # Step 4: Generate LaTeX manuscript
                self.generate_manuscript_tex()

                # Step 5: Copy style files
                self.copy_style_files()

                # Step 6: Compile LaTeX to PDF
                if not self.compile_latex():
                    self.log("Build failed: LaTeX compilation failed", "ERROR")
                    op.add_metadata("latex_compilation_passed", False)
                    return False
                op.add_metadata("latex_compilation_passed", True)

                # Step 7: Validate PDF
                if not self.validate_pdf():
                    self.log("Build failed: PDF validation failed", "ERROR")
                    op.add_metadata("pdf_validation_passed", False)
                    return False
                op.add_metadata("pdf_validation_passed", True)

                # Step 8: Copy final PDF
                self.copy_final_pdf()

                # Success
                self.log("PDF build completed successfully!", "SUCCESS")
                self.log(f"📄 Generated: {self.output_pdf}")

                # End performance tracking
                if self.performance_tracker:
                    self.performance_tracker.end_operation("complete_build", metadata={"result": "success"})

                op.add_metadata("build_successful", True)
                return True

            except KeyboardInterrupt:
                self.log("Build interrupted by user", "WARNING")
                if self.performance_tracker:
                    self.performance_tracker.end_operation("complete_build", metadata={"error": "interrupted"})
                op.add_metadata("build_successful", False)
                op.add_metadata("interruption_reason", "user_interrupt")
                return False

            except Exception as e:
                self.log(f"Build failed with unexpected error: {e}", "ERROR")
                logger.error(f"Unexpected build error: {e}")
                if self.performance_tracker:
                    self.performance_tracker.end_operation("complete_build", metadata={"error": str(e)})
                op.add_metadata("build_successful", False)
                op.add_metadata("error", str(e))
                return False
