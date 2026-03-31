"""
MODULE 5: AI INSIGHT ENGINE 🔥
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Converts raw data into human-readable business insights.
This is the KILLER FEATURE — no AI API needed, pure analytical intelligence.
"""

import pandas as pd
import numpy as np


def generate_insights(df, cleaning_report=None):
    """
    Generate comprehensive AI-style business insights from the data.

    Args:
        df: cleaned DataFrame
        cleaning_report: optional dict from cleaner module

    Returns:
        list of dicts: [{'icon', 'category', 'insight', 'severity'}, ...]
        severity: 'info', 'positive', 'warning', 'critical'
    """
    insights = []

    # ── Data Quality Insights ────────────────────────────────────────
    if cleaning_report:
        completeness = cleaning_report.get('data_completeness', 100)
        if completeness >= 98:
            insights.append({
                'icon': '✅',
                'category': 'Data Quality',
                'insight': f'Excellent data quality — {completeness}% completeness after cleaning.',
                'severity': 'positive'
            })
        elif completeness >= 90:
            insights.append({
                'icon': '⚠️',
                'category': 'Data Quality',
                'insight': f'Good data quality at {completeness}% completeness. Some missing values were imputed.',
                'severity': 'info'
            })
        else:
            insights.append({
                'icon': '🚨',
                'category': 'Data Quality',
                'insight': f'Data quality concern — only {completeness}% completeness. Results may be affected by imputed values.',
                'severity': 'warning'
            })

        dups = cleaning_report.get('duplicates_removed', 0)
        if dups > 0:
            insights.append({
                'icon': '🔄',
                'category': 'Data Quality',
                'insight': f'{dups} duplicate row{"s" if dups > 1 else ""} detected and removed for accurate analysis.',
                'severity': 'info'
            })

    # ── Numeric Column Insights ──────────────────────────────────────
    numeric_cols = df.select_dtypes(include='number').columns.tolist()

    for col in numeric_cols[:5]:  # Limit to top 5 numeric columns
        values = df[col].dropna()
        if len(values) < 3:
            continue

        mean_val = values.mean()
        std_val = values.std()
        cv = (std_val / abs(mean_val) * 100) if abs(mean_val) > 1e-10 else 0

        # Variability insight
        if cv > 80:
            insights.append({
                'icon': '📊',
                'category': 'Variability',
                'insight': f'High variability in "{col}" (CV: {cv:.1f}%) — values are widely spread, indicating inconsistent performance or diverse data groups.',
                'severity': 'warning'
            })
        elif cv < 15:
            insights.append({
                'icon': '📊',
                'category': 'Stability',
                'insight': f'"{col}" shows very stable values (CV: {cv:.1f}%) — consistent and predictable.',
                'severity': 'positive'
            })

        # Skewness insight
        skewness = values.skew()
        if abs(skewness) > 1.5:
            direction = 'right (positive)' if skewness > 0 else 'left (negative)'
            insights.append({
                'icon': '📐',
                'category': 'Distribution',
                'insight': f'"{col}" is heavily skewed to the {direction} (skew: {skewness:.2f}). Consider using median instead of mean for this metric.',
                'severity': 'info'
            })

        # Trend insight (if data has a natural order)
        if len(values) >= 10:
            n = max(1, len(values) // 5)
            first_chunk = values.head(n).mean()
            last_chunk = values.tail(n).mean()
            if abs(first_chunk) > 1e-10:
                change = ((last_chunk - first_chunk) / abs(first_chunk)) * 100
                if change > 15:
                    insights.append({
                        'icon': '📈',
                        'category': 'Trend',
                        'insight': f'"{col}" shows a significant upward trend (+{change:.1f}% from start to end).',
                        'severity': 'positive'
                    })
                elif change < -15:
                    insights.append({
                        'icon': '📉',
                        'category': 'Trend',
                        'insight': f'"{col}" shows a declining trend ({change:.1f}% from start to end). Investigate potential causes.',
                        'severity': 'warning'
                    })

    # ── Categorical Column Insights ──────────────────────────────────
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    for col in cat_cols[:3]:
        value_counts = df[col].value_counts()
        n_unique = len(value_counts)

        if n_unique <= 1:
            insights.append({
                'icon': '⚡',
                'category': 'Low Variance',
                'insight': f'Column "{col}" has only {n_unique} unique value(s) — may not contribute to analysis.',
                'severity': 'info'
            })
        elif n_unique <= 20:
            top = value_counts.index[0]
            top_pct = (value_counts.iloc[0] / len(df)) * 100
            if top_pct > 50:
                insights.append({
                    'icon': '🏆',
                    'category': 'Dominance',
                    'insight': f'"{top}" dominates "{col}" at {top_pct:.1f}% of all records.',
                    'severity': 'info'
                })

    # ── Cross-Column Insights ────────────────────────────────────────
    if len(numeric_cols) >= 2:
        corr_matrix = df[numeric_cols].corr()
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.8:
                    relation = 'strong positive' if corr_val > 0 else 'strong negative'
                    insights.append({
                        'icon': '🔗',
                        'category': 'Correlation',
                        'insight': f'"{numeric_cols[i]}" and "{numeric_cols[j]}" have a {relation} correlation ({corr_val:.2f}). Changes in one strongly predict changes in the other.',
                        'severity': 'info'
                    })

    # ── Dataset Size Insights ────────────────────────────────────────
    n_rows = len(df)
    if n_rows < 30:
        insights.append({
            'icon': '⚠️',
            'category': 'Sample Size',
            'insight': f'Small dataset ({n_rows} rows). Statistical results should be interpreted with caution.',
            'severity': 'warning'
        })
    elif n_rows > 10000:
        insights.append({
            'icon': '📦',
            'category': 'Dataset',
            'insight': f'Large dataset with {n_rows:,} rows — analysis results are statistically robust.',
            'severity': 'positive'
        })

    return insights


def generate_summary_narrative(df, kpis, insights):
    """
    Generate a natural language summary paragraph for the report.

    Returns:
        str: A multi-sentence narrative summarizing the data
    """
    parts = []

    parts.append(f"This dataset contains {len(df):,} records across {len(df.columns)} columns.")

    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    if numeric_cols and kpis:
        primary_col = numeric_cols[0]
        if primary_col in kpis:
            k = kpis[primary_col]
            parts.append(
                f"The primary numeric metric \"{primary_col}\" has a total of {k['total']:,.2f}, "
                f"with an average of {k['average']:,.2f} and a median of {k['median']:,.2f}."
            )
            if k['growth_pct'] > 5:
                parts.append(f"This metric shows positive growth of {k['growth_pct']:.1f}%.")
            elif k['growth_pct'] < -5:
                parts.append(f"This metric shows a decline of {k['growth_pct']:.1f}%.")

    # Count insight categories
    positive = sum(1 for i in insights if i['severity'] == 'positive')
    warnings = sum(1 for i in insights if i['severity'] in ('warning', 'critical'))

    if positive > warnings:
        parts.append("Overall, the data presents a healthy pattern with positive indicators.")
    elif warnings > positive:
        parts.append("Several areas require attention based on the analysis findings.")
    else:
        parts.append("The data shows a balanced mix of positive signals and areas to monitor.")

    return " ".join(parts)
