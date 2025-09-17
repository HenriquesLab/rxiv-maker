# First Manuscript - Quick Developer Reference

*Developer-focused quick start for testing and contributing*

> **👋 New User?** For the complete step-by-step walkthrough, see our **[First Manuscript Guide](https://rxiv-maker.henriqueslab.org/getting-started/first-manuscript/)** on the website.

This guide provides **developer shortcuts** for quickly testing rxiv-maker functionality during development.

---

## 🚀 Quick Development Test

### Rapid Setup (30 seconds)
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
rxiv pdf --engine local          # Local build (default)
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

- **[Developer Guide](../development/developer-guide.md)** - Complete development documentation
- **[Testing Guide](../development/github-actions-testing.md)** - Testing workflows
- **[API Documentation](../../src/docs/api/)** - Code reference
- **[Contributing Guide](../../CONTRIBUTING.md)** - Contribution guidelines

## 🌐 User-Facing Documentation

For comprehensive user tutorials and guides, users should visit:

**📖 [Complete First Manuscript Tutorial →](https://rxiv-maker.henriqueslab.org/getting-started/first-manuscript/)**

---

*This developer reference focuses on testing and debugging workflows. For user-facing tutorials, see the [website documentation](https://rxiv-maker.henriqueslab.org/).*