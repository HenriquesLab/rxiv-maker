"""Content management command implementations for rxiv-maker CLI."""

from typing import Optional

from .base import BaseCommand, CommandExecutionError


class ValidationCommand(BaseCommand):
    """Validation command implementation using the framework."""

    def execute_operation(self, detailed: bool = False, no_doi: bool = False, interactive: bool = False) -> bool:
        """Execute manuscript validation.

        Args:
            detailed: Show detailed validation report
            no_doi: Skip DOI validation
            interactive: Use interactive mode to select validation options

        Returns:
            True if validation passed, False otherwise
        """
        # Interactive mode: prompt for validation options
        if interactive:
            from ...cli.interactive import prompt_multi_select

            self.console.print("\n🔍 Validation Options", style="bold blue")
            self.console.print("Select validation options to enable:\n", style="dim")

            options = [
                ("detailed", "Show detailed validation report"),
                ("doi", "Validate DOI references"),
            ]

            selected = prompt_multi_select(title="Validation Options", items=options, default_selected=["doi"])

            if selected is not None:
                detailed = "detailed" in selected
                no_doi = "doi" not in selected  # Invert: if DOI not selected, skip it

                # Show selected options
                self.console.print("\n✓ Selected options:", style="green")
                if detailed:
                    self.console.print("  • Detailed validation report", style="dim")
                if not no_doi:
                    self.console.print("  • DOI validation enabled", style="dim")
                if not detailed and no_doi:
                    self.console.print("  • Basic validation only", style="dim")
                self.console.print()  # Blank line
            else:
                # User cancelled - use defaults
                self.console.print("⚠️  Using default validation options", style="yellow")
                detailed = False
                no_doi = False

        with self.create_progress() as progress:
            task = progress.add_task("Running validation...", total=None)

            # Import and run validation directly
            from rxiv_maker.engines.operations.validate import validate_manuscript

            # Determine DOI validation setting
            enable_doi_validation = None if not no_doi else False

            # Run validation using PathManager
            if self.path_manager is None:
                raise CommandExecutionError("Path manager not initialized")
            validation_passed = validate_manuscript(
                manuscript_path=str(self.path_manager.manuscript_path),
                detailed=detailed,
                verbose=self.verbose,
                include_info=False,
                check_latex=True,
                enable_doi_validation=enable_doi_validation,
            )

            if validation_passed:
                progress.update(task, description="✅ Validation completed")
                self.success_message("Validation passed!")
            else:
                progress.update(task, description="❌ Validation failed")
                self.error_message(
                    "Validation failed. See details above.",
                    "Run with --detailed for more information or use 'rxiv pdf --skip-validation' to build anyway",
                )
                raise CommandExecutionError("Validation failed")

            return validation_passed


class CleanCommand(BaseCommand):
    """Clean command implementation using the framework."""

    def execute_operation(
        self,
        output_dir: str = "output",
        figures_only: bool = False,
        output_only: bool = False,
        arxiv_only: bool = False,
        temp_only: bool = False,
        cache_only: bool = False,
        all_files: bool = False,
        interactive: bool = False,
    ) -> None:
        """Execute cleanup operation.

        Args:
            output_dir: Output directory to clean
            figures_only: Clean only generated figures
            output_only: Clean only output directory
            arxiv_only: Clean only arXiv files
            temp_only: Clean only temporary files
            cache_only: Clean only cache files
            all_files: Clean all generated files
            interactive: Use interactive mode to select what to clean
        """
        import sys

        # Interactive mode: prompt for what to clean
        if interactive:
            from ...cli.interactive import prompt_confirm, prompt_multi_select

            self.console.print("\n🧹 Cleanup Options", style="bold blue")
            self.console.print("Select what you want to clean:\n", style="dim")

            options = [
                ("figures", "Generated figures (FIGURES/ directory)"),
                ("output", "Output directory (PDFs, LaTeX files)"),
                ("arxiv", "arXiv submission files"),
                ("temp", "Temporary files (.aux, .log, etc.)"),
                ("cache", "Cache files (.rxiv-cache/)"),
            ]

            selected = prompt_multi_select(title="Cleanup Options", items=options, default_selected=[])

            if selected is not None and len(selected) > 0:
                # Map selections to flags
                figures_only = "figures" in selected
                output_only = "output" in selected
                arxiv_only = "arxiv" in selected
                temp_only = "temp" in selected
                cache_only = "cache" in selected

                # Show selected options
                self.console.print("\n✓ Will clean:", style="green")
                if figures_only:
                    self.console.print("  • Generated figures", style="dim")
                if output_only:
                    self.console.print("  • Output directory", style="dim")
                if arxiv_only:
                    self.console.print("  • arXiv submission files", style="dim")
                if temp_only:
                    self.console.print("  • Temporary files", style="dim")
                if cache_only:
                    self.console.print("  • Cache files", style="dim")

                # Confirm before proceeding
                if not prompt_confirm("\nProceed with cleanup?", default=False):
                    self.console.print("Cleanup cancelled", style="yellow")
                    return

                self.console.print()  # Blank line
            elif selected is None:
                # User cancelled
                self.console.print("⚠️  Cleanup cancelled", style="yellow")
                return
            else:
                # No options selected - ask if they want to clean everything
                if prompt_confirm("\nNo specific options selected. Clean all files?", default=False):
                    # all_files = True  # Will clean all since no specific flags are set
                    self.console.print("\n✓ Will clean all generated files", style="green")
                    self.console.print()  # Blank line
                else:
                    self.console.print("Cleanup cancelled", style="yellow")
                    return

        with self.create_progress() as progress:
            task = progress.add_task("Cleaning files...", total=None)

            try:
                # Import cleanup command
                from rxiv_maker.engines.operations.cleanup import main as cleanup_main

                # Prepare arguments
                args = []
                if figures_only:
                    args.append("--figures-only")
                if output_only:
                    args.append("--output-only")
                if arxiv_only:
                    args.append("--arxiv-only")
                if temp_only:
                    args.append("--temp-only")
                if cache_only:
                    args.append("--cache-only")
                if self.verbose:
                    args.append("--verbose")

                # Add paths using PathManager
                if self.path_manager is None:
                    raise CommandExecutionError("Path manager not initialized")

                args.extend(["--manuscript-path", str(self.path_manager.manuscript_path)])
                args.extend(["--output-dir", str(self.path_manager.output_dir)])

                # Save original argv and replace
                original_argv = sys.argv
                sys.argv = ["cleanup"] + args

                try:
                    cleanup_main()
                    progress.update(task, description="✅ Cleanup completed")
                    self.success_message("Cleanup completed!")

                    # Show what was cleaned
                    if figures_only:
                        self.console.print("🎨 Generated figures cleaned", style="blue")
                    elif output_only:
                        self.console.print("📁 Output directory cleaned", style="blue")
                    elif arxiv_only:
                        self.console.print("📦 arXiv files cleaned", style="blue")
                    elif temp_only:
                        self.console.print("🧹 Temporary files cleaned", style="blue")
                    elif cache_only:
                        self.console.print("💾 Cache files cleaned", style="blue")
                    else:
                        self.console.print("🧹 All generated files cleaned", style="blue")

                except SystemExit as e:
                    progress.update(task, description="❌ Cleanup failed")
                    if e.code != 0:
                        self.error_message("Cleanup failed. See details above.")
                        raise CommandExecutionError("Cleanup failed") from e

                finally:
                    sys.argv = original_argv

            except Exception as e:
                progress.update(task, description="❌ Cleanup failed")
                self.error_message(f"Cleanup operation failed: {e}")
                raise CommandExecutionError(f"Cleanup failed: {e}") from e


class BibliographyFixCommand(BaseCommand):
    """Bibliography fix command implementation using the framework."""

    def execute_operation(self, dry_run: bool = False) -> None:
        """Execute bibliography fixes.

        Args:
            dry_run: Preview fixes without applying them
        """
        if self.path_manager is None:
            raise CommandExecutionError("Path manager not initialized")

        with self.create_progress() as progress:
            task = progress.add_task("Fixing bibliography...", total=None)

            try:
                # Import bibliography fixing class directly
                from rxiv_maker.engines.operations.fix_bibliography import BibliographyFixer

                # Create and use the BibliographyFixer class directly
                fixer = BibliographyFixer(str(self.path_manager.manuscript_path))
                result = fixer.fix_bibliography(dry_run=dry_run)

                success = result.get("total_fixes", 0) >= 0  # Consider any result a success

                if success:
                    progress.update(task, description="✅ Bibliography fixes completed")
                    if dry_run:
                        self.success_message("Bibliography fixes preview completed!")
                        if result.get("total_fixes", 0) > 0:
                            self.console.print(f"📝 Found {result['total_fixes']} potential fixes", style="blue")
                    else:
                        self.success_message("Bibliography fixes applied successfully!")
                        if result.get("total_fixes", 0) > 0:
                            self.console.print(f"🔧 Applied {result['total_fixes']} fixes", style="blue")
                else:
                    progress.update(task, description="❌ Bibliography fixing failed")
                    self.error_message("Bibliography fixing failed. See details above.")
                    raise CommandExecutionError("Bibliography fixing failed")

            except Exception as e:
                progress.update(task, description="❌ Bibliography fixing failed")
                self.error_message(f"Bibliography fixing failed: {e}")
                raise CommandExecutionError(f"Bibliography fixing failed: {e}") from e


class BibliographyAddCommand(BaseCommand):
    """Bibliography add command implementation using the framework."""

    def execute_operation(self, dois: tuple[str, ...], overwrite: bool = False) -> None:
        """Execute bibliography entry addition.

        Args:
            dois: One or more DOIs or URLs containing DOIs to add
            overwrite: Overwrite existing entries
        """
        if self.path_manager is None:
            raise CommandExecutionError("Path manager not initialized")

        with self.create_progress() as progress:
            task = progress.add_task(f"Adding {len(dois)} bibliography entries...", total=None)

            try:
                # Import bibliography adding class directly
                from rxiv_maker.engines.operations.add_bibliography import BibliographyAdder

                # Create and use the BibliographyAdder class directly
                adder = BibliographyAdder(str(self.path_manager.manuscript_path), overwrite=overwrite)

                # Add each DOI/URL
                total_added = 0
                for doi in dois:
                    try:
                        if adder.add_entry_from_input(doi):
                            total_added += 1
                            if self.verbose:
                                self.console.print(f"✅ Added entry for: {doi}", style="green")
                    except Exception as e:
                        self.console.print(f"⚠️  Failed to add {doi}: {e}", style="yellow")

                if total_added > 0:
                    progress.update(task, description="✅ Bibliography entries added")
                    self.success_message(f"Added {total_added} out of {len(dois)} bibliography entries successfully!")
                    self.console.print(f"📚 Inputs processed: {', '.join(dois)}", style="blue")
                else:
                    progress.update(task, description="❌ No entries were added")
                    self.error_message("No bibliography entries could be added. See details above.")
                    raise CommandExecutionError("No bibliography entries could be added")

            except Exception as e:
                progress.update(task, description="❌ Bibliography adding failed")
                self.error_message(f"Bibliography adding failed: {e}")
                raise CommandExecutionError(f"Bibliography adding failed: {e}") from e


class BibliographyListCommand(BaseCommand):
    """Bibliography list command implementation using the framework."""

    def execute_operation(self, format: str = "text", include_raw: bool = False) -> None:
        """List all bibliography entries.

        Args:
            format: Output format ('text' or 'json')
            include_raw: Include raw BibTeX entry in output (JSON only)
        """
        if self.path_manager is None:
            raise CommandExecutionError("Path manager not initialized")

        try:
            import json

            from rxiv_maker.utils.bibliography_parser import entry_to_dict, parse_bib_file

            # Find bibliography file
            bib_path = self.path_manager.manuscript_path / "03_REFERENCES.bib"

            # Also check config for custom bibliography file name
            config_path = self.path_manager.manuscript_path / "00_CONFIG.yml"
            if config_path.exists():
                try:
                    import yaml

                    config = yaml.safe_load(config_path.read_text())
                    bib_filename = config.get("bibliography", "03_REFERENCES.bib")
                    if not bib_filename.endswith(".bib"):
                        bib_filename += ".bib"
                    bib_path = self.path_manager.manuscript_path / bib_filename
                except Exception:  # nosec B110
                    # Silently fall back to default if config is invalid or missing bibliography key
                    pass

            if not bib_path.exists():
                if format == "json":
                    # Output empty JSON array for programmatic consumption
                    import sys

                    sys.stdout.write("[]\n")
                    sys.stdout.flush()
                else:
                    self.error_message(f"Bibliography file not found: {bib_path}")
                return

            # Parse bibliography file
            entries = parse_bib_file(bib_path)

            if format == "json":
                # Output JSON format for programmatic consumption
                import sys

                entries_dict = [entry_to_dict(entry, include_raw=include_raw) for entry in entries]
                json_output = json.dumps(entries_dict, indent=2, ensure_ascii=False)
                # Use sys.stdout directly to avoid Rich console formatting
                sys.stdout.write(json_output)
                sys.stdout.write("\n")
                sys.stdout.flush()
            else:
                # Human-readable text format
                if not entries:
                    self.console.print("No bibliography entries found.", style="yellow")
                else:
                    self.console.print(f"\n📚 Found {len(entries)} bibliography entries:\n", style="bold blue")

                    for entry in entries:
                        self.console.print(f"  • [{entry.entry_type}] {entry.key}", style="cyan bold")

                        # Display key fields
                        if "title" in entry.fields:
                            title = entry.fields["title"]
                            if len(title) > 80:
                                title = title[:77] + "..."
                            self.console.print(f"    Title: {title}", style="dim")

                        if "author" in entry.fields:
                            author = entry.fields["author"]
                            if len(author) > 80:
                                author = author[:77] + "..."
                            self.console.print(f"    Author: {author}", style="dim")

                        if "year" in entry.fields:
                            self.console.print(f"    Year: {entry.fields['year']}", style="dim")

                        if "doi" in entry.fields:
                            self.console.print(f"    DOI: {entry.fields['doi']}", style="dim")

                        self.console.print()  # Blank line between entries

                    self.console.print(f"Total entries: {len(entries)}", style="bold green")

        except FileNotFoundError as e:
            if format == "json":
                # Output empty JSON array for programmatic consumption
                import sys

                sys.stdout.write("[]\n")
                sys.stdout.flush()
            else:
                self.error_message(f"Bibliography file not found: {e}")
        except Exception as e:
            if format == "json":
                # Output error as JSON for programmatic handling
                import sys

                error_output = json.dumps({"error": str(e)}, ensure_ascii=False)
                sys.stdout.write(error_output)
                sys.stdout.write("\n")
                sys.stdout.flush()
            else:
                self.error_message(f"Failed to list bibliography entries: {e}")
            raise CommandExecutionError(f"Bibliography listing failed: {e}") from e


class FiguresCommand(BaseCommand):
    """Figures command implementation using the framework."""

    def execute_operation(self, force: bool = False, figures_dir: Optional[str] = None) -> None:
        """Execute figure generation.

        Args:
            force: Force regeneration of all figures
            figures_dir: Custom figures directory path
        """
        # Set figures directory using PathManager
        if figures_dir is None:
            if self.path_manager is None:
                raise CommandExecutionError("Path manager not initialized")
            figures_dir = str(self.path_manager.manuscript_path / "FIGURES")

        with self.create_progress() as progress:
            task = progress.add_task("Generating figures...", total=None)

            try:
                if self.verbose:
                    self.console.print("📦 Importing FigureGenerator class...", style="blue")

                from rxiv_maker.engines.operations.generate_figures import FigureGenerator

                if self.verbose:
                    self.console.print("📦 Successfully imported FigureGenerator!", style="green")

                # Create FigureGenerator
                if self.path_manager is None:
                    raise CommandExecutionError("Path manager not initialized")
                generator = FigureGenerator(
                    figures_dir=figures_dir,
                    output_dir=figures_dir,
                    output_format="pdf",
                    r_only=False,
                    enable_content_caching=not force,
                    manuscript_path=str(self.path_manager.manuscript_path),
                )

                if self.verbose:
                    mode_msg = "force mode - ignoring cache" if force else "normal mode"
                    self.console.print(f"🎨 Starting figure generation ({mode_msg})...", style="blue")

                generator.process_figures()

                progress.update(task, description="✅ Figure generation completed")
                self.success_message("Figures generated successfully!", f"Figures directory: {figures_dir}")

            except Exception as e:
                progress.update(task, description="❌ Figure generation failed")
                self.error_message(f"Figure generation failed: {e}", "Check your figure scripts for errors")
                raise CommandExecutionError(f"Figure generation failed: {e}") from e


__all__ = [
    "ValidationCommand",
    "CleanCommand",
    "BibliographyFixCommand",
    "BibliographyAddCommand",
    "BibliographyListCommand",
    "FiguresCommand",
]
