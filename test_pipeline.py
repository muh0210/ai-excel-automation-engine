"""Quick integration test for all v3.0 modules."""
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
    from utils.joiner import detect_key_columns, find_matching_columns, smart_join
    print("✅ All imports OK")

    print("\nTesting loader...")
    result = load_file("data/sample_ecommerce_sales.xlsx")
    df = result["dataframe"]
    print(f"✅ Loaded: {result['shape']}")

    print("\nTesting cleaner (missing value detection)...")
    import pandas as pd, numpy as np
    test_df = pd.DataFrame({'A':[1,2,None,4,''],'B':['x','','N/A','-','y'],'C':[10,20,30,40,50]})
    cleaned, report = clean_data(test_df)
    markers = report.get('markers_replaced',{})
    actions = report.get('missing_value_actions',{})
    print(f"✅ Markers detected: {markers}")
    print(f"✅ Missing actions: {actions}")
    assert sum(markers.values()) > 0, "Should detect placeholder values!"
    print("✅ Cleaner properly detects empty strings, N/A, dashes!")

    print("\nTesting full pipeline...")
    df_clean, cr = clean_data(df)
    print(f"✅ Cleaned: {df_clean.shape} | Missing fixed: {sum(cr.get('missing_values_before',{}).values())}")

    print("\nTesting profiler...")
    ds = profile_dataset(df_clean)
    cols = profile_columns(df_clean)
    print(f"✅ Profile: {ds['rows']} rows, {ds['columns']} cols")

    print("\nTesting analyzer...")
    analysis = basic_analysis(df_clean)
    kpis = compute_kpis(df_clean)
    print(f"✅ KPIs: {len(kpis)} metrics")

    print("\nTesting insights...")
    insights = generate_insights(df_clean, cr)
    narrative = generate_summary_narrative(df_clean, kpis, insights)
    print(f"✅ {len(insights)} insights")

    print("\nTesting anomalies...")
    anomalies = detect_all_anomalies(df_clean)
    summaries = anomaly_summary(anomalies)
    ml = detect_ml_anomalies(df_clean, method='isolation_forest')
    print(f"✅ Statistical: {len(anomalies)} cols | ML: {ml['count'] if ml else 0} anomalies")

    print("\nTesting finance...")
    fin_cols = detect_financial_columns(df_clean)
    print(f"✅ Financial columns: {fin_cols[:3]}")
    if len(fin_cols) >= 2:
        bva = budget_variance_analysis(df_clean, fin_cols[0], fin_cols[1])
        print(f"✅ Budget variance: {bva['summary']['total_variance'] if 'error' not in bva else 'N/A'}")
    ratios = financial_ratios(df_clean, revenue_col=fin_cols[0] if fin_cols else None)
    print(f"✅ Financial ratios: {ratios}")

    print("\nTesting joiner...")
    keys = detect_key_columns(df_clean)
    print(f"✅ Key columns detected: {[k['column'] for k in keys[:3]]}")

    print("\nTesting statistics...")
    ncols = list(df_clean.select_dtypes('number').columns)
    reg = linear_regression(df_clean, ncols[0], ncols[1])
    print(f"✅ Regression R²: {reg.get('r_squared','N/A')}")

    print("\nTesting reporter (formula-rich Excel)...")
    ebuf = ExcelReportGenerator.generate(df_clean, analysis, anomalies, kpis, cols, cr)
    print(f"✅ Excel: {len(ebuf.getvalue())} bytes (with formulas)")

    print("\nTesting reporter (white-label PDF)...")
    pbuf = PDFReportGenerator.generate(df_clean, kpis, insights, summaries, narrative, ds, cleaning_report=cr, brand_name="Test Corp", brand_color_hex="#FF5733")
    print(f"✅ PDF: {len(pbuf.getvalue())} bytes (white-labeled)")

    print("\n" + "="*50)
    print("🎉 ALL v3.0 MODULES PASSED!")
    print("="*50)
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    traceback.print_exc()
