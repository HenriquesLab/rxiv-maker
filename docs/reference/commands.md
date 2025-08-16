# Command Reference

Essential commands for Rxiv-Maker. All commands work with both local and Docker environments.

## Quick Reference

### Modern CLI Commands (Recommended)
| Task | CLI Command | Docker Mode |
|------|-------------|-------------|
| **Generate PDF** | `rxiv pdf` | `rxiv pdf --engine docker` |
| **Validate manuscript** | `rxiv validate` | `rxiv validate --engine docker` |
| **Setup environment** | `rxiv setup` | Not needed (dependencies in container) |
| **Force figure regeneration** | `rxiv pdf --force-figures` | `rxiv pdf --force-figures --engine docker` |
| **Track changes vs git tag** | `rxiv track-changes v1.0.0` | `rxiv track-changes v1.0.0 --engine docker` |
| **Clean outputs** | `rxiv clean` | `rxiv clean --engine docker` |

### Legacy Make Commands (Still Supported)
| Task | Local Command | Docker Command |
|------|---------------|----------------|
| **Generate PDF** | `make pdf` | `make pdf RXIV_ENGINE=DOCKER` |
| **Validate manuscript** | `make validate` | `make validate RXIV_ENGINE=DOCKER` |
| **Setup environment** | `make setup` | Not needed (dependencies in container) |
| **Force figure regeneration** | `make pdf FORCE_FIGURES=true` | `make pdf FORCE_FIGURES=true RXIV_ENGINE=DOCKER` |
| **Track changes vs git tag** | `make pdf-track-changes TAG=v1.0.0` | `make pdf-track-changes TAG=v1.0.0 RXIV_ENGINE=DOCKER` |
| **Clean outputs** | `make clean` | `make clean RXIV_ENGINE=DOCKER` |

## Environment Setup

### Modern CLI Setup (Recommended)
```bash
# Install from PyPI
pip install rxiv-maker

# Initialize new manuscript
rxiv init MY_PAPER/

# Build PDF
rxiv pdf MY_PAPER/
```

### Local Development
```bash
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker
pip install -e .  # Install in development mode
rxiv pdf          # Use CLI
# OR
make setup && make pdf  # Use legacy Make
```

### Docker Development  
```bash
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker
rxiv pdf --engine docker  # Use CLI with Docker
# OR
make pdf RXIV_ENGINE=DOCKER  # Use legacy Make
```

## PDF Generation

### Modern CLI Commands
```bash
# Generate PDF from default manuscript
rxiv pdf

# Generate PDF from specific manuscript directory
rxiv pdf MY_PAPER/

# Force regeneration of all figures
rxiv pdf --force-figures

# Generate PDF without validation (for debugging)
rxiv pdf --skip-validation

# Use Docker engine
rxiv pdf --engine docker
```

### Legacy Make Commands
```bash
# Generate PDF from default manuscript
make pdf

# Generate PDF from specific manuscript directory
make pdf MANUSCRIPT_PATH=MY_PAPER

# Force regeneration of all figures
make pdf FORCE_FIGURES=true

# Generate PDF without validation (for debugging)
make pdf-no-validate
```

### Figure Positioning & Layout
For advanced control over figure positioning, sizing, and layout in your PDFs, see the **[Figure Positioning Guide](../tutorials/figure-positioning.md)**. This comprehensive guide covers:
- Positioning attributes (`tex_position="t"`, `tex_position="h"`, etc.)
- Width control (`width="\textwidth"`, `width="0.8\linewidth"`)
- Panel references without unwanted spaces
- Troubleshooting layout issues

## Change Tracking

Generate PDFs highlighting differences against git tags:

### Modern CLI Commands
```bash
# Track changes against a git tag
rxiv track-changes MANUSCRIPT/ v1.0.0

# Track changes with Docker
rxiv track-changes MANUSCRIPT/ v1.0.0 --engine docker
```

### Legacy Make Commands
```bash
# Track changes against a git tag
make pdf-track-changes TAG=v1.0.0

# Track changes for specific manuscript
make pdf-track-changes TAG=v1.2.0 MANUSCRIPT_PATH=MY_PAPER

# Track changes using Docker mode
make pdf-track-changes TAG=v1.0.0 RXIV_ENGINE=DOCKER
```

## Validation and Testing

### Modern CLI Commands
```bash
# Validate manuscript before building
rxiv validate

# Skip DOI validation
rxiv validate --no-doi

# Detailed validation with error analysis
rxiv validate --detailed

# Validate specific manuscript
rxiv validate MY_PAPER/
```

### Legacy Make Commands
```bash
# Validate manuscript before building
make validate

# Validate with Docker
make validate RXIV_ENGINE=DOCKER
```

### Testing Commands
```bash
# Run tests
pytest tests/
nox -s tests                       # Multiple Python versions

# Or use hatch for testing
hatch run test
hatch run lint
hatch run type-check
```

## Bibliography Management

### Modern CLI Commands
```bash
# Fix bibliography issues automatically
rxiv bibliography fix

# Preview fixes without applying
rxiv bibliography fix --dry-run

# Add bibliography entry from DOI
rxiv bibliography add 10.1000/doi

# Validate bibliography entries
rxiv bibliography validate
```

### Legacy Make Commands
```bash
# Fix bibliography issues automatically
make fix-bibliography

# Preview fixes without applying
make fix-bibliography-dry-run

# Add bibliography entry from DOI
make add-bibliography 10.1000/doi
```

## Maintenance

### Modern CLI Commands
```bash
# Clean output directory and figures
rxiv clean

# Clean specific components
rxiv clean --figures-only          # Generated figures only
rxiv clean --cache-only            # Cache files only

# Prepare arXiv submission
rxiv arxiv
```

### Legacy Make Commands
```bash
# Clean output directory and figures
make clean

# Clean specific components
make clean-output                  # Output directory only
make clean-figures                 # Generated figures only
make clean-cache                   # Cache files only

# Prepare arXiv submission
make arxiv
```

## Environment Variables

```bash
# Key variables (can be set in .env file)
MANUSCRIPT_PATH=MY_PAPER          # Manuscript directory
FORCE_FIGURES=true                # Force figure regeneration
RXIV_ENGINE=DOCKER                # Use Docker mode
```

## Troubleshooting

```bash
# Detailed validation with error analysis
rxiv validate --detailed

# Test figure generation in isolation
rxiv figures --verbose

# Manual LaTeX compilation
cd output && pdflatex manuscript.tex
```

For complete documentation, see:
- [User Guide](../getting-started/user_guide.md) for detailed usage
- [Docker Guide](../workflows/docker-engine-mode.md) for containerized builds
- [GitHub Actions Guide](../workflows/github-actions.md) for automated builds