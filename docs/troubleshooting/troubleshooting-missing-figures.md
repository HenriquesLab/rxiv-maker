# Troubleshooting: Missing Figure Files

## Problem: PDF Generation Fails Due to Missing Figure Files

### Symptoms
- `make pdf` fails with validation errors
- Error messages like: "Figure file not found: FIGURES/SFigure__arxiv_growth/SFigure__arxiv_growth.png"
- The validation shows missing figure files (PNG, PDF, SVG) in MANUSCRIPT/FIGURES/ subdirectories

### Root Cause
The repository tracks generated figure files alongside their generation scripts (Python, R, Mermaid). If these figure files are accidentally deleted (e.g., by `make clean`, manual deletion, or git operations), the build process will fail because the LaTeX compilation expects these files to exist.

## ✅ Automatic Solution (Recommended)

**As of the latest version, `make pdf` automatically detects and runs all figure generation scripts!**

Simply run:
```bash
make pdf
```

The build system will:
1. **Auto-detect missing figures** - Check if output files exist for each generation script
2. **Execute figure generation scripts** - Automatically run `SFigure__arxiv_growth.py`, `SFigure__preprint_trends.R`, Mermaid diagrams, etc.
3. **Generate missing files** - Create PNG, PDF, and SVG versions as appropriate
4. **Continue with PDF build** - Proceed with LaTeX compilation

### Manual Solution (If Needed)
If you need to regenerate figures manually:

```bash
# Navigate to the FIGURES directory
cd MANUSCRIPT/FIGURES

# Activate the virtual environment
source ../../.venv/bin/activate

# Run the figure generation scripts
python SFigure__arxiv_growth.py
Rscript SFigure__preprint_trends.R

# Generate Mermaid diagrams (automatically handled by rxiv)
# Mermaid diagrams are now generated automatically via mermaid.ink API

# Return to project root and test the build
cd ../..
make pdf
```

### Advanced Figure Generation
For more control, you can use the dedicated figure generation command:

```bash
# Generate all figures automatically (Mermaid + Python)
source .venv/bin/activate
rxiv figures --figures-dir MANUSCRIPT/FIGURES --verbose

# Force regenerate all figures even if they exist
make pdf FORCE_FIGURES=true
```

### How It Works
The enhanced build system automatically:
- **Detects figure generation scripts** (`.py`, `.R`, `.mmd` files) in the FIGURES directory
- **Checks for corresponding outputs** (PNG, PDF, and SVG files in subdirectories)
- **Runs missing scripts** using the project's Python environment and R installation
- **Handles multiple formats**: Python scripts, R scripts, and Mermaid diagrams

### Prevention
- The `make clean` command removes generated figures, but `make pdf` will automatically regenerate them
- When cloning the repository, missing figures will be auto-generated on first build
- The build process is now robust against missing figure files

### Why Generated Files Are Still Tracked
Even with automatic generation, generated figure files (PNG, PDF, SVG) remain tracked in git because:
- They ensure reproducible builds across different environments
- Not all users have Python/R dependencies needed for figure generation
- They provide immediate availability without requiring script execution
- They serve as fallbacks when figure generation environments differ
- They guarantee consistent output across different versions of plotting libraries