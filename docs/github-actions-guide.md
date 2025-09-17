# GitHub Actions Guide - Team Collaboration

*Cloud-based PDF generation and team collaboration workflows for rxiv-maker manuscripts*

---

## 🎯 Why Use GitHub Actions?

GitHub Actions enables **zero-installation manuscript building** perfect for:

- **👥 Team collaboration** - No need for everyone to install LaTeX
- **🌍 Cross-platform consistency** - Same results everywhere
- **🔄 Automated builds** - PDF updates on every commit
- **📦 Version control** - Full manuscript history with PDFs
- **⚡ Quick testing** - Test changes without local setup

## 🚀 Quick Setup (5 Minutes)

### 1. Fork or Use Template
```bash
# Option A: Fork existing repository
# Go to https://github.com/HenriquesLab/rxiv-maker and click "Fork"

# Option B: Create new repository with template
rxiv init my-paper
cd my-paper
git init
git remote add origin https://github.com/yourusername/my-paper.git
```

### 2. Enable GitHub Actions
1. Go to your repository on GitHub
2. Click **"Actions"** tab
3. If prompted, click **"I understand my workflows, enable them"**

### 3. Generate Your First PDF
1. Go to **Actions** → **"Build and Release PDF"**
2. Click **"Run workflow"**
3. Select your branch (usually `main`)
4. Click **"Run workflow"**
5. Wait ~2-3 minutes
6. Download PDF from workflow artifacts

**🎉 That's it!** You now have cloud-based PDF generation.

---

## 📋 Available Workflows

### 🏗️ Build and Release PDF
**Purpose**: Generate publication-ready PDFs from your manuscript

**Triggers**:
- Manual workflow dispatch (recommended for testing)
- Push to main branch (for automated builds)
- Pull requests (for review builds)

**Outputs**:
- Main manuscript PDF
- Supplementary information PDF
- arXiv submission package (optional)

### 🧪 Testing and Validation
**Purpose**: Validate manuscript structure and dependencies

**Features**:
- Manuscript structure validation
- Citation checking
- Figure generation testing
- Cross-platform compatibility testing

---

## 👥 Team Collaboration Workflows

### Daily Team Workflow
```mermaid
graph LR
    A[Write Content] --> B[Git Commit]
    B --> C[Git Push]
    C --> D[Auto PDF Build]
    D --> E[Team Review]
    E --> F[Merge to Main]
    F --> G[Release PDF]
```

### 1. **Individual Writing**
```bash
# Work on your section locally
git checkout -b feature/my-section
# Edit your files...
git add .
git commit -m "Add methodology section"
git push origin feature/my-section
```

### 2. **Collaborative Review**
1. Create pull request from your branch
2. GitHub Actions automatically builds PDF preview
3. Team reviews both content and generated PDF
4. Discuss changes in PR comments
5. Merge when approved

### 3. **Automated Publishing**
```bash
# Once merged to main, auto-generate final PDFs
git checkout main
git tag v1.0.0  # Optional: tag for releases
git push origin v1.0.0  # Triggers release workflow
```

---

## ⚙️ Configuration Options

### Workflow Configuration Files
Your repository includes these workflow files:

```
.github/workflows/
├── build-pdf.yml           # Main PDF generation
├── test-manuscript.yml     # Validation and testing
└── release.yml            # Release automation
```

### Customizing PDF Generation
Edit `.github/workflows/build-pdf.yml` for custom options:

```yaml
# Example: Add arXiv package to every build
- name: Generate arXiv Package
  run: rxiv arxiv

# Example: Custom build options
- name: Generate PDF
  run: rxiv pdf --force-figures --verbose
```

### Environment Variables
Set repository secrets for advanced features:

| Variable | Purpose | Example |
|----------|---------|---------|
| `CROSSREF_EMAIL` | Citation metadata | `your@email.com` |
| `ARXIV_CATEGORY` | arXiv submission | `physics.bio-ph` |

---

## 🔧 Advanced Features

### Multi-Manuscript Repositories
For repositories with multiple manuscripts:

```yaml
strategy:
  matrix:
    manuscript: ['paper1', 'paper2', 'paper3']
```

### Conditional Builds
Build only when specific files change:

```yaml
paths:
  - '**.md'
  - 'FIGURES/**'
  - '03_REFERENCES.bib'
```

### Artifact Management
Organize outputs by date and branch:

```yaml
- uses: actions/upload-artifact@v3
  with:
    name: manuscript-${{ github.run_id }}
    path: output/
```

---

## 🚨 Troubleshooting

### Common Issues

#### Build Fails with "LaTeX Error"
```bash
# Check workflow logs for specific error
# Common fix: Update bibliography format in 03_REFERENCES.bib
```

#### "Figure Generation Failed"
```bash
# Ensure Python scripts in FIGURES/ are executable
# Check dependencies in requirements.txt
```

#### Long Build Times (>10 minutes)
```bash
# Optimize figure generation scripts
# Use caching for large datasets
# Consider splitting complex figures
```

### Debug Mode
Enable verbose logging in workflow:

```yaml
- name: Generate PDF (Debug)
  run: rxiv pdf --verbose --debug
```

### Getting Help
1. **Check workflow logs** in Actions tab
2. **Compare with working examples** in rxiv-maker repository
3. **Ask in discussions** - [GitHub Discussions](https://github.com/henriqueslab/rxiv-maker/discussions)
4. **Report bugs** - [GitHub Issues](https://github.com/henriqueslab/rxiv-maker/issues)

---

## 🔗 Related Resources

- **[Workflow Examples](workflows/github-actions.md)** - Working configurations
- **[Testing Documentation](development/github-actions-testing.md)** - Development workflows
- **[Local Setup Guide](quick-start/installation.md)** - Local development
- **[Collaboration Guide](guides/collaboration-guide.md)** - Team writing strategies

---

**💡 Pro Tips**:
- Use draft releases for sharing PDFs with collaborators
- Set up branch protection rules for main branch
- Use GitHub's mobile app to track build status
- Schedule regular builds for long-term projects