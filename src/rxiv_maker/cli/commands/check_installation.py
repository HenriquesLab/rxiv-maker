"""CLI command for checking installation status."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...install.utils.verification import diagnose_installation, verify_installation


@click.command()
@click.option("--detailed", "-d", is_flag=True, help="Show detailed diagnostic information")
@click.option("--fix", is_flag=True, help="Attempt to fix missing dependencies")
@click.option("--json", is_flag=True, help="Output results in JSON format")
def check_installation(detailed: bool, fix: bool, json: bool):
    """Check rxiv-maker installation and system dependencies.

    This command verifies that all required components are installed
    and working correctly, including Python packages, LaTeX, Node.js,
    and other system dependencies.
    """
    console = Console()

    if json:
        _output_json_results(console)
        return

    console.print(Panel.fit("🔍 Checking rxiv-maker Installation", style="blue"))

    # Run verification
    results = verify_installation(verbose=False)

    if detailed:
        _show_detailed_results(console, results)
    else:
        _show_basic_results(console, results)

    # Check if fixes are needed
    missing_critical = []
    for component, installed in results.items():
        if not installed and component != "r":  # R is optional
            missing_critical.append(component)

    if missing_critical:
        console.print(f"\n⚠️  {len(missing_critical)} critical components missing", style="yellow")

        if fix:
            console.print("\n🔧 Attempting to fix missing dependencies...")
            _fix_missing_dependencies(console, missing_critical)
        else:
            console.print("\n💡 Run with --fix to attempt repairs")
            console.print("   Or run: rxiv check-installation --fix")
    else:
        console.print("\n✅ All critical components are working!", style="green")

    # Show next steps
    _show_next_steps(console, results)


def _output_json_results(console: Console):
    """Output results in JSON format."""
    import json

    results = verify_installation(verbose=False)
    diagnosis = diagnose_installation()

    output = {
        "status": "complete" if all(results.values()) else "incomplete",
        "components": results,
        "diagnosis": diagnosis,
        "summary": {
            "total": len(results),
            "installed": sum(results.values()),
            "missing": len(results) - sum(results.values()),
        },
    }

    console.print(json.dumps(output, indent=2))


def _show_basic_results(console: Console, results: dict):
    """Show basic verification results."""
    table = Table(title="Installation Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Description")

    component_descriptions = {
        "python": "Python 3.11+ runtime",
        "latex": "LaTeX distribution (pdflatex, bibtex)",
        "nodejs": "Node.js and npm",
        "r": "R language (optional)",
        "system_libs": "System libraries for Python packages",
        "rxiv_maker": "rxiv-maker Python package",
    }

    for component, installed in results.items():
        status = "✅ Installed" if installed else "❌ Missing"
        style = "green" if installed else "red"
        description = component_descriptions.get(component, "")

        table.add_row(
            component.replace("_", " ").title(),
            status,
            description,
            style=style if not installed else None,
        )

    console.print(table)


def _show_detailed_results(console: Console, results: dict):
    """Show detailed diagnostic information."""
    diagnosis = diagnose_installation()

    for component, installed in results.items():
        status = "✅ Installed" if installed else "❌ Missing"
        style = "green" if installed else "red"

        console.print(f"\n{component.replace('_', ' ').title()}: {status}", style=style)

        if component in diagnosis:
            info = diagnosis[component]

            if info.get("version"):
                console.print(f"  Version: {info['version']}")

            if info.get("path"):
                console.print(f"  Path: {info['path']}")

            if info.get("issues"):
                for issue in info["issues"]:
                    console.print(f"  ⚠️  {issue}", style="yellow")


def _fix_missing_dependencies(console: Console, missing: list):
    """Attempt to fix missing dependencies."""
    try:
        from ...install.manager import InstallManager, InstallMode

        console.print("🔧 Starting repair process...")

        manager = InstallManager(mode=InstallMode.FULL, verbose=True, force=True, interactive=False)

        success = manager.repair()

        if success:
            console.print("✅ Repair completed successfully!", style="green")

            # Re-verify installation
            console.print("\n🔍 Re-checking installation...")
            new_results = verify_installation(verbose=False)
            _show_basic_results(console, new_results)
        else:
            console.print("❌ Repair failed. Check logs for details.", style="red")
            console.print("   Log file: ~/.rxiv-maker/logs/")

    except Exception as e:
        console.print(f"❌ Error during repair: {e}", style="red")


def _show_next_steps(console: Console, results: dict):
    """Show next steps based on installation status."""
    console.print("\n" + "=" * 60)
    console.print("Next Steps:", style="bold blue")

    if all(results.values()):
        console.print("✅ Your installation is complete!")
        console.print("   Try: rxiv init my-paper")
        console.print("   Then: rxiv pdf my-paper")
    else:
        console.print("🔧 To fix missing dependencies:")
        console.print("   Run: rxiv check-installation --fix")
        console.print("   Or:  python -m rxiv_maker.install.manager")

    console.print("\n📚 Documentation:")
    console.print("   https://github.com/henriqueslab/rxiv-maker#readme")

    console.print("\n🆘 Support:")
    console.print("   https://github.com/henriqueslab/rxiv-maker/issues")
    console.print("=" * 60)
