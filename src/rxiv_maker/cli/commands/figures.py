"""Figures command for rxiv-maker CLI."""

import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


@click.command()
@click.argument("manuscript_path", type=click.Path(exists=True, file_okay=False), required=False)
@click.option("--force", "-f", is_flag=True, help="Force regeneration of all figures")
@click.option("--figures-dir", "-d", help="Custom figures directory path")
@click.pass_context
def figures(
    ctx: click.Context,
    manuscript_path: str | None,
    force: bool,
    figures_dir: str | None,
) -> None:
    """Generate figures from scripts.

    MANUSCRIPT_PATH: Path to manuscript directory (default: MANUSCRIPT)

    This command generates figures from:
    - Python scripts (*.py)
    - R scripts (*.R)
    - Mermaid diagrams (*.mmd)
    """
    verbose = ctx.obj.get("verbose", False)
    engine = ctx.obj.get("engine", "local")

    # Default to MANUSCRIPT if not specified
    if manuscript_path is None:
        manuscript_path = os.environ.get("MANUSCRIPT_PATH", "MANUSCRIPT")

    # Docker engine optimization: check Docker readiness
    if engine == "docker":
        from ...docker.manager import get_docker_manager

        try:
            if verbose:
                console.print("🔧 Getting Docker manager in figures command...", style="blue")
            # Use current working directory as workspace for consistency
            workspace_dir = Path.cwd().resolve()
            docker_manager = get_docker_manager(workspace_dir=workspace_dir)
            if verbose:
                console.print(
                    "🔧 Checking Docker availability in figures command...",
                    style="blue",
                )
            if not docker_manager.check_docker_available():
                console.print(
                    "❌ Docker is not available. Please ensure Docker is running.",
                    style="red",
                )
                sys.exit(1)
            if verbose:
                console.print("🔧 Docker is ready in figures command!", style="green")
        except Exception as e:
            console.print(f"❌ Docker setup error: {e}", style="red")
            sys.exit(1)

    # Validate manuscript path exists
    if not Path(manuscript_path).exists():
        console.print(
            f"❌ Error: Manuscript directory '{manuscript_path}' does not exist",
            style="red",
        )
        console.print(
            f"💡 Run 'rxiv init {manuscript_path}' to create a new manuscript",
            style="yellow",
        )
        sys.exit(1)

    # Set figures directory
    if figures_dir is None:
        figures_dir = str(Path(manuscript_path) / "FIGURES")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Generating figures...", total=None)

            # Import figure generation class directly
            if verbose:
                console.print("📦 Importing FigureGenerator class...", style="blue")
            from ...engine.generate_figures import FigureGenerator

            if verbose:
                console.print("📦 Successfully imported FigureGenerator!", style="green")

            try:
                if verbose:
                    console.print("🎨 Creating FigureGenerator...", style="blue")

                # Create FigureGenerator directly instead of using main() function
                generator = FigureGenerator(
                    figures_dir=figures_dir,
                    output_dir=figures_dir,
                    output_format="png",  # default format
                    r_only=False,
                    engine=engine,
                )

                if verbose:
                    console.print("🎨 Starting figure generation...", style="blue")

                if verbose:
                    console.print(
                        "🔧 About to call generator.generate_all_figures()...",
                        style="blue",
                    )
                generator.generate_all_figures()
                if verbose:
                    console.print("🔧 generate_all_figures() completed!", style="green")

                progress.update(task, description="✅ Figure generation completed")
                console.print("✅ Figures generated successfully!", style="green")
                console.print(f"📁 Figures directory: {figures_dir}", style="blue")

            except Exception as e:
                progress.update(task, description="❌ Figure generation failed")
                console.print(f"❌ Figure generation failed: {e}", style="red")
                console.print("💡 Check your figure scripts for errors", style="yellow")
                sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n⏹️  Figure generation interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error during figure generation: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)
