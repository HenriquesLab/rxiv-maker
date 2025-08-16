# Rxiv-Maker CLI Reference

Complete reference for all Rxiv-Maker CLI commands and options.

## Global Options

These options work with all commands:

- `--help`: Show help message and exit
- `--version`: Show version and exit
- `--engine [local|docker]`: Execution engine (default: local)
- `--verbose`: Enable verbose output
- `--quiet`: Suppress non-essential output

## Commands

### `rxiv`

Main entry point for the Rxiv-Maker CLI.

```bash
rxiv [OPTIONS] COMMAND [ARGS]...
```

### `rxiv pdf`

Generate PDF from manuscript.

```bash
rxiv pdf [OPTIONS] [MANUSCRIPT_PATH]
```

**Arguments:**
- `MANUSCRIPT_PATH`: Path to manuscript directory (default: MANUSCRIPT/)

**Options:**
- `--force-figures, -f`: Force regeneration of all figures
- `--skip-validation, -s`: Skip validation step (useful for debugging)
- `--track-changes TAG, -t TAG`: Track changes against specified git tag
- `--output-dir PATH, -o PATH`: Custom output directory
- `--verbose, -v`: Show detailed output
- `--quiet, -q`: Suppress non-essential output
- `--debug, -d`: Enable debug output
- `--engine [local|docker]`: Use specified engine

**Note:** PDF generation includes validation step which respects DOI validation settings in `00_CONFIG.yml`

**Examples:**
```bash
rxiv pdf                          # Build from MANUSCRIPT/
rxiv pdf MY_PAPER/                # Build from custom directory
rxiv pdf --force-figures          # Force figure regeneration
rxiv pdf --track-changes v1.0.0   # Track changes against git tag
rxiv pdf --engine docker          # Use Docker engine
rxiv pdf --skip-validation        # Skip validation for debugging
```

**Figure Issues?** If you encounter figure positioning, layout, or spacing problems in your PDF, see the **[Figure Positioning Guide](tutorials/figure-positioning.md)** for comprehensive troubleshooting and positioning control.

### `rxiv validate`

Validate manuscript structure and content.

```bash
rxiv validate [OPTIONS] [MANUSCRIPT_PATH]
```

**Arguments:**
- `MANUSCRIPT_PATH`: Path to manuscript directory (default: MANUSCRIPT/)

**Options:**
- `--no-doi`: Skip DOI validation (overrides config setting)
- `--detailed, -d`: Show detailed validation report

**DOI Validation:**
DOI validation is enabled by default but can be controlled via:
1. Configuration file: Set `enable_doi_validation: false` in `00_CONFIG.yml`
2. CLI override: Use `--no-doi` flag to disable for a single run
3. Priority: CLI flag > config file > default (enabled)

**Examples:**
```bash
rxiv validate                     # Validate MANUSCRIPT/ (uses config setting)
rxiv validate MY_PAPER/           # Validate custom directory
rxiv validate --no-doi            # Skip DOI checks (overrides config)
rxiv validate --detailed          # Get comprehensive feedback
```

### `rxiv init`

Initialize a new manuscript.

```bash
rxiv init [OPTIONS] [MANUSCRIPT_PATH]
```

**Arguments:**
- `MANUSCRIPT_PATH`: Path for new manuscript (default: MANUSCRIPT/)

**Options:**
- `--template NAME, -t NAME`: Use specific template (basic, research, preprint)
- `--force, -f`: Overwrite existing directory
- `--no-interactive`: Skip interactive prompts and use defaults

**Examples:**
```bash
rxiv init                         # Create MANUSCRIPT/
rxiv init MY_PAPER/               # Create custom directory
rxiv init --template research     # Use research template
rxiv init --no-interactive        # Skip prompts, use defaults
rxiv init --force                 # Overwrite existing directory
```

### `rxiv figures`

Generate or regenerate figures.

```bash
rxiv figures [OPTIONS] [MANUSCRIPT_PATH]
```

**Arguments:**
- `MANUSCRIPT_PATH`: Path to manuscript directory (default: MANUSCRIPT/)

**Options:**
- `--force, -f`: Force regeneration of all figures
- `--figures-dir PATH, -d PATH`: Custom figures directory path
- `--verbose`: Show detailed output
- `--engine [local|docker]`: Use specified engine

**Examples:**
```bash
rxiv figures                      # Generate missing figures
rxiv figures --force              # Regenerate all figures
rxiv figures --verbose            # Show generation details
```

**Figure Positioning:**
For advanced figure positioning, sizing, and layout control, see the **[Figure Positioning Guide](tutorials/figure-positioning.md)**. This covers `tex_position` attributes, width control, panel references, and troubleshooting layout issues.

### `rxiv bibliography`

Manage bibliography entries.

```bash
rxiv bibliography [OPTIONS] COMMAND [ARGS]...
```

**Subcommands:**

#### `rxiv bibliography fix`

Fix bibliography issues using CrossRef.

```bash
rxiv bibliography fix [OPTIONS] [MANUSCRIPT_PATH]
```

**Options:**
- `--dry-run`: Preview changes without applying
- `--verbose`: Show detailed output

**Examples:**
```bash
rxiv bibliography fix             # Fix issues in MANUSCRIPT/
rxiv bibliography fix --dry-run   # Preview fixes
```

#### `rxiv bibliography add`

Add bibliography entries from DOIs or URLs.

```bash
rxiv bibliography add [OPTIONS] DOI1 [DOI2 ...]
```

**Arguments:**
- `DOIS`: One or more DOIs or URLs containing DOIs to add

**Options:**
- `--manuscript-path PATH, -m PATH`: Path to manuscript directory (default: MANUSCRIPT/)
- `--overwrite, -o`: Overwrite existing entries

**Examples:**
```bash
rxiv bibliography add 10.1038/nature12373
rxiv bibliography add 10.1038/nature12373 10.1000/example.doi
rxiv bibliography add https://www.nature.com/articles/d41586-022-00563-z
rxiv bibliography add --manuscript-path MY_PAPER/ 10.1038/nature12373
rxiv bibliography add --overwrite 10.1038/nature12373
```

**Note:** Bibliography validation is now integrated into the main `rxiv validate` command for comprehensive manuscript validation.

### `rxiv clean`

Clean generated files.

```bash
rxiv clean [OPTIONS] [MANUSCRIPT_PATH]
```

**Arguments:**
- `MANUSCRIPT_PATH`: Path to manuscript directory (default: MANUSCRIPT/)

**Options:**
- `--output-dir DIR, -o DIR`: Output directory to clean (default: output)
- `--figures-only, -f`: Clean only generated figures
- `--output-only, -O`: Clean only output directory
- `--arxiv-only, -a`: Clean only arXiv files
- `--temp-only, -t`: Clean only temporary files
- `--cache-only, -c`: Clean only cache files
- `--all, -A`: Clean all generated files

**Examples:**
```bash
rxiv clean                        # Clean all generated files
rxiv clean --figures-only         # Clean only figures
rxiv clean --cache-only           # Clean only cache
rxiv clean --temp-only            # Clean only temporary LaTeX files
rxiv clean --output-dir custom/   # Clean custom output directory
```

### `rxiv arxiv`

Prepare arXiv submission package.

```bash
rxiv arxiv [OPTIONS] [MANUSCRIPT_PATH]
```

**Arguments:**
- `MANUSCRIPT_PATH`: Path to manuscript directory (default: MANUSCRIPT/)

**Options:**
- `--output PATH`: Output directory for arXiv package
- `--validate`: Validate package before creating

**Examples:**
```bash
rxiv arxiv                        # Create arXiv package
rxiv arxiv --validate             # Validate before packaging
```

### `rxiv track-changes`

Generate PDF with tracked changes against a git tag.

```bash
rxiv track-changes [OPTIONS] MANUSCRIPT_PATH TAG
```

**Arguments:**
- `MANUSCRIPT_PATH`: Path to manuscript directory
- `TAG`: Git tag to compare against (e.g., v1.0.0)

**Options:**
- `--engine [local|docker]`: Use specified engine
- `--output PATH`: Custom output path

**Examples:**
```bash
rxiv track-changes MANUSCRIPT/ v1.0.0
rxiv track-changes MY_PAPER/ v2.0.0 --engine docker
```

### `rxiv setup`

Setup development environment.

```bash
rxiv setup [OPTIONS]
```

**Options:**
- `--reinstall`: Remove and recreate virtual environment
- `--upgrade`: Upgrade all dependencies
- `--minimal`: Install minimal dependencies only

**Examples:**
```bash
rxiv setup                        # Standard setup
rxiv setup --reinstall            # Clean reinstall
rxiv setup --upgrade              # Upgrade dependencies
```

### `rxiv config`

Manage configuration.

```bash
rxiv config [OPTIONS] COMMAND [ARGS]...
```

**Subcommands:**

#### `rxiv config show`

Show current configuration.

```bash
rxiv config show [OPTIONS]
```

**Options:**
- `--format [json|yaml]`: Output format

#### `rxiv config set`

Set configuration value.

```bash
rxiv config set KEY VALUE
```

**Examples:**
```bash
rxiv config set general.engine docker
rxiv config set general.check_updates false
```

#### `rxiv config reset`

Reset configuration to defaults.

```bash
rxiv config reset [OPTIONS]
```

**Options:**
- `--confirm`: Skip confirmation prompt

### `rxiv check-installation`

Check system dependencies and installation.

```bash
rxiv check-installation [OPTIONS]
```

**Options:**
- `--detailed`: Show detailed system information
- `--fix`: Attempt to fix missing dependencies

**Examples:**
```bash
rxiv check-installation           # Basic check
rxiv check-installation --detailed # Full system report
rxiv check-installation --fix     # Auto-fix issues
```

### `rxiv install-deps`

Install system dependencies for rxiv-maker.

```bash
rxiv install-deps [OPTIONS]
```

**Options:**
- `--mode [full|minimal|core]`: Installation mode
- `--verbose`: Show detailed output
- `--dry-run`: Show what would be installed without installing

**Examples:**
```bash
rxiv install-deps                 # Full installation
rxiv install-deps --mode minimal  # Essential dependencies only
rxiv install-deps --dry-run       # Preview installation
```

### `rxiv version`

Show version information.

```bash
rxiv version [OPTIONS]
```

**Options:**
- `--detailed`: Show detailed version and system info
- `--check-updates`: Check for available updates

**Examples:**
```bash
rxiv version                      # Show version
rxiv version --detailed           # Show system info
rxiv version --check-updates      # Check for updates
```

## Environment Variables

The CLI respects these environment variables:

- `RXIV_ENGINE`: Default engine (local or docker)
- `MANUSCRIPT_PATH`: Default manuscript path
- `FORCE_FIGURES`: Force figure regeneration
- `RXIV_CONFIG_PATH`: Custom config file location
- `RXIV_CACHE_DIR`: Custom cache directory
- `NO_COLOR`: Disable colored output

## Configuration File

Configuration is stored in `~/.config/rxiv-maker/config.yaml`:

```yaml
general:
  engine: local
  check_updates: true
  verbose: false

paths:
  cache_dir: ~/.cache/rxiv-maker
  
docker:
  image: henriqueslab/rxiv-maker:latest
  
features:
  auto_validate: true
  rich_output: true
```

## Manuscript Configuration

Each manuscript can have its own configuration file `00_CONFIG.yml` containing metadata and build settings:

```yaml
# DOI Validation Settings
enable_doi_validation: true  # Enable DOI validation against CrossRef/DataCite APIs
                            # Set to false to skip DOI validation (useful for offline work)
                            # Can be overridden with --no-doi CLI flag

# Other manuscript settings
title: "Your Paper Title"
authors:
  - name: "Author Name"
    email: "author@example.com"
bibliography: 03_REFERENCES.bib
date: "2025-01-01"
```

**DOI Validation Configuration:**
- **Default**: `enable_doi_validation: true` (enabled)
- **Purpose**: Controls whether DOI validation occurs during manuscript validation
- **Override**: CLI `--no-doi` flag takes precedence over config setting
- **Use cases**: 
  - Set to `false` for offline work or when DOI APIs are unavailable
  - Leave as `true` for complete manuscript validation

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Validation error
- `3`: Missing dependencies
- `4`: File not found
- `5`: Permission denied

## Shell Completion

Enable tab completion for your shell:

```bash
# Bash
rxiv completion bash

# Zsh
rxiv completion zsh

# Fish
rxiv completion fish
```

### `rxiv completion`

Install shell completion for the specified shell.

```bash
rxiv completion [OPTIONS] {bash|zsh|fish}
```

**Arguments:**
- `SHELL`: Shell type (bash, zsh, or fish)

**Examples:**
```bash
rxiv completion zsh               # Install for zsh
rxiv completion bash              # Install for bash
rxiv completion fish              # Install for fish
```

## Tips and Tricks

### Aliases

Create useful aliases in your shell:

```bash
alias rxp='rxiv pdf'
alias rxv='rxiv validate'
alias rxpd='rxiv pdf --engine docker'
```

### Default Engine

Set Docker as default engine:

```bash
rxiv config set general.engine docker
```

### Batch Processing

Process multiple manuscripts:

```bash
for dir in */; do
  if [ -f "$dir/00_CONFIG.yml" ]; then
    rxiv pdf "$dir"
  fi
done
```

### CI/CD Integration

Use in GitHub Actions:

```yaml
- name: Build PDF
  run: |
    pip install rxiv-maker
    rxiv pdf --skip-validation
```

## Getting Help

- `rxiv --help`: General help
- `rxiv COMMAND --help`: Command-specific help
- [GitHub Issues](https://github.com/henriqueslab/rxiv-maker/issues): Report bugs
- [GitHub Discussions](https://github.com/henriqueslab/rxiv-maker/discussions): Ask questions