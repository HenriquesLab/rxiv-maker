#!/usr/bin/env python3
"""Example figure script for rxiv-maker."""

import matplotlib.pyplot as plt
import numpy as np

# Generate example data
x = np.linspace(0, 2 * np.pi, 100)
y = np.sin(x)

# Create the plot
plt.figure(figsize=(8, 6))
plt.plot(x, y, "b-", linewidth=2, label="sin(x)")
plt.xlabel("x")
plt.ylabel("y")
plt.title("Example Figure")
plt.legend()
plt.grid(True, alpha=0.3)

# Save the figure directly (rxiv-maker handles the directory)
plt.tight_layout()
plt.savefig("Figure__example.png", dpi=300, bbox_inches="tight")
plt.close()

print("✅ Example figure generated successfully!")
