"""
AI EXCEL AUTOMATION ENGINE v4.0
Author: Muhammad Rajput (muh0210) | muhrajpoot1921@gmail.com

UI layer — all orchestration delegated to services/engine.py
"""
import streamlit as st
import pandas as pd
import os
from io import BytesIO

# ── Service & utility imports ──────────────────────────────────────
from services.engine import (run_cleaning, run_profiling, run_analysis,
                             run_insights, run_anomaly_detection, run_join)
from utils.loader import load_file, load_specific_sheet
from utils.visualizer import (line_chart, bar_chart, scatter_chart, pie_chart,
    heatmap_chart, box_chart, histogram_chart, anomaly_chart, violin_chart,
    radar_chart, sunburst_chart, scatter_matrix_chart, missing_values_heatmap,
    regression_chart, pareto_chart, COLORS)
from utils.analyzer import trend_analysis, correlation_analysis, pareto_analysis, compare_groups
from utils.profiler import get_correlation_pairs
from utils.statistics import normality_test, anova_test, linear_regression
from utils.transformer import build_pivot_table
from utils.reporter import ExcelReportGenerator, PDFReportGenerator
from utils.finance import (detect_financial_columns, budget_variance_analysis,
    expense_categorization, tax_vat_audit, financial_ratios)
from utils.joiner import detect_key_columns, find_matching_columns, smart_join
from utils.nlq import process_nlq
from utils.anomaly import ml_anomaly_summary

# ═══════════════════════════════════════════════════════════════════
#  PAGE CONFIG & STYLES
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(page_title="AI Excel Automation Engine", page_icon="🚀",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
:root{--purple:#7C3AED;--blue:#3B82F6;--cyan:#06B6D4;--green:#10B981;--yellow:#F59E0B;--red:#EF4444;--bg-dark:#0F172A;--bg-card:#1E293B;--text:#E2E8F0;--text-muted:#94A3B8;--grid:#334155}
html,body{font-family:'Inter',sans-serif!important}
.main-header{background:linear-gradient(135deg,#7C3AED 0%,#3B82F6 50%,#06B6D4 100%);padding:1.5rem 2rem;border-radius:16px;margin-bottom:1.5rem;box-shadow:0 8px 32px rgba(124,58,237,0.3)}
.main-header h1{color:white;font-size:2rem;font-weight:800;margin:0;letter-spacing:-0.5px}
.main-header p{color:rgba(255,255,255,0.85);font-size:0.95rem;margin:0.3rem 0 0 0}
.section-header{background:linear-gradient(90deg,rgba(124,58,237,0.15),transparent);border-left:4px solid var(--purple);padding:0.6rem 1rem;border-radius:0 8px 8px 0;margin:1.5rem 0 1rem 0;font-size:1.1rem;font-weight:700;color:var(--text);display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.kpi-card{background:linear-gradient(145deg,#1E293B,#0F172A);border:1px solid rgba(124,58,237,0.25);border-radius:12px;padding:1rem;text-align:center;transition:all 0.3s ease;box-shadow:0 4px 12px rgba(0,0,0,0.2);overflow:hidden}
.kpi-card:hover{border-color:var(--purple);transform:translateY(-2px);box-shadow:0 8px 24px rgba(124,58,237,0.2)}
.kpi-value{font-size:1.5rem;font-weight:800;color:var(--purple);margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.kpi-label{font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin:0.2rem 0 0 0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.kpi-delta{font-size:0.8rem;font-weight:600;margin-top:0.2rem}
.kpi-delta.positive{color:var(--green)} .kpi-delta.negative{color:var(--red)}
.insight-card{background:var(--bg-card);border-radius:10px;padding:0.8rem 1rem;margin-bottom:0.6rem;border-left:4px solid var(--blue);transition:all 0.2s ease}
.insight-card:hover{background:#263548;transform:translateX(4px)}
.insight-card.positive{border-left-color:var(--green)} .insight-card.warning{border-left-color:var(--yellow)}
.insight-card.critical{border-left-color:var(--red)} .insight-card.info{border-left-color:var(--blue)}
.insight-category{font-size:0.65rem;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);margin-bottom:0.15rem}
.insight-text{color:var(--text);font-size:0.9rem;line-height:1.4}
.badge{display:inline-block;padding:0.2rem 0.6rem;border-radius:20px;font-size:0.72rem;font-weight:600;margin-right:0.4rem;margin-bottom:0.3rem}
.badge-purple{background:rgba(124,58,237,0.2);color:#A78BFA} .badge-blue{background:rgba(59,130,246,0.2);color:#60A5FA}
.badge-green{background:rgba(16,185,129,0.2);color:#34D399} .badge-yellow{background:rgba(245,158,11,0.2);color:#FBBF24}
.badge-red{background:rgba(239,68,68,0.2);color:#F87171}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0F172A,#1E293B)!important}
.stTabs [data-baseweb="tab-list"]{gap:6px} .stTabs [data-baseweb="tab"]{background:transparent;border-radius:8px;padding:6px 14px;color:var(--text-muted)}
.stTabs [aria-selected="true"]{background:rgba(124,58,237,0.2)!important;color:#A78BFA!important}
#MainMenu{visibility:hidden} footer{visibility:hidden}
div[data-testid="stExpander"] summary span{font-size:0.9rem!important}
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""<div style="text-align:center;padding:0.8rem 0"><span style="font-size:2.5rem">🚀</span>
        <h2 style="margin:0.3rem 0 0;font-weight:800;background:linear-gradient(90deg,#7C3AED,#3B82F6);-webkit-background-clip:text;-webkit-text-fill-color:transparent">AI Excel Engine</h2>
        <p style="color:#94A3B8;font-size:0.8rem">Premium Data Automation v4.0</p></div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### ⚙️ Analysis Settings")
    anomaly_method = st.selectbox("Anomaly Method", ['Z-Score','IQR','Isolation Forest (ML)','Local Outlier Factor (ML)'])
    anomaly_sensitivity = st.slider("Sensitivity", 1.0, 4.0, 2.0, 0.5)
    show_raw = st.checkbox("Show Raw Data", False)
    st.markdown("---")
    st.markdown("### 🏷️ White-Label Reports")
    brand_name = st.text_input("Company Name (optional)", "", placeholder="Your Company Name")
    brand_color = st.color_picker("Brand Color", "#7C3AED")
    logo_file = st.file_uploader("Upload Logo (optional)", type=['png','jpg','jpeg'], help="Logo for PDF report cover")
    st.markdown("---")
    st.markdown("""<div style="text-align:center;padding:0.3rem"><p style="color:#64748B;font-size:0.7rem">Built by <b>Muhammad Rajput</b><br>
        <a href="https://github.com/muh0210" style="color:#7C3AED">github.com/muh0210</a></p></div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
#  HEADER & FILE UPLOAD
# ═══════════════════════════════════════════════════════════════════
st.markdown("""<div class="main-header"><h1>🚀 AI Excel Automation Engine</h1>
    <p>Upload → Clean → Profile → Analyze → Insights → Anomalies → Finance → Smart Join → Export</p></div>""", unsafe_allow_html=True)

st.markdown('<div class="section-header">📥 Upload Your Data</div>', unsafe_allow_html=True)
col_up1, col_up2 = st.columns([3,1])
with col_up1:
    uploaded_file = st.file_uploader("Drop your Excel or CSV file", type=['xlsx','xls','csv'], help="Up to 50MB")
with col_up2:
    st.markdown("**Supported:**")
    st.markdown("Excel (.xlsx, .xls), CSV (.csv)")

dc1, dc2, dc3 = st.columns(3)
with dc1: demo_sales = st.button("🛒 E-Commerce Demo", use_container_width=True)
with dc2: demo_emp = st.button("👥 Employee Demo", use_container_width=True)
with dc3: demo_fin = st.button("💰 Finance Demo", use_container_width=True)
dc4, dc5, dc6 = st.columns(3)
with dc4: demo_budget = st.button("📊 Budget vs Actual", use_container_width=True)
with dc5: demo_orders = st.button("📦 Orders Demo", use_container_width=True)
with dc6: demo_messy = st.button("🧪 Messy Data Test", use_container_width=True)

demo_path = None
if demo_sales: demo_path = 'data/sample_ecommerce_sales.xlsx'
elif demo_emp: demo_path = 'data/sample_employee_data.xlsx'
elif demo_fin: demo_path = 'data/sample_financial_report.xlsx'
elif demo_budget: demo_path = 'data/sample_budget_vs_actual.xlsx'
elif demo_orders: demo_path = 'data/sample_orders.xlsx'
elif demo_messy: demo_path = 'data/sample_messy_data.csv'
if demo_path and os.path.exists(demo_path):
    st.session_state['demo_file'] = demo_path

st.markdown('<div class="section-header">🔗 Smart Join (Optional — Upload Second File)</div>', unsafe_allow_html=True)
second_file = st.file_uploader("Upload a second file to join/merge", type=['xlsx','xls','csv'], key='file2',
                               help="Auto-detects matching columns for VLOOKUP-style join")

use_demo = st.session_state.get('demo_file')
active_file = uploaded_file or use_demo

# ═══════════════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════
if active_file is not None:
    if uploaded_file:
        st.session_state.pop('demo_file', None)

    # ── LOAD ──────────────────────────────────────────────────────
    with st.spinner("Loading..."):
        try:
            result = load_file(active_file)
            df_raw = result['dataframe']
        except Exception as e:
            st.error(f"Load failed: {e}"); st.stop()

    if result.get('sheet_names') and len(result['sheet_names']) > 1:
        sel = st.selectbox("Select sheet:", result['sheet_names'])
        if sel != result['sheet_names'][0]:
            if hasattr(active_file, 'seek'): active_file.seek(0)
            df_raw = load_specific_sheet(active_file, sel)

    fn = result.get('file_name', 'data')
    st.markdown(f'<div style="margin:0.8rem 0"><span class="badge badge-purple">📁 {fn}</span>'
                f'<span class="badge badge-blue">📐 {df_raw.shape[0]} rows × {df_raw.shape[1]} cols</span>'
                f'<span class="badge badge-green">💾 {result.get("file_size_kb","?")} KB</span></div>',
                unsafe_allow_html=True)

    if show_raw:
        with st.expander("📋 Raw Data", expanded=False):
            st.dataframe(df_raw, use_container_width=True, height=300)

    # ── CLEAN (cached) ────────────────────────────────────────────
    st.markdown('<div class="section-header">🧹 Data Cleaning Engine</div>', unsafe_allow_html=True)

    @st.cache_data(show_spinner=False)
    def _cached_clean(_df):
        return run_cleaning(_df)

    with st.spinner("Cleaning..."):
        df_clean, cr_report = _cached_clean(df_raw)

    cc = st.columns(4)
    total_missing_fixed = sum(cr_report.get('missing_values_before',{}).values()) + sum(cr_report.get('markers_replaced',{}).values())
    items = [(cr_report["duplicates_removed"], "Duplicates Removed"),
             (total_missing_fixed, "Missing Fixed"),
             (len(cr_report.get('type_conversions',{})), "Type Conversions"),
             (f"{cr_report.get('data_completeness',100)}%", "Completeness")]
    for i,(v,l) in enumerate(items):
        with cc[i]:
            st.markdown(f'<div class="kpi-card"><p class="kpi-value">{v}</p><p class="kpi-label">{l}</p></div>', unsafe_allow_html=True)

    markers = cr_report.get('markers_replaced',{})
    missing_actions = cr_report.get('missing_value_actions',{})
    if markers:
        st.markdown("""<div style="background:linear-gradient(135deg,rgba(239,68,68,0.1),rgba(245,158,11,0.08));border:1px solid rgba(239,68,68,0.3);border-radius:12px;padding:1rem;margin:0.8rem 0">
            <p style="color:#F87171;font-size:0.7rem;text-transform:uppercase;letter-spacing:1.5px;margin:0 0 0.5rem">🔍 Placeholder Values Detected & Converted</p></div>""", unsafe_allow_html=True)
        for col, count in markers.items():
            st.markdown(f'<div class="insight-card critical"><p class="insight-category">Column: {col}</p>'
                        f'<p class="insight-text">🔍 {count} placeholder value(s) (empty, N/A, -, null, etc.) detected and converted to missing</p></div>', unsafe_allow_html=True)

    if missing_actions:
        st.markdown("""<div style="background:linear-gradient(135deg,rgba(245,158,11,0.1),rgba(16,185,129,0.08));border:1px solid rgba(245,158,11,0.3);border-radius:12px;padding:1rem;margin:0.8rem 0">
            <p style="color:#FBBF24;font-size:0.7rem;text-transform:uppercase;letter-spacing:1.5px;margin:0 0 0.5rem">🔧 Missing Values Fixed</p></div>""", unsafe_allow_html=True)
        for col, action in missing_actions.items():
            st.markdown(f'<div class="insight-card warning"><p class="insight-category">Column: {col}</p>'
                        f'<p class="insight-text">🔧 {action}</p></div>', unsafe_allow_html=True)
    elif not markers:
        st.markdown('<div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);border-radius:12px;padding:0.8rem;margin:0.8rem 0">'
                    '<p style="color:#34D399;font-size:0.85rem;margin:0">✅ No missing values — dataset is complete!</p></div>', unsafe_allow_html=True)

    with st.expander("🔍 Full Cleaning Details"):
        if cr_report.get('columns_renamed'):
            st.markdown("**Column Renames:**")
            for o, n in cr_report['columns_renamed'].items(): st.markdown(f"  `{o}` → `{n}`")
        if cr_report.get('type_conversions'):
            st.markdown("**Type Conversions:**")
            for c, ch in cr_report['type_conversions'].items(): st.markdown(f"  - `{c}`: {ch}")
        st.markdown(f"**Shape:** {cr_report['original_shape']} → {cr_report['cleaned_shape']}")
        mvb = cr_report.get('missing_values_before', {})
        if mvb:
            st.markdown("**Missing Per Column (Before):**")
            st.dataframe(pd.DataFrame({'Column': list(mvb.keys()), 'Missing': list(mvb.values())}), use_container_width=True)

    with st.expander("📋 Cleaned Data Preview"):
        st.dataframe(df_clean, use_container_width=True, height=300)

    numeric_cols = list(df_clean.select_dtypes(include='number').columns)
    cat_cols = list(df_clean.select_dtypes(include=['object','category']).columns)
    date_cols = list(df_clean.select_dtypes(include='datetime').columns)

    # ── PROFILE (cached) ─────────────────────────────────────────
    st.markdown('<div class="section-header">🔬 Data Profile</div>', unsafe_allow_html=True)

    @st.cache_data(show_spinner=False)
    def _cached_profile(_df):
        return run_profiling(_df)

    ds_profile, col_profiles, consts, hcard = _cached_profile(df_clean)

    pc = st.columns(4)
    for i,(v,l) in enumerate([(f"{ds_profile['rows']:,}", "Rows"),
                               (f"{ds_profile['columns']}", "Columns"),
                               (f"{ds_profile['missing_pct']}%", "Missing"),
                               (ds_profile['memory_usage'], "Memory")]):
        with pc[i]:
            st.markdown(f'<div class="kpi-card"><p class="kpi-value">{v}</p><p class="kpi-label">{l}</p></div>', unsafe_allow_html=True)

    with st.expander("📊 Column Profiles"):
        pd_rows = []
        for p in col_profiles:
            r = {'Column': p['column'], 'Type': p['dtype'], 'Non-Null': p['count'], 'Missing%': p['missing_pct'], 'Unique': p['unique']}
            if p.get('category') == 'numeric':
                r.update({'Mean': p.get('mean',''), 'Std': p.get('std',''), 'Min': p.get('min',''), 'Max': p.get('max','')})
            elif p.get('category') == 'categorical':
                r.update({'Top Value': p.get('most_common',''), 'Top%': p.get('most_common_pct','')})
            pd_rows.append(r)
        st.dataframe(pd.DataFrame(pd_rows), use_container_width=True)

    if consts: st.warning(f"⚡ {len(consts)} constant column(s): {', '.join(c['column'] for c in consts)}")
    if hcard: st.info(f"🔢 {len(hcard)} high-cardinality column(s): {', '.join(c['column'] for c in hcard)}")

    # ── KPIs (cached) ────────────────────────────────────────────
    st.markdown('<div class="section-header">📊 KPI Dashboard</div>', unsafe_allow_html=True)

    @st.cache_data(show_spinner=False)
    def _cached_analysis(_df):
        return run_analysis(_df)

    kpis, analysis = _cached_analysis(df_clean)

    if kpis:
        kn = list(kpis.keys())[:6]
        r1 = st.columns(min(len(kn), 3))
        for i, cn in enumerate(kn[:3]):
            with r1[i]:
                k = kpis[cn]; dc = 'positive' if k['growth_pct'] >= 0 else 'negative'; di = '▲' if k['growth_pct'] >= 0 else '▼'
                st.markdown(f'<div class="kpi-card"><p class="kpi-value">{k["total"]:,.0f}</p><p class="kpi-label">Total {cn}</p>'
                            f'<p class="kpi-delta {dc}">{di} {k["growth_pct"]:+.1f}%</p></div>', unsafe_allow_html=True)
        if len(kn) > 3:
            r2 = st.columns(min(len(kn)-3, 3))
            for i, cn in enumerate(kn[3:6]):
                with r2[i]:
                    k = kpis[cn]
                    st.markdown(f'<div class="kpi-card"><p class="kpi-value">{k["average"]:,.2f}</p><p class="kpi-label">Avg {cn}</p></div>', unsafe_allow_html=True)

    # ── CHARTS ────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📈 Interactive Visualizations</div>', unsafe_allow_html=True)
    if numeric_cols:
        tabs = st.tabs(["📊 Distribution","📈 Trends","🔗 Correlation","🍩 Categories","📦 Box/Violin","🕸️ Advanced","🔍 Scatter Matrix"])
        with tabs[0]:
            hc = st.selectbox("Column:", numeric_cols, key='hc')
            try: st.plotly_chart(histogram_chart(df_clean, hc), use_container_width=True)
            except Exception as e: st.error(str(e))
        with tabs[1]:
            if date_cols:
                t1, t2 = st.columns(2)
                with t1: td = st.selectbox("Date:", date_cols, key='td')
                with t2: tv = st.selectbox("Value:", numeric_cols, key='tv')
                try:
                    tr = trend_analysis(df_clean, td, tv)
                    if tr:
                        st.markdown(f'<div style="background:#1E293B;border-radius:10px;padding:0.8rem;margin-bottom:0.8rem">'
                                    f'<span class="badge badge-purple">Trend: {tr["direction"]}</span>'
                                    f'<span class="badge badge-blue">Change: {tr["change_pct"]:+.1f}%</span></div>', unsafe_allow_html=True)
                        st.plotly_chart(line_chart(tr['time_series_df'], td, tv), use_container_width=True)
                except Exception as e: st.error(str(e))
            else:
                iv = st.selectbox("Value:", numeric_cols, key='iv')
                dp = df_clean[[iv]].reset_index()
                try: st.plotly_chart(line_chart(dp, 'index', iv), use_container_width=True)
                except Exception as e: st.error(str(e))
        with tabs[2]:
            try:
                corr = correlation_analysis(df_clean)
                if corr is not None and len(corr) > 1:
                    st.plotly_chart(heatmap_chart(corr), use_container_width=True)
                    pairs = get_correlation_pairs(df_clean, 0.5)
                    if pairs: st.dataframe(pd.DataFrame(pairs), use_container_width=True)
                else: st.info("Need 2+ numeric columns.")
            except Exception as e: st.error(str(e))
        with tabs[3]:
            if cat_cols:
                c1, c2 = st.columns(2)
                with c1: catc = st.selectbox("Category:", cat_cols, key='catc')
                with c2: valc = st.selectbox("Value:", numeric_cols, key='valc')
                try:
                    g = df_clean.groupby(catc)[valc].sum().reset_index()
                    gc1, gc2 = st.columns(2)
                    with gc1: st.plotly_chart(pie_chart(g, catc, valc), use_container_width=True)
                    with gc2: st.plotly_chart(bar_chart(g, catc, valc), use_container_width=True)
                    pa = pareto_analysis(df_clean, catc, valc)
                    if pa:
                        st.plotly_chart(pareto_chart(pa['categories'], pa['values'], title=f'Pareto: {valc} by {catc}'), use_container_width=True)
                        st.info(f"Top {pa['categories_for_80_pct']} of {pa['total_categories']} categories = ~80% of {valc}")
                except Exception as e: st.error(str(e))
            else: st.info("No categorical columns.")
        with tabs[4]:
            b1, b2 = st.columns(2)
            with b1: bxc = st.selectbox("Numeric:", numeric_cols, key='bxc')
            with b2: bxg = st.selectbox("Group by:", ['None']+cat_cols, key='bxg')
            cb = bxg if bxg != 'None' else None
            c1, c2 = st.columns(2)
            with c1:
                try: st.plotly_chart(box_chart(df_clean, bxc, color_col=cb), use_container_width=True)
                except: pass
            with c2:
                try: st.plotly_chart(violin_chart(df_clean, bxc, color_col=cb), use_container_width=True)
                except: pass
        with tabs[5]:
            at = st.selectbox("Type:", ["Missing Values Heatmap","Radar (Averages)"], key='at')
            if at == "Missing Values Heatmap":
                try: st.plotly_chart(missing_values_heatmap(df_raw), use_container_width=True)
                except Exception as e: st.error(str(e))
            elif numeric_cols:
                try:
                    avgs = [df_clean[c].mean() for c in numeric_cols[:8]]
                    mx = max(abs(a) for a in avgs) if avgs else 1
                    norm = [v/mx*100 for v in avgs]
                    st.plotly_chart(radar_chart(df_clean, numeric_cols[:8], norm), use_container_width=True)
                except Exception as e: st.error(str(e))
        with tabs[6]:
            if len(numeric_cols) >= 2:
                sel = st.multiselect("Columns:", numeric_cols, default=numeric_cols[:min(4,len(numeric_cols))], key='sm')
                if len(sel) >= 2:
                    try: st.plotly_chart(scatter_matrix_chart(df_clean, sel), use_container_width=True)
                    except Exception as e: st.error(str(e))
    else: st.info("No numeric columns for visualization.")

    # ── INSIGHTS ──────────────────────────────────────────────────
    st.markdown('<div class="section-header">🧠 AI-Generated Insights</div>', unsafe_allow_html=True)

    @st.cache_data(show_spinner=False)
    def _cached_insights(_df, _cr, _kpis):
        return run_insights(_df, _cr, _kpis)

    insights, narrative = _cached_insights(df_clean, cr_report, kpis)

    st.markdown(f'<div style="background:linear-gradient(135deg,rgba(124,58,237,0.1),rgba(59,130,246,0.1));border:1px solid rgba(124,58,237,0.2);border-radius:12px;padding:1rem;margin-bottom:1rem">'
                f'<p style="color:#A78BFA;font-size:0.7rem;text-transform:uppercase;letter-spacing:1.5px;margin:0 0 0.4rem">Executive Summary</p>'
                f'<p style="color:#E2E8F0;font-size:0.9rem;line-height:1.5;margin:0">{narrative}</p></div>', unsafe_allow_html=True)
    for ins in insights:
        st.markdown(f'<div class="insight-card {ins["severity"]}"><p class="insight-category">{ins["category"]}</p>'
                    f'<p class="insight-text">{ins["icon"]} {ins["insight"]}</p></div>', unsafe_allow_html=True)

    # ── ANOMALIES ─────────────────────────────────────────────────
    st.markdown('<div class="section-header">🚨 Anomaly Detection</div>', unsafe_allow_html=True)

    with st.spinner("Running anomaly detection..."):
        ml_result, anomaly_results, anom_summaries = run_anomaly_detection(df_clean, anomaly_method, anomaly_sensitivity)

    if ml_result:
        for s in ml_anomaly_summary(ml_result): st.markdown(s)
        if ml_result.get('count', 0) > 0:
            with st.expander(f"📋 ML Anomalies ({ml_result['count']})"):
                d = ml_result['anomalies_df'].copy()
                if '_row_index' in d.columns: d = d.drop(columns=['_row_index'])
                st.dataframe(d, use_container_width=True)
    for s in anom_summaries: st.markdown(s)
    if anomaly_results:
        acol = st.selectbox("Visualize:", list(anomaly_results.keys()), key='avc')
        if acol:
            ar = anomaly_results[acol]
            df_c2 = df_clean.copy()
            if '_row_index' not in df_c2.columns: df_c2['_row_index'] = range(len(df_c2))
            xa = date_cols[0] if date_cols else '_row_index'
            try: st.plotly_chart(anomaly_chart(df_c2, xa, acol, ar['anomaly_mask']), use_container_width=True)
            except: pass
            if not ar['anomalies_df'].empty:
                with st.expander(f"📋 Anomalies ({ar['count']})"):
                    d = ar['anomalies_df'].copy()
                    if '_row_index' in d.columns: d = d.drop(columns=['_row_index'])
                    st.dataframe(d, use_container_width=True)

    # ── STATISTICAL TESTS ─────────────────────────────────────────
    st.markdown('<div class="section-header">📐 Statistical Analysis</div>', unsafe_allow_html=True)
    stabs = st.tabs(["Regression","Group Comparison","Normality","Pivot Table"])
    with stabs[0]:
        if len(numeric_cols) >= 2:
            rc1, rc2 = st.columns(2)
            with rc1: rx = st.selectbox("X:", numeric_cols, key='rx')
            with rc2: ry = st.selectbox("Y:", [c for c in numeric_cols if c != rx] or numeric_cols, key='ry')
            reg = linear_regression(df_clean, rx, ry)
            if reg and 'error' not in reg:
                st.plotly_chart(regression_chart(df_clean, rx, ry, reg), use_container_width=True)
                mc = st.columns(4)
                with mc[0]: st.metric("R²", f"{reg['r_squared']:.4f}")
                with mc[1]: st.metric("Slope", f"{reg['slope']:.4f}")
                with mc[2]: st.metric("P-value", f"{reg['p_value']:.4f}")
                with mc[3]: st.metric("Points", reg['n_points'])
                st.info(f"📊 {reg['interpretation']}")
                st.code(reg['equation'])
    with stabs[1]:
        if cat_cols and numeric_cols:
            g1, g2 = st.columns(2)
            with g1: gcol = st.selectbox("Group:", cat_cols, key='gcol')
            with g2: gval = st.selectbox("Value:", numeric_cols, key='gval')
            comp = compare_groups(df_clean, gcol, gval)
            if comp is not None: st.dataframe(comp, use_container_width=True)
            an = anova_test(df_clean, gval, gcol)
            if an and 'error' not in an: st.info(f"📊 ANOVA: {an['interpretation']}")
    with stabs[2]:
        if numeric_cols:
            nc = st.selectbox("Column:", numeric_cols, key='nc')
            nr = normality_test(df_clean[nc])
            if 'error' not in nr:
                st.metric(f"{nr['test']}", f"{nr['statistic']:.4f}")
                st.metric("P-value", f"{nr['p_value']:.4f}")
                if nr['is_normal']: st.success(f"✅ {nr['interpretation']}")
                else: st.warning(f"⚠️ {nr['interpretation']}")
    with stabs[3]:
        if cat_cols and numeric_cols:
            p1, p2, p3 = st.columns(3)
            with p1: pidx = st.selectbox("Rows:", cat_cols, key='pidx')
            with p2: pval = st.selectbox("Values:", numeric_cols, key='pval')
            with p3: pagg = st.selectbox("Agg:", ['mean','sum','count','min','max'], key='pagg')
            pcol = st.selectbox("Columns:", ['None']+[c for c in cat_cols if c != pidx], key='pcol')
            pvt = build_pivot_table(df_clean, pidx, pval, pagg, pcol if pcol != 'None' else None)
            if pvt is not None: st.dataframe(pvt, use_container_width=True)

    # ── FINANCE MODULE ────────────────────────────────────────────
    st.markdown('<div class="section-header">💰 Finance & Accounting</div>', unsafe_allow_html=True)
    fin_cols = detect_financial_columns(df_clean)
    if fin_cols and len(fin_cols) >= 1:
        ftabs = st.tabs(["Budget Variance","Expense Analysis","Tax/VAT Audit","Financial Ratios"])
        with ftabs[0]:
            if len(fin_cols) >= 2:
                f1, f2, f3 = st.columns(3)
                with f1: bcol = st.selectbox("Budget Column:", fin_cols, key='bcol')
                with f2: acol2 = st.selectbox("Actual Column:", [c for c in fin_cols if c != bcol] or fin_cols, key='acol2')
                with f3: ccol = st.selectbox("Category:", ['None']+cat_cols, key='ccol')
                bva = budget_variance_analysis(df_clean, bcol, acol2, ccol if ccol != 'None' else None)
                if 'error' not in bva:
                    s = bva['summary']
                    bc = st.columns(4)
                    with bc[0]: st.metric("Total Budget", f"{s['total_budget']:,.0f}")
                    with bc[1]: st.metric("Total Actual", f"{s['total_actual']:,.0f}")
                    with bc[2]: st.metric("Variance", f"{s['total_variance']:+,.0f}")
                    with bc[3]: st.metric("Variance %", f"{s['total_variance_pct']:+.1f}%")
                    st.dataframe(bva['detail_df'][['variance','variance_pct','status']].head(20) if 'detail_df' in bva else pd.DataFrame(), use_container_width=True)
                    if 'category_breakdown' in s: st.dataframe(s['category_breakdown'], use_container_width=True)
            else: st.info("Need 2+ financial columns for budget variance.")
        with ftabs[1]:
            if cat_cols and fin_cols:
                e1, e2 = st.columns(2)
                with e1: ecol = st.selectbox("Amount:", fin_cols, key='ecol')
                with e2: ecat = st.selectbox("Category:", cat_cols, key='ecat')
                exp = expense_categorization(df_clean, ecol, ecat)
                if 'error' not in exp:
                    ec = st.columns(3)
                    with ec[0]: st.metric("Total", f"{exp['total_expenses']:,.0f}")
                    with ec[1]: st.metric("Categories", exp['n_categories'])
                    with ec[2]: st.metric("Top 3 = ", f"{exp['top_3_percentage']}%")
                    st.dataframe(exp['breakdown'], use_container_width=True)
            else: st.info("Need category + numeric columns.")
        with ftabs[2]:
            if fin_cols:
                ta1, ta2 = st.columns(2)
                with ta1: tamount = st.selectbox("Amount Column:", fin_cols, key='tamount')
                tax_col_opts = [c for c in fin_cols if c != tamount]
                with ta2: ttax = st.selectbox("Tax Column (optional):", ['None']+tax_col_opts, key='ttax')
                item_col = st.selectbox("Item Column (optional):", ['None']+cat_cols, key='titem')
                audit = tax_vat_audit(df_clean, tamount, ttax if ttax != 'None' else None,
                                      item_col=item_col if item_col != 'None' else None)
                if 'error' not in audit:
                    for f in audit.get('findings', []):
                        sev_class = {'critical':'critical','warning':'warning','positive':'positive'}.get(f['severity'], 'info')
                        st.markdown(f'<div class="insight-card {sev_class}"><p class="insight-category">{f["severity"].upper()}</p>'
                                    f'<p class="insight-text">{f["icon"]} {f["issue"]}</p></div>', unsafe_allow_html=True)
                        if f.get('details'): st.markdown(f"  *{f['details']}*")
            else: st.info("No financial columns detected.")
        with ftabs[3]:
            if fin_cols:
                ratios = financial_ratios(df_clean,
                    revenue_col=fin_cols[0] if len(fin_cols) >= 1 else None,
                    cost_col=fin_cols[1] if len(fin_cols) >= 2 else None,
                    profit_col=fin_cols[2] if len(fin_cols) >= 3 else None)
                if ratios:
                    rc = st.columns(min(len(ratios), 4))
                    for i, (k, v) in enumerate(ratios.items()):
                        with rc[i%4]: st.metric(k.replace('_',' ').title(), f"{v:,.2f}")

    # ── SMART JOIN ────────────────────────────────────────────────
    if second_file:
        st.markdown('<div class="section-header">🔗 Smart Join Results</div>', unsafe_allow_html=True)
        with st.spinner("Loading second file..."):
            try:
                r2 = load_file(second_file)
                df2 = r2['dataframe']
                st.markdown(f'<span class="badge badge-green">📁 {r2.get("file_name","file2")}: {df2.shape[0]} rows × {df2.shape[1]} cols</span>', unsafe_allow_html=True)
                keys1 = detect_key_columns(df_clean)
                keys2 = detect_key_columns(df2)
                matches = find_matching_columns(df_clean, df2)
                if matches:
                    st.success(f"✅ Found {len(matches)} potential column match(es)!")
                    st.dataframe(pd.DataFrame(matches), use_container_width=True)
                    best = matches[0]
                    j1, j2, j3 = st.columns(3)
                    with j1: left_key = st.selectbox("Left key:", df_clean.columns, index=list(df_clean.columns).index(best['col1']) if best['col1'] in df_clean.columns else 0, key='lk')
                    with j2: right_key = st.selectbox("Right key:", df2.columns, index=list(df2.columns).index(best['col2']) if best['col2'] in df2.columns else 0, key='rk')
                    with j3: join_type = st.selectbox("Join type:", ['left','inner','outer','right'], key='jt')
                    if st.button("🔗 Execute Join", use_container_width=True):
                        jresult = run_join(df_clean, df2, left_key, right_key, join_type)
                        if 'error' not in jresult:
                            jc = st.columns(4)
                            with jc[0]: st.metric("Left Rows", jresult['left_rows'])
                            with jc[1]: st.metric("Right Rows", jresult['right_rows'])
                            with jc[2]: st.metric("Merged Rows", jresult['merged_rows'])
                            with jc[3]: st.metric("Match Rate", f"{jresult['match_rate_left']}%")
                            st.dataframe(jresult['merged_df'], use_container_width=True, height=400)
                            buf = BytesIO()
                            jresult['merged_df'].to_excel(buf, index=False)
                            buf.seek(0)
                            st.download_button("📥 Download Merged Data", buf, "merged_data.xlsx",
                                              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                        else: st.error(jresult['error'])
                else: st.warning("Could not auto-detect matching columns. Please select manually.")
            except Exception as e: st.error(f"Join error: {e}")

    # ── NLQ ───────────────────────────────────────────────────────
    st.markdown('<div class="section-header">💬 Natural Language Query</div>', unsafe_allow_html=True)
    st.markdown('<div style="background:#1E293B;border-radius:10px;padding:0.8rem;margin-bottom:0.8rem">'
                '<p style="color:#94A3B8;font-size:0.8rem;margin:0"><b style="color:#A78BFA">Try:</b> '
                '"top 5 by sales" · "average of profit" · "group by region and sum sales" · '
                '"compare sales between North and South" · "what correlates with profit?"</p></div>', unsafe_allow_html=True)
    uq = st.text_input("Ask about your data:", placeholder="e.g., group by category and sum sales", key='nlq')
    if uq:
        qr = process_nlq(df_clean, uq)
        if qr['success']:
            st.success(f"✅ {qr['explanation']}")
            if qr.get('dataframe') is not None: st.dataframe(qr['dataframe'], use_container_width=True)
            if qr.get('value') is not None: st.metric("Result", qr['value'])
        else: st.warning(f"⚠️ {qr['explanation']}")

    # ── EXPORT ────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📄 Export Reports</div>', unsafe_allow_html=True)
    logo_path = None
    if logo_file:
        logo_path = '/tmp/logo_upload.png'
        with open(logo_path, 'wb') as f: f.write(logo_file.read())

    rc = st.columns(2)
    with rc[0]:
        st.markdown('<div class="kpi-card"><p style="font-size:1.8rem;margin:0">📊</p>'
                    '<p class="kpi-label" style="margin:0.3rem 0">Excel Report (Formula-Rich)</p>'
                    '<p style="color:#64748B;font-size:0.7rem;margin:0">Live SUM/AVG/MIN/MAX formulas + conditional formatting</p></div>', unsafe_allow_html=True)
        try:
            ebuf = ExcelReportGenerator.generate(df_clean, analysis, anomaly_results, kpis, col_profiles, cr_report)
            sn = fn.rsplit('.', 1)[0] if '.' in fn else fn
            st.download_button("📥 Download Excel Report", ebuf, f"ai_report_{sn}.xlsx",
                              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                              use_container_width=True, key='dl_xl')
        except Exception as e: st.error(f"Excel error: {e}")
    with rc[1]:
        st.markdown(f'<div class="kpi-card"><p style="font-size:1.8rem;margin:0">📄</p>'
                    f'<p class="kpi-label" style="margin:0.3rem 0">PDF Report {"(White-Label)" if brand_name else ""}</p>'
                    f'<p style="color:#64748B;font-size:0.7rem;margin:0">{"Branded for " + brand_name if brand_name else "Professional report with TOC & insights"}</p></div>', unsafe_allow_html=True)
        try:
            ml_info = ml_anomaly_summary(ml_result) if ml_result else None
            pbuf = PDFReportGenerator.generate(df_clean, kpis, insights, anom_summaries, narrative, ds_profile, ml_info, cr_report,
                                               brand_name=brand_name or None, brand_color_hex=brand_color, logo_path=logo_path)
            sn = fn.rsplit('.', 1)[0] if '.' in fn else fn
            st.download_button("📥 Download PDF Report", pbuf, f"ai_report_{sn}.pdf", "application/pdf",
                              use_container_width=True, key='dl_pdf')
        except Exception as e: st.error(f"PDF error: {e}")

    # ── FOOTER ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div style="text-align:center;padding:0.8rem"><p style="color:#64748B;font-size:0.75rem">'
                '🚀 <b>AI Excel Automation Engine v4.0</b> — Built by <a href="https://github.com/muh0210" style="color:#7C3AED">Muhammad Rajput</a><br>'
                '<span style="font-size:0.65rem">Streamlit · Pandas · Plotly · scikit-learn · Python</span></p></div>', unsafe_allow_html=True)

else:
    # ── LANDING PAGE ──────────────────────────────────────────────
    fc = st.columns(3)
    features = [
        ("🧹","Smart Cleaning","Detects empty cells, N/A, spaces as missing — fills intelligently"),
        ("🧠","AI Insights","20+ insight types: Pareto, trends, outliers, correlations, recommendations"),
        ("📈","15+ Chart Types","Line, bar, pie, heatmap, violin, radar, sunburst, pareto & more"),
        ("🚨","ML Anomaly Detection","Z-Score, IQR, Isolation Forest & Local Outlier Factor"),
        ("💰","Finance Module","Budget variance, expense analysis, tax/VAT audit, financial ratios"),
        ("🔗","Smart Join","Upload 2 files — auto-detect keys and merge. The VLOOKUP killer"),
        ("📐","Statistical Tests","Regression, ANOVA, normality, chi-square, pivot tables"),
        ("🏷️","White-Label Reports","Custom logo, brand colors, company name on PDF reports"),
        ("📊","Formula-Rich Excel","Live SUM/AVG/STDEV formulas + conditional color formatting")]
    for i,(icon,title,desc) in enumerate(features):
        with fc[i%3]:
            st.markdown(f'<div class="kpi-card" style="margin-bottom:0.8rem;text-align:left;padding:1.2rem">'
                        f'<p style="font-size:1.8rem;margin:0">{icon}</p>'
                        f'<p style="color:#E2E8F0;font-size:0.95rem;font-weight:700;margin:0.4rem 0 0.2rem">{title}</p>'
                        f'<p style="color:#94A3B8;font-size:0.75rem;margin:0;line-height:1.3">{desc}</p></div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;margin-top:1.5rem;padding:1.5rem;background:linear-gradient(135deg,rgba(124,58,237,0.08),rgba(59,130,246,0.08));border-radius:16px;border:1px dashed rgba(124,58,237,0.3)">'
                '<p style="font-size:2.2rem;margin:0">📂</p>'
                '<p style="color:#A78BFA;font-size:1rem;font-weight:600;margin:0.4rem 0">Upload a file or try a demo dataset</p>'
                '<p style="color:#64748B;font-size:0.8rem">Supports Excel (.xlsx, .xls) and CSV up to 50MB</p></div>', unsafe_allow_html=True)
