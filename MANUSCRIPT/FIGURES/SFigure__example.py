#!/usr/bin/env python3
"""SFigure__example: Example supplementary figure generation script for the template."""

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend

import matplotlib.pyplot as plt
import numpy as np

# Files will be saved directly to the current working directory

# Generate sample data
np.random.seed(42)
data = np.random.normal(0, 1, 1000)

# Create histogram
plt.figure(figsize=(8, 6))
plt.hist(data, bins=30, alpha=0.7, color="blue", edgecolor="black")
plt.xlabel("Value")
plt.ylabel("Frequency")
plt.title("Example Supplementary Figure")
plt.grid(True, alpha=0.3)

# Save as both PNG and PDF
plt.savefig("SFigure__example.png", dpi=300, bbox_inches="tight")
plt.savefig("SFigure__example.pdf", bbox_inches="tight")
plt.close()

print("SFigure__example generated successfully!")
