# Daily Workflows: Essential Commands

The commands you'll use every day when working with Rxiv-Maker.

## Core Manuscript Workflow

### 1. Daily Writing Session
```bash
# Start your writing session
rxiv validate                    # Check for issues
# Edit your manuscript files...
rxiv pdf                        # Generate updated PDF
```

### 2. Adding Figures
```bash
# Create new Python/R script in FIGURES/
# Add figure reference to your Markdown
rxiv pdf --force-figures        # Regenerate all figures
```

### 3. Quick Validation
```bash
rxiv validate                   # Basic checks
rxiv validate --detailed        # Comprehensive feedback
```

## Working with Multiple Manuscripts

### Switch Between Projects
```bash
# Work on different manuscripts
rxiv pdf project-a/
rxiv pdf project-b/
rxiv validate project-c/
```

### Batch Operations
```bash
# Validate multiple manuscripts
for dir in paper-*/; do
  echo "Checking $dir"
  rxiv validate "$dir"
done
```

## Figure Management

### Force Figure Regeneration
```bash
rxiv pdf --force-figures        # Regenerate all figures
rxiv figures                    # Generate figures only
```

### Figure Development Workflow
```bash
# While developing a complex figure
rxiv figures --force           # Test figure generation
# Edit your Python/R script...
rxiv figures --force           # Test again
rxiv pdf                       # Include in manuscript when ready
```

## Citation Management

### Add New References
```bash
# Add DOI to bibliography
rxiv bibliography add 10.1038/nature12373
rxiv bibliography add 10.1126/science.1234567

# Fix bibliography issues
rxiv bibliography fix
```

### Validate Citations
```bash
rxiv bibliography validate     # Check all citations
rxiv validate --detailed       # Includes citation checks
```

## Collaboration Workflows

### Before Sharing Changes
```bash
rxiv validate                  # Ensure manuscript is valid
rxiv pdf                       # Generate latest PDF
git add -A && git commit -m "Update manuscript"
git push
```

### After Pulling Changes
```bash
git pull
rxiv pdf --force-figures       # Regenerate in case figures changed
```

## Publication Preparation

### arXiv Submission
```bash
rxiv validate --detailed       # Final validation
rxiv pdf                       # Generate final PDF
rxiv arxiv                     # Prepare arXiv package
```

### Journal Submission
```bash
# Generate final versions
rxiv pdf                       # Main manuscript
rxiv clean                     # Clean temporary files
# Manual: Copy PDF and source files to submission system
```

## Troubleshooting Workflow

### When Things Go Wrong
```bash
# Step 1: Validate first
rxiv validate --detailed

# Step 2: Clean and rebuild
rxiv clean
rxiv pdf

# Step 3: Force figure regeneration if needed
rxiv pdf --force-figures

# Step 4: Try Docker if local issues
rxiv pdf --engine docker
```

### Debug Mode
```bash
rxiv pdf --verbose             # Detailed output
rxiv pdf --debug               # Maximum verbosity
```

## Docker Workflows

### Set Docker as Default
```bash
# One-time setup for consistent environment
export RXIV_ENGINE_TYPE=docker

# Now all commands use Docker automatically
rxiv pdf                       # Runs in container
rxiv validate                  # Runs in container
```

### Temporary Docker Use
```bash
rxiv pdf --engine docker       # Just this command
rxiv validate --engine docker  # Just this validation
```

## Configuration Management

### View Current Settings
```bash
# Use environment variables for configuration
echo $RXIV_ENGINE_TYPE         # Current engine
echo $MANUSCRIPT_PATH          # Current manuscript path
```

### Common Configuration
```bash
# Set default manuscript directory
export MANUSCRIPT_PATH="manuscripts/"

# Set default engine
export RXIV_ENGINE_TYPE=docker

# Use rxiv.yml files for manuscript-specific settings
cat > rxiv.yml << 'EOF'
engine:
  type: docker
output:
  directory: "custom-output"
EOF
```

## Performance Tips

### Faster Builds
```bash
# Skip validation for quick iterations
rxiv pdf --skip-validation

# Use Docker for consistent performance
rxiv pdf --engine docker
```

### Efficient Figure Development
```bash
# Generate only figures (no PDF)
rxiv figures

# Work on specific figure interactively
cd FIGURES/
python my_figure.py  # Direct execution for rapid iteration
```

## File Management

### Clean Up
```bash
rxiv clean                     # Remove generated files
rxiv clean --output-only       # Keep figures, remove PDF
```

### Output Organization
```bash
# Custom output location
rxiv pdf --output-dir results/
rxiv pdf --output-dir "paper-v$(date +%Y%m%d)/"
```

## Quick Reference Card

```bash
# Essential daily commands
rxiv validate                  # Check manuscript
rxiv pdf                      # Generate PDF
rxiv pdf --force-figures      # Regenerate figures
rxiv clean                    # Clean outputs
rxiv arxiv                    # Prepare submission

# Help and Information
rxiv --help                  # Get help
rxiv pdf --help              # Command-specific help

# Troubleshooting
rxiv validate --detailed     # Comprehensive checks
rxiv pdf --verbose           # Detailed output
rxiv pdf --engine docker     # Use containerized build
```

## Workflow Automation

### Shell Aliases
Add to your `.bashrc` or `.zshrc`:

```bash
alias rpdf='rxiv pdf'
alias rval='rxiv validate'
alias rfig='rxiv pdf --force-figures'
alias rclean='rxiv clean'
```

### Git Hooks
Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Validate manuscript before commit
rxiv validate || exit 1
```

## Next Steps

- **[Complete Guide](../guides/user_guide.md)** - Comprehensive documentation
- **[CLI Reference](../reference/cli-commands.md)** - All commands and options
- **[Troubleshooting](../troubleshooting/)** - Common issues and solutions