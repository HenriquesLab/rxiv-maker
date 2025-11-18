# Methods Placement Test

This test manuscript verifies the `methods_placement` configuration option introduced in rxiv-maker v1.11.1.

## Test Configuration

**Config**: `methods_placement: 2` (numeric value, maps to `"after_results"`)

## Expected Behavior

When using `methods_placement: 2` (maps to `"after_results"`), the Methods section should appear after the Results section, before Discussion.

## Test Verification

### Section Ordering
The manuscript sections should appear in this order:

1. **Introduction**
2. **Results**
3. **Methods** ← Appears after Results, before Discussion
4. **Discussion**
5. **Conclusions**
6. **Bibliography**

### What This Tests

- ✅ Numeric value mapping (2 → "after_results")
- ✅ Methods section appears after Results
- ✅ Methods appears before Discussion
- ✅ Methods is NOT inline (not between Introduction and Results)
- ✅ Methods is NOT after Bibliography
- ✅ Placeholders correctly replaced (`<PY-RPL:METHODS-AFTER-RESULTS>` contains Methods content)

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
\section*{Results}
\section*{Methods}
\section*{Discussion}
\section*{Conclusions}
\section*{Bibliography}
```

## Related Tests

To test other placement options, modify `00_CONFIG.yml`:

- **Inline** (default): `methods_placement: "inline"` or `methods_placement: 1`
  - Expected: Introduction → Methods → Results → Discussion

- **After Results** (current test): `methods_placement: "after_results"` or `methods_placement: 2`
  - Expected: Introduction → Results → Methods → Discussion

- **After Bibliography**: `methods_placement: "after_bibliography"` or `methods_placement: 3`
  - Expected: Introduction → Results → Discussion → Conclusions → Bibliography → Methods

### Numeric Value Mapping
- `1` → `"inline"`
- `2` → `"after_results"`
- `3` → `"after_bibliography"`

## Version

Introduced in: **v1.11.1**

Breaking change from: `methods_after_bibliography` boolean (v1.11.0)
