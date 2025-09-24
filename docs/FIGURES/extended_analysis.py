#!/usr/bin/env python3
"""
Extended analysis figure for intermediate guide example.
"""

import matplotlib.pyplot as plt
import numpy as np

# Extended performance analysis
fig, ax = plt.subplots(figsize=(12, 8))

# Time series data
weeks = np.arange(1, 13)
traditional_latex = [100, 95, 90, 85, 82, 80, 78, 76, 74, 72, 70, 68]
overleaf = [100, 90, 85, 82, 80, 78, 76, 75, 74, 73, 72, 71]
rxiv_maker = [100, 85, 75, 65, 55, 50, 45, 42, 40, 38, 36, 35]

# Plot lines
ax.plot(weeks, traditional_latex, "o-", label="Traditional LaTeX", linewidth=3, markersize=8)
ax.plot(weeks, overleaf, "s-", label="Overleaf", linewidth=3, markersize=8)
ax.plot(weeks, rxiv_maker, "^-", label="Rxiv-Maker", linewidth=3, markersize=8)

# Customize plot
ax.set_xlabel("Weeks of Experience", fontsize=12)
ax.set_ylabel("Time to Complete Manuscript (hours)", fontsize=12)
ax.set_title("Extended Performance Analysis\nLearning Curve Comparison Over Time", fontsize=14, fontweight="bold")
ax.legend(fontsize=12, loc="upper right")
ax.grid(True, alpha=0.3)
ax.set_xlim(1, 12)
ax.set_ylim(30, 105)

# Add annotations
ax.annotate(
    "Steepest learning curve",
    xy=(8, 42),
    xytext=(6, 60),
    arrowprops={"arrowstyle": "->", "lw": 1.5, "color": "red"},
    fontsize=10,
    ha="center",
)

ax.annotate(
    "Minimal improvement",
    xy=(10, 72),
    xytext=(8, 85),
    arrowprops={"arrowstyle": "->", "lw": 1.5, "color": "blue"},
    fontsize=10,
    ha="center",
)

plt.tight_layout()
plt.savefig("docs/quick-start/FIGURES/extended_analysis.pdf", dpi=300, bbox_inches="tight")
plt.savefig("docs/quick-start/FIGURES/extended_analysis.png", dpi=300, bbox_inches="tight")

print("Extended analysis figure generated")
