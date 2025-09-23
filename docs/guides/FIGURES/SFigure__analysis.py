#!/usr/bin/env python3
"""
Statistical analysis figure for documentation example.

Generates supplementary figure showing data analysis results.
"""

import matplotlib.pyplot as plt
import numpy as np

# Example statistical analysis
np.random.seed(42)
x = np.random.normal(100, 15, 150)
y = x * 0.8 + np.random.normal(0, 10, 150)

# Create figure
plt.figure(figsize=(8, 6))
plt.scatter(x, y, alpha=0.6)
plt.xlabel("Variable A")
plt.ylabel("Variable B")
plt.title("Data Analysis Results\nCorrelation between Variables A and B (n=150, p<0.001)")

# Add correlation line
z = np.polyfit(x, y, 1)
p = np.poly1d(z)
plt.plot(x, p(x), "r--", alpha=0.8)

plt.grid(True, alpha=0.3)
plt.tight_layout()

# Save figure
plt.savefig("docs/guides/FIGURES/SFigure__analysis.pdf", dpi=300, bbox_inches="tight")
plt.savefig("docs/guides/FIGURES/SFigure__analysis.png", dpi=300, bbox_inches="tight")

print("Statistical analysis figure generated successfully")
