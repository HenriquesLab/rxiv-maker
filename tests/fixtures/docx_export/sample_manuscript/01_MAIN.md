---
title:
  long: "Sample Manuscript for DOCX Export Testing"
  short: "DOCX Export Test"
authors:
  - name: "Test Author"
    affiliation: "Test University"
    orcid: "0000-0000-0000-0000"
keywords: ["docx", "export", "testing"]
---

# Abstract

This is a sample manuscript for testing DOCX export functionality. It includes various citation styles and formatting to validate the export process.

# Introduction

Scientific publishing requires collaboration with researchers who may not be familiar with LaTeX [@smith2021]. The DOCX export feature addresses this need by providing a familiar format for review and collaboration.

Previous studies have shown the importance of accessible manuscript formats [@jones2022; @brown2023]. Multiple citations can appear together [@wilson2020; @davis2019], and single citations can appear inline like @taylor2021.

## Background

The field has evolved significantly in recent years. Early work by @anderson2018 established the foundation, while later studies [@miller2020; @garcia2021] extended the approach.

# Methods

We implemented the export functionality using **python-docx** library [@python-docx2023]. The process involves:

- Citation extraction and mapping
- Markdown parsing and conversion
- Bibliography formatting with DOIs
- Document generation with proper styling

Code samples can be included using inline `code` or code blocks:

```python
def export_manuscript(path):
    exporter = DocxExporter(path)
    return exporter.export()
```

# Results

Our approach successfully handles various citation patterns:

1. Single citations: @smith2021
2. Multiple citations: [@jones2022; @brown2023]
3. Mixed with text: Recent work [@wilson2020] demonstrates this.

The system also preserves *italic text*, **bold text**, and other `inline formatting`.

# Discussion

This work builds on previous efforts [@anderson2018; @miller2020] to improve manuscript accessibility. Future work will extend the system to handle more complex formatting requirements.

# Conclusion

We have demonstrated a functional DOCX export system that maintains citation integrity and provides DOI footnotes for easy reference lookup.

# References
