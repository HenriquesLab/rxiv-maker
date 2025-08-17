[![DOI](https://img.shields.io/badge/DOI-10.48550%2FarXiv.2508.00836-blue)](https://doi.org/10.48550/arXiv.2508.00836)
[![License](https://img.shields.io/github/license/henriqueslab/rxiv-maker?color=Green)](https://github.com/henriqueslab/rxiv-maker/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/henriqueslab/rxiv-maker?style=social)](https://github.com/HenriquesLab/rxiv-maker/stargazers)

# Rxiv-Maker

<img src="src/logo/logo-rxiv-maker.svg" align="right" width="200" style="margin-left: 20px;"/>

Rxiv-Maker transforms scientific writing by converting Markdown manuscripts into publication-ready PDFs with automated figure generation, professional LaTeX typesetting, and zero LaTeX expertise required.

**Key Features:** Scientific cross-references, automated Python/R figures, citation management, Docker support, and modern CLI with rich output.

## 🚀 Getting Started

### Quick Install
```bash
pip install rxiv-maker
rxiv init my-paper
cd my-paper
rxiv pdf
```

### Alternative Methods

**🐳 Docker** (No local dependencies)
```bash
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker
rxiv pdf --engine docker
```

**🌐 Google Colab** (Browser-based)  
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HenriquesLab/rxiv-maker/blob/main/notebooks/rxiv_maker_colab.ipynb)

## Essential Commands

```bash
rxiv pdf                            # Generate PDF
rxiv validate                       # Check manuscript
rxiv clean                          # Clean output files
rxiv arxiv                          # Prepare arXiv submission
```

## Documentation

📚 **[Progressive Learning Path](docs/quick-start/)** - 5min → 15min → Daily workflows

📖 **[CLI Reference](docs/reference/cli-commands.md)** - Complete command documentation  

🔧 **[Troubleshooting](docs/troubleshooting/common-issues.md)** - Common issues and solutions

## Contributing

```bash
git clone https://github.com/henriqueslab/rxiv-maker.git
pip install -e ".[dev]" && pre-commit install
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Citation

If you use Rxiv-Maker in your research, please cite:

```bibtex
@misc{saraiva_2025_rxivmaker,
      title={Rxiv-Maker: an automated template engine for streamlined scientific publications}, 
      author={Bruno M. Saraiva and Guillaume Jaquemet and Ricardo Henriques},
      year={2025},
      eprint={2508.00836},
      archivePrefix={arXiv},
      url={https://arxiv.org/abs/2508.00836}, 
}
```

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**© 2025 Jacquemet and Henriques Labs | Rxiv-Maker**  
*"Because science is hard enough without fighting with LaTeX."*
