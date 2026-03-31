"""
MODULE 3: ANALYSIS ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━
Statistical analysis, correlations, grouping, trend detection, and top/bottom N.
Designed to work with ANY dataset — auto-detects column types.
"""

import pandas as pd
import numpy as np


def basic_analysis(df):
    """
    Generate comprehensive summary statistics.

    Returns:
        dict with 'numeric_summary', 'categorical_summary', 'shape_info'
    """
    result = {}

    # Numeric summary
    numeric_df = df.select_dtypes(include='number')
    if not numeric_df.empty:
        result['numeric_summary'] = numeric_df.describe().round(2)
    else:
        result['numeric_summary'] = None

    # Categorical summary
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
    """
    Compute correlation matrix for numeric columns.

    Returns:
        pd.DataFrame (correlation matrix) or None if insufficient numeric columns
    """
    numeric_df = df.select_dtypes(include='number')
    if numeric_df.shape[1] < 2:
        return None
    return numeric_df.corr().round(3)


def group_analysis(df, group_col, value_col, agg_func='sum'):
    """
    Group by a categorical column and aggregate a numeric column.

    Args:
        df: DataFrame
        group_col: column to group by
        value_col: numeric column to aggregate
        agg_func: 'sum', 'mean', 'count', 'min', 'max'

    Returns:
        pd.DataFrame sorted by aggregated values descending
    """
    if group_col not in df.columns or value_col not in df.columns:
        return None

    agg_map = {
        'sum': 'sum',
        'mean': 'mean',
        'count': 'count',
        'min': 'min',
        'max': 'max'
    }

    func = agg_map.get(agg_func, 'sum')
    grouped = df.groupby(group_col)[value_col].agg(func).reset_index()
    grouped.columns = [group_col, f'{value_col}_{func}']
    grouped = grouped.sort_values(by=f'{value_col}_{func}', ascending=False).reset_index(drop=True)
    return grouped


def auto_group_analysis(df):
    """
    Automatically find the best grouping combinations.
    Groups each categorical column with each numeric column.

    Returns:
        list of dicts: [{'group_col', 'value_col', 'result_df'}, ...]
    """
    cat_cols = list(df.select_dtypes(include=['object', 'category']).columns)
    num_cols = list(df.select_dtypes(include='number').columns)

    results = []
    for cat_col in cat_cols[:3]:  # Limit to top 3 categorical columns
        if df[cat_col].nunique() > 20:  # Skip high-cardinality columns
            continue
        for num_col in num_cols[:3]:  # Limit to top 3 numeric columns
            grouped = group_analysis(df, cat_col, num_col, 'sum')
            if grouped is not None and len(grouped) > 1:
                results.append({
                    'group_col': cat_col,
                    'value_col': num_col,
                    'result_df': grouped
                })
    return results


def trend_analysis(df, date_col, value_col):
    """
    Analyze trend over time for a date-indexed numeric column.

    Returns:
        dict with trend info or None
    """
    if date_col not in df.columns or value_col not in df.columns:
        return None

    try:
        df_sorted = df[[date_col, value_col]].dropna().sort_values(by=date_col)
        if len(df_sorted) < 3:
            return None

        values = df_sorted[value_col].values

        # Simple linear trend
        x = np.arange(len(values))
        if len(x) > 1:
            slope = np.polyfit(x, values, 1)[0]
        else:
            slope = 0

        # Calculate period-over-period changes
        first_half = values[:len(values)//2].mean()
        second_half = values[len(values)//2:].mean()
        change_pct = ((second_half - first_half) / max(abs(first_half), 1e-10)) * 100

        return {
            'direction': 'Upward 📈' if slope > 0 else 'Downward 📉' if slope < 0 else 'Flat ➡️',
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
    """
    Get top N and bottom N rows by a numeric column.

    Returns:
        dict with 'top' and 'bottom' DataFrames
    """
    if column not in df.columns or not pd.api.types.is_numeric_dtype(df[column]):
        return None

    df_sorted = df.sort_values(by=column, ascending=False)
    return {
        'top': df_sorted.head(n),
        'bottom': df_sorted.tail(n)
    }


def compute_kpis(df):
    """
    Compute dashboard KPI metrics for all numeric columns.

    Returns:
        dict: {column_name: {total, average, median, min, max, std, growth_pct}}
    """
    numeric_cols = df.select_dtypes(include='number').columns
    kpis = {}

    for col in numeric_cols:
        values = df[col].dropna()
        if len(values) == 0:
            continue

        # Growth: compare first 10% vs last 10%
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
