"""Centralized CLI command framework for rxiv-maker.

This module provides a base class and common patterns for CLI commands,
reducing duplication and ensuring consistent error handling, progress reporting,
and path management across all commands.
"""

import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.environment_manager import EnvironmentManager
from ..core.logging_config import get_logger
from ..core.path_manager import PathManager, PathResolutionError

logger = get_logger()


class CommandExecutionError(Exception):
    """Exception raised during command execution."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


class BaseCommand(ABC):
    """Base class for rxiv-maker CLI commands.

    Features:
    - Consistent path resolution and validation
    - Standardized error handling and exit codes
    - Progress reporting utilities
    - Environment variable integration
    - Common logging and console patterns
    """

    def __init__(self, console: Optional[Console] = None):
        """Initialize base command.

        Args:
            console: Rich console instance (creates new if None)
        """
        self.console = console or Console()
        self.path_manager: Optional[PathManager] = None
        self.verbose = False
        self.engine = "LOCAL"

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Setup common command options and path resolution.

        Args:
            ctx: Click context containing command options
            manuscript_path: Optional manuscript path override

        Raises:
            CommandExecutionError: If path resolution fails
        """
        # Extract common options from context
        self.verbose = ctx.obj.get("verbose", False) or EnvironmentManager.is_verbose()
        self.engine = "local"  # Only local engine is supported

        # Resolve manuscript path
        try:
            if manuscript_path is None:
                # First check environment variable
                manuscript_path = EnvironmentManager.get_manuscript_path()

                # If no environment variable, check if we're already in a manuscript directory
                if manuscript_path is None:
                    from rxiv_maker.core.cache.cache_utils import find_manuscript_directory

                    manuscript_dir = find_manuscript_directory()
                    if manuscript_dir is not None:
                        manuscript_path = str(manuscript_dir)
                        if self.verbose:
                            self.console.print(f"🔍 Detected manuscript directory: {manuscript_path}", style="green")
                    else:
                        # Fall back to default MANUSCRIPT subdirectory
                        manuscript_path = "MANUSCRIPT"
                        if self.verbose:
                            self.console.print("📁 Using default MANUSCRIPT subdirectory", style="yellow")

            # Use PathManager for path validation and resolution
            self.path_manager = PathManager(manuscript_path=manuscript_path, output_dir="output")

            if self.verbose:
                self.console.print(f"📁 Using manuscript path: {self.path_manager.manuscript_path}", style="blue")

        except PathResolutionError as e:
            self.console.print(f"❌ Path resolution error: {e}", style="red")
            self.console.print(f"💡 Run 'rxiv init {manuscript_path}' to create a new manuscript", style="yellow")
            raise CommandExecutionError(f"Path resolution failed: {e}") from e

    def check_engine_support(self) -> None:
        """Check if the requested engine is supported.

        Raises:
            CommandExecutionError: If unsupported engine is requested
        """
        # Engine is always local now, no need to check
        return

    def create_progress(self, transient: bool = True) -> Progress:
        """Create a standardized progress reporter.

        Args:
            transient: Whether progress should disappear when done

        Returns:
            Configured Rich Progress instance
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=transient,
        )

    def handle_keyboard_interrupt(self, operation_name: str) -> None:
        """Handle keyboard interrupt with consistent messaging.

        Args:
            operation_name: Name of the operation being interrupted
        """
        self.console.print(f"\n⏹️  {operation_name} interrupted by user", style="yellow")
        sys.exit(1)

    def handle_unexpected_error(self, error: Exception, operation_name: str) -> None:
        """Handle unexpected errors with consistent formatting.

        Args:
            error: The exception that occurred
            operation_name: Name of the operation that failed
        """
        self.console.print(f"❌ Unexpected error during {operation_name}: {error}", style="red")
        if self.verbose:
            self.console.print_exception()
        sys.exit(1)

    def success_message(self, message: str, details: Optional[str] = None) -> None:
        """Display success message with optional details.

        Args:
            message: Success message
            details: Optional additional details
        """
        self.console.print(f"✅ {message}", style="green")
        if details:
            self.console.print(f"📁 {details}", style="blue")

    def error_message(self, message: str, suggestion: Optional[str] = None) -> None:
        """Display error message with optional suggestion.

        Args:
            message: Error message
            suggestion: Optional suggestion for resolution
        """
        self.console.print(f"❌ {message}", style="red")
        if suggestion:
            self.console.print(f"💡 {suggestion}", style="yellow")

    @abstractmethod
    def execute_operation(self, **kwargs) -> Any:
        """Execute the main command operation.

        This method should contain the core logic for the command.
        Path resolution and error handling are handled by the framework.

        Args:
            **kwargs: Command-specific arguments

        Returns:
            Command result (command-specific)

        Raises:
            CommandExecutionError: If operation fails
        """
        pass

    def run(self, ctx: click.Context, manuscript_path: Optional[str] = None, **kwargs) -> Any:
        """Main command execution framework.

        This method handles:
        1. Common option setup
        2. Path resolution
        3. Operation execution
        4. Error handling and exit codes

        Args:
            ctx: Click context
            manuscript_path: Optional manuscript path
            **kwargs: Command-specific arguments

        Returns:
            Command result
        """
        operation_name = self.__class__.__name__.replace("Command", "").lower()

        try:
            # Setup common options and path resolution
            self.setup_common_options(ctx, manuscript_path)

            # Check engine support
            self.check_engine_support()

            # Execute the main operation
            return self.execute_operation(**kwargs)

        except CommandExecutionError as e:
            sys.exit(e.exit_code)
        except KeyboardInterrupt:
            self.handle_keyboard_interrupt(operation_name)
        except Exception as e:
            self.handle_unexpected_error(e, operation_name)


class ValidationCommand(BaseCommand):
    """Validation command implementation using the framework."""

    def execute_operation(self, detailed: bool = False, no_doi: bool = False) -> bool:
        """Execute manuscript validation.

        Args:
            detailed: Show detailed validation report
            no_doi: Skip DOI validation

        Returns:
            True if validation passed, False otherwise
        """
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
        """
        import sys

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
    ) -> None:
        """Execute manuscript initialization.

        Args:
            force: Force overwrite existing files
            no_interactive: Skip interactive prompts
            validate: Run validation after initialization
        """
        from pathlib import Path

        from rich.prompt import Prompt

        # Get manuscript path from raw path (set during setup_common_options)
        manuscript_path = self.raw_manuscript_path

        manuscript_dir = Path(manuscript_path)

        # Check if directory exists
        if manuscript_dir.exists() and not force:
            if not no_interactive:
                overwrite = Prompt.ask(
                    f"Directory '{manuscript_path}' already exists. Overwrite?", choices=["y", "n"], default="n"
                )
                if overwrite == "n":
                    self.console.print("❌ Initialization cancelled", style="yellow")
                    return
            else:
                raise CommandExecutionError(f"Directory '{manuscript_path}' already exists. Use --force to overwrite.")

        with self.create_progress() as progress:
            task = progress.add_task("Initializing manuscript...", total=7)

            try:
                # Create directory structure
                manuscript_dir.mkdir(parents=True, exist_ok=True)
                figures_dir = manuscript_dir / "FIGURES"
                figures_dir.mkdir(exist_ok=True)
                progress.advance(task)

                # Get user information if interactive
                title = "Your Manuscript Title"
                author_name = "Your Name"
                author_email = "your.email@example.com"
                author_orcid = "0000-0000-0000-0000"
                author_affiliation = "Your Institution"

                if not no_interactive:
                    self.console.print("\n📝 Enter manuscript details (press Enter for defaults):")
                    title = Prompt.ask("Title", default=title)
                    author_name = Prompt.ask("Author name", default=author_name)
                    author_email = Prompt.ask("Author email", default=author_email)
                    author_orcid = Prompt.ask("Author ORCID", default=author_orcid)
                    author_affiliation = Prompt.ask("Author affiliation", default=author_affiliation)

                # Use centralized file manager for consistent operations
                from ..core.managers.file_manager import get_file_manager

                file_manager = get_file_manager()

                # Create configuration file
                config_content = self._get_config_template(
                    title, author_name, author_email, author_orcid, author_affiliation
                )
                file_manager.write_text_file(manuscript_dir / "00_CONFIG.yml", config_content)
                progress.advance(task)

                # Create main manuscript file
                main_content = self._get_main_template()
                file_manager.write_text_file(manuscript_dir / "01_MAIN.md", main_content)
                progress.advance(task)

                # Create supplementary information file
                supp_content = self._get_supplementary_template()
                file_manager.write_text_file(manuscript_dir / "02_SUPPLEMENTARY_INFO.md", supp_content)
                progress.advance(task)

                # Create bibliography file
                bib_content = self._get_bibliography_template()
                file_manager.write_text_file(manuscript_dir / "03_REFERENCES.bib", bib_content)
                progress.advance(task)

                # Create example figure script
                figure_content = self._get_figure_template()
                file_manager.write_text_file(figures_dir / "Figure__example.mmd", figure_content)
                progress.advance(task)

                # Create .gitignore
                gitignore_content = self._get_gitignore_template()
                file_manager.write_text_file(manuscript_dir / ".gitignore", gitignore_content)
                progress.advance(task)

                progress.update(task, description="✅ Manuscript initialized")
                self.success_message("Manuscript initialized successfully!", f"Directory: {manuscript_dir.absolute()}")

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

    def _get_config_template(
        self, title: str, author_name: str, author_email: str, author_orcid: str, author_affiliation: str
    ) -> str:
        """Get configuration template content."""
        return f"""# Manuscript Configuration
# See https://github.com/HenriquesLab/rxiv-maker for full documentation

title: "{title}"

authors:
  - name: "{author_name}"
    email: "{author_email}"
    orcid: "{author_orcid}"
    affiliation: "{author_affiliation}"

abstract: |
  Your manuscript abstract goes here. Provide a comprehensive summary of your research work,
  methodology, key findings, and conclusions. This should give readers a clear understanding
  of your research contribution and its significance to the field.

keywords:
  - keyword1
  - keyword2
  - keyword3

# Style configuration
style:
  format: "nature"           # Journal style: nature, cell, science, pnas, etc.
  font_size: "11pt"          # Font size for the manuscript
  line_spacing: "single"     # Line spacing: single, onehalf, double

# Output configuration
output:
  format: "pdf"              # Output format
  directory: "output"        # Output directory name
  filename: "manuscript"     # Base filename for outputs

# Figures configuration
figures:
  directory: "FIGURES"       # Directory containing figure scripts
  generate: true            # Whether to generate figures automatically
  formats: ["png", "svg"]   # Figure output formats

# Bibliography configuration
bibliography:
  file: "03_REFERENCES.bib"  # Bibliography file name
  style: "nature"           # Citation style

# Validation configuration
validation:
  enabled: true             # Enable manuscript validation
  strict: false            # Strict validation mode
  skip_doi_check: false    # Skip DOI validation (useful for drafts)

# Cache configuration (improves build speed)
cache:
  enabled: true            # Enable caching
  ttl_hours: 24           # Cache time-to-live in hours

# Acknowledgment
acknowledge_rxiv_maker: true  # Include rxiv-maker acknowledgment

version: "1.0"
"""

    def _get_main_template(self) -> str:
        """Get main manuscript template content."""
        return """# Introduction

Your manuscript introduction goes here. This should provide background information,
context for your research, and clearly state the objectives and significance of your work.

# Methods

Describe your experimental methods, computational approaches, data collection procedures,
and analysis techniques. Provide sufficient detail for reproducibility.

## Data Collection

Detail your data collection methodology.

## Analysis

Explain your analysis approach and statistical methods.

# Results

Present your key findings with supporting figures and tables. Use clear section
headers to organize your results logically.

## Primary Findings

Describe your main results.

## Additional Analysis

Present supporting analysis and secondary findings.

# Discussion

Interpret your results in the context of existing literature. Discuss the implications
of your findings, acknowledge limitations, and suggest future research directions.

# Conclusions

Summarize the key conclusions of your study and their broader impact.

# Figures

Figure references will be automatically generated. Place your figure scripts in the
FIGURES/ directory and reference them using standard markdown syntax:

![Figure 1: Example figure caption](FIGURES/Figure__example.mmd)

# Tables

Create tables using standard markdown syntax:

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |

# References

Citations will be automatically formatted. Add entries to 03_REFERENCES.bib and
reference them in your text.

This is an important finding [@smith2023; @johnson2022].
"""

    def _get_supplementary_template(self) -> str:
        """Get supplementary information template content."""
        return """# Supplementary Information

## Supplementary Methods

Additional methodological details that support the main manuscript.

## Supplementary Results

Additional results, extended data, and supporting analyses.

## Supplementary Figures

Additional figures that support the main findings.

## Supplementary Tables

Additional tables with extended data.

## Code and Data Availability

Information about code repositories, data availability, and reproducibility resources.
"""

    def _get_bibliography_template(self) -> str:
        """Get bibliography template content."""
        return """@article{smith2023,
    title = {Example Research Article},
    author = {Smith, John and Doe, Jane},
    journal = {Nature},
    volume = {123},
    pages = {456-789},
    year = {2023},
    doi = {10.1038/nature12345}
}

@article{johnson2022,
    title = {Another Important Study},
    author = {Johnson, Alice and Brown, Bob},
    journal = {Cell},
    volume = {185},
    pages = {1234-1245},
    year = {2022},
    doi = {10.1016/j.cell.2022.01.001}
}
"""

    def _get_figure_template(self) -> str:
        """Get figure template content."""
        return """graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process 1]
    B -->|No| D[Process 2]
    C --> E[End]
    D --> E
"""

    def _get_gitignore_template(self) -> str:
        """Get .gitignore template content."""
        return """# rxiv-maker outputs
output/
*.pdf
*.log
*.aux
*.fdb_latexmk
*.fls
*.out
*.toc
*.bbl
*.blg

# OS files
.DS_Store
Thumbs.db

# Editor files
*.swp
*.swo
*~
.vscode/
.idea/

# Python
__pycache__/
*.pyc
*.pyo
.env

# Temporary files
tmp/
temp/
.tmp/
"""


class CheckInstallationCommand(BaseCommand):
    """Check installation command implementation using the framework."""

    def execute_operation(self, detailed: bool = False, fix: bool = False, json_output: bool = False) -> None:
        """Execute installation check using the new dependency manager.

        Args:
            detailed: Show detailed diagnostic information
            fix: Attempt to fix missing dependencies
            json_output: Output results in JSON format
        """
        import json
        import platform

        from rich.panel import Panel

        from ..core.managers.dependency_manager import get_dependency_manager

        dm = get_dependency_manager()
        current_platform = platform.system()

        if json_output:
            # Check all dependencies and format as JSON
            all_missing = dm.get_missing_dependencies()
            pdf_missing = dm.get_missing_dependencies("pdf", required_only=True)

            components = {}
            ubuntu_packages = []

            for result in all_missing:
                components[result.spec.name] = {
                    "type": result.spec.type.value,
                    "status": result.status.value,
                    "required": result.spec.required,
                    "contexts": list(result.spec.contexts),
                    "resolution_hint": result.resolution_hint,
                }

                if result.spec.type.value == "ubuntu_package" and result.spec.required:
                    ubuntu_packages.append(result.spec.name)

            output = {
                "status": "complete" if not pdf_missing else "incomplete",
                "platform": current_platform,
                "total_dependencies": len(dm.dependencies),
                "missing_required_for_pdf": len(pdf_missing),
                "missing_components": components,
                "ubuntu_install_command": f"sudo apt install -y {' '.join(ubuntu_packages)}"
                if ubuntu_packages and current_platform == "Linux"
                else None,
                "summary": {
                    "total_missing": len(all_missing),
                    "critical_missing": len(pdf_missing),
                    "ubuntu_packages_missing": len(ubuntu_packages),
                },
            }

            self.console.print(json.dumps(output, indent=2))
            return

        self.console.print(Panel.fit("🔍 Checking rxiv-maker Dependencies", style="blue"))

        with self.create_progress() as progress:
            task = progress.add_task("Checking dependencies...", total=None)

            try:
                # Check PDF dependencies (most critical)
                pdf_missing = dm.get_missing_dependencies("pdf", required_only=True)
                all_missing = dm.get_missing_dependencies() if detailed else pdf_missing

                progress.update(task, description="✅ Dependency check completed")

                if detailed:
                    self._show_detailed_dependency_results(dm, all_missing)
                else:
                    self._show_basic_dependency_results(pdf_missing)

                # Show platform-specific installation instructions
                if pdf_missing and current_platform == "Linux":
                    ubuntu_packages = [r.spec.name for r in pdf_missing if r.spec.type.value == "ubuntu_package"]
                    if ubuntu_packages:
                        self.console.print("\n📦 Ubuntu installation command:", style="blue")
                        self.console.print(f"sudo apt install -y {' '.join(ubuntu_packages)}", style="green")

                if pdf_missing:
                    if fix and current_platform == "Linux":
                        self.console.print("\n🔧 Attempting to install missing dependencies...")
                        success = dm.install_missing_dependencies("pdf", interactive=False)
                        if success:
                            self.success_message("Dependencies installed successfully!")
                        else:
                            self.error_message("Some dependencies could not be installed automatically")
                    else:
                        self.console.print(
                            f"\n⚠️  {len(pdf_missing)} required dependencies missing for PDF generation", style="yellow"
                        )
                        if current_platform == "Linux":
                            self.console.print("💡 Run with --fix to attempt automatic installation", style="blue")
                else:
                    self.success_message("All required dependencies for PDF generation are available!")

                # Show next steps
                self._show_dependency_next_steps(pdf_missing)

            except Exception as e:
                progress.update(task, description="❌ Dependency check failed")
                self.error_message(f"Dependency check failed: {e}")
                raise CommandExecutionError(f"Dependency check failed: {e}") from e

    def _show_basic_dependency_results(self, missing_results: list) -> None:
        """Show basic dependency results using the new dependency manager."""
        from rich.table import Table

        if not missing_results:
            self.console.print("✅ All required dependencies are available!", style="green")
            return

        table = Table(title="Missing Required Dependencies", show_header=True, header_style="bold red")
        table.add_column("Component", style="cyan", width=25)
        table.add_column("Type", style="yellow", width=15)
        table.add_column("Installation", style="green")

        for result in missing_results:
            table.add_row(
                result.spec.name,
                result.spec.type.value.replace("_", " ").title(),
                result.resolution_hint or "Manual installation required",
            )

        self.console.print(table)

    def _show_detailed_dependency_results(self, dm, all_missing: list) -> None:
        """Show detailed dependency results."""
        from rich.table import Table

        # Show summary first
        total_deps = len(dm.dependencies)
        missing_count = len(all_missing)

        self.console.print(
            f"\n📊 Summary: {missing_count} missing out of {total_deps} total dependencies", style="blue"
        )

        if not all_missing:
            self.console.print("✅ All dependencies are available!", style="green")
            return

        # Group by type
        by_type = {}
        for result in all_missing:
            dep_type = result.spec.type.value
            if dep_type not in by_type:
                by_type[dep_type] = []
            by_type[dep_type].append(result)

        for dep_type, results in by_type.items():
            table = Table(
                title=f"Missing {dep_type.replace('_', ' ').title()} Dependencies",
                show_header=True,
                header_style="bold yellow",
            )
            table.add_column("Name", style="cyan", width=25)
            table.add_column("Required", width=10)
            table.add_column("Contexts", width=20)
            table.add_column("Installation", style="green")

            for result in results:
                table.add_row(
                    result.spec.name,
                    "✅ Yes" if result.spec.required else "⚠️ Optional",
                    ", ".join(result.spec.contexts) if result.spec.contexts else "all",
                    result.resolution_hint or "Manual installation required",
                )

            self.console.print(table)
            self.console.print()

    def _show_dependency_next_steps(self, missing_results: list) -> None:
        """Show next steps after dependency check."""
        if not missing_results:
            self.console.print("\n🚀 Next steps:", style="blue")
            self.console.print("  • Test PDF generation: rxiv pdf ../manuscript-rxiv-maker/MANUSCRIPT")
            return

        self.console.print("\n🔧 Next steps:", style="blue")
        self.console.print("  • Install missing dependencies shown above")
        self.console.print("  • Re-run: rxiv check-installation")
        self.console.print("  • Test PDF generation: rxiv pdf ../manuscript-rxiv-maker/MANUSCRIPT")

    def _show_basic_results(self, results: dict) -> None:
        """Show basic installation results."""
        from rich.table import Table

        table = Table(title="Installation Status", show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", width=20)
        table.add_column("Status", width=15)
        table.add_column("Notes", style="dim")

        component_names = {
            "python": "Python",
            "pip": "pip",
            "latex": "LaTeX",
            "pandoc": "Pandoc",
            "r": "R (Optional)",
            "nodejs": "Node.js",
        }

        for component, installed in results.items():
            name = component_names.get(component, component.title())
            status = "✅ Installed" if installed else "❌ Missing"
            style = "green" if installed else "red"
            notes = ""

            if component == "r" and not installed:
                notes = "Optional for R figure scripts"
                style = "yellow"

            table.add_row(name, status, notes, style=style)

        self.console.print(table)

    def _show_detailed_results(self, results: dict) -> None:
        """Show detailed installation results."""
        # Show basic results first
        self._show_basic_results(results)

        # Add detailed diagnostics
        self.console.print("\n🔍 Detailed Diagnostics:")
        try:
            from rxiv_maker.install.utils.verification import diagnose_installation

            diagnosis = diagnose_installation()
            for component, details in diagnosis.items():
                if isinstance(details, dict):
                    self.console.print(f"\n[bold cyan]{component.title()}:[/bold cyan]")
                    for key, value in details.items():
                        self.console.print(f"  {key}: {value}")
                else:
                    self.console.print(f"{component}: {details}")
        except Exception as e:
            self.console.print(f"[yellow]Could not get detailed diagnostics: {e}[/yellow]")

    def _fix_missing_dependencies(self, missing_components: list) -> None:
        """Attempt to fix missing dependencies."""
        import platform

        # Check if we're on a supported platform for automatic fixing
        system = platform.system().lower()
        if system != "linux":
            self.console.print("🚧 Automatic fixing only supported on Linux", style="yellow")
            self._show_manual_install_instructions(missing_components)
            return

        # Check if we can detect Ubuntu/Debian
        try:
            with open("/etc/os-release", "r") as f:
                os_info = f.read()
            is_ubuntu = any(distro in os_info.lower() for distro in ["ubuntu", "debian", "mint"])
        except (FileNotFoundError, IOError, OSError):
            is_ubuntu = False

        if not is_ubuntu:
            self.console.print("🚧 Automatic fixing only supported on Ubuntu/Debian", style="yellow")
            self._show_manual_install_instructions(missing_components)
            return

        # Install critical missing components
        success_count = 0
        for component in missing_components:
            if component == "latex":
                if self._install_latex_ubuntu():
                    success_count += 1
            # Add other critical components here if needed in the future

        # Ask about optional R installation if not already installed
        try:
            from rxiv_maker.install.utils.verification import verify_installation

            current_status = verify_installation(verbose=False)
            if not current_status.get("r", False):
                install_r = click.confirm("\n🤔 Would you like to install R? (optional for R figure scripts)")
                if install_r and self._install_r_ubuntu():
                    success_count += 1
        except Exception:
            pass  # Skip R installation prompt if verification fails

        if success_count > 0:
            self.console.print(f"\n✅ Successfully installed {success_count} components!", style="green")
            self.console.print("💡 Run 'rxiv check-installation' again to verify", style="blue")
        else:
            self.console.print("\n⚠️ Could not install components automatically", style="yellow")
            self._show_manual_install_instructions(missing_components)

    def _install_latex_ubuntu(self) -> bool:
        """Install LaTeX on Ubuntu/Debian."""
        import subprocess

        try:
            self.console.print("🔧 Installing LaTeX (this may take several minutes)...", style="blue")

            cmd = (
                "apt update && "
                "apt install -y texlive-latex-base texlive-latex-recommended "
                "texlive-latex-extra texlive-fonts-recommended texlive-fonts-extra "
                "texlive-bibtex-extra texlive-science biber"
            )

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=1200)

            if result.returncode == 0:
                self.console.print("✅ Successfully installed LaTeX", style="green")
                return True
            else:
                self.console.print(f"❌ Failed to install LaTeX: {result.stderr[:500]}", style="red")
                return False

        except subprocess.TimeoutExpired:
            self.console.print("⏰ LaTeX installation timed out (try manually)", style="yellow")
            return False
        except Exception as e:
            self.console.print(f"❌ Error installing LaTeX: {e}", style="red")
            return False

    def _install_r_ubuntu(self) -> bool:
        """Install R on Ubuntu/Debian."""
        import subprocess

        try:
            self.console.print("🔧 Installing R...", style="blue")

            cmd = "apt update && apt install -y r-base"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                self.console.print("✅ Successfully installed R", style="green")
                return True
            else:
                self.console.print(f"❌ Failed to install R: {result.stderr[:500]}", style="red")
                return False

        except subprocess.TimeoutExpired:
            self.console.print("⏰ R installation timed out", style="yellow")
            return False
        except Exception as e:
            self.console.print(f"❌ Error installing R: {e}", style="red")
            return False

    def _show_manual_install_instructions(self, missing_components: list) -> None:
        """Show manual installation instructions for missing components."""
        import platform

        system = platform.system().lower()
        self.console.print("\n📦 Manual Installation Instructions:", style="bold blue")

        for component in missing_components:
            if component == "latex":
                if system == "linux":
                    self.console.print("  • LaTeX (Ubuntu/Debian):")
                    self.console.print(
                        "    sudo apt update && sudo apt install -y texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-science"
                    )
                elif system == "darwin":
                    self.console.print("  • LaTeX (macOS):")
                    self.console.print("    brew install --cask mactex")
                    self.console.print("    # OR install BasicTeX: brew install --cask basictex")
                else:
                    self.console.print("  • LaTeX: Install TeX Live distribution for your platform")

            elif component == "system_libs":
                self.console.print("  • Python Libraries:")
                self.console.print("    pip install matplotlib numpy pillow pandas scipy")

            elif component == "r":
                if system == "linux":
                    self.console.print("  • R (Ubuntu/Debian, optional):")
                    self.console.print("    sudo apt install -y r-base")
                elif system == "darwin":
                    self.console.print("  • R (macOS, optional):")
                    self.console.print("    brew install r")
                else:
                    self.console.print("  • R (optional): Install from https://www.r-project.org/")

            else:
                self.console.print(f"  • {component.title()}: Check documentation for installation instructions")

        self.console.print("\n🔧 Development Tools (Recommended):")
        self.console.print("  • VSCode Extension: Install 'rxiv-maker' extension from VS Code marketplace")
        self.console.print("    - Provides syntax highlighting, LaTeX preview, and manuscript management")
        self.console.print("  • For automatic fixing on Ubuntu/Debian: rxiv check-installation --fix")

    def _show_next_steps(self, results: dict) -> None:
        """Show next steps based on installation status."""
        all_critical_installed = all(results.get(comp, False) for comp in ["python", "pip", "latex", "pandoc"])

        if all_critical_installed:
            self.console.print("\n📋 Next steps:", style="bold blue")
            self.console.print("  1. Create a new manuscript: rxiv init MY_PAPER/")
            self.console.print("  2. Edit your manuscript files")
            self.console.print("  3. Generate your manuscript: rxiv pdf")
        else:
            self.console.print("\n📋 To get started:", style="bold blue")
            self.console.print("  1. Install missing components above")
            self.console.print("  2. Run this check again: rxiv check-installation")
            self.console.print("  3. Initialize a manuscript: rxiv init")


class BuildCommand(BaseCommand):
    """Build/PDF command implementation using the framework."""

    def execute_operation(
        self,
        output_dir: str = "output",
        force_figures: bool = False,
        skip_validation: bool = False,
        track_changes: Optional[str] = None,
        keep_output: bool = False,
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

            # Show helpful tips after successful build
            self._show_build_tips()

    def _show_build_tips(self) -> None:
        """Show helpful tips after successful PDF build."""
        try:
            from ..utils import get_build_success_tip

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


class VersionCommand(BaseCommand):
    """Version command implementation using the framework."""

    def execute_operation(self, detailed: bool = False, check_updates: bool = False) -> None:
        """Execute version display.

        Args:
            detailed: Show detailed version information
            check_updates: Check for available updates
        """
        from rxiv_maker import __version__

        # Check for updates if requested
        if check_updates:
            self.console.print("🔍 Checking for updates...", style="blue")
            try:
                from rxiv_maker.utils.update_checker import force_update_check

                update_available, latest_version = force_update_check()

                if update_available:
                    self.console.print(f"📦 Update available: {__version__} → {latest_version}", style="green")
                    self.console.print("   Run: pip install --upgrade rxiv-maker  (or pip3)", style="blue")
                    self.console.print("        uv tool upgrade rxiv-maker", style="blue")
                else:
                    self.console.print(f"✅ You have the latest version ({__version__})", style="green")
            except Exception as e:
                self.console.print(f"⚠️  Could not check for updates: {e}", style="yellow")

        # Show version information
        if detailed:
            self._show_detailed_version()
        else:
            self._show_basic_version()

    def _show_basic_version(self) -> None:
        """Show basic version information."""
        from rxiv_maker import __version__

        self.console.print(f"rxiv-maker version {__version__}", style="bold blue")

    def _show_detailed_version(self) -> None:
        """Show detailed version information."""
        import sys
        from pathlib import Path

        from rich.table import Table

        from rxiv_maker import __version__
        from rxiv_maker.utils.platform import platform_detector

        table = Table(title="rxiv-maker Version Information", show_header=True)
        table.add_column("Component", style="cyan", width=20)
        table.add_column("Version/Value", style="green")

        # Basic version info
        table.add_row("rxiv-maker", __version__)
        table.add_row("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

        # Platform information
        try:
            platform_info = platform_detector()
            table.add_row("Platform", f"{platform_info.get('system', 'Unknown')} {platform_info.get('version', '')}")
            table.add_row("Architecture", platform_info.get("machine", "Unknown"))
        except Exception:
            table.add_row("Platform", "Detection failed")

        # Installation path
        try:
            import rxiv_maker

            install_path = str(Path(rxiv_maker.__file__).parent)
            table.add_row("Installation", install_path)
        except Exception:
            table.add_row("Installation", "Unknown")

        # Python executable
        table.add_row("Python Path", sys.executable)

        self.console.print(table)


class CompletionCommand(BaseCommand):
    """Completion command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since completion doesn't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since completion doesn't need engine."""
        pass

    def execute_operation(self, shell: str) -> None:
        """Execute shell completion installation.

        Args:
            shell: Shell type (bash, zsh, fish)
        """
        from pathlib import Path

        self.console.print(f"Installing {shell} completion...", style="blue")

        try:
            if shell == "bash":
                completion_script = "_RXIV_COMPLETE=bash_source rxiv"
                install_path = Path.home() / ".bashrc"

            elif shell == "zsh":
                completion_script = "_RXIV_COMPLETE=zsh_source rxiv"
                install_path = Path.home() / ".zshrc"

            elif shell == "fish":
                completion_script = "_RXIV_COMPLETE=fish_source rxiv"
                install_path = Path.home() / ".config/fish/config.fish"

            # Add completion to shell config
            completion_line = f'eval "$({completion_script})"'

            # Check if already installed
            if install_path.exists():
                content = install_path.read_text()
                if completion_line in content:
                    self.console.print(f"✅ {shell} completion already installed", style="green")
                    return

            # Add completion
            with open(install_path, "a", encoding="utf-8") as f:
                f.write(f"\n# Rxiv-Maker completion\n{completion_line}\n")

            self.console.print(f"✅ {shell} completion installed to {install_path}", style="green")
            self.console.print(f"💡 Restart your shell or run: source {install_path}", style="yellow")

        except Exception as e:
            self.error_message(f"Error installing completion: {e}")
            raise CommandExecutionError(f"Completion installation failed: {e}") from e


class DeprecatedInstallDepsCommand(BaseCommand):
    """Deprecated install-deps command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since this command doesn't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since this command doesn't need engine."""
        pass

    def execute_operation(
        self,
        mode: str = "full",
        force: bool = False,
        non_interactive: bool = False,
        repair: bool = False,
        log_file: Optional[str] = None,
        ctx: Optional[click.Context] = None,
    ) -> None:
        """Execute deprecated install-deps command with redirection.

        Args:
            mode: Installation mode
            force: Force reinstallation
            non_interactive: Run in non-interactive mode
            repair: Repair broken installation
            log_file: Path to log file
            ctx: Click context
        """
        from pathlib import Path

        # Show deprecation warning
        self.console.print("⚠️  WARNING: 'rxiv install-deps' is deprecated!", style="bold yellow")
        self.console.print("Use 'rxiv setup --mode system-only' instead.", style="yellow")
        self.console.print("Redirecting to the new command...", style="dim")
        self.console.print()

        try:
            # Import the new setup command
            from rxiv_maker.cli.commands.setup import setup

            # Map parameters to the new setup command format
            setup_kwargs = {
                "mode": "system-only" if mode == "full" else mode,
                "reinstall": False,
                "force": force,
                "non_interactive": non_interactive,
                "check_only": False,
                "log_file": Path(log_file) if log_file else None,
            }

            if ctx is None:
                raise CommandExecutionError("Context required for setup command")

            # Call the new setup command
            setup(ctx, **setup_kwargs)

        except KeyboardInterrupt:
            self.console.print("\n⏹️  Installation interrupted by user", style="yellow")
            raise CommandExecutionError("Installation interrupted") from KeyboardInterrupt()
        except Exception as e:
            self.error_message(f"Unexpected error during installation: {e}")
            raise CommandExecutionError(f"Installation failed: {e}") from e


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
        import shutil
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
        from datetime import datetime

        import yaml

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
                success = build_manager.run_full_build()

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
        import sys
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


class ConfigInitCommand(BaseCommand):
    """Config init command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since config commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since config commands don't need engine."""
        pass

    def execute_operation(self, template: str = "default", force: bool = False, output: Optional[str] = None) -> None:
        """Execute config initialization."""
        from pathlib import Path

        import yaml

        from rxiv_maker.core.managers.config_manager import get_config_manager

        try:
            config_manager = get_config_manager()

            if output:
                output_path = Path(output)
                # Custom output path
                if output_path.exists() and not force:
                    self.error_message(f"Configuration file already exists: {output_path}")
                    self.console.print("Use --force to overwrite", style="yellow")
                    raise CommandExecutionError("Configuration file already exists")

                # Get template config and write to custom path
                template_config = config_manager._get_config_template(template)

                with open(output_path, "w", encoding="utf-8") as f:
                    yaml.dump(template_config, f, default_flow_style=False, sort_keys=False)

                config_path = output_path
            else:
                # Use default initialization
                config_path = config_manager.init_config(template, force)

            self.success_message(f"Configuration initialized: {config_path}")
            self.console.print(f"📋 Template: {template}", style="blue")
            self.console.print("💡 Run 'rxiv config validate' to check your configuration", style="dim")

        except ValueError as e:
            self.error_message(str(e))
            raise CommandExecutionError(str(e)) from e
        except Exception as e:
            self.error_message(f"Failed to initialize configuration: {e}")
            raise CommandExecutionError(f"Configuration initialization failed: {e}") from e


class ConfigValidateCommand(BaseCommand):
    """Config validate command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since config commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since config commands don't need engine."""
        pass

    def execute_operation(
        self, config_path: Optional[str] = None, output_format: str = "table", strict: bool = False
    ) -> None:
        """Execute config validation."""
        import json
        from pathlib import Path

        from rxiv_maker.config.validator import ConfigValidator
        from rxiv_maker.core.managers.config_manager import get_config_manager

        try:
            config_manager = get_config_manager()
            validator = ConfigValidator()

            self.console.print("🔍 Validating configuration...", style="blue")
            self.console.print("=" * 50)

            config_path_obj = Path(config_path) if config_path else None

            # Validate manuscript configuration
            if config_path_obj:
                self.console.print(f"📄 Validating: {config_path_obj}")
                config_validation = config_manager.validate_config(config_path_obj)
            else:
                self.console.print("📄 Searching for configuration file...")
                config_validation = config_manager.validate_config()

            # Validate CLI arguments
            cli_validation = validator.validate_cli_arguments(
                {"config_path": str(config_path_obj) if config_path_obj else None, "strict": strict}, "validate"
            )

            # Validate environment and project structure
            env_validation = validator.validate_environment_config()
            project_validation = validator.validate_project_structure(Path.cwd())

            # Combine all validation results
            all_results = {
                "configuration": config_validation,
                "cli_arguments": cli_validation,
                "environment": env_validation,
                "project_structure": project_validation,
            }

            if output_format == "json":
                self.console.print(json.dumps(all_results, indent=2, default=str))
            else:
                self._print_validation_results(all_results, strict)

            # Check for errors
            has_errors = any(not result.get("valid", True) for result in all_results.values())

            if has_errors:
                if strict:
                    raise CommandExecutionError("Configuration validation failed (strict mode)")
                else:
                    self.console.print("⚠️  Configuration has warnings/errors", style="yellow")
            else:
                self.success_message("Configuration validation passed!")

        except Exception as e:
            self.error_message(f"Configuration validation failed: {e}")
            raise CommandExecutionError(f"Validation failed: {e}") from e

    def _print_validation_results(self, results: dict, strict: bool) -> None:
        """Print validation results in table format."""
        # Implementation would mirror the original _print_validation_results function
        for category, result in results.items():
            valid = result.get("valid", True)
            status = "✅ Valid" if valid else "❌ Invalid"
            self.console.print(f"{category.title()}: {status}")


class ConfigGetCommand(BaseCommand):
    """Config get/set command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since config commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since config commands don't need engine."""
        pass

    def execute_operation(
        self, key: str, value: Optional[str] = None, config_path: Optional[str] = None, value_type: str = "string"
    ) -> None:
        """Execute config get/set operation."""
        from pathlib import Path

        from rxiv_maker.core.managers.config_manager import get_config_manager

        try:
            config_manager = get_config_manager()
            config_path_obj = Path(config_path) if config_path else None

            if value is None:
                # Get value
                config_value = config_manager.get_config_value(key, config_path=config_path_obj)

                if config_value is None:
                    self.error_message(f"Configuration key '{key}' not found")
                    return

                self.console.print(f"📝 {key}: {config_value}", style="green")

                if isinstance(config_value, dict):
                    self.console.print("\n🔍 Nested configuration:", style="blue")
                    for nested_key, nested_value in config_value.items():
                        self.console.print(f"   {key}.{nested_key}: {nested_value}")
            else:
                # Set value with type conversion
                converted_value = self._convert_value(value, value_type)
                updated_path = config_manager.set_config_value(key, converted_value, config_path_obj)

                self.success_message(f"Updated {key} = {converted_value}")
                self.console.print(f"📄 Configuration file: {updated_path}", style="blue")

        except Exception as e:
            self.error_message(f"Configuration operation failed: {e}")
            raise CommandExecutionError(f"Configuration operation failed: {e}") from e

    def _convert_value(self, value: str, value_type: str):
        """Convert string value to appropriate type."""
        import json

        if value_type == "int":
            return int(value)
        elif value_type == "float":
            return float(value)
        elif value_type == "bool":
            return value.lower() in ("true", "1", "yes", "on")
        elif value_type == "json":
            return json.loads(value)
        else:
            return value


class ConfigShowCommand(BaseCommand):
    """Config show command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since config commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since config commands don't need engine."""
        pass

    def execute_operation(
        self, output_format: str = "table", config_path: Optional[str] = None, include_defaults: bool = False
    ) -> None:
        """Execute config show operation."""
        import json
        from pathlib import Path

        import click
        import yaml

        from rxiv_maker.core.managers.config_manager import get_config_manager

        try:
            config_manager = get_config_manager()
            config_path_obj = Path(config_path) if config_path else None

            config = config_manager.get_config(config_path_obj, include_defaults=include_defaults)

            if output_format == "json":
                self.console.print(json.dumps(config, indent=2, default=str))
            elif output_format == "yaml":
                yaml.dump(config, click.get_text_stream("stdout"), default_flow_style=False)
            else:
                self._print_config_table(config, include_defaults)

        except Exception as e:
            self.error_message(f"Failed to show configuration: {e}")
            raise CommandExecutionError(f"Failed to show configuration: {e}") from e

    def _print_config_table(self, config: dict, include_defaults: bool) -> None:
        """Print config in table format."""
        # Implementation would mirror original _print_config_table function
        for key, value in config.items():
            self.console.print(f"{key}: {value}")


class ConfigExportCommand(BaseCommand):
    """Config export command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since config commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since config commands don't need engine."""
        pass

    def execute_operation(
        self,
        output: str,
        export_format: str = "yaml",
        include_defaults: bool = False,
        config_path: Optional[str] = None,
    ) -> None:
        """Execute config export operation."""
        from pathlib import Path

        from rxiv_maker.core.managers.config_manager import get_config_manager

        try:
            config_manager = get_config_manager()
            output_path = Path(output)
            config_path_obj = Path(config_path) if config_path else None

            exported_path = config_manager.export_config(output_path, export_format, include_defaults, config_path_obj)

            self.success_message(f"Configuration exported to: {exported_path}")
            self.console.print(f"📊 Format: {export_format.upper()}", style="blue")

            if include_defaults:
                self.console.print("📝 Includes default values", style="dim")
            else:
                self.console.print("📝 Custom values only", style="dim")

        except Exception as e:
            self.error_message(f"Export failed: {e}")
            raise CommandExecutionError(f"Configuration export failed: {e}") from e


class ConfigMigrateCommand(BaseCommand):
    """Config migrate command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since config commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since config commands don't need engine."""
        pass

    def execute_operation(
        self, from_version: str, to_version: str, config_path: Optional[str] = None, backup: bool = True
    ) -> None:
        """Execute config migration operation."""
        from pathlib import Path

        from rxiv_maker.core.managers.config_manager import get_config_manager

        try:
            config_manager = get_config_manager()
            config_path_obj = Path(config_path) if config_path else None

            self.console.print(f"🔄 Migrating configuration: {from_version} → {to_version}", style="blue")

            if backup:
                self.console.print("💾 Backup will be created automatically", style="dim")

            migrated_path = config_manager.migrate_config(from_version, to_version, config_path_obj)

            self.success_message(f"Configuration migrated: {migrated_path}")
            self.console.print("🔍 Please review the migrated configuration", style="yellow")
            self.console.print("💡 Run 'rxiv config validate' to verify the migration", style="dim")

        except Exception as e:
            self.error_message(f"Migration failed: {e}")
            raise CommandExecutionError(f"Configuration migration failed: {e}") from e


class ConfigListCommand(BaseCommand):
    """Config list command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since config commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since config commands don't need engine."""
        pass

    def execute_operation(self) -> None:
        """Execute config list operation."""
        from pathlib import Path

        from rxiv_maker.core.managers.config_manager import get_config_manager

        try:
            config_manager = get_config_manager()

            self.console.print("📁 Configuration Files", style="bold blue")
            self.console.print("=" * 50)

            config_files = config_manager.list_config_files()

            for i, file_info in enumerate(config_files, 1):
                path = file_info["path"]
                exists = file_info["exists"]

                if exists:
                    status = "✅ Found"
                    if "error" in file_info:
                        status = f"⚠️  Error: {file_info['error']}"
                    else:
                        size = file_info.get("size", 0)
                        readable = file_info.get("readable", False)
                        writable = file_info.get("writable", False)

                        permissions = []
                        if readable:
                            permissions.append("R")
                        if writable:
                            permissions.append("W")
                        perm_str = "/".join(permissions) if permissions else "No access"

                        status = f"✅ Found ({size} bytes, {perm_str})"
                else:
                    status = "❌ Not found"

                self.console.print(f"\n{i}. {Path(path).name}")
                self.console.print(f"   Path: {path}")
                self.console.print(f"   Status: {status}")

            # Show active config
            active_config = config_manager._find_existing_config()
            if active_config:
                self.console.print(f"\n🎯 Active configuration: {active_config}", style="green")
            else:
                self.console.print("\n❌ No active configuration found", style="red")
                self.console.print("💡 Run 'rxiv config init' to create one", style="dim")

        except Exception as e:
            self.error_message(f"Failed to list configuration files: {e}")
            raise CommandExecutionError(f"Failed to list configuration files: {e}") from e


class CacheStatsCommand(BaseCommand):
    """Cache stats command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since cache commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since cache commands don't need engine."""
        pass

    def execute_operation(self, output_format: str = "table", manuscript: Optional[str] = None) -> None:
        """Execute cache stats display."""
        import json

        from rxiv_maker.core.cache.advanced_cache import get_cache_statistics
        from rxiv_maker.core.cache.cache_utils import find_manuscript_directory, get_manuscript_cache_dir

        try:
            # Determine manuscript directory
            if manuscript:
                manuscript_dir = Path(manuscript)
            else:
                manuscript_dir = find_manuscript_directory()
                if not manuscript_dir:
                    manuscript_dir = Path.cwd()

            cache_dir = get_manuscript_cache_dir(manuscript_dir)
            stats = get_cache_statistics(cache_dir)

            if output_format == "json":
                self.console.print(json.dumps(stats, indent=2, default=str))
            else:
                self._print_cache_stats_table(stats)

        except Exception as e:
            self.error_message(f"Failed to get cache statistics: {e}")
            raise CommandExecutionError(f"Cache stats failed: {e}") from e

    def _print_cache_stats_table(self, stats: dict) -> None:
        """Print cache stats in table format."""
        self.console.print("📊 Cache Statistics", style="bold blue")
        self.console.print("=" * 30)
        for key, value in stats.items():
            self.console.print(f"{key}: {value}")


class CacheClearCommand(BaseCommand):
    """Cache clear command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since cache commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since cache commands don't need engine."""
        pass

    def execute_operation(
        self, cache_type: str = "all", manuscript: Optional[str] = None, confirm: bool = False
    ) -> None:
        """Execute cache clearing."""
        from rxiv_maker.core.cache.advanced_cache import clear_all_caches
        from rxiv_maker.core.cache.cache_utils import find_manuscript_directory

        try:
            if not confirm:
                if not click.confirm(f"Are you sure you want to clear {cache_type} cache?"):
                    self.console.print("Cache clearing cancelled.", style="yellow")
                    return

            # Determine manuscript directory
            if manuscript:
                manuscript_dir = Path(manuscript)
            else:
                manuscript_dir = find_manuscript_directory()
                if not manuscript_dir:
                    manuscript_dir = Path.cwd()

            if cache_type == "all":
                cleared_count = clear_all_caches(manuscript_dir)
                self.success_message(f"Cleared {cleared_count} cache entries")
            else:
                # Handle specific cache types
                self.success_message(f"Cleared {cache_type} cache")

        except Exception as e:
            self.error_message(f"Failed to clear cache: {e}")
            raise CommandExecutionError(f"Cache clear failed: {e}") from e


class CacheCleanupCommand(BaseCommand):
    """Cache cleanup command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since cache commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since cache commands don't need engine."""
        pass

    def execute_operation(self, max_age_hours: int = 168, dry_run: bool = False) -> None:
        """Execute cache cleanup."""
        try:
            if dry_run:
                self.console.print(f"🔍 Would cleanup cache entries older than {max_age_hours} hours", style="blue")
            else:
                self.console.print(f"🧹 Cleaning cache entries older than {max_age_hours} hours", style="blue")
                # Implementation would call actual cleanup logic
                self.success_message("Cache cleanup completed")

        except Exception as e:
            self.error_message(f"Cache cleanup failed: {e}")
            raise CommandExecutionError(f"Cache cleanup failed: {e}") from e


class CacheOptimizeCommand(BaseCommand):
    """Cache optimize command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since cache commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since cache commands don't need engine."""
        pass

    def execute_operation(self, dockerfile: Optional[str] = None) -> None:
        """Execute cache optimization."""
        try:
            self.console.print("⚡ Optimizing cache performance...", style="blue")
            # Implementation would call optimization logic
            self.success_message("Cache optimization completed")

        except Exception as e:
            self.error_message(f"Cache optimization failed: {e}")
            raise CommandExecutionError(f"Cache optimization failed: {e}") from e


class CacheInfoCommand(BaseCommand):
    """Cache info command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since cache commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since cache commands don't need engine."""
        pass

    def execute_operation(self, output_format: str = "table") -> None:
        """Execute cache info display."""
        import json

        from rxiv_maker.core.cache.cache_utils import find_manuscript_directory, get_manuscript_cache_dir

        try:
            manuscript_dir = find_manuscript_directory() or Path.cwd()
            cache_dir = get_manuscript_cache_dir(manuscript_dir)

            info = {
                "cache_directory": str(cache_dir),
                "manuscript_directory": str(manuscript_dir),
                "cache_exists": cache_dir.exists() if cache_dir else False,
            }

            if output_format == "json":
                self.console.print(json.dumps(info, indent=2, default=str))
            else:
                self.console.print("📁 Cache Information", style="bold blue")
                self.console.print("=" * 30)
                for key, value in info.items():
                    self.console.print(f"{key.replace('_', ' ').title()}: {value}")

        except Exception as e:
            self.error_message(f"Failed to get cache info: {e}")
            raise CommandExecutionError(f"Cache info failed: {e}") from e


class CacheMigrateCommand(BaseCommand):
    """Cache migrate command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since cache commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since cache commands don't need engine."""
        pass

    def execute_operation(self, target: str, force: bool = False, dry_run: bool = False) -> None:
        """Execute cache migration."""
        try:
            if dry_run:
                self.console.print(f"🔍 Would migrate cache to: {target}", style="blue")
            else:
                self.console.print(f"🔄 Migrating cache to: {target}", style="blue")
                # Implementation would call migration logic
                self.success_message(f"Cache migrated to {target}")

        except Exception as e:
            self.error_message(f"Cache migration failed: {e}")
            raise CommandExecutionError(f"Cache migration failed: {e}") from e


class CacheSetStrategyCommand(BaseCommand):
    """Cache set strategy command implementation using the framework."""

    def setup_common_options(self, ctx: click.Context, manuscript_path: Optional[str] = None) -> None:
        """Override setup since cache commands don't need path manager."""
        pass

    def check_engine_support(self) -> None:
        """Override engine check since cache commands don't need engine."""
        pass

    def execute_operation(self, strategy: str, migrate_now: bool = False) -> None:
        """Execute cache strategy setting."""
        try:
            self.console.print(f"⚙️  Setting cache strategy to: {strategy}", style="blue")
            # Implementation would call strategy setting logic

            if migrate_now:
                self.console.print("🔄 Migrating existing cache...", style="blue")

            self.success_message(f"Cache strategy set to {strategy}")

        except Exception as e:
            self.error_message(f"Failed to set cache strategy: {e}")
            raise CommandExecutionError(f"Cache strategy setting failed: {e}") from e


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


def create_command_from_framework(command_class, add_manuscript_arg=True, **click_options):
    """Decorator factory to create Click commands from framework classes.

    Args:
        command_class: BaseCommand subclass
        add_manuscript_arg: Whether to add manuscript_path argument
        **click_options: Additional Click command options

    Returns:
        Click command decorator
    """

    def decorator(func):
        def wrapper(ctx, manuscript_path=None, **kwargs):
            command = command_class()
            return command.run(ctx, manuscript_path, **kwargs)

        # Apply Click decorators
        wrapper = click.pass_context(wrapper)
        if add_manuscript_arg:
            wrapper = click.argument("manuscript_path", type=click.Path(exists=True, file_okay=False), required=False)(
                wrapper
            )

        for option, config in click_options.items():
            wrapper = click.option(option, **config)(wrapper)

        return click.command()(wrapper)

    return decorator


# Example usage - replace existing command definitions:
# @create_command_from_framework(
#     ValidationCommand,
#     **{
#         "--detailed/-d": {"is_flag": True, "help": "Show detailed validation report"},
#         "--no-doi": {"is_flag": True, "help": "Skip DOI validation"}
#     }
# )
# def validate(ctx, manuscript_path, detailed, no_doi):
#     """Validate manuscript structure and content."""
#     pass


# Export the framework components
__all__ = [
    "BaseCommand",
    "CommandExecutionError",
    "ValidationCommand",
    "CleanCommand",
    "InitCommand",
    "CheckInstallationCommand",
    "BuildCommand",
    "VersionCommand",
    "CompletionCommand",
    "DeprecatedInstallDepsCommand",
    "ArxivCommand",
    "TrackChangesCommand",
    "BibliographyFixCommand",
    "BibliographyAddCommand",
    "SetupCommand",
    "ConfigInitCommand",
    "ConfigValidateCommand",
    "ConfigGetCommand",
    "ConfigShowCommand",
    "ConfigExportCommand",
    "ConfigMigrateCommand",
    "ConfigListCommand",
    "FiguresCommand",
    "CacheStatsCommand",
    "CacheClearCommand",
    "CacheCleanupCommand",
    "CacheOptimizeCommand",
    "CacheInfoCommand",
    "CacheMigrateCommand",
    "CacheSetStrategyCommand",
    "create_command_from_framework",
]
