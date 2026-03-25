[![DOI](https://img.shields.io/badge/DOI-10.48550%2FarXiv.2508.00836-blue)](https://doi.org/10.48550/arXiv.2508.00836)
[![License](https://img.shields.io/github/license/henriqueslab/rxiv-maker?color=Green)](https://github.com/henriqueslab/rxiv-maker/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/henriqueslab/rxiv-maker?style=social)](https://github.com/HenriquesLab/rxiv-maker/stargazers)

# Rxiv-Maker

<img src="https://raw.githubusercontent.com/HenriquesLab/rxiv-maker/main/src/logo/logo-rxiv-maker.svg" align="right" width="200" style="margin-left: 20px;"/>

Rxiv-Maker converts enhanced Markdown into professional PDFs with automated figure generation, citation management, and LaTeX typesetting. Write in Markdown, get publication-ready output for arXiv, bioRxiv, and other preprint servers.

## Installation

**macOS** (includes LaTeX automatically):
```bash
brew install henriqueslab/formulas/rxiv-maker
```

**Linux / Windows (WSL)**:
```bash
pipx install rxiv-maker    # or: uv tool install rxiv-maker
```

Verify setup:
```bash
rxiv check-installation
```

LaTeX is required. See the [installation guide](https://rxiv-maker.henriqueslab.org/getting-started/installation/) for platform-specific LaTeX instructions.

## Quick Start

```bash
rxiv init my-paper
cd my-paper
rxiv pdf
```

To explore a complete working example:
```bash
rxiv get-rxiv-preprint
cd manuscript-rxiv-maker/MANUSCRIPT
rxiv pdf
```

## Features

- **Enhanced Markdown** - Scientific cross-references (`@fig:plot`, `@eq:formula`), auto-numbered figures/tables/equations, LaTeX math
- **Automated figures** - Python and R scripts executed during PDF generation, with intelligent caching
- **Executable code blocks** - Jupyter-like `{{py:exec}}` and `{{py:get variable}}` for live data in manuscripts
- **Citation management** - BibTeX with `[@citation]` syntax, multiple styles, inline DOI resolution
- **Dual output** - PDF and DOCX from the same source
- **arXiv/bioRxiv submission** - Generate submission packages automatically
- **Track changes** - Visual diff between manuscript versions
- **VS Code extension** - Syntax highlighting, citation autocompletion, one-click builds

## Documentation

**[rxiv-maker.henriqueslab.org](https://rxiv-maker.henriqueslab.org)** - Installation, guides, CLI reference, troubleshooting.

For contributors: **[CONTRIBUTING.md](CONTRIBUTING.md)**

## Ecosystem

| Repository | Purpose |
|------------|---------|
| [rxiv-maker](https://github.com/HenriquesLab/rxiv-maker) | Core CLI tool |
| [docker-rxiv-maker](https://github.com/HenriquesLab/docker-rxiv-maker) | Pre-configured container with LaTeX |
| [manuscript-rxiv-maker](https://github.com/HenriquesLab/manuscript-rxiv-maker) | Complete example (arXiv:2508.00836) |
| [vscode-rxiv-maker](https://marketplace.visualstudio.com/items?itemName=HenriquesLab.rxiv-maker) | VS Code extension |

## Publications

See the [publications showcase](https://rxiv-maker.henriqueslab.org/examples/showcase/) for preprints made with Rxiv-Maker.

Using it for your research? [Let us know](https://github.com/HenriquesLab/rxiv-maker/issues/new?template=publication_submission.yml).

## Community

- [GitHub Discussions](https://github.com/henriqueslab/rxiv-maker/discussions) - Questions and tips
- [Issues](https://github.com/henriqueslab/rxiv-maker/issues) - Bug reports and feature requests
- [Google Colab](https://colab.research.google.com/github/HenriquesLab/rxiv-maker/blob/main/notebooks/rxiv_maker_colab.ipynb) - Try without installing

## Citation

```bibtex
@misc{saraiva_2025_rxivmaker,
  title={Rxiv-Maker: an automated template engine for streamlined scientific publications},
  author={Bruno M. Saraiva and Ant\'{o}nio D. Brito and Guillaume Jaquemet and Ricardo Henriques},
  year={2025},
  eprint={2508.00836},
  archivePrefix={arXiv},
  url={https://arxiv.org/abs/2508.00836}
}
```

## License

MIT License - see [LICENSE](LICENSE) for details.
