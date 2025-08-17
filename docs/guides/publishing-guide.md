# Publishing Guide: From Manuscript to Publication

Complete guide for preparing and submitting your manuscript for publication.

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
- **Comments**: Include journal submission status if relevant
- **Updates**: Use "replace" for corrections, not new submissions

## Journal Submission

### Prepare Journal-Specific Format
```bash
# Generate final PDF
rxiv pdf

# Check journal requirements:
# - Word count limits
# - Figure resolution requirements
# - Reference format
# - Supplementary material guidelines
```

### Common Journal Requirements

#### High-Impact Journals (Nature, Science, Cell)
- **Word limits**: 3000-4500 words (including references)
- **Figures**: Maximum 4-6 main figures
- **Format**: Single column for submission
- **Supplementary**: Extensive supplementary allowed

#### Specialized Journals
- **Format**: Often double-column
- **Length**: More flexible word counts
- **Figures**: More figures typically allowed
- **Specificity**: Domain-specific formatting requirements

### Submission Process
1. **Journal Selection**: Impact factor, scope, open access policy
2. **Format Check**: Ensure manuscript meets guidelines
3. **Cover Letter**: Explain significance and fit
4. **Suggest Reviewers**: Provide 3-5 potential reviewers
5. **Upload**: Submit through journal system

## Version Control for Publications

### Tagging Versions
```bash
# Tag submission versions
git tag -a arxiv-v1 -m "arXiv submission v1"
git tag -a journal-submitted -m "Journal submission to Nature"
git tag -a revision-1 -m "First revision after peer review"
```

### Track Changes Between Versions
```bash
# Generate change-tracked PDF for revisions
rxiv track-changes arxiv-v1 --output-dir revision-outputs/

# This creates a PDF highlighting all changes since arXiv v1
```

## Responding to Peer Review

### Prepare Revision
1. **Create Response Document**: Address each reviewer comment
2. **Track Changes**: Use change tracking to show modifications
3. **Update Manuscript**: Make requested changes
4. **Generate Clean Version**: Final PDF without change marks

### Revision Workflow
```bash
# Before making changes
git tag -a pre-revision -m "Before addressing reviewer comments"

# Make your changes to manuscript files
# Edit 01_MAIN.md, update figures, add references

# Generate change-tracked version for editors
rxiv track-changes pre-revision --output-dir reviewer-response/

# Generate clean final version
rxiv pdf --output-dir final-revision/
```

## Open Access and Licensing

### Choose Appropriate License
- **CC BY**: Most permissive, allows commercial use
- **CC BY-NC**: Non-commercial use only
- **CC BY-SA**: Share-alike requirement
- **Traditional Copyright**: Journal retains rights

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