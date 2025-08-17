# Figure Positioning in Rxiv-Maker

This tutorial covers how to control figure placement and formatting in your manuscripts using Rxiv-Maker.

## Basic Figure Syntax

```markdown
![Caption text](FIGURES/Figure__name.svg)
{#fig:label tex_position="t" width="0.8\linewidth"}
```

## Positioning Options

### `tex_position` Parameter

Controls where LaTeX places your figure:

| Value | Description | Use Case |
|-------|-------------|----------|
| `"t"` | Top of page | Most common, places figure at top |
| `"b"` | Bottom of page | When you want figure at bottom |
| `"h"` | Here (approximately) | Place figure near the text |
| `"H"` | Here (exactly) | Force exact placement (requires `float` package) |
| `"p"` | Dedicated page | For large figures that need their own page |
| `"ht"` | Top or here | LaTeX chooses best between top/here |
| `"!t"` | Force top | Override LaTeX's spacing rules |

**Example:**
```markdown
![System architecture](FIGURES/Figure__architecture.svg)
{#fig:architecture tex_position="t" width="0.9\linewidth"}
```

## Width Control

### Single Column Figures

```markdown
# Standard width (recommended)
{#fig:example width="0.8\linewidth"}

# Full column width  
{#fig:example width="\linewidth"}

# Specific size
{#fig:example width="10cm"}
```

### Two-Column Spanning Figures

For figures that should span both columns in a two-column layout:

```markdown
![Wide figure caption](FIGURES/Figure__workflow.svg)
{#fig:workflow width="\textwidth" tex_position="t"}
```

**Note:** `width="\textwidth"` automatically creates a `figure*` environment for two-column spanning.

## Panel References

Reference figure panels without unwanted spaces:

```markdown
As shown in @fig:results A, the data indicates...
```

**Renders as:** Fig. 1A (no space between number and letter)

## Common Positioning Patterns

### 1. Standard Figure (Most Common)
```markdown
![Your caption here](FIGURES/Figure__results.svg)
{#fig:results tex_position="t" width="0.8\linewidth"}
```

### 2. Full-Width Figure (Two-Column Documents)
```markdown
![Complex workflow diagram](FIGURES/Figure__workflow.svg)  
{#fig:workflow width="\textwidth" tex_position="t"}
```

### 3. Small Inline Figure
```markdown
![Small diagram](FIGURES/Figure__diagram.svg)
{#fig:diagram tex_position="h" width="0.5\linewidth"}
```

### 4. Large Figure (Dedicated Page)
```markdown
![Detailed schematic](FIGURES/Figure__schematic.svg)
{#fig:schematic tex_position="p" width="\textwidth"}
```

## Figure File Organization

### Ready Figures (Recommended)
Place your figure directly in the FIGURES directory:
```
FIGURES/
├── Figure__results.png
├── Figure__workflow.svg
└── Figure__architecture.pdf
```

### Generated Figures  
For programmatically generated figures, use subdirectories:
```
FIGURES/
├── Figure__analysis.py          # Python script
├── Figure__analysis/            # Auto-generated
│   ├── Figure__analysis.png
│   └── Figure__analysis.pdf
└── Figure__plots.R              # R script
```

## Troubleshooting

### Figure Appears on Wrong Page
- Try `tex_position="!t"` to force top placement
- For large figures, use `tex_position="p"` for dedicated page

### Figure Too Large
- Reduce `width` parameter: `width="0.7\linewidth"`
- For two-column figures, ensure `width="\textwidth"`

### Spacing Issues with References
- Use `@fig:name A` for panel references (automatic spacing)
- Standard references: `@fig:name` → Fig. 1

### Figure Not Found
- Check file path: `FIGURES/Figure__name.ext`
- Ensure figure file exists and has correct extension
- For ready figures, place directly in FIGURES/ directory

## Best Practices

1. **Use descriptive figure names**: `Figure__workflow` not `Figure1`
2. **Consistent positioning**: Stick to `tex_position="t"` for most figures
3. **Appropriate widths**: 0.8\linewidth for single-column, \textwidth for spanning
4. **Panel references**: Always use `@fig:name A` format for panels
5. **File formats**: SVG for diagrams, PNG for photos, PDF for print quality

## Example Complete Figure

```markdown
![**Rxiv-Maker Workflow.** The framework separates user responsibilities 
(content creation) from automated processes (parsing, conversion, compilation). 
Users write content while the system handles technical manuscript preparation.](FIGURES/Figure__workflow.svg)
{#fig:workflow width="\textwidth" tex_position="t"}

The workflow in @fig:workflow A shows the input stage, while @fig:workflow B 
demonstrates the automated processing pipeline.
```

This creates a professional, well-positioned figure with proper panel references.