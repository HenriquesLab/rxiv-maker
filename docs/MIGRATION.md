# Migration Guide: From Make to Modern CLI

This guide helps you transition from traditional Make commands to the modern Rxiv-Maker CLI interface.

## Why Migrate?

The modern CLI provides:
- ✅ **Better error messages** with actionable suggestions
- ✅ **Rich terminal output** with progress indicators and colors
- ✅ **Auto-completion** for bash, zsh, and fish shells
- ✅ **Consistent interface** across all platforms
- ✅ **Easier to remember** commands with logical structure

## Installation

### Quick Start
```bash
# Install from PyPI
pip install rxiv-maker

# Enable auto-completion (optional)
rxiv --install-completion bash  # or zsh, fish
```

### Development Installation
```bash
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker
pip install -e .
```

## Command Mapping

### Core Commands

| Legacy Make Command | Modern CLI Command | Notes |
|-------------------|-------------------|-------|
| `make setup` | `rxiv setup` | Installs dependencies |
| `make pdf` | `rxiv pdf` | Builds PDF from MANUSCRIPT/ |
| `make pdf MANUSCRIPT_PATH=MY_PAPER` | `rxiv pdf MY_PAPER/` | Custom manuscript path |
| `make validate` | `rxiv validate` | Validates manuscript |
| `make clean` | `rxiv clean` | Cleans output files |
| `make arxiv` | `rxiv arxiv` | Prepares arXiv submission |

### Advanced Options

| Legacy Make Command | Modern CLI Command | Notes |
|-------------------|-------------------|-------|
| `make pdf FORCE_FIGURES=true` | `rxiv pdf --force-figures` | Force figure regeneration |
| `make pdf-no-validate` | `rxiv pdf --skip-validation` | Skip validation step |
| `make pdf VERBOSE=true` | `rxiv pdf --verbose` | Verbose output |
| `make validate MANUSCRIPT_PATH=X` | `rxiv validate X/` | Validate specific path |

### Docker Mode

| Legacy Make Command | Modern CLI Command | Notes |
|-------------------|-------------------|-------|
| `make pdf RXIV_ENGINE=DOCKER` | `rxiv pdf --engine docker` | Use Docker engine |
| `make validate RXIV_ENGINE=DOCKER` | `rxiv validate --engine docker` | Validate in Docker |
| `export RXIV_ENGINE=DOCKER` | Set in config or use `--engine` | Per-command option |

### Bibliography Management

| Legacy Make Command | Modern CLI Command | Notes |
|-------------------|-------------------|-------|
| `make fix-bibliography` | `rxiv bibliography fix` | Fix bibliography issues |
| `make fix-bibliography-dry-run` | `rxiv bibliography fix --dry-run` | Preview fixes |
| `make add-bibliography 10.1000/doi` | `rxiv bibliography add 10.1000/doi` | Add from DOI |

### Figure Generation

| Legacy Make Command | Modern CLI Command | Notes |
|-------------------|-------------------|-------|
| Force figures via make | `rxiv figures --force` | Generate figures only |
| N/A | `rxiv figures --verbose` | Detailed figure output |

### Change Tracking

| Legacy Make Command | Modern CLI Command | Notes |
|-------------------|-------------------|-------|
| `make pdf-track-changes TAG=v1.0.0` | `rxiv track-changes MANUSCRIPT/ v1.0.0` | Track changes |
| With custom path and Docker | `rxiv track-changes MY_PAPER/ v1.0.0 --engine docker` | Combined options |

## Migration Examples

### Example 1: Basic Workflow
```bash
# Old workflow
make setup
make validate
make pdf

# New workflow
rxiv setup
rxiv validate
rxiv pdf
```

### Example 2: Custom Manuscript with Docker
```bash
# Old workflow
MANUSCRIPT_PATH=MY_PAPER RXIV_ENGINE=DOCKER make validate
MANUSCRIPT_PATH=MY_PAPER RXIV_ENGINE=DOCKER make pdf

# New workflow
rxiv validate MY_PAPER/ --engine docker
rxiv pdf MY_PAPER/ --engine docker
```

### Example 3: Force Figure Regeneration
```bash
# Old workflow
make pdf FORCE_FIGURES=true VERBOSE=true

# New workflow
rxiv pdf --force-figures --verbose
```

## Tips for Smooth Migration

1. **Both interfaces work together** - You can use CLI and Make commands interchangeably
2. **Start gradually** - Try one or two CLI commands first
3. **Use help frequently** - `rxiv --help` and `rxiv COMMAND --help` provide detailed information
4. **Enable auto-completion** - Makes discovering commands easier
5. **Check configuration** - `rxiv config show` displays current settings

## Common Patterns

### Setting Default Engine
```bash
# Old way (session only)
export RXIV_ENGINE=DOCKER

# New way (persistent)
rxiv config set general.engine docker
```

### Checking Installation
```bash
# New CLI provides detailed checks
rxiv check-installation
rxiv check-installation --detailed
rxiv check-installation --fix  # Auto-fix issues
```

### Version Information
```bash
# Simple version
rxiv --version

# Detailed version with system info
rxiv version --detailed

# Check for updates
rxiv version --check-updates
```

## Troubleshooting

### Command Not Found
If `rxiv` command is not found after installation:
```bash
# Ensure it's installed
pip show rxiv-maker

# Try using as module
python -m rxiv_maker.cli --help

# Reinstall
pip install --force-reinstall rxiv-maker
```

### Auto-completion Not Working
```bash
# Reinstall completion
rxiv --install-completion bash --force

# Restart shell
exec $SHELL
```

## Need Help?

- Run `rxiv --help` for general help
- Run `rxiv COMMAND --help` for command-specific help
- Check [CLI Reference](CLI_REFERENCE.md) for complete command documentation
- Visit [GitHub Discussions](https://github.com/henriqueslab/rxiv-maker/discussions) for community support

## Keeping Legacy Commands

The Make interface remains fully supported. You can:
- Continue using Make commands as before
- Mix CLI and Make commands as needed
- Gradually adopt CLI at your own pace

Both interfaces will be maintained for the foreseeable future.