# Methods Placement Test

This test manuscript verifies the `methods_placement` configuration option introduced in rxiv-maker v1.11.1.

## Test Configuration

**Config**: `methods_placement: "inline"`

## Expected Behavior

When using `methods_placement: "inline"` (the default), the Methods section should appear exactly where the author writes it in the markdown file.

## Test Verification

### Section Ordering
The manuscript sections should appear in this order:

1. **Introduction**
2. **Methods** ← Appears inline between Introduction and Results
3. **Results**
4. **Discussion**
5. **Conclusions**
6. **Bibliography**

### What This Tests

- ✅ Methods section appears in authored position (inline)
- ✅ Methods is NOT moved to after Results
- ✅ Methods is NOT moved to after Bibliography
- ✅ Section ordering matches markdown file structure
- ✅ Placeholders correctly replaced (`<PY-RPL:METHODS-AFTER-RESULTS>` and `<PY-RPL:METHODS-AFTER-BIBLIOGRAPHY>` are empty)

## How to Run

```bash
rxiv pdf tests/visual/methods-placement/
```

## View Results

```bash
open tests/visual/methods-placement/output/methods-placement.pdf
```

## Verify Section Order

```bash
grep "^\\section" tests/visual/methods-placement/output/methods-placement.tex
```

Expected output:
```
\section*{Introduction}
\section*{Methods}
\section*{Results}
\section*{Discussion}
\section*{Conclusions}
\section*{Bibliography}
```

## Related Tests

To test other placement options, modify `00_CONFIG.yml`:

- **After Results**: `methods_placement: "after_results"`
  - Expected: Introduction → Results → Methods → Discussion

- **After Bibliography**: `methods_placement: "after_bibliography"`
  - Expected: Introduction → Results → Discussion → Conclusions → Bibliography → Methods

## Version

Introduced in: **v1.11.1**

Breaking change from: `methods_after_bibliography` boolean (v1.11.0)
