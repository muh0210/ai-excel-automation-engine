"""
MODULE 6: ANOMALY DETECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Identifies unusual patterns using Z-Score and IQR methods.
Flags potential errors or significant business events.
"""

import pandas as pd
import numpy as np


def detect_anomalies_zscore(df, column, threshold=2.0):
    """
    Detect anomalies using Z-Score method.

    A data point is anomalous if it's more than `threshold` standard deviations
    from the mean.

    Args:
        df: DataFrame
        column: numeric column name
        threshold: number of std deviations (default: 2.0)

    Returns:
        dict: {
            'anomaly_mask': bool Series,
            'anomalies_df': DataFrame of anomalous rows,
            'count': int,
            'threshold_upper': float,
            'threshold_lower': float,
            'method': str
        }
    """
    if column not in df.columns or not pd.api.types.is_numeric_dtype(df[column]):
        return None

    values = df[column].dropna()
    if len(values) < 5:
        return None

    mean = values.mean()
    std = values.std()

    if std == 0:
        return {
            'anomaly_mask': pd.Series([False] * len(df), index=df.index),
            'anomalies_df': pd.DataFrame(),
            'count': 0,
            'threshold_upper': mean,
            'threshold_lower': mean,
            'method': 'Z-Score'
        }

    z_scores = ((df[column] - mean) / std).abs()
    anomaly_mask = z_scores > threshold

    return {
        'anomaly_mask': anomaly_mask,
        'anomalies_df': df[anomaly_mask].copy(),
        'count': int(anomaly_mask.sum()),
        'threshold_upper': round(mean + threshold * std, 2),
        'threshold_lower': round(mean - threshold * std, 2),
        'method': 'Z-Score',
        'mean': round(mean, 2),
        'std': round(std, 2)
    }


def detect_anomalies_iqr(df, column, multiplier=1.5):
    """
    Detect anomalies using the Interquartile Range (IQR) method.

    A data point is anomalous if it falls outside [Q1 - multiplier*IQR, Q3 + multiplier*IQR].

    Args:
        df: DataFrame
        column: numeric column name
        multiplier: IQR multiplier (default: 1.5)

    Returns:
        dict (same structure as zscore method)
    """
    if column not in df.columns or not pd.api.types.is_numeric_dtype(df[column]):
        return None

    values = df[column].dropna()
    if len(values) < 5:
        return None

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr

    anomaly_mask = (df[column] < lower_bound) | (df[column] > upper_bound)

    return {
        'anomaly_mask': anomaly_mask,
        'anomalies_df': df[anomaly_mask].copy(),
        'count': int(anomaly_mask.sum()),
        'threshold_upper': round(upper_bound, 2),
        'threshold_lower': round(lower_bound, 2),
        'method': 'IQR',
        'q1': round(q1, 2),
        'q3': round(q3, 2),
        'iqr': round(iqr, 2)
    }


def detect_all_anomalies(df, method='zscore', threshold=2.0):
    """
    Detect anomalies across all numeric columns.

    Args:
        df: DataFrame
        method: 'zscore' or 'iqr'
        threshold: sensitivity (Z-Score: std multiplier, IQR: IQR multiplier)

    Returns:
        dict: {column_name: anomaly_result_dict, ...}
    """
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    results = {}

    for col in numeric_cols:
        if method == 'zscore':
            result = detect_anomalies_zscore(df, col, threshold)
        else:
            result = detect_anomalies_iqr(df, col, threshold)

        if result and result['count'] > 0:
            results[col] = result

    return results


def anomaly_summary(results):
    """
    Generate a human-readable anomaly summary.

    Args:
        results: dict from detect_all_anomalies

    Returns:
        list of summary strings
    """
    if not results:
        return ["✅ No anomalies detected across any numeric column. Data appears clean and consistent."]

    summaries = []
    total_anomalies = sum(r['count'] for r in results.values())

    summaries.append(f"🚨 **{total_anomalies} anomalies** detected across **{len(results)} column(s)**:")

    for col, result in results.items():
        method = result['method']
        count = result['count']
        lower = result['threshold_lower']
        upper = result['threshold_upper']
        summaries.append(
            f"  • **{col}**: {count} anomalous value(s) "
            f"(outside [{lower:,.2f}, {upper:,.2f}] via {method})"
        )

    return summaries
