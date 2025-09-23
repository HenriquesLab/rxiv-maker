#!/usr/bin/env python3
"""
Workflow diagram for intermediate guide example.
"""

import matplotlib.patches as patches
import matplotlib.pyplot as plt

# Create workflow diagram
fig, ax = plt.subplots(figsize=(12, 8))

# Define workflow steps
steps = [
    {"name": "Write\nMarkdown", "pos": (1, 6), "color": "#e3f2fd"},
    {"name": "Create\nFigures", "pos": (1, 4), "color": "#e8f5e8"},
    {"name": "Add\nReferences", "pos": (1, 2), "color": "#fff3e0"},
    {"name": "Process\nContent", "pos": (5, 6), "color": "#f3e5f5"},
    {"name": "Generate\nLaTeX", "pos": (5, 4), "color": "#fce4ec"},
    {"name": "Compile\nPDF", "pos": (5, 2), "color": "#e0f2f1"},
    {"name": "Review\n& Publish", "pos": (9, 4), "color": "#fff8e1"},
]

# Draw workflow steps
for step in steps:
    rect = patches.FancyBboxPatch(
        (step["pos"][0] - 0.6, step["pos"][1] - 0.4),
        1.2,
        0.8,
        boxstyle="round,pad=0.1",
        facecolor=step["color"],
        edgecolor="black",
        linewidth=1.5,
    )
    ax.add_patch(rect)
    ax.text(step["pos"][0], step["pos"][1], step["name"], ha="center", va="center", fontsize=10, fontweight="bold")

# Draw arrows
arrows = [
    ((1, 5.6), (1, 4.4)),  # Write -> Create
    ((1, 3.6), (1, 2.4)),  # Create -> References
    ((1.6, 6), (4.4, 6)),  # Write -> Process
    ((1.6, 4), (4.4, 4)),  # Create -> Generate
    ((1.6, 2), (4.4, 2)),  # References -> Compile
    ((5, 5.6), (5, 4.4)),  # Process -> Generate
    ((5, 3.6), (5, 2.4)),  # Generate -> Compile
    ((5.6, 4), (8.4, 4)),  # Generate -> Review
]

for start, end in arrows:
    ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="->", lw=2, color="black"))

ax.set_xlim(0, 10)
ax.set_ylim(1, 7)
ax.set_title(
    "Experimental Workflow Diagram\nRxiv-Maker Manuscript Processing Pipeline", fontsize=14, fontweight="bold", pad=20
)
ax.axis("off")

plt.tight_layout()
plt.savefig("docs/quick-start/FIGURES/workflow_diagram.pdf", dpi=300, bbox_inches="tight")
plt.savefig("docs/quick-start/FIGURES/workflow_diagram.png", dpi=300, bbox_inches="tight")

print("Workflow diagram generated")
