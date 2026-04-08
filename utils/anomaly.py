"""
MODULE 6: ANOMALY DETECTION ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Identifies unusual patterns using Z-Score, IQR, and ML-based methods.
ML Methods: Isolation Forest, Local Outlier Factor.
Flags potential errors or significant business events.
"""

import pandas as pd
import numpy as np

# ML-based anomaly detection (optional)
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.neighbors import LocalOutlierFactor
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


def detect_anomalies_zscore(df, column, threshold=2.0):
    """
    Detect anomalies using Z-Score method.

    A data point is anomalous if it's more than `threshold` standard deviations
    from the mean.
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


def detect_anomalies_isolation_forest(df, columns=None, contamination=0.05):
    """
    Detect anomalies using Isolation Forest (ML-based).

    Uses all numeric columns by default. Detects multivariate anomalies
    that single-column methods might miss.

    Args:
        df: DataFrame
        columns: list of numeric column names (None = all numeric)
        contamination: expected proportion of anomalies (0.01 to 0.5)

    Returns:
        dict with anomaly results
    """
    if not SKLEARN_AVAILABLE:
        return None

    try:
        if columns is None:
            columns = df.select_dtypes(include='number').columns.tolist()

        if len(columns) == 0:
            return None

        # Prepare data
        data = df[columns].dropna()
        if len(data) < 10:
            return None

        # Scale features
        scaler = StandardScaler()
        scaled = scaler.fit_transform(data)

        # Fit Isolation Forest
        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        predictions = iso_forest.fit_predict(scaled)
        scores = iso_forest.decision_function(scaled)

        # Map predictions: -1 = anomaly, 1 = normal
        anomaly_mask_data = predictions == -1
        full_mask = pd.Series([False] * len(df), index=df.index)
        full_mask.loc[data.index] = anomaly_mask_data

        # Anomaly scores (lower = more anomalous)
        score_series = pd.Series(np.nan, index=df.index)
        score_series.loc[data.index] = scores

        return {
            'anomaly_mask': full_mask,
            'anomalies_df': df[full_mask].copy(),
            'count': int(full_mask.sum()),
            'method': 'Isolation Forest',
            'columns_used': columns,
            'contamination': contamination,
            'anomaly_scores': score_series,
            'threshold_upper': None,
            'threshold_lower': None,
        }
    except Exception as e:
        return {'error': str(e), 'count': 0, 'anomaly_mask': pd.Series([False] * len(df), index=df.index),
                'anomalies_df': pd.DataFrame(), 'method': 'Isolation Forest',
                'threshold_upper': None, 'threshold_lower': None}


def detect_anomalies_lof(df, columns=None, contamination=0.05, n_neighbors=20):
    """
    Detect anomalies using Local Outlier Factor (ML-based).

    Detects anomalies based on local density — points in low-density regions
    are flagged as anomalies.

    Args:
        df: DataFrame
        columns: list of numeric column names
        contamination: expected proportion of anomalies
        n_neighbors: number of neighbors for density estimation

    Returns:
        dict with anomaly results
    """
    if not SKLEARN_AVAILABLE:
        return None

    try:
        if columns is None:
            columns = df.select_dtypes(include='number').columns.tolist()

        if len(columns) == 0:
            return None

        data = df[columns].dropna()
        if len(data) < max(n_neighbors + 1, 10):
            return None

        scaler = StandardScaler()
        scaled = scaler.fit_transform(data)

        lof = LocalOutlierFactor(
            n_neighbors=min(n_neighbors, len(data) - 1),
            contamination=contamination
        )
        predictions = lof.fit_predict(scaled)
        scores = lof.negative_outlier_factor_

        anomaly_mask_data = predictions == -1
        full_mask = pd.Series([False] * len(df), index=df.index)
        full_mask.loc[data.index] = anomaly_mask_data

        score_series = pd.Series(np.nan, index=df.index)
        score_series.loc[data.index] = scores

        return {
            'anomaly_mask': full_mask,
            'anomalies_df': df[full_mask].copy(),
            'count': int(full_mask.sum()),
            'method': 'Local Outlier Factor',
            'columns_used': columns,
            'contamination': contamination,
            'anomaly_scores': score_series,
            'threshold_upper': None,
            'threshold_lower': None,
        }
    except Exception as e:
        return {'error': str(e), 'count': 0, 'anomaly_mask': pd.Series([False] * len(df), index=df.index),
                'anomalies_df': pd.DataFrame(), 'method': 'Local Outlier Factor',
                'threshold_upper': None, 'threshold_lower': None}


def detect_all_anomalies(df, method='zscore', threshold=2.0):
    """
    Detect anomalies across all numeric columns using statistical methods.
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


def detect_ml_anomalies(df, method='isolation_forest', contamination=0.05):
    """
    Detect multivariate anomalies using ML methods.

    Args:
        df: DataFrame
        method: 'isolation_forest' or 'lof'
        contamination: expected anomaly ratio

    Returns:
        dict with anomaly results or None
    """
    if not SKLEARN_AVAILABLE:
        return None

    if method == 'isolation_forest':
        return detect_anomalies_isolation_forest(df, contamination=contamination)
    elif method == 'lof':
        return detect_anomalies_lof(df, contamination=contamination)
    return None


def anomaly_summary(results):
    """Generate a human-readable anomaly summary."""
    if not results:
        return ["No anomalies detected across any numeric column. Data appears clean and consistent."]

    summaries = []
    total_anomalies = sum(r['count'] for r in results.values())

    summaries.append(f"**{total_anomalies} anomalies** detected across **{len(results)} column(s)**:")

    for col, result in results.items():
        method = result['method']
        count = result['count']
        lower = result.get('threshold_lower')
        upper = result.get('threshold_upper')
        if lower is not None and upper is not None:
            summaries.append(
                f"  - **{col}**: {count} anomalous value(s) "
                f"(outside [{lower:,.2f}, {upper:,.2f}] via {method})"
            )
        else:
            summaries.append(
                f"  - **{col}**: {count} anomalous value(s) detected via {method}"
            )

    return summaries


def ml_anomaly_summary(result):
    """Generate summary for ML-based anomaly detection."""
    if result is None:
        return ["ML anomaly detection not available (scikit-learn not installed)."]

    if result.get('error'):
        return [f"ML detection error: {result['error']}"]

    method = result.get('method', 'ML')
    count = result.get('count', 0)
    cols = result.get('columns_used', [])

    summaries = [
        f"**{method}** analyzed {len(cols)} numeric column(s) simultaneously.",
        f"**{count} multivariate anomalies** detected (data points that are unusual "
        f"considering ALL numeric features together)."
    ]

    if count > 0:
        summaries.append(
            "These anomalies may not be obvious when looking at individual columns, "
            "but stand out when considering the combination of all features."
        )

    return summaries
