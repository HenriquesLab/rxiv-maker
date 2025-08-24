# Troubleshooting Missing Figures

*This troubleshooting content has been integrated into the comprehensive troubleshooting guide.*

**👉 [View complete troubleshooting guide →](troubleshooting.md#figure-generation-failures)**

## Quick Fixes for Figure Issues

```bash
# 🔥 Emergency figure fix - regenerate all figures
rxiv pdf --force-figures

# 🔍 Debug figure generation
rxiv pdf --verbose

# 🐳 Use Docker to bypass local issues
RXIV_ENGINE=DOCKER rxiv pdf
```

## Common Figure Problems

### Figure Not Appearing in PDF
- **Check file path**: Ensure `FIGURES/script_name.py` exists
- **Check script syntax**: Verify Python/R script runs without errors
- **Force regeneration**: Use `--force-figures` flag

### Script Execution Errors
- **Python issues**: Check imports and dependencies
- **R issues**: Verify R packages are installed
- **Path issues**: Ensure relative paths work from manuscript directory

### Figure Quality Problems
- **Resolution**: Set `dpi=300` in matplotlib `savefig()`
- **Format**: Use vector formats (SVG, PDF) when possible
- **Size**: Match figure size to desired output dimensions

## Quick Links

- **[Figure Generation Failures](troubleshooting.md#figure-generation-failures)**
- **[Python Environment Issues](troubleshooting.md#environment-setup-problems)**
- **[Container Engine Issues](troubleshooting.md#container-engine-issues)**
- **[Complete Figure Guide](../guides/figures-guide.md)**

---

**📖 Complete Troubleshooting:** [Troubleshooting Guide](troubleshooting.md)

**📊 Figure Documentation:** [Complete Figure Guide](../guides/figures-guide.md)