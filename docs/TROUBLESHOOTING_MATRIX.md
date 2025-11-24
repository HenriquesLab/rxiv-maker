# Troubleshooting Matrix

Comprehensive troubleshooting guide for rxiv-maker across all setup methods and platforms.

## 📑 Table of Contents

- [Installation Issues](#installation-issues)
- [PDF Generation Problems](#pdf-generation-problems)
- [Figure Generation Failures](#figure-generation-failures)
- [Citation and Bibliography Issues](#citation-and-bibliography-issues)
- [Platform-Specific Issues](#platform-specific-issues)
- [Integration Problems](#integration-problems)
- [Performance Issues](#performance-issues)

## 🔧 Installation Issues

### "command not found: rxiv"

**Symptom**: Shell cannot find `rxiv` command after installation

**Causes & Solutions by Installation Method**:

| Method | Cause | Solution |
|--------|-------|----------|
| **pipx** | Not in PATH | `pipx ensurepath` then restart shell |
| **pip** | System vs user install | Use `python -m rxiv_maker` instead or reinstall with `--user` flag |
| **Homebrew** | Homebrew not in PATH | Add `/opt/homebrew/bin` (M1/M2) or `/usr/local/bin` (Intel) to PATH |
| **uv** | Tool not in PATH | `uv tool update-shell` then restart shell |

**Quick Test**:
```bash
# Find where rxiv is installed
which rxiv  # macOS/Linux
where rxiv  # Windows

# Try full path
python -m rxiv_maker --version
```

### "rxiv: No module named 'rxiv_maker'"

**Symptom**: Python cannot find rxiv-maker module

**Solutions**:
1. **Wrong Python environment**:
   ```bash
   # Check Python version
   python --version  # Must be 3.11+

   # Reinstall in correct environment
   pip install --force-reinstall rxiv-maker
   ```

2. **Virtual environment not activated**:
   ```bash
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate     # Windows
   ```

3. **Multiple Python installations**:
   ```bash
   # Use specific Python
   python3.11 -m pip install rxiv-maker
   python3.11 -m rxiv_maker --version
   ```

### "LaTeX not found" or "pdflatex: command not found"

**Symptom**: LaTeX executables not available

**Platform-Specific Solutions**:

| Platform | Solution |
|----------|----------|
| **macOS** | `brew install texlive` or install MacTeX from https://tug.org/mactex/ |
| **Ubuntu/Debian** | `sudo apt-get install texlive-full` |
| **Fedora/RHEL** | `sudo dnf install texlive-scheme-full` |
| **Windows** | Install MiKTeX from https://miktex.org or TeX Live |

**Alternative**: Use Docker (no LaTeX installation needed):
```bash
docker run -v $(pwd):/workspace henriqueslab/rxiv-maker-base:latest rxiv pdf .
```

**Verify Installation**:
```bash
rxiv check-installation
```

## 📄 PDF Generation Problems

### "LaTeX Error: File not found"

**Symptom**: LaTeX cannot find bibliography, figures, or other files

**Common Causes**:

1. **Working directory incorrect**:
   ```bash
   # Must run from project root or specify path
   rxiv pdf MANUSCRIPT/

   # Or cd into manuscript directory
   cd MANUSCRIPT && rxiv pdf .
   ```

2. **Missing files**:
   ```bash
   # Validate manuscript structure
   rxiv validate MANUSCRIPT/
   ```

3. **Case-sensitive paths** (especially on macOS/Linux):
   ```bash
   # These are different!
   figures/plot.png  # Correct
   Figures/Plot.png  # Won't work
   ```

### "Undefined control sequence" or LaTeX Syntax Errors

**Symptom**: LaTeX compilation fails with cryptic errors

**Diagnosis Steps**:
1. Check recent changes to Markdown files
2. Look for unescaped special characters: `_`, `%`, `&`, `#`, `$`
3. Validate mathematical expressions

**Solutions**:

| Issue | Fix |
|-------|-----|
| Bare underscore | Use `\_` or wrap in math mode `$x_1$` |
| Percent sign | Use `\%` |
| Dollar sign | Use `\$` or `$$` for math |
| Ampersand | Use `\&` |
| Hash/pound | Use `\#` |

**Test LaTeX directly** (advanced):
```bash
cd MANUSCRIPT/output
pdflatex article.tex
# Read error messages for specific line numbers
```

### "Bibliography not generated" or Empty References

**Symptom**: Reference section is missing or citations show as `[?]`

**Solutions**:

1. **Check BibTeX file**:
   ```bash
   # Validate BibTeX syntax
   cat MANUSCRIPT/03_REFERENCES.bib
   ```

2. **Re-run compilation**:
   ```bash
   # LaTeX requires multiple passes for references
   rxiv pdf MANUSCRIPT/
   ```

3. **Fix bibliography entries**:
   ```bash
   # Auto-fix common issues
   rxiv fix-bibliography MANUSCRIPT/
   ```

4. **Verify citations in text**:
   - Use `@citationkey` or `[@key1; @key2]` format
   - Ensure citation keys match those in `03_REFERENCES.bib`

## 🎨 Figure Generation Failures

### "Figure script failed to execute"

**Symptom**: Python or R figure scripts crash during generation

**Debug Process**:

1. **Test script manually**:
   ```bash
   cd MANUSCRIPT/FIGURES
   python Figure_01.py
   # Check for errors
   ```

2. **Check dependencies**:
   ```bash
   # Install missing packages
   pip install matplotlib seaborn pandas numpy scipy
   ```

3. **Verify data files**:
   ```bash
   ls -la MANUSCRIPT/FIGURES/DATA/
   # Ensure all required data files exist
   ```

4. **Check script output location**:
   - Scripts must save to current directory
   - Use relative paths: `plt.savefig('Figure_01.png')`

### "Module not found" in Figure Scripts

**Symptom**: Python figure scripts can't import libraries

**Solutions**:

1. **Install in correct environment**:
   ```bash
   # If using virtual environment
   source .venv/bin/activate
   pip install matplotlib seaborn
   ```

2. **Use requirements file**:
   ```bash
   # If manuscript has requirements.txt
   pip install -r MANUSCRIPT/requirements.txt
   ```

3. **System vs user packages**:
   ```bash
   # Install user-wide
   pip install --user matplotlib seaborn
   ```

### Mermaid Diagrams Not Generating

**Symptom**: `.mmd` files not converted to PDFs

**Requirements**:
- Node.js and npm installed
- `@mermaid-js/mermaid-cli` package

**Solutions**:
```bash
# Install mermaid-cli globally
npm install -g @mermaid-js/mermaid-cli

# Or use npx (no installation)
npx -p @mermaid-js/mermaid-cli mmdc --version

# Test mermaid file
cd MANUSCRIPT/FIGURES
mmdc -i Figure_diagram.mmd -o Figure_diagram.pdf
```

## 📚 Citation and Bibliography Issues

### Citations Showing as [?] in PDF

**Symptom**: Citations not resolving to numbers or author names

**Checklist**:
- [ ] Citation key exists in `03_REFERENCES.bib`
- [ ] Citation format correct: `@key` or `[@key1; @key2]`
- [ ] BibTeX file has valid syntax
- [ ] Multiple compilation passes completed

**Fix**:
```bash
# Clean and rebuild
rxiv clean MANUSCRIPT/
rxiv pdf MANUSCRIPT/
```

### "Invalid BibTeX entry" Errors

**Symptom**: Bibliography compilation fails

**Common Issues**:

1. **Missing required fields**:
   ```bibtex
   @article{smith2024,
     title = {Paper Title},
     author = {Smith, John},
     journal = {Journal Name},  % Required!
     year = {2024}               % Required!
   }
   ```

2. **Unescaped special characters**:
   ```bibtex
   title = {Understanding \& Implementing...}  % Escape &
   ```

3. **Unmatched braces**:
   ```bash
   # Use validation tool
   rxiv fix-bibliography MANUSCRIPT/
   ```

### DOI Resolution Not Working

**Symptom**: `rxiv add-bibliography` fails to fetch DOI metadata

**Causes & Solutions**:

| Issue | Solution |
|-------|----------|
| Invalid DOI format | Verify DOI at https://doi.org/ |
| Network issues | Check internet connection, try again |
| API rate limiting | Wait a few minutes, retry |
| CrossRef/DataCite down | Check service status, try later |

## 🖥️ Platform-Specific Issues

### macOS: Permission Denied Errors

**Symptom**: Cannot write to output directory

**Solutions**:
```bash
# Fix permissions
chmod +w MANUSCRIPT/output

# Or recreate output directory
rm -rf MANUSCRIPT/output
mkdir MANUSCRIPT/output
```

### Windows: Path Too Long Errors

**Symptom**: File paths exceed Windows 260-character limit

**Solutions**:
1. **Enable long paths** (Windows 10+):
   - Run as Administrator: `reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1`
   - Restart computer

2. **Use shorter paths**:
   ```bash
   # Instead of C:\Users\Username\Documents\Projects\...
   # Use C:\Projects\manuscript\
   ```

3. **Use WSL** (Windows Subsystem for Linux):
   ```bash
   wsl
   # Follow Linux installation instructions
   ```

### Linux: Missing System Dependencies

**Symptom**: Various compilation errors on Linux

**Install build essentials**:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install build-essential python3-dev

# Fedora/RHEL
sudo dnf groupinstall "Development Tools"
sudo dnf install python3-devel
```

## 🔗 Integration Problems

### VS Code Extension Not Working

**Symptom**: Syntax highlighting or commands not available

**Solutions**:

1. **Check file recognition**:
   - Files must be `.rxm`, `01_MAIN.md`, or `02_SUPPLEMENTARY_INFO.md`
   - Open Command Palette → "Change Language Mode" → "Rxiv Markdown"

2. **Reload extension**:
   - Command Palette → "Reload Window"

3. **Check extension version**:
   - Should match rxiv-maker version (major.minor)
   - Update if needed

4. **Verify rxiv-maker installed**:
   ```bash
   rxiv --version
   ```

### GitHub Actions Failing

**Symptom**: PDF generation works locally but fails in CI

**Common Causes**:

1. **Timeout issues**:
   - Actions have 6-hour default limit
   - Large figures may take longer in CI

2. **Missing secrets/variables**:
   - Check repository secrets are set
   - Verify GitHub token permissions

3. **Dependency mismatch**:
   - Pin versions in requirements.txt
   - Use same Python version locally and in CI

**Debug Steps**:
```yaml
# Add debug step to workflow
- name: Debug Environment
  run: |
    rxiv --version
    rxiv check-installation
    ls -la MANUSCRIPT/
```

### Docker Container Issues

**Symptom**: Container fails to build or run

**Solutions**:

1. **Pull latest image**:
   ```bash
   docker pull henriqueslab/rxiv-maker-base:latest
   ```

2. **Check volume mounts**:
   ```bash
   # Correct mounting
   docker run -v $(pwd):/workspace henriqueslab/rxiv-maker-base:latest

   # Windows (PowerShell)
   docker run -v ${PWD}:/workspace henriqueslab/rxiv-maker-base:latest
   ```

3. **Permissions issues**:
   ```bash
   # Run with user ID mapping
   docker run --user $(id -u):$(id -g) -v $(pwd):/workspace henriqueslab/rxiv-maker-base:latest
   ```

## ⚡ Performance Issues

### Slow PDF Generation

**Symptom**: Builds take excessive time

**Optimization Steps**:

1. **Use figure caching** (default behavior):
   ```bash
   # Only regenerate changed figures
   rxiv pdf MANUSCRIPT/

   # Force regenerate all (slower)
   rxiv pdf MANUSCRIPT/ --force-figures
   ```

2. **Optimize figures**:
   - Reduce DPI for non-print versions: `plt.savefig('fig.png', dpi=150)`
   - Use PNG for photos, PDF for vector graphics
   - Compress large images before including

3. **Reduce LaTeX packages**:
   - Review `00_CONFIG.yml` for unnecessary packages
   - Remove unused custom LaTeX in manuscript

4. **Use faster LaTeX engine**:
   - Consider LuaLaTeX for complex documents (if supported)

### High Memory Usage

**Symptom**: System runs out of memory during build

**Solutions**:

1. **Process figures separately**:
   ```bash
   # Generate figures first
   rxiv figures MANUSCRIPT/

   # Then compile PDF
   rxiv pdf MANUSCRIPT/
   ```

2. **Reduce figure complexity**:
   - Simplify plots with many data points
   - Use sampling for dense datasets
   - Reduce subplot count per figure

3. **Close other applications**:
   - Free up system RAM
   - Use swap/pagefile if available

## 🆘 Getting More Help

### Community Resources

- **GitHub Discussions**: https://github.com/HenriquesLab/rxiv-maker/discussions
- **GitHub Issues**: Report bugs at https://github.com/HenriquesLab/rxiv-maker/issues
- **Documentation**: https://rxiv-maker.henriqueslab.org

### Reporting Issues

When reporting problems, include:

1. **Environment**:
   ```bash
   rxiv --version
   python --version
   rxiv check-installation
   ```

2. **Minimal example**: Smallest manuscript that reproduces the issue

3. **Full error output**: Copy complete error messages

4. **What you tried**: Steps already attempted

### Emergency Workarounds

If completely stuck:

1. **Use Google Colab**: No local installation needed
   - https://colab.research.google.com/github/HenriquesLab/rxiv-maker/blob/main/notebooks/rxiv_maker_colab.ipynb

2. **Use Docker**: Bypass local dependencies
   ```bash
   docker run -v $(pwd):/workspace henriqueslab/rxiv-maker-base:latest rxiv pdf .
   ```

3. **Generate LaTeX manually**: Last resort
   ```bash
   rxiv pdf --keep-tex MANUSCRIPT/
   # Edit MANUSCRIPT/output/article.tex manually
   cd MANUSCRIPT/output && pdflatex article.tex
   ```

---

**Last Updated**: November 2025
**Contribute**: Found a solution not listed here? Please submit a PR!
