"""
MODULE 12: COMPLIANCE CHECKER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Automated tax/VAT auditing and invoice validation:
  • Tax/VAT rate consistency checking
  • Missing TRN detection
  • Invoice date discrepancy flagging
  • Duplicate invoice detection
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def check_tax_consistency(df, item_col=None, tax_col=None, amount_col=None):
    """
    Flag items where the same product/service has different tax rates.

    Returns:
        dict with inconsistency results
    """
    col_lower = {c.lower().replace(' ', '_'): c for c in df.columns}

    if item_col is None:
        for key in ('item', 'product', 'service', 'description', 'name', 'particular'):
            if key in col_lower:
                item_col = col_lower[key]
                break

    if tax_col is None:
        for key in ('tax', 'vat', 'gst', 'tax_rate', 'vat_rate', 'tax_pct', 'tax_amount'):
            if key in col_lower:
                tax_col = col_lower[key]
                break

    if item_col is None or tax_col is None:
        return None

    if item_col not in df.columns or tax_col not in df.columns:
        return None

    # Group by item, find items with multiple tax rates
    grouped = df.groupby(item_col)[tax_col].agg(['nunique', 'mean', 'min', 'max', list])
    inconsistent = grouped[grouped['nunique'] > 1].copy()

    if len(inconsistent) == 0:
        return {
            'has_issues': False,
            'message': '✅ All items have consistent tax rates.',
            'inconsistent_items': pd.DataFrame(),
            'total_items_checked': len(grouped),
        }

    inconsistent_df = inconsistent.reset_index()
    inconsistent_df.columns = [item_col, 'Distinct Rates', 'Average Rate', 'Min Rate', 'Max Rate', 'All Rates']

    return {
        'has_issues': True,
        'message': f'⚠️ {len(inconsistent)} item(s) have inconsistent tax rates!',
        'inconsistent_items': inconsistent_df,
        'total_items_checked': len(grouped),
        'pct_inconsistent': round(len(inconsistent) / max(len(grouped), 1) * 100, 1),
    }


def check_missing_trn(df):
    """
    Identify transactions without Tax Registration Numbers.

    Returns:
        dict with results
    """
    col_lower = {c.lower().replace(' ', '_'): c for c in df.columns}

    trn_col = None
    for key in ('trn', 'tax_registration', 'tin', 'vat_number', 'gst_number',
                'tax_id', 'registration_number', 'ein'):
        if key in col_lower:
            trn_col = col_lower[key]
            break

    if trn_col is None:
        return {
            'has_trn_column': False,
            'message': 'ℹ️ No TRN/Tax ID column detected in this dataset.',
        }

    missing = df[df[trn_col].isna() | (df[trn_col].astype(str).str.strip() == '')]
    total = len(df)

    return {
        'has_trn_column': True,
        'trn_column': trn_col,
        'total_records': total,
        'missing_trn': len(missing),
        'missing_pct': round(len(missing) / max(total, 1) * 100, 1),
        'missing_records': missing if len(missing) > 0 else pd.DataFrame(),
        'has_issues': len(missing) > 0,
        'message': f'⚠️ {len(missing)} record(s) ({round(len(missing)/max(total,1)*100,1)}%) missing TRN/Tax ID'
                   if len(missing) > 0 else '✅ All records have TRN/Tax ID.',
    }


def check_invoice_dates(df, date_col=None, invoice_col=None):
    """
    Flag future-dated invoices, out-of-sequence numbers, and date gaps.

    Returns:
        dict with flagged issues
    """
    col_lower = {c.lower().replace(' ', '_'): c for c in df.columns}

    if date_col is None:
        for key in ('date', 'invoice_date', 'transaction_date', 'bill_date', 'posting_date'):
            if key in col_lower:
                date_col = col_lower[key]
                break

    if invoice_col is None:
        for key in ('invoice', 'invoice_no', 'invoice_number', 'bill_no', 'receipt_no', 'doc_no'):
            if key in col_lower:
                invoice_col = col_lower[key]
                break

    issues = []

    if date_col and date_col in df.columns:
        dates = pd.to_datetime(df[date_col], errors='coerce')
        now = pd.Timestamp.now()

        # Future dates
        future = df[dates > now]
        if len(future) > 0:
            issues.append({
                'type': '📅 Future-Dated',
                'severity': 'warning',
                'count': len(future),
                'message': f'{len(future)} invoice(s) have future dates',
                'records': future,
            })

        # Very old dates (> 2 years)
        two_years_ago = now - pd.Timedelta(days=730)
        old = df[dates < two_years_ago]
        if len(old) > 0:
            issues.append({
                'type': '📆 Aged Invoice',
                'severity': 'info',
                'count': len(old),
                'message': f'{len(old)} invoice(s) are older than 2 years',
                'records': old,
            })

    if invoice_col and invoice_col in df.columns:
        # Try to detect numeric invoice sequences
        inv_nums = pd.to_numeric(df[invoice_col], errors='coerce').dropna()
        if len(inv_nums) > 2:
            sorted_nums = inv_nums.sort_values()
            gaps = sorted_nums.diff().dropna()
            large_gaps = gaps[gaps > gaps.median() * 3]
            if len(large_gaps) > 0:
                issues.append({
                    'type': '🔢 Sequence Gap',
                    'severity': 'warning',
                    'count': len(large_gaps),
                    'message': f'{len(large_gaps)} gap(s) detected in invoice numbering sequence',
                    'records': pd.DataFrame(),
                })

    return {
        'issues': issues,
        'total_issues': sum(i['count'] for i in issues),
        'has_issues': len(issues) > 0,
        'date_col': date_col,
        'invoice_col': invoice_col,
    }


def check_duplicate_invoices(df, amount_col=None, date_col=None, vendor_col=None):
    """
    Find potential duplicate invoices by amount + date proximity.

    Returns:
        dict with potential duplicates
    """
    col_lower = {c.lower().replace(' ', '_'): c for c in df.columns}

    if amount_col is None:
        for key in ('amount', 'total', 'value', 'invoice_amount', 'net_amount'):
            if key in col_lower:
                amount_col = col_lower[key]
                break

    if amount_col is None or not pd.api.types.is_numeric_dtype(df.get(amount_col, pd.Series())):
        return None

    # Find rows with identical amounts
    duplicated_amounts = df[df.duplicated(subset=[amount_col], keep=False)]

    if len(duplicated_amounts) == 0:
        return {
            'has_duplicates': False,
            'message': '✅ No potential duplicate invoices found.',
            'duplicates_df': pd.DataFrame(),
        }

    # Sort by amount for easy review
    duplicated_amounts = duplicated_amounts.sort_values(amount_col)

    return {
        'has_duplicates': True,
        'message': f'⚠️ {len(duplicated_amounts)} record(s) share the same amount — potential duplicates.',
        'duplicates_df': duplicated_amounts,
        'unique_amounts': int(duplicated_amounts[amount_col].nunique()),
        'amount_col': amount_col,
    }


def run_all_compliance_checks(df):
    """
    Run all compliance checks and return grouped results.
    """
    results = {
        'tax_consistency': check_tax_consistency(df),
        'missing_trn': check_missing_trn(df),
        'invoice_dates': check_invoice_dates(df),
        'duplicate_invoices': check_duplicate_invoices(df),
    }

    total_issues = 0
    for key, val in results.items():
        if val and val.get('has_issues', False):
            total_issues += val.get('total_issues', val.get('missing_trn', 0) or 1)

    results['summary'] = {
        'total_checks': 4,
        'checks_with_issues': sum(1 for v in results.values() if isinstance(v, dict) and v.get('has_issues', False)),
        'total_issues': total_issues,
        'overall_status': '🟢 Clean' if total_issues == 0 else '🟡 Minor Issues' if total_issues < 5 else '🔴 Needs Review',
    }

    return results
