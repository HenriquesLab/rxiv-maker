# Conda/Mamba Installation Guide

This guide covers installing and using rxiv-maker in conda and mamba environments, including Anaconda, Miniconda, and Mambaforge distributions.

## Quick Start

```bash
# Install rxiv-maker in your conda environment
pip install rxiv-maker

# Verify conda environment detection
rxiv version --detailed

# Optional: Install additional dependencies via conda
conda install -c conda-forge nodejs r-base
```

## Conda Environment Detection

Rxiv-maker automatically detects conda/mamba environments and adapts its behavior accordingly:

- **Environment Detection**: Automatically detects if running in a conda or mamba environment
- **Python Path Resolution**: Uses the correct Python interpreter from your conda environment
- **Package Installation**: Prefers conda packages when available, falls back to pip
- **Dependency Management**: Validates conda-specific installations

## Installation Methods

### Method 1: Conda Environment + pip (Recommended)

This is the most reliable approach for conda users:

```bash
# Create and activate environment
conda create -n rxiv-maker python=3.11
conda activate rxiv-maker

# Install scientific dependencies via conda (faster, better compatibility)
conda install -c conda-forge numpy matplotlib pandas seaborn nodejs r-base

# Install rxiv-maker via pip (latest version)
pip install rxiv-maker

# Verify installation
rxiv version --detailed
```

### Method 2: Pure pip in Conda Environment

If you prefer using pip for everything:

```bash
# Create and activate environment
conda create -n rxiv-maker python=3.11
conda activate rxiv-maker

# Install everything via pip
pip install rxiv-maker

# Verify installation
rxiv version --detailed
```

### Method 3: Environment with Dependencies

Create an environment file for reproducible installations:

```yaml
# environment.yml
name: rxiv-maker
channels:
  - conda-forge
  - defaults
dependencies:
  - python>=3.11
  - numpy>=1.24.0
  - matplotlib>=3.7.0
  - pandas>=2.0.0
  - seaborn>=0.12.0
  - nodejs  # For mermaid diagrams
  - r-base  # For R-based figures
  - pip
  - pip:
    - rxiv-maker
```

Then install:

```bash
conda env create -f environment.yml
conda activate rxiv-maker
```

## Conda vs Mamba

Both conda and mamba are fully supported:

| Feature | Conda | Mamba |
|---------|-------|--------|
| Speed | Slower | Faster |
| Compatibility | Universal | Drop-in replacement |
| rxiv-maker Support | ✅ Full | ✅ Full |
| Recommendation | For stability | For speed |

### Installing Mamba

If you want faster package installation:

```bash
# Install mamba in base environment
conda install -n base -c conda-forge mamba

# Use mamba instead of conda
mamba create -n rxiv-maker python=3.11
mamba activate rxiv-maker
mamba install -c conda-forge numpy matplotlib nodejs r-base
pip install rxiv-maker
```

## Conda-Specific Features

### Automatic Environment Detection

```python
# rxiv-maker automatically detects your environment
from rxiv_maker.utils.platform import platform_detector

print(f"In conda environment: {platform_detector.is_in_conda_env()}")
print(f"Environment name: {platform_detector.get_conda_env_name()}")
print(f"Python command: {platform_detector.python_cmd}")
```

### Conda Package Preferences

When rxiv-maker detects a conda environment, it will:

1. **Use conda python**: Automatically uses the conda environment's Python interpreter
2. **Prefer conda packages**: Uses conda for R and Node.js when available  
3. **Smart installation**: Falls back to pip for packages not available in conda
4. **Environment validation**: Checks that conda environment is properly configured

## Common Workflow

### 1. Environment Setup

```bash
# Create dedicated environment
conda create -n my-paper python=3.11
conda activate my-paper

# Install scientific stack via conda (recommended)
conda install -c conda-forge numpy matplotlib pandas seaborn

# Install rxiv-maker
pip install rxiv-maker
```

### 2. Project Initialization

```bash
# Initialize new manuscript
rxiv init my-paper/

# Navigate to project
cd my-paper/
```

### 3. Generate PDF

```bash
# Generate PDF
rxiv pdf
```

## Troubleshooting Conda Issues

### Problem: "conda not detected"

**Symptoms:**
```bash
rxiv version --detailed
# Shows: Conda/Mamba: ❌ Not found
```

**Solutions:**
```bash
# Ensure conda is in PATH
which conda  # Should show conda location

# Activate environment properly
conda activate your-environment

# Check environment variables
echo $CONDA_DEFAULT_ENV
echo $CONDA_PREFIX
```

### Problem: "Wrong Python interpreter"

**Symptoms:**
- rxiv-maker uses system Python instead of conda Python

**Solutions:**
```bash
# Check which Python is being used
which python
python --version

# Ensure conda environment is activated
conda activate your-environment

# Reinstall rxiv-maker if needed
pip uninstall rxiv-maker
pip install rxiv-maker
```

### Problem: "Package conflicts"

**Symptoms:**
- Installation fails due to dependency conflicts

**Solutions:**
```bash
# Create clean environment
conda create -n rxiv-clean python=3.11
conda activate rxiv-clean

# Install scientific packages first
conda install -c conda-forge numpy matplotlib pandas

# Then install rxiv-maker
pip install rxiv-maker

# Alternative: Use mamba for better dependency resolution
mamba install -c conda-forge numpy matplotlib pandas
pip install rxiv-maker
```

### Problem: "LaTeX not found in conda"

**Note:** Conda's LaTeX packages are limited. Recommended approaches:

```bash
# Option 1: System LaTeX + conda Python environment
# Install LaTeX via system package manager
sudo apt install texlive-full  # Ubuntu/Debian
brew install mactex-no-gui     # macOS
choco install miktex          # Windows

# Use conda for Python environment
conda activate rxiv-maker
rxiv pdf

# Option 2: Use containerized version (no local LaTeX needed)
# See docker-rxiv-maker repository
```

### Problem: "Figure generation fails"

**For R-based figures:**
```bash
# Install R via conda
conda install -c conda-forge r-base

# Verify R installation
which R
R --version
```

**For Node.js/mermaid figures:**
```bash
# Install Node.js via conda
conda install -c conda-forge nodejs

# Verify installation
which node
node --version
```

## Advanced Configuration

### Environment Variables

Set these in your conda environment:

```bash
# In ~/.condarc or environment
RXIV_ENGINE=local  # or docker
RXIV_DEFAULT_PYTHON=conda  # prefer conda python
```

### Conda Environment Activation Scripts

Add automatic configuration when activating:

```bash
# Create activation script
mkdir -p $CONDA_PREFIX/etc/conda/activate.d
cat > $CONDA_PREFIX/etc/conda/activate.d/rxiv-maker.sh << 'EOF'
export RXIV_ENGINE=local
export PYTHONPATH=$CONDA_PREFIX/lib/python3.11/site-packages:$PYTHONPATH
EOF
```

## Integration with Existing Conda Workflows

### Jupyter Notebooks

```bash
# Install jupyter in same environment
conda install jupyter

# Use rxiv-maker from notebooks
jupyter notebook
```

### CI/CD with Conda

```yaml
# .github/workflows/conda-test.yml
- name: Setup conda
  uses: conda-incubator/setup-miniconda@v3
  with:
    python-version: 3.11
    activate-environment: test-env
    
- name: Install dependencies
  shell: bash -l {0}
  run: |
    conda install -c conda-forge numpy matplotlib
    pip install rxiv-maker
    
- name: Test manuscript build
  shell: bash -l {0}
  run: |
    rxiv init test-paper
    cd test-paper && rxiv pdf
```

## Performance Tips

1. **Use mamba**: 5-10x faster than conda for package installation
2. **Conda-forge first**: Install scientific packages via conda, rxiv-maker via pip
3. **Minimal environments**: Only install packages you need
4. **Cache environments**: Reuse environments across projects when possible

## Best Practices

1. **Dedicated environments**: Create separate environments for different projects
2. **Environment files**: Use `environment.yml` for reproducible setups
3. **Version pinning**: Pin critical package versions for stability
4. **Documentation**: Document environment setup in your manuscript repository

## Getting Help

- **Check environment**: `rxiv version --detailed`
- **Test installation**: `rxiv init test-project`
- **Environment info**: `conda info` and `conda list`
- **Issues**: Report conda-specific issues with environment details

## See Also

- [General Installation Guide](../getting-started/installation.md)
- [Docker Guide (deprecated)](../development/docker-engine-mode.md)
- [Troubleshooting Guide](../troubleshooting/troubleshooting-missing-figures.md)
- [Platform-specific guides](../platforms/)