[![DOI](https://img.shields.io/badge/DOI-10.48550%2FarXiv.2508.00836-blue)](https://doi.org/10.48550/arXiv.2508.00836)
[![License](https://img.shields.io/github/license/henriqueslab/rxiv-maker?color=Green)](https://github.com/henriqueslab/rxiv-maker/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/henriqueslab/rxiv-maker?style=social)](https://github.com/HenriquesLab/rxiv-maker/stargazers)

# Rxiv-Maker

<img src="src/logo/logo-rxiv-maker.svg" align="right" width="200" style="margin-left: 20px;"/>

Rxiv-Maker is an automated LaTeX article generation system that transforms scientific writing from chaos to clarity. It converts Markdown manuscripts into publication-ready PDFs with reproducible figures, professional typesetting, and zero LaTeX hassle.

The platform bridges the gap between **easy writing** (Markdown) and **beautiful output** (LaTeX), featuring automated figure generation from Python/R scripts and Mermaid diagrams, seamless citation management, Docker containerization for minimal-dependency execution (only Docker and Make required), and integration with GitHub Actions for accelerated cloud-based PDF generation.

Rxiv-Maker enhances the capabilities of traditional scientific writing by ensuring version control compatibility, facilitating reproducible science workflows, and providing professional formatting that meets publication standards.

## Key Features

- **20+ Enhanced Markdown Features** - Scientific cross-references, citations, subscript/superscript (**rxiv-markdown**)
- **Automated Figure Generation** - Python/R scripts and Mermaid diagrams with smart caching
- **Intelligent Validation** - Pre-build error detection with actionable feedback
- **Professional Output** - LaTeX-quality PDFs with various citation styles
- **Multi-Environment** - Local, Docker, Google Colab, and GitHub Actions support
- **Change Tracking** - Visual diff PDFs against git tags
- **VS Code Integration** - Dedicated extension with syntax highlighting
- **Modern CLI** - Beautiful command-line interface with rich output and auto-completion

**Key rxiv-markdown features:** Scientific cross-references (`@fig:label`, `@eq:label`), citations (`@citation`), text formatting (`~subscript~`, `^superscript^`), document control (`<newpage>`), and automated figure generation.

## Key Benefits

- **Accessibility** - Write in Markdown without LaTeX expertise
- **Reproducibility** - Automated figures and version control ensure consistent results
- **Flexibility** - Generate PDFs locally, in Docker, or via GitHub Actions
- **Professional Output** - LaTeX-quality formatting with automated bibliography management
- **Collaboration** - Git-based workflows with automated PDF generation

## System Requirements

<details>
<summary><strong>📋 Dependencies & Requirements</strong></summary>

### Core Requirements
- **Python**: 3.11+ (automatically handled in Docker/Colab modes)
- **Git**: For repository management
- **Make**: Build automation (see [platform-specific installation](docs/getting-started/installation.md))

### Python Dependencies
Automatically installed with `pip install rxiv-maker` or `make setup`:
```
matplotlib>=3.7.0    # Figure generation
seaborn>=0.12.0      # Statistical plotting  
numpy>=1.24.0        # Numerical computing
pandas>=2.0.0        # Data manipulation
PyYAML>=6.0.0        # Configuration parsing
pypdf>=3.0.0         # PDF processing
crossref-commons     # Citation validation
click>=8.0.0         # Modern CLI framework
rich>=13.0.0         # Beautiful terminal output
```

### Optional Dependencies (Local Development Only Without Docker)
- **LaTeX**: For PDF generation (TeX Live, MacTeX, or MikTeX)
- **R**: For R-based figure scripts

### Platform-Specific Setup
- **Docker Mode**: Only Docker Desktop + Make required
- **Google Colab**: Zero local installation needed
- **GitHub Actions**: Zero local installation needed
- **Local Development**: Full dependency stack required

### Quick Troubleshooting
- **Permission errors**: Ensure user has write access to project directory
- **LaTeX not found**: Use Docker mode or install platform-specific LaTeX
- **Python version issues**: Use Docker mode or upgrade to Python 3.11+
- **Make command not found**: Install build tools for your platform

**📖 Full Installation Guide**: [Complete platform-specific instructions](docs/getting-started/installation.md)

</details>

## Quickstart

### 🚀 Modern CLI (Recommended)

**📦 Universal Install (Recommended)**
```bash
# One command installs everything
pip install rxiv-maker

# Verify installation
rxiv check-installation

# Initialize new manuscript
rxiv init MY_PAPER/

# Build PDF
rxiv pdf MY_PAPER/

# Enable auto-completion (optional)
rxiv --install-completion bash  # or zsh, fish
```

**🎛️ Installation Options**
```bash
# Full installation (default)
pip install rxiv-maker

# Minimal installation (Python + LaTeX only)
RXIV_INSTALL_MODE=minimal pip install rxiv-maker

# Skip system dependencies
RXIV_SKIP_SYSTEM_DEPS=1 pip install rxiv-maker
```

### 📋 Alternative Setup Options

**🌐 Google Colab** (Easiest - no installation)
- **Prerequisites**: Google account only
- **Setup Time**: 2 minutes
- [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HenriquesLab/rxiv-maker/blob/main/notebooks/rxiv_maker_colab.ipynb)

**🐳 Docker** (Minimal dependencies)
- **Prerequisites**: [Docker Desktop](https://www.docker.com/products/docker-desktop) + Make
- **Setup Time**: 3-5 minutes
```bash
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker
make pdf RXIV_ENGINE=DOCKER
```

**🏠 Local Development** (Full control)
- **Prerequisites**: Python 3.11+, LaTeX, Make ([platform guide](docs/getting-started/installation.md))
- **Setup Time**: 10-30 minutes
```bash
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker
pip install -e .                    # Install with modern CLI
rxiv pdf                            # Generate PDF using CLI
```

**🛠️ Legacy Make Interface** (Still supported)
```bash
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker
make setup && make pdf
```

## Modern CLI Usage

Rxiv-Maker includes a modern command-line interface with rich output and intuitive commands:

### Quick Start
```bash
# Install from PyPI
pip install rxiv-maker

# Initialize new manuscript
rxiv init MY_PAPER/

# Build PDF
rxiv pdf MY_PAPER/

# Validate manuscript
rxiv validate MY_PAPER/
```

### Key CLI Commands
```bash
# Essential commands
rxiv pdf                            # Generate PDF from MANUSCRIPT/
rxiv pdf --force-figures            # Force regeneration of figures
rxiv validate                       # Validate manuscript
rxiv clean                          # Clean generated files

# Manuscript management
rxiv init MY_PROJECT/               # Initialize new manuscript
rxiv figures                        # Generate figures only
rxiv arxiv                          # Prepare arXiv submission

# Bibliography management
rxiv bibliography add 10.1000/doi   # Add DOI to bibliography
rxiv bibliography fix               # Fix bibliography issues
rxiv bibliography validate          # Validate bibliography

# Utility commands
rxiv version                        # Show version
rxiv version --detailed             # Show detailed system info
rxiv --help                         # Show help
```

### 🔧 CLI Features
- **Rich Output**: Beautiful colors, progress bars, and formatted tables
- **Smart Validation**: Pre-build error detection with helpful suggestions
- **Auto-completion**: Support for bash/zsh/fish shells
- **Flexible Arguments**: Intuitive command structure
- **Error Handling**: Clear error messages with resolution tips
- **Configuration**: Persistent settings with `~/.rxiv/config.toml`
- **Backward Compatibility**: All Make commands still work

### 📚 Complete CLI Reference

#### 📖 Manuscript Management
```bash
rxiv init MY_PAPER/                 # Initialize new manuscript
rxiv pdf MY_PAPER/                  # Generate PDF
rxiv validate MY_PAPER/             # Validate manuscript
rxiv clean MY_PAPER/                # Clean generated files
```

#### 🎨 Figure Generation
```bash
rxiv figures MY_PAPER/              # Generate all figures
rxiv figures --force                # Force regeneration
rxiv pdf --force-figures            # Build with fresh figures
```

#### 📚 Bibliography Management
```bash
rxiv bibliography add 10.1000/doi   # Add DOI to bibliography
rxiv bibliography fix               # Fix bibliography issues
rxiv bibliography validate          # Validate bibliography
```

#### 📦 Publishing
```bash
rxiv arxiv MY_PAPER/                # Prepare arXiv submission
rxiv track-changes MY_PAPER/ v1.0.0 # Track changes vs git tag
```

#### ⚙️ Configuration
```bash
rxiv config show                    # Show current configuration
rxiv config set key value           # Set configuration value
rxiv config get key                 # Get configuration value
rxiv config reset                   # Reset to defaults
```

#### 🔧 System
```bash
rxiv setup                          # Setup development environment
rxiv version                        # Show version
rxiv version --detailed             # Show detailed system info
rxiv --help                         # Show help
```

#### 🐳 Docker Support
```bash
rxiv pdf --engine docker            # Use Docker engine
rxiv config set general.default_engine docker  # Set Docker as default
```

## Installation

### 🚀 Universal Install (Recommended)
```bash
# One command installs everything automatically
pip install rxiv-maker

# Verify installation
rxiv check-installation
```

**What gets installed:**
- Python packages (matplotlib, numpy, etc.)
- LaTeX distribution (for PDF generation)
- R language (optional, for statistical figures)
- System libraries (automatically detected)

### 🎛️ Installation Options
```bash
# Full installation (default)
pip install rxiv-maker

# Minimal installation (Python + essential LaTeX only)
RXIV_INSTALL_MODE=minimal pip install rxiv-maker

# Core installation (Python + LaTeX, skip Node.js/R)
RXIV_INSTALL_MODE=core pip install rxiv-maker

# Python packages only (skip all system dependencies)
RXIV_SKIP_SYSTEM_DEPS=1 pip install rxiv-maker

# Conda/Mamba environments (recommended for data science users)
conda create -n rxiv-maker python=3.11
conda activate rxiv-maker
conda install -c conda-forge numpy matplotlib nodejs r-base
pip install rxiv-maker
```

### 🍺 Homebrew (macOS) - Deprecated
```bash
# Still supported but deprecated in favor of universal installer
brew tap henriqueslab/rxiv-maker
brew install rxiv-maker
```

### 📋 Development Install
```bash
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker
pip install -e .                       # Modern hatch-based build system
```

### 🔧 Auto-completion Setup
```bash
# For bash users
rxiv --install-completion bash

# For zsh users  
rxiv --install-completion zsh

# For fish users
rxiv --install-completion fish
```

### 🔄 Migration from Make Commands

Existing users can continue using Make commands or migrate to the CLI:

| Make Command | CLI Command | Notes |
|-------------|-------------|-------|
| `make setup` | `rxiv setup` | Setup environment |
| `make pdf` | `rxiv pdf` | Build PDF |
| `make validate` | `rxiv validate` | Validate manuscript |
| `make clean` | `rxiv clean` | Clean files |
| `make arxiv` | `rxiv arxiv` | Prepare arXiv |
| `make pdf FORCE_FIGURES=true` | `rxiv pdf --force-figures` | Force figures |
| `MANUSCRIPT_PATH=path/ make pdf` | `rxiv pdf path/` | Custom path |

📖 **Complete migration guide**: [docs/MIGRATION.md](docs/MIGRATION.md)  
📚 **Complete CLI reference**: [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)  
📋 **CLI modernization changelog**: [docs/CHANGELOG_CLI.md](docs/CHANGELOG_CLI.md)

**⚡ GitHub Actions** (Team collaboration)
- **Prerequisites**: GitHub account only
- **Setup Time**: 5 minutes
- **Guide**: [Automated cloud builds guide](docs/workflows/github-actions.md)

**📝 VS Code** (Enhanced editing)
- **Prerequisites**: VS Code editor
- **Extension**: [VS Code Extension](https://github.com/HenriquesLab/vscode-rxiv-maker) for syntax highlighting

## Core Workflow

1. **Write** manuscript in Markdown (`01_MAIN.md`)
2. **Configure** metadata in YAML (`00_CONFIG.yml`)
3. **Create** figures with Python/R scripts or Mermaid diagrams
4. **Validate** with `make validate`
5. **Build** PDF with `make pdf`

## Documentation

<details>
<summary><strong>📚 Complete Documentation Index</strong></summary>

### Getting Started
- **[Installation Guide](docs/getting-started/installation.md)** - Complete setup for all platforms
- **[User Guide](docs/getting-started/user_guide.md)** - Complete usage instructions

### Platform Guides  
- **[Local Development Setup](docs/platforms/LOCAL_DEVELOPMENT.md)** - Platform-specific installation
- **[Docker Engine Mode](docs/workflows/docker-engine-mode.md)** - Containerized development
- **[Google Colab Tutorial](docs/tutorials/google_colab.md)** - Browser-based PDF generation
- **[GitHub Actions Guide](docs/workflows/github-actions.md)** - Automated cloud builds

### Advanced Features
- **[Change Tracking](docs/workflows/change-tracking.md)** - Version diff PDFs
- **[Troubleshooting](docs/troubleshooting/troubleshooting-missing-figures.md)** - Common issues and fixes
- **[Cache Migration Guide](docs/troubleshooting/cache-migration.md)** - Platform-standard cache directories

### Development
- **[VS Code Extension](https://github.com/HenriquesLab/vscode-rxiv-maker)** - Enhanced editing experience
- **[API Documentation](docs/api/)** - Code reference

</details>

### Quick Commands
```bash
make pdf                              # Generate PDF
make validate                         # Validate manuscript  
make pdf MANUSCRIPT_PATH=MY_PAPER     # Custom manuscript
make pdf FORCE_FIGURES=true           # Force figure regeneration
make pdf-track-changes TAG=v1.0.0     # Track changes vs git tag
make clean                            # Clean output files
make setup                            # Install dependencies
```

### Quick Help
- **Issues?** Check [Troubleshooting Guide](docs/troubleshooting/troubleshooting-missing-figures.md)
- **Platform problems?** See [Installation Guide](docs/getting-started/installation.md) 
- **Need help?** Visit [GitHub Discussions](https://github.com/henriqueslab/rxiv-maker/discussions)

## Project Structure

```
rxiv-maker/
├── MANUSCRIPT/              # Your manuscript files
│   ├── 00_CONFIG.yml       # Metadata and configuration
│   ├── 01_MAIN.md          # Main manuscript content
│   ├── 02_SUPPLEMENTARY_INFO.md  # Optional supplementary
│   ├── 03_REFERENCES.bib   # Bibliography
│   └── FIGURES/            # Figure generation scripts
├── output/                 # Generated PDFs and artifacts
├── src/                    # Rxiv-Maker source code
└── docs/                   # Documentation
```

## Docker Strategy

Rxiv-Maker provides robust Docker support through an integrated architecture that ensures consistency across environments while maintaining streamlined development workflows.

### 🏗️ Architecture Overview

**Integrated Design**: Docker infrastructure is maintained in [`src/docker/`](src/docker/) to:
- Enable streamlined development and maintenance workflows
- Provide centralized CI/CD workflows for container builds
- Simplify repository structure and dependency management
- Support rapid iteration and testing of Docker improvements

**Docker Infrastructure**: All Docker build scripts and configuration are consolidated in the [`src/docker/`](src/docker/) directory for simplified management.

### 🐳 Available Images

| Image | Purpose | Use Case |
|-------|---------|----------|
| `henriqueslab/rxiv-maker-base:latest` | Production image | PDF generation with mermaid.ink API |

**Note**: As of v1.8+, we use the mermaid.ink API for diagram generation, eliminating browser dependencies.

### 🚀 Usage Patterns

**Modern CLI**:
```bash
# Use Docker engine for builds
rxiv pdf --engine docker

# Set Docker as default
rxiv config set general.default_engine docker

# Use Docker engine
rxiv pdf --engine docker
```

**Legacy Make Commands**:
```bash
# Standard Docker builds
make pdf RXIV_ENGINE=DOCKER

# Docker builds
make pdf RXIV_ENGINE=DOCKER
```

### ⚙️ Benefits

- **Zero Dependencies**: Only Docker and Make required locally
- **Consistency**: Identical environment across development, CI/CD, and production
- **Performance**: Pre-built images with all dependencies (~5x faster than dependency installation)
- **Isolation**: No conflicts with existing system packages
- **Multi-platform**: AMD64 support with ARM64 compatibility via Rosetta

For detailed Docker documentation, see the [Docker infrastructure directory](src/docker/) and [Docker Engine Mode Guide](docs/workflows/docker-engine-mode.md).

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
git clone https://github.com/henriqueslab/rxiv-maker.git
pip install -e ".[dev]" && pre-commit install
```

### Release Process
For maintainers releasing new versions:
1. **Create GitHub release** with tag `v1.4.0`
2. **PyPI publishing** happens automatically
3. **Homebrew formula** updates manually or daily
4. See [Release Process Guide](docs/RELEASE_PROCESS.md) for details

### 🔧 Troubleshooting Installation

If installation fails or components are missing:

```bash
# Check what's installed
rxiv check-installation --detailed

# Repair broken installation
rxiv check-installation --fix

# Or manually repair
python -m rxiv_maker.install.manager --repair

# Reinstall system dependencies
python -m rxiv_maker.install.manager --mode full
```

**Common Issues:**
- **No admin rights**: Use `RXIV_INSTALL_MODE=minimal` 
- **Behind proxy**: System package managers may fail
- **Docker/CI**: Use `RXIV_SKIP_SYSTEM_DEPS=1`
- **Partial install**: Run repair command above

## How to Cite

<a href="https://arxiv.org/abs/2508.00836"><img src="docs/screenshots/preprint.png" align="right" width="300" style="margin-left: 20px; margin-bottom: 20px;" alt="Rxiv-Maker Preprint"/></a>

If you use Rxiv-Maker in your research, please cite our work:

**BibTeX:**
```bibtex
@misc{saraiva_2025_rxivmaker,
      title={Rxiv-Maker: an automated template engine for streamlined scientific publications}, 
      author={Bruno M. Saraiva and Guillaume Jaquemet and Ricardo Henriques},
      year={2025},
      eprint={2508.00836},
      archivePrefix={arXiv},
      primaryClass={cs.DL},
      url={https://arxiv.org/abs/2508.00836}, 
}
```

**APA Style:**
Saraiva, B. M., Jacquemet, G., & Henriques, R. (2025). Rxiv-Maker: an automated template engine for streamlined scientific publications. *Arxiv*. https://doi.org/10.48550/arXiv.2508.00836

## Related Projects

- **[Rxiv-Maker VS Code Extension](https://github.com/HenriquesLab/vscode-rxiv-maker)** - Enhanced editing experience with syntax highlighting, IntelliSense, and project integration

## Acknowledgments

We extend our gratitude to the scientific computing community, especially the matplotlib and seaborn communities for their plotting tools, the LaTeX Project for professional typesetting, and Mermaid for accessible diagram generation.

## License

MIT License - see [LICENSE](LICENSE) for details. Use it, modify it, share it freely.

---


**© 2025 Jacquemet and Henriques Labs | Rxiv-Maker**  
*"Because science is hard enough without fighting with LaTeX."*
