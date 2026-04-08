"""
MODULE 9: DATA TRANSFORMER
━━━━━━━━━━━━━━━━━━━━━━━━━━
Interactive data transformations: column operations, binning,
calculated columns, pivot tables, encoding, and aggregation.
"""

import pandas as pd
import numpy as np


def rename_column(df, old_name, new_name):
    """Rename a single column."""
    if old_name not in df.columns:
        return df, f"Column '{old_name}' not found."
    if new_name in df.columns:
        return df, f"Column '{new_name}' already exists."
    df_new = df.rename(columns={old_name: new_name})
    return df_new, f"Renamed '{old_name}' → '{new_name}'"


def drop_columns(df, columns):
    """Drop one or more columns."""
    existing = [c for c in columns if c in df.columns]
    if not existing:
        return df, "No matching columns found."
    df_new = df.drop(columns=existing)
    return df_new, f"Dropped {len(existing)} column(s): {', '.join(existing)}"


def bin_column(df, column, n_bins=5, labels=None):
    """Convert a numeric column into categorical bins."""
    if column not in df.columns or not pd.api.types.is_numeric_dtype(df[column]):
        return df, "Column not found or not numeric."

    new_col = f"{column}_binned"
    try:
        if labels and len(labels) == n_bins:
            df[new_col] = pd.cut(df[column], bins=n_bins, labels=labels)
        else:
            df[new_col] = pd.cut(df[column], bins=n_bins)
        return df, f"Created '{new_col}' with {n_bins} bins."
    except Exception as e:
        return df, f"Binning failed: {str(e)}"


def create_calculated_column(df, new_col_name, formula_col1, formula_col2, operation):
    """
    Create a new column from two existing columns.

    Operations: 'add', 'subtract', 'multiply', 'divide', 'ratio_pct'
    """
    if formula_col1 not in df.columns or formula_col2 not in df.columns:
        return df, "One or both columns not found."

    try:
        if operation == 'add':
            df[new_col_name] = df[formula_col1] + df[formula_col2]
        elif operation == 'subtract':
            df[new_col_name] = df[formula_col1] - df[formula_col2]
        elif operation == 'multiply':
            df[new_col_name] = df[formula_col1] * df[formula_col2]
        elif operation == 'divide':
            df[new_col_name] = df[formula_col1] / df[formula_col2].replace(0, np.nan)
        elif operation == 'ratio_pct':
            df[new_col_name] = (df[formula_col1] / df[formula_col2].replace(0, np.nan) * 100).round(2)
        else:
            return df, f"Unknown operation: {operation}"

        df[new_col_name] = df[new_col_name].round(2)
        return df, f"Created '{new_col_name}' = {formula_col1} {operation} {formula_col2}"
    except Exception as e:
        return df, f"Calculation failed: {str(e)}"


def build_pivot_table(df, index_col, value_col, agg_func='mean', columns_col=None):
    """
    Build a pivot table.

    Args:
        df: DataFrame
        index_col: row grouping column
        value_col: values to aggregate
        agg_func: 'mean', 'sum', 'count', 'min', 'max'
        columns_col: optional column for cross-tab

    Returns:
        pd.DataFrame (pivot table)
    """
    try:
        if columns_col and columns_col != 'None':
            pivot = pd.pivot_table(
                df, values=value_col, index=index_col,
                columns=columns_col, aggfunc=agg_func, fill_value=0
            )
        else:
            pivot = pd.pivot_table(
                df, values=value_col, index=index_col,
                aggfunc=agg_func
            )
        return pivot.round(2)
    except Exception:
        return None


def custom_aggregation(df, group_col, value_cols, agg_funcs):
    """
    Custom multi-column, multi-function aggregation.

    Args:
        df: DataFrame
        group_col: column to group by
        value_cols: list of columns to aggregate
        agg_funcs: list of functions ('sum', 'mean', 'count', 'min', 'max', 'std')

    Returns:
        pd.DataFrame
    """
    try:
        agg_dict = {col: agg_funcs for col in value_cols}
        result = df.groupby(group_col).agg(agg_dict).round(2)
        # Flatten multi-level columns
        result.columns = ['_'.join(col).strip() for col in result.columns.values]
        return result.reset_index()
    except Exception:
        return None


def filter_dataframe(df, column, operator, value):
    """
    Filter DataFrame by condition.

    Operators: '==', '!=', '>', '<', '>=', '<=', 'contains', 'not_contains'
    """
    try:
        if operator == '==' or operator == 'equals':
            if pd.api.types.is_numeric_dtype(df[column]):
                mask = df[column] == float(value)
            else:
                mask = df[column].astype(str).str.lower() == str(value).lower()
        elif operator == '!=':
            if pd.api.types.is_numeric_dtype(df[column]):
                mask = df[column] != float(value)
            else:
                mask = df[column].astype(str).str.lower() != str(value).lower()
        elif operator == '>':
            mask = df[column] > float(value)
        elif operator == '<':
            mask = df[column] < float(value)
        elif operator == '>=':
            mask = df[column] >= float(value)
        elif operator == '<=':
            mask = df[column] <= float(value)
        elif operator == 'contains':
            mask = df[column].astype(str).str.contains(str(value), case=False, na=False)
        elif operator == 'not_contains':
            mask = ~df[column].astype(str).str.contains(str(value), case=False, na=False)
        else:
            return df, f"Unknown operator: {operator}"

        filtered = df[mask]
        return filtered, f"Filtered to {len(filtered)} rows (from {len(df)})"
    except Exception as e:
        return df, f"Filter error: {str(e)}"


def value_mapping(df, column, mapping_dict):
    """Replace values in a column according to a mapping."""
    try:
        df[column] = df[column].replace(mapping_dict)
        return df, f"Mapped {len(mapping_dict)} values in '{column}'"
    except Exception as e:
        return df, f"Mapping error: {str(e)}"


def one_hot_encode(df, column, drop_original=True):
    """One-hot encode a categorical column."""
    try:
        if column not in df.columns:
            return df, f"Column '{column}' not found."
        dummies = pd.get_dummies(df[column], prefix=column, dtype=int)
        df_new = pd.concat([df, dummies], axis=1)
        if drop_original:
            df_new = df_new.drop(columns=[column])
        return df_new, f"One-hot encoded '{column}' into {len(dummies.columns)} columns"
    except Exception as e:
        return df, f"Encoding error: {str(e)}"
