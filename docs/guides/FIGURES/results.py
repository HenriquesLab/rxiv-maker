# Example Figure Script - Results Analysis
# This is a placeholder file for documentation examples

import matplotlib.pyplot as plt
import numpy as np

# Generate example data
x = np.linspace(0, 10, 100)
y = np.sin(x)

# Create figure
plt.figure(figsize=(8, 6))
plt.plot(x, y)
plt.title("Example Results")
plt.xlabel("X axis")
plt.ylabel("Y axis")
plt.savefig("results.png", dpi=300, bbox_inches="tight")
plt.show()
