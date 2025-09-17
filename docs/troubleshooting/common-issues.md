# Common Issues - Quick Solutions

*This documentation has been consolidated into the comprehensive Troubleshooting Guide.*

**👉 [View the complete Troubleshooting Guide →](troubleshooting.md)**

## 🚨 Emergency Quick Fixes

**Having urgent issues? Try these first:**

```bash
# 🔥 Nuclear option - clean everything and rebuild
rxiv clean --all && rxiv setup && rxiv pdf

# 🔍 Debug mode - see what's failing
rxiv pdf --verbose

# ⚡ Skip validation - quick build to test
rxiv pdf --skip-validation
```

## 🔍 Quick Issue Lookup

| Issue Type | Quick Solution | Detailed Guide |
|------------|----------------|----------------|
| **Command not found** | `pipx install rxiv-maker` | [Installation Issues](troubleshooting.md#installation-issues) |
| **PDF generation fails** | `rxiv pdf --verbose` | [PDF Generation Failures](troubleshooting.md#pdf-generation-failures) |
| **Missing figures** | `rxiv pdf --force-figures` | [Figure Generation Failures](troubleshooting.md#figure-generation-failures) |
| **Citation errors** | Check `03_REFERENCES.bib` format | [Citation Problems](troubleshooting.md#citation-and-bibliography-problems) |
| **Performance issues** | `rxiv clean` then rebuild | [Performance Issues](troubleshooting.md#performance-issues) |
| **LaTeX errors** | `rxiv validate --detailed` | [Platform-Specific Problems](troubleshooting.md#platform-specific-problems) |

## 📞 Getting Help

- **Quick questions**: [GitHub Discussions](https://github.com/henriqueslab/rxiv-maker/discussions)
- **Bug reports**: [GitHub Issues](https://github.com/henriqueslab/rxiv-maker/issues)
- **Detailed solutions**: [Complete Troubleshooting Guide](troubleshooting.md)

## 💡 Prevention Tips

1. **Always run** `rxiv validate` before `rxiv pdf`
2. **Keep dependencies updated**: `pipx upgrade rxiv-maker`
3. **Use version control**: `git` for your manuscripts
4. **Regular cleanup**: `rxiv clean` periodically

---

**📖 For comprehensive troubleshooting, see the [Complete Troubleshooting Guide](troubleshooting.md).**