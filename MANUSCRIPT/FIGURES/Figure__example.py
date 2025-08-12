#!/usr/bin/env python3
"""Figure__example: Example figure generation script for the template.

This script demonstrates how to create figures programmatically.
"""

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend

import matplotlib.pyplot as plt
import numpy as np

# Files will be saved directly to the current working directory

# Generate sample data
x = np.linspace(0, 10, 100)
y = np.sin(x) * np.exp(-x / 5)

# Create the plot
plt.figure(figsize=(8, 6))
plt.plot(x, y, linewidth=2, label="Sample data")
plt.xlabel("X values")
plt.ylabel("Y values")
plt.title("Example Figure")
plt.legend()
plt.grid(True, alpha=0.3)

# Save as both PNG and PDF
plt.savefig("Figure__example.png", dpi=300, bbox_inches="tight")
plt.savefig("Figure__example.pdf", bbox_inches="tight")
plt.close()

print("Figure__example generated successfully!")
