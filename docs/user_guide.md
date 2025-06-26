# Rxiv-Maker User Guide

This guide covers everything from getting started to advanced workflows, practical examples, and troubleshooting.

## Table of Contents
- [Getting Started](#getting-started)
- [Manuscript Validation](#manuscript-validation)
- [Advanced Usage](#advanced-usage)
- [Examples & Cookbook](#examples--cookbook)
- [Troubleshooting & Debugging](#troubleshooting--debugging)
- [Where to Get Help](#where-to-get-help)

---

## Getting Started

For platform-specific setup, see [platforms/LOCAL_DEVELOPMENT.md](platforms/LOCAL_DEVELOPMENT.md).

- Install dependencies and LaTeX as described in the platform guide.
- Build your first PDF:
  ```bash
  make setup
  make validate  # Check for issues first
  make pdf       # Generate PDF
  ```
- Use a different manuscript folder:
  ```bash
  MANUSCRIPT_PATH=MY_ARTICLE make pdf
  ```

---

## Manuscript Validation

Rxiv-Maker includes a comprehensive validation system that checks your manuscript for errors before PDF generation. This helps catch issues early and provides actionable feedback.

### Quick Validation
```bash
# Basic validation check
make validate

# Validate specific manuscript
make validate MANUSCRIPT_PATH=MY_PAPER

# Recommended workflow: validate then build
make validate && make pdf
```

### Detailed Validation
```bash
# Get comprehensive feedback with suggestions
python src/py/scripts/validate_manuscript.py --detailed MANUSCRIPT

# Advanced validation with rich output
python src/py/commands/validate.py MANUSCRIPT --verbose
```

### What Gets Validated

**Content & Structure:**
- Required files (`00_CONFIG.yml`, `01_MAIN.md`, `03_REFERENCES.bib`)
- YAML configuration syntax and required fields
- File readability and basic format checks

**Citations & References:**
- Citation syntax (`@citation`, `[@cite1;@cite2]`)
- Cross-references (`@fig:label`, `@tbl:label`, `@eq:label`)
- Bibliography entries against citations
- Undefined references and unused definitions

**Figures & Math:**
- Figure file existence and accessibility
- Mathematical expression syntax (`$...$`, `$$...$$`)
- LaTeX command validity
- Figure generation script errors

**Build Issues:**
- LaTeX compilation error analysis
- Common error pattern recognition
- User-friendly error explanations

### Understanding Validation Output

**Error Levels:**
- 🔴 **ERROR**: Critical issues preventing PDF generation
- 🟡 **WARNING**: Potential problems or quality issues  
- 🔵 **INFO**: Statistics and informational messages

**Example Output:**
```
ERROR: Citation 'smith2023' not found in bibliography
  File: 01_MAIN.md:42
  Context: > See @smith2023 for details
  Suggestion: Add reference to 03_REFERENCES.bib or check spelling

WARNING: Figure file FIGURES/plot.png not found
  Suggestion: Create the figure or update the path
```

### Integration with Build Process

Validation runs automatically before PDF generation:
```bash
make pdf  # Includes validation step
```

For more detailed validation information, see [Manuscript Validation Guide](validate_manuscript.md).

---

## Advanced Usage

- **Custom Manuscript Paths:**
  ```bash
  MANUSCRIPT_PATH=MY_ARTICLE make pdf
  ```
- **Advanced Figure Generation:**
  - Place Python or Mermaid files in `MANUSCRIPT/FIGURES/`
  - Force regeneration:
    ```bash
    make pdf FORCE_FIGURES=true
    ```
- **Custom LaTeX Templates:**
  - Add `.sty`, `.cls`, or `.tex` files to `src/tex/style/`
  - Reference your custom style in `00_CONFIG.yml`
- **Continuous Integration (CI):**
  - GitHub Actions builds PDFs via manual trigger or git tags
  - See [GitHub Actions Guide](github-actions-guide.md) for step-by-step instructions
  - Customize workflows in `.github/workflows/`
- **Environment Variables:**
  - Use a `.env` file for persistent settings
- **Debugging and Verbose Output:**
  - Use `VERBOSE=true` for detailed logs:
    ```bash
    make pdf VERBOSE=true
    ```
- **Pre-commit Hooks and Linting:**
  - Install hooks: `pre-commit install`
  - Run all checks: `pre-commit run --all-files`

---

## Examples & Cookbook

- **Basic PDF Generation:**
  ```bash
  make validate  # Check for issues first
  make pdf       # Generate PDF
  ```
- **Custom Manuscript Directory:**
  ```bash
  MANUSCRIPT_PATH=MY_PAPER make pdf
  ```
- **Adding Figures:**
  - Place `.py` or `.mmd` files in `MANUSCRIPT/FIGURES/`
  - Reference in Markdown:
    ```markdown
    ![My Plot](FIGURES/my_plot.py){#fig:plot}
    See @fig:plot for details.
    ```
- **Customizing Templates:**
  - Add `.sty` or `.cls` files to `src/tex/style/`
  - Reference in `00_CONFIG.yml`
- **Using Mermaid Diagrams:**
  - Place `.mmd` files in `FIGURES/`
  - Example:
    ```mermaid
    graph TD;
      A-->B;
      B-->C;
    ```
- **Citations and Bibliography:**
  - Add references to `03_REFERENCES.bib`
  - Use `[@cite1;@cite2]` in Markdown
- **CI/CD Automation:**
  - GitHub Actions builds PDFs on manual trigger or tags
  - See [GitHub Actions Guide](github-actions-guide.md) for complete instructions

---

## Troubleshooting & Debugging

- **Validation Errors:**
  - Error: Various validation failures
  - Solution: Run `make validate` to see specific issues and suggestions
  - Debug: Use `python src/py/scripts/validate_manuscript.py --detailed MANUSCRIPT` for comprehensive feedback
- **LaTeX Not Found:**
  - Error: `LaTeX Error: File not found`
  - Solution: Install LaTeX (see [platforms/LOCAL_DEVELOPMENT.md](platforms/LOCAL_DEVELOPMENT.md))
  - Check: Is `pdflatex` in your PATH?
- **Python Import Errors:**
  - Error: `ModuleNotFoundError` or similar
  - Solution: Run `make setup` to install dependencies
  - Check: Is your virtual environment activated?
- **Figure Generation Fails:**
  - Error: Figures not generated or missing in PDF
  - Solution:
    - Check Python scripts in `FIGURES/` for errors
    - Use `make pdf FORCE_FIGURES=true`
    - Check for missing data files
- **Build Fails on GitHub Actions:**
  - Check: Is the manuscript directory path correct?
  - Check: Are all dependencies listed in `pyproject.toml`?
  - Check: Does the manuscript have required files (`00_CONFIG.yml`, `01_MAIN.md`)?
  - Solution: Review workflow logs in Actions tab → Click failed run → Click "build-pdf" job
  - See [GitHub Actions Guide](github-actions-guide.md) for detailed troubleshooting
- **Debugging Tips:**
  - Always start with `make validate` to catch issues early
  - Use `make pdf VERBOSE=true` for more output
  - Check `output/ARTICLE.log` for LaTeX errors
  - Use detailed validation: `python src/py/scripts/validate_manuscript.py --detailed MANUSCRIPT`
  - Use `pytest` for running tests

---

## Where to Get Help
- [GitHub Issues](https://github.com/henriqueslab/rxiv-maker/issues)
- [Discussions](https://github.com/henriqueslab/rxiv-maker/discussions)
- [Contributing Guide](../CONTRIBUTING.md)
