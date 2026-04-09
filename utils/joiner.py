"""
MODULE 12: SMART JOIN ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Multi-table relational mapping:
  • Auto-detect primary/foreign keys
  • Fuzzy column name matching
  • Intelligent merge with preview
  • The VLOOKUP Killer
"""

import pandas as pd
import numpy as np
from difflib import SequenceMatcher


def detect_key_columns(df):
    """
    Auto-detect likely key/ID columns in a DataFrame.

    Returns:
        list of dicts: [{'column', 'score', 'reason'}, ...]
    """
    candidates = []
    id_keywords = ['id', 'key', 'code', 'number', 'no', 'num', 'pk', 'uuid',
                   'ref', 'reference', 'index', 'identifier']

    for col in df.columns:
        score = 0
        reasons = []
        col_lower = col.lower().replace('_', '').replace(' ', '')

        # Keyword match
        for kw in id_keywords:
            if kw in col_lower:
                score += 30
                reasons.append(f'name contains "{kw}"')
                break

        # High uniqueness (>90%)
        uniqueness = df[col].nunique() / max(len(df), 1)
        if uniqueness > 0.9:
            score += 40
            reasons.append(f'{uniqueness*100:.0f}% unique values')
        elif uniqueness > 0.5:
            score += 20
            reasons.append(f'{uniqueness*100:.0f}% unique values')

        # No nulls
        if df[col].isnull().sum() == 0:
            score += 10
            reasons.append('no nulls')

        # Not too many values (probably not a free-text field)
        if df[col].nunique() < len(df) * 1.1:
            score += 5

        if score >= 30:
            candidates.append({
                'column': col,
                'score': score,
                'reason': ', '.join(reasons),
                'unique_values': int(df[col].nunique()),
                'dtype': str(df[col].dtype),
            })

    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates


def find_matching_columns(df1, df2, threshold=0.6):
    """
    Find columns in df2 that likely match columns in df1,
    even if names are slightly different.

    Uses fuzzy string matching on column names AND value overlap.

    Returns:
        list of dicts: [{'col1', 'col2', 'name_similarity', 'value_overlap', 'match_score'}, ...]
    """
    matches = []

    for col1 in df1.columns:
        for col2 in df2.columns:
            # Name similarity
            name_sim = SequenceMatcher(
                None,
                col1.lower().replace('_', '').replace(' ', ''),
                col2.lower().replace('_', '').replace(' ', '')
            ).ratio()

            # Value overlap (for categorical/string columns)
            value_overlap = 0.0
            if df1[col1].dtype == 'object' and df2[col2].dtype == 'object':
                set1 = set(df1[col1].dropna().astype(str).str.lower().unique())
                set2 = set(df2[col2].dropna().astype(str).str.lower().unique())
                if set1 and set2:
                    intersection = len(set1 & set2)
                    value_overlap = intersection / min(len(set1), len(set2))
            elif df1[col1].dtype == df2[col2].dtype:
                # For numeric, check range overlap
                if pd.api.types.is_numeric_dtype(df1[col1]):
                    set1 = set(df1[col1].dropna().unique())
                    set2 = set(df2[col2].dropna().unique())
                    if set1 and set2:
                        intersection = len(set1 & set2)
                        value_overlap = intersection / min(len(set1), len(set2))

            # Combined score
            match_score = name_sim * 0.6 + value_overlap * 0.4

            if match_score > threshold or name_sim > 0.8 or value_overlap > 0.7:
                matches.append({
                    'col1': col1,
                    'col2': col2,
                    'name_similarity': round(name_sim, 3),
                    'value_overlap': round(value_overlap, 3),
                    'match_score': round(match_score, 3),
                })

    matches.sort(key=lambda x: x['match_score'], reverse=True)

    # Remove duplicate pairs (keep best match per col1)
    seen_col1 = set()
    seen_col2 = set()
    unique_matches = []
    for m in matches:
        if m['col1'] not in seen_col1 and m['col2'] not in seen_col2:
            unique_matches.append(m)
            seen_col1.add(m['col1'])
            seen_col2.add(m['col2'])

    return unique_matches


def smart_join(df1, df2, left_on, right_on, how='left'):
    """
    Perform an intelligent join between two DataFrames.

    Args:
        df1: left DataFrame
        df2: right DataFrame
        left_on: column name in df1
        right_on: column name in df2
        how: 'left', 'right', 'inner', 'outer'

    Returns:
        dict with merged DataFrame and join statistics
    """
    try:
        # Normalize join keys for better matching
        df1_copy = df1.copy()
        df2_copy = df2.copy()

        # If both are string type, normalize case and whitespace
        if df1_copy[left_on].dtype == 'object':
            df1_copy[left_on] = df1_copy[left_on].astype(str).str.strip().str.lower()
        if df2_copy[right_on].dtype == 'object':
            df2_copy[right_on] = df2_copy[right_on].astype(str).str.strip().str.lower()

        # Perform merge
        merged = pd.merge(df1_copy, df2_copy, left_on=left_on, right_on=right_on, how=how, suffixes=('', '_joined'))

        # Calculate statistics
        left_matched = df1_copy[left_on].isin(df2_copy[right_on]).sum()
        right_matched = df2_copy[right_on].isin(df1_copy[left_on]).sum()

        return {
            'merged_df': merged,
            'left_rows': len(df1),
            'right_rows': len(df2),
            'merged_rows': len(merged),
            'left_matched': int(left_matched),
            'left_unmatched': len(df1) - int(left_matched),
            'right_matched': int(right_matched),
            'right_unmatched': len(df2) - int(right_matched),
            'match_rate_left': round(left_matched / max(len(df1), 1) * 100, 1),
            'match_rate_right': round(right_matched / max(len(df2), 1) * 100, 1),
            'new_columns': len(merged.columns) - len(df1.columns),
            'join_type': how,
        }
    except Exception as e:
        return {'error': str(e)}


def preview_join(df1, df2, left_on, right_on, n=5):
    """
    Generate a preview of what the join would look like.

    Returns:
        dict with sample matched and unmatched records
    """
    try:
        # Sample matched
        if df1[left_on].dtype == 'object':
            keys1 = set(df1[left_on].astype(str).str.strip().str.lower().dropna())
        else:
            keys1 = set(df1[left_on].dropna())

        if df2[right_on].dtype == 'object':
            keys2 = set(df2[right_on].astype(str).str.strip().str.lower().dropna())
        else:
            keys2 = set(df2[right_on].dropna())

        matched_keys = keys1 & keys2
        unmatched_left = keys1 - keys2
        unmatched_right = keys2 - keys1

        return {
            'matched_keys_sample': list(matched_keys)[:n],
            'unmatched_left_sample': list(unmatched_left)[:n],
            'unmatched_right_sample': list(unmatched_right)[:n],
            'total_matched': len(matched_keys),
            'total_unmatched_left': len(unmatched_left),
            'total_unmatched_right': len(unmatched_right),
        }
    except Exception as e:
        return {'error': str(e)}
