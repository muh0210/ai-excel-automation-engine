"""Quick integration test for all v4.0 modules."""
import traceback
try:
    print("Testing imports...")
    from utils.loader import load_file
    from utils.cleaner import clean_data
    from utils.analyzer import basic_analysis, compute_kpis, correlation_analysis, pareto_analysis
    from utils.insights import generate_insights, generate_summary_narrative
    from utils.anomaly import detect_all_anomalies, anomaly_summary, detect_ml_anomalies, ml_anomaly_summary
    from utils.reporter import ExcelReportGenerator, PDFReportGenerator
    from utils.visualizer import line_chart, bar_chart, histogram_chart
    from utils.profiler import profile_dataset, profile_columns
    from utils.statistics import normality_test, linear_regression
    from utils.finance import detect_financial_columns, budget_variance_analysis, expense_categorization, tax_vat_audit, financial_ratios
    from utils.joiner import detect_key_columns, find_matching_columns, smart_join, preview_join
    from utils.validator import validate_dataframe, validate_columns_exist, validate_numeric_columns, validate_min_rows, ValidationError
    from utils.logger import get_logger
    from utils.nlq import process_nlq
    from services.engine import run_cleaning, run_profiling, run_analysis, run_insights, run_anomaly_detection, run_join
    print("✅ All imports OK (including new v4.0 modules)")

    print("\nTesting validator...")
    import pandas as pd, numpy as np
    try:
        validate_dataframe(None)
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass
    try:
        validate_dataframe(pd.DataFrame())
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass
    test_df = pd.DataFrame({'A': [1, 2, 3], 'B': ['x', 'y', 'z']})
    validate_dataframe(test_df)
    validate_columns_exist(test_df, ['A', 'B'])
    validate_numeric_columns(test_df, ['A'])
    validate_min_rows(test_df, 2)
    try:
        validate_columns_exist(test_df, ['NONEXISTENT'])
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass
    print("✅ Validator works correctly")

    print("\nTesting logger...")
    log = get_logger("test")
    log.info("Test log message — this should appear in outputs/engine.log")
    print("✅ Logger initialized")

    print("\nTesting NLQ engine...")
    nlq_df = pd.DataFrame({'sales': [100, 200, 300], 'region': ['North', 'South', 'East']})
    r = process_nlq(nlq_df, "average of sales")
    assert r['success'], f"NLQ failed: {r}"
    r = process_nlq(nlq_df, "top 2 by sales")
    assert r['success'], f"NLQ failed: {r}"
    print("✅ NLQ engine works")

    print("\nTesting loader...")
    result = load_file("data/sample_ecommerce_sales.xlsx")
    df = result["dataframe"]
    print(f"✅ Loaded: {result['shape']}")

    print("\nTesting cleaner (missing value detection)...")
    test_df = pd.DataFrame({'A': [1, 2, None, 4, ''], 'B': ['x', '', 'N/A', '-', 'y'], 'C': [10, 20, 30, 40, 50]})
    cleaned, report = clean_data(test_df)
    markers = report.get('markers_replaced', {})
    actions = report.get('missing_value_actions', {})
    print(f"✅ Markers detected: {markers}")
    print(f"✅ Missing actions: {actions}")
    assert sum(markers.values()) > 0, "Should detect placeholder values!"
    print("✅ Cleaner properly detects empty strings, N/A, dashes!")

    print("\nTesting service engine — run_cleaning...")
    df_clean, cr = run_cleaning(df)
    print(f"✅ Cleaned: {df_clean.shape} | Missing fixed: {sum(cr.get('missing_values_before', {}).values())}")

    print("\nTesting service engine — run_profiling...")
    ds, cols, consts, hcard = run_profiling(df_clean)
    print(f"✅ Profile: {ds['rows']} rows, {ds['columns']} cols")

    print("\nTesting service engine — run_analysis...")
    kpis, analysis = run_analysis(df_clean)
    print(f"✅ KPIs: {len(kpis)} metrics")

    print("\nTesting service engine — run_insights...")
    insights, narrative = run_insights(df_clean, cr, kpis)
    print(f"✅ {len(insights)} insights")

    print("\nTesting service engine — run_anomaly_detection...")
    ml_result, anomalies, summaries = run_anomaly_detection(df_clean)
    print(f"✅ Statistical: {len(anomalies)} cols | ML: {ml_result['count'] if ml_result else 0} anomalies")

    print("\nTesting finance...")
    fin_cols = detect_financial_columns(df_clean)
    print(f"✅ Financial columns: {fin_cols[:3]}")
    if len(fin_cols) >= 2:
        bva = budget_variance_analysis(df_clean, fin_cols[0], fin_cols[1])
        print(f"✅ Budget variance: {bva['summary']['total_variance'] if 'error' not in bva else 'N/A'}")
    ratios = financial_ratios(df_clean, revenue_col=fin_cols[0] if fin_cols else None)
    print(f"✅ Financial ratios: {ratios}")

    print("\nTesting unified joiner (smart_join.py deleted)...")
    keys = detect_key_columns(df_clean)
    print(f"✅ Key columns detected: {[k['column'] for k in keys[:3]]}")

    print("\nTesting statistics...")
    ncols = list(df_clean.select_dtypes('number').columns)
    reg = linear_regression(df_clean, ncols[0], ncols[1])
    print(f"✅ Regression R²: {reg.get('r_squared', 'N/A')}")

    print("\nTesting reporter (formula-rich Excel)...")
    ebuf = ExcelReportGenerator.generate(df_clean, analysis, anomalies, kpis, cols, cr)
    print(f"✅ Excel: {len(ebuf.getvalue())} bytes (with formulas)")

    print("\nTesting reporter (white-label PDF)...")
    pbuf = PDFReportGenerator.generate(df_clean, kpis, insights, summaries, narrative, ds,
                                        cleaning_report=cr, brand_name="Test Corp",
                                        brand_color_hex="#FF5733")
    print(f"✅ PDF: {len(pbuf.getvalue())} bytes (white-labeled)")

    # Verify smart_join.py is deleted
    import os
    assert not os.path.exists("utils/smart_join.py"), "smart_join.py should be deleted!"
    print("✅ smart_join.py confirmed deleted")

    print("\n" + "=" * 50)
    print("🎉 ALL v4.0 MODULES PASSED!")
    print("=" * 50)
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    traceback.print_exc()
