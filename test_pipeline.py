"""Quick integration test for all modules (v2.0)."""
import traceback

try:
    print("Testing imports...")
    from utils.loader import load_file
    from utils.cleaner import clean_data
    from utils.analyzer import basic_analysis, compute_kpis, correlation_analysis, pareto_analysis, moving_average
    from utils.insights import generate_insights, generate_summary_narrative
    from utils.anomaly import detect_all_anomalies, anomaly_summary, detect_ml_anomalies, ml_anomaly_summary
    from utils.reporter import ExcelReportGenerator, PDFReportGenerator
    from utils.visualizer import line_chart, bar_chart, histogram_chart, violin_chart, radar_chart, pareto_chart
    from utils.profiler import profile_dataset, profile_columns, detect_constant_columns, get_correlation_pairs
    from utils.transformer import build_pivot_table, create_calculated_column
    from utils.statistics import normality_test, linear_regression, anova_test
    print("✅ All imports OK")

    print("\nTesting loader...")
    result = load_file("data/sample_ecommerce_sales.xlsx")
    df = result["dataframe"]
    print(f"✅ Loaded: {result['shape']}")

    print("\nTesting cleaner...")
    df_clean, report = clean_data(df)
    print(f"✅ Cleaned: {df_clean.shape} | Dups: {report['duplicates_removed']} | Complete: {report['data_completeness']}%")

    print("\nTesting profiler...")
    ds = profile_dataset(df_clean)
    cols = profile_columns(df_clean)
    print(f"✅ Profile: {ds['rows']} rows, {ds['columns']} cols, {ds['memory_usage']}")

    print("\nTesting analyzer...")
    analysis = basic_analysis(df_clean)
    kpis = compute_kpis(df_clean)
    print(f"✅ KPIs: {list(kpis.keys())[:4]}")

    pa = pareto_analysis(df_clean, df_clean.select_dtypes(['object','category']).columns[0], df_clean.select_dtypes('number').columns[0])
    print(f"✅ Pareto: {pa['categories_for_80_pct']}/{pa['total_categories']} categories = 80%")

    print("\nTesting insights...")
    insights = generate_insights(df_clean, report)
    narrative = generate_summary_narrative(df_clean, kpis, insights)
    print(f"✅ {len(insights)} insights generated")

    print("\nTesting statistical anomalies...")
    anomalies = detect_all_anomalies(df_clean)
    summaries = anomaly_summary(anomalies)
    print(f"✅ Anomalies in {len(anomalies)} columns")

    print("\nTesting ML anomalies...")
    ml = detect_ml_anomalies(df_clean, method='isolation_forest')
    if ml: print(f"✅ Isolation Forest: {ml['count']} anomalies")
    else: print("⚠️ ML not available")

    print("\nTesting statistics...")
    reg = linear_regression(df_clean, df_clean.select_dtypes('number').columns[0], df_clean.select_dtypes('number').columns[1])
    print(f"✅ Regression R²: {reg.get('r_squared','N/A')}")

    norm = normality_test(df_clean[df_clean.select_dtypes('number').columns[0]])
    print(f"✅ Normality: {norm.get('interpretation','N/A')[:50]}")

    print("\nTesting reporter...")
    excel_buf = ExcelReportGenerator.generate(df_clean, analysis, anomalies, kpis, cols)
    print(f"✅ Excel: {len(excel_buf.getvalue())} bytes")
    pdf_buf = PDFReportGenerator.generate(df_clean, kpis, insights, summaries, narrative, ds)
    print(f"✅ PDF: {len(pdf_buf.getvalue())} bytes")

    print("\n" + "="*50)
    print("🎉 ALL v2.0 MODULES PASSED!")
    print("="*50)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    traceback.print_exc()
