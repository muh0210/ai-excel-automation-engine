"""
MODULE 13: SMART JOIN (Multi-Table Relational Mapping)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Intelligent merging of multiple datasets:
  • Auto-detect join keys via column name similarity + value overlap
  • Handle name mismatches (e.g. "Emp_ID" vs "EmployeeNumber")
  • Preview before merging
  • Join quality reporting
"""

import pandas as pd
import numpy as np
from difflib import SequenceMatcher


def _normalize_col_name(name):
    """Normalize column name for comparison."""
    import re
    name = str(name).lower().strip()
    name = re.sub(r'[^a-z0-9]', '', name)
    return name


def _name_similarity(name1, name2):
    """Compute similarity between two column names."""
    n1 = _normalize_col_name(name1)
    n2 = _normalize_col_name(name2)

    # Exact match after normalization
    if n1 == n2:
        return 1.0

    # One contains the other
    if n1 in n2 or n2 in n1:
        return 0.85

    # Sequence matcher
    return SequenceMatcher(None, n1, n2).ratio()


def _value_overlap(series1, series2):
    """Compute what fraction of values overlap between two series."""
    try:
        s1 = set(series1.dropna().astype(str).str.strip().str.lower().unique())
        s2 = set(series2.dropna().astype(str).str.strip().str.lower().unique())

        if not s1 or not s2:
            return 0.0

        intersection = s1 & s2
        # Overlap relative to the smaller set (Jaccard-like)
        overlap = len(intersection) / min(len(s1), len(s2))
        return round(overlap, 3)
    except Exception:
        return 0.0


def detect_join_keys(df1, df2, top_n=5):
    """
    Auto-detect the best join key candidates between two dataframes.

    Uses:
      - Column name similarity (fuzzy matching)
      - Data type compatibility
      - Value overlap analysis

    Returns:
        list of dicts: [{
            'col1': str, 'col2': str,
            'name_similarity': float,
            'value_overlap': float,
            'confidence': float,
            'dtype_match': bool
        }, ...]
    """
    candidates = []

    for col1 in df1.columns:
        for col2 in df2.columns:
            # Name similarity
            name_sim = _name_similarity(col1, col2)

            # Skip very low similarity
            if name_sim < 0.3:
                continue

            # Data type compatibility
            dtype_match = (
                (pd.api.types.is_numeric_dtype(df1[col1]) and pd.api.types.is_numeric_dtype(df2[col2])) or
                (pd.api.types.is_string_dtype(df1[col1]) and pd.api.types.is_string_dtype(df2[col2])) or
                (pd.api.types.is_datetime64_any_dtype(df1[col1]) and pd.api.types.is_datetime64_any_dtype(df2[col2]))
            )

            # Value overlap (sample for performance)
            s1 = df1[col1].head(1000)
            s2 = df2[col2].head(1000)
            val_overlap = _value_overlap(s1, s2) if dtype_match or name_sim > 0.5 else 0.0

            # Composite confidence score
            confidence = (name_sim * 0.4 + val_overlap * 0.4 + (0.2 if dtype_match else 0.0))

            if confidence > 0.2:
                candidates.append({
                    'col1': col1,
                    'col2': col2,
                    'name_similarity': round(name_sim, 2),
                    'value_overlap': round(val_overlap, 2),
                    'confidence': round(confidence, 2),
                    'dtype_match': dtype_match,
                })

    candidates.sort(key=lambda x: x['confidence'], reverse=True)
    return candidates[:top_n]


def smart_merge(df1, df2, left_key, right_key, how='left'):
    """
    Merge two dataframes with quality reporting.

    Args:
        df1, df2: DataFrames to merge
        left_key: column name from df1
        right_key: column name from df2
        how: 'left', 'right', 'inner', 'outer'

    Returns:
        dict: {
            'merged_df': pd.DataFrame,
            'matched_rows': int,
            'unmatched_left': int,
            'unmatched_right': int,
            'quality_score': float,
            'quality_label': str,
        }
    """
    try:
        # Ensure comparable types
        df1_copy = df1.copy()
        df2_copy = df2.copy()

        # Normalize key values for matching
        df1_copy['_merge_key'] = df1_copy[left_key].astype(str).str.strip().str.lower()
        df2_copy['_merge_key'] = df2_copy[right_key].astype(str).str.strip().str.lower()

        merged = df1_copy.merge(df2_copy, on='_merge_key', how=how, indicator=True, suffixes=('', '_joined'))

        matched = int((merged['_merge'] == 'both').sum())
        left_only = int((merged['_merge'] == 'left_only').sum())
        right_only = int((merged['_merge'] == 'right_only').sum())

        # Remove helper columns
        merged = merged.drop(columns=['_merge_key', '_merge'], errors='ignore')

        total = max(len(df1), 1)
        quality_score = round(matched / total * 100, 1)

        if quality_score > 90:
            quality_label = '🟢 Excellent Match'
        elif quality_score > 70:
            quality_label = '🟡 Good Match'
        elif quality_score > 50:
            quality_label = '🟠 Partial Match'
        else:
            quality_label = '🔴 Poor Match'

        return {
            'merged_df': merged,
            'matched_rows': matched,
            'unmatched_left': left_only,
            'unmatched_right': right_only,
            'quality_score': quality_score,
            'quality_label': quality_label,
            'total_rows_result': len(merged),
        }
    except Exception as e:
        return {
            'error': str(e),
            'merged_df': pd.DataFrame(),
            'matched_rows': 0,
            'quality_score': 0,
            'quality_label': '🔴 Failed',
        }
