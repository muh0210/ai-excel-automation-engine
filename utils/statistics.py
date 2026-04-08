"""
MODULE 10: STATISTICAL TESTING ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Advanced statistical tests: normality, t-tests, ANOVA,
chi-square, regression, percentile analysis.
"""

import pandas as pd
import numpy as np

try:
    from scipy import stats as scipy_stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


def normality_test(series, test='shapiro'):
    """
    Test if a numeric series follows a normal distribution.

    Args:
        series: pd.Series (numeric)
        test: 'shapiro' or 'anderson'

    Returns:
        dict with test results
    """
    if not SCIPY_AVAILABLE:
        return {'error': 'scipy not available'}

    values = series.dropna().values
    if len(values) < 8:
        return {'error': 'Need at least 8 data points'}

    # Limit to 5000 for Shapiro (it's slow for large N)
    if test == 'shapiro':
        sample = values[:5000] if len(values) > 5000 else values
        stat, p_value = scipy_stats.shapiro(sample)
        return {
            'test': 'Shapiro-Wilk',
            'statistic': round(stat, 4),
            'p_value': round(p_value, 4),
            'is_normal': p_value > 0.05,
            'interpretation': 'Data appears normally distributed (p > 0.05)' if p_value > 0.05
                             else 'Data does NOT appear normally distributed (p ≤ 0.05)'
        }
    elif test == 'anderson':
        result = scipy_stats.anderson(values)
        return {
            'test': 'Anderson-Darling',
            'statistic': round(result.statistic, 4),
            'critical_values': {f'{sl}%': round(cv, 4) for sl, cv in
                               zip(result.significance_level, result.critical_values)},
            'is_normal': result.statistic < result.critical_values[2],  # 5% level
            'interpretation': 'Data appears normal at 5% significance'
                             if result.statistic < result.critical_values[2]
                             else 'Data does NOT appear normal at 5% significance'
        }
    return {'error': f'Unknown test: {test}'}


def ttest_two_groups(df, numeric_col, group_col, group1, group2):
    """
    Independent samples t-test between two groups.

    Returns:
        dict with test results
    """
    if not SCIPY_AVAILABLE:
        return {'error': 'scipy not available'}

    try:
        g1 = df[df[group_col] == group1][numeric_col].dropna()
        g2 = df[df[group_col] == group2][numeric_col].dropna()

        if len(g1) < 3 or len(g2) < 3:
            return {'error': 'Need at least 3 data points per group'}

        stat, p_value = scipy_stats.ttest_ind(g1, g2, equal_var=False)
        return {
            'test': 'Welch\'s T-Test',
            'group1': str(group1),
            'group1_mean': round(float(g1.mean()), 2),
            'group1_n': len(g1),
            'group2': str(group2),
            'group2_mean': round(float(g2.mean()), 2),
            'group2_n': len(g2),
            'statistic': round(float(stat), 4),
            'p_value': round(float(p_value), 4),
            'significant': p_value < 0.05,
            'interpretation': f'Significant difference between groups (p={p_value:.4f})'
                             if p_value < 0.05
                             else f'No significant difference between groups (p={p_value:.4f})'
        }
    except Exception as e:
        return {'error': str(e)}


def anova_test(df, numeric_col, group_col):
    """
    One-way ANOVA test across multiple groups.

    Returns:
        dict with test results
    """
    if not SCIPY_AVAILABLE:
        return {'error': 'scipy not available'}

    try:
        groups = []
        group_names = df[group_col].dropna().unique()
        for g in group_names:
            vals = df[df[group_col] == g][numeric_col].dropna()
            if len(vals) >= 2:
                groups.append(vals.values)

        if len(groups) < 2:
            return {'error': 'Need at least 2 groups with 2+ data points each'}

        stat, p_value = scipy_stats.f_oneway(*groups)
        return {
            'test': 'One-Way ANOVA',
            'n_groups': len(groups),
            'f_statistic': round(float(stat), 4),
            'p_value': round(float(p_value), 4),
            'significant': p_value < 0.05,
            'interpretation': f'Significant differences exist between groups (p={p_value:.4f})'
                             if p_value < 0.05
                             else f'No significant differences between groups (p={p_value:.4f})'
        }
    except Exception as e:
        return {'error': str(e)}


def chi_square_test(df, col1, col2):
    """
    Chi-square test of independence between two categorical columns.

    Returns:
        dict with test results
    """
    if not SCIPY_AVAILABLE:
        return {'error': 'scipy not available'}

    try:
        contingency = pd.crosstab(df[col1], df[col2])
        chi2, p_value, dof, expected = scipy_stats.chi2_contingency(contingency)
        return {
            'test': 'Chi-Square Test of Independence',
            'chi2_statistic': round(float(chi2), 4),
            'p_value': round(float(p_value), 4),
            'dof': int(dof),
            'significant': p_value < 0.05,
            'interpretation': f'{col1} and {col2} are DEPENDENT (p={p_value:.4f})'
                             if p_value < 0.05
                             else f'{col1} and {col2} are INDEPENDENT (p={p_value:.4f})'
        }
    except Exception as e:
        return {'error': str(e)}


def linear_regression(df, x_col, y_col):
    """
    Simple linear regression between two numeric columns.

    Returns:
        dict with regression results
    """
    if not SCIPY_AVAILABLE:
        return {'error': 'scipy not available'}

    try:
        valid = df[[x_col, y_col]].dropna()
        if len(valid) < 5:
            return {'error': 'Need at least 5 data points'}

        slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(
            valid[x_col].values, valid[y_col].values
        )
        return {
            'test': 'Simple Linear Regression',
            'x_column': x_col,
            'y_column': y_col,
            'slope': round(float(slope), 4),
            'intercept': round(float(intercept), 4),
            'r_squared': round(float(r_value ** 2), 4),
            'r_value': round(float(r_value), 4),
            'p_value': round(float(p_value), 4),
            'std_error': round(float(std_err), 4),
            'equation': f'y = {slope:.4f}x + {intercept:.4f}',
            'significant': p_value < 0.05,
            'interpretation': f'Strong linear relationship (R²={r_value**2:.3f})'
                             if r_value ** 2 > 0.5
                             else f'Weak linear relationship (R²={r_value**2:.3f})'
                             if r_value ** 2 > 0.1
                             else f'No meaningful linear relationship (R²={r_value**2:.3f})',
            'n_points': len(valid),
        }
    except Exception as e:
        return {'error': str(e)}


def percentile_analysis(series, percentiles=None):
    """
    Compute custom percentile breakdowns.

    Returns:
        dict with percentile values
    """
    if percentiles is None:
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]

    values = series.dropna()
    if len(values) == 0:
        return {}

    result = {}
    for p in percentiles:
        result[f'P{p}'] = round(float(np.percentile(values, p)), 2)

    result['IQR'] = round(result.get('P75', 0) - result.get('P25', 0), 2)
    return result


def run_all_normality_tests(df):
    """
    Run normality tests on all numeric columns.

    Returns:
        list of dicts with results per column
    """
    results = []
    for col in df.select_dtypes(include='number').columns:
        test_result = normality_test(df[col])
        if 'error' not in test_result:
            test_result['column'] = col
            results.append(test_result)
    return results
