# FIGURES Directory

This directory contains figure generation scripts and data for your manuscript.

## Structure

- `*.py` - Python scripts that generate figures programmatically
- `*.mmd` - Mermaid diagram files
- `DATA/` - Directory for data files used by figure generation scripts
- Generated figure directories (created automatically when scripts run)

## Usage

Place your figure generation scripts here. The system will automatically:
1. Execute Python scripts during build
2. Process Mermaid diagrams  
3. Generate PNG and PDF outputs
4. Include figures in your manuscript

## Examples

- `example_figure.py` - Sample Python figure script
- `supplementary_figure.py` - Sample supplementary figure script
- `DATA/example_data.csv` - Sample data file