# 📚 Rxiv-Maker User Guide

*Complete guide for productive scientific writing with Rxiv-Maker*

**Prerequisites**: Complete the [first manuscript walkthrough](../quick-start/first-manuscript.md) for installation and basic setup.

---

## 📑 Table of Contents

1. [Daily Writing Workflows](#-daily-writing-workflows)
2. [Manuscript Structure & Best Practices](#-manuscript-structure--best-practices)  
3. [Advanced Markdown Features](#-advanced-markdown-features)
4. [Figure Management & Automation](#-figure-management--automation)
5. [Citation & Bibliography Management](#-citation--bibliography-management)
6. [Collaboration & Version Control](#-collaboration--version-control)
7. [Publication & Submission Workflows](#-publication--submission-workflows)
8. [Advanced Configuration & Customization](#-advanced-configuration--customization)

---

## 🖊️ Daily Writing Workflows

### Core Daily Routine

**Interactive 3-Command Writing Cycle:**

```bash
# Complete writing cycle with progress tracking (copy entire block)
echo "📝 DAILY WRITING SESSION: $(date)"
echo "====================================="

# 1. Health check and current state
echo "🔍 Checking manuscript quality..."
rxiv validate --quick && echo "✅ Structure OK" || echo "⚠️ Issues found"

# 2. Interactive editing prompt
echo "📝 Time to edit! Open your files:"
echo "  → 01_MAIN.md (main content)"
echo "  → FIGURES/ (add/edit analysis scripts)"
echo "  → 03_REFERENCES.bib (citations)"
read -p "Press Enter when finished editing..."

# 3. Generate updated PDF with timing
echo "🚀 Generating updated PDF..."
time rxiv pdf

if [ -f output/*.pdf ]; then
    echo "✅ PDF generated successfully!"
    echo "📁 Location: $(ls output/*.pdf)"
    # Auto-open if available
    command -v open >/dev/null && open output/*.pdf
else
    echo "❌ PDF generation failed. Check errors above."
fi

echo "✅ Writing session completed: $(date)"
```

### Writing Session Best Practices

#### 🌅 Start of Writing Session Script

```bash
# Complete session startup routine (copy and run)
echo "🌅 STARTING WRITING SESSION"
echo "$(date)"
echo "=========================="

# Environment check
echo "🔧 System health check:"
rxiv --version && echo "✅ Rxiv-Maker ready"
echo "📁 Project: $(basename $(pwd))"

# Quick manuscript validation
echo "🔍 Quick health check..."
rxiv validate --syntax-only

if [ $? -eq 0 ]; then
    echo "✅ Manuscript structure OK"
else
    echo "⚠️ Validation issues found - check before proceeding"
fi

# Preview current state
echo "📄 Generating current preview..."
rxiv pdf --skip-validation --fast

# Figure freshness check
echo "📊 Checking figures..."
figure_count=$(find FIGURES -name "*.py" -o -name "*.R" | wc -l 2>/dev/null || echo 0)
echo "Found $figure_count analysis scripts"

if [ "$figure_count" -gt 0 ]; then
    read -p "Force regenerate all figures? (y/N): " regenerate
    if [[ $regenerate =~ ^[Yy]$ ]]; then
        echo "🚀 Regenerating figures..."
        rxiv pdf --force-figures
    fi
fi

echo "🎉 Session ready! Happy writing!"
```

#### ✍️ During Writing - Quick Actions

**Speed iteration script (for active writing):**
```bash
# Ultra-fast iteration mode (copy and run)
echo "⚡ SPEED WRITING MODE"
echo "Press Ctrl+C to exit"
echo "===================="

while true; do
    echo "📝 Make your edits, then press Enter (or Ctrl+C to quit)"
    read
    echo "🚀 Fast build: $(date '+%H:%M:%S')"
    rxiv pdf --skip-validation --fast --quiet
    
    if [ $? -eq 0 ]; then
        echo "✅ Updated successfully"
    else
        echo "❌ Build failed - check errors"
    fi
done
```

**Selective validation scripts:**
```bash
# Check only citations (copy and run)
echo "📚 CITATION CHECK"
rxiv validate --citations-only
echo "✅ Citation check complete"

# Check only figures (copy and run)  
echo "📊 FIGURE CHECK"
rxiv validate --figures-only
echo "✅ Figure check complete"

# Generate draft with watermark (copy and run)
echo "📄 DRAFT GENERATION"
rxiv pdf --draft
echo "✅ Draft PDF with watermark generated"
```

#### 🌆 End of Writing Session Script

```bash
# Complete session wrap-up routine (copy and run)
echo "🌆 ENDING WRITING SESSION"
echo "$(date)"
echo "========================"

# Final comprehensive validation
echo "🔍 Final quality check..."
rxiv validate --detailed

validation_status=$?
if [ $validation_status -eq 0 ]; then
    echo "✅ All validations passed"
else
    echo "⚠️ Validation issues found - review before finalizing"
fi

# Clean and generate final version
echo "🧹 Cleaning temporary files..."
rxiv clean

echo "📄 Generating final clean PDF..."
rxiv pdf

if [ -f output/*.pdf ]; then
    pdf_size=$(ls -lh output/*.pdf | awk '{print $5}')
    echo "✅ Final PDF generated: $pdf_size"
    echo "📁 Location: $(ls output/*.pdf)"
else
    echo "❌ Final PDF generation failed"
fi

# Git integration (if available)
if [ -d ".git" ]; then
    echo "🗺️ Git repository detected"
    echo "Modified files:"
    git status --porcelain
    
    read -p "Commit changes? (Y/n): " commit_changes
    if [[ ! $commit_changes =~ ^[Nn]$ ]]; then
        read -p "Commit message: " commit_msg
        git add .
        git commit -m "${commit_msg:-Writing session $(date '+%Y-%m-%d %H:%M')}"
        echo "✅ Changes committed"
    fi
fi

echo "🎉 Session completed successfully!"
echo "Word count: $(wc -w 01_MAIN.md | awk '{print $1}') words"
```

### Multi-Project Management

#### Working with Multiple Manuscripts
```bash
# Organize projects
├── project1/
│   ├── 01_MAIN.md
│   └── FIGURES/
├── project2/
│   ├── 01_MAIN.md
│   └── FIGURES/
└── shared-figures/    # Reusable figure scripts

# Switch between projects
cd project1 && rxiv pdf
cd ../project2 && rxiv pdf

# Global configuration
rxiv config set author "Dr. Your Name"
rxiv config set engine docker  # Use across all projects
```

#### Initialize Projects
```bash
# Create preprints for different research areas
rxiv init protein-folding-study
rxiv init climate-modeling-analysis  
rxiv init neural-network-optimization
rxiv init genomics-pipeline-paper
```

---

## 📖 Manuscript Structure & Best Practices

### File Organization

#### Standard Structure
```
my-paper/
├── 00_CONFIG.yml          # Metadata and settings
├── 01_MAIN.md             # Main manuscript content
├── 02_APPENDIX.md         # Optional appendices  
├── 03_REFERENCES.bib      # Bibliography
├── FIGURES/               # Figure generation scripts
│   ├── fig1_analysis.py   # Python scripts
│   ├── fig2_plots.R       # R scripts
│   └── diagram.mermaid    # Diagram sources
├── output/                # Generated PDFs and files
└── data/                  # Raw data (not processed)
```

#### 00_CONFIG.yml Configuration
```yaml
# Basic metadata
title: "My Research Title"
authors:
  - name: "First Author"
    affiliation: "University Name"
    email: "first@university.edu"
  - name: "Second Author"
    affiliation: "Another Institution"

# Publication settings
journal: "Nature"
citation_style: "nature"
acknowledge_rxiv_maker: true

# Figure settings
figure_dpi: 300
figure_format: "pdf"

# Advanced options
latex_engine: "xelatex"
bibliography_style: "unsrt"
```

### Content Organization Best Practices

#### Section Structure
```markdown
# Title

## Abstract

## Introduction
- Context and motivation
- Literature review
- Research questions/hypotheses

## Methods
- Experimental design
- Materials and procedures
- Analysis methods

## Results
- Key findings with figures/tables
- Statistical analyses

## Discussion
- Interpretation of results
- Limitations
- Future work

## Conclusion
- Main takeaways
- Significance

## Acknowledgments

## References
```

#### Writing Style Guidelines

**Cross-References:**
```markdown
# Use consistent labeling
![Main results](FIGURES/results.py)
{#fig:main-results}

# Reference in text
Our analysis (Figure @fig:main-results) shows...
The correlation is significant (p < 0.05, see Table @tbl:stats).
```

**Mathematical Notation:**
```markdown
# Inline math
The correlation coefficient was $r = 0.95$.

# Display equations
$$
E = mc^2
$$ {#eq:einstein}

# Reference equations  
As shown in Equation @eq:einstein...
```

**Code Integration:**
```markdown
# Inline code
Use the `rxiv pdf` command to generate output.

# Code blocks
```python
import numpy as np
import matplotlib.pyplot as plt
# Analysis code here
```
```

---

## ⚡ Advanced Markdown Features

### Scientific Cross-References

#### Figure References
```markdown
![Figure caption](FIGURES/analysis.py)
{#fig:analysis tex_position="t" width="0.8\linewidth"}

# Reference in text
Figure @fig:analysis shows the relationship between...

# Multiple references
Figures @fig:analysis and @fig:comparison demonstrate...
```

#### Table References
```markdown
| Variable | Mean | SD |
|----------|------|----| 
| X        | 5.2  | 1.1|
| Y        | 3.8  | 0.9|
{#tbl:descriptive}

# Reference in text
Table @tbl:descriptive presents descriptive statistics...
```

#### Equation References
```markdown
$$
\hat{y} = \beta_0 + \beta_1 x + \epsilon
$$ {#eq:regression}

# Reference in text
The regression model (Equation @eq:regression) was used...
```

### Advanced Formatting

#### Custom Figure Positioning
```markdown
# Figure positioning options
{#fig:label tex_position="t"}     # Top of page
{#fig:label tex_position="b"}     # Bottom of page  
{#fig:label tex_position="h"}     # Here (approximately)
{#fig:label tex_position="H"}     # Here (exactly)
{#fig:label tex_position="p"}     # Full page
{#fig:label tex_position="!t"}    # Force top

# Figure sizing
{#fig:label width="0.5\linewidth"}           # Half page width
{#fig:label width="8cm"}                     # Specific width
{#fig:label width="0.8\linewidth" height="6cm"}  # Width and height
```

#### Special Text Formatting
```markdown
# Scientific notation
The concentration was 1.23 × 10^-6^ M.

# Subscripts and superscripts
H~2~O, CO~2~, x^2^

# Highlighting (for drafts)
==This text is highlighted==

# Comments (not rendered)
<!-- This is a comment for collaborators -->
```

#### Lists and Enumerations
```markdown
# Numbered lists with custom styling
1. First point
   a. Sub-point  
   b. Another sub-point
2. Second point

# Definition lists
Term 1
:   Definition of term 1

Term 2  
:   Definition of term 2
```

---

## 📊 Figure Management & Automation

### Python Figure Scripts

#### 🚀 Complete Python Figure Template

**Copy this complete figure template to FIGURES/:**
```python
# FIGURES/publication_ready_figure.py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from pathlib import Path

# Publication-quality matplotlib setup
def setup_publication_style():
    """Configure matplotlib for publication-ready figures"""
    plt.style.use('seaborn-v0_8-whitegrid')  # Clean, professional style
    plt.rcParams.update({
        'figure.figsize': (10, 6),
        'figure.dpi': 300,
        'font.size': 12,
        'font.family': 'DejaVu Sans',
        'axes.linewidth': 1.2,
        'axes.titlesize': 14,
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'legend.frameon': True,
        'legend.fancybox': True,
        'legend.shadow': True,
        'grid.alpha': 0.3
    })
    print("✅ Publication style configured")

def create_example_data():
    """Generate example data for demonstration"""
    np.random.seed(42)  # Reproducible results
    x = np.linspace(0, 10, 100)
    y_clean = np.sin(x)
    y_noisy = y_clean + 0.1 * np.random.normal(0, 1, len(x))
    
    return x, y_clean, y_noisy

def main():
    """Main figure generation function"""
    print("📊 Generating publication-ready figure...")
    
    # Setup
    setup_publication_style()
    x, y_theory, y_data = create_example_data()
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot theoretical curve
    ax.plot(x, y_theory, 'r-', linewidth=3, label='Theoretical Model', alpha=0.8)
    
    # Plot experimental data points
    ax.scatter(x[::5], y_data[::5], c='blue', s=40, alpha=0.7, 
               label='Experimental Data', edgecolors='black', linewidth=0.5)
    
    # Formatting
    ax.set_xlabel('Time (seconds)', fontweight='bold')
    ax.set_ylabel('Amplitude', fontweight='bold')
    ax.set_title('Experimental Validation of Theoretical Model', 
                 fontweight='bold', pad=20)
    
    # Professional legend
    legend = ax.legend(loc='best', framealpha=0.9)
    legend.get_frame().set_edgecolor('black')
    legend.get_frame().set_linewidth(0.5)
    
    # Grid and layout
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_facecolor('#f8f9fa')
    plt.tight_layout()
    
    # Statistics annotation
    r_squared = np.corrcoef(y_theory[::5], y_data[::5])[0,1]**2
    ax.text(0.05, 0.95, f'R² = {r_squared:.3f}', 
            transform=ax.transAxes, fontsize=11, 
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    print(f"📈 Correlation R²: {r_squared:.3f}")
    print("✅ Figure generated successfully!")
    
    # This triggers Rxiv-Maker to save the figure
    plt.show()

if __name__ == "__main__":
    main()
```

**🧪 Test this figure script:**
```bash
# Create and test the figure script (copy entire block)
echo "🧪 TESTING FIGURE SCRIPT"
mkdir -p FIGURES

# Test direct execution
echo "🔧 Testing Python script directly..."
cd FIGURES && python publication_ready_figure.py
echo "✅ Direct execution complete"

# Test through Rxiv-Maker
echo "🚀 Testing through Rxiv-Maker..."
cd .. && rxiv generate-figures
echo "✅ Rxiv-Maker generation complete"

# Check outputs
echo "📁 Generated files:"
ls -la FIGURES/*.png 2>/dev/null || echo "No PNG files found"
ls -la FIGURES/*.pdf 2>/dev/null || echo "No PDF files found"
```

### R Figure Scripts

#### Basic R Template
```r
# FIGURES/statistical_analysis.R
library(ggplot2)
library(dplyr)

# Load data
data <- read.csv("data/experiment.csv")

# Create publication-quality plot
p <- ggplot(data, aes(x = treatment, y = response)) +
  geom_boxplot(aes(fill = treatment), alpha = 0.7) +
  geom_jitter(width = 0.2, alpha = 0.5) +
  theme_minimal() +
  theme(
    text = element_text(size = 12),
    axis.text = element_text(size = 10),
    legend.position = "none"
  ) +
  labs(
    x = "Treatment Group",
    y = "Response Variable",
    title = "Treatment Effect Analysis"
  )

# Save plot (Rxiv-Maker handles this automatically)
print(p)
```

### Figure Management Commands

```bash
# Force regenerate all figures
rxiv pdf --force-figures

# Clean just figure cache
rxiv clean --figures-only

# Generate figures without full PDF
python FIGURES/my_script.py  # Test individual scripts

# Debug figure issues
rxiv pdf --verbose           # See detailed figure generation logs
```

---

## 📚 Citation & Bibliography Management

### BibTeX Management

#### 03_REFERENCES.bib Structure
```bibtex
@article{smith2023,
    title={Important Research Finding},
    author={Smith, John and Doe, Jane},
    journal={Nature},
    volume={123},
    number={4567},
    pages={123--456},
    year={2023},
    publisher={Nature Publishing Group},
    doi={10.1038/nature12345}
}

@book{jones2024,
    title={Comprehensive Methods Guide},
    author={Jones, Bob},
    publisher={Academic Press},
    year={2024},
    edition={2nd},
    isbn={978-0123456789}
}
```

#### Citation Syntax in Manuscript
```markdown
# Single citation
Previous work [@smith2023] demonstrated...

# Multiple citations  
Several studies [@smith2023; @jones2024; @wang2023] have shown...

# Citation with page numbers
As described in detail [@jones2024, pp. 123-125]...

# Author-year format
@smith2023 showed that the correlation was significant.

# Suppress author
The method was first described [-@jones2024].
```

### Citation Validation
```bash
# Check all citations
rxiv validate --citations-only

# Generate bibliography preview  
rxiv pdf --draft  # See how citations render
```

---

## 👥 Collaboration & Version Control

### Git Integration

#### Initial Setup
```bash
# Initialize manuscript with git
rxiv init collaborative-paper
cd collaborative-paper
git init
git add .
git commit -m "Initial manuscript setup"

# Share with collaborators
git remote add origin https://github.com/yourteam/paper-repo.git
git push -u origin main
```

#### Collaboration Workflow
```bash
# Daily collaboration routine
git pull origin main           # Get latest changes
rxiv validate                 # Check manuscript health
# ... make your changes ...
rxiv pdf                      # Test your changes
git add .
git commit -m "Updated methodology section"
git push origin main
```

### Track Changes for Revisions

#### Revision Documentation
```bash
# Create comprehensive revision package
rxiv track-changes submitted-version revision-version \
    --format pdf \
    --words-only \
    --output revision-package/
```

---

## 🎯 arXiv & Preprint Workflows

### arXiv Submissions

#### Standard arXiv Workflow
```bash
# Generate arXiv package
rxiv arxiv --validate --include-source

# Check contents
unzip -l output/for_arxiv.zip

# Version control for resubmissions
git tag arxiv-v1
rxiv arxiv --output arxiv-v1.zip
```

---

## 🔧 Advanced Configuration & Customization

### Global Configuration

#### User-Wide Settings
```bash
# Set global defaults
rxiv config set author "Dr. Jane Smith"
rxiv config set institution "University Name" 
rxiv config set email "jane@university.edu"
rxiv config set engine "docker"
rxiv config set citation-style "nature"

# View current settings
rxiv config show
```

### Performance Optimization

#### Fast Development Builds
```bash
# Quick iteration during writing
rxiv pdf --skip-validation --draft

# Cache figure generation
export RXIV_CACHE_FIGURES=1

# Parallel processing
export RXIV_PARALLEL_JOBS=8
```

---

## 🎓 Summary & Next Steps

### 📋 Documentation Navigation

#### 🎯 **Essential Next Steps**
- **[📝 CLI Reference](../reference/cli-reference.md)** - Master all commands 
- **[🔧 Troubleshooting](../troubleshooting/troubleshooting.md)** - Solve any issues
- **[👩‍💻 Developer Guide](../development/developer-guide.md)** - Contribute to Rxiv-Maker

#### 🎆 **Complete Documentation Hub**
**[🗺️ Documentation Index →](../../DOCUMENTATION_INDEX.md)** - Navigate all documentation by topic and user type

### Quick Reference Cards

#### Daily Commands Cheat Sheet
```bash
rxiv validate              # Check manuscript
rxiv pdf                   # Generate PDF  
rxiv pdf --draft          # Quick draft
rxiv clean && rxiv pdf    # Clean build
rxiv track-changes v1 v2  # Show changes
```

#### Emergency Troubleshooting
```bash
# Build failing?
rxiv pdf --verbose        # See detailed errors
rxiv clean --all         # Nuclear option
rxiv check-installation  # Verify setup

# Figures broken?
rxiv clean --figures-only # Clear figure cache
python FIGURES/script.py  # Test individual script
```

### 🤝 **Community & Support**

- **[💬 GitHub Discussions](https://github.com/henriqueslab/rxiv-maker/discussions)** - Ask questions, share tips
- **[🐛 GitHub Issues](https://github.com/henriqueslab/rxiv-maker/issues)** - Report bugs, request features  
- **[🤝 Contributing Guide](../../CONTRIBUTING.md)** - Help make Rxiv-Maker better

---

**🎉 Congratulations!** You've mastered the Rxiv-Maker User Guide. You're now equipped to write publication-quality manuscripts with confidence.

**🚀 Happy writing! Transform your research into beautiful publications with Rxiv-Maker.**