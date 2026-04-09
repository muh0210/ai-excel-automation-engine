"""
MODULE 11: FINANCE & ACCOUNTING ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Budget variance analysis, financial modeling,
tax/VAT auditing, expense categorization, and financial ratios.
"""

import pandas as pd
import numpy as np


def detect_financial_columns(df):
    """Auto-detect which columns are likely financial data."""
    finance_keywords = ['amount', 'price', 'cost', 'revenue', 'sales', 'profit',
                       'expense', 'budget', 'actual', 'variance', 'tax', 'vat',
                       'total', 'subtotal', 'discount', 'payment', 'balance',
                       'income', 'debit', 'credit', 'net', 'gross', 'fee',
                       'salary', 'wage', 'bonus', 'commission', 'invoice']
    detected = []
    for col in df.columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in finance_keywords):
            if pd.api.types.is_numeric_dtype(df[col]):
                detected.append(col)
    # Also include any numeric columns with currency-like values
    if not detected:
        detected = list(df.select_dtypes(include='number').columns)
    return detected


def budget_variance_analysis(df, budget_col, actual_col, category_col=None):
    """
    Compute budget vs. actual variance analysis.

    Returns:
        dict with variance data and summary
    """
    try:
        result_df = df.copy()

        # Calculate variances
        result_df['variance'] = result_df[actual_col] - result_df[budget_col]
        result_df['variance_pct'] = ((result_df[actual_col] - result_df[budget_col]) / result_df[budget_col].replace(0, np.nan) * 100).round(2)
        result_df['status'] = result_df['variance'].apply(
            lambda x: '✅ Under Budget' if x < 0 else '⚠️ Over Budget' if x > 0 else '➡️ On Target'
        )

        # Summary
        total_budget = result_df[budget_col].sum()
        total_actual = result_df[actual_col].sum()
        total_variance = total_actual - total_budget
        total_variance_pct = (total_variance / total_budget * 100) if total_budget != 0 else 0

        summary = {
            'total_budget': round(total_budget, 2),
            'total_actual': round(total_actual, 2),
            'total_variance': round(total_variance, 2),
            'total_variance_pct': round(total_variance_pct, 2),
            'over_budget_items': int((result_df['variance'] > 0).sum()),
            'under_budget_items': int((result_df['variance'] < 0).sum()),
            'on_target_items': int((result_df['variance'] == 0).sum()),
        }

        # Category breakdown
        if category_col and category_col in df.columns:
            cat_summary = result_df.groupby(category_col).agg({
                budget_col: 'sum',
                actual_col: 'sum',
                'variance': 'sum',
            }).round(2)
            cat_summary['variance_pct'] = ((cat_summary[actual_col] - cat_summary[budget_col]) / cat_summary[budget_col].replace(0, np.nan) * 100).round(2)
            cat_summary = cat_summary.sort_values('variance', ascending=False)
            summary['category_breakdown'] = cat_summary.reset_index()

        return {
            'detail_df': result_df,
            'summary': summary,
        }
    except Exception as e:
        return {'error': str(e)}


def expense_categorization(df, amount_col, category_col):
    """
    Categorize and analyze expenses.

    Returns:
        dict with expense breakdown
    """
    try:
        grouped = df.groupby(category_col)[amount_col].agg(['sum', 'mean', 'count', 'min', 'max']).round(2)
        grouped.columns = ['Total', 'Average', 'Count', 'Min', 'Max']
        grouped = grouped.sort_values('Total', ascending=False)

        total = grouped['Total'].sum()
        grouped['Percentage'] = (grouped['Total'] / total * 100).round(1)
        grouped['Cumulative_Pct'] = grouped['Percentage'].cumsum().round(1)

        # Top expense categories
        top_categories = list(grouped.index[:3])
        top_pct = grouped['Cumulative_Pct'].iloc[2] if len(grouped) >= 3 else 100

        return {
            'breakdown': grouped.reset_index(),
            'total_expenses': round(total, 2),
            'n_categories': len(grouped),
            'top_3_categories': top_categories,
            'top_3_percentage': round(top_pct, 1),
            'largest_category': str(grouped.index[0]),
            'largest_amount': round(grouped['Total'].iloc[0], 2),
        }
    except Exception as e:
        return {'error': str(e)}


def tax_vat_audit(df, amount_col, tax_col=None, rate_col=None, item_col=None):
    """
    Audit tax/VAT consistency in financial data.

    Detects:
    - Missing tax entries
    - Inconsistent tax rates for same items
    - Unusual tax amounts (outliers)

    Returns:
        dict with audit findings
    """
    findings = []

    try:
        # 1. Check for missing tax values
        if tax_col and tax_col in df.columns:
            missing_tax = df[df[tax_col].isnull()]
            if len(missing_tax) > 0:
                findings.append({
                    'severity': 'critical',
                    'icon': '🚨',
                    'issue': f'{len(missing_tax)} transaction(s) have missing tax/VAT values',
                    'details': f'Rows: {list(missing_tax.index[:10])}',
                    'count': len(missing_tax),
                })

            # 2. Check for zero tax on non-zero amounts
            if amount_col in df.columns:
                zero_tax = df[(df[tax_col] == 0) & (df[amount_col] > 0)]
                if len(zero_tax) > 0:
                    findings.append({
                        'severity': 'warning',
                        'icon': '⚠️',
                        'issue': f'{len(zero_tax)} transaction(s) have zero tax on positive amounts',
                        'details': 'These may be tax-exempt items or data entry errors',
                        'count': len(zero_tax),
                    })

            # 3. Check for negative tax
            negative_tax = df[df[tax_col] < 0]
            if len(negative_tax) > 0:
                findings.append({
                    'severity': 'warning',
                    'icon': '⚠️',
                    'issue': f'{len(negative_tax)} transaction(s) have negative tax values',
                    'details': 'May indicate refunds or credits — verify each',
                    'count': len(negative_tax),
                })

        # 4. Compute effective tax rate and check consistency
        if tax_col and amount_col and tax_col in df.columns and amount_col in df.columns:
            valid = df[(df[amount_col] > 0) & (df[tax_col] > 0)].copy()
            if len(valid) > 0:
                valid['effective_rate'] = (valid[tax_col] / valid[amount_col] * 100).round(2)

                # Check if rates are inconsistent for same items
                if item_col and item_col in df.columns:
                    for item in valid[item_col].unique():
                        item_data = valid[valid[item_col] == item]
                        if len(item_data) > 1:
                            rates = item_data['effective_rate'].unique()
                            if len(rates) > 1:
                                findings.append({
                                    'severity': 'critical',
                                    'icon': '🚨',
                                    'issue': f'Inconsistent tax rate for "{item}": {sorted(rates)} %',
                                    'details': f'{len(rates)} different rates applied across {len(item_data)} transactions',
                                    'count': len(item_data),
                                })

                # 5. Outlier tax rates
                if len(valid) > 5:
                    q1 = valid['effective_rate'].quantile(0.25)
                    q3 = valid['effective_rate'].quantile(0.75)
                    iqr = q3 - q1
                    outlier_mask = (valid['effective_rate'] < q1 - 1.5 * iqr) | (valid['effective_rate'] > q3 + 1.5 * iqr)
                    outliers = valid[outlier_mask]
                    if len(outliers) > 0:
                        findings.append({
                            'severity': 'warning',
                            'icon': '🔍',
                            'issue': f'{len(outliers)} transaction(s) have unusual effective tax rates',
                            'details': f'Outlier rates: {sorted(outliers["effective_rate"].unique()[:5])} %',
                            'count': len(outliers),
                        })

        if not findings:
            findings.append({
                'severity': 'positive',
                'icon': '✅',
                'issue': 'No tax/VAT anomalies detected',
                'details': 'All transactions appear consistent',
                'count': 0,
            })

        return {
            'findings': findings,
            'total_findings': sum(f['count'] for f in findings if f['severity'] != 'positive'),
            'critical_count': sum(1 for f in findings if f['severity'] == 'critical'),
            'warning_count': sum(1 for f in findings if f['severity'] == 'warning'),
        }
    except Exception as e:
        return {'error': str(e), 'findings': [], 'total_findings': 0}


def financial_ratios(df, revenue_col=None, cost_col=None, profit_col=None, assets_col=None):
    """
    Calculate common financial ratios from the data.

    Returns:
        dict with computed ratios
    """
    ratios = {}

    try:
        if revenue_col and cost_col:
            total_revenue = df[revenue_col].sum()
            total_cost = df[cost_col].sum()
            if total_revenue > 0:
                ratios['gross_margin'] = round((total_revenue - total_cost) / total_revenue * 100, 2)
                ratios['cost_ratio'] = round(total_cost / total_revenue * 100, 2)

        if profit_col and revenue_col:
            total_profit = df[profit_col].sum()
            total_revenue = df[revenue_col].sum()
            if total_revenue > 0:
                ratios['profit_margin'] = round(total_profit / total_revenue * 100, 2)

        if profit_col and assets_col:
            total_profit = df[profit_col].sum()
            total_assets = df[assets_col].sum()
            if total_assets > 0:
                ratios['roa'] = round(total_profit / total_assets * 100, 2)

        # Revenue per transaction
        if revenue_col:
            ratios['avg_revenue'] = round(df[revenue_col].mean(), 2)
            ratios['total_revenue'] = round(df[revenue_col].sum(), 2)
            ratios['revenue_std'] = round(df[revenue_col].std(), 2)

        return ratios
    except Exception:
        return ratios


def income_expense_summary(df, amount_col, type_col=None):
    """
    Generate income vs expense summary.

    If type_col is provided, uses it to distinguish income/expense.
    Otherwise, treats positive values as income and negative as expense.
    """
    try:
        if type_col and type_col in df.columns:
            income_keywords = ['income', 'revenue', 'credit', 'deposit', 'sale', 'earning']
            expense_keywords = ['expense', 'cost', 'debit', 'payment', 'withdrawal', 'purchase']

            df_copy = df.copy()
            df_copy['_is_income'] = df_copy[type_col].astype(str).str.lower().apply(
                lambda x: any(kw in x for kw in income_keywords)
            )

            income = df_copy[df_copy['_is_income']][amount_col].sum()
            expenses = df_copy[~df_copy['_is_income']][amount_col].sum()
        else:
            income = df[df[amount_col] >= 0][amount_col].sum()
            expenses = abs(df[df[amount_col] < 0][amount_col].sum())

        net = income - expenses

        return {
            'total_income': round(income, 2),
            'total_expenses': round(expenses, 2),
            'net_amount': round(net, 2),
            'income_pct': round(income / max(income + expenses, 1) * 100, 1),
            'expense_pct': round(expenses / max(income + expenses, 1) * 100, 1),
            'savings_rate': round(net / max(income, 1) * 100, 1),
        }
    except Exception as e:
        return {'error': str(e)}
