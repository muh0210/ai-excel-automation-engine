"""
MODULE 5: AI INSIGHT ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Converts raw data into human-readable business insights.
Enhanced with Pareto insights, outlier narratives, cross-column
dependencies, seasonal patterns, and actionable recommendations.
"""

import pandas as pd
import numpy as np


def generate_insights(df, cleaning_report=None):
    """
    Generate comprehensive AI-style business insights from the data.

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

    for col in numeric_cols[:6]:
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
        elif cv < 15 and len(values) > 10:
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

        # Trend insight
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

        # Outlier narrative
        q1, q3 = values.quantile(0.25), values.quantile(0.75)
        iqr = q3 - q1
        extreme_high = values[values > q3 + 3 * iqr]
        extreme_low = values[values < q1 - 3 * iqr]
        total_extreme = len(extreme_high) + len(extreme_low)
        if total_extreme > 0:
            insights.append({
                'icon': '🔍',
                'category': 'Extreme Values',
                'insight': f'"{col}" has {total_extreme} extreme outlier(s) — values beyond 3x IQR. These may represent errors or significant events worth investigating.',
                'severity': 'warning'
            })

    # ── Categorical Column Insights ──────────────────────────────────
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    for col in cat_cols[:4]:
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
                    'insight': f'"{top}" dominates "{col}" at {top_pct:.1f}% of all records. Consider investigating imbalance.',
                    'severity': 'info'
                })

            # Imbalance detection
            bottom_pct = (value_counts.iloc[-1] / len(df)) * 100
            if top_pct > 10 * bottom_pct and n_unique > 2:
                insights.append({
                    'icon': '⚖️',
                    'category': 'Imbalance',
                    'insight': f'Severe imbalance in "{col}": "{top}" ({top_pct:.0f}%) vs "{value_counts.index[-1]}" ({bottom_pct:.0f}%). This may bias grouped analyses.',
                    'severity': 'warning'
                })

    # ── Cross-Column Insights ────────────────────────────────────────
    if len(numeric_cols) >= 2:
        corr_matrix = df[numeric_cols].corr()
        strong_pairs = []
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.8:
                    strong_pairs.append((numeric_cols[i], numeric_cols[j], corr_val))

        if strong_pairs:
            for col1, col2, corr_val in strong_pairs[:3]:
                relation = 'strong positive' if corr_val > 0 else 'strong negative'
                insights.append({
                    'icon': '🔗',
                    'category': 'Correlation',
                    'insight': f'"{col1}" and "{col2}" have a {relation} correlation ({corr_val:.2f}). Changes in one strongly predict changes in the other.',
                    'severity': 'info'
                })

    # ── Pareto Insights ──────────────────────────────────────────────
    for cat_col in cat_cols[:2]:
        if df[cat_col].nunique() > 20 or df[cat_col].nunique() < 3:
            continue
        for num_col in numeric_cols[:2]:
            try:
                grouped = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False)
                total = grouped.sum()
                if total == 0:
                    continue
                cumsum = grouped.cumsum()
                cats_80 = (cumsum / total < 0.8).sum() + 1
                total_cats = len(grouped)
                if cats_80 <= total_cats * 0.4:  # True Pareto pattern
                    top_cats = list(grouped.index[:cats_80])
                    insights.append({
                        'icon': '📊',
                        'category': 'Pareto Pattern',
                        'insight': f'Top {cats_80} of {total_cats} "{cat_col}" values ({", ".join(str(c) for c in top_cats)}) contribute ~80% of total "{num_col}" — classic 80/20 distribution.',
                        'severity': 'info'
                    })
            except Exception:
                pass

    # ── Cross-Column Dependencies ────────────────────────────────────
    for cat_col in cat_cols[:2]:
        if df[cat_col].nunique() > 10 or df[cat_col].nunique() < 2:
            continue
        for num_col in numeric_cols[:2]:
            try:
                group_means = df.groupby(cat_col)[num_col].mean()
                overall_mean = df[num_col].mean()
                if abs(overall_mean) > 1e-10:
                    max_dev = ((group_means.max() - overall_mean) / abs(overall_mean)) * 100
                    max_group = group_means.idxmax()
                    if abs(max_dev) > 30:
                        insights.append({
                            'icon': '🎯',
                            'category': 'Group Analysis',
                            'insight': f'When "{cat_col}" is "{max_group}", average "{num_col}" is {max_dev:+.0f}% vs overall average. This group significantly outperforms others.',
                            'severity': 'positive' if max_dev > 0 else 'warning'
                        })
            except Exception:
                pass

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

    # ── Recommendations ──────────────────────────────────────────────
    warning_count = sum(1 for i in insights if i['severity'] in ('warning', 'critical'))
    if warning_count > 3:
        insights.append({
            'icon': '💡',
            'category': 'Recommendation',
            'insight': f'{warning_count} areas need attention. Consider investigating high-variability columns and extreme outliers first.',
            'severity': 'info'
        })

    # Missing value pattern insight
    missing_by_col = df.isnull().sum()
    cols_with_missing = missing_by_col[missing_by_col > 0]
    if len(cols_with_missing) > 1:
        # Check if missing values correlate (occur in same rows)
        missing_matrix = df[cols_with_missing.index].isnull()
        corr_missing = missing_matrix.corr()
        high_corr_pairs = []
        cols_list = list(cols_with_missing.index)
        for i in range(len(cols_list)):
            for j in range(i + 1, len(cols_list)):
                if abs(corr_missing.iloc[i, j]) > 0.5:
                    high_corr_pairs.append((cols_list[i], cols_list[j]))
        if high_corr_pairs:
            pair_str = ', '.join(f'"{a}" & "{b}"' for a, b in high_corr_pairs[:2])
            insights.append({
                'icon': '🔍',
                'category': 'Missing Data Pattern',
                'insight': f'Missing values cluster together in columns: {pair_str}. This suggests a systematic data collection issue rather than random gaps.',
                'severity': 'info'
            })

    return insights


def generate_summary_narrative(df, kpis, insights):
    """Generate a natural language summary paragraph for the report."""
    parts = []

    parts.append(f"This dataset contains {len(df):,} records across {len(df.columns)} columns.")

    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    if numeric_cols and kpis:
        primary_col = numeric_cols[0]
        if primary_col in kpis:
            k = kpis[primary_col]
            parts.append(
                f'The primary numeric metric "{primary_col}" has a total of {k["total"]:,.2f}, '
                f'with an average of {k["average"]:,.2f} and a median of {k["median"]:,.2f}.'
            )
            if k['growth_pct'] > 5:
                parts.append(f"This metric shows positive growth of {k['growth_pct']:.1f}%.")
            elif k['growth_pct'] < -5:
                parts.append(f"This metric shows a decline of {k['growth_pct']:.1f}%.")

    # Summarize categories
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    if cat_cols:
        parts.append(f"The data includes {len(cat_cols)} categorical dimension(s) for segmentation analysis.")

    # Count insight categories
    positive = sum(1 for i in insights if i['severity'] == 'positive')
    warnings = sum(1 for i in insights if i['severity'] in ('warning', 'critical'))

    if positive > warnings:
        parts.append("Overall, the data presents a healthy pattern with positive indicators outweighing concerns.")
    elif warnings > positive:
        parts.append("Several areas require attention based on the analysis findings. Review the warning insights for actionable items.")
    else:
        parts.append("The data shows a balanced mix of positive signals and areas to monitor.")

    parts.append(f"A total of {len(insights)} AI-generated insights were produced from this analysis.")

    return " ".join(parts)
