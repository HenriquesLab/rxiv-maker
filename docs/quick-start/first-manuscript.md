# Your First Manuscript: 5-Minute Walkthrough

Get from zero to your first scientific PDF in 5 minutes.

## Prerequisites

- Python 3.11+ installed
- 5 minutes of your time

## Step 1: Install Rxiv-Maker (30 seconds)

```bash
pip install rxiv-maker
```

**✅ Success Check**: Run `rxiv --version` - you should see version information.

## Step 2: Create Your First Manuscript (1 minute)

```bash
# Create a new manuscript project
rxiv init my-first-paper
cd my-first-paper
```

**✅ Success Check**: You should see these files created:
- `00_CONFIG.yml` - Manuscript metadata
- `01_MAIN.md` - Your manuscript content
- `03_REFERENCES.bib` - Bibliography file
- `FIGURES/` - Directory for figure scripts

## Step 3: Write Some Content (2 minutes)

Open `01_MAIN.md` and replace the content with:

```markdown
# A Revolutionary Discovery

## Abstract

This paper demonstrates the incredible power of Rxiv-Maker for scientific writing.

## Introduction

Scientific writing has never been easier. With Rxiv-Maker, you can:

- Write in **Markdown** instead of LaTeX
- Generate figures automatically from Python scripts
- Manage citations effortlessly
- Collaborate using Git

## Methods

We used Rxiv-Maker version 1.8+ to generate this manuscript.

## Results

The results were amazing! See @fig:example for details.

![Example Figure](FIGURES/example.py){#fig:example width="0.8\\textwidth"}

## Conclusion

Rxiv-Maker transforms scientific writing from chaos to clarity.

## References

Research shows this approach works [@smith2023].
```

Add this to your `03_REFERENCES.bib`:

```bibtex
@article{smith2023,
  title={The Future of Scientific Writing},
  author={Smith, Jane},
  journal={Nature},
  year={2023}
}
```

## Step 4: Create a Simple Figure (1 minute)

Create `FIGURES/example.py`:

```python
import matplotlib.pyplot as plt
import numpy as np

# Generate sample data
x = np.linspace(0, 10, 100)
y = np.sin(x)

# Create the plot
plt.figure(figsize=(8, 6))
plt.plot(x, y, 'b-', linewidth=2, label='sin(x)')
plt.xlabel('x')
plt.ylabel('y')
plt.title('Example Scientific Figure')
plt.legend()
plt.grid(True, alpha=0.3)

# Save the figure
plt.savefig('example.png', dpi=300, bbox_inches='tight')
plt.close()
```

## Step 5: Generate Your PDF (30 seconds)

```bash
rxiv pdf
```

**✅ Success Check**: You should see:
1. Figure generation messages
2. PDF compilation progress
3. Final message: "✅ PDF generated successfully"
4. Your PDF in `output/my-first-paper.pdf`

## 🎉 Congratulations!

You've just created your first scientific manuscript with:
- Professional LaTeX formatting
- Automatically generated figures
- Proper citations and cross-references
- Publication-ready PDF output

## Next Steps (15-Minute Deep Dive)

Ready to learn more? Continue with:

1. **[Writing Guide](../guides/user_guide.md)** - Advanced Markdown features
2. **[Figures Guide](../guides/figures-guide.md)** - Complex figure positioning
3. **[Publishing Guide](../guides/publishing-guide.md)** - arXiv submission
4. **[CLI Commands](../reference/cli-commands.md)** - Complete command reference

## Troubleshooting

**PDF generation failed?**
- Run `rxiv validate` to check for issues
- See [Troubleshooting Guide](../troubleshooting/troubleshooting-missing-figures.md)

**Figure not appearing?**
- Check `FIGURES/example.py` syntax
- Run `rxiv pdf --force-figures` to regenerate

**LaTeX errors?**
- Try `rxiv pdf --engine docker` for containerized build
- Check `output/my-first-paper.log` for details

## Need Help?

- [GitHub Discussions](https://github.com/henriqueslab/rxiv-maker/discussions)
- [Troubleshooting Guides](../troubleshooting/)
- [Complete Documentation](../guides/user_guide.md)