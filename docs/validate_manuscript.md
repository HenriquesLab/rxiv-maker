# Manuscript Validation System

Rxiv-Maker includes a comprehensive validation system that checks your manuscript for errors, missing references, citation issues, and LaTeX compilation problems before generating PDFs. This helps catch issues early and provides actionable feedback.

## Quick Start

```bash
# Basic validation
make validate

# Custom manuscript path
make validate MANUSCRIPT_PATH=MY_PAPER

# Detailed validation with suggestions
python src/py/scripts/validate_manuscript.py --detailed MANUSCRIPT

# Advanced validation options
python src/py/commands/validate.py MANUSCRIPT --verbose --output detailed
```

## Validation Types

### 1. Content Validation
**What it checks:**
- Required files (`00_CONFIG.yml`, `01_MAIN.md`, `03_REFERENCES.bib`)
- Optional files (`02_SUPPLEMENTARY_INFO.md`)
- Directory structure (`FIGURES/`, etc.)
- File readability and basic format validation

**Example issues caught:**
- Missing configuration file
- Empty manuscript content
- Malformed YAML syntax
- Invalid BibTeX entries

### 2. Citation Validation
**What it checks:**
- Citation syntax (`@citation`, `[@cite1;@cite2]`)
- Citation keys against bibliography file
- Undefined citations
- Unused bibliography entries

**Example issues caught:**
```
ERROR: Citation 'smith2023' not found in bibliography
SUGGESTION: Add the reference to 03_REFERENCES.bib or check spelling
```

### 3. Cross-Reference Validation
**What it checks:**
- Figure references (`@fig:label`, `@sfig:label`)
- Table references (`@tbl:label`, `@stable:label`) 
- Equation references (`@eq:label`)
- Supplementary note references (`@snote:label`)
- Label definitions against references

**Example issues caught:**
```
ERROR: Reference @fig:nonexistent used but label not defined
SUGGESTION: Add {#fig:nonexistent} to a figure or check reference spelling
```

### 4. Figure Validation
**What it checks:**
- Figure file existence and accessibility
- Figure syntax and attributes
- Python script validity for generated figures
- Mermaid diagram syntax
- Image format compatibility

**Example issues caught:**
```
ERROR: Figure file FIGURES/missing.png not found
SUGGESTION: Create the figure file or update the figure path
```

### 5. Mathematical Expression Validation
**What it checks:**
- LaTeX math syntax (`$...$`, `$$...$$`)
- Balanced delimiters and braces
- Valid LaTeX commands
- Equation label format
- Math environment syntax

**Example issues caught:**
```
ERROR: Unbalanced braces in math expression: $E = mc^{2$
SUGGESTION: Close the brace: $E = mc^{2}$
```

### 6. Syntax Validation
**What it checks:**
- Markdown syntax compliance
- Special rxiv-maker elements
- Text formatting consistency
- List structure
- Code block syntax
- HTML element processing

**Example issues caught:**
```
WARNING: Unclosed bold formatting detected
SUGGESTION: Ensure all ** bold markers are properly paired
```

### 7. LaTeX Error Analysis
**What it checks:**
- LaTeX compilation log parsing
- Common error pattern recognition
- User-friendly error translation
- Build failure diagnosis

**Example issues caught:**
```
ERROR: LaTeX compilation failed - Unknown command \unknowncommand
SUGGESTION: Check if you need to include a package or fix the command spelling
```

## Usage Options

### Basic Validation (Makefile)
```bash
# Quick validation check
make validate

# Validate specific manuscript
make validate MANUSCRIPT_PATH=PROJECT_A

# Validate before PDF generation (recommended workflow)
make validate && make pdf
```

### Script-based Validation
```bash
# Basic validation
python src/py/scripts/validate_manuscript.py MANUSCRIPT

# Detailed validation with context and suggestions
python src/py/scripts/validate_manuscript.py --detailed MANUSCRIPT

# Quiet mode (errors only)
python src/py/scripts/validate_manuscript.py --quiet MANUSCRIPT

# Verbose mode (all details)
python src/py/scripts/validate_manuscript.py --verbose MANUSCRIPT
```

### Advanced Validation Command
```bash
# Comprehensive validation with rich output
python src/py/commands/validate.py MANUSCRIPT

# Different output formats
python src/py/commands/validate.py MANUSCRIPT --output basic
python src/py/commands/validate.py MANUSCRIPT --output detailed
python src/py/commands/validate.py MANUSCRIPT --output verbose

# Focus on specific validation types
python src/py/commands/validate.py MANUSCRIPT --validators citation,reference
python src/py/commands/validate.py MANUSCRIPT --skip-validators latex
```

## Understanding Validation Output

### Error Levels
- **ERROR** (🔴): Critical issues that will prevent PDF generation
- **WARNING** (🟡): Issues that might cause problems or affect quality
- **INFO** (🔵): Informational messages and statistics

### Output Format
```
ERROR: Short description of the problem
  File: /path/to/file.md:42:15
  Context: > Relevant line of content where error occurred
  Suggestion: Specific action to fix the issue

STATISTICS:
  Citations found: 15 (12 valid, 3 undefined)
  Figures referenced: 8 (7 found, 1 missing)
  Math expressions: 23 (all valid)
```

### Exit Codes
- `0`: Validation passed (no errors, may have warnings)
- `1`: Validation failed (has errors that need fixing)

## Integration with Build Process

### Pre-build Validation
Validation is automatically integrated into the PDF generation process:

```bash
# Validation runs automatically before PDF generation
make pdf

# Manual control over validation
make validate  # Check first
make pdf       # Generate PDF if validation passes
```

### GitHub Actions Integration
The validation system works seamlessly with GitHub Actions:

```yaml
# Validation runs automatically in CI/CD
- name: Validate manuscript
  run: make validate

- name: Generate PDF
  run: make pdf
```

## Common Validation Scenarios

### 1. New Manuscript Setup
```bash
# Check if your new manuscript has proper structure
make validate MANUSCRIPT_PATH=NEW_PROJECT

# Expected output for valid setup:
# ✓ All required files found
# ✓ Configuration valid
# ✓ No citation or reference errors
```

### 2. Citation Issues
```bash
# Check citation problems
python src/py/commands/validate.py MANUSCRIPT --validators citation

# Common fixes:
# - Add missing references to 03_REFERENCES.bib
# - Fix citation key spelling
# - Check citation syntax [@key] vs @key
```

### 3. Figure Problems
```bash
# Check figure-related issues
python src/py/commands/validate.py MANUSCRIPT --validators figure

# Common fixes:
# - Create missing figure files
# - Fix figure paths
# - Update Python scripts for figure generation
```

### 4. LaTeX Compilation Debugging
```bash
# Check LaTeX-specific issues after a failed build
python src/py/commands/validate.py MANUSCRIPT --validators latex

# Common fixes based on log analysis:
# - Fix special character escaping
# - Add missing LaTeX packages
# - Correct mathematical syntax
```

## Validation Architecture

### Modular Validator System
The validation system uses a modular architecture with specialized validators:

- **BaseValidator**: Common validation infrastructure
- **CitationValidator**: Citation syntax and bibliography checking
- **ReferenceValidator**: Cross-reference validation
- **FigureValidator**: Figure file and syntax validation
- **MathValidator**: Mathematical expression validation
- **SyntaxValidator**: General syntax and formatting validation
- **LaTeXErrorParser**: LaTeX compilation error analysis

### Content Protection
The validation system respects the same content protection used in the conversion pipeline:
- Math expressions are protected during validation
- Code blocks are handled specially
- Table content is validated carefully
- Multi-stage restoration maintains content integrity

## Best Practices

### 1. Validate Early and Often
```bash
# Run validation after significant changes
make validate

# Include validation in your development workflow
alias build="make validate && make pdf"
```

### 2. Use Detailed Mode for Debugging
```bash
# Get comprehensive feedback when troubleshooting
python src/py/scripts/validate_manuscript.py --detailed MANUSCRIPT
```

### 3. Fix Errors Before Warnings
- Address ERROR level issues first (prevent build failures)
- Then tackle WARNING level issues (improve quality)
- INFO level messages provide useful statistics

### 4. Leverage Suggestions
Each validation error includes specific suggestions:
```
ERROR: Citation 'smith2023' not found in bibliography
SUGGESTION: Add the reference to 03_REFERENCES.bib or check spelling
```

### 5. Validate in CI/CD
```bash
# In your GitHub Actions or other CI systems
make validate  # Fails fast if there are errors
make pdf       # Only runs if validation passes
```

## Troubleshooting

### Common Issues

#### Validation Script Not Found
```bash
# If you get "command not found" errors
python -m src.py.scripts.validate_manuscript MANUSCRIPT
```

#### Import Errors
```bash
# Ensure you're in the rxiv-maker root directory
cd /path/to/rxiv-maker
python src/py/scripts/validate_manuscript.py MANUSCRIPT
```

#### Permission Issues
```bash
# Check file permissions
ls -la MANUSCRIPT/
chmod 644 MANUSCRIPT/*.md MANUSCRIPT/*.yml MANUSCRIPT/*.bib
```

### Performance Considerations

- Basic validation is fast (< 1 second for typical manuscripts)
- Detailed validation with LaTeX log parsing may take 2-5 seconds
- Figure validation time depends on number of figure files
- Large bibliographies may increase citation validation time

### Custom Validation Rules

The validation system is extensible. You can create custom validators by:

1. Inheriting from `BaseValidator`
2. Implementing the `validate()` method
3. Returning `ValidationResult` with errors/warnings
4. Adding to the validation pipeline

## Integration Examples

### Pre-commit Hook
```bash
# Add to .git/hooks/pre-commit
#!/bin/bash
make validate || {
    echo "Validation failed! Please fix errors before committing."
    exit 1
}
```

### VS Code Task
```json
{
    "label": "Validate Manuscript",
    "type": "shell",
    "command": "make validate",
    "group": "build",
    "presentation": {
        "echo": true,
        "reveal": "always"
    }
}
```

---

*This validation system helps ensure high-quality, error-free manuscripts while providing clear guidance for fixing any issues that arise. For more information, see the [User Guide](user_guide.md) and [API Reference](api/README.md).*