# Documentation Maintenance Guide

*Comprehensive guide for maintaining high-quality documentation across the rxiv-maker ecosystem*

---

## 🎯 Documentation Standards

### Cross-Repository Consistency
The rxiv-maker ecosystem spans multiple repositories, each with specific documentation responsibilities:

| Repository | Purpose | Documentation Focus |
|------------|---------|-------------------|
| **[Website](https://rxiv-maker.henriqueslab.org/)** | Primary user docs | Tutorials, guides, examples |
| **[Main Repo](https://github.com/HenriquesLab/rxiv-maker)** | Technical reference | API, development, troubleshooting |
| **[VS Code Extension](https://github.com/HenriquesLab/vscode-rxiv-maker)** | IDE integration | Extension features and usage |
| **[Docker Repo](https://github.com/HenriquesLab/docker-rxiv-maker)** | Container workflows | Container setup and deployment |

### Navigation Principles
1. **Single Source of Truth**: Each topic has one primary location
2. **Progressive Disclosure**: Basic → Intermediate → Advanced learning paths
3. **Cross-Repository Links**: Clear navigation between repositories
4. **User-Centric Organization**: Organize by user needs, not technical structure

---

## 🔧 Automated Link Checking

### Link Checker Script
The repository includes an automated link checker to maintain documentation quality:

```bash
# Run locally
python scripts/check-docs-links.py

# Verbose output
python scripts/check-docs-links.py --verbose

# Save report to file
python scripts/check-docs-links.py --output link-report.txt
```

### GitHub Actions Integration
The link checker runs automatically:

- **On every push** to main/experimental branches (for docs changes)
- **On pull requests** affecting documentation
- **Weekly on Mondays** to catch external link changes
- **Manual trigger** via workflow dispatch

### Handling Link Check Failures

#### For Pull Requests
When the link checker fails on a PR:
1. Check the PR comment for specific issues
2. Fix broken links identified in the report
3. Test fixes locally: `python scripts/check-docs-links.py`
4. Push fixes to the PR branch

#### For Scheduled Runs
Weekly failures create GitHub issues automatically:
1. Review the created issue for details
2. Fix identified problems across repositories
3. Close the issue when resolved

---

## 📋 Link Management Best Practices

### Internal Links (Within Repository)

#### ✅ Good Practices
```markdown
# Relative paths from current file location
[Developer Guide](../development/developer-guide.md)
[API Reference](../../src/docs/api/)

# With anchors
[CLI Commands](../reference/cli-reference.md#core-commands)

# Absolute paths from repository root
[Contributing](/CONTRIBUTING.md)
```

#### ❌ Avoid These Patterns
```markdown
# Don't use absolute filesystem paths
[Guide](/Users/name/repo/docs/guide.md)

# Don't hardcode GitHub URLs for internal links
[Guide](https://github.com/HenriquesLab/rxiv-maker/blob/main/docs/guide.md)

# Don't use broken relative paths
[Guide](guide.md)  # When guide.md is not in same directory
```

### Cross-Repository Links

#### ✅ Recommended Patterns
```markdown
# Website (primary user documentation)
[User Guide](https://rxiv-maker.henriqueslab.org/guides/)

# Main repository (technical documentation)
[Developer Guide](https://github.com/HenriquesLab/rxiv-maker/blob/main/docs/development/developer-guide.md)

# VS Code extension
[Extension Features](https://marketplace.visualstudio.com/items?itemName=henriqueslab.rxiv-maker)

# Docker infrastructure
[Container Setup](https://github.com/HenriquesLab/docker-rxiv-maker)
```

#### 🔄 Standard Link Formats
Use these standardized URLs for consistency:

```markdown
# Installation (point to website)
[Installation Guide](https://rxiv-maker.henriqueslab.org/getting-started/installation/)

# Getting started (point to website)
[First Manuscript](https://rxiv-maker.henriqueslab.org/getting-started/first-manuscript/)

# User documentation (point to website)
[User Guide](https://rxiv-maker.henriqueslab.org/guides/)

# Technical reference (main repository)
[CLI Reference](https://github.com/HenriquesLab/rxiv-maker/blob/main/docs/reference/cli-reference.md)

# Developer docs (main repository)
[Developer Guide](https://github.com/HenriquesLab/rxiv-maker/blob/main/docs/development/developer-guide.md)
```

### Navigation Integration

#### Use the Navigation System
Always include navigation context for users:

```markdown
# At the top of technical docs
> **👋 New User?** For complete tutorials, see our **[Website Documentation](https://rxiv-maker.henriqueslab.org/)**.

# At the bottom of guides
**📖 [Complete Documentation Navigation →](../navigation.md)**

# Cross-repository navigation
| **For Users** | **For Developers** | **For Teams** |
|-------|---------|------|
| [Website Docs](https://rxiv-maker.henriqueslab.org/) | [Technical Reference](../navigation.md) | [Docker Setup](https://github.com/HenriquesLab/docker-rxiv-maker) |
```

---

## 🔄 Maintenance Workflows

### Regular Maintenance Tasks

#### Monthly Review Checklist
- [ ] Run link checker across all repositories
- [ ] Review and update cross-repository references
- [ ] Check for outdated external links
- [ ] Update navigation.md if new documentation added
- [ ] Verify installation instructions work on different platforms

#### When Adding New Documentation
1. **Plan the location**: Determine if content belongs in website, main repo, or extension docs
2. **Use standard structure**: Follow existing patterns for headers, navigation, and linking
3. **Add cross-references**: Update navigation.md and add bidirectional links
4. **Test locally**: Run link checker before committing
5. **Update indexes**: Add to relevant README files and navigation systems

#### When Moving Documentation
1. **Create redirect files**: Leave redirect stubs in old locations
2. **Update all references**: Search for links to the old location
3. **Update navigation systems**: Modify navigation.md and index files
4. **Test thoroughly**: Run link checker after all changes

### Automated Maintenance

#### GitHub Actions
The repository includes automated workflows for:
- **Link checking** on documentation changes
- **Cross-repository validation** for ecosystem links
- **Issue creation** for maintenance needs

#### Pre-commit Hooks
Consider adding pre-commit hooks for:
```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: doc-link-check
        name: Check documentation links
        entry: python scripts/check-docs-links.py
        language: system
        files: '\.md$'
        pass_filenames: false
```

---

## 🚨 Troubleshooting

### Common Link Issues

#### "File not found" Errors
```bash
# Debug: Check if file exists
ls -la docs/path/to/file.md

# Fix: Update path or create missing file
# If file was moved, create redirect:
echo '[View Updated Guide →](new-location.md)' > old-location.md
```

#### "Anchor not found" Errors
```bash
# Debug: Check anchor exists in target file
grep -n "anchor-name" docs/target-file.md

# Fix: Update anchor or add missing header
# Anchors are auto-generated from headers: "## My Header" → "#my-header"
```

#### Cross-Repository Link Issues
```bash
# Debug: Test external link manually
curl -I "https://example.com/path"

# Fix: Update to correct URL or add redirect notice
```

### Link Checker Issues

#### False Positives
If the link checker reports issues incorrectly:
1. Check if the file/anchor actually exists
2. Verify the relative path calculation
3. Update the checker script if needed

#### Performance Issues
For large repositories:
```bash
# Check specific directories only
python scripts/check-docs-links.py --base-path docs/specific-area

# Use verbose mode to debug slow operations
python scripts/check-docs-links.py --verbose
```

---

## 📚 Reference Resources

### Documentation Tools
- **MkDocs Material** (Website) - [Documentation](https://squidfunk.github.io/mkdocs-material/)
- **GitHub Pages** (Website hosting)
- **VS Code Markdown** - [Extensions](https://code.visualstudio.com/docs/languages/markdown)

### Style Guides
- [Microsoft Writing Style Guide](https://docs.microsoft.com/en-us/style-guide/)
- [Google Developer Documentation Style Guide](https://developers.google.com/style)
- [Write the Docs Community Resources](https://www.writethedocs.org/guide/)

### Link Checking Tools
- **Internal**: `scripts/check-docs-links.py` (this repository)
- **External**: [markdown-link-check](https://github.com/tcort/markdown-link-check)
- **VS Code**: [Markdown All in One](https://marketplace.visualstudio.com/items?itemName=yzhang.markdown-all-in-one)

---

**📍 Need help maintaining documentation?** See the [Complete Navigation Guide](../navigation.md) or ask in [GitHub Discussions](https://github.com/henriqueslab/rxiv-maker/discussions).