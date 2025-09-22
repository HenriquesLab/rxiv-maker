# Example Figure Script - Analysis
# This is a placeholder file for documentation examples

import matplotlib.pyplot as plt
import numpy as np

# Generate example analysis data
np.random.seed(42)
data = np.random.normal(0, 1, 1000)

# Create analysis figure
plt.figure(figsize=(10, 6))
plt.hist(data, bins=30, alpha=0.7, edgecolor="black")
plt.title("Example Data Analysis")
plt.xlabel("Values")
plt.ylabel("Frequency")
plt.savefig("analysis.png", dpi=300, bbox_inches="tight")
plt.show()
