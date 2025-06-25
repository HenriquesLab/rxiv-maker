[![License](https://img.shields.io/github/license/henriqueslab/rxiv-maker?color=Green)](https://github.com/henriqueslab/rxiv-maker/blob/main/LICENSE)
[![Contributors](https://img.shields.io/github/contributors-anon/henriqueslab/rxiv-maker)](https://github.com/henriqueslab/rxiv-maker/graphs/contributors)
[![GitHub stars](https://img.shields.io/github/stars/henriqueslab/rxiv-maker?style=social)](https://github.com/henriqueslab/rxiv-maker/)
[![GitHub forks](https://img.shields.io/github/forks/henriqueslab/rxiv-maker?style=social)](https://github.com/henriqueslab/rxiv-maker/)

![Enhanced Markdown](https://img.shields.io/badge/enhanced_markdown-20+_features-blue?labelColor=white&color=gray)
![Figure Generation](https://img.shields.io/badge/figures-python_&_mermaid-blue?labelColor=white&color=gray)
![Cross References](https://img.shields.io/badge/cross_refs-automated-blue?labelColor=white&color=gray)
![Citations](https://img.shields.io/badge/citations-bibtex-blue?labelColor=white&color=gray)
![LaTeX Output](https://img.shields.io/badge/output-professional_pdf-blue?labelColor=white&color=gray)
![GitHub Actions](https://img.shields.io/badge/deployment-cloud_&_local-blue?labelColor=white&color=gray)

<img src="src/logo/logo-rxiv-maker.svg" align="right" width="200"/>

# RXiv-Maker

RXiv-Maker is an automated LaTeX article generation system that transforms scientific writing from chaos to clarity. It converts Markdown manuscripts into publication-ready PDFs with reproducible figures, professional typesetting, and zero LaTeX hassle.

The platform bridges the gap between **easy writing** (Markdown) and **beautiful output** (LaTeX), featuring automated figure generation from Python scripts and Mermaid diagrams, seamless citation management, and GitHub Actions integration for cloud-based PDF generation.

RXiv-Maker extends the capabilities of traditional scientific writing by ensuring version control compatibility, reproducible science workflows, and professional formatting that meets publication standards.

## Key Features

- **20+ Enhanced Markdown Features** including scientific cross-references, citations, subscript/superscript, and programmatic figure generation. Complete feature list documented in [Supplementary Table](EXAMPLE_MANUSCRIPT/02_SUPPLEMENTARY_INFO.md).
- **Automated Figure Generation** from Python scripts and Mermaid diagrams with smart caching and dependency management.
- **GitHub Actions Integration** for cloud-based PDF generation with manual triggers and automated releases.
- **Professional LaTeX Templates** supporting various citation styles and academic formatting conventions.
- **Version Control Friendly** with Git-based workflows and reproducible build processes.
- **Multi-Environment Support** including local development, Google Colab, and GitHub Actions automation.

## Key Benefits of RXiv-Maker

- **Accessibility:** Write in familiar Markdown syntax without LaTeX expertise. Interactive workflows lower barriers for researchers.
- **Reproducibility:** Automated figure generation and version control ensure consistent results across builds.
- **Flexibility:** Generate PDFs locally, in the cloud, or via GitHub Actions. No vendor lock-in.
- **Professional Output:** LaTeX-quality formatting with automated bibliography and cross-reference management.
- **Collaboration:** Git-based workflows enable team editing with automated PDF generation for reviews.
- **Extensibility:** Modular architecture supports custom templates, styles, and figure generation scripts.

## What is RXiv-Maker?

- A comprehensive manuscript generation system combining Markdown simplicity with LaTeX professionalism.
- Fully automated figure generation from Python scripts and Mermaid diagrams integrated into the document build process.
- GitHub Actions workflows providing cloud-based PDF generation with dependency caching and artifact management.
- Professional templates supporting academic publishing conventions including author affiliations, ORCID integration, and citation styles.
- Version-controlled workflow enabling collaborative writing with automated quality checks and build validation.

## Quickstart

<details>
<summary><strong>🚀 Quick Start (2 minutes)</strong></summary>

### 🎯 **Which Option is Right for You?**

| User Type | Best Option | Requirements | Setup Time |
|-----------|-------------|--------------|------------|
| **📚 New to coding** | Google Colab | Google account | 2 minutes |
| **⚡ Want automation** | GitHub Actions | GitHub account | 5 minutes |
| **🔧 Full control** | Local Install | Python 3.9+, LaTeX, Make | 10-30 minutes |

### Google Colab (Easiest - No Installation Required)
**Perfect for beginners and quick experiments without any local setup.**

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/henriqueslab/rxiv-maker/blob/main/rxiv_forge_colab.ipynb)

**✅ Perfect for:**
- First-time users wanting to try RXiv-Maker
- Quick one-off document generation
- Users without technical setup experience
- Collaborative editing with shared notebooks

### GitHub Actions (Recommended for Regular Use)
**Automatic PDF generation on every commit - works with both public and private repos.**

1. **Fork** this repository to your GitHub account
2. **Go to Actions tab** → "Build and Release PDF"
3. **Click "Run workflow"** → Select manuscript path → "Run workflow"
4. **Download PDF** from completed workflow run

**✅ Perfect for:**
- Regular manuscript writing and revisions
- Team collaboration and version control
- Automatic backup and PDF generation
- Professional workflow without local setup

### Local Development (Full Control)
**First time? See [platform setup guide](docs/platforms/LOCAL_DEVELOPMENT.md) for Windows/macOS/Linux installation.**

```bash
# Clone the repository
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker

# Set up environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
make setup

# Generate your first PDF
make pdf MANUSCRIPT_PATH=EXAMPLE_MANUSCRIPT
```

**✅ Perfect for:**
- Advanced users and developers
- Custom modifications and extensions
- Offline work environments
- Integration with local development tools

</details>

<details>
<summary><strong>📋 Installation Options</strong></summary>

### Option A: Fork (Recommended for Contributors)
```bash
# 1. Click "Fork" on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/rxiv-maker.git
cd rxiv-maker

# 3. Add upstream for updates
git remote add upstream https://github.com/henriqueslab/rxiv-maker.git
```

### Option B: Direct Clone
```bash
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker
```

### Prerequisites
- **Local**: Python 3.9+, LaTeX, Make (10-30 minutes setup) - [Platform-specific instructions](docs/platforms/LOCAL_DEVELOPMENT.md)
- **GitHub Actions**: GitHub account (instant)
- **Colab**: Google account (instant)

</details>

<details>
<summary><strong>🖥️ Platform Setup</strong></summary>

### Local Development
```bash
# After cloning, install dependencies
make setup

# Test with example
make pdf MANUSCRIPT_PATH=EXAMPLE_MANUSCRIPT

# Create your manuscript
cp -r EXAMPLE_MANUSCRIPT MY_ARTICLE
# Edit MY_ARTICLE/00_CONFIG.yml and 01_MAIN.md
make pdf MANUSCRIPT_PATH=MY_ARTICLE
```

### Requirements
- **LaTeX**: Full installation required - [Windows/macOS/Linux guides](docs/platforms/LOCAL_DEVELOPMENT.md)
- **Python**: 3.9+ with virtual environment recommended
- **Make**: Build automation tool (included in platform guides)

</details>

## Core Workflow

1. **Write** your manuscript in Markdown (`01_MAIN.md`)
2. **Configure** metadata in YAML (`00_CONFIG.yml`)
3. **Create** figures with Python scripts or Mermaid diagrams
4. **Build** PDF locally (`make pdf`) or via GitHub Actions
5. **Collaborate** using Git workflows with automated PDF generation

## Enhanced Markdown Syntax

RXiv-Maker extends standard Markdown with 20+ scientific publishing features:

```markdown
# Academic Markdown Features

## Text formatting
**bold text** *italic text* ~subscript~ ^superscript^
H~2~O, CO~2~, E=mc^2^, Ca^2+^

**📌 Important for Forks**: 
- Forked repositories have limited GitHub Actions permissions
- PDFs are generated and available as **workflow artifacts** (not releases)
- To access your PDF: Go to Actions tab → Click workflow run → Download "generated-pdf" artifact
- Artifacts are retained for 90 days

#### 3️⃣ **Google Colab** (No Installation)
Perfect for quick testing and collaboration:
- Click the Colab badge above
- Upload your manuscript files
- Run the notebook cells
- Download your PDF

=======
## Cross-references  
@fig:label @sfig:label @table:label @stable:label @eq:label @snote:label


## Citations
@citation or [@cite1;@cite2] for multiple citations

## Figures with attributes and captions
![](FIGURES/my_plot.py)
{#fig:results width="80%"} **Figure caption here**

## Page control
<newpage> <clearpage> <!-- comments -->
```

## Documentation

### Essential Guides
- **[Google Colab Tutorial](docs/tutorials/google_colab.md)** – Browser-based PDF generation (no installation required)
- **[GitHub Actions Tutorial](docs/tutorials/github_actions.md)** – Automated PDF generation and team workflows
- **[GitHub Actions Guide](docs/github-actions-guide.md)** – Complete cloud PDF generation tutorial
- **[User Guide](docs/user_guide.md)** – Comprehensive usage instructions and troubleshooting
- **[Architecture Overview](docs/architecture.md)** – System design and technical details

### Platform-Specific Setup
- **[Windows/macOS/Linux Setup](docs/platforms/LOCAL_DEVELOPMENT.md)** – Complete installation guides for all platforms

### Reference Documentation
- **[API Reference](docs/api/README.md)** – Python API documentation

### Quick Reference
| Task | Command | Documentation |
|------|---------|---------------|
| Generate PDF | `make pdf` | [User Guide](docs/user_guide.md) |
| Cloud PDF Generation | Actions → "Run workflow" | [GitHub Actions Guide](docs/github-actions-guide.md) |
| Custom Manuscript | `make pdf MANUSCRIPT_PATH=MY_PAPER` | [User Guide](docs/user_guide.md) |
| Force Figure Regeneration | `make pdf FORCE_FIGURES=true` | [User Guide](docs/user_guide.md) |

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
├── src/                    # RXiv-Maker source code
└── docs/                   # Documentation
```

<details>
<summary><strong>💡 Advanced Features</strong></summary>

### Multiple Manuscripts
```bash
# Work with different manuscript directories
make pdf MANUSCRIPT_PATH=PROJECT_A
make pdf MANUSCRIPT_PATH=PROJECT_B
```

### Custom Templates
```bash
# Add custom style files
cp my_style.sty src/tex/style/
# Reference in 00_CONFIG.yml
```

### Automated Workflows
- **GitHub Actions**: Cloud-based PDF generation with caching
- **Pre-commit Hooks**: Automated formatting and validation
- **Continuous Integration**: Automated testing and quality checks

</details>

<details>
<summary><strong>🔧 Troubleshooting</strong></summary>

### Common Issues
- **LaTeX not found**: Install LaTeX - [Windows/macOS/Linux setup](docs/platforms/LOCAL_DEVELOPMENT.md)
- **Python import errors**: Run `make setup` to install dependencies
- **Figure generation fails**: Check Python scripts and data files
- **GitHub Actions fails**: Review workflow logs and manuscript structure

### Debug Commands
```bash
# Verbose output
make pdf VERBOSE=true

# Check logs
cat output/MANUSCRIPT.log

# Test specific manuscript
make pdf MANUSCRIPT_PATH=EXAMPLE_MANUSCRIPT
```

### Getting Help
- [GitHub Issues](https://github.com/henriqueslab/rxiv-maker/issues)
- [Discussions](https://github.com/henriqueslab/rxiv-maker/discussions)
- [Documentation](docs/)

</details>

## Contributing

We welcome contributions! Check out our [contributing guidelines](CONTRIBUTING.md) and help improve RXiv-Maker.

```bash
# Development setup
git clone https://github.com/henriqueslab/rxiv-maker.git
pip install -e ".[dev]"
pre-commit install
```

## Acknowledgments

We extend our gratitude to the scientific computing community, especially the matplotlib/seaborn communities for plotting tools, the LaTeX Project for professional typesetting, and Mermaid for accessible diagram generation.

## License

MIT License - see [LICENSE](LICENSE) for details. Use it, modify it, share it freely.

---


**© 2024 Jacquemet and Henriques Labs | RXiv-Maker**  
*"Because science is hard enough without fighting with LaTeX."*