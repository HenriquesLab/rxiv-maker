[![DOI](https://img.shields.io/badge/DOI-10.48550%2FarXiv.2508.00836-blue)](https://doi.org/10.48550/arXiv.2508.00836)
[![License](https://img.shields.io/github/license/henriqueslab/rxiv-maker?color=Green)](https://github.com/henriqueslab/rxiv-maker/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/henriqueslab/rxiv-maker?style=social)](https://github.com/HenriquesLab/rxiv-maker/stargazers)

# Rxiv-Maker

<img src="src/logo/logo-rxiv-maker.svg" align="right" width="200" style="margin-left: 20px;"/>

**Write scientific preprints in Markdown. Generate publication-ready PDFs efficiently.**

Rxiv-Maker converts enhanced Markdown into professional PDFs with automated figure generation, citation management, and LaTeX typesetting. While LaTeX installation is required, users don't need to write LaTeX code directly.

## ✨ Why Rxiv-Maker?

### 🎯 **For Researchers**
- **Write in Markdown**: Focus on content, not formatting
- **Automated Figures**: Python/R scripts become publication figures  
- **Smart Citations**: BibTeX integration with cross-references
- **Instant PDFs**: From Markdown to professional academic PDF

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

**Quick Installation (All Platforms):**

```bash
# Using pipx (recommended)
pipx install rxiv-maker

# Verify installation
rxiv check-installation
```

**Need platform-specific setup?** 📖 **[Complete Installation Guide →](https://rxiv-maker.henriqueslab.org/getting-started/installation/)**

**For developers:** 🛠️ **[Developer Setup →](docs/quick-start/installation.md)**

## 🔥 Quick Start

**Get your first PDF quickly:**

```bash
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

### 📊 **Automated Figures & Data Analysis**
- Execute Python/R scripts during PDF generation
- **🐍 NEW: Jupyter-like executable Python code blocks**
- Real-time data analysis with `{{py:exec}}` and `{{py:get variable}}`
- Matplotlib, ggplot2, and custom visualizations
- Version-controlled figure code and analysis modules

### 📚 **Citation Management**
- BibTeX integration with `[@citation]` syntax
- Automatic bibliography generation
- Multiple citation styles (APA, Nature, etc.)
- CrossRef DOI resolution

### 🔧 **Developer Experience**
- Modern CLI with rich output and progress bars
- Consistent environments with package management
- Git-friendly workflow with meaningful diffs
- Comprehensive validation and error reporting

## 🌟 Example Manuscript

**Input Markdown:**
```markdown
# Introduction

{{py:exec
import pandas as pd
import numpy as np

df = pd.read_csv("FIGURES/DATA/experimental_results.csv")

# Calculate correlation between specific columns (safer than iloc)
# Assuming the CSV has columns like 'treatment_effect' and 'baseline_score'
correlation = df['treatment_effect'].corr(df['baseline_score'])
sample_size = len(df)
}}

Our analysis of {{py:get sample_size}} samples in Figure @fig:results shows 
significant improvement over previous methods [@smith2023; @jones2024].

![Research Results](EXAMPLE_MANUSCRIPT/FIGURES/SFigure__arxiv_growth.py)
{#fig:results}

The correlation coefficient was r = {{py:get correlation:.2f}} (p < 0.001).

## References
```

**Output:** Professional PDF with numbered figures, live data integration, citations, and LaTeX-quality typesetting.

## 📖 Documentation

| Guide | Purpose | Scope |
|-------|---------|-------|
| **[🚀 Getting Started](docs/quick-start/first-manuscript.md)** | Installation → First PDF | Quick start |
| **[📚 User Guide](docs/guides/user_guide.md)** | Complete workflows & features | Comprehensive |
| **[🐍 Python Execution Guide](docs/guides/python-execution-guide.md)** | Jupyter-like code blocks & data analysis | Focused guide |
| **[⚙️ CLI Reference](docs/reference/cli-reference.md)** | All commands & options | Reference |
| **[🔧 Troubleshooting](docs/troubleshooting/troubleshooting.md)** | Common issues & solutions | As needed |
| **[👩‍💻 Developer Guide](docs/development/developer-guide.md)** | Contributing & development | Advanced guide |

## 🎯 Use Cases

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

## 🏃‍♀️ Alternative Workflows

**Need specialized environments?**

- **🌐 Google Colab**: Browser-based editing and PDF generation  
- **⚡ GitHub Actions**: Automated cloud builds for teams
- **🐳 Docker**: Use [docker-rxiv-maker](https://github.com/HenriquesLab/docker-rxiv-maker) for containerized execution

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
- **📚 [Example Manuscript](EXAMPLE_MANUSCRIPT/)** - Complete manuscript example
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
