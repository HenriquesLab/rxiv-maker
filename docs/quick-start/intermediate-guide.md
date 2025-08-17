# Intermediate Guide: 15-Minute Deep Dive

Build on your first manuscript with advanced features and professional workflows.

## Prerequisites

- Completed [5-Minute First Manuscript](first-manuscript.md)
- Basic familiarity with scientific writing
- 15 minutes for this walkthrough

## What You'll Learn

- Scientific cross-references and citations
- Automated figure generation with Python
- Professional manuscript metadata
- Change tracking and version control
- Publication-ready output

---

## Step 1: Enhanced Manuscript Structure (3 minutes)

### Update Configuration
Open `00_CONFIG.yml` in your manuscript directory and update it:

```yaml
title: "Automated Scientific Writing: A Comparative Analysis"
short_title: "Automated Scientific Writing"

authors:
  - name: "Dr. Sarah Chen"
    affiliation: "Department of Computer Science, University of Research"
    orcid: "0000-0000-0000-0000"
    corresponding: true
    email: "s.chen@university.edu"
  - name: "Prof. Michael Rodriguez"
    affiliation: "Institute for Scientific Computing"
    orcid: "0000-0000-0000-0001"

abstract: |
  We present a comprehensive analysis of automated scientific writing tools, 
  demonstrating significant improvements in productivity and reproducibility. 
  Our results show a 300% reduction in formatting time and 95% fewer citation errors.

keywords: ["scientific writing", "automation", "reproducibility", "LaTeX", "Markdown"]

journal:
  name: "Journal of Computational Science"
  style: "elsevier"

# Enable advanced features
acknowledge_rxiv_maker: true
enable_doi_validation: true
```

### Add Scientific Content
Replace `01_MAIN.md` with a more structured manuscript:

```markdown
# Automated Scientific Writing: A Comparative Analysis

## Abstract

We present a comprehensive analysis of automated scientific writing tools, demonstrating significant improvements in productivity and reproducibility. Our results show a 300% reduction in formatting time and 95% fewer citation errors.

**Keywords:** scientific writing, automation, reproducibility, LaTeX, Markdown

## Introduction

The scientific publishing landscape has evolved dramatically in recent years [@smith2023evolution; @rodriguez2024automation]. Traditional LaTeX-based workflows, while powerful, present significant barriers to adoption [@chen2023barriers].

Recent developments in automated writing tools have shown promise in addressing these challenges [@wilson2024tools]. This study evaluates the effectiveness of modern writing automation systems.

## Methods

### Experimental Design

We conducted a controlled comparison study with three groups:
- **Control Group**: Traditional LaTeX workflow (n=30)
- **Treatment Group A**: Markdown-based automation (n=30)  
- **Treatment Group B**: Hybrid LaTeX-Markdown system (n=30)

### Metrics Evaluated

Our primary outcome measures included:
1. **Time to Publication**: From first draft to submission-ready PDF
2. **Error Rate**: Citation, reference, and formatting errors
3. **User Satisfaction**: Likert scale survey (1-7)

For detailed methodology, see @fig:workflow.

![Experimental workflow diagram](FIGURES/workflow_diagram.py){#fig:workflow width="0.8\\textwidth"}

## Results

### Primary Outcomes

The automated writing approach demonstrated significant advantages across all measured parameters (see @tbl:results).

| Metric | Traditional LaTeX | Markdown Automation | Improvement |
|--------|------------------|-------------------|-------------|
| Time to Publication (hours) | 24.3 ± 4.2 | 8.1 ± 1.8 | 67% faster |
| Citation Errors | 3.2 ± 1.1 | 0.2 ± 0.4 | 94% reduction |
| User Satisfaction | 4.1 ± 0.9 | 6.4 ± 0.7 | 56% increase |

: Comparison of writing systems across key metrics {#tbl:results}

### Figure Analysis

@fig:performance shows the dramatic performance improvements achieved through automation. The most significant gains were observed in:

- **Setup Time**: 90% reduction in initial configuration
- **Revision Cycles**: 75% faster iteration during peer review
- **Collaboration Efficiency**: 85% improvement in multi-author workflows

![Performance comparison across different writing systems](FIGURES/performance_comparison.py){#fig:performance width="\\textwidth"}

## Discussion

### Key Findings

Our results demonstrate that automated scientific writing tools can significantly improve both productivity and output quality. The 67% reduction in time-to-publication (@fig:performance) represents a major advancement for the scientific community.

### Implications for Scientific Publishing

These findings suggest that adoption of automated writing tools could:
1. **Democratize scientific publishing** by reducing technical barriers
2. **Improve reproducibility** through standardized formatting
3. **Accelerate scientific communication** via faster publication cycles

### Limitations

Several limitations should be noted:
- Learning curve for new users varies significantly
- Complex mathematical notation may require LaTeX knowledge
- Integration with legacy workflows needs improvement

### Future Directions

Future research should focus on:
- Advanced mathematical notation support
- Real-time collaborative editing features  
- Integration with reference management systems
- Machine learning-assisted content suggestions

## Conclusion

Automated scientific writing represents a paradigm shift in academic publishing. Our study demonstrates substantial improvements in efficiency, accuracy, and user experience compared to traditional approaches.

The evidence suggests that widespread adoption of these tools could transform scientific communication, making high-quality publication accessible to a broader research community while maintaining rigorous academic standards.

## Acknowledgments

We thank the participants in our user study and the developers of open-source scientific writing tools. This research was supported by the National Science Foundation (Grant #12345).

## References

*References are automatically generated from 03_REFERENCES.bib*
```

## Step 2: Add Scientific References (3 minutes)

### Create Bibliography
Add to `03_REFERENCES.bib`:

```bibtex
@article{smith2023evolution,
  title={The Evolution of Scientific Publishing in the Digital Age},
  author={Smith, Jane A. and Johnson, Robert B.},
  journal={Nature Communications},
  volume={14},
  number={1},
  pages={1--12},
  year={2023},
  publisher={Nature Publishing Group},
  doi={10.1038/s41467-023-36789-1}
}

@article{rodriguez2024automation,
  title={Automation in Academic Writing: Tools and Techniques},
  author={Rodriguez, Michael and Chen, Sarah},
  journal={Journal of Computational Science},
  volume={45},
  pages={101--115},
  year={2024},
  doi={10.1016/j.jocs.2024.101234}
}

@article{chen2023barriers,
  title={Barriers to Adoption of Modern Writing Tools in Academia},
  author={Chen, Sarah and Wilson, David},
  journal={Computers \& Education},
  volume={189},
  pages={104567},
  year={2023},
  doi={10.1016/j.compedu.2023.104567}
}

@article{wilson2024tools,
  title={A Comprehensive Review of Scientific Writing Tools},
  author={Wilson, David and Brown, Emma},
  journal={PLOS ONE},
  volume={19},
  number={3},
  pages={e0287654},
  year={2024},
  doi={10.1371/journal.pone.0287654}
}
```

### Add More DOIs Automatically
```bash
# Add recent papers automatically from DOIs
rxiv bibliography add 10.1038/s41586-024-07123-4
rxiv bibliography add 10.1126/science.adf1234
```

## Step 3: Create Automated Figures (4 minutes)

### Create Workflow Diagram
Create `FIGURES/workflow_diagram.py`:

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

# Set up the figure
fig, ax = plt.subplots(1, 1, figsize=(12, 8))
ax.set_xlim(0, 10)
ax.set_ylim(0, 8)
ax.axis('off')

# Define colors
color_traditional = '#FF6B6B'
color_automated = '#4ECDC4'
color_arrow = '#95A5A6'

# Traditional workflow (left side)
traditional_boxes = [
    (1, 6.5, 'LaTeX Setup'),
    (1, 5.5, 'Manual Formatting'),
    (1, 4.5, 'Citation Management'),
    (1, 3.5, 'Figure Integration'),
    (1, 2.5, 'Bibliography'),
    (1, 1.5, 'Final Compilation')
]

# Automated workflow (right side)
automated_boxes = [
    (7, 6.5, 'Markdown Writing'),
    (7, 5.5, 'Auto Formatting'),
    (7, 4.5, 'DOI Integration'),
    (7, 3.5, 'Python Figures'),
    (7, 2.5, 'Auto Bibliography'),
    (7, 1.5, 'One-Click PDF')
]

# Draw workflow boxes
for x, y, text in traditional_boxes:
    box = FancyBboxPatch((x-0.8, y-0.3), 1.6, 0.6, 
                         boxstyle="round,pad=0.1", 
                         facecolor=color_traditional, 
                         edgecolor='black', alpha=0.7)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=10, weight='bold')

for x, y, text in automated_boxes:
    box = FancyBboxPatch((x-0.8, y-0.3), 1.6, 0.6, 
                         boxstyle="round,pad=0.1", 
                         facecolor=color_automated, 
                         edgecolor='black', alpha=0.7)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=10, weight='bold')

# Add arrows between steps
arrow_props = dict(arrowstyle='->', lw=2, color=color_arrow)

# Traditional workflow arrows
for i in range(len(traditional_boxes)-1):
    ax.annotate('', xy=(1, traditional_boxes[i+1][1]+0.3), 
                xytext=(1, traditional_boxes[i][1]-0.3), 
                arrowprops=arrow_props)

# Automated workflow arrows  
for i in range(len(automated_boxes)-1):
    ax.annotate('', xy=(7, automated_boxes[i+1][1]+0.3), 
                xytext=(7, automated_boxes[i][1]-0.3), 
                arrowprops=arrow_props)

# Add titles
ax.text(1, 7.5, 'Traditional LaTeX Workflow', ha='center', va='center', 
        fontsize=14, weight='bold', color=color_traditional)
ax.text(7, 7.5, 'Automated Rxiv-Maker Workflow', ha='center', va='center', 
        fontsize=14, weight='bold', color=color_automated)

# Add comparison arrow
ax.annotate('', xy=(6, 4), xytext=(2.5, 4), 
            arrowprops=dict(arrowstyle='->', lw=4, color='green'))
ax.text(4.25, 4.5, '67% Faster', ha='center', va='center', 
        fontsize=12, weight='bold', color='green')

# Add time indicators
ax.text(1, 0.5, '~24 hours', ha='center', va='center', 
        fontsize=12, weight='bold', color=color_traditional)
ax.text(7, 0.5, '~8 hours', ha='center', va='center', 
        fontsize=12, weight='bold', color=color_automated)

plt.title('Scientific Writing Workflow Comparison', fontsize=16, weight='bold', pad=20)
plt.tight_layout()
plt.savefig('workflow_diagram.png', dpi=300, bbox_inches='tight')
plt.savefig('workflow_diagram.pdf', bbox_inches='tight')
plt.close()
```

### Create Performance Comparison Chart
Create `FIGURES/performance_comparison.py`:

```python
import matplotlib.pyplot as plt
import numpy as np

# Data for comparison
categories = ['Setup Time', 'Writing Speed', 'Error Rate', 'Collaboration', 'Publication Time']
traditional_scores = [2, 4, 2, 3, 2]  # Lower is worse
automated_scores = [8, 7, 9, 8, 8]    # Higher is better

x = np.arange(len(categories))
width = 0.35

fig, ax = plt.subplots(figsize=(12, 6))

# Create bars
bars1 = ax.bar(x - width/2, traditional_scores, width, label='Traditional LaTeX', 
               color='#FF6B6B', alpha=0.8, edgecolor='black')
bars2 = ax.bar(x + width/2, automated_scores, width, label='Rxiv-Maker Automation', 
               color='#4ECDC4', alpha=0.8, edgecolor='black')

# Add value labels on bars
def add_value_labels(bars):
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height}', ha='center', va='bottom', fontweight='bold')

add_value_labels(bars1)
add_value_labels(bars2)

# Customization
ax.set_xlabel('Performance Metrics', fontsize=12, fontweight='bold')
ax.set_ylabel('Performance Score (1-10)', fontsize=12, fontweight='bold')
ax.set_title('Scientific Writing Tool Performance Comparison', fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(categories, rotation=0, ha='center')
ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=True)
ax.set_ylim(0, 10)

# Add grid for better readability
ax.grid(True, linestyle='--', alpha=0.7, axis='y')
ax.set_axisbelow(True)

# Add improvement percentages
improvements = [(automated_scores[i] - traditional_scores[i]) / traditional_scores[i] * 100 
                for i in range(len(categories))]

for i, improvement in enumerate(improvements):
    ax.text(i, 9.5, f'+{improvement:.0f}%', ha='center', va='center', 
            fontweight='bold', color='green', fontsize=10,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7))

plt.tight_layout()
plt.savefig('performance_comparison.png', dpi=300, bbox_inches='tight')
plt.savefig('performance_comparison.pdf', bbox_inches='tight')
plt.close()
```

## Step 4: Build and Validate (2 minutes)

### Generate Your Professional PDF
```bash
# Validate everything first
rxiv validate --detailed

# Generate figures and PDF
rxiv pdf --force-figures
```

**✅ Success Check**: You should get a professional PDF with:
- Proper title page with author information
- Automatically numbered sections and subsections
- Working cross-references (clicking @fig:workflow jumps to the figure)
- Professional figure captions
- Automatically generated bibliography
- Proper scientific formatting

### Test Change Tracking
```bash
# Make a small edit to your manuscript
# Then track changes (assuming you have git)
git add . && git commit -m "Initial manuscript version"
git tag -a v1.0 -m "First complete draft"

# Make another edit and track changes
# Edit 01_MAIN.md to add a sentence...
rxiv track-changes . v1.0
```

## Step 5: Advanced Features (3 minutes)

### Add Supplementary Information
Create `02_SUPPLEMENTARY_INFO.md`:

```markdown
# Supplementary Information

## Supplementary Methods

### Detailed Statistical Analysis

We performed additional analyses to validate our core findings...

### Software Versions

All analyses were performed using:
- Python 3.11.5
- Matplotlib 3.7.2
- NumPy 1.24.3
- Rxiv-Maker v2.0.0

## Supplementary Results

### Extended Performance Metrics

![Extended performance analysis](FIGURES/extended_analysis.py){#sfig:extended width="\\textwidth"}

Additional metrics showed consistent improvements across all categories measured.

## Supplementary Tables

| Tool | Learning Curve (days) | Advanced Features | Community Support |
|------|----------------------|-------------------|-------------------|
| LaTeX | 14-30 | Excellent | Strong |
| Rxiv-Maker | 1-3 | Very Good | Growing |
| Word | 1 | Limited | Commercial |

: Detailed tool comparison {#stbl:tools}
```

### Prepare for Submission
```bash
# Create arXiv-ready package
rxiv arxiv

# This creates output/for_arxiv.zip with everything needed for submission
```

### Configure for Different Journals
Update your `00_CONFIG.yml` for specific journals:

```yaml
# For Nature journals
journal:
  name: "Nature"
  style: "nature"
  
# For Science
journal:
  name: "Science" 
  style: "science"

# For PLOS journals
journal:
  name: "PLOS ONE"
  style: "plos"
```

---

## What You've Accomplished

🎉 **Congratulations!** You've created a professional, publication-ready scientific manuscript with:

- **Professional Structure**: Complete manuscript with all standard sections
- **Automated Citations**: Working bibliography with DOI integration  
- **Dynamic Figures**: Python-generated visualizations with proper referencing
- **Change Tracking**: Version control integration for collaborative editing
- **Publication Ready**: arXiv submission package and journal formatting

## Next Steps

**Ready for more?** Check out these advanced guides:

- **[Daily Workflows](daily-workflows.md)** - Essential commands for regular use
- **[Publishing Guide](../guides/publishing-guide.md)** - From submission to publication
- **[Writing Guide](../guides/writing-guide.md)** - Advanced Rxiv-Markdown syntax
- **[Collaboration Guide](../guides/collaboration-guide.md)** - Multi-author workflows

## Common Next Questions

**Q: How do I add mathematical equations?**
```markdown
Inline math: $E = mc^2$

Block equations:
$$
\frac{\partial u}{\partial t} = D \nabla^2 u
$$ {#eq:diffusion}

Reference: See @eq:diffusion for the diffusion equation.
```

**Q: How do I manage large bibliographies?**
```bash
# Add papers by DOI
rxiv bibliography add 10.1038/nature12373 10.1126/science.123456

# Fix formatting issues
rxiv bibliography fix --dry-run  # Preview fixes
rxiv bibliography fix            # Apply fixes
```

**Q: How do I work with collaborators?**
```bash
# Use git for version control
git init
git add .
git commit -m "Initial manuscript"

# Share via GitHub/GitLab for collaboration
# Each collaborator can edit and generate their own PDFs
```

**Q: My figures aren't showing up?**
```bash
# Force regenerate all figures
rxiv pdf --force-figures

# Debug figure generation
rxiv figures --verbose

# Check specific figure
cd FIGURES && python workflow_diagram.py
```

You now have the skills to create professional scientific documents with automated figure generation, citations, and professional formatting!