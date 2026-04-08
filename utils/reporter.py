"""
MODULE 7: AUTO REPORT GENERATOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generates downloadable PDF and Excel reports.
  - PDF: Title page, table of contents, KPIs, insights, anomaly table, data preview
  - Excel: Multi-sheet workbook with conditional formatting (cleaned data, stats, anomalies, profile)
"""

import pandas as pd
import io
import os
from datetime import datetime

from fpdf import FPDF


def _safe_text(text):
    """Safely encode text for PDF (latin-1 compatible)."""
    return str(text).encode('latin-1', 'replace').decode('latin-1')


class ExcelReportGenerator:
    """Generate a multi-sheet Excel report with formatting."""

    @staticmethod
    def generate(df_clean, summary_stats, anomalies_dict=None, kpis=None, profile_data=None):
        """
        Generate an Excel report as bytes buffer.
        """
        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            workbook = writer.book

            # ── Formats ──────────────────────────────────────────────
            header_fmt = workbook.add_format({
                'bold': True, 'bg_color': '#7C3AED', 'font_color': '#FFFFFF',
                'border': 1, 'text_wrap': True, 'valign': 'vcenter',
                'font_name': 'Segoe UI', 'font_size': 11,
            })
            cell_fmt = workbook.add_format({
                'border': 1, 'valign': 'vcenter', 'font_name': 'Segoe UI', 'font_size': 10,
            })
            number_fmt = workbook.add_format({
                'border': 1, 'valign': 'vcenter', 'font_name': 'Segoe UI', 'font_size': 10,
                'num_format': '#,##0.00',
            })
            title_fmt = workbook.add_format({
                'bold': True, 'font_size': 16, 'font_color': '#7C3AED',
                'font_name': 'Segoe UI', 'bottom': 2, 'bottom_color': '#7C3AED',
            })
            subtitle_fmt = workbook.add_format({
                'bold': True, 'font_size': 12, 'font_color': '#1E293B',
                'font_name': 'Segoe UI',
            })

            # ── Sheet 1: Dashboard ───────────────────────────────────
            ws_dash = workbook.add_worksheet('Dashboard')
            writer.sheets['Dashboard'] = ws_dash
            ws_dash.set_column('A:A', 20)
            ws_dash.set_column('B:F', 15)
            ws_dash.set_tab_color('#7C3AED')

            ws_dash.write('A1', 'AI Excel Automation Engine — Report', title_fmt)
            ws_dash.write('A2', f'Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}', subtitle_fmt)
            ws_dash.write('A3', f'Dataset: {len(df_clean):,} rows x {len(df_clean.columns)} columns')

            if kpis:
                ws_dash.write('A5', 'Key Performance Indicators', subtitle_fmt)
                row = 6
                kpi_metrics = ['total', 'average', 'median', 'min', 'max', 'std', 'growth_pct']
                headers = ['Metric'] + [m.replace('_', ' ').title() for m in kpi_metrics]
                for col_idx, h in enumerate(headers):
                    ws_dash.write(row, col_idx, h, header_fmt)
                row += 1
                for col_name, metrics in kpis.items():
                    ws_dash.write(row, 0, str(col_name), cell_fmt)
                    for col_idx, metric in enumerate(kpi_metrics):
                        val = metrics.get(metric, 0)
                        ws_dash.write(row, col_idx + 1, val, number_fmt)
                    row += 1

            # ── Sheet 2: Cleaned Data ────────────────────────────────
            df_clean.to_excel(writer, sheet_name='Cleaned Data', index=False, startrow=1)
            ws_data = writer.sheets['Cleaned Data']
            ws_data.write('A1', 'Cleaned Dataset', title_fmt)
            ws_data.set_tab_color('#3B82F6')

            for col_idx, col_name in enumerate(df_clean.columns):
                ws_data.write(1, col_idx, col_name, header_fmt)
                ws_data.set_column(col_idx, col_idx, max(12, min(25, len(str(col_name)) + 4)))

            # ── Sheet 3: Summary Statistics ──────────────────────────
            if summary_stats.get('numeric_summary') is not None:
                summary_stats['numeric_summary'].to_excel(writer, sheet_name='Statistics', startrow=1)
                ws_stats = writer.sheets['Statistics']
                ws_stats.write('A1', 'Summary Statistics', title_fmt)
                ws_stats.set_tab_color('#10B981')

            # ── Sheet 4: Anomalies ───────────────────────────────────
            if anomalies_dict:
                all_anomalies = []
                for col, result in anomalies_dict.items():
                    if result.get('count', 0) > 0:
                        anom_df = result['anomalies_df'].copy()
                        anom_df['_anomaly_column'] = col
                        anom_df['_method'] = result.get('method', 'Unknown')
                        all_anomalies.append(anom_df)
                if all_anomalies:
                    combined = pd.concat(all_anomalies, ignore_index=True)
                    combined.to_excel(writer, sheet_name='Anomalies', index=False, startrow=1)
                    ws_anom = writer.sheets['Anomalies']
                    ws_anom.write('A1', 'Detected Anomalies', title_fmt)
                    ws_anom.set_tab_color('#EF4444')

                    for col_idx, col_name in enumerate(combined.columns):
                        ws_anom.write(1, col_idx, col_name, header_fmt)

            # ── Sheet 5: Data Profile ────────────────────────────────
            if profile_data:
                try:
                    profile_df = pd.DataFrame(profile_data)
                    profile_df.to_excel(writer, sheet_name='Data Profile', index=False, startrow=1)
                    ws_profile = writer.sheets['Data Profile']
                    ws_profile.write('A1', 'Column Profile', title_fmt)
                    ws_profile.set_tab_color('#F59E0B')

                    for col_idx, col_name in enumerate(profile_df.columns):
                        ws_profile.write(1, col_idx, col_name, header_fmt)
                except Exception:
                    pass

        buffer.seek(0)
        return buffer


class PDFReportGenerator:
    """Generate a professional PDF report."""

    @staticmethod
    def generate(df_clean, kpis, insights, anomaly_summaries, narrative='',
                 profile_summary=None, ml_anomaly_info=None):
        """Generate a PDF report as bytes buffer."""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)

        # ── Title Page ───────────────────────────────────────────────
        pdf.add_page()
        pdf.set_fill_color(124, 58, 237)
        pdf.rect(0, 0, 210, 297, 'F')

        # Decorative gradient bands
        pdf.set_fill_color(59, 130, 246)
        pdf.rect(0, 250, 210, 5, 'F')
        pdf.set_fill_color(6, 182, 212)
        pdf.rect(0, 257, 210, 3, 'F')

        pdf.set_font('Helvetica', 'B', 42)
        pdf.set_text_color(255, 255, 255)
        pdf.ln(70)
        pdf.cell(0, 22, 'AI Excel Automation', align='C', ln=True)
        pdf.set_font('Helvetica', 'B', 28)
        pdf.cell(0, 14, 'Engine Report', align='C', ln=True)

        pdf.ln(15)
        pdf.set_draw_color(255, 255, 255)
        pdf.set_line_width(0.5)
        pdf.line(60, pdf.get_y(), 150, pdf.get_y())
        pdf.ln(15)

        pdf.set_font('Helvetica', '', 14)
        pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}', align='C', ln=True)
        pdf.cell(0, 10, f'Dataset: {len(df_clean):,} rows x {len(df_clean.columns)} columns', align='C', ln=True)

        n_insights = len(insights) if insights else 0
        pdf.cell(0, 10, f'AI Insights Generated: {n_insights}', align='C', ln=True)

        pdf.ln(35)
        pdf.set_font('Helvetica', 'I', 10)
        pdf.set_text_color(220, 220, 240)
        pdf.cell(0, 8, 'Automated analysis powered by AI Excel Automation Engine', align='C', ln=True)
        pdf.cell(0, 8, 'github.com/muh0210', align='C', ln=True)

        # ── Table of Contents ────────────────────────────────────────
        pdf.add_page()
        pdf.set_text_color(30, 30, 60)
        _pdf_section_header(pdf, 'Table of Contents')
        pdf.ln(4)

        toc_items = [
            ('1. Executive Summary', 3),
            ('2. Key Performance Indicators', 3),
            ('3. AI-Generated Insights', 4),
            ('4. Anomaly Detection Results', 5),
        ]
        if profile_summary:
            toc_items.append(('5. Data Profile', 6))
        toc_items.append((f'{len(toc_items) + 1}. Data Preview', len(toc_items) + 2))

        pdf.set_font('Helvetica', '', 12)
        pdf.set_text_color(40, 40, 70)
        for item, _ in toc_items:
            pdf.cell(0, 9, f'   {item}', ln=True)
        pdf.ln(6)

        # ── Executive Summary ────────────────────────────────────────
        _pdf_section_header(pdf, '1. Executive Summary')
        pdf.ln(4)

        pdf.set_text_color(40, 40, 70)
        pdf.set_font('Helvetica', '', 11)
        if narrative:
            pdf.multi_cell(0, 7, _safe_text(narrative))
        pdf.ln(4)

        # ── KPI Section ──────────────────────────────────────────────
        if kpis:
            _pdf_section_header(pdf, '2. Key Performance Indicators')
            pdf.ln(4)

            pdf.set_text_color(40, 40, 70)
            for col, metrics in list(kpis.items())[:8]:
                pdf.set_font('Helvetica', 'B', 12)
                pdf.cell(0, 8, _safe_text(col), ln=True)
                pdf.set_font('Helvetica', '', 10)

                total = metrics.get('total', 0)
                avg = metrics.get('average', 0)
                median = metrics.get('median', 0)
                growth = metrics.get('growth_pct', 0)

                pdf.cell(0, 6, f"    Total: {total:,.2f}   |   Average: {avg:,.2f}   |   Median: {median:,.2f}   |   Growth: {growth:+.1f}%", ln=True)
                pdf.ln(2)

        # ── Insights Section ─────────────────────────────────────────
        if insights:
            pdf.add_page()
            _pdf_section_header(pdf, '3. AI-Generated Insights')
            pdf.ln(4)

            severity_colors = {
                'positive': (16, 185, 129),
                'info': (59, 130, 246),
                'warning': (245, 158, 11),
                'critical': (239, 68, 68),
            }

            pdf.set_text_color(40, 40, 70)
            for insight in insights:
                severity = insight.get('severity', 'info')
                color = severity_colors.get(severity, (59, 130, 246))

                # Colored severity indicator
                pdf.set_fill_color(*color)
                x_pos = pdf.get_x()
                y_pos = pdf.get_y()
                pdf.rect(x_pos, y_pos + 1, 3, 5, 'F')

                pdf.set_font('Helvetica', 'B', 10)
                pdf.set_x(x_pos + 6)
                category = _safe_text(insight['category'])
                pdf.cell(0, 7, f"[{category}] ({severity.upper()})", ln=True)

                pdf.set_font('Helvetica', '', 10)
                text = _safe_text(insight['insight'])
                pdf.set_x(x_pos + 6)
                pdf.multi_cell(0, 6, text)
                pdf.ln(3)

        # ── Anomaly Section ──────────────────────────────────────────
        if anomaly_summaries:
            pdf.add_page()
            _pdf_section_header(pdf, '4. Anomaly Detection Results')
            pdf.ln(4)

            pdf.set_text_color(40, 40, 70)
            pdf.set_font('Helvetica', '', 10)
            for summary in anomaly_summaries:
                safe = _safe_text(summary).replace('**', '')
                pdf.multi_cell(0, 6, safe)
                pdf.ln(2)

            if ml_anomaly_info:
                pdf.ln(4)
                pdf.set_font('Helvetica', 'B', 12)
                pdf.cell(0, 8, 'ML-Based Anomaly Detection', ln=True)
                pdf.set_font('Helvetica', '', 10)
                for line in ml_anomaly_info:
                    safe = _safe_text(line).replace('**', '')
                    pdf.multi_cell(0, 6, safe)
                    pdf.ln(1)

        # ── Data Profile Section ─────────────────────────────────────
        if profile_summary:
            pdf.add_page()
            _pdf_section_header(pdf, '5. Data Profile')
            pdf.ln(4)

            pdf.set_text_color(40, 40, 70)
            pdf.set_font('Helvetica', '', 10)

            profile_items = [
                f"Total Rows: {profile_summary.get('rows', '?'):,}",
                f"Total Columns: {profile_summary.get('columns', '?')}",
                f"Numeric Columns: {profile_summary.get('numeric_columns', '?')}",
                f"Categorical Columns: {profile_summary.get('categorical_columns', '?')}",
                f"DateTime Columns: {profile_summary.get('datetime_columns', '?')}",
                f"Memory Usage: {profile_summary.get('memory_usage', '?')}",
                f"Missing Cells: {profile_summary.get('total_missing', '?')} ({profile_summary.get('missing_pct', '?')}%)",
                f"Duplicate Rows: {profile_summary.get('total_duplicates', '?')} ({profile_summary.get('duplicate_pct', '?')}%)",
            ]

            for item in profile_items:
                pdf.cell(0, 7, f"    {item}", ln=True)

        # ── Data Preview Section ─────────────────────────────────────
        pdf.add_page()
        _pdf_section_header(pdf, f'{6 if profile_summary else 5}. Data Preview (First 20 Rows)')
        pdf.ln(4)

        preview = df_clean.head(20)
        cols = list(preview.columns)[:6]
        col_width = (pdf.w - 20) / len(cols)

        # Header
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_fill_color(124, 58, 237)
        pdf.set_text_color(255, 255, 255)
        for col in cols:
            safe_col = _safe_text(str(col)[:15])
            pdf.cell(col_width, 8, safe_col, border=1, fill=True, align='C')
        pdf.ln()

        # Rows with alternating colors
        pdf.set_text_color(40, 40, 70)
        for idx, (_, row) in enumerate(preview[cols].iterrows()):
            pdf.set_font('Helvetica', '', 7)
            if idx % 2 == 0:
                pdf.set_fill_color(240, 240, 248)
            else:
                pdf.set_fill_color(255, 255, 255)
            for col in cols:
                val = _safe_text(str(row[col])[:18])
                pdf.cell(col_width, 7, val, border=1, fill=True, align='C')
            pdf.ln()

        # ── Footer ───────────────────────────────────────────────────
        pdf.ln(15)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(130, 130, 160)
        pdf.cell(0, 8, 'Report generated by AI Excel Automation Engine', align='C', ln=True)
        pdf.cell(0, 8, f'Muhammad Rajput | github.com/muh0210 | {datetime.now().strftime("%Y-%m-%d %H:%M")}', align='C', ln=True)

        # Output to buffer
        buffer = io.BytesIO()
        pdf_output = pdf.output()
        buffer.write(pdf_output)
        buffer.seek(0)
        return buffer


def _pdf_section_header(pdf, title):
    """Render a styled section header in the PDF."""
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_fill_color(124, 58, 237)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 13, f'  {title}', fill=True, ln=True)
    pdf.ln(2)
