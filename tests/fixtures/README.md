# Test Fixtures

This directory contains test manuscript fixtures for regression testing.

## GUILLAUME_TEST_MANUSCRIPT

This fixture contains a comprehensive test manuscript that validates Guillaume's reported issues and their fixes:

- **Issue #1**: Panel references should have no spaces: `(@fig:test A)` → `(Fig. 1A)`
- **Issue #2**: Ready files should use direct paths, not subdirectory structure
- **Issue #3**: Section headers like `## Introduction` should appear as "Introduction" not "Main"
- **Issue #4**: Full-page positioning with `tex_position="p"` should use `figure[p]` not `figure*[p]`

### Usage in Tests

```python
import pytest
from pathlib import Path

def test_guillaume_fixes():
    """Test Guillaume's fixes using the fixture manuscript."""
    fixture_dir = Path(__file__).parent.parent / "fixtures"
    manuscript_dir = fixture_dir
    
    # Test manuscript contains:
    # - Ready figures in FIGURES/Fig1.png, Fig2.png, etc.
    # - Panel references with Guillaume's specific formatting
    # - Introduction section (not Main)
    # - Full-page positioning examples
    
    # Run your tests here...
```

### Files Structure

```
GUILLAUME_TEST_MANUSCRIPT/
├── 00_CONFIG.yml          # Manuscript configuration
├── 01_MAIN.md             # Main manuscript with Guillaume's test cases
├── 03_REFERENCES.bib      # Bibliography
├── FIGURES/               # Ready figure files
│   ├── Fig1.png
│   ├── Fig2.png
│   ├── Fig3.png
│   └── Fig4.png
└── output/                # Generated output (if built)
    ├── GUILLAUME_TEST_MANUSCRIPT.tex
    ├── GUILLAUME_TEST_MANUSCRIPT.pdf
    └── Figures/           # Copied figures
```

This fixture can be used for regression testing, integration testing, and verifying that Guillaume's reported issues remain fixed.