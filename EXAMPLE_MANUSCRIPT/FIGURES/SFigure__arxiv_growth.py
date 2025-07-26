#!/usr/bin/env python3
"""SFigure__arxiv_growth: ArXiv Preprints Over Time.

Publication-ready plot showing the growth of arXiv submissions from 1991 to 2025.
Optimized for single-column format in academic preprints.
Runs in headless mode by default (no display window).
Data source: https://arxiv.org/stats/monthly_submissions.

Usage:
    python SFigure__arxiv_growth.py           # Headless mode (save files only)
    python SFigure__arxiv_growth.py --show    # Display plot and save files
    python SFigure__arxiv_growth.py --help    # Show help message
"""

import os
import sys
from pathlib import Path

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

# Set backend based on command line arguments
if "--show" not in sys.argv:
    matplotlib.use("Agg")  # Use non-interactive backend for headless operation

# Set up modern publication-quality plotting parameters
plt.rcParams.update(
    {
        "font.size": 9,
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#333333",
        "xtick.major.size": 4,
        "xtick.minor.size": 2,
        "ytick.major.size": 4,
        "ytick.minor.size": 2,
        "xtick.color": "#333333",
        "ytick.color": "#333333",
        "legend.frameon": False,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
        "text.color": "#333333",
        "axes.labelcolor": "#333333",
    }
)


def load_and_process_data():
    """Load and process the arXiv submission data."""
    # Define the path to the data file
    data_path = (
        Path(__file__).parent
        / "DATA"
        / "SFigure__arxiv_growth"
        / "arxiv_monthly_submissions.csv"
    )

    # Load the data
    df = pd.read_csv(data_path)

    # Convert month column to datetime
    df["date"] = pd.to_datetime(df["month"], format="%Y-%m")

    # Sort by date to ensure proper chronological order
    df = df.sort_values("date").reset_index(drop=True)

    return df


def create_figure():
    """Create the publication-ready figure."""
    # Load data
    df = load_and_process_data()

    # Create figure and axis with modern styling
    fig, ax = plt.subplots(figsize=(3.5, 4))
    fig.patch.set_facecolor("white")

    # Use a modern colour palette
    primary_color = "#1f77b4"  # Modern blue
    secondary_color = "#aec7e8"  # Light blue for fill

    # Plot the data with modern styling
    ax.plot(
        df["date"],
        df["submissions"],
        linewidth=1.5,
        color=primary_color,
        alpha=0.9,
        zorder=3,
    )

    # Fill area under the curve with gradient-like effect
    ax.fill_between(
        df["date"], df["submissions"], alpha=0.3, color=secondary_color, zorder=1
    )

    # Customize axes with smaller fonts for column format
    ax.set_xlabel("Year", fontsize=9, fontweight="bold")
    ax.set_ylabel("Monthly Submissions", fontsize=9, fontweight="bold")
    ax.set_title(
        "arXiv Preprint Growth (1991-2025)", fontsize=10, fontweight="bold", pad=10
    )

    # Format x-axis with fewer ticks for compact format
    ax.xaxis.set_major_locator(mdates.YearLocator(10))  # Every 10 years
    ax.xaxis.set_minor_locator(mdates.YearLocator(5))  # Every 5 years
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # Format y-axis with thousands separator and scientific notation for large numbers
    def format_thousands(x, pos):
        if x >= 1000:
            return f"{x / 1000:.0f}k"
        else:
            return f"{x:.0f}"

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_thousands))

    # Set y-axis to start from 0
    ax.set_ylim(bottom=0)

    # Add modern grid styling
    ax.grid(True, alpha=0.3, linestyle="-", linewidth=0.5, color="#E0E0E0", zorder=0)
    ax.set_axisbelow(True)

    # Set background color for better contrast
    ax.set_facecolor("#FAFAFA")

    # Rotate x-axis labels for better readability
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha="center")

    # Add compact annotations for column format

    # Find peak values with proper type handling
    peak_idx = df["submissions"].idxmax()
    peak_submissions = int(df.iloc[peak_idx]["submissions"])
    peak_month = df.iloc[peak_idx]["month"]
    peak_date = pd.to_datetime(peak_month)

    # Add compact annotation for peak
    ax.text(
        0.98,
        0.95,
        f"Peak: {peak_submissions // 1000}k\n({peak_date.strftime('%Y')})",
        transform=ax.transAxes,
        ha="right",
        va="top",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.9},
        fontsize=7,
    )

    # Tight layout
    plt.tight_layout()

    return fig, ax


def save_figure(fig, output_path=None):
    """Save the figure in multiple formats."""
    # Use environment variable if set, otherwise current working directory
    if output_path is None:
        env_output_dir = os.environ.get("RXIV_FIGURE_OUTPUT_DIR")
        output_path = Path(env_output_dir) if env_output_dir else Path.cwd()
    else:
        output_path = Path(output_path)

    # Save as PDF (vector format for LaTeX)
    fig.savefig(
        output_path / "SFigure__arxiv_growth.pdf",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )

    # Save as SVG (vector format for web)
    fig.savefig(
        output_path / "SFigure__arxiv_growth.svg",
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )

    # Save as high-resolution PNG (raster format for LaTeX compatibility)
    fig.savefig(
        output_path / "SFigure__arxiv_growth.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )

    # Print save locations
    print("Figure saved to:")
    print(f"  - {output_path / 'SFigure__arxiv_growth.pdf'}")
    print(f"  - {output_path / 'SFigure__arxiv_growth.svg'}")
    print(f"  - {output_path / 'SFigure__arxiv_growth.png'}")


def main():
    """Main function to create and save the figure."""
    # Check for help flag
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python SFigure__arxiv_growth.py [--show] [--help|-h]")
        print("  --show: Display plot (default is headless mode)")
        print("  --help|-h: Show this help message")
        return

    # Check if script should show plot (default is headless)
    show_plot = "--show" in sys.argv

    try:
        fig, ax = create_figure()
        save_figure(fig)

        # Only show plot if explicitly requested
        if show_plot:
            plt.show()
        else:
            plt.close(fig)  # Clean up memory

    except FileNotFoundError as e:
        print(f"Error: Could not find data file. {e}")
        print(
            "Please ensure arxiv_monthly_submissions.csv is in the "
            "DATA/SFigure__arxiv_growth/ directory."
        )
    except Exception as e:
        print(f"Error creating figure: {e}")
        raise


if __name__ == "__main__":
    main()
