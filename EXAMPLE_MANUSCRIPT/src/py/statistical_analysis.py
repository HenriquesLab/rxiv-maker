"""Statistical analysis utilities for the example manuscript.

This module provides advanced statistical functions that demonstrate
the power of executable manuscripts with sophisticated data analysis.
"""

from typing import Any, Dict, List

import numpy as np
from scipy import stats


def bootstrap_confidence_interval(
    data: np.ndarray, statistic: str = "mean", confidence_level: float = 0.95, n_bootstrap: int = 10000
) -> Dict[str, float]:
    """Calculate bootstrap confidence intervals for a statistic.

    Args:
        data: Input data array
        statistic: Statistic to calculate ('mean', 'median', 'std')
        confidence_level: Confidence level for the interval
        n_bootstrap: Number of bootstrap samples

    Returns:
        Dictionary with statistic value and confidence interval
    """
    np.random.seed(42)  # For reproducibility

    # Define statistic function
    stat_functions = {"mean": np.mean, "median": np.median, "std": np.std}

    if statistic not in stat_functions:
        raise ValueError(f"Statistic must be one of {list(stat_functions.keys())}")

    stat_func = stat_functions[statistic]

    # Calculate original statistic
    original_stat = stat_func(data)

    # Bootstrap sampling
    bootstrap_stats = []
    n = len(data)

    for _ in range(n_bootstrap):
        bootstrap_sample = np.random.choice(data, size=n, replace=True)
        bootstrap_stats.append(stat_func(bootstrap_sample))

    bootstrap_stats = np.array(bootstrap_stats)

    # Calculate confidence interval
    alpha = 1 - confidence_level
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100

    ci_lower = np.percentile(bootstrap_stats, lower_percentile)
    ci_upper = np.percentile(bootstrap_stats, upper_percentile)

    return {
        "statistic": statistic,
        "value": float(original_stat),
        "confidence_level": confidence_level,
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "standard_error": float(np.std(bootstrap_stats)),
    }


def power_analysis(
    effect_size: float, alpha: float = 0.05, power: float = 0.8, alternative: str = "two-sided"
) -> Dict[str, float]:
    """Perform power analysis for two-sample t-test.

    Args:
        effect_size: Expected effect size (Cohen's d)
        alpha: Type I error rate
        power: Desired statistical power
        alternative: Type of test ('two-sided', 'greater', 'less')

    Returns:
        Dictionary with required sample size and power analysis results
    """
    from scipy.stats import norm

    # Critical values
    if alternative == "two-sided":
        z_alpha = norm.ppf(1 - alpha / 2)
        z_beta = norm.ppf(power)
    else:
        z_alpha = norm.ppf(1 - alpha)
        z_beta = norm.ppf(power)

    # Sample size calculation (per group)
    n_per_group = ((z_alpha + z_beta) ** 2 * 2) / (effect_size**2)
    n_per_group = int(np.ceil(n_per_group))

    # Calculate achieved power with this sample size
    achieved_power = 1 - norm.cdf(z_alpha - effect_size * np.sqrt(n_per_group / 2))

    return {
        "effect_size": effect_size,
        "alpha": alpha,
        "desired_power": power,
        "alternative": alternative,
        "n_per_group": n_per_group,
        "total_n": n_per_group * 2,
        "achieved_power": float(achieved_power),
    }


def effect_size_interpretation(cohens_d: float) -> Dict[str, Any]:
    """Interpret Cohen's d effect size.

    Args:
        cohens_d: Cohen's d value

    Returns:
        Dictionary with interpretation information
    """
    abs_d = abs(cohens_d)

    if abs_d < 0.2:
        magnitude = "negligible"
    elif abs_d < 0.5:
        magnitude = "small"
    elif abs_d < 0.8:
        magnitude = "medium"
    else:
        magnitude = "large"

    # Calculate percentage of non-overlap
    non_overlap = 2 * stats.norm.cdf(-abs_d / 2)
    overlap = 1 - non_overlap

    # Probability of superiority
    prob_superiority = stats.norm.cdf(abs_d / np.sqrt(2))

    return {
        "cohens_d": float(cohens_d),
        "magnitude": magnitude,
        "percent_overlap": float(overlap * 100),
        "percent_non_overlap": float(non_overlap * 100),
        "probability_superiority": float(prob_superiority),
    }


def multiple_comparisons_correction(p_values: List[float], method: str = "bonferroni") -> Dict[str, Any]:
    """Apply multiple comparisons correction.

    Args:
        p_values: List of p-values to correct
        method: Correction method ('bonferroni', 'fdr_bh')

    Returns:
        Dictionary with corrected p-values and results
    """
    p_values = np.array(p_values)
    n_tests = len(p_values)

    if method == "bonferroni":
        corrected_p = p_values * n_tests
        corrected_p = np.minimum(corrected_p, 1.0)
        alpha_corrected = 0.05 / n_tests

    elif method == "fdr_bh":
        # Benjamini-Hochberg procedure
        sorted_indices = np.argsort(p_values)
        sorted_p = p_values[sorted_indices]

        # Calculate critical values
        critical_values = np.arange(1, n_tests + 1) * 0.05 / n_tests

        # Find largest i such that p[i] <= critical_value[i]
        significant_indices = sorted_p <= critical_values

        if np.any(significant_indices):
            last_significant = np.where(significant_indices)[0][-1]
            alpha_corrected = critical_values[last_significant]
        else:
            alpha_corrected = 0.0

        corrected_p = np.minimum(sorted_p * n_tests / np.arange(1, n_tests + 1), 1.0)

        # Restore original order
        corrected_p_full = np.empty_like(corrected_p)
        corrected_p_full[sorted_indices] = corrected_p
        corrected_p = corrected_p_full

    else:
        raise ValueError("Method must be 'bonferroni' or 'fdr_bh'")

    return {
        "method": method,
        "original_p_values": p_values.tolist(),
        "corrected_p_values": corrected_p.tolist(),
        "significant_original": (p_values < 0.05).tolist(),
        "significant_corrected": (corrected_p < 0.05).tolist(),
        "alpha_corrected": float(alpha_corrected),
        "n_tests": n_tests,
    }


def regression_analysis(x: np.ndarray, y: np.ndarray, include_quadratic: bool = False) -> Dict[str, Any]:
    """Perform linear/polynomial regression analysis.

    Args:
        x: Independent variable
        y: Dependent variable
        include_quadratic: Whether to include quadratic term

    Returns:
        Dictionary with regression results
    """
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score
    from sklearn.preprocessing import PolynomialFeatures

    # Prepare data
    X = x.reshape(-1, 1)

    if include_quadratic:
        poly_features = PolynomialFeatures(degree=2)
        X_poly = poly_features.fit_transform(X)
        model = LinearRegression()
        model.fit(X_poly, y)
        y_pred = model.predict(X_poly)
        coefficients = model.coef_
        intercept = model.intercept_
    else:
        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)
        coefficients = model.coef_
        intercept = model.intercept_

    # Calculate statistics
    r_squared = r2_score(y, y_pred)
    n = len(y)
    k = len(coefficients) if include_quadratic else 1
    adjusted_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - k - 1)

    # Calculate standard errors and t-statistics
    residuals = y - y_pred
    mse = np.mean(residuals**2)
    rmse = np.sqrt(mse)

    return {
        "model_type": "quadratic" if include_quadratic else "linear",
        "coefficients": coefficients.tolist(),
        "intercept": float(intercept),
        "r_squared": float(r_squared),
        "adjusted_r_squared": float(adjusted_r_squared),
        "rmse": float(rmse),
        "n_observations": n,
        "predictions": y_pred.tolist(),
        "residuals": residuals.tolist(),
    }


def normality_tests(data: np.ndarray) -> Dict[str, Any]:
    """Perform multiple normality tests on data.

    Args:
        data: Data array to test

    Returns:
        Dictionary with test results
    """
    results = {}

    # Shapiro-Wilk test
    if len(data) <= 5000:  # Shapiro-Wilk is limited to n <= 5000
        shapiro_stat, shapiro_p = stats.shapiro(data)
        results["shapiro_wilk"] = {
            "statistic": float(shapiro_stat),
            "p_value": float(shapiro_p),
            "interpretation": "normal" if shapiro_p > 0.05 else "not_normal",
        }

    # Kolmogorov-Smirnov test against normal distribution
    mean, std = np.mean(data), np.std(data, ddof=1)
    ks_stat, ks_p = stats.kstest(data, lambda x: stats.norm.cdf(x, mean, std))
    results["kolmogorov_smirnov"] = {
        "statistic": float(ks_stat),
        "p_value": float(ks_p),
        "interpretation": "normal" if ks_p > 0.05 else "not_normal",
    }

    # Anderson-Darling test
    ad_stat, ad_critical, ad_significance = stats.anderson(data, dist="norm")
    # Use 5% significance level (index 2)
    ad_result = ad_stat < ad_critical[2]
    results["anderson_darling"] = {
        "statistic": float(ad_stat),
        "critical_value_5pct": float(ad_critical[2]),
        "interpretation": "normal" if ad_result else "not_normal",
    }

    # Jarque-Bera test
    jb_stat, jb_p = stats.jarque_bera(data)
    results["jarque_bera"] = {
        "statistic": float(jb_stat),
        "p_value": float(jb_p),
        "interpretation": "normal" if jb_p > 0.05 else "not_normal",
    }

    # Skewness and kurtosis
    skewness = stats.skew(data)
    kurtosis = stats.kurtosis(data)

    results["descriptive"] = {
        "skewness": float(skewness),
        "kurtosis": float(kurtosis),
        "skewness_interpretation": "symmetric" if abs(skewness) < 0.5 else "skewed",
        "kurtosis_interpretation": "mesokurtic"
        if abs(kurtosis) < 0.5
        else ("platykurtic" if kurtosis < 0 else "leptokurtic"),
    }

    return results
