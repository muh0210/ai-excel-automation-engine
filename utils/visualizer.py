"""
MODULE 4: VISUALIZATION ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Interactive Plotly charts — premium quality, auto-configured.
Supports line, bar, scatter, pie, heatmap, and box plots.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


# ── Color Palette (Premium) ─────────────────────────────────────────
COLORS = {
    'primary': '#7C3AED',
    'secondary': '#3B82F6',
    'accent': '#06B6D4',
    'success': '#10B981',
    'warning': '#F59E0B',
    'danger': '#EF4444',
    'bg_dark': '#0F172A',
    'bg_card': '#1E293B',
    'text': '#E2E8F0',
    'text_muted': '#94A3B8',
    'grid': '#334155',
}

COLOR_SEQUENCE = [
    '#7C3AED', '#3B82F6', '#06B6D4', '#10B981', '#F59E0B',
    '#EF4444', '#EC4899', '#8B5CF6', '#14B8A6', '#F97316',
    '#6366F1', '#22D3EE', '#A78BFA', '#34D399', '#FBBF24',
]

CHART_LAYOUT = dict(
    paper_bgcolor=COLORS['bg_dark'],
    plot_bgcolor=COLORS['bg_card'],
    font=dict(color=COLORS['text'], family='Inter, sans-serif', size=13),
    margin=dict(l=40, r=40, t=60, b=40),
    xaxis=dict(gridcolor=COLORS['grid'], zerolinecolor=COLORS['grid']),
    yaxis=dict(gridcolor=COLORS['grid'], zerolinecolor=COLORS['grid']),
    legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(size=11)),
    hoverlabel=dict(bgcolor=COLORS['bg_card'], font_size=13),
)


def _apply_layout(fig, title=''):
    """Apply the premium layout to a figure."""
    fig.update_layout(**CHART_LAYOUT, title=dict(text=title, font=dict(size=18, color=COLORS['text'])))
    return fig


def line_chart(df, x_col, y_col, title=None, color_col=None):
    """Interactive line chart for time-series / trends."""
    title = title or f'{y_col} over {x_col}'
    fig = px.line(
        df, x=x_col, y=y_col, color=color_col,
        title=title, color_discrete_sequence=COLOR_SEQUENCE,
        markers=True
    )
    fig.update_traces(line=dict(width=2.5))
    return _apply_layout(fig, title)


def bar_chart(df, x_col, y_col, title=None, color_col=None, horizontal=False):
    """Interactive bar chart for comparisons."""
    title = title or f'{y_col} by {x_col}'
    if horizontal:
        fig = px.bar(
            df, y=x_col, x=y_col, color=color_col, orientation='h',
            title=title, color_discrete_sequence=COLOR_SEQUENCE
        )
    else:
        fig = px.bar(
            df, x=x_col, y=y_col, color=color_col,
            title=title, color_discrete_sequence=COLOR_SEQUENCE
        )
    fig.update_traces(marker_line_width=0, opacity=0.9)
    return _apply_layout(fig, title)


def scatter_chart(df, x_col, y_col, title=None, color_col=None, size_col=None):
    """Interactive scatter plot for relationship analysis."""
    title = title or f'{y_col} vs {x_col}'
    fig = px.scatter(
        df, x=x_col, y=y_col, color=color_col, size=size_col,
        title=title, color_discrete_sequence=COLOR_SEQUENCE,
        opacity=0.75
    )
    return _apply_layout(fig, title)


def pie_chart(df, names_col, values_col, title=None):
    """Donut chart for category distribution."""
    title = title or f'Distribution of {values_col} by {names_col}'
    fig = px.pie(
        df, names=names_col, values=values_col,
        title=title, color_discrete_sequence=COLOR_SEQUENCE,
        hole=0.45
    )
    fig.update_traces(
        textinfo='percent+label',
        textfont_size=12,
        marker=dict(line=dict(color=COLORS['bg_dark'], width=2))
    )
    return _apply_layout(fig, title)


def heatmap_chart(corr_matrix, title='Correlation Heatmap'):
    """Heatmap for correlation matrix."""
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale=[
            [0, '#EF4444'],
            [0.25, '#F97316'],
            [0.5, '#1E293B'],
            [0.75, '#3B82F6'],
            [1, '#7C3AED']
        ],
        zmin=-1, zmax=1,
        text=corr_matrix.values.round(2),
        texttemplate='%{text}',
        textfont=dict(size=11, color=COLORS['text']),
        hoverongaps=False,
        colorbar=dict(
            title='Correlation',
            titlefont=dict(color=COLORS['text']),
            tickfont=dict(color=COLORS['text'])
        )
    ))
    return _apply_layout(fig, title)


def box_chart(df, column, title=None, color_col=None):
    """Box plot for distribution & outlier visualization."""
    title = title or f'Distribution of {column}'
    if color_col and color_col in df.columns:
        fig = px.box(
            df, y=column, x=color_col,
            title=title, color=color_col,
            color_discrete_sequence=COLOR_SEQUENCE
        )
    else:
        fig = px.box(
            df, y=column, title=title,
            color_discrete_sequence=COLOR_SEQUENCE
        )
    return _apply_layout(fig, title)


def histogram_chart(df, column, title=None, nbins=30):
    """Histogram for value distribution."""
    title = title or f'Distribution of {column}'
    fig = px.histogram(
        df, x=column, title=title, nbins=nbins,
        color_discrete_sequence=[COLORS['primary']],
        opacity=0.85
    )
    fig.update_traces(marker_line_width=1, marker_line_color=COLORS['bg_dark'])
    return _apply_layout(fig, title)


def anomaly_chart(df, x_col, y_col, anomaly_mask, title=None):
    """
    Line/scatter chart with anomalies highlighted.

    Args:
        df: DataFrame
        x_col: x-axis column
        y_col: y-axis column
        anomaly_mask: boolean Series — True for anomaly rows
        title: chart title
    """
    title = title or f'Anomaly Detection — {y_col}'

    fig = go.Figure()

    # Normal points
    normal = df[~anomaly_mask]
    fig.add_trace(go.Scatter(
        x=normal[x_col], y=normal[y_col],
        mode='lines+markers',
        name='Normal',
        line=dict(color=COLORS['primary'], width=2),
        marker=dict(size=5, color=COLORS['primary']),
    ))

    # Anomaly points
    anomalies = df[anomaly_mask]
    fig.add_trace(go.Scatter(
        x=anomalies[x_col], y=anomalies[y_col],
        mode='markers',
        name='⚠️ Anomaly',
        marker=dict(size=12, color=COLORS['danger'], symbol='x',
                     line=dict(width=2, color='#FECACA')),
    ))

    return _apply_layout(fig, title)


def kpi_sparkline(values, title='', color=None):
    """Mini sparkline chart for KPI cards."""
    color = color or COLORS['primary']
    fig = go.Figure(go.Scatter(
        y=values, mode='lines',
        fill='tozeroy',
        line=dict(color=color, width=2),
        fillcolor=f'rgba({int(color[1:3], 16)},{int(color[3:5], 16)},{int(color[5:7], 16)},0.15)'
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=60, width=150,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig
