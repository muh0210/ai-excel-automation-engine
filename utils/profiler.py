"""
MODULE 8: DATA PROFILER
━━━━━━━━━━━━━━━━━━━━━━━
Deep data profiling: column-by-column stats, missing value patterns,
cardinality analysis, memory usage, constant/zero-variance detection.
"""

import pandas as pd
import numpy as np


def profile_dataset(df):
    """
    Generate comprehensive dataset-level profile.

    Returns:
        dict with dataset-level metrics
    """
    total_cells = df.shape[0] * df.shape[1]
    total_missing = int(df.isnull().sum().sum())
    total_duplicates = int(df.duplicated().sum())

    memory_bytes = int(df.memory_usage(deep=True).sum())
    if memory_bytes > 1_048_576:
        memory_str = f"{memory_bytes / 1_048_576:.1f} MB"
    else:
        memory_str = f"{memory_bytes / 1024:.1f} KB"

    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    date_cols = df.select_dtypes(include='datetime').columns.tolist()
    bool_cols = df.select_dtypes(include='bool').columns.tolist()

    return {
        'rows': df.shape[0],
        'columns': df.shape[1],
        'total_cells': total_cells,
        'total_missing': total_missing,
        'missing_pct': round(total_missing / max(total_cells, 1) * 100, 1),
        'total_duplicates': total_duplicates,
        'duplicate_pct': round(total_duplicates / max(df.shape[0], 1) * 100, 1),
        'memory_usage': memory_str,
        'memory_bytes': memory_bytes,
        'numeric_columns': len(numeric_cols),
        'categorical_columns': len(cat_cols),
        'datetime_columns': len(date_cols),
        'boolean_columns': len(bool_cols),
        'numeric_col_names': numeric_cols,
        'categorical_col_names': cat_cols,
        'datetime_col_names': date_cols,
    }


def profile_columns(df):
    """
    Generate column-level profile for every column.

    Returns:
        list of dicts, one per column
    """
    profiles = []

    for col in df.columns:
        series = df[col]
        profile = {
            'column': col,
            'dtype': str(series.dtype),
            'count': int(series.count()),
            'missing': int(series.isnull().sum()),
            'missing_pct': round(series.isnull().mean() * 100, 1),
            'unique': int(series.nunique()),
            'unique_pct': round(series.nunique() / max(len(series), 1) * 100, 1),
        }

        if pd.api.types.is_numeric_dtype(series):
            values = series.dropna()
            if len(values) > 0:
                profile.update({
                    'mean': round(float(values.mean()), 2),
                    'std': round(float(values.std()), 2),
                    'min': round(float(values.min()), 2),
                    'q25': round(float(values.quantile(0.25)), 2),
                    'median': round(float(values.median()), 2),
                    'q75': round(float(values.quantile(0.75)), 2),
                    'max': round(float(values.max()), 2),
                    'skewness': round(float(values.skew()), 2),
                    'kurtosis': round(float(values.kurtosis()), 2),
                    'zeros': int((values == 0).sum()),
                    'zeros_pct': round((values == 0).mean() * 100, 1),
                    'negative': int((values < 0).sum()),
                })
            profile['category'] = 'numeric'

        elif pd.api.types.is_datetime64_any_dtype(series):
            values = series.dropna()
            if len(values) > 0:
                profile.update({
                    'min_date': str(values.min()),
                    'max_date': str(values.max()),
                    'date_range_days': (values.max() - values.min()).days,
                })
            profile['category'] = 'datetime'

        else:
            values = series.dropna()
            if len(values) > 0:
                vc = values.value_counts()
                profile.update({
                    'most_common': str(vc.index[0]) if len(vc) > 0 else 'N/A',
                    'most_common_count': int(vc.iloc[0]) if len(vc) > 0 else 0,
                    'most_common_pct': round(vc.iloc[0] / len(values) * 100, 1) if len(vc) > 0 else 0,
                    'least_common': str(vc.index[-1]) if len(vc) > 0 else 'N/A',
                    'avg_length': round(values.astype(str).str.len().mean(), 1),
                })
            profile['category'] = 'categorical'

        profiles.append(profile)

    return profiles


def missing_value_matrix(df):
    """
    Generate a missing value matrix (True = missing).

    Returns:
        pd.DataFrame of booleans (True where null)
    """
    return df.isnull()


def detect_constant_columns(df):
    """Find columns with only one unique value."""
    constants = []
    for col in df.columns:
        if df[col].nunique(dropna=True) <= 1:
            val = df[col].dropna().iloc[0] if df[col].count() > 0 else 'N/A'
            constants.append({'column': col, 'value': str(val)})
    return constants


def detect_high_cardinality(df, threshold=0.9):
    """Find categorical columns where almost every row is unique."""
    high_card = []
    cat_cols = df.select_dtypes(include=['object', 'category']).columns
    for col in cat_cols:
        ratio = df[col].nunique() / max(len(df), 1)
        if ratio > threshold:
            high_card.append({
                'column': col,
                'unique_count': int(df[col].nunique()),
                'unique_pct': round(ratio * 100, 1),
            })
    return high_card


def detect_zero_variance(df):
    """Find numeric columns with zero variance."""
    zero_var = []
    for col in df.select_dtypes(include='number').columns:
        if df[col].std() == 0 or df[col].nunique() <= 1:
            zero_var.append(col)
    return zero_var


def get_correlation_pairs(df, min_corr=0.5):
    """
    Get all highly correlated column pairs.

    Returns:
        list of dicts: [{'col1', 'col2', 'correlation'}, ...]
    """
    numeric_df = df.select_dtypes(include='number')
    if numeric_df.shape[1] < 2:
        return []

    corr = numeric_df.corr()
    pairs = []
    for i in range(len(corr.columns)):
        for j in range(i + 1, len(corr.columns)):
            val = corr.iloc[i, j]
            if abs(val) >= min_corr:
                pairs.append({
                    'col1': corr.columns[i],
                    'col2': corr.columns[j],
                    'correlation': round(val, 3),
                    'strength': 'Strong' if abs(val) > 0.8 else 'Moderate',
                    'direction': 'Positive' if val > 0 else 'Negative',
                })
    pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)
    return pairs
