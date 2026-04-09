"""
MODULE 12: UNIFIED SMART JOIN ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Multi-table relational mapping (merged from joiner + smart_join):
  • Auto-detect primary/foreign keys
  • Fuzzy column name matching with SAMPLING (memory-safe)
  • Intelligent merge with quality scoring
  • Preview before merging
  • The VLOOKUP Killer
"""

import pandas as pd
import numpy as np
from difflib import SequenceMatcher
from utils.logger import get_logger
from utils.validator import validate_dataframe, validate_columns_exist

log = get_logger(__name__)

# ── Safety limits ────────────────────────────────────────────────────
MAX_SAMPLE_SIZE = 10_000    # Cap unique‑value scans to prevent OOM
MIN_NAME_SIM = 0.3          # Skip column pairs below this threshold


def detect_key_columns(df):
    """
    Auto-detect likely key/ID columns in a DataFrame.

    Returns:
        list of dicts: [{'column', 'score', 'reason'}, ...]
    """
    validate_dataframe(df, "detect_key_columns input")
    candidates = []
    id_keywords = ['id', 'key', 'code', 'number', 'no', 'num', 'pk', 'uuid',
                   'ref', 'reference', 'index', 'identifier']

    for col in df.columns:
        score = 0
        reasons = []
        col_lower = col.lower().replace('_', '').replace(' ', '')

        for kw in id_keywords:
            if kw in col_lower:
                score += 30
                reasons.append(f'name contains "{kw}"')
                break

        uniqueness = df[col].nunique() / max(len(df), 1)
        if uniqueness > 0.9:
            score += 40
            reasons.append(f'{uniqueness*100:.0f}% unique values')
        elif uniqueness > 0.5:
            score += 20
            reasons.append(f'{uniqueness*100:.0f}% unique values')

        if df[col].isnull().sum() == 0:
            score += 10
            reasons.append('no nulls')

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


def _sampled_value_overlap(series1, series2):
    """
    Compute value overlap between two series using SAMPLED unique values.
    Caps at MAX_SAMPLE_SIZE to prevent memory explosion on large datasets.
    """
    try:
        s1 = set(
            series1.dropna()
            .astype(str).str.strip().str.lower()
            .head(MAX_SAMPLE_SIZE).unique()
        )
        s2 = set(
            series2.dropna()
            .astype(str).str.strip().str.lower()
            .head(MAX_SAMPLE_SIZE).unique()
        )
        if not s1 or not s2:
            return 0.0
        intersection = len(s1 & s2)
        return round(intersection / min(len(s1), len(s2)), 3)
    except Exception:
        return 0.0


def find_matching_columns(df1, df2, threshold=0.6):
    """
    Find columns in df2 that likely match columns in df1,
    even if names are slightly different.

    Uses fuzzy string matching on column names AND sampled value overlap.
    Memory-safe: caps unique value scans at MAX_SAMPLE_SIZE.

    Returns:
        list of dicts: [{'col1', 'col2', 'name_similarity', 'value_overlap', 'match_score'}, ...]
    """
    validate_dataframe(df1, "left table")
    validate_dataframe(df2, "right table")
    matches = []

    for col1 in df1.columns:
        for col2 in df2.columns:
            # Name similarity
            n1 = col1.lower().replace('_', '').replace(' ', '')
            n2 = col2.lower().replace('_', '').replace(' ', '')
            name_sim = SequenceMatcher(None, n1, n2).ratio()

            # Early exit for very low similarity
            if name_sim < MIN_NAME_SIM:
                continue

            # Value overlap (sampled)
            value_overlap = 0.0
            dtype_compatible = (
                (df1[col1].dtype == 'object' and df2[col2].dtype == 'object') or
                (df1[col1].dtype == df2[col2].dtype)
            )
            if dtype_compatible or name_sim > 0.5:
                value_overlap = _sampled_value_overlap(df1[col1], df2[col2])

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

    log.info("Column matching: %d pair(s) found between %d×%d columns",
             len(unique_matches), len(df1.columns), len(df2.columns))
    return unique_matches


def smart_join(df1, df2, left_on, right_on, how='left'):
    """
    Perform an intelligent join between two DataFrames with quality scoring.

    Merged from the old joiner.smart_join + smart_join.smart_merge —
    now a single unified engine.

    Args:
        df1: left DataFrame
        df2: right DataFrame
        left_on: column name in df1
        right_on: column name in df2
        how: 'left', 'right', 'inner', 'outer'

    Returns:
        dict with merged DataFrame, join statistics, and quality score
    """
    try:
        validate_dataframe(df1, "left table")
        validate_dataframe(df2, "right table")
        validate_columns_exist(df1, left_on, "left table")
        validate_columns_exist(df2, right_on, "right table")

        df1_copy = df1.copy()
        df2_copy = df2.copy()

        # Normalize join keys for better matching
        if df1_copy[left_on].dtype == 'object':
            df1_copy['_merge_key'] = df1_copy[left_on].astype(str).str.strip().str.lower()
        else:
            df1_copy['_merge_key'] = df1_copy[left_on]
        if df2_copy[right_on].dtype == 'object':
            df2_copy['_merge_key'] = df2_copy[right_on].astype(str).str.strip().str.lower()
        else:
            df2_copy['_merge_key'] = df2_copy[right_on]

        # Merge with indicator
        merged = pd.merge(
            df1_copy, df2_copy,
            on='_merge_key', how=how,
            indicator=True, suffixes=('', '_joined'),
        )

        matched = int((merged['_merge'] == 'both').sum())
        left_only = int((merged['_merge'] == 'left_only').sum())
        right_only = int((merged['_merge'] == 'right_only').sum())

        # Clean up helper columns
        merged = merged.drop(columns=['_merge_key', '_merge'], errors='ignore')

        # Quality scoring (from smart_join.smart_merge)
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

        log.info("Join complete — %d rows, quality %.1f%% (%s)",
                 len(merged), quality_score, quality_label)

        return {
            'merged_df': merged,
            'left_rows': len(df1),
            'right_rows': len(df2),
            'merged_rows': len(merged),
            'left_matched': matched,
            'left_unmatched': left_only,
            'right_matched': int(len(df2) - right_only),
            'right_unmatched': right_only,
            'match_rate_left': round(matched / total * 100, 1),
            'match_rate_right': round((len(df2) - right_only) / max(len(df2), 1) * 100, 1),
            'new_columns': len(merged.columns) - len(df1.columns),
            'join_type': how,
            'quality_score': quality_score,
            'quality_label': quality_label,
        }
    except Exception as e:
        log.error("Join failed: %s", e, exc_info=True)
        return {'error': str(e)}


def preview_join(df1, df2, left_on, right_on, n=5):
    """
    Generate a preview of what the join would look like.

    Returns:
        dict with sample matched and unmatched records
    """
    try:
        if df1[left_on].dtype == 'object':
            keys1 = set(
                df1[left_on].astype(str).str.strip().str.lower()
                .dropna().head(MAX_SAMPLE_SIZE).unique()
            )
        else:
            keys1 = set(df1[left_on].dropna().head(MAX_SAMPLE_SIZE).unique())

        if df2[right_on].dtype == 'object':
            keys2 = set(
                df2[right_on].astype(str).str.strip().str.lower()
                .dropna().head(MAX_SAMPLE_SIZE).unique()
            )
        else:
            keys2 = set(df2[right_on].dropna().head(MAX_SAMPLE_SIZE).unique())

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
        log.error("Preview join failed: %s", e, exc_info=True)
        return {'error': str(e)}
