"""Plotting utilities for the arXiv submission analysis manuscript.

This module provides reusable plotting functions that can be called
from manuscript Python blocks to generate publication-quality figures
based on real arXiv submission data.
"""

from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def set_publication_style():
    """Set matplotlib style for publication-quality figures."""
    plt.style.use("default")
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.labelsize": 10,
            "axes.titlesize": 12,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "figure.titlesize": 14,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.3,
            "lines.linewidth": 1.5,
        }
    )

    # Set color palette
    colors = ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#592F7B"]
    plt.rcParams["axes.prop_cycle"] = plt.cycler(color=colors)


def create_arxiv_timeline_plot(
    df: pd.DataFrame, title: str = "arXiv Submission Timeline", save_path: Optional[str] = None
) -> str:
    """Create a timeline plot of arXiv submissions over time.

    Args:
        df: DataFrame with arXiv submission data
        title: Plot title
        save_path: Path to save the figure (optional)

    Returns:
        Path where the figure was saved
    """
    set_publication_style()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    # Monthly submissions timeline
    ax1.plot(df["year_month"], df["submissions"], color="#2E86AB", linewidth=1.5, alpha=0.8)
    ax1.set_ylabel("Monthly Submissions")
    ax1.set_title("Monthly arXiv Submissions")
    ax1.grid(True, alpha=0.3)

    # Add trend line
    from scipy import stats

    x_numeric = np.arange(len(df))
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_numeric, df["submissions"])
    trend_line = slope * x_numeric + intercept
    ax1.plot(
        df["year_month"],
        trend_line,
        color="#A23B72",
        linewidth=2,
        linestyle="--",
        alpha=0.7,
        label=f"Trend (R²={r_value**2:.3f})",
    )
    ax1.legend()

    # Cumulative submissions
    ax2.plot(df["year_month"], df["cumulative_submissions"], color="#F18F01", linewidth=2)
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Cumulative Submissions")
    ax2.set_title("Cumulative arXiv Submissions")
    ax2.grid(True, alpha=0.3)

    plt.suptitle(title)
    plt.tight_layout()

    if save_path is None:
        save_path = "arxiv_timeline.png"

    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()

    return save_path


def create_seasonal_analysis_plot(
    df: pd.DataFrame, title: str = "Seasonal Patterns in arXiv Submissions", save_path: Optional[str] = None
) -> str:
    """Create seasonal analysis plots for arXiv submissions.

    Args:
        df: DataFrame with arXiv submission data
        title: Plot title
        save_path: Path to save the figure (optional)

    Returns:
        Path where the figure was saved
    """
    set_publication_style()

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

    # Monthly averages across all years
    monthly_avg = df.groupby("month")["submissions"].mean()
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    ax1.bar(range(1, 13), monthly_avg.values, color="#2E86AB", alpha=0.7)
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Average Submissions")
    ax1.set_title("Monthly Averages")
    ax1.set_xticks(range(1, 13))
    ax1.set_xticklabels(month_names, rotation=45)
    ax1.grid(True, alpha=0.3)

    # Quarterly averages
    quarterly_avg = df.groupby("quarter")["submissions"].mean()
    quarters = ["Q1", "Q2", "Q3", "Q4"]

    ax2.bar(range(1, 5), quarterly_avg.values, color="#A23B72", alpha=0.7)
    ax2.set_xlabel("Quarter")
    ax2.set_ylabel("Average Submissions")
    ax2.set_title("Quarterly Averages")
    ax2.set_xticks(range(1, 5))
    ax2.set_xticklabels(quarters)
    ax2.grid(True, alpha=0.3)

    # Yearly trends
    yearly_sums = df.groupby("year")["submissions"].sum()
    ax3.plot(yearly_sums.index, yearly_sums.values, marker="o", color="#F18F01", linewidth=2)
    ax3.set_xlabel("Year")
    ax3.set_ylabel("Total Submissions")
    ax3.set_title("Yearly Totals")
    ax3.grid(True, alpha=0.3)

    # Heatmap of month vs year
    pivot_data = df.pivot_table(values="submissions", index="month", columns="year", aggfunc="mean")
    im = ax4.imshow(pivot_data.values, cmap="YlOrRd", aspect="auto")
    ax4.set_xlabel("Year")
    ax4.set_ylabel("Month")
    ax4.set_title("Monthly Submissions Heatmap")
    ax4.set_yticks(range(12))
    ax4.set_yticklabels(month_names)

    # Only show every few years on x-axis for readability
    year_ticks = pivot_data.columns[::3]
    ax4.set_xticks(range(0, len(pivot_data.columns), 3))
    ax4.set_xticklabels(year_ticks, rotation=45)

    plt.colorbar(im, ax=ax4, label="Submissions")

    plt.suptitle(title)
    plt.tight_layout()

    if save_path is None:
        save_path = "seasonal_analysis.png"

    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()

    return save_path


def create_arxiv_growth_analysis(
    df: pd.DataFrame, title: str = "arXiv Growth Analysis", save_path: Optional[str] = None
) -> str:
    """Create growth analysis plots for arXiv submissions.

    Args:
        df: DataFrame with arXiv submission data
        title: Plot title
        save_path: Path to save the figure (optional)

    Returns:
        Path where the figure was saved
    """
    set_publication_style()

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

    # Year-over-year growth rates
    yearly_sums = df.groupby("year")["submissions"].sum()
    you_growth = yearly_sums.pct_change().dropna() * 100

    ax1.bar(yoy_growth.index, yoy_growth.values, color="#2E86AB", alpha=0.7)
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Growth Rate (%)")
    ax1.set_title("Year-over-Year Growth")
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color="black", linestyle="-", linewidth=0.8)

    # Cumulative growth from baseline
    baseline_year = df["year"].min()
    baseline_total = yearly_sums.iloc[0]
    cumulative_growth = (yearly_sums - baseline_total) / baseline_total * 100

    ax2.plot(cumulative_growth.index, cumulative_growth.values, marker="o", color="#A23B72", linewidth=2)
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Cumulative Growth (%)")
    ax2.set_title(f"Growth Since {baseline_year}")
    ax2.grid(True, alpha=0.3)

    # Monthly volatility (coefficient of variation by year)
    monthly_cv_by_year = df.groupby("year")["submissions"].apply(lambda x: x.std() / x.mean() * 100)

    ax3.plot(monthly_cv_by_year.index, monthly_cv_by_year.values, marker="s", color="#F18F01", linewidth=2)
    ax3.set_xlabel("Year")
    ax3.set_ylabel("Coefficient of Variation (%)")
    ax3.set_title("Monthly Submission Volatility")
    ax3.grid(True, alpha=0.3)

    # Decade comparison
    df["decade"] = (df["year"] // 10) * 10
    decade_avg = df.groupby("decade")["submissions"].mean()
    decades = [f"{int(d)}s" for d in decade_avg.index]

    ax4.bar(decades, decade_avg.values, color="#C73E1D", alpha=0.7)
    ax4.set_xlabel("Decade")
    ax4.set_ylabel("Average Monthly Submissions")
    ax4.set_title("Average Submissions by Decade")
    ax4.grid(True, alpha=0.3)

    plt.suptitle(title)
    plt.tight_layout()

    if save_path is None:
        save_path = "arxiv_growth_analysis.png"

    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()

    return save_path


def create_arxiv_statistics_summary(
    stats: Dict[str, Any], title: str = "arXiv Submission Statistics Summary", save_path: Optional[str] = None
) -> str:
    """Create statistical summary visualization for arXiv data.

    Args:
        stats: Statistics dictionary from data_processing.compute_arxiv_statistics()
        title: Plot title
        save_path: Path to save the figure (optional)

    Returns:
        Path where the figure was saved
    """
    set_publication_style()

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

    # Monthly statistics comparison
    monthly_stats = stats["monthly"]
    metrics = ["Mean", "Median", "Min", "Max"]
    values = [
        monthly_stats["mean_monthly"],
        monthly_stats["median_monthly"],
        monthly_stats["min_monthly"],
        monthly_stats["max_monthly"],
    ]

    bars = ax1.bar(metrics, values, color=["#2E86AB", "#A23B72", "#F18F01", "#C73E1D"], alpha=0.7)
    ax1.set_ylabel("Monthly Submissions")
    ax1.set_title("Monthly Submission Statistics")
    ax1.grid(True, alpha=0.3)

    # Add values on bars
    for bar, value in zip(bars, values, strict=False):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(values) * 0.01,
            f"{value:.0f}",
            ha="center",
            va="bottom",
        )

    # Yearly vs Monthly comparison
    yearly_stats = stats["yearly"]
    comparison_metrics = ["Mean", "Std Dev"]
    monthly_vals = [monthly_stats["mean_monthly"], monthly_stats["std_monthly"]]
    yearly_vals = [yearly_stats["mean_yearly"] / 12, yearly_stats["std_yearly"] / 12]  # Convert to monthly equivalent

    x = np.arange(len(comparison_metrics))
    width = 0.35

    ax2.bar(x - width / 2, monthly_vals, width, label="Monthly Data", color="#2E86AB", alpha=0.7)
    ax2.bar(x + width / 2, yearly_vals, width, label="Yearly Data (÷12)", color="#A23B72", alpha=0.7)
    ax2.set_ylabel("Submissions")
    ax2.set_title("Monthly vs Yearly Statistics")
    ax2.set_xticks(x)
    ax2.set_xticklabels(comparison_metrics)
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Growth metrics
    growth_stats = stats["growth"]
    growth_metrics = ["Total Growth (%)", "Annual Growth Rate (%)"]
    growth_values = [growth_stats["total_growth_percent"], growth_stats["compound_annual_growth_rate"]]

    bars3 = ax3.bar(growth_metrics, growth_values, color=["#F18F01", "#C73E1D"], alpha=0.7)
    ax3.set_ylabel("Growth Rate (%)")
    ax3.set_title("Growth Analysis")
    ax3.grid(True, alpha=0.3)

    for bar, value in zip(bars3, growth_values, strict=False):
        ax3.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(growth_values) * 0.05,
            f"{value:.1f}%",
            ha="center",
            va="bottom",
        )

    # Data scale visualization
    scale_labels = ["Total\nSubmissions", "Months\nAnalyzed", "First Year\nTotal", "Last Year\nTotal"]
    scale_values = [
        monthly_stats["total_submissions"],
        monthly_stats["months_analyzed"],
        growth_stats["first_year_submissions"],
        growth_stats["last_year_submissions"],
    ]

    # Normalize for display (different scales)
    normalized_values = [v / max(scale_values) * 100 for v in scale_values]
    colors = ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D"]

    bars4 = ax4.bar(scale_labels, normalized_values, color=colors, alpha=0.7)
    ax4.set_ylabel("Normalized Scale")
    ax4.set_title("Data Scale Overview")
    ax4.grid(True, alpha=0.3)

    # Add actual values as text
    for bar, actual_val in zip(bars4, scale_values, strict=False):
        ax4.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 5,
            f"{actual_val:,}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    plt.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()

    if save_path is None:
        save_path = "arxiv_statistics_summary.png"

    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()

    return save_path
