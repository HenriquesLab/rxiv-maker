# Preprint Guide: From Manuscript to arXiv

Complete guide for preparing and submitting your preprint to arXiv and other preprint servers.

## Pre-Submission Checklist

### 1. Final Validation
```bash
# Comprehensive manuscript check
rxiv validate --detailed

# Ensure all figures generate correctly
rxiv pdf --force-figures

# Clean build for final PDF
rxiv clean && rxiv pdf
```

### 2. Content Review
- [ ] All figures have proper captions and labels
- [ ] All citations are valid and formatted correctly
- [ ] Abstract fits journal word limits
- [ ] Keywords are appropriate for the field
- [ ] Author affiliations and ORCID IDs are correct

## arXiv Submission

### Generate arXiv Package
```bash
# Create submission-ready package
rxiv arxiv

# This creates:
# - output/for_arxiv.zip - Complete arXiv submission
# - All source files, figures, and bibliography
```

### arXiv Submission Process
1. **Upload**: Go to [arxiv.org/submit](https://arxiv.org/submit)
2. **Category**: Select appropriate subject class
3. **Files**: Upload the generated `for_arxiv.zip`
4. **Metadata**: Title, authors, abstract, comments
5. **Preview**: Review generated PDF
6. **Submit**: Submit for moderation

### arXiv Best Practices
- **Timing**: Submit by 14:00 UTC for next-day publication
- **Categories**: Choose primary and secondary categories carefully
- **Comments**: Include preprint version or update notes if relevant
- **Updates**: Use "replace" for corrections, not new submissions

## Version Control for Preprints

### Tagging Versions
```bash
# Tag submission versions
git tag -a arxiv-v1 -m "arXiv submission v1"
git tag -a biorxiv-v1 -m "bioRxiv submission v1"
git tag -a arxiv-v2 -m "Updated arXiv version with improvements"
```

### Track Changes Between Versions
```bash
# Generate change-tracked PDF for revisions
rxiv track-changes arxiv-v1 --output-dir revision-outputs/

# This creates a PDF highlighting all changes since arXiv v1
```

## Open Access and Licensing

### Choose Appropriate License
- **CC BY**: Most permissive, allows commercial use
- **CC BY-NC**: Non-commercial use only
- **CC BY-SA**: Share-alike requirement
- **All Rights Reserved**: Traditional copyright protection

### Funding Requirements
Check if your funding agency requires:
- Open access publication
- Specific repositories (PMC, arXiv)
- Data availability statements
- Code sharing

## Supplementary Materials

### Organize Supplementary Content
```bash
# Create supplementary figures
# Place in FIGURES/ with "S" prefix
# Example: FIGURES/SFigure_1_detailed_methods.py

# Reference in main text
# "See Supplementary Figure S1 for detailed methods"
```

### Supplementary File Structure
```
supplementary/
├── supplementary_text.md       # Extended methods, results
├── supplementary_figures/      # Additional figures
├── supplementary_tables/       # Data tables
├── code/                      # Analysis scripts
└── data/                      # Raw data (if appropriate)
```

## Post-Publication

### Share Your Work
- **Social Media**: Twitter, LinkedIn with key findings
- **Institutional Website**: Add to publications list
- **ORCID**: Update publication record
- **Google Scholar**: Verify citation tracking

### Monitor Impact
- **Citations**: Track via Google Scholar, Web of Science
- **Altmetrics**: Social media mentions, news coverage
- **Downloads**: arXiv downloads, journal access statistics

## Common Submission Pitfalls

### Technical Issues
- **Figure Resolution**: Too low for print (need 300+ DPI)
- **File Size**: Too large for submission systems
- **Format Problems**: Incompatible with journal LaTeX class
- **Missing Files**: Figures or bibliography not included

### Content Issues
- **Scope Mismatch**: Manuscript doesn't fit journal scope
- **Length Violations**: Exceeds word/page limits
- **Citation Errors**: Incomplete or incorrect references
- **Figure Quality**: Poor visualization or unclear captions

## Submission Templates

### arXiv Metadata Template
```yaml
# Add to 00_CONFIG.yml for arXiv
arxiv:
  primary_category: "physics.bio-ph"
  secondary_categories: 
    - "q-bio.QM"
  comments: "12 pages, 4 figures"
  msc_class: "92C37"
  acm_class: "J.3"
```

### Journal Cover Letter Template
```markdown
Dear Editor,

We submit our manuscript "Title" for consideration at [Journal Name].

This work reports [key finding] and demonstrates [significance]. 
The results advance our understanding of [field] by [contribution].

This manuscript is appropriate for [Journal] because [reasons]:
- [Reason 1]
- [Reason 2]
- [Reason 3]

We suggest the following reviewers:
- Dr. X (expertise in Y)
- Prof. Z (expert in related work)

We confirm this work has not been published elsewhere.

Sincerely,
[Corresponding Author]
```

## Automation and Tools

### Automated Checks
```bash
# Pre-submission validation script
#!/bin/bash
echo "Running pre-submission checks..."

# Validate manuscript
rxiv validate --detailed || exit 1

# Check figure quality
find FIGURES/ -name "*.png" -exec identify {} \; | grep -v "300x300"

# Count words (approximate)
wc -w MANUSCRIPT/01_MAIN.md

# Generate final PDF
rxiv pdf --force-figures

echo "✅ Ready for submission!"
```

### Integration with Reference Managers
- **Zotero**: Export BibTeX from collections
- **Mendeley**: Sync bibliography automatically
- **EndNote**: Convert to BibTeX format

## Next Steps

- **[Collaboration Guide](collaboration-guide.md)** - Multi-author workflows
- **[Change Tracking](change-tracking.md)** - Version comparison
- **[User Guide](user_guide.md)** - Complete documentation