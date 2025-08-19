[![DOI](https://img.shields.io/badge/DOI-10.48550%2FarXiv.2508.00836-blue)](https://doi.org/10.48550/arXiv.2508.00836)
[![License](https://img.shields.io/github/license/henriqueslab/rxiv-maker?color=Green)](https://github.com/henriqueslab/rxiv-maker/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/henriqueslab/rxiv-maker?style=social)](https://github.com/HenriquesLab/rxiv-maker/stargazers)

# Rxiv-Maker

<img src="src/logo/logo-rxiv-maker.svg" align="right" width="200" style="margin-left: 20px;"/>

Rxiv-Maker transforms scientific writing by converting Markdown manuscripts into publication-ready PDFs with automated figure generation, professional LaTeX typesetting, and zero LaTeX expertise required.

**Key Features:** Scientific cross-references, automated Python/R figures, citation management, Docker support, and modern CLI with rich output.

## 🚀 Getting Started

### 🎯 Quick Install
```bash
pip install rxiv-maker
rxiv check-installation --fix  # Auto-install dependencies
rxiv init my-paper
cd my-paper
rxiv pdf
```

### 📦 Dependencies by Platform

<details>
<summary><strong>🍎 macOS - Homebrew (Recommended)</strong></summary>

**Install dependencies with Homebrew:**
```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install system dependencies
brew install python@3.11 node@20 texlive
brew tap henriqueslab/rxiv-maker
brew install rxiv-maker  # Complete installation with all dependencies

# Verify installation
rxiv check-installation
```

</details>

<details>
<summary><strong>🐧 Linux - Choose Your Method</strong></summary>

**Option A: APT Repository (Ubuntu/Debian - Recommended)**
```bash
sudo apt update
sudo apt install ca-certificates
curl -fsSL https://raw.githubusercontent.com/HenriquesLab/apt-rxiv-maker/apt-repo/pubkey.gpg | sudo gpg --dearmor -o /usr/share/keyrings/rxiv-maker.gpg
echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/rxiv-maker.gpg] https://raw.githubusercontent.com/HenriquesLab/apt-rxiv-maker/apt-repo stable main' | sudo tee /etc/apt/sources.list.d/rxiv-maker.list
sudo apt update
sudo apt install rxiv-maker
```

**Option B: Homebrew on Linux (All Distributions)**
```bash
# Install Homebrew on Linux
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install rxiv-maker with all dependencies
brew tap henriqueslab/rxiv-maker  
brew install rxiv-maker

# Verify installation
rxiv check-installation
```

</details>

<details>
<summary><strong>🪟 Windows - WSL2 (Recommended)</strong></summary>

**Setup WSL2 with Ubuntu:**
```powershell
# Windows PowerShell as Administrator
wsl --install -d Ubuntu-22.04
# Restart computer when prompted
```

**Inside WSL2 Ubuntu terminal:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Option A: Use APT repository
sudo apt install ca-certificates
curl -fsSL https://raw.githubusercontent.com/HenriquesLab/apt-rxiv-maker/apt-repo/pubkey.gpg | sudo gpg --dearmor -o /usr/share/keyrings/rxiv-maker.gpg
echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/rxiv-maker.gpg] https://raw.githubusercontent.com/HenriquesLab/apt-rxiv-maker/apt-repo stable main' | sudo tee /etc/apt/sources.list.d/rxiv-maker.list
sudo apt update
sudo apt install rxiv-maker

# Option B: Use pip with dependencies
sudo apt install -y python3.11 python3-pip texlive-latex-recommended
pip install rxiv-maker

# Verify installation
rxiv check-installation
```

</details>

### ✅ Verification
```bash
# Check installation status
rxiv check-installation

# Create test project
rxiv init test-paper
cd test-paper

# Generate your first PDF
rxiv pdf
```

### 🌐 Alternative Methods

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
