#!/usr/bin/env python3
"""Example supplementary figure generation script for the template."""

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import os

import matplotlib.pyplot as plt
import numpy as np

# Create output directory if it doesn't exist
output_dir = "supplementary_figure"
os.makedirs(output_dir, exist_ok=True)

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
plt.savefig(f"{output_dir}/supplementary_figure.png", dpi=300, bbox_inches="tight")
plt.savefig(f"{output_dir}/supplementary_figure.pdf", bbox_inches="tight")
plt.close()

print("Supplementary figure generated successfully!")
