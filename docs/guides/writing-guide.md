# Scientific Writing with Rxiv-Markdown

Complete guide to writing scientific manuscripts using Rxiv-Maker's enhanced Markdown syntax.

## Quick Reference

### Essential Syntax
```markdown
# Heading 1 (Title)
## Heading 2 (Section)
### Heading 3 (Subsection)

**Bold text** and *italic text*

- Unordered list
1. Ordered list

[Link text](https://example.com)
```

### Scientific Cross-References
```markdown
@fig:label          # References a figure: "Fig. 1"
@fig:label A        # Panel reference: "Fig. 1A"
@sfig:label         # Supplementary figure: "Fig. S1"
@eq:label           # Equation reference: "Eq. 1"
@tbl:label          # Table reference: "Table 1"
@sec:label          # Section reference: "Section 2"
```

### Citations
```markdown
@smith2023                    # (Smith, 2023)
[@smith2023]                 # [Smith, 2023]
[@smith2023; @jones2024]     # [Smith, 2023; Jones, 2024]
```

## Manuscript Structure

### Standard Scientific Paper Format
```markdown
# Title

## Abstract
Brief summary of the work (150-250 words).

## Introduction
Background and motivation. End with clear objectives.

## Methods
Detailed methodology for reproducibility.

## Results
Present findings objectively with figures and tables.

## Discussion
Interpret results, acknowledge limitations.

## Conclusion
Key takeaways and future directions.

## References
Automatically generated from 03_REFERENCES.bib
```

### Configuration in 00_CONFIG.yml
```yaml
title: "Your Paper Title"
authors:
  - name: "First Author"
    affiliation: "University"
    orcid: "0000-0000-0000-0000"
    corresponding: true
    email: "author@university.edu"
  - name: "Second Author"
    affiliation: "Institute"

abstract: "Brief summary of your work..."
keywords: ["keyword1", "keyword2", "keyword3"]

journal:
  name: "Nature"
  style: "nature"  # Citation style
```

## Advanced Markdown Features

### Mathematical Expressions
```markdown
Inline math: $E = mc^2$

Block equations:
$$
\frac{\partial u}{\partial t} = D \nabla^2 u
$$ {#eq:diffusion}

Reference the equation: See @eq:diffusion for the diffusion equation.
```

### Figures with Advanced Positioning
```markdown
![Figure Caption](FIGURES/figure_script.py){#fig:results width="0.8\textwidth" tex_position="t"}

- `width`: Control figure size
- `tex_position`: "t" (top), "b" (bottom), "h" (here), "p" (page)
- `#fig:label`: Create referenceable label
```

### Tables
```markdown
| Parameter | Value | Unit |
|-----------|-------|------|
| Temperature | 298 | K |
| Pressure | 1.0 | atm |

: Experimental conditions {#tbl:conditions}

Reference: See @tbl:conditions for details.
```

### Text Formatting
```markdown
**Bold text** for emphasis
*Italic text* for emphasis
`code` for inline code
~subscript~ for chemical formulas: H~2~O
^superscript^ for exponents: E = mc^2^
```

### Document Control
```markdown
<newpage>              # Force page break
<clearpage>            # Clear floats and start new page

<!-- Comments (not visible in output) -->
```

## Writing Best Practices

### Abstract Writing
- **Purpose**: Why was the study conducted?
- **Methods**: What was done? (briefly)
- **Results**: What was found? (key findings)
- **Conclusions**: What do the results mean?

Example:
```markdown
## Abstract

Understanding protein folding is crucial for drug design **[Purpose]**. 
We used molecular dynamics simulations to study folding pathways **[Methods]**. 
Our results reveal three distinct intermediates in the folding process **[Results]**. 
These findings provide new targets for therapeutic intervention **[Conclusions]**.
```

### Introduction Structure
1. **General Context**: Broad field importance
2. **Specific Problem**: What gap exists?
3. **Previous Work**: What's been done?
4. **Knowledge Gap**: What's missing?
5. **Objectives**: What will you do?

### Results Organization
- **Logical Flow**: Each subsection builds on previous
- **Figure Integration**: Reference figures naturally in text
- **Objective Tone**: Present findings without interpretation
- **Clear Transitions**: Connect sections smoothly

### Discussion Framework
1. **Key Findings**: Summarize main results
2. **Interpretation**: What do results mean?
3. **Literature Context**: How do they fit existing knowledge?
4. **Limitations**: What are the constraints?
5. **Future Work**: What's next?

## Citation Best Practices

### When to Cite
- **Previous work**: All relevant background
- **Methods**: Established techniques
- **Comparisons**: Similar studies
- **Contradictions**: Conflicting results
- **Support**: Claims needing evidence

### Citation Styles by Journal
```yaml
# Nature style
journal:
  style: "nature"      # Numbered citations [1,2]

# Science style  
journal:
  style: "science"     # Numbered citations (1,2)

# Cell style
journal:
  style: "cell"        # Author-year (Smith, 2023)
```

## Figure Integration

### Effective Figure References
```markdown
# Good examples:
Figure @fig:results shows that protein expression increases over time.
The dose-response relationship (see @fig:dose) demonstrates saturation.
As expected (@fig:control), the control group showed no change.

# Avoid:
The figure below shows results.
See Figure 1.
```

### Figure Design Guidelines
- **Clarity**: Single clear message per figure
- **Labels**: All axes, units, error bars explained
- **Color**: Colorblind-friendly palettes
- **Size**: Readable at publication size
- **Caption**: Complete, standalone description

### Multi-Panel Figures
```python
# In FIGURES/multi_panel.py
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Panel A
ax1.plot(data1)
ax1.text(0.05, 0.95, 'A', transform=ax1.transAxes, 
         fontsize=16, weight='bold')

# Panel B  
ax2.plot(data2)
ax2.text(0.05, 0.95, 'B', transform=ax2.transAxes,
         fontsize=16, weight='bold')

plt.tight_layout()
plt.savefig('multi_panel.png', dpi=300, bbox_inches='tight')
```

Reference panels:
```markdown
![Multi-panel results](FIGURES/multi_panel.py){#fig:multi}

Panel @fig:multi A shows treatment effects, while @fig:multi B shows controls.
```

## Collaboration Workflows

### Multi-Author Writing
1. **Structure First**: Agree on outline before writing
2. **Section Assignment**: Each author owns specific sections  
3. **Regular Syncs**: Weekly progress meetings
4. **Version Control**: Use git for change tracking
5. **Review Process**: Systematic peer review

### Version Control Best Practices
```bash
# Commit frequently with clear messages
git add 01_MAIN.md
git commit -m "Add results section for protein expression"

# Use branches for major revisions
git checkout -b reviewer-response
# Make changes...
git commit -m "Address reviewer comments on methodology"

# Tag important versions
git tag -a submission-v1 -m "Initial journal submission"
```

### Review and Feedback
- **Track Changes**: Use `rxiv track-changes` for revisions
- **Comments**: Add TODO comments in Markdown
- **Suggestions**: Use pull requests for proposed changes

## Common Writing Patterns

### Transition Phrases
- **Addition**: Furthermore, Additionally, Moreover
- **Contrast**: However, Nevertheless, In contrast
- **Causation**: Therefore, Consequently, As a result
- **Example**: For instance, Specifically, In particular

### Scientific Voice
- **Active vs Passive**: Prefer active voice when appropriate
- **Precision**: Use specific terms, avoid vague language
- **Objectivity**: Present results without bias
- **Conciseness**: Remove unnecessary words

### Common Mistakes to Avoid
- **Overstating**: "Proves" vs "suggests" or "indicates"
- **Anthropomorphizing**: "The data wants to tell us" → "The data indicate"
- **Redundancy**: "Future prospects" → "Prospects"
- **Informality**: "Pretty good" → "Satisfactory"

## Journal-Specific Guidelines

### High-Impact Journals (Nature, Science, Cell)
- **Length**: 3000-4500 words including references
- **Figures**: Maximum 4-6 main figures
- **Abstract**: 150-200 words
- **Format**: Single column for submission
- **Novelty**: Emphasis on broad significance

### Specialized Journals
- **Length**: More flexible, often 6000+ words
- **Figures**: More figures typically allowed
- **Detail**: More methodological detail expected
- **Audience**: Field-specific terminology appropriate

## Quality Checklist

### Before Submission
- [ ] All figures have proper captions and labels
- [ ] All citations are formatted correctly
- [ ] Cross-references work properly
- [ ] Abstract fits word limit
- [ ] Methods are sufficiently detailed for reproduction
- [ ] Results are presented objectively
- [ ] Discussion addresses limitations
- [ ] Grammar and spelling checked
- [ ] Figure quality suitable for publication

### Technical Validation
```bash
# Check manuscript validity
rxiv validate --detailed

# Generate final PDF
rxiv pdf --force-figures

# Verify all references work
grep -o "@[a-zA-Z0-9:_-]*" 01_MAIN.md
```

## Next Steps

- **[Publishing Guide](publishing-guide.md)** - Submission and peer review
- **[Figures Guide](figures-guide.md)** - Advanced figure creation
- **[CLI Reference](../reference/cli-commands.md)** - Complete command guide