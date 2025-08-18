#!/usr/bin/env python3
"""Generate a test figure for positioning examples."""

import matplotlib.pyplot as plt
import numpy as np

# Create a comprehensive test figure
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8))

# Top left - sine wave
x = np.linspace(0, 4 * np.pi, 100)
ax1.plot(x, np.sin(x), "b-", label="sin(x)")
ax1.set_title("Sine Wave")
ax1.legend()
ax1.grid(True, alpha=0.3)

# Top right - cosine wave
ax2.plot(x, np.cos(x), "r-", label="cos(x)")
ax2.set_title("Cosine Wave")
ax2.legend()
ax2.grid(True, alpha=0.3)

# Bottom left - scatter plot
np.random.seed(42)
x_scatter = np.random.randn(50)
y_scatter = np.random.randn(50)
ax3.scatter(x_scatter, y_scatter, alpha=0.6)
ax3.set_title("Random Scatter")
ax3.grid(True, alpha=0.3)

# Bottom right - bar chart
categories = ["A", "B", "C", "D"]
values = [23, 45, 56, 78]
ax4.bar(categories, values)
ax4.set_title("Sample Bar Chart")
ax4.grid(True, alpha=0.3)

plt.suptitle("Comprehensive Positioning Test Figure", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("Figure__positioning_test.png", dpi=150, bbox_inches="tight")
plt.close()

print("Generated Figure__positioning_test.png")
