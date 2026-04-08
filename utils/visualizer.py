"""
MODULE 4: VISUALIZATION ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Interactive Plotly charts — premium quality, auto-configured.
Supports: line, bar, scatter, pie, heatmap, box, histogram, anomaly,
          violin, radar, waterfall, funnel, sunburst, scatter_matrix,
          stacked_area, missing_heatmap.
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
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text=title, font=dict(size=18, color=COLORS['text']))
    )
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


def scatter_chart(df, x_col, y_col, title=None, color_col=None, size_col=None, trendline=None):
    """Interactive scatter plot for relationship analysis."""
    title = title or f'{y_col} vs {x_col}'
    fig = px.scatter(
        df, x=x_col, y=y_col, color=color_col, size=size_col,
        title=title, color_discrete_sequence=COLOR_SEQUENCE,
        opacity=0.75, trendline=trendline
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
        x=list(corr_matrix.columns),
        y=list(corr_matrix.columns),
        colorscale=[
            [0, '#EF4444'],
            [0.25, '#F97316'],
            [0.5, '#1E293B'],
            [0.75, '#3B82F6'],
            [1, '#7C3AED']
        ],
        zmin=-1, zmax=1,
        text=np.round(corr_matrix.values, 2),
        texttemplate='%{text}',
        textfont=dict(size=11, color=COLORS['text']),
        hoverongaps=False,
        colorbar=dict(
            title=dict(text='Correlation', font=dict(color=COLORS['text'])),
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
    """Line/scatter chart with anomalies highlighted."""
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
    if len(anomalies) > 0:
        fig.add_trace(go.Scatter(
            x=anomalies[x_col], y=anomalies[y_col],
            mode='markers',
            name='Anomaly',
            marker=dict(size=12, color=COLORS['danger'], symbol='x',
                        line=dict(width=2, color='#FECACA')),
        ))

    return _apply_layout(fig, title)


# ═══════════════════════════════════════════════════════════════════
#  NEW ADVANCED CHART TYPES
# ═══════════════════════════════════════════════════════════════════

def violin_chart(df, column, title=None, color_col=None):
    """Violin plot for enhanced distribution view."""
    title = title or f'Distribution of {column}'
    if color_col and color_col in df.columns:
        fig = px.violin(
            df, y=column, x=color_col, color=color_col,
            box=True, points='outliers',
            title=title, color_discrete_sequence=COLOR_SEQUENCE
        )
    else:
        fig = px.violin(
            df, y=column, box=True, points='outliers',
            title=title, color_discrete_sequence=[COLORS['primary']]
        )
    return _apply_layout(fig, title)


def radar_chart(df, categories, values, title='Radar Chart'):
    """Radar/Spider chart for multi-metric comparison."""
    fig = go.Figure()

    # Ensure the radar is closed
    cats = list(categories) + [categories[0]]
    vals = list(values) + [values[0]]

    fig.add_trace(go.Scatterpolar(
        r=vals,
        theta=cats,
        fill='toself',
        fillcolor=f'rgba(124, 58, 237, 0.25)',
        line=dict(color=COLORS['primary'], width=2),
        marker=dict(size=6, color=COLORS['primary']),
        name='Values'
    ))

    fig.update_layout(
        polar=dict(
            bgcolor=COLORS['bg_card'],
            radialaxis=dict(gridcolor=COLORS['grid'], tickfont=dict(color=COLORS['text_muted'])),
            angularaxis=dict(gridcolor=COLORS['grid'], tickfont=dict(color=COLORS['text'])),
        ),
        paper_bgcolor=COLORS['bg_dark'],
        font=dict(color=COLORS['text'], family='Inter, sans-serif'),
        title=dict(text=title, font=dict(size=18, color=COLORS['text'])),
        showlegend=False,
    )
    return fig


def waterfall_chart(categories, values, title='Waterfall Chart'):
    """Waterfall chart for cumulative impact analysis."""
    measures = ['relative'] * len(values)
    measures[-1] = 'total'  # Last bar is total

    fig = go.Figure(go.Waterfall(
        x=categories,
        y=values,
        measure=measures,
        connector=dict(line=dict(color=COLORS['grid'])),
        increasing=dict(marker=dict(color=COLORS['success'])),
        decreasing=dict(marker=dict(color=COLORS['danger'])),
        totals=dict(marker=dict(color=COLORS['primary'])),
        textposition='outside',
        text=[f'{v:+,.0f}' if m != 'total' else f'{v:,.0f}' for v, m in zip(values, measures)],
        textfont=dict(color=COLORS['text']),
    ))

    return _apply_layout(fig, title)


def funnel_chart(df, stage_col, value_col, title=None):
    """Funnel chart for pipeline/conversion analysis."""
    title = title or f'Funnel: {value_col} by {stage_col}'
    fig = px.funnel(
        df, x=value_col, y=stage_col,
        title=title, color_discrete_sequence=COLOR_SEQUENCE
    )
    return _apply_layout(fig, title)


def sunburst_chart(df, path_cols, value_col, title=None):
    """Sunburst chart for hierarchical data."""
    title = title or f'Hierarchy: {" → ".join(path_cols)}'
    try:
        fig = px.sunburst(
            df, path=path_cols, values=value_col,
            title=title, color_discrete_sequence=COLOR_SEQUENCE
        )
        fig.update_layout(
            paper_bgcolor=COLORS['bg_dark'],
            font=dict(color=COLORS['text'], family='Inter, sans-serif'),
            title=dict(text=title, font=dict(size=18, color=COLORS['text'])),
        )
        return fig
    except Exception:
        return None


def scatter_matrix_chart(df, columns, title='Scatter Matrix'):
    """Pairwise scatter matrix for multi-variable relationships."""
    if len(columns) > 5:
        columns = columns[:5]  # Limit for readability

    fig = px.scatter_matrix(
        df, dimensions=columns,
        title=title, color_discrete_sequence=[COLORS['primary']],
        opacity=0.5
    )
    fig.update_traces(
        diagonal_visible=True,
        marker=dict(size=3),
    )
    fig.update_layout(
        paper_bgcolor=COLORS['bg_dark'],
        plot_bgcolor=COLORS['bg_card'],
        font=dict(color=COLORS['text'], family='Inter, sans-serif', size=10),
        title=dict(text=title, font=dict(size=18, color=COLORS['text'])),
        height=600,
    )
    return fig


def stacked_area_chart(df, x_col, y_cols, title=None):
    """Stacked area chart for composition over time."""
    title = title or f'Composition over {x_col}'
    fig = go.Figure()

    for i, col in enumerate(y_cols):
        color = COLOR_SEQUENCE[i % len(COLOR_SEQUENCE)]
        fig.add_trace(go.Scatter(
            x=df[x_col], y=df[col],
            mode='lines',
            name=col,
            stackgroup='one',
            line=dict(width=0.5, color=color),
            fillcolor=color.replace(')', ', 0.6)').replace('rgb', 'rgba') if 'rgb' in color else color,
        ))

    return _apply_layout(fig, title)


def missing_values_heatmap(df, title='Missing Values Heatmap'):
    """Heatmap showing missing value patterns across columns."""
    missing = df.isnull().astype(int)

    # Sample rows if dataset is very large
    if len(missing) > 100:
        step = max(1, len(missing) // 100)
        missing = missing.iloc[::step]

    fig = go.Figure(data=go.Heatmap(
        z=missing.values.T,
        x=list(range(len(missing))),
        y=list(missing.columns),
        colorscale=[[0, COLORS['bg_card']], [1, COLORS['danger']]],
        zmin=0, zmax=1,
        showscale=True,
        colorbar=dict(
            title=dict(text='Missing', font=dict(color=COLORS['text'])),
            tickfont=dict(color=COLORS['text']),
            tickvals=[0, 1],
            ticktext=['Present', 'Missing'],
        ),
        hoverongaps=False,
    ))

    fig.update_layout(
        paper_bgcolor=COLORS['bg_dark'],
        plot_bgcolor=COLORS['bg_card'],
        font=dict(color=COLORS['text'], family='Inter, sans-serif'),
        title=dict(text=title, font=dict(size=18, color=COLORS['text'])),
        xaxis=dict(title='Row Index', gridcolor=COLORS['grid']),
        yaxis=dict(title='Columns', gridcolor=COLORS['grid']),
        margin=dict(l=120, r=40, t=60, b=40),
    )
    return fig


def regression_chart(df, x_col, y_col, reg_result, title=None):
    """Scatter plot with regression line overlay."""
    title = title or f'Regression: {y_col} vs {x_col}'

    fig = go.Figure()

    # Scatter points
    fig.add_trace(go.Scatter(
        x=df[x_col], y=df[y_col],
        mode='markers',
        name='Data Points',
        marker=dict(size=7, color=COLORS['primary'], opacity=0.6),
    ))

    # Regression line
    if reg_result and 'slope' in reg_result:
        x_range = np.linspace(df[x_col].min(), df[x_col].max(), 100)
        y_pred = reg_result['slope'] * x_range + reg_result['intercept']
        fig.add_trace(go.Scatter(
            x=x_range, y=y_pred,
            mode='lines',
            name=f'R² = {reg_result["r_squared"]:.3f}',
            line=dict(color=COLORS['danger'], width=2, dash='dash'),
        ))

    return _apply_layout(fig, title)


def pareto_chart(categories, values, title='Pareto Analysis'):
    """Pareto chart — bar + cumulative percentage line."""
    # Sort descending
    sorted_pairs = sorted(zip(categories, values), key=lambda x: x[1], reverse=True)
    cats = [p[0] for p in sorted_pairs]
    vals = [p[1] for p in sorted_pairs]
    total = sum(vals)
    cum_pct = [sum(vals[:i+1]) / total * 100 for i in range(len(vals))]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(x=cats, y=vals, name='Value',
               marker_color=COLORS['primary'], opacity=0.85),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=cats, y=cum_pct, name='Cumulative %',
                   line=dict(color=COLORS['danger'], width=2.5),
                   marker=dict(size=6)),
        secondary_y=True,
    )

    # 80% line
    fig.add_hline(y=80, line_dash="dash", line_color=COLORS['warning'],
                  annotation_text="80%", secondary_y=True)

    fig.update_layout(
        paper_bgcolor=COLORS['bg_dark'],
        plot_bgcolor=COLORS['bg_card'],
        font=dict(color=COLORS['text'], family='Inter, sans-serif'),
        title=dict(text=title, font=dict(size=18, color=COLORS['text'])),
        yaxis=dict(gridcolor=COLORS['grid'], title='Value'),
        yaxis2=dict(gridcolor=COLORS['grid'], title='Cumulative %', range=[0, 105]),
        xaxis=dict(gridcolor=COLORS['grid']),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
        hoverlabel=dict(bgcolor=COLORS['bg_card']),
    )
    return fig
