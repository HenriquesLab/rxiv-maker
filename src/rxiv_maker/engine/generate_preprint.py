"""Generate LaTeX preprint from markdown template."""

import os
import sys

import yaml

# Add the parent directory to the path to allow imports when run as a script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rxiv_maker.processors.template_processor import (
    generate_supplementary_tex,
    get_template_path,
    process_template_replacements,
)
from rxiv_maker.utils import (
    create_output_dir,
    find_manuscript_md,
    write_manuscript_output,
)


def generate_preprint(output_dir, yaml_metadata, manuscript_path=None):
    """Generate the preprint using the template."""
    # Ensure output directory exists
    create_output_dir(output_dir)

    template_path = get_template_path()
    with open(template_path, encoding="utf-8") as template_file:
        template_content = template_file.read()

    # Find and process the manuscript markdown
    manuscript_md = find_manuscript_md(manuscript_path)

    # Process all template replacements
    template_content = process_template_replacements(template_content, yaml_metadata, str(manuscript_md))

    # Extract manuscript name using centralized logic (PathManager handles this via write_manuscript_output)
    # The write_manuscript_output function now uses PathManager internally for consistent name extraction
    manuscript_output = write_manuscript_output(output_dir, template_content, manuscript_name=None)

    # Generate supplementary information
    generate_supplementary_tex(output_dir, yaml_metadata)

    return manuscript_output


# CLI integration
def main():
    """Main function for CLI integration."""
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Generate LaTeX preprint from markdown")
    parser.add_argument("--output-dir", help="Output directory for generated files")
    parser.add_argument("--config", help="YAML config file path")

    args = parser.parse_args()

    # Use current directory if no output dir specified
    output_dir = args.output_dir or "."

    # Load YAML metadata
    config_path = args.config or "00_CONFIG.yml"
    if Path(config_path).exists():
        with open(config_path, encoding="utf-8") as f:
            yaml_metadata = yaml.safe_load(f)
    else:
        yaml_metadata = {}

    try:
        result = generate_preprint(output_dir, yaml_metadata)
        print(f"Generated preprint: {result}")
        return 0  # Success
    except Exception as e:
        print(f"Error generating preprint: {e}")
        return 1  # Error


if __name__ == "__main__":
    main()
