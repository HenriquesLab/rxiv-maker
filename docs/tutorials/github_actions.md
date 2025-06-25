# GitHub Actions Tutorial for RXiv-Maker

## Overview

GitHub Actions provides automated PDF generation for RXiv-Maker manuscripts. Every time you push changes or manually trigger a build, GitHub automatically generates your PDF and makes it available for download.

## Quick Setup (5 Minutes)

### Step 1: Fork the Repository
1. Go to [https://github.com/henriqueslab/rxiv-maker](https://github.com/henriqueslab/rxiv-maker)
2. Click the **"Fork"** button in the top-right corner
3. Choose your GitHub account as the destination

### Step 2: Add Your Manuscript
1. Navigate to your forked repository
2. Edit files directly in GitHub's web interface or clone locally
3. Modify the manuscript in the `MANUSCRIPT/` folder:
   - Edit `MANUSCRIPT/00_CONFIG.yml` with your paper details
   - Write your content in `MANUSCRIPT/01_MAIN.md`
   - Add references to `MANUSCRIPT/03_REFERENCES.bib`
   - Add figures to `MANUSCRIPT/FIGURES/`

### Step 3: Generate PDF
**Option A: Automatic on Push**
1. Make any change to your manuscript
2. Commit and push to the main branch
3. PDF generation starts automatically

**Option B: Manual Trigger**
1. Go to the **"Actions"** tab in your repository
2. Click **"Build and Release PDF"** workflow
3. Click **"Run workflow"**
4. Select manuscript path and click **"Run workflow"**

### Step 4: Download Your PDF
1. Go to the **"Actions"** tab
2. Click on the latest workflow run
3. Scroll down to **"Artifacts"** section
4. Download the generated PDF

## Benefits of GitHub Actions

- ✅ **Automated builds** on every commit
- ✅ **Version control** for your manuscripts
- ✅ **Team collaboration** with shared repositories
- ✅ **No local setup** required
- ✅ **Free for public repositories**
- ✅ **Works with private repositories**

## Advanced Features

### Multiple Manuscripts
Work with different manuscript folders:
1. Use manual trigger with custom `MANUSCRIPT_PATH`
2. Set up separate branches for different projects

### Team Collaboration
1. **Authors** push changes to feature branches
2. **Pull requests** trigger automatic PDF generation
3. **Reviewers** download PDFs from PR Actions
4. **Team lead** merges approved changes

### Troubleshooting
- **Build failed**: Check the workflow logs in the Actions tab
- **No artifacts**: Ensure the build completed successfully
- **Permission errors**: Verify Actions are enabled in repository settings

For detailed troubleshooting and advanced workflows, see the [GitHub Actions Guide](../github-actions-guide.md) and [User Guide](../user_guide.md).