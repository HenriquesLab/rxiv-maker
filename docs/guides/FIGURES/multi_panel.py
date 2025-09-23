#!/usr/bin/env python3
"""
Multi-panel figure for writing guide example.
"""

import matplotlib.pyplot as plt
import numpy as np

# Create multi-panel figure
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

# Panel A: Line plot
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)
ax1.plot(x, y1, label="sin(x)", color="blue")
ax1.plot(x, y2, label="cos(x)", color="red")
ax1.set_title("A. Trigonometric Functions")
ax1.set_xlabel("x")
ax1.set_ylabel("y")
ax1.legend()
ax1.grid(True, alpha=0.3)

# Panel B: Scatter plot
np.random.seed(42)
x2 = np.random.normal(50, 15, 100)
y2 = x2 * 0.8 + np.random.normal(0, 10, 100)
ax2.scatter(x2, y2, alpha=0.6, color="green")
ax2.set_title("B. Correlation Analysis")
ax2.set_xlabel("Variable X")
ax2.set_ylabel("Variable Y")

# Panel C: Bar chart
categories = ["Group 1", "Group 2", "Group 3", "Group 4"]
values = [23, 17, 35, 29]
ax3.bar(categories, values, color=["#ff9999", "#66b3ff", "#99ff99", "#ffcc99"])
ax3.set_title("C. Group Comparison")
ax3.set_ylabel("Count")

# Panel D: Histogram
data = np.random.normal(100, 15, 1000)
ax4.hist(data, bins=30, alpha=0.7, color="purple", edgecolor="black")
ax4.set_title("D. Distribution Analysis")
ax4.set_xlabel("Value")
ax4.set_ylabel("Frequency")

plt.tight_layout()
plt.savefig("docs/guides/FIGURES/multi_panel.pdf", dpi=300, bbox_inches="tight")
plt.savefig("docs/guides/FIGURES/multi_panel.png", dpi=300, bbox_inches="tight")

print("Multi-panel figure generated")
