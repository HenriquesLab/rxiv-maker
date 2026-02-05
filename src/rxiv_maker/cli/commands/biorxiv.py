"""bioRxiv submission package generation command."""

import rich_click as click

from ..framework.workflow_commands import BioRxivCommand


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("manuscript_path", type=click.Path(exists=True, file_okay=False), required=False)
@click.option("--output-dir", "-o", default="output", help="Output directory for generated files")
@click.option(
    "--biorxiv-dir",
    "-b",
    help="Custom bioRxiv submission directory (default: output/biorxiv_submission)",
)
@click.option(
    "--zip-filename",
    "-z",
    help="Custom ZIP filename (default: {manuscript}_biorxiv.zip)",
)
@click.option(
    "--no-zip",
    is_flag=True,
    help="Don't create ZIP file (only create submission directory)",
)
@click.pass_context
def biorxiv(ctx, manuscript_path, output_dir, biorxiv_dir, zip_filename, no_zip):
    r"""Generate bioRxiv submission package.

    Creates a complete submission package including:
    - bioRxiv author template (TSV file)
    - Manuscript PDF
    - Source files (TeX, figures, bibliography)
    - ZIP file for upload

    \b
    Example:
        rxiv biorxiv                           # Full package with ZIP
        rxiv biorxiv --no-zip                  # Package without ZIP
        rxiv biorxiv -b custom_dir             # Custom submission directory
        rxiv biorxiv -z my_submission.zip      # Custom ZIP filename
    """
    command = BioRxivCommand()
    return command.run(
        ctx,
        manuscript_path=manuscript_path,
        output_dir=output_dir,
        biorxiv_dir=biorxiv_dir,
        zip_filename=zip_filename,
        no_zip=no_zip,
    )
