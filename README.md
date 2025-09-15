[![DOI](https://img.shields.io/badge/DOI-10.48550%2FarXiv.2508.00836-blue)](https://doi.org/10.48550/arXiv.2508.00836)
[![License](https://img.shields.io/github/license/henriqueslab/rxiv-maker?color=Green)](https://github.com/henriqueslab/rxiv-maker/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/henriqueslab/rxiv-maker?style=social)](https://github.com/HenriquesLab/rxiv-maker/stargazers)

# Rxiv-Maker

<img src="src/logo/logo-rxiv-maker.svg" align="right" width="200" style="margin-left: 20px;"/>

**Write scientific papers in Markdown. Get publication-ready PDFs with automated figures and citations.**

Perfect for biology researchers who want professional manuscripts without LaTeX complexity. Your analysis code runs automatically to generate up-to-date figures and results.

## 🔄 How it Works

Simple 4-step process:

1. **📝 Write in Markdown** - Use familiar markdown syntax (for advanced users, you can even embed Python code on the manuscript)
2. **🔄 Smart Processing** - Rxiv-Maker automatically runs your code and formats everything professionally
3. **📊 Live Figures** - Your scripts generate up-to-date plots and results in real-time
4. **📄 Professional PDF** - Get LaTeX-quality output without learning LaTeX

*From simple Markdown with analysis code to publication-ready PDF in seconds.*

## 🌟 Example in Action

See how a simple analysis becomes a professional manuscript:

**What you write (Markdown):**
```markdown
# Introduction

{{py:exec
import pandas as pd
df = pd.read_csv("FIGURES/DATA/results.csv")
correlation = df.corr().iloc[0,1]
sample_size = len(df)
}}

Our analysis of {{py:get sample_size}} samples in Figure @fig:results shows
significant improvement over previous methods [@smith2023; @jones2024].

![Research Results](FIGURES/generate_plot.py)
{#fig:results}

The correlation coefficient was r = {{py:get correlation:.2f}} (p < 0.001).
```

**What happens automatically:**
- 🐍 Python code runs and calculates your statistics
- 📊 Figure script executes to create your plot
- 📚 Citations get formatted and bibliography is generated
- 🔢 Cross-references are numbered automatically

**What you get:** Professional PDF with live data, properly formatted citations, numbered figures, and LaTeX-quality typesetting.

## 🚀 Installation

**Universal Installation (Recommended):**

```bash
# Using pipx (isolated environment, recommended)
pipx install rxiv-maker

# Or using pip
pip install rxiv-maker
```

<details>
<summary><strong>🐧 Linux Installation</strong></summary>

**Ubuntu/Debian:**
```bash
# 1. Install system dependencies
sudo apt update
sudo apt install python3-pip pipx texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended texlive-fonts-extra texlive-science fonts-liberation fonts-dejavu-core fonts-lmodern fontconfig

# 2. Install rxiv-maker
pipx install rxiv-maker

# 3. Verify installation
rxiv check-installation
```

</details>

<details>
<summary><strong>🍎 macOS Installation</strong></summary>

**Prerequisites:**
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install system dependencies
brew install pipx
brew install texlive # Full LaTeX installation
```

**Installation:**
```bash
# Install rxiv-maker
pipx install rxiv-maker

# Verify installation
rxiv check-installation
```

</details>

<details>
<summary><strong>🪟 Windows Installation</strong></summary>

**WSL2 (Recommended)**
```bash
# Install WSL2 with Ubuntu (Windows PowerShell as Administrator)
wsl --install -d Ubuntu-22.04

# Restart computer, then launch Ubuntu and run:
sudo apt update
sudo apt install python3-pip pipx texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended texlive-fonts-extra texlive-science fonts-liberation fonts-dejavu-core fonts-lmodern fontconfig
pipx install rxiv-maker
rxiv check-installation
```

</details>

**Verify your installation:**
```bash
rxiv check-installation  # Verify all dependencies
rxiv --version           # Check version
rxiv --help             # View available commands
```

## 🔥 Quick Start

**Get your first PDF in under 2 minutes:**

```bash
# Create manuscript 
rxiv init my-paper

# Generate PDF
rxiv pdf my-paper
```

**🎯 [Complete Getting Started Guide →](docs/quick-start/first-manuscript.md)**

## ⚙️ Advanced Features

**🐍 Python Integration**
- Execute analysis code directly in your manuscript with `{{py:exec ...}}` and `{{py:get variable}}`
- Real-time data analysis and visualization
- Matplotlib, ggplot2, and custom plotting support

**📚 Smart Citations & References**
- BibTeX integration with `[@citation]` syntax
- Automatic bibliography generation and formatting
- CrossRef DOI resolution and validation

**🎨 Scientific Writing Features**
- Auto-numbered figures, tables, and equations
- Cross-references (`@fig:plot`, `@eq:formula`)
- Mathematical notation with LaTeX math support
- Professional formatting and typesetting

**🔧 Workflow & Collaboration**
- Git-friendly version control for manuscripts
- Modern CLI with progress indicators
- Comprehensive validation and error checking
- Multi-platform support (Windows, macOS, Linux)

## 📚 Documentation & Help

**📖 Learning Resources**
| **Start Here** | **Purpose** | **Time** |
|-------------|-----------|--------|
| **[🚀 Getting Started](docs/quick-start/first-manuscript.md)** | Your first manuscript in 5 minutes | 5 min |
| **[📚 User Guide](docs/guides/user_guide.md)** | Complete workflows & all features | 30 min |
| **[🐍 Python Guide](docs/guides/python-execution-guide.md)** | Data analysis & code execution | 15 min |
| **[🔧 Troubleshooting](docs/troubleshooting/troubleshooting.md)** | Fix common issues | As needed |

**🤝 Community & Support**
- **💬 [Ask Questions](https://github.com/henriqueslab/rxiv-maker/discussions)** - Get help from the community
- **🐛 [Report Issues](https://github.com/henriqueslab/rxiv-maker/issues)** - Found a bug? Let us know
- **🧪 [Try Online](https://colab.research.google.com/github/HenriquesLab/rxiv-maker/blob/main/notebooks/rxiv_maker_colab.ipynb)** - Test without installing
- **📚 [See Examples](examples/)** - Real manuscript examples

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
