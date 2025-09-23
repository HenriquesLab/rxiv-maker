#!/usr/bin/env python3
"""
Experimental analysis figure for writing guide example.
"""

import matplotlib.pyplot as plt
import numpy as np

# Generate example experimental data
np.random.seed(42)
conditions = ["Control", "Treatment A", "Treatment B", "Treatment C"]
values = [78.5, 85.2, 92.1, 88.7]
errors = [3.2, 2.8, 4.1, 3.5]

# Create figure
plt.figure(figsize=(8, 6))
bars = plt.bar(conditions, values, yerr=errors, capsize=5, color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"])

plt.ylabel("Response Rate (%)")
plt.title("Experimental Analysis Results")
plt.ylim(0, 100)

# Add value labels on bars
for bar, value in zip(bars, values, strict=False):
    plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, f"{value:.1f}%", ha="center", va="bottom")

plt.tight_layout()
plt.savefig("docs/guides/FIGURES/experimental_analysis.pdf", dpi=300, bbox_inches="tight")
plt.savefig("docs/guides/FIGURES/experimental_analysis.png", dpi=300, bbox_inches="tight")

print("Experimental analysis figure generated")
