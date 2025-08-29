#!/usr/bin/env python3
"""Generate a ready figure for testing figure positioning."""

import matplotlib.pyplot as plt
import numpy as np

# Create a simple test figure
fig, ax = plt.subplots(1, 1, figsize=(6, 4))

x = np.linspace(0, 10, 100)
y = np.sin(x)

ax.plot(x, y, "b-", linewidth=2, label="Ready Figure")
ax.set_xlabel("X axis")
ax.set_ylabel("Y axis")
ax.set_title("Ready Figure Example")
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("ReadyFig.png", dpi=150, bbox_inches="tight")
plt.close()

print("Generated ReadyFig.png")
