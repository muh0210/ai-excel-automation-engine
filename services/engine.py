"""
SERVICE ENGINE — Orchestration Layer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Separates business logic from UI layer.
Called by app.py; wraps all heavy processing.
"""

import pandas as pd
from utils.logger import get_logger
from utils.validator import validate_dataframe, ValidationError
from utils.cleaner import clean_data
from utils.analyzer import basic_analysis, correlation_analysis, compute_kpis
from utils.profiler import profile_dataset, profile_columns, detect_constant_columns, detect_high_cardinality, get_correlation_pairs
from utils.insights import generate_insights, generate_summary_narrative
from utils.anomaly import (detect_all_anomalies, anomaly_summary,
                           detect_ml_anomalies, ml_anomaly_summary, SKLEARN_AVAILABLE)
from utils.statistics import normality_test, anova_test, linear_regression
from utils.finance import (detect_financial_columns, budget_variance_analysis,
                           expense_categorization, tax_vat_audit, financial_ratios)
from utils.joiner import detect_key_columns, find_matching_columns, smart_join, preview_join

log = get_logger("engine")


def run_cleaning(df_raw):
    """Clean raw data and return (df_clean, cleaning_report)."""
    validate_dataframe(df_raw, "raw data")
    log.info("Cleaning %d rows × %d cols", df_raw.shape[0], df_raw.shape[1])
    df_clean, report = clean_data(df_raw)
    log.info("Cleaning done — %d dupes removed, shape %s",
             report.get("duplicates_removed", 0), df_clean.shape)
    return df_clean, report


def run_profiling(df_clean):
    """Run profiling and return (dataset_profile, column_profiles, constants, high_cardinality)."""
    validate_dataframe(df_clean, "cleaned data")
    ds = profile_dataset(df_clean)
    cols = profile_columns(df_clean)
    consts = detect_constant_columns(df_clean)
    hcard = detect_high_cardinality(df_clean)
    log.info("Profile: %d rows, %d cols, %.1f%% missing",
             ds["rows"], ds["columns"], ds["missing_pct"])
    return ds, cols, consts, hcard


def run_analysis(df_clean):
    """Run KPI + basic analysis."""
    validate_dataframe(df_clean, "cleaned data")
    kpis = compute_kpis(df_clean)
    analysis = basic_analysis(df_clean)
    log.info("Analysis: %d KPIs computed", len(kpis))
    return kpis, analysis


def run_insights(df_clean, cleaning_report, kpis):
    """Generate AI insights and narrative."""
    insights = generate_insights(df_clean, cleaning_report)
    narrative = generate_summary_narrative(df_clean, kpis, insights)
    log.info("Generated %d insights", len(insights))
    return insights, narrative


def run_anomaly_detection(df_clean, method="Z-Score", sensitivity=2.0):
    """Run anomaly detection (statistical + optional ML)."""
    validate_dataframe(df_clean, "cleaned data")
    is_ml = "ML" in method or "Forest" in method or "Outlier" in method
    ml_result = None
    anomaly_results = {}
    anom_summaries = []

    if is_ml and SKLEARN_AVAILABLE:
        ml_m = "isolation_forest" if "Forest" in method else "lof"
        cont = max(0.01, min(0.3, 1.0 / sensitivity))
        ml_result = detect_ml_anomalies(df_clean, method=ml_m, contamination=cont)
        anomaly_results = detect_all_anomalies(df_clean, "zscore", sensitivity)
        anom_summaries = anomaly_summary(anomaly_results)
        log.info("ML anomaly detection (%s): %d anomalies",
                 ml_m, ml_result.get("count", 0) if ml_result else 0)
    else:
        m = "zscore" if "Z-Score" in method else "iqr"
        anomaly_results = detect_all_anomalies(df_clean, m, sensitivity)
        anom_summaries = anomaly_summary(anomaly_results)
        log.info("Statistical anomaly scan (%s): %d columns with anomalies",
                 m, len(anomaly_results))

    return ml_result, anomaly_results, anom_summaries


def run_join(df1, df2, left_key, right_key, join_type="left"):
    """Execute a smart join between two DataFrames."""
    validate_dataframe(df1, "left table")
    validate_dataframe(df2, "right table")
    log.info("Joining on %s=%s (%s), left=%d rows, right=%d rows",
             left_key, right_key, join_type, len(df1), len(df2))
    result = smart_join(df1, df2, left_key, right_key, join_type)
    if "error" not in result:
        log.info("Join result: %d merged rows, %.1f%% match rate",
                 result["merged_rows"], result["match_rate_left"])
    else:
        log.error("Join failed: %s", result["error"])
    return result
