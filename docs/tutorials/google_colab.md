# Google Colab Tutorial for RXiv-Maker

## Quick Start Guide

Google Colab provides the easiest way to use RXiv-Maker without any local installation. Simply click the badge below to get started:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/henriqueslab/rxiv-maker/blob/main/rxiv_forge_colab.ipynb)

## Step-by-Step Instructions

1. **Open the Colab notebook** by clicking the badge above
2. **Connect to runtime** by clicking "Connect" in the top-right corner
3. **Run the setup cells** to install LaTeX and dependencies
4. **Upload your manuscript files** or modify the example manuscript
5. **Run the build cell** to generate your PDF
6. **Download your PDF** when the build completes

## Working with Your Own Manuscript

To use your own manuscript:

1. Upload your manuscript folder to Colab using the file browser
2. Update the `MANUSCRIPT_PATH` variable in the notebook
3. Ensure your manuscript has the required files:
   - `00_CONFIG.yml` - Paper metadata
   - `01_MAIN.md` - Main content
   - `03_REFERENCES.bib` - Bibliography
   - `FIGURES/` - Figure scripts and data

## Benefits of Using Colab

- ✅ **No installation required** - Works in any web browser
- ✅ **Free LaTeX environment** - No need to install LaTeX locally
- ✅ **Easy sharing** - Share notebooks with collaborators
- ✅ **GPU acceleration** available for complex figure generation
- ✅ **Cloud storage** - Save your work to Google Drive

For detailed troubleshooting and advanced features, see the main [User Guide](../user_guide.md).