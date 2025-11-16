#!/usr/bin/env python3
"""Generate a test figure for positioning examples."""

import matplotlib.pyplot as plt
import numpy as np

# Create a simple test figure with different appearance from ReadyFig
fig, ax = plt.subplots(1, 1, figsize=(6, 4))

x = np.linspace(0, 10, 100)
y1 = np.cos(x)
y2 = np.sin(x) * 0.5

ax.plot(x, y1, "r-", linewidth=2, label="Positioning Test")
ax.plot(x, y2, "g--", linewidth=2, label="Secondary")
ax.set_xlabel("X axis")
ax.set_ylabel("Y axis")
ax.set_title("Positioning Test Figure")
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("Figure__positioning_test.png", dpi=150, bbox_inches="tight")
plt.close()

print("Generated Figure__positioning_test.png")
