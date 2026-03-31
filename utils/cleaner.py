"""
MODULE 2: DATA CLEANING ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Automated preprocessing pipeline:
  • Duplicate removal
  • Missing value imputation
  • Data type correction
  • Column name standardization
  • Comprehensive cleaning report
"""

import pandas as pd
import numpy as np
import re


def clean_data(df):
    """
    Run the full cleaning pipeline on a dataframe.

    Args:
        df: pd.DataFrame — the raw dataframe

    Returns:
        tuple: (cleaned_df, cleaning_report)
            cleaning_report is a dict with details of all changes made.
    """
    report = {}
    df_clean = df.copy()
    original_shape = df_clean.shape

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

        # Try to convert object columns to datetime
        if df_clean[col].dtype == 'object':
            converted = _try_convert_datetime(df_clean[col])
            if converted is not None:
                df_clean[col] = converted
                type_changes[col] = f"{original_dtype} → datetime64"
                continue

            # Try to convert to numeric
            converted = _try_convert_numeric(df_clean[col])
            if converted is not None:
                df_clean[col] = converted
                type_changes[col] = f"{original_dtype} → {converted.dtype}"
                continue

            # Strip whitespace from string columns
            df_clean[col] = df_clean[col].astype(str).str.strip()

    report['type_conversions'] = type_changes

    # ── 4. Handle missing values ─────────────────────────────────────
    missing_before = df_clean.isnull().sum().to_dict()
    missing_actions = {}

    for col in df_clean.columns:
        n_missing = df_clean[col].isnull().sum()
        if n_missing == 0:
            continue

        if pd.api.types.is_numeric_dtype(df_clean[col]):
            fill_value = round(df_clean[col].mean(), 2)
            df_clean[col] = df_clean[col].fillna(fill_value)
            missing_actions[col] = f"Filled {n_missing} nulls with mean ({fill_value})"
        elif pd.api.types.is_datetime64_any_dtype(df_clean[col]):
            df_clean[col] = df_clean[col].ffill().bfill()
            missing_actions[col] = f"Forward/back-filled {n_missing} null dates"
        else:
            df_clean[col] = df_clean[col].fillna("Unknown")
            missing_actions[col] = f"Filled {n_missing} nulls with 'Unknown'"

    report['missing_values_before'] = {k: int(v) for k, v in missing_before.items() if v > 0}
    report['missing_value_actions'] = missing_actions

    # ── 5. Summary ───────────────────────────────────────────────────
    report['original_shape'] = original_shape
    report['cleaned_shape'] = df_clean.shape
    report['rows_removed'] = original_shape[0] - df_clean.shape[0]
    total_missing = sum(v for v in missing_before.values())
    total_cells = original_shape[0] * original_shape[1]
    report['data_completeness'] = round((1 - total_missing / max(total_cells, 1)) * 100, 1)

    return df_clean, report


def _standardize_column_name(name):
    """Convert column name to clean snake_case."""
    name = str(name).strip()
    # Replace special chars with underscores
    name = re.sub(r'[^\w\s]', '_', name)
    # Replace spaces with underscores
    name = re.sub(r'\s+', '_', name)
    # Remove consecutive underscores
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    # Lowercase
    name = name.lower()
    return name if name else 'unnamed_column'


def _try_convert_datetime(series):
    """Attempt to convert a series to datetime."""
    try:
        # Only try if a reasonable portion looks like dates
        sample = series.dropna().head(20)
        if len(sample) == 0:
            return None
        converted = pd.to_datetime(sample, errors='coerce')
        # If more than 70% converted successfully, convert the whole column
        if converted.notna().mean() > 0.7:
            return pd.to_datetime(series, errors='coerce')
    except Exception:
        pass
    return None


def _try_convert_numeric(series):
    """Attempt to convert a series to numeric."""
    try:
        sample = series.dropna().head(20)
        if len(sample) == 0:
            return None
        # Remove currency symbols and commas for conversion
        cleaned = sample.astype(str).str.replace(r'[$€£¥,]', '', regex=True).str.strip()
        converted = pd.to_numeric(cleaned, errors='coerce')
        # If more than 80% converted, apply to whole column
        if converted.notna().mean() > 0.8:
            full_cleaned = series.astype(str).str.replace(r'[$€£¥,]', '', regex=True).str.strip()
            return pd.to_numeric(full_cleaned, errors='coerce')
    except Exception:
        pass
    return None
