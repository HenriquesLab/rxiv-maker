# First Manuscript Guide

> **📖 For the complete tutorial**, see the **[First Manuscript Guide](https://rxiv-maker.henriqueslab.org/getting-started/first-manuscript/)** on our website.

This file provides developer shortcuts for testing rxiv-maker functionality.

---

## 👤 User Tutorial

**For new users**, please visit our step-by-step tutorial:

**🔗 [rxiv-maker.henriqueslab.org/getting-started/first-manuscript](https://rxiv-maker.henriqueslab.org/getting-started/first-manuscript/)**

The website guide includes:
- Step-by-step walkthrough (5 minutes)
- Sample content and examples
- Troubleshooting tips
- Next steps and learning path
- Clear explanations of each step

---

## 🧪 Developer Quick Test

For developers testing rxiv-maker functionality:

### Quick Development Test
```bash
# Quick development test
rxiv init test-manuscript && cd test-manuscript
rxiv pdf && echo "✅ Basic functionality working"
```

### Verify Development Features
```bash
# Test key development scenarios
rxiv validate --detailed        # Structure validation
rxiv pdf --verbose              # Debug output
rxiv clean && rxiv pdf          # Clean build test
## 🧪 Development Testing Scenarios

### Test Different Build Options
```bash
# Test various build configurations
rxiv pdf                         # Standard build (default)
rxiv pdf --force-figures         # Force figure regeneration
rxiv pdf --skip-validation      # Skip structure validation
```

### Test Error Handling
```bash
# Test validation catches issues
echo "Invalid content" > 01_MAIN.md
rxiv validate                    # Should show validation errors
rxiv pdf                        # Should fail gracefully

# Reset to template
rxiv clean && git checkout 01_MAIN.md
```

### Test Extension Points
```bash
# Test Python execution
echo '{{py:exec print("Development test")}}' >> 01_MAIN.md
rxiv pdf

# Test custom LaTeX
echo '{{tex: \\textbf{Development build}}}' >> 01_MAIN.md
rxiv pdf
```

## 🔧 Developer Debugging Workflows

### Common Development Scenarios
```bash
# Test manuscript validation
rxiv validate --detailed          # Check structure
rxiv validate --fix-common        # Auto-fix issues

# Debug PDF generation
rxiv pdf --debug                  # Maximum verbosity
rxiv pdf --dry-run               # Validate without building

# Test figure generation
rxiv pdf --figures-only          # Only generate figures
```

### Integration Testing
```bash
# Test complete workflow
rxiv init integration-test
cd integration-test

# Add complex test content
echo "{{py:exec import numpy as np}}" >> 01_MAIN.md
echo "Test reference [@test2023]" >> 01_MAIN.md

# Test should pass
rxiv validate && rxiv pdf
```

## 🔗 Developer Resources

- **[Contributing Guide](../CONTRIBUTING.md)** - Contribution guidelines

## 🌐 User-Facing Documentation

For comprehensive user tutorials and guides, users should visit:

**📖 [Complete First Manuscript Tutorial →](https://rxiv-maker.henriqueslab.org/getting-started/first-manuscript/)**

---

*This developer reference focuses on testing and debugging workflows. For user-facing tutorials, see the [website documentation](https://rxiv-maker.henriqueslab.org/).*