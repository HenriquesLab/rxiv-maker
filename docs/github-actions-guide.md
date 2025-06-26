# GitHub Actions Guide for Rxiv-Maker

This guide provides step-by-step instructions for using GitHub Actions to automatically generate PDFs from your manuscripts.

## 🎯 Quick Start

The fastest way to generate a PDF using GitHub Actions:

1. **Fork or clone** this repository to your GitHub account
2. **Add your manuscript** files to the `MANUSCRIPT/` directory
3. **Go to Actions tab** in your GitHub repository
4. **Click "Run workflow"** button
5. **Download your PDF** from the run results

## 📋 Table of Contents

- [How GitHub Actions Works](#how-github-actions-works)
- [Manual PDF Generation](#manual-pdf-generation)
- [Automatic PDF Generation](#automatic-pdf-generation)
- [Configuration Options](#configuration-options)
- [Download Your PDFs](#download-your-pdfs)
- [Multiple Manuscripts](#multiple-manuscripts)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

---

## 🔧 How GitHub Actions Works

Rxiv-Maker uses GitHub Actions to automatically:
- Install LaTeX and Python dependencies
- Generate figures from your Python/Mermaid scripts
- Convert Markdown to LaTeX and compile to PDF
- Create releases with downloadable PDFs

### When PDFs are Generated

The workflow triggers in two ways:

1. **Manual Trigger** (Recommended for beginners):
   - Go to Actions tab → "Build and Release PDF" → "Run workflow"
   - Choose manuscript path and click "Run workflow"

2. **Automatic Trigger** (For advanced users):
   - When you push a **git tag** (e.g., `v1.0.0`)
   - Uses `.env` file configuration or defaults to `EXAMPLE_MANUSCRIPT`

---

## 🚀 Manual PDF Generation

### Step 1: Access GitHub Actions

1. Go to your repository on GitHub
2. Click the **"Actions"** tab at the top
3. You'll see "Build and Release PDF" workflow

### Step 2: Trigger the Workflow

1. Click on **"Build and Release PDF"**
2. Click the **"Run workflow"** button (gray button on the right)
3. A form will appear with options:
   - **Use workflow from**: Choose `main` (default)
   - **Path to manuscript directory**: Enter your manuscript path
     - Use `MANUSCRIPT` for your main manuscript
     - Use `EXAMPLE_MANUSCRIPT` to test with the example
     - Use custom path like `MY_PAPER` if you have multiple manuscripts

### Step 3: Start the Build

1. Click the green **"Run workflow"** button
2. The workflow will start running (you'll see a yellow circle)
3. Wait for completion (usually 2-5 minutes)

### Step 4: Check Results

1. Click on the running workflow to see progress
2. Green checkmark = success ✅
3. Red X = failure ❌ (see [Troubleshooting](#troubleshooting))

---

## ⚡ Automatic PDF Generation

For advanced users who want automatic PDF generation:

### Method 1: Using Git Tags

```bash
# Create and push a tag to trigger PDF generation
git tag v1.0.0
git push origin v1.0.0
```

### Method 2: Using .env File

Create a `.env` file in your repository root:

```bash
# .env file
MANUSCRIPT_PATH=MANUSCRIPT
```

Then push a tag:
```bash
git tag v1.0.1
git push origin v1.0.1
```

---

## 📥 Download Your PDFs

After successful build, you can download PDFs in two ways:

### Option 1: From Actions Tab (Artifacts)

1. Go to **Actions** tab
2. Click on your completed workflow run
3. Scroll down to **"Artifacts"** section
4. Click **"generated-pdf"** to download

### Option 2: From Releases (Permanent Links)

1. Go to **"Releases"** section (right side of repository)
2. Find your release (created automatically)
3. Download PDF from **"Assets"** section

**💡 Pro Tip**: Release downloads are permanent and have direct URLs!

---

## 🎛️ Configuration Options

### Manuscript Path Options

| Path | Description | Use Case |
|------|-------------|----------|
| `MANUSCRIPT` | Default manuscript directory | Your main paper |
| `EXAMPLE_MANUSCRIPT` | Example provided with Rxiv-Maker | Testing/learning |
| `MY_PAPER` | Custom directory name | Multiple manuscripts |
| `PROJECT_A` | Another custom directory | Multiple projects |

### Environment Variables

Create a `.env` file in your repository root:

```bash
# .env file - used for automatic builds
MANUSCRIPT_PATH=MANUSCRIPT
FORCE_FIGURES=false
```

### Workflow Inputs

When running manually, you can specify:
- **manuscript_path**: Which directory contains your manuscript
- Defaults to `MANUSCRIPT` if not specified

---

## 📚 Multiple Manuscripts

You can manage multiple manuscripts in one repository:

### Directory Structure
```
your-repo/
├── MANUSCRIPT/           # Main manuscript
├── PROJECT_A/           # First project
├── PROJECT_B/           # Second project
├── EXAMPLE_MANUSCRIPT/  # Keep as reference
└── .env                 # Default configuration
```

### Generate PDFs for Different Projects

1. **Manually**: Use "Run workflow" with different manuscript paths
2. **Automatically**: 
   - Change `.env` file to point to desired manuscript
   - Push a new tag

---

## 🔍 Troubleshooting

### Common Issues and Solutions

#### ❌ "Workflow failed" - No PDF generated

**Problem**: The workflow runs but fails to generate PDF

**Solutions**:
1. **Run validation first**: Use `make validate` locally to catch issues before pushing
2. **Check manuscript path**: Ensure the directory exists and has required files
3. **Verify file structure**: Must have `00_CONFIG.yml` and `01_MAIN.md`
4. **Check Python scripts**: Ensure figure generation scripts are valid
5. **Review workflow logs**: Click on failed workflow → click on "build-pdf" job → check red X steps

#### ❌ "LaTeX compilation failed"

**Problem**: LaTeX cannot compile your document

**Solutions**:
1. **Check LaTeX syntax**: Ensure your Markdown converts to valid LaTeX
2. **Verify citations**: Check `03_REFERENCES.bib` file syntax
3. **Review special characters**: Some characters need escaping
4. **Check figure references**: Ensure all referenced figures exist

#### ❌ "Figure generation failed"

**Problem**: Python or Mermaid figures cannot be generated

**Solutions**:
1. **Check Python scripts**: Ensure scripts can run without errors
2. **Verify data files**: Check that data files exist in `FIGURES/DATA/`
3. **Review imports**: Ensure all required packages are in `pyproject.toml`
4. **Check file paths**: Use relative paths within the FIGURES directory

#### ❌ "Permission denied" or "File not found"

**Problem**: Workflow cannot access files or directories

**Solutions**:
1. **Check repository permissions**: Ensure Actions are enabled
2. **Verify file names**: Check exact spelling and case
3. **Check .gitignore**: Ensure manuscript files aren't ignored
4. **Verify branch**: Ensure you're working on the correct branch

### Debug Steps

1. **Check workflow logs**:
   - Actions tab → Click on failed run → Click on "build-pdf" → Expand red X steps

2. **Test locally first**:
   ```bash
   make validate MANUSCRIPT_PATH=your_manuscript  # Check for issues first
   make pdf MANUSCRIPT_PATH=your_manuscript       # Then generate PDF
   ```

3. **Use example manuscript**:
   - Try with `EXAMPLE_MANUSCRIPT` first to ensure workflow works

4. **Run validation locally**:
   ```bash
   # Quick validation check
   make validate MANUSCRIPT_PATH=MANUSCRIPT
   
   # Detailed validation with suggestions
   python src/py/scripts/validate_manuscript.py --detailed MANUSCRIPT
   ```

5. **Check file structure**:
   ```bash
   ls -la MANUSCRIPT/
   # Should show: 00_CONFIG.yml, 01_MAIN.md, FIGURES/, etc.
   ```

---

## 🏆 Advanced Usage

### Custom Workflow Triggers

You can modify `.github/workflows/build-pdf.yml` to add more triggers:

```yaml
on:
  push:
    branches: [ main ]  # Trigger on every push to main
    tags: [ 'v*' ]      # Trigger on version tags
  pull_request:         # Trigger on pull requests
  workflow_dispatch:    # Manual trigger
```

### Multiple Manuscript Builds

Build multiple manuscripts in one workflow:

```yaml
strategy:
  matrix:
    manuscript: [MANUSCRIPT, PROJECT_A, PROJECT_B]
```

### Scheduled Builds

Run builds on a schedule:

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
```

### Custom Build Commands

Override default build commands:

```yaml
- name: Custom build
  run: |
    export CUSTOM_OPTION=true
    make pdf MANUSCRIPT_PATH=${{ matrix.manuscript }}
```

---

## 🔗 Quick Reference

### Essential Commands

| Action | Command |
|--------|---------|
| Manual trigger | Actions tab → "Run workflow" |
| Download PDF | Actions tab → Completed run → "Artifacts" |
| Permanent link | Releases → Download from "Assets" |
| Test locally | `make validate && make pdf MANUSCRIPT_PATH=MANUSCRIPT` |
| Check logs | Actions → Failed run → "build-pdf" job |
| Validate manuscript | `make validate MANUSCRIPT_PATH=MANUSCRIPT` |

### File Locations

| File | Purpose |
|------|---------|
| `.github/workflows/build-pdf.yml` | GitHub Actions workflow |
| `.env` | Environment variables |
| `MANUSCRIPT/00_CONFIG.yml` | Manuscript configuration |
| `MANUSCRIPT/01_MAIN.md` | Main manuscript content |
| `MANUSCRIPT/FIGURES/` | Figure generation scripts |

### URLs to Remember

- **Actions tab**: `https://github.com/YOUR_USERNAME/YOUR_REPO/actions`
- **Releases**: `https://github.com/YOUR_USERNAME/YOUR_REPO/releases`
- **Workflow file**: `https://github.com/YOUR_USERNAME/YOUR_REPO/blob/main/.github/workflows/build-pdf.yml`

---

## 💡 Best Practices

1. **Start with manual triggers** until you're comfortable
2. **Test with EXAMPLE_MANUSCRIPT** first
3. **Always validate locally** before pushing (`make validate`)
4. **Keep manuscript files organized** in dedicated directories
5. **Use descriptive tag names** like `v1.0.0`, `draft-2024-01-15`
6. **Check builds regularly** to catch issues early
7. **Use meaningful commit messages** for easier debugging

---

## 📞 Getting Help

If you encounter issues:

1. **Check this guide** first
2. **Review workflow logs** for specific error messages
3. **Test locally** with `make pdf`
4. **Search existing issues**: [GitHub Issues](https://github.com/henriqueslab/rxiv-maker/issues)
5. **Create new issue** with workflow logs and error details

---

*This guide is part of the Rxiv-Maker documentation. For more information, see the [main README](../README.md) and [User Guide](user_guide.md).*