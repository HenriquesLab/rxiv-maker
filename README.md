[![DOI](https://img.shields.io/badge/DOI-10.48550%2FarXiv.2508.00836-blue)](https://doi.org/10.48550/arXiv.2508.00836)
[![License](https://img.shields.io/github/license/henriqueslab/rxiv-maker?color=Green)](https://github.com/henriqueslab/rxiv-maker/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/henriqueslab/rxiv-maker?style=social)](https://github.com/HenriquesLab/rxiv-maker/stargazers)

# Rxiv-Maker

<img src="src/logo/logo-rxiv-maker.svg" align="right" width="200" style="margin-left: 20px;"/>

**Write scientific preprints in Markdown. Generate publication-ready PDFs instantly.**

Rxiv-Maker transforms scientific preprint writing by converting enhanced Markdown into professional PDFs with automated figure generation, citation management, and LaTeX typesetting - no LaTeX knowledge required. One beautiful template, infinite possibilities.

## ✨ Why Rxiv-Maker?

### 🎯 **For Researchers**
- **Write in Markdown**: Focus on content, not formatting
- **Automated Figures**: Python/R scripts become publication figures  
- **Smart Citations**: BibTeX integration with cross-references
- **Instant PDFs**: From Markdown to camera-ready in seconds

### 🚀 **For Teams**  
- **Git-Friendly**: Version control for manuscripts and figures
- **Reproducible**: All figures generated from code
- **Collaborative**: Standard tools, no vendor lock-in
- **Multi-Platform**: Works everywhere with Docker support

### 📈 **For Publishing**
- **arXiv Ready**: Generate submission packages automatically
- **Track Changes**: Visual diff between manuscript versions
- **Quality Assurance**: Built-in validation and error checking

## 🔥 Quick Start

**Get your first PDF in under 2 minutes:**

```bash
# Install
pip install rxiv-maker

# Create manuscript 
rxiv init my-paper
cd my-paper

# Generate PDF
rxiv pdf
```

**🎯 [Complete Getting Started Guide →](docs/quick-start/first-manuscript.md)**

## 🏆 Key Features

### 🎨 **Enhanced Markdown**
- Scientific cross-references (`@fig:plot`, `@eq:formula`)
- Auto-numbered figures, tables, and equations
- Mathematical notation with LaTeX math
- Code blocks with syntax highlighting

### 📊 **Automated Figures**
- Execute Python/R scripts during PDF generation
- Matplotlib, ggplot2, and custom visualizations
- Consistent styling and professional quality
- Version-controlled figure code

### 📚 **Citation Management**
- BibTeX integration with `[@citation]` syntax
- Automatic bibliography generation
- Multiple citation styles (APA, Nature, etc.)
- CrossRef DOI resolution

### 🔧 **Developer Experience**
- Modern CLI with rich output and progress bars
- Docker support for consistent environments
- Git-friendly workflow with meaningful diffs
- Comprehensive validation and error reporting

## 🌟 Example Manuscript

**Input Markdown:**
```markdown
# Introduction

Our analysis in Figure @fig:results shows significant improvement
over previous methods [@smith2023; @jones2024].

![Research Results](FIGURES/generate_plot.py)
{#fig:results}

The correlation coefficient was $r = 0.95$ (p < 0.001).

## References
```

**Output:** Professional PDF with numbered figures, citations, and LaTeX-quality typesetting.

## 📖 Documentation

| Guide | Purpose | Time |
|-------|---------|------|
| **[🚀 Getting Started](docs/quick-start/first-manuscript.md)** | Installation → First PDF | 5 min |
| **[📚 User Guide](docs/guides/user_guide.md)** | Complete workflows & features | 30 min |
| **[⚙️ CLI Reference](docs/reference/cli-reference.md)** | All commands & options | 10 min |
| **[🔧 Troubleshooting](docs/troubleshooting/troubleshooting.md)** | Common issues & solutions | As needed |
| **[👩‍💻 Developer Guide](docs/development/developer-guide.md)** | Contributing & development | 45 min |

## 🎯 Use Cases

### 📄 **Research Preprints**
- arXiv preprints with automated submission packages
- bioRxiv and other preprint servers with professional formatting
- Conference papers with consistent styling

### 📊 **Reports & Analyses**  
- Data analysis reports with live figures
- Technical documentation with code examples
- Grant applications with professional formatting

### 🎓 **Academic Workflows**
- Thesis chapters with cross-references
- Collaborative writing with version control
- Supplementary materials with automated generation

## 🏃‍♀️ Installation Options

**Need different installation methods?** [View all options →](docs/quick-start/installation.md)

- **🔥 pip install**: Universal, works everywhere
- **🍺 Homebrew**: macOS/Linux package management  
- **🐳 Docker**: Containerized, zero config
- **🌐 Google Colab**: Browser-based, no installation
- **🪟 WSL2**: Best Windows experience

## 🚀 Essential Commands

```bash
rxiv init my-paper          # Create new manuscript
rxiv pdf                    # Generate PDF  
rxiv validate              # Check manuscript quality
rxiv arxiv                 # Prepare arXiv submission
rxiv track-changes v1 v2   # Visual version comparison
```

**[📖 Complete Command Reference →](docs/reference/cli-reference.md)**

## 🤝 Community

- **💬 [GitHub Discussions](https://github.com/henriqueslab/rxiv-maker/discussions)** - Ask questions, share tips
- **🐛 [Issues](https://github.com/henriqueslab/rxiv-maker/issues)** - Report bugs, request features  
- **📚 [Examples](examples/)** - Real-world manuscript examples
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

**[📋 Full Contributing Guide →](docs/development/developer-guide.md)**

## 📄 Citation

If Rxiv-Maker helps your research, please cite:

```bibtex
@misc{saraiva_2025_rxivmaker,
  title={Rxiv-Maker: an automated template engine for streamlined scientific publications}, 
  author={Bruno M. Saraiva and Guillaume Jaquemet and Ricardo Henriques},
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

**[🚀 Start Writing →](docs/quick-start/first-manuscript.md)** | **[📚 Learn More →](docs/guides/user_guide.md)** | **[⚙️ Commands →](docs/reference/cli-reference.md)**

</div>
