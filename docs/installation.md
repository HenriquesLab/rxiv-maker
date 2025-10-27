# Installation Guide

> **📖 For complete installation instructions**, see the **[Official Installation Guide](https://rxiv-maker.henriqueslab.org/getting-started/installation/)** on our website.

This file provides developer-specific installation workflows for contributing to rxiv-maker.

---

## 👤 User Installation

**For standard users**, please visit our comprehensive installation guide:

**🔗 [rxiv-maker.henriqueslab.org/getting-started/installation](https://rxiv-maker.henriqueslab.org/getting-started/installation/)**

The website guide includes:
- Platform-specific instructions (macOS, Linux, Windows)
- LaTeX distribution setup
- Troubleshooting common issues
- Verification steps
- Quick start examples

---

## 🛠️ Developer Installation

For contributors and developers working on rxiv-maker itself:

### Quick Developer Setup
```bash
# Clone repository
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Setup pre-commit hooks (mandatory)
pre-commit install

# Verify development setup
rxiv check-installation --detailed
```

### Virtual Environment Setup
```bash
# Create isolated development environment
python -m venv .venv-dev
source .venv-dev/bin/activate  # Linux/macOS
# .venv-dev\Scripts\activate   # Windows

# Install development dependencies
pip install -e ".[dev]"
pre-commit install
```

## 🔧 Development Workflows

### Testing & Contribution Setup
```bash
# Run tests to verify your setup
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/unit/ -v        # Unit tests only
python -m pytest tests/integration/ -v  # Integration tests

# Run linting and formatting
pre-commit run --all-files

# Build documentation locally
mkdocs serve  # If working on website
```

### Advanced Installation Options

#### From Source (Latest Development)
```bash
# Install from main branch
pip install git+https://github.com/henriqueslab/rxiv-maker.git

# Install specific branch or tag
pip install git+https://github.com/henriqueslab/rxiv-maker.git@feature-branch
pip install git+https://github.com/henriqueslab/rxiv-maker.git@v1.2.3
```

#### With Optional Dependencies
```bash
# Full development environment
pip install "rxiv-maker[dev]"

# Documentation building
pip install "rxiv-maker[docs]"

# All optional dependencies
pip install "rxiv-maker[all]"
```

## 🧪 Testing Your Development Setup

After installation, verify everything works:

```bash
# Run development health check
rxiv check-installation --detailed

# Create test manuscript
rxiv init test-manuscript
cd test-manuscript

# Test basic functionality
rxiv validate           # Check manuscript structure
rxiv pdf               # Generate PDF
rxiv clean            # Clean up

# Run project tests (from repo root)
cd .. && python -m pytest tests/unit/ -v
```

## 🐳 Container Development

For containerized development without dependency installation:

**📖 [Container Development Guide →](containers.md)**

## 🌐 Alternative Development Environments

### GitHub Codespaces
Develop rxiv-maker in the cloud:

1. Go to [rxiv-maker repository](https://github.com/HenriquesLab/rxiv-maker)
2. Click "Code" → "Codespaces" → "Create codespace"
3. Wait for environment setup
4. Run `pip install -e ".[dev]"` in terminal

### Google Colab Development
For quick experimentation:

**📖 [Colab Development Notebook →](https://colab.research.google.com/github/HenriquesLab/rxiv-maker/blob/main/notebooks/rxiv_maker_colab.ipynb)**

## 🆘 Developer Support

- **Development Questions**: [GitHub Discussions](https://github.com/henriqueslab/rxiv-maker/discussions)
- **Bug Reports**: [GitHub Issues](https://github.com/henriqueslab/rxiv-maker/issues)
- **Contributing Guide**: [CONTRIBUTING.md](../CONTRIBUTING.md)

## 🔗 Related Resources

- **[User Installation Guide](https://rxiv-maker.henriqueslab.org/getting-started/installation/)** - Standard installation
- **[Container Guide](containers.md)** - Container development

---

*This developer guide focuses on technical setup for contributing to rxiv-maker. For standard user installation, see our [website](https://rxiv-maker.henriqueslab.org/).*