"""
MODULE 3: ANALYSIS ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━
Statistical analysis, correlations, grouping, trend detection, top/bottom N,
Pareto analysis, moving averages, seasonality, percentile rankings.
Designed to work with ANY dataset — auto-detects column types.
"""

import pandas as pd
import numpy as np


def basic_analysis(df):
    """Generate comprehensive summary statistics."""
    result = {}

    numeric_df = df.select_dtypes(include='number')
    if not numeric_df.empty:
        result['numeric_summary'] = numeric_df.describe().round(2)
    else:
        result['numeric_summary'] = None

    cat_df = df.select_dtypes(include=['object', 'category'])
    if not cat_df.empty:
        cat_summary = {}
        for col in cat_df.columns:
            value_counts = df[col].value_counts()
            cat_summary[col] = {
                'unique_values': int(df[col].nunique()),
                'most_common': str(value_counts.index[0]) if len(value_counts) > 0 else 'N/A',
                'most_common_count': int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                'least_common': str(value_counts.index[-1]) if len(value_counts) > 0 else 'N/A',
            }
        result['categorical_summary'] = cat_summary
    else:
        result['categorical_summary'] = None

    result['shape_info'] = {
        'rows': df.shape[0],
        'columns': df.shape[1],
        'numeric_columns': len(numeric_df.columns),
        'categorical_columns': len(cat_df.columns),
        'datetime_columns': len(df.select_dtypes(include='datetime').columns)
    }

    return result


def correlation_analysis(df):
    """Compute correlation matrix for numeric columns."""
    numeric_df = df.select_dtypes(include='number')
    if numeric_df.shape[1] < 2:
        return None
    return numeric_df.corr().round(3)


def group_analysis(df, group_col, value_col, agg_func='sum'):
    """Group by a categorical column and aggregate a numeric column."""
    if group_col not in df.columns or value_col not in df.columns:
        return None

    agg_map = {
        'sum': 'sum', 'mean': 'mean', 'count': 'count',
        'min': 'min', 'max': 'max', 'median': 'median', 'std': 'std'
    }

    func = agg_map.get(agg_func, 'sum')
    grouped = df.groupby(group_col)[value_col].agg(func).reset_index()
    grouped.columns = [group_col, f'{value_col}_{func}']
    grouped = grouped.sort_values(by=f'{value_col}_{func}', ascending=False).reset_index(drop=True)
    return grouped


def auto_group_analysis(df):
    """Automatically find the best grouping combinations."""
    cat_cols = list(df.select_dtypes(include=['object', 'category']).columns)
    num_cols = list(df.select_dtypes(include='number').columns)

    results = []
    for cat_col in cat_cols[:3]:
        if df[cat_col].nunique() > 20:
            continue
        for num_col in num_cols[:3]:
            grouped = group_analysis(df, cat_col, num_col, 'sum')
            if grouped is not None and len(grouped) > 1:
                results.append({
                    'group_col': cat_col,
                    'value_col': num_col,
                    'result_df': grouped
                })
    return results


def trend_analysis(df, date_col, value_col):
    """Analyze trend over time for a date-indexed numeric column."""
    if date_col not in df.columns or value_col not in df.columns:
        return None

    try:
        df_sorted = df[[date_col, value_col]].dropna().sort_values(by=date_col)
        if len(df_sorted) < 3:
            return None

        values = df_sorted[value_col].values

        x = np.arange(len(values))
        if len(x) > 1:
            slope = np.polyfit(x, values, 1)[0]
        else:
            slope = 0

        first_half = values[:len(values)//2].mean()
        second_half = values[len(values)//2:].mean()
        change_pct = ((second_half - first_half) / max(abs(first_half), 1e-10)) * 100

        return {
            'direction': 'Upward' if slope > 0 else 'Downward' if slope < 0 else 'Flat',
            'slope': round(slope, 4),
            'first_half_avg': round(first_half, 2),
            'second_half_avg': round(second_half, 2),
            'change_pct': round(change_pct, 2),
            'data_points': len(values),
            'min_value': round(float(values.min()), 2),
            'max_value': round(float(values.max()), 2),
            'time_series_df': df_sorted
        }
    except Exception:
        return None


def top_bottom_n(df, column, n=5):
    """Get top N and bottom N rows by a numeric column."""
    if column not in df.columns or not pd.api.types.is_numeric_dtype(df[column]):
        return None

    df_sorted = df.sort_values(by=column, ascending=False)
    return {
        'top': df_sorted.head(n),
        'bottom': df_sorted.tail(n)
    }


def compute_kpis(df):
    """Compute dashboard KPI metrics for all numeric columns."""
    numeric_cols = df.select_dtypes(include='number').columns
    kpis = {}

    for col in numeric_cols:
        values = df[col].dropna()
        if len(values) == 0:
            continue

        n = max(1, len(values) // 10)
        first_chunk = values.head(n).mean()
        last_chunk = values.tail(n).mean()
        growth = ((last_chunk - first_chunk) / max(abs(first_chunk), 1e-10)) * 100

        kpis[col] = {
            'total': round(float(values.sum()), 2),
            'average': round(float(values.mean()), 2),
            'median': round(float(values.median()), 2),
            'min': round(float(values.min()), 2),
            'max': round(float(values.max()), 2),
            'std': round(float(values.std()), 2),
            'growth_pct': round(growth, 2),
            'count': int(len(values))
        }

    return kpis


# ═══════════════════════════════════════════════════════════════════
#  NEW ADVANCED ANALYSIS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def pareto_analysis(df, category_col, value_col, agg_func='sum'):
    """
    Identify which categories contribute the most (80/20 rule).

    Returns:
        dict with pareto data and the number of categories making up 80%
    """
    try:
        grouped = df.groupby(category_col)[value_col].agg(agg_func).sort_values(ascending=False)
        total = grouped.sum()
        if total == 0:
            return None

        cumulative = grouped.cumsum()
        cumulative_pct = (cumulative / total * 100).round(1)

        # Find how many categories make up 80%
        categories_for_80 = 0
        for pct in cumulative_pct:
            categories_for_80 += 1
            if pct >= 80:
                break

        return {
            'categories': list(grouped.index),
            'values': list(grouped.values),
            'cumulative_pct': list(cumulative_pct.values),
            'total': round(float(total), 2),
            'categories_for_80_pct': categories_for_80,
            'total_categories': len(grouped),
            'concentration_ratio': round(categories_for_80 / len(grouped) * 100, 1),
        }
    except Exception:
        return None


def moving_average(df, date_col, value_col, window=7):
    """
    Compute Simple Moving Average (SMA) and Exponential Moving Average (EMA).

    Returns:
        DataFrame with SMA and EMA columns added
    """
    try:
        df_sorted = df[[date_col, value_col]].dropna().sort_values(by=date_col).copy()
        if len(df_sorted) < window:
            return None

        df_sorted[f'SMA_{window}'] = df_sorted[value_col].rolling(window=window).mean().round(2)
        df_sorted[f'EMA_{window}'] = df_sorted[value_col].ewm(span=window, adjust=False).mean().round(2)

        return df_sorted
    except Exception:
        return None


def seasonality_analysis(df, date_col, value_col):
    """
    Detect seasonal patterns in time-series data.

    Returns:
        dict with monthly/weekly averages and peak periods
    """
    try:
        df_ts = df[[date_col, value_col]].dropna().copy()
        df_ts[date_col] = pd.to_datetime(df_ts[date_col])
        df_ts = df_ts.sort_values(by=date_col)

        if len(df_ts) < 12:
            return None

        # Monthly analysis
        df_ts['month'] = df_ts[date_col].dt.month
        df_ts['month_name'] = df_ts[date_col].dt.month_name()
        monthly_avg = df_ts.groupby('month')[value_col].mean().round(2)

        peak_month = monthly_avg.idxmax()
        low_month = monthly_avg.idxmin()

        # Day of week analysis (if enough data)
        df_ts['day_of_week'] = df_ts[date_col].dt.day_name()
        daily_avg = df_ts.groupby('day_of_week')[value_col].mean().round(2)

        # Quarter analysis
        df_ts['quarter'] = df_ts[date_col].dt.quarter
        quarterly_avg = df_ts.groupby('quarter')[value_col].mean().round(2)

        month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April',
                       5: 'May', 6: 'June', 7: 'July', 8: 'August',
                       9: 'September', 10: 'October', 11: 'November', 12: 'December'}

        return {
            'monthly_avg': monthly_avg.to_dict(),
            'peak_month': month_names.get(peak_month, str(peak_month)),
            'low_month': month_names.get(low_month, str(low_month)),
            'peak_value': round(float(monthly_avg.max()), 2),
            'low_value': round(float(monthly_avg.min()), 2),
            'daily_avg': daily_avg.to_dict(),
            'quarterly_avg': quarterly_avg.to_dict(),
            'seasonal_range': round(float(monthly_avg.max() - monthly_avg.min()), 2),
        }
    except Exception:
        return None


def percentile_ranking(df, column, categories_col=None):
    """
    Rank items by percentile within categories.

    Returns:
        DataFrame with percentile rank column added
    """
    try:
        df_ranked = df.copy()
        if categories_col and categories_col in df.columns:
            df_ranked[f'{column}_percentile'] = df.groupby(categories_col)[column].rank(pct=True).round(3) * 100
        else:
            df_ranked[f'{column}_percentile'] = df[column].rank(pct=True).round(3) * 100
        return df_ranked
    except Exception:
        return df


def compare_groups(df, group_col, value_col):
    """
    Compare statistics across groups within a categorical column.

    Returns:
        DataFrame with group comparison statistics
    """
    try:
        comparison = df.groupby(group_col)[value_col].agg([
            'count', 'mean', 'median', 'std', 'min', 'max', 'sum'
        ]).round(2)
        comparison.columns = ['Count', 'Mean', 'Median', 'Std Dev', 'Min', 'Max', 'Total']
        comparison = comparison.sort_values('Total', ascending=False)
        return comparison.reset_index()
    except Exception:
        return None
