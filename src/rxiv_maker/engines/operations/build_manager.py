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
        quiet: bool = False,
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
            quiet: Suppress non-critical warnings
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
        self.quiet = quiet
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

    def _should_show_latex_warning(self, warning_type: str) -> bool:
        """Determine if a LaTeX warning should be shown based on quiet mode.

        Args:
            warning_type: Type of warning (e.g., 'compilation', 'pdf_generation')

        Returns:
            True if warning should be shown
        """
        if not self.quiet:
            return True

        # In quiet mode, suppress routine LaTeX compilation warnings
        routine_warnings = {
            "latex_compilation_pass",  # pdflatex pass warnings
            "pdf_generation_warnings",  # PDF generated despite warnings
        }

        return warning_type not in routine_warnings

    def log(self, message: str, level: str = "INFO"):
        """Log message with consistent formatting."""
        if level == "STEP":
            # Step messages always show, just log to file
            print(f"📝 {message}")
            logger.debug(f"STEP: {message}")  # Use debug level to avoid console duplication
        elif level == "INFO":
            # Info messages show in verbose mode or are just logged
            logger.info(message)
            if self.verbose:
                print(f"ℹ️ {message}")
        elif level == "WARNING":
            # Warning messages always show - for actionable issues only
            print(f"⚠️ {message}")
            logger.warning(message)
        elif level == "VERBOSE_WARNING":
            # Verbose warnings - only show in verbose mode (for non-actionable issues)
            if self.verbose:
                print(f"⚠️ {message}")
                logger.warning(message)
            else:
                logger.debug(f"VERBOSE_WARNING: {message}")
        elif level == "QUIET_WARNING":
            # Quiet warnings - show only if not in quiet mode
            if not self.quiet:
                print(f"⚠️ {message}")
            # Still log to file but don't show in console if quiet
            if not self.quiet:
                logger.warning(message)
            else:
                logger.debug(f"QUIET_WARNING: {message}")
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
        self.log(f"Output directory ready: {self.output_dir}", "INFO")

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
                self.log("Local validation completed successfully", "INFO")
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

            # Generate all figures in a single pass (mermaid, python, R, etc.)
            figure_gen = FigureGeneratorClass(
                figures_dir=str(self.figures_dir),
                output_dir=str(self.figures_dir),
                output_format="pdf",
                manuscript_path=str(self.manuscript_path),
            )
            figure_gen.process_figures()

            self.log("Figure generation completed", "INFO")

            # Update checksums after successful generation
            try:
                checksum_manager = get_figure_checksum_manager(self.manuscript_path)
                if self.force_figures:
                    # Force update all checksums when figures are force-generated
                    checksum_manager.force_update_all()
                else:
                    # Update checksums for all current source files
                    checksum_manager.update_checksums()

                # Only log checksum updates in verbose mode
                if self.verbose:
                    self.log("Updated figure checksums", "INFO")
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

    def execute_manuscript_code(self):
        """Execute code blocks embedded in manuscript files (future enhancement)."""
        # Placeholder for manuscript code execution functionality
        # This would scan markdown files for ```python blocks and execute them
        # For now, this is a no-op since the main issue (figure generation) is fixed
        pass

    def generate_manuscript_tex(self):
        """Generate the LaTeX manuscript file."""
        self.log("Generating LaTeX manuscript...", "STEP")

        try:
            # Use performance tracking if available
            if self.performance_tracker:
                self.performance_tracker.start_operation("manuscript_generation")

            from ...processors.yaml_processor import extract_yaml_metadata
            from ...utils.citation_utils import inject_rxiv_citation
            from ...utils.file_helpers import find_manuscript_md
            from ..operations.generate_preprint import generate_preprint

            # Extract YAML metadata from the manuscript
            manuscript_md = find_manuscript_md(str(self.path_manager.manuscript_path))
            yaml_metadata = extract_yaml_metadata(str(manuscript_md))

            # Inject rxiv-maker citation if acknowledgment is enabled
            try:
                inject_rxiv_citation(yaml_metadata)
            except Exception as e:
                self.log(f"Warning: Citation injection failed: {e}", "WARNING")
                # Continue with build process even if citation injection fails

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
                self.log("LaTeX manuscript generated successfully", "INFO")
            else:
                raise RuntimeError("Manuscript generation failed")

            # End performance tracking
            if self.performance_tracker:
                self.performance_tracker.end_operation("manuscript_generation")

        except Exception as e:
            # Don't log here - let the higher level handle the detailed logging
            if self.performance_tracker:
                self.performance_tracker.end_operation("manuscript_generation", metadata={"error": str(e)})
            raise

    def display_python_execution_report(self):
        """Display Python execution report in the console during build."""
        try:
            # Import the Python execution reporter
            from ...utils.python_execution_reporter import get_python_execution_reporter

            reporter = get_python_execution_reporter()

            # Check if any Python code was executed
            if not reporter.has_python_activity():
                return

            self.log("Python Code Execution Summary", "STEP")

            summary = reporter.get_execution_summary()

            # Display execution summary
            self.log(f"📊 Total Python operations: {summary['total_entries']}")
            if summary["exec_blocks"] > 0:
                self.log(f"🔧 Initialization blocks: {summary['exec_blocks']}")
            if summary["get_variables"] > 0:
                self.log(f"📝 Variable retrievals: {summary['get_variables']}")
            if summary["inline_blocks"] > 0:
                self.log(f"⚡ Inline executions: {summary['inline_blocks']}")
            if summary["total_execution_time"] is not None:
                self.log(f"⏱️  Total execution time: {summary['total_execution_time']:.3f}s")

            # Display outputs from exec blocks
            exec_entries = [e for e in reporter.entries if e.entry_type == "exec" and e.output.strip()]
            if exec_entries:
                self.log("📤 Python Execution Output:")
                for i, entry in enumerate(exec_entries, 1):
                    if entry.line_number:
                        self.log(f"   Block {i} (line {entry.line_number}):")
                    else:
                        self.log(f"   Block {i}:")

                    # Display output with proper indentation
                    output_lines = entry.output.strip().split("\n")
                    for line in output_lines:
                        self.log(f"     {line}")

                    if i < len(exec_entries):  # Add spacing between blocks
                        self.log("")

            # Display errors if any
            error_entries = [e for e in reporter.entries if e.entry_type == "error"]
            if error_entries:
                self.log("❌ Python Execution Errors:")
                for i, entry in enumerate(error_entries, 1):
                    if entry.line_number:
                        self.log(f"   Error {i} (line {entry.line_number}): {entry.error_message}", "ERROR")
                    else:
                        self.log(f"   Error {i}: {entry.error_message}", "ERROR")

        except Exception as e:
            self.log(f"Failed to display Python execution report: {e}", "WARNING")

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
                    text=False,
                    cwd=str(self.output_dir),
                    timeout=300,
                )

                if result.returncode != 0:
                    self.log("First pdflatex pass had warnings/errors", "VERBOSE_WARNING")
                    if result.stdout and self.verbose:
                        try:
                            stdout_text = result.stdout.decode("utf-8", errors="replace")
                            self.log(f"pdflatex stdout: {stdout_text[:500]}...")
                        except Exception:
                            self.log("pdflatex stdout: <unable to decode output>")
                    if result.stderr and self.verbose:
                        try:
                            stderr_text = result.stderr.decode("utf-8", errors="replace")
                            self.log(f"pdflatex stderr: {stderr_text[:500]}...")
                        except Exception:
                            self.log("pdflatex stderr: <unable to decode output>")
                    # Continue processing - LaTeX can still generate PDF despite warnings

                # Check if bibliography exists and run bibtex
                aux_file = tex_file.with_suffix(".aux")

                if self.references_bib.exists() and aux_file.exists():
                    self.log("Running bibtex...")
                    bibtex_result = subprocess.run(
                        ["bibtex", tex_file.stem],
                        capture_output=True,
                        text=False,
                        cwd=str(self.output_dir),
                        timeout=60,
                    )

                    if bibtex_result.returncode == 0:
                        self.log("Bibtex completed successfully", "INFO")

                        # Second pass - after bibtex
                        self.log("Running pdflatex (second pass)...")
                        result = subprocess.run(
                            ["pdflatex", "-interaction=nonstopmode", tex_file.name],
                            capture_output=True,
                            text=False,
                            cwd=str(self.output_dir),
                            timeout=300,
                        )

                        if result.returncode != 0:
                            self.log("Second pdflatex pass failed", "VERBOSE_WARNING")
                            if self.verbose:
                                try:
                                    stderr_text = result.stderr.decode("utf-8", errors="replace")
                                    self.log(f"Second pass stderr: {stderr_text[:200]}...")
                                except Exception:
                                    self.log("Second pass stderr: <unable to decode output>")
                    else:
                        self.log("Bibtex failed, continuing with single pass", "WARNING")

                # Third pass - final compilation
                self.log("Running pdflatex (final pass)...")
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", tex_file.name],
                    capture_output=True,
                    text=False,
                    cwd=str(self.output_dir),
                    timeout=300,
                )

                # Check if PDF was generated successfully regardless of return code
                if pdf_file.exists():
                    self.log(f"PDF generated successfully: {pdf_file}", "INFO")
                    if result.returncode != 0:
                        self.log("PDF generated despite LaTeX warnings/errors", "VERBOSE_WARNING")
                        if result.stderr and self.verbose:
                            try:
                                stderr_text = result.stderr.decode("utf-8", errors="replace")
                                self.log(f"Final pass stderr: {stderr_text[:500]}...")
                            except Exception:
                                self.log("Final pass stderr: <unable to decode output>")
                    return True
                else:
                    self.log("PDF generation failed - no output file created", "ERROR")
                    if result.stderr:
                        try:
                            stderr_text = result.stderr.decode("utf-8", errors="replace")
                            self.log(f"Final pass stderr: {stderr_text[:500]}...")
                        except Exception:
                            self.log("Final pass stderr: <unable to decode output>")
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
                manuscript_path=str(self.manuscript_dir), pdf_path=str(pdf_file), verbose=self.verbose, quiet=self.quiet
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

    def compile_pdf(self) -> bool:
        """Compile PDF from LaTeX sources. Alias for compile_latex for backward compatibility."""
        return self.compile_latex()

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

    def run_word_count_analysis(self):
        """Analyze word counts from manuscript markdown and display results."""
        self.log("Analyzing word counts...", "STEP")

        try:
            # Import word count analysis functions from the deprecated module
            from ...converters.md2tex import extract_content_sections
            from ...utils.file_helpers import find_manuscript_md

            # Find the manuscript markdown file
            manuscript_md = find_manuscript_md(str(self.path_manager.manuscript_path))
            if not manuscript_md:
                self.log("Could not find manuscript markdown file", "WARNING")
                return

            # Extract content sections from markdown
            content_sections = extract_content_sections(str(manuscript_md))

            # Analyze word counts with improved section mapping
            self._analyze_improved_section_word_counts(content_sections)

            self.log("Word count analysis completed", "INFO")

        except Exception as e:
            self.log(f"Word count analysis failed: {e}", "WARNING")
            logger.error(f"Word count analysis error: {e}")
            import traceback

            logger.debug(f"Word count analysis traceback: {traceback.format_exc()}")

    def _analyze_improved_section_word_counts(self, content_sections):
        """Analyze word counts for each section with improved main content detection."""
        from ...utils.text_utils import count_words_in_text

        # Define section guidelines with main content calculation
        section_guidelines = {
            "abstract": {"ideal": 150, "max_warning": 250, "description": "Abstract"},
            "introduction": {"ideal": 500, "max_warning": 1000, "description": "Introduction"},
            "methods": {"ideal": 1000, "max_warning": 3000, "description": "Methods"},
            "results": {"ideal": 800, "max_warning": 2000, "description": "Results"},
            "discussion": {"ideal": 600, "max_warning": 1500, "description": "Discussion"},
            "results_and_discussion": {"ideal": 1400, "max_warning": 3500, "description": "Results and Discussion"},
            "conclusion": {"ideal": 200, "max_warning": 500, "description": "Conclusion"},
            "funding": {"ideal": 50, "max_warning": 150, "description": "Funding"},
            "acknowledgements": {"ideal": 100, "max_warning": 300, "description": "Acknowledgements"},
            "data_availability": {"ideal": 30, "max_warning": 100, "description": "Data Availability"},
            "code_availability": {"ideal": 30, "max_warning": 100, "description": "Code Availability"},
            "author_contributions": {"ideal": 50, "max_warning": 200, "description": "Author Contributions"},
        }

        print("\n📊 WORD COUNT ANALYSIS:")
        print("=" * 50)

        # Calculate main content by combining introduction, results, discussion, conclusion, and any "main" section
        main_content_sections = [
            "main",
            "introduction",
            "results",
            "discussion",
            "conclusion",
            "results_and_discussion",
        ]
        main_content_words = 0
        total_words = 0

        # First pass: calculate main content and total words
        section_word_counts = {}
        for section_key, content in content_sections.items():
            if content and content.strip():
                word_count = count_words_in_text(content)
                section_word_counts[section_key] = word_count
                total_words += word_count

                if section_key in main_content_sections:
                    main_content_words += word_count

        # Display main content first if we have main content sections
        if main_content_words > 0:
            status = "✓"
            warning = ""
            if main_content_words > 3000:
                status = "⚠️"
                warning = " (exceeds typical 3000 word limit)"
            elif main_content_words > 2000:
                status = "⚠️"
                warning = " (consider typical ~1500 words)"

            print(f"{status} {'Main content':<16}: {main_content_words:>4} words{warning}")

        # Display individual sections
        for section_key, word_count in section_word_counts.items():
            # Skip main content sections since we've already shown the combined count
            # Also skip any "main" section as it's included in the main content calculation
            if section_key in main_content_sections or section_key == "main":
                continue

            guidelines = section_guidelines.get(section_key, {})
            section_name = guidelines.get("description", section_key.replace("_", " ").title())
            ideal = guidelines.get("ideal")
            max_warning = guidelines.get("max_warning")

            # Format output
            status = "✓"
            warning = ""

            if max_warning and word_count > max_warning:
                status = "⚠️"
                warning = f" (exceeds typical {max_warning} word limit)"
            elif ideal is not None and isinstance(ideal, (int, float)) and word_count > (ideal * 1.5):
                status = "⚠️"
                warning = f" (consider typical ~{ideal} words)"

            print(f"{status} {section_name:<16}: {word_count:>4} words{warning}")

        print("-" * 50)
        print(f"📝 Total article words: {total_words}")

        # Overall article length guidance
        if total_words > 8000:
            print("⚠️  Article is quite long (>8000 words) - consider condensing for most journals")
        elif total_words > 5000:
            print("ℹ️  Article length is substantial - check target journal word limits")
        elif total_words < 2000:
            print("ℹ️  Article is relatively short - ensure adequate detail for publication")

        print("=" * 50)

    def copy_references(self):
        """Copy references bibliography file to output directory."""
        self.log("Copying references...", "STEP")

        try:
            # Check if references file exists
            if not self.path_manager.references_bib.exists():
                self.log("No references file found, skipping copy", "WARNING")
                return False

            # Copy references to output directory
            import shutil

            output_refs_path = self.output_dir / "03_REFERENCES.bib"
            shutil.copy2(self.path_manager.references_bib, output_refs_path)
            self.log(f"Copied {self.path_manager.references_bib.name} to output directory", "INFO")
            return True

        except Exception as e:
            self.log(f"Failed to copy references: {e}", "WARNING")
            return False

    def copy_style_files(self):
        """Copy LaTeX style files to output directory using centralized PathManager."""
        self.log("Copying style files...", "STEP")

        try:
            # Use centralized path manager method for style file copying
            copied_files = self.path_manager.copy_style_files_to_output()

            for copied_file in copied_files:
                self.log(f"Copied {copied_file.name} to output directory", "INFO")

            return True

        except Exception as e:
            self.log(f"Failed to copy style files: {e}", "ERROR")
            raise

    def copy_figures(self):
        """Copy figures to output directory using centralized PathManager."""
        self.log("Copying figures to output directory...", "STEP")

        try:
            # Use centralized path manager method for figure copying
            copied_files = self.path_manager.copy_figures_to_output()

            if copied_files:
                for copied_file in copied_files:
                    self.log(f"Copied {copied_file.name} to output directory", "INFO")
                self.log(f"Copied {len(copied_files)} figures to output directory", "INFO")
            else:
                self.log("No figures found to copy", "INFO")

            return True

        except Exception as e:
            self.log(f"Failed to copy figures: {e}", "ERROR")
            raise

    def generate_tex_files(self):
        """Generate LaTeX files (wrapper for backward compatibility)."""
        try:
            self.generate_manuscript_tex()
            return True
        except Exception:
            return False

    def build(self) -> bool:
        """Execute the complete build process."""
        with create_operation("pdf_build", manuscript=self.manuscript_path) as op:
            try:
                # Start overall performance tracking
                if self.performance_tracker:
                    self.performance_tracker.start_operation("complete_build")

                # Set manuscript path in environment for Python executor
                EnvironmentManager.set_manuscript_path(self.manuscript_dir)

                self.log("Starting PDF build process...", "STEP")
                self.log(f"📁 Manuscript: {self.manuscript_dir}", "INFO")
                self.log(f"📁 Output: {self.output_dir}", "INFO")

                # Step 1: Setup
                self.setup_output_directory()

                # Reset Python execution reporter for this build
                try:
                    from ...utils.python_execution_reporter import reset_python_execution_reporter

                    reset_python_execution_reporter()
                except ImportError:
                    pass  # Reporter not available

                # Step 2: Generate figures first (before validation)
                self.generate_figures()

                # Step 3: Execute manuscript code blocks (if any)
                self.execute_manuscript_code()

                # Step 4: Validation (after figures and code execution)
                if not self.validate_manuscript():
                    self.log("Build failed: Manuscript validation failed", "ERROR")
                    op.add_metadata("validation_passed", False)
                    return False
                op.add_metadata("validation_passed", True)

                # Step 5: Generate LaTeX manuscript
                self.generate_manuscript_tex()

                # Step 5.5: Display Python execution report in console (if applicable)
                self.display_python_execution_report()

                # Step 6: Copy references
                self.copy_references()

                # Step 7: Copy style files
                self.copy_style_files()

                # Step 7.5: Copy figures to output directory
                self.copy_figures()

                # Step 8: Compile LaTeX to PDF
                if not self.compile_latex():
                    self.log("Build failed: LaTeX compilation failed", "ERROR")
                    op.add_metadata("latex_compilation_passed", False)
                    return False
                op.add_metadata("latex_compilation_passed", True)

                # Step 9: Validate PDF
                if not self.validate_pdf():
                    self.log("Build failed: PDF validation failed", "ERROR")
                    op.add_metadata("pdf_validation_passed", False)
                    return False
                op.add_metadata("pdf_validation_passed", True)

                # Step 10: Copy final PDF
                self.copy_final_pdf()

                # Step 11: Word count analysis
                self.run_word_count_analysis()

                # Build completed - let CLI framework handle success messaging

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
                # Log once with detailed context, don't duplicate
                logger.error(f"Unexpected build error: {e}")
                if self.performance_tracker:
                    self.performance_tracker.end_operation("complete_build", metadata={"error": str(e)})
                op.add_metadata("build_successful", False)
                op.add_metadata("error", str(e))
                return False

    # Alias for compatibility with CLI code
    def run(self) -> bool:
        """Run the build process (alias for build method)."""
        return self.build()
