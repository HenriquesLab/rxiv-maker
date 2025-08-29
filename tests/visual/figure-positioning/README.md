# Figure Positioning Visual Test Manuscript

This test manuscript demonstrates comprehensive figure positioning options in Rxiv-Maker, including solutions to issues reported by users like Guillaume.

**Note:** This is a **visual test manuscript** located in `tests/visual/` and is primarily used for automated testing of figure positioning functionality. For user-facing examples, see `docs/examples/`.

## What This Example Covers

### Figure Positioning Options
- `tex_position="t"` - Top of page (recommended default)
- `tex_position="b"` - Bottom of page  
- `tex_position="h"` - Here (approximately)
- `tex_position="H"` - Here (exactly, requires float package)
- `tex_position="p"` - Dedicated page
- `tex_position="!t"` - Force top (override spacing rules)
- `tex_position="ht"` - Top or here (flexible)

### Width Specifications
- Default: `\linewidth` (single column width)
- `width="\textwidth"` - Full text width (triggers two-column spanning)
- `width="0.8"` - 80% of line width
- `width="90%"` - Percentage values (converted to decimal)
- `width="0.9\textwidth"` - Explicit textwidth fraction

### Two-Column Layout
- Auto-detection for `width="\textwidth"` 
- Manual control with `span="2col"` or `twocolumn="true"`
- Enhanced caption formatting for wide figures

### Resolved Issues (Guillaume's Reports)
- Ready figures load from single `FIGURES/` directory
- Panel references without spaces: `(@fig:test A)` → `(Fig. 1A)`
- `tex_position="p"` works with all width specifications
- Dedicated page figures use `figure` environment, not `figure*`

### New Features
- {{blindtext}} commands for placeholder text
- {{Blindtext}} for paragraph-level placeholder text
- {{py: code}} commands for Python code execution
- {py: code} commands for inline Python calculations
- Extensible command system for future R execution

## Running This Visual Test

```bash
# Generate the visual test manuscript
rxiv pdf tests/visual/figure-positioning

# Or from within the directory
cd tests/visual/figure-positioning
rxiv pdf .
```

**Automated Testing:**
This manuscript is used in automated visual testing via:
- `tests/e2e/test_visual_manuscripts.py` - End-to-end visual feature testing
- `tests/regression/test_guillaume_issues.py` - Regression testing for reported issues

## Files Structure

```
figure-positioning-examples/
├── 00_CONFIG.yml           # Manuscript configuration
├── 01_MAIN.md              # Main content with all examples
├── README.md               # This file
└── FIGURES/
    ├── ReadyFig.py         # Script to generate ready figure
    ├── ReadyFig.png        # Ready figure (direct in FIGURES/)
    └── Figure__positioning_test.py  # Generated figure script
```

## Key Learning Points

### Ready vs Generated Figures

**Ready Figures**: Place directly in `FIGURES/filename.ext`
- Example: `FIGURES/ReadyFig.png`
- LaTeX path: `Figures/ReadyFig.png` (direct)
- No subdirectory required

**Generated Figures**: Use `Figure__name.py` naming convention
- Example: `FIGURES/Figure__positioning_test.py`
- Output: `FIGURES/Figure__positioning_test/Figure__positioning_test.png`
- LaTeX path: `Figures/Figure__positioning_test/Figure__positioning_test.png`

### Figure Environment Selection

| Width | Position | Environment | Use Case |
|-------|----------|-------------|----------|
| `\linewidth` | any | `figure` | Standard single-column |
| `\textwidth` | `p` | `figure` | Dedicated page full-width |
| `\textwidth` | other | `figure*` | Two-column spanning |
| `0.8`, `90%` | `p` | `figure` | Dedicated page custom width |
| `0.8`, `90%` | other | `figure` | Single-column custom width |

### Panel References

Correct syntax for panel references:
```markdown
(@fig:figureid A)  →  (Fig. 1A)
(@fig:figureid B)  →  (Fig. 1B)
@fig:figureid A    →  Fig. 1A (without parentheses)
```

### Blindtext Commands

```markdown
{{blindtext}}  →  \blindtext  (short placeholder text)
{{Blindtext}}  →  \Blindtext  (paragraph placeholder text)
```

### Python Execution Commands

```markdown
{py: 2 + 3}                    →  5 (inline calculation)
{py: sum(range(1, 11))}        →  55 (inline expression)

{{py:                          →  Code block with output
data = [1, 2, 3, 4, 5]
print(f"Mean: {sum(data)/len(data)}")
}}
```

**Security Features:**
- Sandboxed execution with subprocess isolation
- Whitelist-based import restrictions
- Timeout protection (10 seconds default)
- No file system access outside working directory
- Error handling with graceful degradation

This example serves as a comprehensive reference for implementing complex figure layouts, dynamic content generation, and resolves all known positioning issues.