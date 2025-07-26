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
- `--force-figures`: Force regeneration of all figures
- `--skip-validation`: Skip validation step (useful for debugging)
- `--engine [local|docker]`: Use specified engine
- `--verbose, -v`: Show detailed output
- `--quiet, -q`: Suppress non-essential output
- `--debug, -d`: Enable debug output
- `--output-dir PATH, -o PATH`: Custom output directory

**Examples:**
```bash
rxiv pdf                          # Build from MANUSCRIPT/
rxiv pdf MY_PAPER/                # Build from custom directory
rxiv pdf --force-figures          # Force figure regeneration
rxiv pdf --engine docker          # Use Docker engine
rxiv pdf --skip-validation        # Skip validation for debugging
```

### `rxiv validate`

Validate manuscript structure and content.

```bash
rxiv validate [OPTIONS] [MANUSCRIPT_PATH]
```

**Arguments:**
- `MANUSCRIPT_PATH`: Path to manuscript directory (default: MANUSCRIPT/)

**Options:**
- `--no-doi`: Skip DOI validation
- `--detailed, -d`: Show detailed validation report

**Examples:**
```bash
rxiv validate                     # Validate MANUSCRIPT/
rxiv validate MY_PAPER/           # Validate custom directory
rxiv validate --no-doi            # Skip DOI checks
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
- `--template NAME`: Use specific template
- `--force`: Overwrite existing directory

**Examples:**
```bash
rxiv init                         # Create MANUSCRIPT/
rxiv init MY_PAPER/               # Create custom directory
rxiv init --template article      # Use article template
```

### `rxiv figures`

Generate or regenerate figures.

```bash
rxiv figures [OPTIONS] [MANUSCRIPT_PATH]
```

**Arguments:**
- `MANUSCRIPT_PATH`: Path to manuscript directory (default: MANUSCRIPT/)

**Options:**
- `--force`: Force regeneration of all figures
- `--verbose`: Show detailed output
- `--engine [local|docker]`: Use specified engine

**Examples:**
```bash
rxiv figures                      # Generate missing figures
rxiv figures --force              # Regenerate all figures
rxiv figures --verbose            # Show generation details
```

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

Add bibliography entry from DOI.

```bash
rxiv bibliography add [OPTIONS] DOI [MANUSCRIPT_PATH]
```

**Arguments:**
- `DOI`: DOI to add (e.g., 10.1000/journal.123)
- `MANUSCRIPT_PATH`: Path to manuscript directory (default: MANUSCRIPT/)

**Examples:**
```bash
rxiv bibliography add 10.1038/nature12373
rxiv bibliography add 10.1038/nature12373 MY_PAPER/
```

#### `rxiv bibliography validate`

Validate bibliography entries.

```bash
rxiv bibliography validate [OPTIONS] [MANUSCRIPT_PATH]
```

**Options:**
- `--no-doi`: Skip DOI validation

### `rxiv clean`

Clean generated files.

```bash
rxiv clean [OPTIONS] [MANUSCRIPT_PATH]
```

**Arguments:**
- `MANUSCRIPT_PATH`: Path to manuscript directory (default: MANUSCRIPT/)

**Options:**
- `--figures-only`: Clean only generated figures
- `--cache-only`: Clean only cache files
- `--all`: Clean everything including logs

**Examples:**
```bash
rxiv clean                        # Clean output directory
rxiv clean --figures-only         # Clean only figures
rxiv clean --cache-only           # Clean only cache
rxiv clean --all                  # Deep clean
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
rxiv --install-completion bash

# Zsh
rxiv --install-completion zsh

# Fish
rxiv --install-completion fish

# PowerShell
rxiv --install-completion powershell
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