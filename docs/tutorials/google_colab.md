# Google Colab Tutorial for Rxiv-Maker

## Quick Start Guide

Google Colab provides the easiest way to use Rxiv-Maker without any local installation. Simply click the image below to get started:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://githubtocolab.com/HenriquesLab/rxiv-maker/blob/main/notebooks/rxiv_maker_colab.ipynb)

## Step-by-Step Instructions

1. **Open the Colab notebook** by clicking the badge above
2. **Connect to runtime** by clicking "Connect" in the top-right corner
3. **Run the setup cells** to install LaTeX and dependencies
4. **Upload your manuscript files** or modify the example manuscript
5. **Run the build cell** to generate your PDF
6. **Download your PDF** when the build completes

## Uploading Your Manuscript Files

### Option A: Use Colab Runtime
1. Run the cells until you clone the repository.
2. Use the file browser on the left to upload your manuscript files directly into the folder corresponding to the `MANUSCRIPT_NAME` variable in the notebook.
3. Continue with the notebook to build your PDF.
4. Download the desired files:
   - Your PDF file
   - Your text files
   - A Zip containing all generated files

### Option B: Use Google Drive
1. Mount your Google Drive in the Colab notebook by selecting the Google Drive option.
2. Make sure your Google Drive has a folder with the selected `MANUSCRIPT_NAME`.
3. The notebook will automatically use the files from your Google Drive folder.

## Updating Your Own Manuscript

To update your manuscript:

1. Upload your manuscript folder to Colab or your Google Drive
2. Update the `MANUSCRIPT_NAME` variable in the notebook
3. Ensure your manuscript has the required files:
   - `00_CONFIG.yml` - Paper metadata
   - `01_MAIN.md` - Main content
   - `03_REFERENCES.bib` - Bibliography
   - `FIGURES/` - Figure scripts and data

## Editing Your Manuscript
You can edit your manuscript files locally by downloading them from Colab or directly working on them in your Google Drive. The recommended way to edit is to use a text editor like VSCode, which supports Markdown and LaTeX syntax.  
Once you are happy with your changes, upload the updated files back to Colab or Google Drive and run the notebook cells to compile the LaTeX files and generate a Rxiv PDF.

## Benefits of Using Colab

- ✅ **No installation required** - Works in any web browser
- ✅ **Free LaTeX environment** - No need to install LaTeX locally
- ✅ **Easy sharing** - Share notebooks with collaborators
- ✅ **GPU acceleration** available for complex figure generation
- ✅ **Cloud storage** - Save your work to Google Drive

For detailed troubleshooting and advanced features, see the main [User Guide](../user_guide.md).
