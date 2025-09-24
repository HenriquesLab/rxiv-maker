#!/usr/bin/env python3
"""
Performance comparison figure for intermediate guide example.
"""

import matplotlib.pyplot as plt

# Performance data for different writing systems
systems = ["Traditional\nLaTeX", "Overleaf", "Word", "Rxiv-Maker"]
setup_time = [120, 15, 5, 10]  # minutes
writing_speed = [60, 75, 90, 95]  # words per minute effective
formatting_time = [180, 60, 90, 5]  # minutes for formatting
revision_efficiency = [40, 65, 70, 90]  # percentage

# Create subplots
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

# Setup Time
bars1 = ax1.bar(systems, setup_time, color=["#ff7f7f", "#7fbfff", "#7fff7f", "#ffbf7f"])
ax1.set_title("A. Initial Setup Time")
ax1.set_ylabel("Time (minutes)")
for bar, value in zip(bars1, setup_time, strict=False):
    ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2, f"{value}", ha="center", va="bottom")

# Writing Speed
bars2 = ax2.bar(systems, writing_speed, color=["#ff7f7f", "#7fbfff", "#7fff7f", "#ffbf7f"])
ax2.set_title("B. Effective Writing Speed")
ax2.set_ylabel("Words per minute")
for bar, value in zip(bars2, writing_speed, strict=False):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, f"{value}", ha="center", va="bottom")

# Formatting Time
bars3 = ax3.bar(systems, formatting_time, color=["#ff7f7f", "#7fbfff", "#7fff7f", "#ffbf7f"])
ax3.set_title("C. Formatting & Layout Time")
ax3.set_ylabel("Time (minutes)")
for bar, value in zip(bars3, formatting_time, strict=False):
    ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3, f"{value}", ha="center", va="bottom")

# Revision Efficiency
bars4 = ax4.bar(systems, revision_efficiency, color=["#ff7f7f", "#7fbfff", "#7fff7f", "#ffbf7f"])
ax4.set_title("D. Revision Efficiency")
ax4.set_ylabel("Efficiency (%)")
ax4.set_ylim(0, 100)
for bar, value in zip(bars4, revision_efficiency, strict=False):
    ax4.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, f"{value}%", ha="center", va="bottom")

plt.suptitle("Performance Comparison Across Different Writing Systems", fontsize=16, fontweight="bold", y=0.98)
plt.tight_layout()
plt.subplots_adjust(top=0.93)

plt.savefig("docs/quick-start/FIGURES/performance_comparison.pdf", dpi=300, bbox_inches="tight")
plt.savefig("docs/quick-start/FIGURES/performance_comparison.png", dpi=300, bbox_inches="tight")

print("Performance comparison figure generated")
