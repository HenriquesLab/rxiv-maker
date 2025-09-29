"""Get rxiv preprint command for rxiv-maker CLI."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional

import click
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..framework import BaseCommand, CommandExecutionError


class GetRxivPreprintCommand(BaseCommand):
    """Command to clone the example manuscript repository."""

    def __init__(self):
        """Initialize the get-rxiv-preprint command."""
        super().__init__()

    def execute_operation(self, **kwargs) -> None:
        """Execute the get-rxiv-preprint operation.

        This method is required by BaseCommand but we handle execution
        in the run method directly for this command.
        """
        # The actual implementation is in the run method
        # This is just to satisfy the abstract method requirement
        pass

    def check_git_availability(self) -> bool:
        """Check if git is available on the system.

        Returns:
            True if git is available, False otherwise
        """
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True, timeout=10)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def clone_repository(self, target_dir: Path, quiet: bool = False) -> bool:
        """Clone the manuscript-rxiv-maker repository.

        Args:
            target_dir: Directory to clone into
            quiet: Whether to suppress git output

        Returns:
            True if successful, False otherwise
        """
        repo_url = "https://github.com/HenriquesLab/manuscript-rxiv-maker.git"

        try:
            # Prepare git command
            cmd = ["git", "clone", repo_url, str(target_dir)]
            if quiet:
                cmd.append("--quiet")

            if not quiet:
                self.console.print(f"🔄 Cloning {repo_url}...", style="blue")

            # Execute git clone
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
            )

            if result.returncode == 0:
                if not quiet:
                    self.console.print(f"✅ Successfully cloned to {target_dir}", style="green")
                return True
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                self.console.print(f"❌ Git clone failed: {error_msg}", style="red")
                return False

        except subprocess.TimeoutExpired:
            self.console.print("⏰ Git clone timed out. Check your network connection.", style="yellow")
            return False
        except Exception as e:
            self.console.print(f"❌ Unexpected error during clone: {e}", style="red")
            return False

    def handle_existing_directory(self, target_dir: Path, force: bool) -> bool:
        """Handle existing directory scenarios.

        Args:
            target_dir: Target directory path
            force: Whether to force overwrite

        Returns:
            True if we should proceed, False otherwise
        """
        if not target_dir.exists():
            return True

        if force:
            self.console.print(f"🗑️  Removing existing directory: {target_dir}", style="yellow")
            shutil.rmtree(target_dir)
            return True
        else:
            self.console.print(f"❌ Directory {target_dir} already exists.", style="red")
            self.console.print("Use --force to overwrite, or choose a different directory.", style="dim")
            return False

    def show_success_message(self, target_dir: Path) -> None:
        """Show success message and next steps.

        Args:
            target_dir: Directory that was cloned to
        """
        manuscript_path = target_dir / "MANUSCRIPT"

        self.console.print("\n🎉 Example manuscript ready!", style="bold green")
        self.console.print(f"📁 Cloned to: {target_dir}", style="dim")

        if manuscript_path.exists():
            self.console.print("\n📋 Next steps:", style="bold blue")
            self.console.print(f"   1. cd {manuscript_path}", style="cyan")
            self.console.print("   2. rxiv pdf", style="cyan")
        else:
            self.console.print("\n📋 Next steps:", style="bold blue")
            self.console.print(f"   1. cd {target_dir}", style="cyan")
            self.console.print("   2. Explore the manuscript structure", style="cyan")

        self.console.print("\n💡 The example manuscript demonstrates:", style="bold")
        self.console.print("   • Figure generation with Python/R", style="dim")
        self.console.print("   • Bibliography management", style="dim")
        self.console.print("   • Professional LaTeX formatting", style="dim")
        self.console.print("   • Supplementary information", style="dim")

    def run(
        self, ctx: click.Context, directory: Optional[str] = None, force: bool = False, quiet: bool = False
    ) -> None:
        """Execute the get-rxiv-preprint command.

        Args:
            ctx: Click context
            directory: Target directory name
            force: Force overwrite existing directory
            quiet: Minimal output mode
        """
        try:
            # Determine target directory
            target_dir = Path(directory) if directory else Path("manuscript-rxiv-maker")

            # Check git availability
            if not self.check_git_availability():
                raise CommandExecutionError(
                    "❌ Git is not available on your system.\n"
                    "Please install git and try again.\n"
                    "Visit: https://git-scm.com/downloads"
                )

            # Handle existing directory
            if not self.handle_existing_directory(target_dir, force):
                raise CommandExecutionError("Operation cancelled.", exit_code=1)

            # Clone repository
            if not quiet:
                with Progress(
                    SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=self.console
                ) as progress:
                    progress.add_task("Cloning repository...", total=None)
                    success = self.clone_repository(target_dir, quiet=True)
            else:
                success = self.clone_repository(target_dir, quiet=True)

            if not success:
                raise CommandExecutionError("Failed to clone repository.", exit_code=1)

            # Show success message
            if not quiet:
                self.show_success_message(target_dir)

        except CommandExecutionError:
            raise
        except Exception as e:
            raise CommandExecutionError(f"Unexpected error: {e}") from e


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("directory", type=click.Path(), required=False)
@click.option("--force", "-f", is_flag=True, help="Force overwrite existing directory")
@click.option("--quiet", "-q", is_flag=True, help="Minimal output mode")
@click.pass_context
def get_rxiv_preprint(
    ctx: click.Context,
    directory: Optional[str],
    force: bool,
    quiet: bool,
) -> None:
    """Clone the official rxiv-maker example manuscript.

    **DIRECTORY**: Target directory for the cloned repository.
    Defaults to 'manuscript-rxiv-maker/'

    This command clones the official example manuscript from:
    https://github.com/HenriquesLab/manuscript-rxiv-maker

    The example demonstrates all rxiv-maker features including figure generation,
    bibliography management, and professional formatting.

    ## Examples

    **Clone to default directory:**

        $ rxiv get-rxiv-preprint

    **Clone to custom directory:**

        $ rxiv get-rxiv-preprint my-example/

    **Force overwrite existing directory:**

        $ rxiv get-rxiv-preprint --force

    **Quiet mode (minimal output):**

        $ rxiv get-rxiv-preprint --quiet

    ## After Cloning

    Navigate to the manuscript directory and generate the PDF:

        $ cd manuscript-rxiv-maker/MANUSCRIPT
        $ rxiv pdf

    This will create a publication-ready PDF demonstrating all rxiv-maker features.
    """
    # Use centralized command framework
    command = GetRxivPreprintCommand()
    command.run(ctx, directory=directory, force=force, quiet=quiet)
