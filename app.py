"""
🚀 AI EXCEL AUTOMATION ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Premium Streamlit Application
Upload → Clean → Analyze → Explain → Detect Anomalies → Visualize → Export

Author: Muhammad Rajput (muh0210)
Contact: muhrajpoot1921@gmail.com
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO

# ── Local Module Imports ─────────────────────────────────────────────
from utils.loader import load_file, load_specific_sheet, get_file_preview
from utils.cleaner import clean_data
from utils.analyzer import (
    basic_analysis, correlation_analysis, auto_group_analysis,
    trend_analysis, top_bottom_n, compute_kpis
)
from utils.visualizer import (
    line_chart, bar_chart, scatter_chart, pie_chart,
    heatmap_chart, box_chart, histogram_chart, anomaly_chart,
    COLORS
)
from utils.insights import generate_insights, generate_summary_narrative
from utils.anomaly import (
    detect_anomalies_zscore, detect_anomalies_iqr,
    detect_all_anomalies, anomaly_summary
)
from utils.reporter import ExcelReportGenerator, PDFReportGenerator


# ══════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS (must be defined before UI code)
# ══════════════════════════════════════════════════════════════════════
def _find_column(df, name):
    """Fuzzy-match a column name from user query."""
    name_lower = name.lower().strip()
    for col in df.columns:
        if col.lower() == name_lower:
            return col
    for col in df.columns:
        if name_lower in col.lower() or col.lower() in name_lower:
            return col
    return None


def process_natural_language_query(df, query):
    """Process a natural language query against the dataframe."""
    query_lower = query.lower().strip()
    try:
        if 'show columns' in query_lower or 'list columns' in query_lower:
            cols_df = pd.DataFrame({
                'Column': df.columns,
                'Type': [str(dt) for dt in df.dtypes],
                'Non-Null Count': [int(df[c].notna().sum()) for c in df.columns]
            })
            return {'success': True, 'explanation': f'Dataset has {len(df.columns)} columns:', 'dataframe': cols_df, 'value': None}

        match = re.search(r'describe\s+(\w+)', query_lower)
        if match:
            col = _find_column(df, match.group(1))
            if col:
                return {'success': True, 'explanation': f'Description of "{col}":', 'dataframe': df[col].describe().reset_index(), 'value': None}

        match = re.search(r'(top|bottom|highest|lowest|best|worst)\s+(\d+)\s+(?:by|in|of)?\s*(\w+)', query_lower)
        if match:
            direction = match.group(1)
            n = int(match.group(2))
            col = _find_column(df, match.group(3))
            if col and pd.api.types.is_numeric_dtype(df[col]):
                ascending = direction in ('bottom', 'lowest', 'worst')
                result_df = df.sort_values(by=col, ascending=ascending).head(n)
                label = 'Bottom' if ascending else 'Top'
                return {'success': True, 'explanation': f'{label} {n} records by "{col}":', 'dataframe': result_df, 'value': None}

        match = re.search(r'(average|avg|mean|sum|total|min|minimum|max|maximum|median|count)\s+(?:of\s+)?(\w+)', query_lower)
        if match:
            func_str = match.group(1)
            col = _find_column(df, match.group(2))
            if col and pd.api.types.is_numeric_dtype(df[col]):
                func_map = {'average': 'mean', 'avg': 'mean', 'mean': 'mean', 'sum': 'sum', 'total': 'sum',
                            'min': 'min', 'minimum': 'min', 'max': 'max', 'maximum': 'max', 'median': 'median', 'count': 'count'}
                func = func_map.get(func_str, 'mean')
                value = getattr(df[col], func)()
                return {'success': True, 'explanation': f'{func.capitalize()} of "{col}":', 'dataframe': None, 'value': f'{value:,.2f}'}

        match = re.search(r'filter\s+(?:where\s+)?(\w+)\s+(?:is|equals?|==|contains?)\s+(.+)', query_lower)
        if match:
            col = _find_column(df, match.group(1))
            value = match.group(2).strip().strip('"\'')
            if col:
                if pd.api.types.is_numeric_dtype(df[col]):
                    try:
                        num_val = float(value)
                        filtered = df[df[col] == num_val]
                    except ValueError:
                        filtered = df[df[col].astype(str).str.contains(value, case=False, na=False)]
                else:
                    filtered = df[df[col].astype(str).str.contains(value, case=False, na=False)]
                return {'success': True, 'explanation': f'Filtered {len(filtered)} rows where "{col}" matches "{value}":', 'dataframe': filtered, 'value': None}

        match = re.search(r'sort\s+(?:by\s+)?(\w+)\s*(asc|ascending|desc|descending)?', query_lower)
        if match:
            col = _find_column(df, match.group(1))
            direction = match.group(2) or 'desc'
            ascending = direction.startswith('asc')
            if col:
                sorted_df = df.sort_values(by=col, ascending=ascending)
                return {'success': True, 'explanation': f'Sorted by "{col}" {"ascending" if ascending else "descending"}:', 'dataframe': sorted_df, 'value': None}

        match = re.search(r'(?:count\s+)?unique\s+(\w+)', query_lower)
        if match:
            col = _find_column(df, match.group(1))
            if col:
                unique_count = df[col].nunique()
                value_counts = df[col].value_counts().reset_index()
                value_counts.columns = [col, 'Count']
                return {'success': True, 'explanation': f'{unique_count} unique values in "{col}":', 'dataframe': value_counts, 'value': None}

        return {'success': False, 'explanation': 'Could not understand the query. Try: "show top 5 by sales", "average of profit", "filter where region is North", or "show columns".', 'dataframe': None, 'value': None}
    except Exception as e:
        return {'success': False, 'explanation': f'Error processing query: {str(e)}', 'dataframe': None, 'value': None}


# ══════════════════════════════════════════════════════════════════════
#  PAGE CONFIGURATION
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AI Excel Automation Engine",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 50%, #06B6D4 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(124, 58, 237, 0.3);
    }
    .main-header h1 {
        color: white; font-size: 2.2rem; font-weight: 800; margin: 0; letter-spacing: -0.5px;
    }
    .main-header p {
        color: rgba(255,255,255,0.85); font-size: 1rem; margin: 0.5rem 0 0 0; font-weight: 300;
    }

    .section-header {
        background: linear-gradient(90deg, rgba(124,58,237,0.15), transparent);
        border-left: 4px solid #7C3AED;
        padding: 0.75rem 1.25rem;
        border-radius: 0 8px 8px 0;
        margin: 1.5rem 0 1rem 0;
        font-size: 1.25rem;
        font-weight: 700;
        color: #E2E8F0;
    }

    .kpi-card {
        background: linear-gradient(145deg, #1E293B, #0F172A);
        border: 1px solid rgba(124,58,237,0.25);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .kpi-card:hover {
        border-color: #7C3AED;
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(124,58,237,0.2);
    }
    .kpi-value { font-size: 1.75rem; font-weight: 800; color: #7C3AED; margin: 0; }
    .kpi-label { font-size: 0.8rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; margin: 0.25rem 0 0 0; }
    .kpi-delta { font-size: 0.85rem; font-weight: 600; margin-top: 0.25rem; }
    .kpi-delta.positive { color: #10B981; }
    .kpi-delta.negative { color: #EF4444; }

    .insight-card {
        background: #1E293B; border-radius: 10px; padding: 1rem 1.25rem;
        margin-bottom: 0.75rem; border-left: 4px solid #3B82F6; transition: all 0.2s ease;
    }
    .insight-card:hover { background: #263548; }
    .insight-card.positive { border-left-color: #10B981; }
    .insight-card.warning { border-left-color: #F59E0B; }
    .insight-card.critical { border-left-color: #EF4444; }
    .insight-card.info { border-left-color: #3B82F6; }
    .insight-category { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1.5px; color: #94A3B8; margin-bottom: 0.25rem; }
    .insight-text { color: #E2E8F0; font-size: 0.95rem; line-height: 1.5; }

    .badge {
        display: inline-block; padding: 0.25rem 0.75rem; border-radius: 20px;
        font-size: 0.75rem; font-weight: 600; margin-right: 0.5rem; margin-bottom: 0.35rem;
    }
    .badge-purple { background: rgba(124,58,237,0.2); color: #A78BFA; }
    .badge-blue { background: rgba(59,130,246,0.2); color: #60A5FA; }
    .badge-green { background: rgba(16,185,129,0.2); color: #34D399; }
    .badge-yellow { background: rgba(245,158,11,0.2); color: #FBBF24; }
    .badge-red { background: rgba(239,68,68,0.2); color: #F87171; }

    .empty-state {
        background: #1E293B; border-radius: 12px; padding: 2rem; text-align: center;
        border: 1px dashed rgba(124,58,237,0.3);
    }
    .empty-state p.icon { font-size: 2rem; margin: 0; }
    .empty-state p.msg { color: #94A3B8; font-size: 0.9rem; margin: 0.5rem 0 0; }

    [data-testid="stFileUploader"] { border: 2px dashed rgba(124,58,237,0.4); border-radius: 12px; padding: 1rem; }
    [data-testid="stFileUploader"]:hover { border-color: #7C3AED; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0F172A, #1E293B) !important; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background: transparent; border-radius: 8px; padding: 8px 16px; color: #94A3B8; }
    .stTabs [aria-selected="true"] { background: rgba(124,58,237,0.2) !important; color: #A78BFA !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0;">
        <span style="font-size: 3rem;">🚀</span>
        <h2 style="margin: 0.5rem 0 0; font-weight: 800; background: linear-gradient(90deg, #7C3AED, #3B82F6);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        AI Excel Engine</h2>
        <p style="color: #94A3B8; font-size: 0.85rem;">Premium Data Automation</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ⚙️ Settings")

    anomaly_method = st.selectbox(
        "Anomaly Detection Method",
        ['Z-Score', 'IQR'],
        help="Z-Score: Uses standard deviations. IQR: Uses interquartile range."
    )

    anomaly_sensitivity = st.slider(
        "Anomaly Sensitivity",
        min_value=1.0, max_value=4.0, value=2.0, step=0.5,
        help="Lower = more sensitive (catches more). Higher = stricter."
    )

    show_raw_data = st.checkbox("Show Raw Data", value=False)

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; padding: 0.5rem;">
        <p style="color: #64748B; font-size: 0.75rem;">
            Built by <b>Muhammad Rajput</b><br>
            <a href="https://github.com/muh0210" style="color: #7C3AED;">github.com/muh0210</a>
        </p>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="main-header">
    <h1>🚀 AI Excel Automation Engine</h1>
    <p>Upload → Clean → Analyze → Explain → Detect Anomalies → Visualize → Export</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  FILE UPLOAD
# ══════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">📥 Upload Your Data</div>', unsafe_allow_html=True)

col_upload, col_info = st.columns([2, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "Drop your Excel or CSV file here",
        type=['xlsx', 'xls', 'csv'],
        help="Supports .xlsx, .xls, and .csv files up to 50MB"
    )

with col_info:
    st.markdown("""
    <div style="background: #1E293B; border-radius: 10px; padding: 1rem; margin-top: 0.5rem;">
        <p style="color: #94A3B8; font-size: 0.85rem; margin:0;">
            <b style="color: #A78BFA;">Supported Formats:</b><br>
            📊 Excel (.xlsx, .xls)<br>
            📄 CSV (.csv)<br><br>
            <b style="color: #A78BFA;">Features:</b><br>
            ✅ Auto data cleaning<br>
            ✅ Smart insights<br>
            ✅ Interactive charts<br>
            ✅ Anomaly detection<br>
            ✅ Report export
        </p>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  MAIN PROCESSING PIPELINE
# ══════════════════════════════════════════════════════════════════════
if uploaded_file is not None:

    # ── STEP 1: Load Data ────────────────────────────────────────────
    with st.spinner("📥 Loading your data..."):
        try:
            result = load_file(uploaded_file)
            df_raw = result['dataframe']
        except Exception as e:
            st.error(f"❌ Failed to load file: {str(e)}")
            st.stop()

    # Handle multi-sheet Excel files
    if result.get('sheet_names') and len(result['sheet_names']) > 1:
        selected_sheet = st.selectbox(
            "📑 Multiple sheets detected — select one:",
            result['sheet_names']
        )
        if selected_sheet != result['sheet_names'][0]:
            uploaded_file.seek(0)
            df_raw = load_specific_sheet(uploaded_file, selected_sheet)

    # File info badges
    file_name = result.get('file_name', 'data')
    st.markdown(f"""
    <div style="margin: 1rem 0;">
        <span class="badge badge-purple">📁 {file_name}</span>
        <span class="badge badge-blue">📐 {df_raw.shape[0]} rows × {df_raw.shape[1]} cols</span>
        <span class="badge badge-green">💾 {result.get('file_size_kb', '?')} KB</span>
    </div>
    """, unsafe_allow_html=True)

    # Show raw data (optional)
    if show_raw_data:
        with st.expander("📋 Raw Data Preview", expanded=False):
            st.dataframe(df_raw, use_container_width=True, height=300)

    # ── STEP 2: Clean Data ───────────────────────────────────────────
    st.markdown('<div class="section-header">🧹 Data Cleaning Engine</div>', unsafe_allow_html=True)

    with st.spinner("🧹 Cleaning your data..."):
        df_clean, cleaning_report = clean_data(df_raw)

    # Cleaning report KPI cards
    cr1, cr2, cr3, cr4 = st.columns(4)
    with cr1:
        st.markdown(f'<div class="kpi-card"><p class="kpi-value">{cleaning_report["duplicates_removed"]}</p><p class="kpi-label">Duplicates Removed</p></div>', unsafe_allow_html=True)
    with cr2:
        total_missing = sum(cleaning_report.get('missing_values_before', {}).values())
        st.markdown(f'<div class="kpi-card"><p class="kpi-value">{total_missing}</p><p class="kpi-label">Missing Values Fixed</p></div>', unsafe_allow_html=True)
    with cr3:
        type_changes = len(cleaning_report.get('type_conversions', {}))
        st.markdown(f'<div class="kpi-card"><p class="kpi-value">{type_changes}</p><p class="kpi-label">Type Conversions</p></div>', unsafe_allow_html=True)
    with cr4:
        completeness = cleaning_report.get('data_completeness', 100)
        st.markdown(f'<div class="kpi-card"><p class="kpi-value">{completeness}%</p><p class="kpi-label">Data Completeness</p></div>', unsafe_allow_html=True)

    # Detailed cleaning report expander
    with st.expander("🔍 Detailed Cleaning Report", expanded=False):
        if cleaning_report.get('columns_renamed'):
            st.markdown("**Column Renames:**")
            for old, new in cleaning_report['columns_renamed'].items():
                st.markdown(f"  `{old}` → `{new}`")
        if cleaning_report.get('missing_value_actions'):
            st.markdown("**Missing Value Actions:**")
            for col, action in cleaning_report['missing_value_actions'].items():
                st.markdown(f"  - `{col}`: {action}")
        if cleaning_report.get('type_conversions'):
            st.markdown("**Type Conversions:**")
            for col, change in cleaning_report['type_conversions'].items():
                st.markdown(f"  - `{col}`: {change}")
        st.markdown(f"**Shape:** {cleaning_report['original_shape']} → {cleaning_report['cleaned_shape']}")

    with st.expander("📋 Cleaned Data Preview", expanded=False):
        st.dataframe(df_clean, use_container_width=True, height=300)

    # ── Detect column types for later use ────────────────────────────
    numeric_cols = list(df_clean.select_dtypes(include='number').columns)
    cat_cols = list(df_clean.select_dtypes(include=['object', 'category']).columns)
    date_cols = list(df_clean.select_dtypes(include='datetime').columns)

    # ── STEP 3: KPI Dashboard ───────────────────────────────────────
    st.markdown('<div class="section-header">📊 KPI Dashboard</div>', unsafe_allow_html=True)

    kpis = compute_kpis(df_clean)
    analysis = basic_analysis(df_clean)

    if kpis:
        kpi_names = list(kpis.keys())[:4]
        cols = st.columns(len(kpi_names))
        for i, col_name in enumerate(kpi_names):
            with cols[i]:
                k = kpis[col_name]
                delta_class = 'positive' if k['growth_pct'] >= 0 else 'negative'
                delta_icon = '▲' if k['growth_pct'] >= 0 else '▼'
                st.markdown(f"""
                <div class="kpi-card">
                    <p class="kpi-value">{k['total']:,.0f}</p>
                    <p class="kpi-label">Total {col_name}</p>
                    <p class="kpi-delta {delta_class}">{delta_icon} {k['growth_pct']:+.1f}% growth</p>
                </div>
                """, unsafe_allow_html=True)

        # Averages row
        avg_cols = st.columns(len(kpi_names))
        for i, col_name in enumerate(kpi_names):
            with avg_cols[i]:
                k = kpis[col_name]
                st.markdown(f"""
                <div class="kpi-card">
                    <p class="kpi-value">{k['average']:,.2f}</p>
                    <p class="kpi-label">Avg {col_name}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state"><p class="icon">📭</p><p class="msg">No numeric columns found for KPI calculations.<br>Upload a dataset with numeric data to see metrics here.</p></div>', unsafe_allow_html=True)

    # ── STEP 4: Interactive Charts ───────────────────────────────────
    st.markdown('<div class="section-header">📈 Interactive Visualizations</div>', unsafe_allow_html=True)

    if not numeric_cols:
        st.markdown('<div class="empty-state"><p class="icon">📊</p><p class="msg">No numeric columns available for visualization.<br>Upload a dataset with numeric data to see interactive charts.</p></div>', unsafe_allow_html=True)
    else:
        chart_tabs = st.tabs(["📊 Distribution", "📈 Trends", "🔗 Correlation", "🍩 Categories", "📦 Box Plot"])

        with chart_tabs[0]:
            hist_col = st.selectbox("Select column:", numeric_cols, key='hist_col')
            try:
                fig = histogram_chart(df_clean, hist_col)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Chart error: {e}")

        with chart_tabs[1]:
            if date_cols:
                tc1, tc2 = st.columns(2)
                with tc1:
                    trend_date = st.selectbox("Date column:", date_cols, key='trend_date')
                with tc2:
                    trend_val = st.selectbox("Value column:", numeric_cols, key='trend_val')
                try:
                    trend_result = trend_analysis(df_clean, trend_date, trend_val)
                    if trend_result:
                        st.markdown(f"""
                        <div style="background: #1E293B; border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
                            <span class="badge badge-purple">Trend: {trend_result['direction']}</span>
                            <span class="badge badge-blue">Change: {trend_result['change_pct']:+.1f}%</span>
                            <span class="badge badge-green">Points: {trend_result['data_points']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        fig = line_chart(trend_result['time_series_df'], trend_date, trend_val)
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Trend chart error: {e}")
            else:
                idx_val = st.selectbox("Value column:", numeric_cols, key='idx_trend_val')
                try:
                    df_plot = df_clean[[idx_val]].reset_index()
                    fig = line_chart(df_plot, 'index', idx_val, title=f'{idx_val} Over Row Index')
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Trend chart error: {e}")

        with chart_tabs[2]:
            try:
                corr = correlation_analysis(df_clean)
                if corr is not None and len(corr) > 1:
                    fig = heatmap_chart(corr)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Need at least 2 numeric columns for correlation analysis.")
            except Exception as e:
                st.error(f"Heatmap error: {e}")

        with chart_tabs[3]:
            if cat_cols:
                cc1, cc2 = st.columns(2)
                with cc1:
                    cat_col = st.selectbox("Category column:", cat_cols, key='cat_col')
                with cc2:
                    val_col = st.selectbox("Value column:", numeric_cols, key='cat_val')
                try:
                    grouped = df_clean.groupby(cat_col)[val_col].sum().reset_index()
                    grouped.columns = [cat_col, val_col]
                    c1, c2 = st.columns(2)
                    with c1:
                        fig = pie_chart(grouped, cat_col, val_col)
                        st.plotly_chart(fig, use_container_width=True)
                    with c2:
                        fig = bar_chart(grouped, cat_col, val_col)
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Category chart error: {e}")
            else:
                st.info("No categorical columns found for category analysis.")

        with chart_tabs[4]:
            bc1, bc2 = st.columns(2)
            with bc1:
                box_col = st.selectbox("Numeric column:", numeric_cols, key='box_col')
            with bc2:
                box_cat = st.selectbox("Group by (optional):", ['None'] + cat_cols, key='box_cat')
            try:
                color_by = box_cat if box_cat != 'None' else None
                fig = box_chart(df_clean, box_col, color_col=color_by)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Box plot error: {e}")

    # ── STEP 5: AI Insights ──────────────────────────────────────────
    st.markdown('<div class="section-header">🧠 AI-Generated Insights</div>', unsafe_allow_html=True)

    with st.spinner("🧠 Generating AI insights..."):
        insights = generate_insights(df_clean, cleaning_report)
        narrative = generate_summary_narrative(df_clean, kpis, insights)

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(124,58,237,0.1), rgba(59,130,246,0.1));
                border: 1px solid rgba(124,58,237,0.2); border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem;">
        <p style="color: #A78BFA; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; margin: 0 0 0.5rem;">
            Executive Summary
        </p>
        <p style="color: #E2E8F0; font-size: 0.95rem; line-height: 1.6; margin: 0;">{narrative}</p>
    </div>
    """, unsafe_allow_html=True)

    for insight in insights:
        st.markdown(f"""
        <div class="insight-card {insight['severity']}">
            <p class="insight-category">{insight['category']}</p>
            <p class="insight-text">{insight['icon']} {insight['insight']}</p>
        </div>
        """, unsafe_allow_html=True)

    # ── STEP 6: Anomaly Detection ────────────────────────────────────
    st.markdown('<div class="section-header">🚨 Anomaly Detection</div>', unsafe_allow_html=True)

    method = 'zscore' if anomaly_method == 'Z-Score' else 'iqr'
    with st.spinner("🚨 Scanning for anomalies..."):
        anomaly_results = detect_all_anomalies(df_clean, method=method, threshold=anomaly_sensitivity)
        anom_summaries = anomaly_summary(anomaly_results)

    for summary_line in anom_summaries:
        st.markdown(summary_line)

    if anomaly_results:
        anomaly_col = st.selectbox(
            "Visualize anomalies for:",
            list(anomaly_results.keys()),
            key='anom_viz_col'
        )
        if anomaly_col:
            anom_result = anomaly_results[anomaly_col]
            if date_cols:
                x_axis = date_cols[0]
            else:
                df_clean = df_clean.copy()
                df_clean['_row_index'] = range(len(df_clean))
                x_axis = '_row_index'
            try:
                fig = anomaly_chart(df_clean, x_axis, anomaly_col, anom_result['anomaly_mask'])
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Anomaly chart error: {e}")

            if not anom_result['anomalies_df'].empty:
                with st.expander(f"📋 Anomalous Records ({anom_result['count']} found)"):
                    display_df = anom_result['anomalies_df'].copy()
                    if '_row_index' in display_df.columns:
                        display_df = display_df.drop(columns=['_row_index'])
                    st.dataframe(display_df, use_container_width=True)

    # ── STEP 7: Natural Language Query ───────────────────────────────
    st.markdown('<div class="section-header">💬 Natural Language Query</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="background: #1E293B; border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
        <p style="color: #94A3B8; font-size: 0.85rem; margin:0;">
            <b style="color: #A78BFA;">Try queries like:</b><br>
            • "show top 5 by sales" &nbsp; • "average of profit" &nbsp; • "filter where region is North"<br>
            • "show columns" &nbsp; • "count unique category" &nbsp; • "sort by quantity descending"
        </p>
    </div>
    """, unsafe_allow_html=True)

    user_query = st.text_input(
        "Ask a question about your data:",
        placeholder="e.g., show top 10 by sales",
        key='nlq_input'
    )

    if user_query:
        query_result = process_natural_language_query(df_clean, user_query)
        if query_result['success']:
            st.success(f"✅ {query_result['explanation']}")
            if query_result.get('dataframe') is not None:
                st.dataframe(query_result['dataframe'], use_container_width=True)
            if query_result.get('value') is not None:
                st.metric("Result", query_result['value'])
        else:
            st.warning(f"⚠️ {query_result['explanation']}")

    # ── STEP 8: Export Reports ───────────────────────────────────────
    st.markdown('<div class="section-header">📄 Export Reports</div>', unsafe_allow_html=True)

    report_cols = st.columns(2)

    with report_cols[0]:
        st.markdown("""
        <div class="kpi-card">
            <p style="font-size: 2rem; margin: 0;">📊</p>
            <p class="kpi-label" style="margin: 0.5rem 0;">Excel Report</p>
            <p style="color: #64748B; font-size: 0.75rem; margin: 0;">
                Multi-sheet workbook with cleaned data, stats, KPIs & anomalies
            </p>
        </div>
        """, unsafe_allow_html=True)

        try:
            excel_buffer = ExcelReportGenerator.generate(
                df_clean, analysis, anomaly_results, kpis
            )
            safe_name = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
            st.download_button(
                label="📥 Download Excel Report",
                data=excel_buffer,
                file_name=f"ai_report_{safe_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key='dl_excel_btn'
            )
        except Exception as e:
            st.error(f"Excel report error: {e}")

    with report_cols[1]:
        st.markdown("""
        <div class="kpi-card">
            <p style="font-size: 2rem; margin: 0;">📄</p>
            <p class="kpi-label" style="margin: 0.5rem 0;">PDF Report</p>
            <p style="color: #64748B; font-size: 0.75rem; margin: 0;">
                Professional report with KPIs, insights, anomalies & data preview
            </p>
        </div>
        """, unsafe_allow_html=True)

        try:
            pdf_buffer = PDFReportGenerator.generate(
                df_clean, kpis, insights, anom_summaries, narrative
            )
            safe_name = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_buffer,
                file_name=f"ai_report_{safe_name}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key='dl_pdf_btn'
            )
        except Exception as e:
            st.error(f"PDF report error: {e}")

    # ── Footer ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <p style="color: #64748B; font-size: 0.8rem;">
            🚀 <b>AI Excel Automation Engine</b> — Built by
            <a href="https://github.com/muh0210" style="color: #7C3AED;">Muhammad Rajput</a>
            <br>
            <span style="font-size: 0.7rem;">Powered by Streamlit, Pandas, Plotly & Python</span>
        </p>
    </div>
    """, unsafe_allow_html=True)


else:
    # ── Landing State (No file uploaded) ─────────────────────────────
    st.markdown("")

    feature_cols = st.columns(3)
    features = [
        ("🧹", "Smart Cleaning", "Auto-removes duplicates, fills missing values, fixes data types"),
        ("🧠", "AI Insights", "Converts raw data into human-readable business narratives"),
        ("📈", "Rich Visualizations", "Interactive Plotly charts — line, bar, pie, heatmap & more"),
        ("🚨", "Anomaly Detection", "Z-Score & IQR methods to flag unusual data patterns"),
        ("💬", "Natural Language", "Query your data in plain English — no code needed"),
        ("📄", "Auto Reports", "Download professional PDF & Excel reports instantly"),
    ]

    for i, (icon, title, desc) in enumerate(features):
        with feature_cols[i % 3]:
            st.markdown(f"""
            <div class="kpi-card" style="margin-bottom: 1rem; text-align: left; padding: 1.5rem;">
                <p style="font-size: 2rem; margin: 0;">{icon}</p>
                <p style="color: #E2E8F0; font-size: 1rem; font-weight: 700; margin: 0.5rem 0 0.25rem;">{title}</p>
                <p style="color: #94A3B8; font-size: 0.8rem; margin: 0; line-height: 1.4;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; padding: 2rem; background: linear-gradient(135deg, rgba(124,58,237,0.08), rgba(59,130,246,0.08));
                border-radius: 16px; border: 1px dashed rgba(124,58,237,0.3);">
        <p style="font-size: 2.5rem; margin: 0;">📂</p>
        <p style="color: #A78BFA; font-size: 1.1rem; font-weight: 600; margin: 0.5rem 0;">Upload a file to get started</p>
        <p style="color: #64748B; font-size: 0.85rem;">Drop an Excel or CSV file in the upload area above</p>
    </div>
    """, unsafe_allow_html=True)
