"""
NATURAL LANGUAGE QUERY ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Regex-based NLQ processor for conversational BI.
Extracted from app.py for separation of concerns.

Supports: aggregation, grouping, filtering, sorting,
top/bottom N, correlation, describe, unique values.
"""

import re
import pandas as pd
from utils.logger import get_logger

log = get_logger(__name__)


def _find_column(df, name):
    """Fuzzy-match a user-typed column name to actual columns."""
    nl = name.lower().strip()
    for c in df.columns:
        if c.lower() == nl:
            return c
    for c in df.columns:
        if nl in c.lower() or c.lower() in nl:
            return c
    return None


def process_nlq(df, query):
    """
    Process a natural-language query against a DataFrame.

    Returns:
        dict: {success, explanation, dataframe, value}
    """
    q = query.lower().strip()
    log.info("NLQ query: %s", q)

    try:
        # Show / list columns
        if 'show columns' in q or 'list columns' in q:
            return {
                'success': True,
                'explanation': f'{len(df.columns)} columns:',
                'dataframe': pd.DataFrame({
                    'Column': df.columns,
                    'Type': [str(d) for d in df.dtypes],
                }),
                'value': None,
            }

        # Group by + aggregate
        m = re.search(
            r'group\s+(?:by\s+)?(\w+)\s+(?:and\s+)?(sum|mean|avg|count|max|min)\s+(?:of\s+)?(\w+)', q
        )
        if m:
            gc, fn, vc = _find_column(df, m.group(1)), m.group(2), _find_column(df, m.group(3))
            if gc and vc:
                fn = 'mean' if fn == 'avg' else fn
                g = df.groupby(gc)[vc].agg(fn).reset_index().sort_values(vc, ascending=False)
                return {
                    'success': True,
                    'explanation': f'{fn.title()} of "{vc}" by "{gc}":',
                    'dataframe': g,
                    'value': None,
                }

        # Compare between groups
        m = re.search(r'compare\s+(\w+)\s+between\s+(\w+)\s+and\s+(\w+)', q)
        if m:
            vc, g1, g2 = _find_column(df, m.group(1)), m.group(2), m.group(3)
            if vc:
                for cc in df.select_dtypes(['object', 'category']).columns:
                    vals = df[cc].astype(str).str.lower()
                    if g1.lower() in vals.values and g2.lower() in vals.values:
                        comp = pd.DataFrame({
                            g1: df[vals == g1.lower()][vc].describe(),
                            g2: df[vals == g2.lower()][vc].describe(),
                        })
                        return {
                            'success': True,
                            'explanation': f'Comparing "{vc}":',
                            'dataframe': comp,
                            'value': None,
                        }

        # Top / bottom N
        m = re.search(r'(top|bottom|highest|lowest)\s+(\d+)\s+(?:by|in|of)?\s*(\w+)', q)
        if m:
            d, n, col = m.group(1), int(m.group(2)), _find_column(df, m.group(3))
            if col and pd.api.types.is_numeric_dtype(df[col]):
                asc = d in ('bottom', 'lowest')
                return {
                    'success': True,
                    'explanation': f'{"Bottom" if asc else "Top"} {n} by "{col}":',
                    'dataframe': df.sort_values(col, ascending=asc).head(n),
                    'value': None,
                }

        # Aggregate (average, sum, min, max, median, count)
        m = re.search(r'(average|avg|mean|sum|total|min|max|median|count)\s+(?:of\s+)?(\w+)', q)
        if m:
            fs, col = m.group(1), _find_column(df, m.group(2))
            if col and pd.api.types.is_numeric_dtype(df[col]):
                fm = {
                    'average': 'mean', 'avg': 'mean', 'mean': 'mean',
                    'sum': 'sum', 'total': 'sum',
                    'min': 'min', 'max': 'max',
                    'median': 'median', 'count': 'count',
                }
                val = getattr(df[col], fm.get(fs, 'mean'))()
                return {
                    'success': True,
                    'explanation': f'{fm.get(fs, "mean").title()} of "{col}":',
                    'dataframe': None,
                    'value': f'{val:,.2f}',
                }

        # Correlation
        m = re.search(r'correlat\w*\s+(?:with\s+)?(\w+)', q)
        if m:
            col = _find_column(df, m.group(1))
            if col and pd.api.types.is_numeric_dtype(df[col]):
                cr = (
                    df.select_dtypes('number')
                    .corr()[col]
                    .drop(col)
                    .sort_values(key=abs, ascending=False)
                    .reset_index()
                )
                cr.columns = ['Column', 'Correlation']
                return {
                    'success': True,
                    'explanation': f'Correlations with "{col}":',
                    'dataframe': cr,
                    'value': None,
                }

        # Filter equals / contains
        m = re.search(r'filter\s+(?:where\s+)?(\w+)\s+(?:is|equals?|==|contains?)\s+(.+)', q)
        if m:
            col, val = _find_column(df, m.group(1)), m.group(2).strip().strip('"\'')
            if col:
                if pd.api.types.is_numeric_dtype(df[col]):
                    try:
                        f = df[df[col] == float(val)]
                    except Exception:
                        f = df[df[col].astype(str).str.contains(val, case=False, na=False)]
                else:
                    f = df[df[col].astype(str).str.contains(val, case=False, na=False)]
                return {
                    'success': True,
                    'explanation': f'{len(f)} rows matched:',
                    'dataframe': f,
                    'value': None,
                }

        # Filter between
        m = re.search(r'filter\s+(?:where\s+)?(\w+)\s+between\s+([\d.]+)\s+and\s+([\d.]+)', q)
        if m:
            col = _find_column(df, m.group(1))
            if col and pd.api.types.is_numeric_dtype(df[col]):
                lo, hi = float(m.group(2)), float(m.group(3))
                f = df[(df[col] >= lo) & (df[col] <= hi)]
                return {
                    'success': True,
                    'explanation': f'{len(f)} rows:',
                    'dataframe': f,
                    'value': None,
                }

        # Sort
        m = re.search(r'sort\s+(?:by\s+)?(\w+)\s*(asc|desc)?', q)
        if m:
            col = _find_column(df, m.group(1))
            if col:
                asc = (m.group(2) or 'desc').startswith('asc')
                return {
                    'success': True,
                    'explanation': f'Sorted by "{col}":',
                    'dataframe': df.sort_values(col, ascending=asc),
                    'value': None,
                }

        # Unique values
        m = re.search(r'unique\s+(\w+)', q)
        if m:
            col = _find_column(df, m.group(1))
            if col:
                vc = df[col].value_counts().reset_index()
                vc.columns = [col, 'Count']
                return {
                    'success': True,
                    'explanation': f'{df[col].nunique()} unique values:',
                    'dataframe': vc,
                    'value': None,
                }

        # Describe
        m = re.search(r'describe\s+(\w+)', q)
        if m:
            col = _find_column(df, m.group(1))
            if col:
                return {
                    'success': True,
                    'explanation': f'Description of "{col}":',
                    'dataframe': df[col].describe().reset_index(),
                    'value': None,
                }

        # No match — show help
        log.warning("NLQ: no pattern matched for query: %s", q)
        return {
            'success': False,
            'explanation': (
                'Try: "top 5 by sales", "average of profit", '
                '"group by region and sum sales", '
                '"compare sales between North and South", '
                '"filter where sales between 100 and 500", '
                '"what correlates with profit?"'
            ),
            'dataframe': None,
            'value': None,
        }

    except Exception as e:
        log.error("NLQ error: %s", e, exc_info=True)
        return {
            'success': False,
            'explanation': f'Error: {e}',
            'dataframe': None,
            'value': None,
        }
