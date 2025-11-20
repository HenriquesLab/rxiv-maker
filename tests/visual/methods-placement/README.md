# Methods Placement Test

This test manuscript verifies the `methods_placement` configuration option in rxiv-maker v1.12.1.

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
- ✅ Methods is NOT after Introduction
- ✅ Methods is NOT after Discussion
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

- **After Introduction**: `methods_placement: "after_intro"` or `methods_placement: 1`
  - Expected: Introduction → Methods → Results → Discussion (classic paper style)

- **After Results** (current test): `methods_placement: "after_results"` or `methods_placement: 2`
  - Expected: Introduction → Results → Methods → Discussion

- **After Discussion**: `methods_placement: "after_discussion"` or `methods_placement: 3`
  - Expected: Introduction → Results → Discussion → Methods → Conclusions → Bibliography

- **After Bibliography** (default): `methods_placement: "after_bibliography"` or `methods_placement: 4`
  - Expected: Introduction → Results → Discussion → Conclusions → Bibliography → Methods (Nature Methods style)

### Numeric Value Mapping
- `1` → `"after_intro"` (after Introduction)
- `2` → `"after_results"` (after Results)
- `3` → `"after_discussion"` (after Discussion)
- `4` → `"after_bibliography"` (after Bibliography - **default**)

## Version

**v1.12.1** (BREAKING CHANGE from v1.12.0)
- Removed "inline" option (not working reliably)
- New numeric mapping: 1-4 (was 1-5 in v1.12.0)
- 4 placement options (was 5 in v1.12.0)
- Numeric values shifted down by 1 for most users

**v1.12.0** (BREAKING CHANGE)
- Redesigned with 5 options including "inline"
- New numeric mapping (1-5 instead of 1-3)
- New default: `"after_bibliography"` (was `"inline"`)
- New options: `"after_intro"` and `"after_discussion"`

Previous versions:
- Introduced in: **v1.11.1**
- Breaking change from: `methods_after_bibliography` boolean (v1.11.0)
