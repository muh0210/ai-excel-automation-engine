"""
MODULE 2: DATA CLEANING ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Automated preprocessing pipeline:
  • Duplicate removal
  • Missing value imputation (detects empty strings, spaces, N/A, -, etc.)
  • Data type correction
  • Column name standardization
  • Comprehensive cleaning report with per-cell detail
"""

import pandas as pd
import numpy as np
import re


# Values that should be treated as missing/null
MISSING_MARKERS = [
    '', ' ', 'nan', 'NaN', 'NAN', 'null', 'NULL', 'none', 'None', 'NONE',
    'n/a', 'N/A', 'NA', 'na', '#N/A', '#NA', '#REF!', '#VALUE!', '#DIV/0!',
    '-', '--', '---', '.', '..', 'missing', 'Missing', 'MISSING',
    'undefined', 'not available', 'not applicable', 'nil', 'NIL',
]


def clean_data(df):
    """
    Run the full cleaning pipeline on a dataframe.

    Returns:
        tuple: (cleaned_df, cleaning_report)
    """
    report = {}
    df_clean = df.copy()
    original_shape = df_clean.shape

    # ── 0. Convert known missing markers to NaN FIRST ────────────────
    # This catches empty strings, spaces, "N/A", "-", etc. that pandas
    # does NOT treat as null by default
    markers_replaced = {}
    for col in df_clean.columns:
        before_nulls = df_clean[col].isnull().sum()

        # For object/string columns, check for missing markers
        if df_clean[col].dtype == 'object':
            # Strip whitespace first
            stripped = df_clean[col].astype(str).str.strip()
            mask = stripped.isin(MISSING_MARKERS) | (stripped == '')
            # Don't replace actual string 'nan' from non-null values
            # Only replace if original was string-type
            original_nulls = df_clean[col].isnull()
            combined_mask = mask | original_nulls
            n_new = int(combined_mask.sum() - original_nulls.sum())
            if n_new > 0:
                df_clean.loc[mask & ~original_nulls, col] = np.nan
                markers_replaced[col] = n_new

    report['markers_replaced'] = markers_replaced

    # ── 1. Standardize column names ──────────────────────────────────
    original_columns = list(df_clean.columns)
    df_clean.columns = [_standardize_column_name(col) for col in df_clean.columns]
    renamed = {orig: new for orig, new in zip(original_columns, df_clean.columns) if orig != new}
    report['columns_renamed'] = renamed
    report['column_names'] = list(df_clean.columns)

    # ── 2. Remove duplicate rows ─────────────────────────────────────
    n_duplicates = df_clean.duplicated().sum()
    if n_duplicates > 0:
        df_clean = df_clean.drop_duplicates().reset_index(drop=True)
    report['duplicates_removed'] = int(n_duplicates)

    # ── 3. Fix data types ────────────────────────────────────────────
    type_changes = {}
    for col in df_clean.columns:
        original_dtype = str(df_clean[col].dtype)

        if df_clean[col].dtype == 'object':
            # Try datetime first
            converted = _try_convert_datetime(df_clean[col])
            if converted is not None:
                df_clean[col] = converted
                type_changes[col] = f"{original_dtype} → datetime64"
                continue

            # Try numeric
            converted = _try_convert_numeric(df_clean[col])
            if converted is not None:
                df_clean[col] = converted
                type_changes[col] = f"{original_dtype} → {converted.dtype}"
                continue

            # Strip whitespace from remaining string columns
            df_clean[col] = df_clean[col].where(df_clean[col].isnull(), df_clean[col].astype(str).str.strip())

    report['type_conversions'] = type_changes

    # ── 4. Handle missing values ─────────────────────────────────────
    missing_before = df_clean.isnull().sum().to_dict()
    missing_actions = {}

    for col in df_clean.columns:
        n_missing = int(df_clean[col].isnull().sum())
        if n_missing == 0:
            continue

        # Find which row indices are missing
        missing_rows = df_clean[df_clean[col].isnull()].index.tolist()
        row_info = f" (rows: {', '.join(str(r+1) for r in missing_rows[:10])}{'...' if len(missing_rows) > 10 else ''})"

        if pd.api.types.is_numeric_dtype(df_clean[col]):
            median_val = round(df_clean[col].median(), 2)
            mean_val = round(df_clean[col].mean(), 2)
            # Use median for skewed data, mean for normal
            skew = abs(df_clean[col].dropna().skew()) if len(df_clean[col].dropna()) > 2 else 0
            fill_value = median_val if skew > 1 else mean_val
            fill_method = 'median' if skew > 1 else 'mean'
            df_clean[col] = df_clean[col].fillna(fill_value)
            missing_actions[col] = f"Filled {n_missing} missing cell(s) with {fill_method} ({fill_value}){row_info}"
        elif pd.api.types.is_datetime64_any_dtype(df_clean[col]):
            df_clean[col] = df_clean[col].ffill().bfill()
            missing_actions[col] = f"Forward/back-filled {n_missing} missing date(s){row_info}"
        else:
            df_clean[col] = df_clean[col].fillna("Unknown")
            missing_actions[col] = f"Filled {n_missing} missing cell(s) with 'Unknown'{row_info}"

    report['missing_values_before'] = {k: int(v) for k, v in missing_before.items() if v > 0}
    report['missing_value_actions'] = missing_actions

    # ── 5. Summary ───────────────────────────────────────────────────
    report['original_shape'] = original_shape
    report['cleaned_shape'] = df_clean.shape
    report['rows_removed'] = original_shape[0] - df_clean.shape[0]
    total_missing = sum(v for v in missing_before.values())
    # Also count markers that were converted
    total_markers = sum(markers_replaced.values()) if markers_replaced else 0
    total_issues = total_missing + total_markers
    total_cells = original_shape[0] * original_shape[1]
    report['data_completeness'] = round((1 - total_issues / max(total_cells, 1)) * 100, 1)

    return df_clean, report


def _standardize_column_name(name):
    """Convert column name to clean snake_case."""
    name = str(name).strip()
    name = re.sub(r'[^\w\s]', '_', name)
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    name = name.lower()
    return name if name else 'unnamed_column'


def _try_convert_datetime(series):
    """Attempt to convert a series to datetime."""
    try:
        sample = series.dropna().head(20)
        if len(sample) == 0:
            return None
        converted = pd.to_datetime(sample, errors='coerce', format='mixed')
        if converted.notna().mean() > 0.7:
            return pd.to_datetime(series, errors='coerce', format='mixed')
    except Exception:
        pass
    return None


def _try_convert_numeric(series):
    """Attempt to convert a series to numeric."""
    try:
        sample = series.dropna().head(20)
        if len(sample) == 0:
            return None
        cleaned = sample.astype(str).str.replace(r'[$€£¥,]', '', regex=True).str.strip()
        converted = pd.to_numeric(cleaned, errors='coerce')
        if converted.notna().mean() > 0.8:
            full_cleaned = series.astype(str).str.replace(r'[$€£¥,]', '', regex=True).str.strip()
            result = pd.to_numeric(full_cleaned, errors='coerce')
            # Preserve original NaN positions
            result[series.isnull()] = np.nan
            return result
    except Exception:
        pass
    return None
