# Change Tracking Workflow

Change tracking in Rxiv-Maker allows researchers to generate PDFs that visually highlight differences between the current manuscript and any previous version stored in git. This capability is essential for academic workflows involving manuscript revisions, collaborative reviews, and version documentation.

## Overview

The change tracking system:

- **Compares versions**: Current manuscript vs. any git tag
- **Visual highlighting**: Uses LaTeX diff markup to show changes
- **Preserves formatting**: Maintains publication-quality typesetting
- **Handles complexity**: Works with figures, tables, equations, and citations
- **Cross-platform**: Supports both local and Docker execution

## Quick Start

```bash
# Create a baseline tag
git tag -a v1.0.0 -m "Initial version"

# Make changes to your manuscript
# Edit MANUSCRIPT/01_MAIN.md, add figures, update references, etc.

# Generate change-tracked PDF
make pdf-track-changes TAG=v1.0.0

# Output: output/MANUSCRIPT_changes_vs_v1.0.0.pdf
```

## Academic Workflows

### Pre-Submission Review

```bash
# Before submitting to journal
git tag -a "submission-ready" -m "Ready for journal submission"
git push origin submission-ready

# After receiving reviewer comments
# ... make revisions ...

# Generate PDF showing all changes made
make pdf-track-changes TAG=submission-ready

# Send change-tracked PDF to co-authors for review
```

### Preprint Version Tracking

```bash
# After posting initial preprint
git tag -a "preprint-v1" -m "Initial preprint on bioRxiv"

# After incorporating community feedback
# ... update manuscript ...

# Show changes for updated preprint
make pdf-track-changes TAG=preprint-v1

# Upload change-tracked PDF as supplementary material
```

### Multi-Round Peer Review

```bash
# Tag each review round
git tag -a "review-round-1" -m "After first peer review"
git tag -a "review-round-2" -m "After second peer review"

# Show cumulative changes across review rounds
make pdf-track-changes TAG=review-round-1

# Show changes from most recent round
make pdf-track-changes TAG=review-round-2
```

### Collaborative Writing

```bash
# Daily collaboration workflow
git tag -a "daily-$(date +%Y-%m-%d)" -m "Daily checkpoint"

# At end of writing session
make pdf-track-changes TAG=daily-$(date -d yesterday +%Y-%m-%d)

# Share daily change summary with collaborators
```

## Advanced Usage

### Custom Output Directories

```bash
# Track changes for specific manuscript
make pdf-track-changes TAG=v1.0.0 MANUSCRIPT_PATH=MY_RESEARCH_PAPER

# Use custom output location
rxiv track-changes \
    --manuscript-path MANUSCRIPT \
    --git-tag v1.0.0 \
    --output-dir custom_output \
    --verbose
```

### Docker Integration

```bash
# Use Docker for consistent environment
make pdf-track-changes TAG=v1.0.0 RXIV_ENGINE=DOCKER

# Combine with figure regeneration
make clean && make pdf-track-changes TAG=v1.0.0 FORCE_FIGURES=true RXIV_ENGINE=DOCKER
```

### CI/CD Integration

#### GitHub Actions

```yaml
name: Generate Change Tracking PDF

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  change-tracking:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
      with:
        fetch-depth: 0  # Fetch full history for tag access
        
    - name: Get previous tag
      id: prev-tag
      run: |
        PREV_TAG=$(git describe --tags --abbrev=0 HEAD~1 2>/dev/null || echo "")
        echo "prev_tag=$PREV_TAG" >> $GITHUB_OUTPUT
        
    - name: Generate change tracking PDF
      if: steps.prev-tag.outputs.prev_tag != ''
      run: |
        make pdf-track-changes TAG=${{ steps.prev-tag.outputs.prev_tag }} RXIV_ENGINE=DOCKER
        
    - name: Upload change tracking PDF
      if: steps.prev-tag.outputs.prev_tag != ''
      uses: actions/upload-artifact@v3
      with:
        name: change-tracking-pdf
        path: output/*_changes_vs_*.pdf
```

#### GitLab CI

```yaml
stages:
  - build
  - track-changes

track-changes:
  stage: track-changes
  image: henriqueslab/rxiv-maker-base:latest
  script:
    - PREV_TAG=$(git describe --tags --abbrev=0 HEAD~1 2>/dev/null || echo "")
    - if [ -n "$PREV_TAG" ]; then
        make pdf-track-changes TAG=$PREV_TAG RXIV_ENGINE=DOCKER;
      fi
  artifacts:
    paths:
      - output/*_changes_vs_*.pdf
    expire_in: 1 week
  only:
    - main
    - develop
```

## Understanding Change Markup

The generated PDF uses visual markers to highlight changes:

### Text Changes
- **🔵 Added text**: <ins>Underlined in blue</ins>
- **🔴 Deleted text**: ~~Struck through in red~~
- **🟡 Modified text**: Combination of deletion + addition

### Structural Changes
- **New sections**: Entire sections highlighted if added
- **Reorganized content**: Shows moved paragraphs and sections
- **Figure updates**: Highlights figure caption and reference changes
- **Table modifications**: Shows changed table content and structure

### Mathematical Content
- **Equation changes**: Highlights modified mathematical expressions
- **Formula updates**: Shows changes in chemical formulas and scientific notation
- **Reference updates**: Highlights changed equation numbering and cross-references

## Troubleshooting

### Common Issues

#### Git Tag Not Found
```bash
# Error: Git tag 'v1.0.0' does not exist
git tag -l                    # List available tags
git tag -a v1.0.0 -m "Tag"    # Create missing tag
```

#### LaTeX Compilation Errors
```bash
# Check compilation log
cat output/MANUSCRIPT_changes_vs_TAG.log

# Test LaTeX compilation manually
cd output
pdflatex MANUSCRIPT_changes_vs_TAG.tex
```

#### Missing Files
```bash
# Verify manuscript structure
ls MANUSCRIPT/
ls MANUSCRIPT/FIGURES/

# Check git repository status
git status
git log --oneline -5
```

### Debugging Commands

```bash
# Verbose change tracking
rxiv track-changes \
    --manuscript-path MANUSCRIPT \
    --git-tag v1.0.0 \
    --verbose

# Test latexdiff directly
latexdiff output/tag/tag_manuscript.tex output/current/MANUSCRIPT.tex

# Verify git tag extraction
git show v1.0.0:MANUSCRIPT/01_MAIN.md
```

## Performance Optimization

### Large Manuscripts
- Use `make clean` before change tracking for consistent results
- Consider breaking large manuscripts into sections for faster processing
- Monitor Docker resources for memory-intensive compilations

### Frequent Usage
- Cache compiled LaTeX files between runs
- Use incremental figure generation (`FORCE_FIGURES=false`)
- Implement automated tagging strategies for regular checkpoints

### Network Considerations
- DOI validation may slow processing - use `--no-doi` for offline work
- Docker image pulls may be slow - pre-pull images for CI/CD

## Best Practices

### Tagging Strategy
```bash
# Use semantic versioning
git tag -a v1.0.0 -m "Initial submission"
git tag -a v1.1.0 -m "Minor revisions"
git tag -a v2.0.0 -m "Major revision"

# Use descriptive tags for milestones
git tag -a submission-nature -m "Submitted to Nature"
git tag -a response-reviewers -m "Response to reviewers"
git tag -a final-accepted -m "Accepted version"
```

### Collaborative Workflows
- Establish team tagging conventions
- Share change-tracked PDFs through git LFS for large files
- Use pull request workflows for tracking contributor changes
- Document significant changes in git commit messages

### Quality Assurance
- Always validate manuscripts before change tracking
- Review change-tracked PDFs before sharing with collaborators
- Test change tracking with example manuscripts
- Verify all figures and references appear correctly

## Integration Examples

### With Overleaf
```bash
# Export from Overleaf, track changes, then re-import
git clone https://git.overleaf.com/project-id
cd project-id
git tag -a overleaf-export -m "Exported from Overleaf"

# Convert to Rxiv-Maker format
# ... conversion steps ...

make pdf-track-changes TAG=overleaf-export
```

### With Reference Managers
```bash
# Before major bibliography updates
git tag -a before-bib-update -m "Before bibliography revision"

# After updating references
make pdf-track-changes TAG=before-bib-update

# Highlights show citation changes clearly
```

### With Figure Updates
```bash
# Before regenerating figures
git tag -a before-figure-update -m "Before figure regeneration"

# After updating figure scripts
make pdf-track-changes TAG=before-figure-update FORCE_FIGURES=true

# Shows both text and figure changes
```

---

*This workflow guide provides comprehensive coverage of change tracking capabilities. For technical details, see the [Commands Reference](../reference/commands.md#change-tracking). For troubleshooting, see the [Troubleshooting Guide](../troubleshooting/common-issues.md).*