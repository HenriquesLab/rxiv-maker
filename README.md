[![DOI](https://img.shields.io/badge/DOI-10.48550%2FarXiv.2508.00836-blue)](https://doi.org/10.48550/arXiv.2508.00836)
[![License](https://img.shields.io/github/license/henriqueslab/rxiv-maker?color=Green)](https://github.com/henriqueslab/rxiv-maker/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/henriqueslab/rxiv-maker?style=social)](https://github.com/HenriquesLab/rxiv-maker/stargazers)

# Rxiv-Maker

<img src="https://raw.githubusercontent.com/HenriquesLab/rxiv-maker/main/src/logo/logo-rxiv-maker.svg" align="right" width="200" style="margin-left: 20px;"/>

**Write scientific preprints in Markdown. Generate publication-ready PDFs efficiently.**

> **💡 Best Experience:** Use the [VS Code Extension](https://marketplace.visualstudio.com/items?itemName=HenriquesLab.rxiv-maker) for syntax highlighting and citations.

Rxiv-Maker converts enhanced Markdown into professional PDFs with automated figure generation, citation management, and LaTeX typesetting. While LaTeX installation is required, users don't need to write LaTeX code directly.

## ✨ Why Rxiv-Maker?

### 🎯 **For Researchers**
- **Write in Markdown**: Focus on content, not formatting
- **Automated Figures**: Python/R scripts become publication figures  
- **Smart Citations**: BibTeX integration with cross-references
- **Automated PDF Generation**: From Markdown to professional academic PDF

### 🚀 **For Teams**  
- **Git-Friendly**: Version control for manuscripts and figures
- **Reproducible**: All figures generated from code
- **Collaborative**: Standard tools, no vendor lock-in
- **Multi-Platform**: Works everywhere with local installation

### 📈 **For Publishing**
- **arXiv Ready**: Generate submission packages automatically
- **Track Changes**: Visual diff between manuscript versions
- **Quality Assurance**: Built-in validation and error checking

## 🚀 Installation

**Recommended (All Platforms):**
```bash
pipx install rxiv-maker
rxiv check-installation
```

**📋 Requirements:**
> [!IMPORTANT]
> **LaTeX** is required for PDF generation. Run `rxiv check-installation` to verify your setup.

- **Python 3.11+**: For rxiv-maker CLI and figure generation
- **LaTeX Distribution**: Install via your system package manager or see the [installation guide](https://rxiv-maker.henriqueslab.org/getting-started/installation/)

> **🍎 macOS Users:** Prefer Homebrew? `brew install rxiv-maker` includes LaTeX automatically.
> **📖 Need help?** See the [complete installation guide](https://rxiv-maker.henriqueslab.org/getting-started/installation/) for platform-specific instructions.

**Upgrading:**
```bash
# Automatic upgrade (detects your installation method)
rxiv upgrade

# Or manually: pipx upgrade rxiv-maker
```

## 🔥 Quick Start

**Get your first PDF quickly:**

```bash
# Create manuscript
rxiv init my-paper
cd my-paper

# Generate PDF
rxiv pdf
```

**Or explore the complete example manuscript:**

```bash
# Clone the official example with one command
rxiv get-rxiv-preprint
cd manuscript-rxiv-maker/MANUSCRIPT

# Generate PDF
rxiv pdf
```

**🎯 [Getting Started Guide](docs/first-manuscript.md)**

## 🏆 Key Features

### 🎨 **Enhanced Markdown**
- Scientific cross-references (`@fig:plot`, `@eq:formula`)
- Auto-numbered figures, tables, and equations
- Mathematical notation with LaTeX math
- Code blocks with syntax highlighting
- Markdown comments (`<!-- note -->`) for TODOs and notes

### 📊 **Automated Figures & Data Analysis**
- Execute Python/R scripts during PDF generation
- **🐍 NEW: Jupyter-like executable Python code blocks**
- Real-time data analysis with `{{py:exec}}` and `{{py:get variable}}`
- Matplotlib, ggplot2, and custom visualizations
- Version-controlled figure code and analysis modules

### 📚 **Citation Management**
- BibTeX integration with `[@citation]` syntax
- Automatic bibliography generation
- **Multiple citation styles**: Choose between numbered `[1, 2]` or author-date `(Smith, 2024)` citations
- **Configurable author name formatting**: Format bibliography as `Smith, J.A.` or `Smith, John A.` or `John A. Smith`
- **Inline DOI resolution**: Paste DOIs directly in text `10.1038/...` and auto-convert to citations
- CrossRef/DataCite DOI validation and metadata fetching


> 📖 **Learn more**: [10-Minute Tutorial](https://rxiv-maker.henriqueslab.org/getting-started/citations-tutorial/) | [Complete Guide](https://rxiv-maker.henriqueslab.org/guides/citations-and-references/)

### 🔧 **Developer Experience**
- Modern CLI with rich output and progress bars
- Consistent environments with package management
- Git-friendly workflow with meaningful diffs
- Comprehensive validation and error reporting

## 🌟 Example Manuscript

> **💡 Get this complete example instantly:**
> ```bash
> rxiv get-rxiv-preprint
> ```
> This clones [manuscript-rxiv-maker](https://github.com/HenriquesLab/manuscript-rxiv-maker) with all features demonstrated.

**Input Markdown:**
```markdown
# Introduction

Rxiv-Maker enables collaborative manuscript writing with
automated citations [@henriques2024rxivmaker] and figure
generation [@smith2023; @jones2024].

![Example Results](FIGURES/results_plot.py)
{#fig:results}

Our findings in Figure @fig:results demonstrate this approach.

DOI: 10.1038/s41467-024-12345-x will auto-resolve to citation.

## References
```

**Output:** Professional PDF with auto-numbered figures, resolved citations, and LaTeX typesetting.

> **💡 See the complete working example:**
> `rxiv get-rxiv-preprint` - clones [manuscript-rxiv-maker](https://github.com/HenriquesLab/manuscript-rxiv-maker) with advanced features including Python execution, data analysis, and more.

## 📖 Documentation

### For Users
Visit our **[official documentation website](https://rxiv-maker.henriqueslab.org)** for comprehensive guides:
- **[Installation Guide](https://rxiv-maker.henriqueslab.org/getting-started/installation/)** - Setup for all platforms
- **[First Manuscript Tutorial](https://rxiv-maker.henriqueslab.org/getting-started/first-manuscript/)** - 5-minute walkthrough
- **[User Guide](https://rxiv-maker.henriqueslab.org/guides/)** - Complete features and workflows
- **[CLI Reference](https://rxiv-maker.henriqueslab.org/api/)** - All commands and options
- **[Troubleshooting](https://rxiv-maker.henriqueslab.org/community/troubleshooting/)** - Solutions to common issues

### For Developers
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[CI-LOCAL-TESTING.md](CI-LOCAL-TESTING.md)** - Local CI workflow testing
- **[Developer Docs](docs/)** - Technical documentation and API details

## 🎯 Use Cases

<details>
<summary>📄 <strong>Research Preprints, Reproducible Figures, and Collaborative Workflows</strong></summary>

### 📄 **Research Preprints**
- arXiv preprints with automated submission packages
- bioRxiv and other preprint servers with professional formatting
- Conference papers with consistent styling

### 📊 **Preprint Features**
- **Reproducible figures** generated from Python/R scripts
- **Live data integration** that updates with analysis changes
- **Professional formatting** optimized for preprint servers

### 🎓 **Preprint Workflows**
- **arXiv submissions** with cross-references and mathematical notation
- **Collaborative preprint writing** with version control
- **Supplementary materials** with automated generation

</details>

## 🏃‍♀️ Ecosystem & Workflows

**Three ways to use rxiv-maker:**
- 🖥️ **Local Installation**: Install directly on your system (recommended)
- 🐳 **Docker**: Pre-configured container with all dependencies
- ☁️ **Cloud**: GitHub Actions or Google Colab for browser-based editing

<details>
<summary>🔗 <strong>Ecosystem Details</strong> - Core repositories, development tools, and integration patterns</summary>

### 📦 **Core Repositories**

1. **[rxiv-maker](https://github.com/HenriquesLab/rxiv-maker)** (this repository)
   - Main Python package and CLI tool
   - Core processing engine
   - Development and contribution hub

2. **[website-rxiv-maker](https://github.com/HenriquesLab/website-rxiv-maker)**
   - Official documentation website
   - User guides and tutorials
   - API reference and examples
   - Visit: [rxiv-maker.henriqueslab.org](https://rxiv-maker.henriqueslab.org)

3. **[manuscript-rxiv-maker](https://github.com/HenriquesLab/manuscript-rxiv-maker)**
   - Official example manuscript (published as arXiv:2508.00836)
   - Complete working example with all features
   - Clone with: `rxiv get-rxiv-preprint`

### 🔧 **Development Tools**

- **📝 [VS Code Extension](https://github.com/HenriquesLab/vscode-rxiv-maker)**
  - Syntax highlighting and autocompletion
  - Integrated build commands
  - Real-time validation

- **🐳 [Docker Support](https://github.com/HenriquesLab/docker-rxiv-maker)**
  - Containerized execution environment with pre-installed rxiv-maker
  - Pre-configured LaTeX, Python, R, and all dependencies
  - Perfect for CI/CD and users without local LaTeX installation
  - Separate repository for easier maintenance and faster image updates

### 🚀 **Deployment Options**

- **⚡ Local Installation**: Native system setup (recommended for development)
- **☁️ GitHub Actions**: Automated cloud builds and CI/CD
- **🌐 Google Colab**: Browser-based editing without local installation
- **🐳 Containers**: Docker for reproducible environments

### 📦 **Architecture Diagram**

```mermaid
graph LR
    A[rxiv-maker<br/>Core Tool] --> B[PyPI]
    A --> C[Homebrew]
    D[docker-rxiv-maker<br/>Container] --> E[Docker Hub]
    D -.installs.-> A
    F[vscode-rxiv-maker<br/>Extension] -.extends.-> A
    G[website-rxiv-maker<br/>Docs] -.documents.-> A
    H[manuscript-rxiv-maker<br/>Example] -.demonstrates.-> A

    style A fill:#e1f5ff
    style D fill:#fff4e6
    style F fill:#fff4e6
    style G fill:#e8f5e9
    style H fill:#e8f5e9
```

### 🔗 **Repository Cross-Reference**

| Repository | Purpose | Install/Access | Dependencies |
|------------|---------|----------------|--------------|
| **rxiv-maker** (this repo) | Main CLI tool & Python package | `brew install` / `pipx install` | LaTeX |
| **[docker-rxiv-maker](https://github.com/HenriquesLab/docker-rxiv-maker)** | Pre-built container with all deps | `docker pull henriqueslab/rxiv-maker-base` | Docker |
| **[manuscript-rxiv-maker](https://github.com/HenriquesLab/manuscript-rxiv-maker)** | Official example (arXiv:2508.00836) | `rxiv get-rxiv-preprint` | rxiv-maker |
| **[vscode-rxiv-maker](https://github.com/HenriquesLab/vscode-rxiv-maker)** | VS Code extension | VS Code Marketplace | rxiv-maker |
| **[website-rxiv-maker](https://github.com/HenriquesLab/website-rxiv-maker)** | Documentation website | [rxiv-maker.henriqueslab.org](https://rxiv-maker.henriqueslab.org) | - |

> **Note**: As of v1.8.4, we've streamlined the ecosystem while maintaining multiple installation options (Homebrew, pip, pipx, uv) with optional Docker support for containerized workflows.
>
> **📋 [Ecosystem Guide](docs/ECOSYSTEM.md)** - Complete architecture and integration patterns
> **📋 [Migration Guide](docs/migration-v1.7.9.md)** - For users upgrading from previous versions

</details>

## 🚀 Quick Commands

**Essential commands to get started:**

```bash
rxiv init my-paper       # Create new manuscript
rxiv pdf                 # Generate PDF
rxiv validate           # Check manuscript quality
rxiv upgrade            # Upgrade to latest version
```

<details>
<summary>📋 <strong>Complete Command Reference</strong> - Repository management, export options, and advanced workflows</summary>

### Core Commands
```bash
rxiv init my-paper          # Create new manuscript
rxiv get-rxiv-preprint     # Clone complete example manuscript
rxiv pdf                    # Generate PDF
rxiv docx                   # Export to DOCX for collaborative review
rxiv validate              # Check manuscript quality
rxiv arxiv                 # Prepare arXiv submission
rxiv track-changes v1 v2   # Visual version comparison
```

### Repository Management
```bash
# Initial setup
rxiv repo-init             # Interactive setup
rxiv config                # Interactive configuration menu

# Create and manage repositories
rxiv create-repo my-paper  # Create new manuscript repository (with GitHub integration)
rxiv repos                 # List all manuscript repositories
rxiv repos-search          # Search and clone from GitHub

# Configuration
rxiv config set-repo-parent-dir ~/manuscripts
rxiv config set-repo-org YourGitHubOrg
rxiv config --non-interactive  # Show current settings
```

### Maintenance
```bash
rxiv upgrade               # Upgrade to latest version
rxiv changelog             # View changelog and release notes
rxiv changelog --recent 5  # View last 5 versions
```

> **💡 CI/Automation Note:** All interactive commands support non-interactive mode or configuration files for use in CI/CD pipelines and automated workflows. Use `--non-interactive` flag or configure via `~/.rxiv-maker/config` for non-TTY environments.

**📖 [Complete CLI Reference](https://rxiv-maker.henriqueslab.org/getting-started/quick-reference/)** - Full command documentation with examples and options.

</details>

## 🤝 Community

- **💬 [GitHub Discussions](https://github.com/henriqueslab/rxiv-maker/discussions)** - Ask questions, share tips
- **🐛 [Issues](https://github.com/henriqueslab/rxiv-maker/issues)** - Report bugs, request features  
- **📚 [Example Manuscript](https://github.com/HenriquesLab/manuscript-rxiv-maker)** - Clone instantly: `rxiv get-rxiv-preprint`
- **🧪 [Google Colab](https://colab.research.google.com/github/HenriquesLab/rxiv-maker/blob/main/notebooks/rxiv_maker_colab.ipynb)** - Try without installing

## 🏗️ Contributing

We welcome contributions! Whether it's:

- 🐛 Bug reports and fixes
- ✨ New features and improvements  
- 📖 Documentation enhancements
- 🧪 Testing and validation

**Quick contributor setup:**
```bash
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker
pip install -e ".[dev]"
pre-commit install
```

## 📄 Citation

If Rxiv-Maker helps your research, please cite:

```bibtex
@misc{saraiva_2025_rxivmaker,
  title={Rxiv-Maker: an automated template engine for streamlined scientific publications}, 
  author={Bruno M. Saraiva and António D. Brito and Guillaume Jaquemet and Ricardo Henriques},
  year={2025},
  eprint={2508.00836},
  archivePrefix={arXiv},
  url={https://arxiv.org/abs/2508.00836}
}
```

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**🔬 From [Jacquemet](https://github.com/guijacquemet) and [Henriques](https://github.com/HenriquesLab) Labs**

*"Because science is hard enough without fighting with LaTeX."*

**[🚀 Start Writing](https://rxiv-maker.henriqueslab.org/getting-started/first-manuscript/)** | **[📚 User Guide](https://rxiv-maker.henriqueslab.org/guides/)** | **[⚙️ CLI Reference](https://rxiv-maker.henriqueslab.org/getting-started/quick-reference/)**

</div>
