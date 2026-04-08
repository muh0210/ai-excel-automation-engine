"""
AI EXCEL AUTOMATION ENGINE — Premium Streamlit Application
Upload -> Clean -> Profile -> Analyze -> Insights -> Anomalies -> Visualize -> Export
Author: Muhammad Rajput (muh0210) | muhrajpoot1921@gmail.com
"""
import streamlit as st
import pandas as pd
import numpy as np
import re, os
from io import BytesIO

from utils.loader import load_file, load_specific_sheet, get_file_preview
from utils.cleaner import clean_data
from utils.analyzer import (
    basic_analysis, correlation_analysis, auto_group_analysis,
    trend_analysis, top_bottom_n, compute_kpis, pareto_analysis,
    moving_average, seasonality_analysis, compare_groups
)
from utils.visualizer import (
    line_chart, bar_chart, scatter_chart, pie_chart,
    heatmap_chart, box_chart, histogram_chart, anomaly_chart,
    violin_chart, radar_chart, waterfall_chart, funnel_chart,
    sunburst_chart, scatter_matrix_chart, stacked_area_chart,
    missing_values_heatmap, regression_chart, pareto_chart, COLORS
)
from utils.insights import generate_insights, generate_summary_narrative
from utils.anomaly import (
    detect_anomalies_zscore, detect_anomalies_iqr,
    detect_all_anomalies, anomaly_summary,
    detect_ml_anomalies, ml_anomaly_summary, SKLEARN_AVAILABLE
)
from utils.reporter import ExcelReportGenerator, PDFReportGenerator
from utils.profiler import profile_dataset, profile_columns, detect_constant_columns, detect_high_cardinality, get_correlation_pairs
from utils.transformer import build_pivot_table, create_calculated_column, bin_column
from utils.statistics import normality_test, ttest_two_groups, anova_test, chi_square_test, linear_regression, percentile_analysis

# ══════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════
def _find_column(df, name):
    name_lower = name.lower().strip()
    for col in df.columns:
        if col.lower() == name_lower:
            return col
    for col in df.columns:
        if name_lower in col.lower() or col.lower() in name_lower:
            return col
    return None

def process_nlq(df, query):
    q = query.lower().strip()
    try:
        if 'show columns' in q or 'list columns' in q:
            cols_df = pd.DataFrame({'Column': df.columns, 'Type': [str(dt) for dt in df.dtypes], 'Non-Null': [int(df[c].notna().sum()) for c in df.columns]})
            return {'success': True, 'explanation': f'Dataset has {len(df.columns)} columns:', 'dataframe': cols_df, 'value': None}
        m = re.search(r'describe\s+(\w+)', q)
        if m:
            col = _find_column(df, m.group(1))
            if col:
                return {'success': True, 'explanation': f'Description of "{col}":', 'dataframe': df[col].describe().reset_index(), 'value': None}
        m = re.search(r'group\s+(?:by\s+)?(\w+)\s+(?:and\s+)?(sum|mean|avg|count|max|min)\s+(?:of\s+)?(\w+)', q)
        if m:
            gc, func, vc = _find_column(df, m.group(1)), m.group(2), _find_column(df, m.group(3))
            if gc and vc:
                func = 'mean' if func == 'avg' else func
                grouped = df.groupby(gc)[vc].agg(func).reset_index().sort_values(vc, ascending=False)
                return {'success': True, 'explanation': f'{func.title()} of "{vc}" grouped by "{gc}":', 'dataframe': grouped, 'value': None}
        m = re.search(r'compare\s+(\w+)\s+between\s+(\w+)\s+and\s+(\w+)', q)
        if m:
            vc, g1, g2 = _find_column(df, m.group(1)), m.group(2), m.group(3)
            if vc:
                cat_cols = df.select_dtypes(include=['object','category']).columns
                for cc in cat_cols:
                    vals = df[cc].astype(str).str.lower()
                    if g1.lower() in vals.values and g2.lower() in vals.values:
                        d1 = df[vals == g1.lower()][vc].describe()
                        d2 = df[vals == g2.lower()][vc].describe()
                        comp = pd.DataFrame({g1: d1, g2: d2})
                        return {'success': True, 'explanation': f'Comparing "{vc}" between {g1} and {g2}:', 'dataframe': comp, 'value': None}
        m = re.search(r'(top|bottom|highest|lowest|best|worst)\s+(\d+)\s+(?:by|in|of)?\s*(\w+)', q)
        if m:
            direction, n, col = m.group(1), int(m.group(2)), _find_column(df, m.group(3))
            if col and pd.api.types.is_numeric_dtype(df[col]):
                asc = direction in ('bottom', 'lowest', 'worst')
                return {'success': True, 'explanation': f'{"Bottom" if asc else "Top"} {n} by "{col}":', 'dataframe': df.sort_values(col, ascending=asc).head(n), 'value': None}
        m = re.search(r'(average|avg|mean|sum|total|min|minimum|max|maximum|median|count)\s+(?:of\s+)?(\w+)', q)
        if m:
            func_str, col = m.group(1), _find_column(df, m.group(2))
            if col and pd.api.types.is_numeric_dtype(df[col]):
                fm = {'average':'mean','avg':'mean','mean':'mean','sum':'sum','total':'sum','min':'min','minimum':'min','max':'max','maximum':'max','median':'median','count':'count'}
                val = getattr(df[col], fm.get(func_str, 'mean'))()
                return {'success': True, 'explanation': f'{fm.get(func_str,"mean").title()} of "{col}":', 'dataframe': None, 'value': f'{val:,.2f}'}
        m = re.search(r'(?:what\s+)?correlat\w*\s+(?:with\s+)?(\w+)', q)
        if m:
            col = _find_column(df, m.group(1))
            if col and pd.api.types.is_numeric_dtype(df[col]):
                corr = df.select_dtypes(include='number').corr()[col].drop(col).sort_values(key=abs, ascending=False)
                corr_df = corr.reset_index()
                corr_df.columns = ['Column', 'Correlation']
                return {'success': True, 'explanation': f'Correlations with "{col}":', 'dataframe': corr_df, 'value': None}
        m = re.search(r'filter\s+(?:where\s+)?(\w+)\s+(?:is|equals?|==|contains?)\s+(.+)', q)
        if m:
            col, value = _find_column(df, m.group(1)), m.group(2).strip().strip('"\'')
            if col:
                if pd.api.types.is_numeric_dtype(df[col]):
                    try: filtered = df[df[col] == float(value)]
                    except: filtered = df[df[col].astype(str).str.contains(value, case=False, na=False)]
                else:
                    filtered = df[df[col].astype(str).str.contains(value, case=False, na=False)]
                return {'success': True, 'explanation': f'Filtered {len(filtered)} rows where "{col}" matches "{value}":', 'dataframe': filtered, 'value': None}
        m = re.search(r'filter\s+(?:where\s+)?(\w+)\s+between\s+([\d.]+)\s+and\s+([\d.]+)', q)
        if m:
            col = _find_column(df, m.group(1))
            if col and pd.api.types.is_numeric_dtype(df[col]):
                lo, hi = float(m.group(2)), float(m.group(3))
                filtered = df[(df[col] >= lo) & (df[col] <= hi)]
                return {'success': True, 'explanation': f'{len(filtered)} rows where "{col}" between {lo} and {hi}:', 'dataframe': filtered, 'value': None}
        m = re.search(r'sort\s+(?:by\s+)?(\w+)\s*(asc|ascending|desc|descending)?', q)
        if m:
            col = _find_column(df, m.group(1))
            if col:
                asc = (m.group(2) or 'desc').startswith('asc')
                return {'success': True, 'explanation': f'Sorted by "{col}" {"ascending" if asc else "descending"}:', 'dataframe': df.sort_values(col, ascending=asc), 'value': None}
        m = re.search(r'(?:count\s+)?unique\s+(\w+)', q)
        if m:
            col = _find_column(df, m.group(1))
            if col:
                vc = df[col].value_counts().reset_index()
                vc.columns = [col, 'Count']
                return {'success': True, 'explanation': f'{df[col].nunique()} unique values in "{col}":', 'dataframe': vc, 'value': None}
        m = re.search(r'(?:what\s+)?percent\w*\s+(?:of\s+)?(\w+)\s+(?:is|from|are)\s+(\w+)', q)
        if m:
            col, val = _find_column(df, m.group(1)), m.group(2)
            if col:
                matches = df[df[col].astype(str).str.lower() == val.lower()]
                pct = len(matches) / len(df) * 100
                return {'success': True, 'explanation': f'Percentage of "{val}" in "{col}":', 'dataframe': None, 'value': f'{pct:.1f}%'}
        return {'success': False, 'explanation': 'Could not understand. Try: "show top 5 by sales", "average of profit", "group by region and sum sales", "compare sales between North and South", "filter where sales between 100 and 500", "what correlates with profit?"', 'dataframe': None, 'value': None}
    except Exception as e:
        return {'success': False, 'explanation': f'Error: {str(e)}', 'dataframe': None, 'value': None}

# ══════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════════
st.set_page_config(page_title="AI Excel Automation Engine", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    :root {
        --purple: #7C3AED; --blue: #3B82F6; --cyan: #06B6D4;
        --green: #10B981; --yellow: #F59E0B; --red: #EF4444;
        --bg-dark: #0F172A; --bg-card: #1E293B;
        --text: #E2E8F0; --text-muted: #94A3B8; --grid: #334155;
    }
    html, body { font-family: 'Inter', sans-serif !important; }
    .main-header {
        background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 50%, #06B6D4 100%);
        padding: 1.5rem 2rem; border-radius: 16px; margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(124,58,237,0.3);
        animation: headerGlow 3s ease-in-out infinite alternate;
    }
    @keyframes headerGlow {
        0% { box-shadow: 0 8px 32px rgba(124,58,237,0.3); }
        100% { box-shadow: 0 12px 48px rgba(59,130,246,0.4); }
    }
    .main-header h1 { color: white; font-size: 2rem; font-weight: 800; margin: 0; letter-spacing: -0.5px; }
    .main-header p { color: rgba(255,255,255,0.85); font-size: 0.95rem; margin: 0.3rem 0 0 0; }
    .section-header {
        background: linear-gradient(90deg, rgba(124,58,237,0.15), transparent);
        border-left: 4px solid var(--purple); padding: 0.6rem 1rem;
        border-radius: 0 8px 8px 0; margin: 1.5rem 0 1rem 0;
        font-size: 1.1rem; font-weight: 700; color: var(--text);
        display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .kpi-card {
        background: linear-gradient(145deg, #1E293B, #0F172A);
        border: 1px solid rgba(124,58,237,0.25); border-radius: 12px;
        padding: 1rem; text-align: center; transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2); overflow: hidden;
    }
    .kpi-card:hover { border-color: var(--purple); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(124,58,237,0.2); }
    .kpi-value { font-size: 1.5rem; font-weight: 800; color: var(--purple); margin: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .kpi-label { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; margin: 0.2rem 0 0 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .kpi-delta { font-size: 0.8rem; font-weight: 600; margin-top: 0.2rem; }
    .kpi-delta.positive { color: var(--green); }
    .kpi-delta.negative { color: var(--red); }
    .insight-card {
        background: var(--bg-card); border-radius: 10px; padding: 0.8rem 1rem;
        margin-bottom: 0.6rem; border-left: 4px solid var(--blue); transition: all 0.2s ease;
    }
    .insight-card:hover { background: #263548; transform: translateX(4px); }
    .insight-card.positive { border-left-color: var(--green); }
    .insight-card.warning { border-left-color: var(--yellow); }
    .insight-card.critical { border-left-color: var(--red); }
    .insight-card.info { border-left-color: var(--blue); }
    .insight-category { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-muted); margin-bottom: 0.15rem; }
    .insight-text { color: var(--text); font-size: 0.9rem; line-height: 1.4; }
    .badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.72rem; font-weight: 600; margin-right: 0.4rem; margin-bottom: 0.3rem; }
    .badge-purple { background: rgba(124,58,237,0.2); color: #A78BFA; }
    .badge-blue { background: rgba(59,130,246,0.2); color: #60A5FA; }
    .badge-green { background: rgba(16,185,129,0.2); color: #34D399; }
    .badge-yellow { background: rgba(245,158,11,0.2); color: #FBBF24; }
    .badge-red { background: rgba(239,68,68,0.2); color: #F87171; }
    .empty-state { background: var(--bg-card); border-radius: 12px; padding: 2rem; text-align: center; border: 1px dashed rgba(124,58,237,0.3); }
    .empty-state p.icon { font-size: 2rem; margin: 0; }
    .empty-state p.msg { color: var(--text-muted); font-size: 0.85rem; margin: 0.5rem 0 0; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0F172A, #1E293B) !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] { background: transparent; border-radius: 8px; padding: 6px 14px; color: var(--text-muted); }
    .stTabs [aria-selected="true"] { background: rgba(124,58,237,0.2) !important; color: #A78BFA !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    div[data-testid="stExpander"] summary span { font-size: 0.9rem !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""<div style="text-align:center; padding: 0.8rem 0;">
        <span style="font-size: 2.5rem;">🚀</span>
        <h2 style="margin: 0.3rem 0 0; font-weight: 800; background: linear-gradient(90deg, #7C3AED, #3B82F6);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;">AI Excel Engine</h2>
        <p style="color: #94A3B8; font-size: 0.8rem;">Premium Data Automation</p>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Settings")
    anomaly_method = st.selectbox("Anomaly Detection Method", ['Z-Score', 'IQR', 'Isolation Forest (ML)', 'Local Outlier Factor (ML)'], help="Statistical or ML-based anomaly detection")
    anomaly_sensitivity = st.slider("Anomaly Sensitivity", 1.0, 4.0, 2.0, 0.5, help="Lower = more sensitive")
    show_raw_data = st.checkbox("Show Raw Data", value=False)
    st.markdown("---")
    st.markdown("""<div style="text-align:center; padding: 0.3rem;">
        <p style="color: #64748B; font-size: 0.7rem;">Built by <b>Muhammad Rajput</b><br>
        <a href="https://github.com/muh0210" style="color: #7C3AED;">github.com/muh0210</a></p>
    </div>""", unsafe_allow_html=True)

# ── Header ──
st.markdown("""<div class="main-header">
    <h1>🚀 AI Excel Automation Engine</h1>
    <p>Upload → Clean → Profile → Analyze → Insights → Anomalies → Visualize → Export</p>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  FILE UPLOAD
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">📥 Upload Your Data</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("Drop your Excel or CSV file here", type=['xlsx','xls','csv'], help="Supports .xlsx, .xls, .csv up to 50MB")

# Demo data button
demo_col1, demo_col2, demo_col3 = st.columns([1,1,1])
with demo_col1:
    demo_sales = st.button("🛒 Try E-Commerce Demo", use_container_width=True)
with demo_col2:
    demo_emp = st.button("👥 Try Employee Demo", use_container_width=True)
with demo_col3:
    demo_finance = st.button("💰 Try Finance Demo", use_container_width=True)

# Handle demo data
demo_path = None
if demo_sales: demo_path = 'data/sample_ecommerce_sales.xlsx'
elif demo_emp: demo_path = 'data/sample_employee_data.xlsx'
elif demo_finance: demo_path = 'data/sample_financial_report.xlsx'

if demo_path and os.path.exists(demo_path):
    st.session_state['demo_file'] = demo_path

use_demo = st.session_state.get('demo_file')
active_file = uploaded_file or use_demo

# ══════════════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════
if active_file is not None:
    # Clear demo if user uploads
    if uploaded_file:
        st.session_state.pop('demo_file', None)

    # LOAD
    with st.spinner("Loading data..."):
        try:
            result = load_file(active_file)
            df_raw = result['dataframe']
        except Exception as e:
            st.error(f"Failed to load file: {e}")
            st.stop()

    if result.get('sheet_names') and len(result['sheet_names']) > 1:
        selected_sheet = st.selectbox("Multiple sheets detected:", result['sheet_names'])
        if selected_sheet != result['sheet_names'][0]:
            if hasattr(active_file, 'seek'): active_file.seek(0)
            df_raw = load_specific_sheet(active_file, selected_sheet)

    file_name = result.get('file_name', 'data')
    st.markdown(f"""<div style="margin: 0.8rem 0;">
        <span class="badge badge-purple">📁 {file_name}</span>
        <span class="badge badge-blue">📐 {df_raw.shape[0]} rows × {df_raw.shape[1]} cols</span>
        <span class="badge badge-green">💾 {result.get('file_size_kb','?')} KB</span>
    </div>""", unsafe_allow_html=True)

    if show_raw_data:
        with st.expander("📋 Raw Data Preview", expanded=False):
            st.dataframe(df_raw, use_container_width=True, height=300)

    # CLEAN
    st.markdown('<div class="section-header">🧹 Data Cleaning Engine</div>', unsafe_allow_html=True)
    with st.spinner("Cleaning..."):
        df_clean, cleaning_report = clean_data(df_raw)

    cr = st.columns(4)
    items = [
        (cleaning_report["duplicates_removed"], "Duplicates Removed"),
        (sum(cleaning_report.get('missing_values_before',{}).values()), "Missing Fixed"),
        (len(cleaning_report.get('type_conversions',{})), "Type Conversions"),
        (f"{cleaning_report.get('data_completeness',100)}%", "Completeness"),
    ]
    for i, (val, label) in enumerate(items):
        with cr[i]:
            st.markdown(f'<div class="kpi-card"><p class="kpi-value">{val}</p><p class="kpi-label">{label}</p></div>', unsafe_allow_html=True)

    with st.expander("🔍 Detailed Cleaning Report"):
        if cleaning_report.get('columns_renamed'):
            st.markdown("**Column Renames:**")
            for old, new in cleaning_report['columns_renamed'].items(): st.markdown(f"  `{old}` → `{new}`")
        if cleaning_report.get('missing_value_actions'):
            st.markdown("**Missing Value Actions:**")
            for col, act in cleaning_report['missing_value_actions'].items(): st.markdown(f"  - `{col}`: {act}")
        if cleaning_report.get('type_conversions'):
            st.markdown("**Type Conversions:**")
            for col, ch in cleaning_report['type_conversions'].items(): st.markdown(f"  - `{col}`: {ch}")
        st.markdown(f"**Shape:** {cleaning_report['original_shape']} → {cleaning_report['cleaned_shape']}")

    with st.expander("📋 Cleaned Data Preview"):
        st.dataframe(df_clean, use_container_width=True, height=300)

    numeric_cols = list(df_clean.select_dtypes(include='number').columns)
    cat_cols = list(df_clean.select_dtypes(include=['object','category']).columns)
    date_cols = list(df_clean.select_dtypes(include='datetime').columns)

    # DATA PROFILE
    st.markdown('<div class="section-header">🔬 Data Profile</div>', unsafe_allow_html=True)
    ds_profile = profile_dataset(df_clean)
    col_profiles = profile_columns(df_clean)

    pc = st.columns(4)
    profile_items = [
        (f"{ds_profile['rows']:,}", "Total Rows"),
        (f"{ds_profile['columns']}", "Columns"),
        (f"{ds_profile['missing_pct']}%", "Missing"),
        (ds_profile['memory_usage'], "Memory"),
    ]
    for i, (v, l) in enumerate(profile_items):
        with pc[i]:
            st.markdown(f'<div class="kpi-card"><p class="kpi-value">{v}</p><p class="kpi-label">{l}</p></div>', unsafe_allow_html=True)

    with st.expander("📊 Column Profiles"):
        profile_display = []
        for p in col_profiles:
            row = {'Column': p['column'], 'Type': p['dtype'], 'Non-Null': p['count'], 'Missing%': p['missing_pct'], 'Unique': p['unique']}
            if p.get('category') == 'numeric':
                row.update({'Mean': p.get('mean',''), 'Std': p.get('std',''), 'Min': p.get('min',''), 'Max': p.get('max','')})
            elif p.get('category') == 'categorical':
                row.update({'Top Value': p.get('most_common',''), 'Top%': p.get('most_common_pct','')})
            profile_display.append(row)
        st.dataframe(pd.DataFrame(profile_display), use_container_width=True)

    constants = detect_constant_columns(df_clean)
    high_card = detect_high_cardinality(df_clean)
    if constants:
        st.warning(f"⚡ {len(constants)} constant column(s) detected: {', '.join(c['column'] for c in constants)}")
    if high_card:
        st.info(f"🔢 {len(high_card)} high-cardinality column(s): {', '.join(c['column'] for c in high_card)}")

    # KPIs
    st.markdown('<div class="section-header">📊 KPI Dashboard</div>', unsafe_allow_html=True)
    kpis = compute_kpis(df_clean)
    analysis = basic_analysis(df_clean)

    if kpis:
        kpi_names = list(kpis.keys())[:6]
        row1 = st.columns(min(len(kpi_names), 3))
        for i, cn in enumerate(kpi_names[:3]):
            with row1[i]:
                k = kpis[cn]
                dc = 'positive' if k['growth_pct'] >= 0 else 'negative'
                di = '▲' if k['growth_pct'] >= 0 else '▼'
                st.markdown(f"""<div class="kpi-card">
                    <p class="kpi-value">{k['total']:,.0f}</p>
                    <p class="kpi-label">Total {cn}</p>
                    <p class="kpi-delta {dc}">{di} {k['growth_pct']:+.1f}%</p>
                </div>""", unsafe_allow_html=True)
        if len(kpi_names) > 3:
            row2 = st.columns(min(len(kpi_names)-3, 3))
            for i, cn in enumerate(kpi_names[3:6]):
                with row2[i]:
                    k = kpis[cn]
                    st.markdown(f"""<div class="kpi-card">
                        <p class="kpi-value">{k['average']:,.2f}</p>
                        <p class="kpi-label">Avg {cn}</p>
                    </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state"><p class="icon">📭</p><p class="msg">No numeric columns for KPIs.</p></div>', unsafe_allow_html=True)

    # CHARTS
    st.markdown('<div class="section-header">📈 Interactive Visualizations</div>', unsafe_allow_html=True)
    if not numeric_cols:
        st.info("No numeric columns available for visualization.")
    else:
        tabs = st.tabs(["📊 Distribution", "📈 Trends", "🔗 Correlation", "🍩 Categories", "📦 Box/Violin", "🕸️ Advanced", "🔍 Scatter Matrix"])
        with tabs[0]:
            hc = st.selectbox("Column:", numeric_cols, key='hist_col')
            try: st.plotly_chart(histogram_chart(df_clean, hc), use_container_width=True)
            except Exception as e: st.error(f"Chart error: {e}")
        with tabs[1]:
            if date_cols:
                tc1, tc2 = st.columns(2)
                with tc1: td = st.selectbox("Date column:", date_cols, key='td')
                with tc2: tv = st.selectbox("Value column:", numeric_cols, key='tv')
                try:
                    tr = trend_analysis(df_clean, td, tv)
                    if tr:
                        st.markdown(f"""<div style="background:#1E293B;border-radius:10px;padding:0.8rem;margin-bottom:0.8rem;">
                            <span class="badge badge-purple">Trend: {tr['direction']}</span>
                            <span class="badge badge-blue">Change: {tr['change_pct']:+.1f}%</span>
                            <span class="badge badge-green">Points: {tr['data_points']}</span>
                        </div>""", unsafe_allow_html=True)
                        st.plotly_chart(line_chart(tr['time_series_df'], td, tv), use_container_width=True)
                        ma = moving_average(df_clean, td, tv, window=min(7, len(df_clean)//3))
                        if ma is not None:
                            st.plotly_chart(line_chart(ma, td, f'SMA_{min(7, len(df_clean)//3)}', title=f'Moving Average of {tv}'), use_container_width=True)
                except Exception as e: st.error(f"Trend error: {e}")
            else:
                iv = st.selectbox("Value:", numeric_cols, key='iv')
                try:
                    dp = df_clean[[iv]].reset_index()
                    st.plotly_chart(line_chart(dp, 'index', iv, title=f'{iv} Over Row Index'), use_container_width=True)
                except Exception as e: st.error(f"Error: {e}")
        with tabs[2]:
            try:
                corr = correlation_analysis(df_clean)
                if corr is not None and len(corr) > 1:
                    st.plotly_chart(heatmap_chart(corr), use_container_width=True)
                    pairs = get_correlation_pairs(df_clean, min_corr=0.5)
                    if pairs:
                        st.markdown("**Strong Correlations:**")
                        st.dataframe(pd.DataFrame(pairs), use_container_width=True)
                else: st.info("Need 2+ numeric columns for correlation.")
            except Exception as e: st.error(f"Error: {e}")
        with tabs[3]:
            if cat_cols:
                cc1, cc2 = st.columns(2)
                with cc1: catc = st.selectbox("Category:", cat_cols, key='catc')
                with cc2: valc = st.selectbox("Value:", numeric_cols, key='valc')
                try:
                    grouped = df_clean.groupby(catc)[valc].sum().reset_index()
                    c1, c2 = st.columns(2)
                    with c1: st.plotly_chart(pie_chart(grouped, catc, valc), use_container_width=True)
                    with c2: st.plotly_chart(bar_chart(grouped, catc, valc), use_container_width=True)
                    pa = pareto_analysis(df_clean, catc, valc)
                    if pa:
                        st.plotly_chart(pareto_chart(pa['categories'], pa['values'], title=f'Pareto: {valc} by {catc}'), use_container_width=True)
                        st.info(f"Top {pa['categories_for_80_pct']} of {pa['total_categories']} categories contribute ~80% of total {valc}")
                except Exception as e: st.error(f"Error: {e}")
            else: st.info("No categorical columns found.")
        with tabs[4]:
            bc1, bc2 = st.columns(2)
            with bc1: bxc = st.selectbox("Numeric:", numeric_cols, key='bxc')
            with bc2: bxg = st.selectbox("Group by:", ['None']+cat_cols, key='bxg')
            color_by = bxg if bxg != 'None' else None
            c1, c2 = st.columns(2)
            with c1:
                try: st.plotly_chart(box_chart(df_clean, bxc, color_col=color_by), use_container_width=True)
                except Exception as e: st.error(f"Error: {e}")
            with c2:
                try: st.plotly_chart(violin_chart(df_clean, bxc, color_col=color_by), use_container_width=True)
                except Exception as e: st.error(f"Error: {e}")
        with tabs[5]:
            adv_type = st.selectbox("Chart Type:", ["Sunburst", "Missing Values Heatmap", "Radar (Averages)"], key='adv')
            if adv_type == "Sunburst" and len(cat_cols) >= 2 and numeric_cols:
                try:
                    fig = sunburst_chart(df_clean, cat_cols[:2], numeric_cols[0])
                    if fig: st.plotly_chart(fig, use_container_width=True)
                except: st.info("Sunburst requires hierarchical category data.")
            elif adv_type == "Missing Values Heatmap":
                try: st.plotly_chart(missing_values_heatmap(df_raw, title='Missing Values in Raw Data'), use_container_width=True)
                except Exception as e: st.error(f"Error: {e}")
            elif adv_type == "Radar (Averages)" and numeric_cols:
                try:
                    avgs = [df_clean[c].mean() for c in numeric_cols[:8]]
                    norm = [v/max(abs(a) for a in avgs)*100 if max(abs(a) for a in avgs) > 0 else 0 for v in avgs]
                    st.plotly_chart(radar_chart(df_clean, numeric_cols[:8], norm, title='Normalized Metric Comparison'), use_container_width=True)
                except Exception as e: st.error(f"Error: {e}")
        with tabs[6]:
            if len(numeric_cols) >= 2:
                sel = st.multiselect("Select columns:", numeric_cols, default=numeric_cols[:min(4,len(numeric_cols))], key='sm')
                if len(sel) >= 2:
                    try: st.plotly_chart(scatter_matrix_chart(df_clean, sel), use_container_width=True)
                    except Exception as e: st.error(f"Error: {e}")
            else: st.info("Need 2+ numeric columns.")

    # INSIGHTS
    st.markdown('<div class="section-header">🧠 AI-Generated Insights</div>', unsafe_allow_html=True)
    with st.spinner("Generating insights..."):
        insights = generate_insights(df_clean, cleaning_report)
        narrative = generate_summary_narrative(df_clean, kpis, insights)

    st.markdown(f"""<div style="background: linear-gradient(135deg, rgba(124,58,237,0.1), rgba(59,130,246,0.1));
        border: 1px solid rgba(124,58,237,0.2); border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
        <p style="color: #A78BFA; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1.5px; margin: 0 0 0.4rem;">Executive Summary</p>
        <p style="color: #E2E8F0; font-size: 0.9rem; line-height: 1.5; margin: 0;">{narrative}</p>
    </div>""", unsafe_allow_html=True)

    for ins in insights:
        st.markdown(f"""<div class="insight-card {ins['severity']}">
            <p class="insight-category">{ins['category']}</p>
            <p class="insight-text">{ins['icon']} {ins['insight']}</p>
        </div>""", unsafe_allow_html=True)

    # ANOMALY DETECTION
    st.markdown('<div class="section-header">🚨 Anomaly Detection</div>', unsafe_allow_html=True)

    is_ml = 'ML' in anomaly_method or 'Forest' in anomaly_method or 'Outlier' in anomaly_method
    ml_result = None
    anomaly_results = {}
    anom_summaries = []

    if is_ml and SKLEARN_AVAILABLE:
        ml_method = 'isolation_forest' if 'Forest' in anomaly_method else 'lof'
        contamination = max(0.01, min(0.3, 1.0 / anomaly_sensitivity))
        with st.spinner(f"Running {anomaly_method}..."):
            ml_result = detect_ml_anomalies(df_clean, method=ml_method, contamination=contamination)
        ml_sums = ml_anomaly_summary(ml_result)
        for s in ml_sums: st.markdown(s)
        if ml_result and ml_result.get('count', 0) > 0:
            with st.expander(f"📋 ML Anomalous Records ({ml_result['count']} found)"):
                disp = ml_result['anomalies_df'].copy()
                if '_row_index' in disp.columns: disp = disp.drop(columns=['_row_index'])
                st.dataframe(disp, use_container_width=True)
        # Also run statistical for column-level view
        stat_method = 'zscore'
        with st.spinner("Also running statistical detection..."):
            anomaly_results = detect_all_anomalies(df_clean, method=stat_method, threshold=anomaly_sensitivity)
            anom_summaries = anomaly_summary(anomaly_results)
    elif is_ml and not SKLEARN_AVAILABLE:
        st.warning("scikit-learn not installed. Falling back to Z-Score method.")
        with st.spinner("Scanning..."):
            anomaly_results = detect_all_anomalies(df_clean, method='zscore', threshold=anomaly_sensitivity)
            anom_summaries = anomaly_summary(anomaly_results)
    else:
        method = 'zscore' if anomaly_method == 'Z-Score' else 'iqr'
        with st.spinner("Scanning for anomalies..."):
            anomaly_results = detect_all_anomalies(df_clean, method=method, threshold=anomaly_sensitivity)
            anom_summaries = anomaly_summary(anomaly_results)

    for s in anom_summaries: st.markdown(s)

    if anomaly_results:
        acol = st.selectbox("Visualize anomalies for:", list(anomaly_results.keys()), key='avc')
        if acol:
            ar = anomaly_results[acol]
            if date_cols: x_ax = date_cols[0]
            else:
                df_clean = df_clean.copy()
                if '_row_index' not in df_clean.columns: df_clean['_row_index'] = range(len(df_clean))
                x_ax = '_row_index'
            try: st.plotly_chart(anomaly_chart(df_clean, x_ax, acol, ar['anomaly_mask']), use_container_width=True)
            except Exception as e: st.error(f"Chart error: {e}")
            if not ar['anomalies_df'].empty:
                with st.expander(f"📋 Anomalous Records ({ar['count']})"):
                    disp = ar['anomalies_df'].copy()
                    if '_row_index' in disp.columns: disp = disp.drop(columns=['_row_index'])
                    st.dataframe(disp, use_container_width=True)

    # STATISTICAL TESTS
    st.markdown('<div class="section-header">📐 Statistical Analysis</div>', unsafe_allow_html=True)
    stat_tabs = st.tabs(["Regression", "Group Comparison", "Normality", "Pivot Table"])

    with stat_tabs[0]:
        if len(numeric_cols) >= 2:
            rc1, rc2 = st.columns(2)
            with rc1: rx = st.selectbox("X (independent):", numeric_cols, key='rx')
            with rc2: ry = st.selectbox("Y (dependent):", [c for c in numeric_cols if c != rx] or numeric_cols, key='ry')
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
            elif reg: st.warning(reg.get('error','Regression failed'))
        else: st.info("Need 2+ numeric columns.")

    with stat_tabs[1]:
        if cat_cols and numeric_cols:
            gc1, gc2 = st.columns(2)
            with gc1: gcol = st.selectbox("Group by:", cat_cols, key='gcol')
            with gc2: gval = st.selectbox("Value:", numeric_cols, key='gval')
            comp = compare_groups(df_clean, gcol, gval)
            if comp is not None: st.dataframe(comp, use_container_width=True)
            anova = anova_test(df_clean, gval, gcol)
            if anova and 'error' not in anova:
                st.info(f"📊 ANOVA: {anova['interpretation']}")
        else: st.info("Need categorical + numeric columns.")

    with stat_tabs[2]:
        if numeric_cols:
            nc = st.selectbox("Test column:", numeric_cols, key='nc')
            nr = normality_test(df_clean[nc])
            if 'error' not in nr:
                st.metric(f"{nr['test']} Statistic", f"{nr['statistic']:.4f}")
                st.metric("P-value", f"{nr['p_value']:.4f}")
                if nr['is_normal']: st.success(f"✅ {nr['interpretation']}")
                else: st.warning(f"⚠️ {nr['interpretation']}")

    with stat_tabs[3]:
        if cat_cols and numeric_cols:
            pc1, pc2, pc3 = st.columns(3)
            with pc1: pidx = st.selectbox("Rows:", cat_cols, key='pidx')
            with pc2: pval = st.selectbox("Values:", numeric_cols, key='pval')
            with pc3: pagg = st.selectbox("Aggregation:", ['mean','sum','count','min','max'], key='pagg')
            pcols = st.selectbox("Columns (optional):", ['None']+[c for c in cat_cols if c != pidx], key='pcols')
            pivot = build_pivot_table(df_clean, pidx, pval, pagg, pcols if pcols != 'None' else None)
            if pivot is not None: st.dataframe(pivot, use_container_width=True)
        else: st.info("Need categorical + numeric columns for pivot.")

    # NLQ
    st.markdown('<div class="section-header">💬 Natural Language Query</div>', unsafe_allow_html=True)
    st.markdown("""<div style="background:#1E293B;border-radius:10px;padding:0.8rem;margin-bottom:0.8rem;">
        <p style="color:#94A3B8;font-size:0.8rem;margin:0;">
        <b style="color:#A78BFA;">Try:</b> "show top 5 by sales" · "average of profit" · "group by region and sum sales" · "compare sales between North and South" · "what correlates with profit?" · "filter where sales between 100 and 500"
        </p></div>""", unsafe_allow_html=True)

    uq = st.text_input("Ask about your data:", placeholder="e.g., group by category and sum sales", key='nlq')
    if uq:
        qr = process_nlq(df_clean, uq)
        if qr['success']:
            st.success(f"✅ {qr['explanation']}")
            if qr.get('dataframe') is not None: st.dataframe(qr['dataframe'], use_container_width=True)
            if qr.get('value') is not None: st.metric("Result", qr['value'])
        else: st.warning(f"⚠️ {qr['explanation']}")

    # EXPORT
    st.markdown('<div class="section-header">📄 Export Reports</div>', unsafe_allow_html=True)
    rc = st.columns(2)
    with rc[0]:
        st.markdown("""<div class="kpi-card"><p style="font-size:1.8rem;margin:0;">📊</p>
            <p class="kpi-label" style="margin:0.3rem 0;">Excel Report</p>
            <p style="color:#64748B;font-size:0.7rem;margin:0;">Multi-sheet workbook with data, stats, KPIs, anomalies & profile</p>
        </div>""", unsafe_allow_html=True)
        try:
            ebuf = ExcelReportGenerator.generate(df_clean, analysis, anomaly_results, kpis, col_profiles)
            sn = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
            st.download_button("📥 Download Excel Report", ebuf, f"ai_report_{sn}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, key='dl_xl')
        except Exception as e: st.error(f"Excel error: {e}")
    with rc[1]:
        st.markdown("""<div class="kpi-card"><p style="font-size:1.8rem;margin:0;">📄</p>
            <p class="kpi-label" style="margin:0.3rem 0;">PDF Report</p>
            <p style="color:#64748B;font-size:0.7rem;margin:0;">Professional report with TOC, KPIs, insights, anomalies & profile</p>
        </div>""", unsafe_allow_html=True)
        try:
            ml_info = ml_anomaly_summary(ml_result) if ml_result else None
            pbuf = PDFReportGenerator.generate(df_clean, kpis, insights, anom_summaries, narrative, ds_profile, ml_info)
            sn = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
            st.download_button("📥 Download PDF Report", pbuf, f"ai_report_{sn}.pdf", "application/pdf", use_container_width=True, key='dl_pdf')
        except Exception as e: st.error(f"PDF error: {e}")

    # Footer
    st.markdown("---")
    st.markdown("""<div style="text-align:center;padding:0.8rem;">
        <p style="color:#64748B;font-size:0.75rem;">🚀 <b>AI Excel Automation Engine v2.0</b> — Built by
        <a href="https://github.com/muh0210" style="color:#7C3AED;">Muhammad Rajput</a><br>
        <span style="font-size:0.65rem;">Powered by Streamlit, Pandas, Plotly, scikit-learn & Python</span></p>
    </div>""", unsafe_allow_html=True)

else:
    # Landing
    st.markdown("")
    fc = st.columns(3)
    features = [
        ("🧹", "Smart Cleaning", "Auto-removes duplicates, fills missing values, fixes data types"),
        ("🧠", "AI Insights", "Converts raw data into human-readable business narratives"),
        ("📈", "15+ Chart Types", "Line, bar, pie, heatmap, violin, radar, sunburst, pareto & more"),
        ("🚨", "ML Anomaly Detection", "Z-Score, IQR, Isolation Forest & Local Outlier Factor"),
        ("📐", "Statistical Tests", "Regression, ANOVA, normality tests, pivot tables"),
        ("📄", "Pro Reports", "PDF with TOC & Excel with formatting — one-click export"),
    ]
    for i, (icon, title, desc) in enumerate(features):
        with fc[i % 3]:
            st.markdown(f"""<div class="kpi-card" style="margin-bottom:0.8rem;text-align:left;padding:1.2rem;">
                <p style="font-size:1.8rem;margin:0;">{icon}</p>
                <p style="color:#E2E8F0;font-size:0.95rem;font-weight:700;margin:0.4rem 0 0.2rem;">{title}</p>
                <p style="color:#94A3B8;font-size:0.75rem;margin:0;line-height:1.3;">{desc}</p>
            </div>""", unsafe_allow_html=True)
    st.markdown("""<div style="text-align:center;margin-top:1.5rem;padding:1.5rem;background:linear-gradient(135deg, rgba(124,58,237,0.08), rgba(59,130,246,0.08));
        border-radius:16px;border:1px dashed rgba(124,58,237,0.3);">
        <p style="font-size:2.2rem;margin:0;">📂</p>
        <p style="color:#A78BFA;font-size:1rem;font-weight:600;margin:0.4rem 0;">Upload a file or try a demo dataset</p>
        <p style="color:#64748B;font-size:0.8rem;">Supports Excel (.xlsx, .xls) and CSV files up to 50MB</p>
    </div>""", unsafe_allow_html=True)
