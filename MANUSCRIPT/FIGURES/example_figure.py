#!/usr/bin/env python3
"""Example figure generation script for the template.

This script demonstrates how to create figures programmatically.
"""

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import os

import matplotlib.pyplot as plt
import numpy as np

# Create output directory if it doesn't exist
output_dir = "example_figure"
os.makedirs(output_dir, exist_ok=True)

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
plt.savefig(f"{output_dir}/example_figure.png", dpi=300, bbox_inches="tight")
plt.savefig(f"{output_dir}/example_figure.pdf", bbox_inches="tight")
plt.close()

print("Example figure generated successfully!")
