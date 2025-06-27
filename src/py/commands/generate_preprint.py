# load tex template and generate article
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from auxiliary modules
# Import utility functions directly from utils.py
import importlib.util
import sys
from pathlib import Path

from processors.template_processor import (
    generate_supplementary_tex,
    get_template_path,
    process_template_replacements,
)
from processors.yaml_processor import extract_yaml_metadata

# Load utils.py module directly
utils_path = Path(__file__).parent.parent / "utils.py"
spec = importlib.util.spec_from_file_location("utils_module", utils_path)
if spec and spec.loader:
    utils_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(utils_module)

    # Extract the functions we need
    create_output_dir = utils_module.create_output_dir
    find_manuscript_md = utils_module.find_manuscript_md
    write_manuscript_output = utils_module.write_manuscript_output
    inject_rxiv_citation = utils_module.inject_rxiv_citation
else:
    raise ImportError("Could not load utils.py module")


def generate_preprint(output_dir, yaml_metadata):
    """Generate the preprint using the template."""
    template_path = get_template_path()
    with open(template_path) as template_file:
        template_content = template_file.read()

    # Find and process the manuscript markdown
    manuscript_md = find_manuscript_md()

    # Process all template replacements
    template_content = process_template_replacements(
        template_content, yaml_metadata, str(manuscript_md)
    )

    # Write the generated manuscript to the output directory
    manuscript_output = write_manuscript_output(output_dir, template_content)

    # Generate supplementary information
    generate_supplementary_tex(output_dir, yaml_metadata)

    return manuscript_output


def main():
    """Main entry point for the preprint generation command."""
    parser = argparse.ArgumentParser(
        description="Generate LaTeX article from markdown template"
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="output",
        help="Output directory (default: output)",
    )

    args = parser.parse_args()

    try:
        # Create output directory
        create_output_dir(args.output_dir)

        # Find and parse the manuscript markdown
        manuscript_md = find_manuscript_md()
        print(f"Found manuscript: {manuscript_md}")

        yaml_metadata = extract_yaml_metadata(str(manuscript_md))
        print(
            f"Extracted metadata: "
            f"{list(yaml_metadata.keys()) if yaml_metadata else 'None'}"
        )

        # Inject Rxiv-Maker citation if needed
        inject_rxiv_citation(yaml_metadata)

        # Generate the article
        generate_preprint(args.output_dir, yaml_metadata)

        print("Preprint generation completed successfully!")

    except Exception as e:
        import traceback

        print(f"Error: {e}")
        print("Traceback:")
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
