"""Workflow command implementations for rxiv-maker CLI."""

import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
import yaml

from ...templates import get_template_manager
from .base import BaseCommand, CommandExecutionError


class InitCommand(BaseCommand):
    """Initialize command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup to handle manuscript path for initialization.

        Args:
            ctx: Click context containing command options
            manuscript_path: Optional manuscript path override
        """
        from rxiv_maker.core.environment_manager import EnvironmentManager

        # Extract common options from context
        self.verbose = ctx.obj.get("verbose", False) or EnvironmentManager.is_verbose()
        self.engine = "local"  # Only local engine is supported

        # Store manuscript path without PathManager validation since we're creating the directory
        if manuscript_path is None:
            manuscript_path = EnvironmentManager.get_manuscript_path() or "MANUSCRIPT"

        # Store the raw path for use in execute_operation
        self.raw_manuscript_path = manuscript_path

        if self.verbose:
            self.console.print(f"📁 Will create manuscript at: {manuscript_path}", style="blue")

    def execute_operation(
        self,
        force: bool = False,
        no_interactive: bool = False,
        validate: bool = False,
        template: str = "default",
    ) -> None:
        """Execute manuscript initialization.

        Args:
            force: Force overwrite existing files
            no_interactive: Deprecated (command is always non-interactive)
            validate: Run validation after initialization
            template: Template type to use (default, minimal, journal, preprint)
        """
        # Get manuscript path from raw path (set during setup_common_options)
        manuscript_path = self.raw_manuscript_path

        manuscript_dir = Path(manuscript_path)

        # Check if directory exists and fail if --force not used
        if manuscript_dir.exists() and not force:
            raise CommandExecutionError(f"Directory '{manuscript_path}' already exists. Use --force to overwrite.")

        # Always use default values (non-interactive mode only)
        title = "Your Manuscript Title"
        author_name = "Your Name"
        author_email = "your.email@example.com"
        author_orcid = "0000-0000-0000-0000"
        author_affiliation = "Your Institution"

        with self.create_progress() as progress:
            task = progress.add_task(f"Initializing manuscript (template: {template})...", total=2)

            try:
                # Use the new centralized template system
                template_manager = get_template_manager(template)

                # Create all manuscript files from templates
                created_files = template_manager.create_manuscript(
                    manuscript_dir,
                    title=title,
                    author_name=author_name,
                    author_email=author_email,
                    author_orcid=author_orcid,
                    author_affiliation=author_affiliation,
                )
                progress.advance(task)

                progress.update(task, description="✅ Manuscript initialized")
                progress.advance(task)

                self.success_message("Manuscript initialized successfully!", f"Directory: {manuscript_dir.absolute()}")

                if self.verbose:
                    self.console.print("\n📄 Created files:", style="blue")
                    for file_type, file_path in created_files.items():
                        self.console.print(f"  • {file_type}: {file_path.name}", style="dim")

                # Run validation if requested
                if validate:
                    self.console.print("\n🔍 Running validation...")
                    try:
                        from rxiv_maker.engines.operations.validate import validate_manuscript

                        validation_passed = validate_manuscript(
                            str(manuscript_dir), detailed=False, verbose=False, include_info=False, check_latex=False
                        )

                        if validation_passed:
                            self.console.print("✅ Template validation passed!", style="green")
                        else:
                            self.console.print("⚠️  Template validation had issues", style="yellow")

                    except Exception as e:
                        self.console.print(f"⚠️  Validation failed: {e}", style="yellow")

                # Show next steps
                self.console.print("\n📋 Next steps:", style="bold blue")
                self.console.print(f"  1. cd {manuscript_path}")
                self.console.print("  2. Edit 00_CONFIG.yml with your manuscript details")
                self.console.print("  3. Write your content in 01_MAIN.md")
                self.console.print("  4. Add figures to FIGURES/ directory")
                self.console.print("  5. Run 'rxiv pdf' to generate your manuscript")

            except Exception as e:
                progress.update(task, description="❌ Initialization failed")
                self.error_message(f"Initialization failed: {e}")
                raise CommandExecutionError(f"Initialization failed: {e}") from e


class BuildCommand(BaseCommand):
    """Build/PDF command implementation using the framework."""

    def execute_operation(
        self,
        output_dir: str = "output",
        force_figures: bool = False,
        skip_validation: bool = False,
        track_changes: Optional[str] = None,
        keep_output: bool = False,
        docx: bool = False,
        resolve_dois: bool = False,
        debug: bool = False,
        quiet: bool = False,
        container_mode: Optional[str] = None,
    ) -> None:
        """Execute PDF build process.

        Args:
            output_dir: Output directory for generated files
            force_figures: Force regeneration of all figures
            skip_validation: Skip validation step
            track_changes: Track changes against specified git tag
            keep_output: Preserve existing output directory
            docx: Also export to DOCX format
            resolve_dois: Attempt to resolve missing DOIs (for DOCX export)
            debug: Enable debug output
            quiet: Suppress non-critical warnings
            container_mode: Container behavior mode
        """
        from rxiv_maker.core.progress_framework import OperationType, get_progress_manager, progress_operation
        from rxiv_maker.engines.operations.build_manager import BuildManager

        # Initialize progress manager with our centralized framework
        progress_manager = get_progress_manager()

        # Initialize variables to capture build results
        success = False
        pdf_path = None
        build_manager = None

        with progress_operation(progress_manager, OperationType.BUILD, "Building PDF manuscript") as build_op:
            try:
                if self.path_manager is None:
                    raise CommandExecutionError("Path manager not initialized")

                # Create build manager with our centralized path management
                build_manager = BuildManager(
                    manuscript_path=str(self.path_manager.manuscript_path),
                    output_dir=output_dir,
                    force_figures=force_figures,
                    skip_validation=skip_validation,
                    track_changes_tag=track_changes,
                    clear_output=not keep_output,
                    verbose=self.verbose or debug,
                    quiet=quiet,
                )

                # Progress already shown by progress_operation context manager

                # Execute build with centralized error handling
                success = build_manager.build()

                if success:
                    pdf_path = build_manager.output_pdf
                else:
                    self.error_message("PDF build failed", "Check the logs above for detailed error information")
                    raise CommandExecutionError("Build failed")

            except Exception as e:
                progress_manager.report_error(build_op, str(e))
                # Don't duplicate error logging - progress_manager already logged it
                # Just provide helpful tips for specific error types
                if "validation" in str(e).lower():
                    self.info_message("💡 Tip: Use --skip-validation to bypass validation checks")
                elif "figures" in str(e).lower():
                    self.info_message("💡 Tip: Check your figure scripts or use --force-figures")

                raise CommandExecutionError("Build failed") from e

        # Handle success messages outside progress context to avoid persistent progress bar
        if success and pdf_path:
            self.success_message("PDF build completed successfully!", f"Generated: {pdf_path}")

            # Show build statistics using our centralized progress framework
            if build_manager and hasattr(build_manager, "get_build_stats"):
                stats = build_manager.get_build_stats()
                self.console.print(f"📊 Build time: {stats.get('duration', 'N/A')}", style="dim")

            # Export to DOCX if requested
            if docx:
                self._export_docx(resolve_dois=resolve_dois, quiet=quiet, debug=debug)

            # Show helpful tips after successful build
            self._show_build_tips()

    def _export_docx(self, resolve_dois: bool = False, quiet: bool = False, debug: bool = False) -> None:
        """Export manuscript to DOCX format after successful PDF build.

        Args:
            resolve_dois: Whether to attempt DOI resolution for missing entries
            quiet: Suppress non-essential output
            debug: Enable debug output
        """
        try:
            from ...exporters.docx_exporter import DocxExporter

            if not quiet:
                self.console.print("\n[cyan]📝 Exporting to DOCX...[/cyan]")

            exporter = DocxExporter(
                manuscript_path=str(self.path_manager.manuscript_path),
                resolve_dois=resolve_dois,
                include_footnotes=True,
            )

            docx_path = exporter.export()

            if not quiet:
                self.console.print(f"[green]✅ DOCX exported:[/green] {docx_path}")

        except Exception as e:
            self.console.print(f"[yellow]⚠️  DOCX export failed:[/yellow] {e}", err=True)
            if debug:
                import traceback

                self.console.print(f"[dim]{traceback.format_exc()}[/dim]", err=True)

    def _show_build_tips(self) -> None:
        """Show helpful tips after successful PDF build."""
        try:
            from ...utils.tips import get_build_success_tip

            # Always show tips - no configuration needed
            tip = get_build_success_tip(frequency="always")

            if tip:
                self.console.print(tip)
            else:
                # Debug: Show why no tip was displayed
                self.console.print("Debug: No tip returned from get_build_success_tip", style="dim")

        except Exception as e:
            # Tips are non-critical - don't fail if there are issues
            # Always show debug info for now to troubleshoot
            self.console.print(f"Debug: Could not load tips: {e}", style="dim")
            import traceback

            self.console.print(f"Debug: Traceback: {traceback.format_exc()}", style="dim")


class ArxivCommand(BaseCommand):
    """ArXiv command implementation using the framework."""

    def execute_operation(
        self,
        output_dir: str = "output",
        arxiv_dir: Optional[str] = None,
        zip_filename: Optional[str] = None,
        no_zip: bool = False,
    ) -> None:
        """Execute arXiv package preparation.

        Args:
            output_dir: Output directory for generated files
            arxiv_dir: Custom arXiv directory path
            zip_filename: Custom zip filename
            no_zip: Don't create zip file
        """
        import sys
        from pathlib import Path

        from rxiv_maker.engines.operations.build_manager import BuildManager
        from rxiv_maker.engines.operations.prepare_arxiv import main as prepare_arxiv_main

        if self.path_manager is None:
            raise CommandExecutionError("Path manager not initialized")

        manuscript_output_dir = str(self.path_manager.output_dir)

        # Set defaults using PathManager
        if arxiv_dir is None:
            arxiv_dir = str(Path(manuscript_output_dir) / "arxiv_submission")
        if zip_filename is None:
            zip_filename = str(Path(manuscript_output_dir) / "for_arxiv.zip")

        with self.create_progress() as progress:
            # Clear output directory first (similar to PDF command)
            task = progress.add_task("Clearing output directory...", total=None)
            if self.path_manager.output_dir.exists():
                shutil.rmtree(self.path_manager.output_dir)
            self.path_manager.output_dir.mkdir(parents=True, exist_ok=True)

            # First, ensure PDF is built
            progress.update(task, description="Checking PDF exists...")
            pdf_filename = f"{self.path_manager.manuscript_name}.pdf"
            pdf_path = self.path_manager.output_dir / pdf_filename

            if not pdf_path.exists():
                progress.update(task, description="Building PDF first...")
                build_manager = BuildManager(
                    manuscript_path=str(self.path_manager.manuscript_path),
                    output_dir=str(self.path_manager.output_dir),
                    verbose=self.verbose,
                    quiet=False,
                )
                success = build_manager.run()
                if not success:
                    self.error_message("PDF build failed. Cannot prepare arXiv package.")
                    raise CommandExecutionError("PDF build failed")

            # Prepare arXiv package
            progress.update(task, description="Preparing arXiv package...")

            # Prepare arguments using PathManager
            args = [
                "--output-dir",
                manuscript_output_dir,
                "--arxiv-dir",
                arxiv_dir,
                "--manuscript-path",
                str(self.path_manager.manuscript_path),
            ]

            if not no_zip:
                args.extend(["--zip-filename", zip_filename, "--create-zip"])

            # Save original argv and replace
            original_argv = sys.argv
            sys.argv = ["prepare_arxiv"] + args

            try:
                prepare_arxiv_main()
                progress.update(task, description="✅ arXiv package prepared")
                self.success_message("arXiv package prepared successfully!")

                if not no_zip:
                    self.console.print(f"📦 arXiv package: {zip_filename}", style="blue")

                    # Copy to manuscript directory with proper naming
                    config_path = self.path_manager.manuscript_path / "00_CONFIG.yml"
                    year, first_author = self._extract_author_and_year(config_path)

                    # Create proper filename
                    arxiv_filename = f"{year}__{first_author}_et_al__for_arxiv.zip"
                    final_path = self.path_manager.manuscript_path / arxiv_filename

                    # Copy file
                    shutil.copy2(zip_filename, final_path)
                    self.console.print(f"📋 Copied to: {final_path}", style="green")

                self.console.print("📤 Upload the package to arXiv for submission", style="yellow")

            except SystemExit as e:
                progress.update(task, description="❌ arXiv preparation failed")
                if e.code != 0:
                    self.error_message("arXiv preparation failed. See details above.")
                    raise CommandExecutionError("arXiv preparation failed") from e

            except Exception as e:
                progress.update(task, description="❌ arXiv preparation failed")
                self.error_message(f"arXiv preparation failed: {e}")
                raise CommandExecutionError(f"arXiv preparation failed: {e}") from e

            finally:
                sys.argv = original_argv

    def _extract_author_and_year(self, config_path: Path) -> tuple[str, str]:
        """Extract year and first author from manuscript configuration.

        Args:
            config_path: Path to the 00_CONFIG.yml file

        Returns:
            Tuple of (year, first_author) strings
        """
        if not config_path.exists():
            return str(datetime.now().year), "Unknown"

        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
        except (yaml.YAMLError, OSError) as e:
            self.console.print(f"⚠️  Warning: Could not parse config file {config_path}: {e}", style="yellow")
            return str(datetime.now().year), "Unknown"

        # Extract year from date
        year = str(datetime.now().year)  # Default fallback
        date_str = config.get("date", "")
        if date_str and isinstance(date_str, str):
            try:
                year = date_str.split("-")[0] if "-" in date_str else date_str
                # Validate year is numeric
                int(year)
            except (ValueError, IndexError):
                year = str(datetime.now().year)

        # Extract first author
        first_author = "Unknown"  # Default fallback
        authors = config.get("authors", [])
        if authors and isinstance(authors, list) and len(authors) > 0:
            first_author_entry = authors[0]
            if isinstance(first_author_entry, dict):
                # Handle author objects with name/surname
                name = first_author_entry.get("name", "")
                surname = first_author_entry.get("surname", "")
                if surname:
                    first_author = surname
                elif name:
                    # Extract last name from full name
                    name_parts = name.strip().split()
                    if name_parts:
                        first_author = name_parts[-1]
                    else:
                        first_author = name
            elif isinstance(first_author_entry, str):
                # Handle simple string authors
                # Extract last name (assume it's after the last space)
                name_parts = first_author_entry.strip().split()
                if name_parts:
                    first_author = name_parts[-1]

        # Clean up author name for filename and convert to lowercase
        first_author = "".join(c for c in first_author if c.isalnum() or c in "._-").lower()

        return year, first_author


class TrackChangesCommand(BaseCommand):
    """Track changes command implementation using the framework."""

    def execute_operation(
        self,
        tag: str,
        output_dir: str = "output",
        force_figures: bool = False,
        skip_validation: bool = False,
    ) -> None:
        """Execute change tracking build.

        Args:
            tag: Git tag to track changes against
            output_dir: Output directory for generated files
            force_figures: Force regeneration of all figures
            skip_validation: Skip validation step
        """
        from rxiv_maker.engines.operations.build_manager import BuildManager

        if self.path_manager is None:
            raise CommandExecutionError("Path manager not initialized")

        with self.create_progress() as progress:
            # Create build manager with track changes enabled
            task = progress.add_task("Initializing change tracking build...", total=None)
            build_manager = BuildManager(
                manuscript_path=str(self.path_manager.manuscript_path),
                output_dir=str(self.path_manager.output_dir),
                force_figures=force_figures,
                skip_validation=skip_validation,
                track_changes_tag=tag,
                verbose=self.verbose,
                quiet=False,
            )

            # Build the PDF with change tracking
            progress.update(
                task,
                description=f"Generating PDF with changes tracked against {tag}...",
            )

            try:
                success = build_manager.build()

                if success:
                    progress.update(task, description="✅ Change-tracked PDF generated successfully!")
                    self.console.print(
                        f"📄 PDF with change tracking generated: {self.path_manager.output_dir}/{self.path_manager.manuscript_name}.pdf",
                        style="green",
                    )
                    self.console.print(
                        f"🔍 Changes tracked against git tag: {tag}",
                        style="blue",
                    )
                else:
                    progress.update(task, description="❌ Failed to generate PDF with change tracking")
                    self.error_message("PDF generation with change tracking failed")
                    raise CommandExecutionError("Change tracking build failed")

            except Exception as e:
                progress.update(task, description="❌ Change tracking build failed")
                self.error_message(f"Error during change tracking build: {e}")
                raise CommandExecutionError(f"Change tracking build failed: {e}") from e


class SetupCommand(BaseCommand):
    """Setup command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since setup doesn't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since setup doesn't need engine."""
        pass

    def execute_operation(
        self,
        mode: str = "full",
        reinstall: bool = False,
        force: bool = False,
        non_interactive: bool = False,
        check_only: bool = False,
        log_file: Optional[str] = None,
    ) -> None:
        """Execute setup operation.

        Args:
            mode: Setup mode (full, python-only, system-only, minimal, core)
            reinstall: Reinstall Python dependencies
            force: Force reinstallation of existing system dependencies
            non_interactive: Run in non-interactive mode
            check_only: Only check dependencies without installing
            log_file: Path to log file for system dependency installation
        """
        from pathlib import Path

        # Show what we're about to do
        if check_only:
            self.console.print(f"🔍 Checking dependencies in {mode} mode...", style="blue")
        else:
            self.console.print(f"🔧 Setting up rxiv-maker in {mode} mode...", style="blue")

        try:
            python_success = True
            system_success = True

            # Handle Python dependencies (unless system-only mode)
            if mode != "system-only":
                # For check-only mode, skip Python environment setup if not in a Python project directory
                skip_python_setup = (
                    check_only
                    and not Path("pyproject.toml").exists()
                    and not Path("setup.py").exists()
                    and not Path("requirements.txt").exists()
                )

                if skip_python_setup:
                    if self.verbose:
                        self.console.print(
                            "ℹ️  Skipping Python environment check (not in a Python project directory)", style="dim"
                        )
                else:
                    try:
                        from rxiv_maker.engines.operations.setup_environment import main as setup_environment_main

                        # Prepare arguments for Python setup
                        args = []
                        if reinstall:
                            args.append("--reinstall")
                        if check_only:
                            args.append("--check-deps-only")
                        if self.verbose:
                            args.append("--verbose")

                        # Save original argv and replace
                        original_argv = sys.argv
                        sys.argv = ["setup_environment"] + args

                        try:
                            setup_environment_main()
                            if not check_only:
                                self.console.print("✅ Python environment setup completed!", style="green")

                        except SystemExit as e:
                            if e.code != 0:
                                python_success = False
                                self.console.print("❌ Python setup failed!", style="red")

                        finally:
                            sys.argv = original_argv

                    except Exception as e:
                        python_success = False
                        self.console.print(f"❌ Python setup error: {e}", style="red")

            # Handle system dependencies (unless python-only mode)
            if mode != "python-only":
                try:
                    from rxiv_maker.core.managers.install_manager import InstallManager, InstallMode

                    # Map setup modes to install modes
                    install_mode_map = {
                        "full": "full",
                        "system-only": "full",
                        "minimal": "minimal",
                        "core": "core",
                    }
                    install_mode = install_mode_map.get(mode, "full")

                    # Create installation manager
                    log_file_path = Path(log_file) if log_file else None
                    manager = InstallManager(
                        mode=InstallMode(install_mode),
                        verbose=self.verbose,
                        force=force,
                        interactive=not non_interactive,
                        log_file=log_file_path,
                    )

                    if check_only:
                        # Just check system dependencies
                        from rxiv_maker.install.utils.verification import verify_installation

                        verification_results = verify_installation(verbose=self.verbose)

                        # Check if all required components are available
                        failed_components = [comp for comp, status in verification_results.items() if not status]
                        if failed_components:
                            system_success = False
                            self.console.print(
                                f"❌ Missing system dependencies: {', '.join(failed_components)}", style="red"
                            )
                        else:
                            self.console.print("✅ System dependencies check passed!", style="green")
                    else:
                        # Install system dependencies
                        system_success = manager.install()
                        if system_success:
                            self.console.print("✅ System dependencies installed!", style="green")
                        else:
                            self.console.print("❌ System dependency installation failed!", style="red")

                except Exception as e:
                    system_success = False
                    self.console.print(f"❌ System dependency error: {e}", style="red")

            # Final status
            overall_success = python_success and system_success

            if check_only:
                if overall_success:
                    self.success_message("All dependency checks completed successfully!")
                else:
                    self.error_message("Some dependency checks failed. See details above.")
                    raise CommandExecutionError("Dependency checks failed")
            else:
                if overall_success:
                    self.success_message("Setup completed successfully!")
                    self.console.print("💡 Run 'rxiv check-installation' to verify your setup", style="dim")
                else:
                    self.error_message("Setup completed with errors. See details above.")
                    raise CommandExecutionError("Setup failed")

        except KeyboardInterrupt:
            self.console.print("\n⏹️  Setup interrupted by user", style="yellow")
            raise CommandExecutionError("Setup interrupted") from KeyboardInterrupt()
        except Exception as e:
            self.error_message(f"Unexpected error during setup: {e}")
            raise CommandExecutionError(f"Setup failed: {e}") from e


__all__ = [
    "InitCommand",
    "BuildCommand",
    "ArxivCommand",
    "TrackChangesCommand",
    "SetupCommand",
]
