"""Quick integration test for all modules."""
import traceback

try:
    print("Testing imports...")
    from utils.loader import load_file
    from utils.cleaner import clean_data
    from utils.analyzer import basic_analysis, compute_kpis, correlation_analysis
    from utils.insights import generate_insights, generate_summary_narrative
    from utils.anomaly import detect_all_anomalies, anomaly_summary
    from utils.reporter import ExcelReportGenerator, PDFReportGenerator
    from utils.visualizer import line_chart, bar_chart, histogram_chart
    print("✅ All imports OK")

    print("\nTesting loader...")
    result = load_file("data/sample_sales.xlsx")
    df = result["dataframe"]
    print(f"✅ Loaded: {result['shape']}")

    print("\nTesting cleaner...")
    df_clean, report = clean_data(df)
    print(f"✅ Cleaned: {df_clean.shape}")
    print(f"   Duplicates removed: {report['duplicates_removed']}")
    print(f"   Completeness: {report['data_completeness']}%")

    print("\nTesting analyzer...")
    analysis = basic_analysis(df_clean)
    print(f"✅ Analysis OK - numeric summary shape: {analysis['numeric_summary'].shape if analysis['numeric_summary'] is not None else 'None'}")
    
    kpis = compute_kpis(df_clean)
    print(f"✅ KPIs computed for: {list(kpis.keys())}")

    print("\nTesting insights...")
    insights = generate_insights(df_clean, report)
    print(f"✅ Generated {len(insights)} insights")
    for i in insights[:3]:
        print(f"   {i['icon']} [{i['category']}] {i['insight'][:60]}...")

    narrative = generate_summary_narrative(df_clean, kpis, insights)
    print(f"✅ Narrative: {narrative[:80]}...")

    print("\nTesting anomaly detection...")
    anomalies = detect_all_anomalies(df_clean)
    summaries = anomaly_summary(anomalies)
    print(f"✅ Anomalies in {len(anomalies)} columns")
    for s in summaries[:3]:
        print(f"   {s[:80]}")

    print("\nTesting reporter...")
    excel_buf = ExcelReportGenerator.generate(df_clean, analysis, anomalies, kpis)
    print(f"✅ Excel report: {len(excel_buf.getvalue())} bytes")

    pdf_buf = PDFReportGenerator.generate(df_clean, kpis, insights, summaries, narrative)
    print(f"✅ PDF report: {len(pdf_buf.getvalue())} bytes")

    print("\n" + "="*50)
    print("🎉 ALL MODULES PASSED SUCCESSFULLY!")
    print("="*50)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    traceback.print_exc()
