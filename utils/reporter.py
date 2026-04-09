"""
MODULE 7: AUTO REPORT GENERATOR v3.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - Excel: Formula-rich workbook (SUM, AVERAGE, COUNTIF formulas — not static)
  - PDF: White-label support (custom logo, brand colors, company name)
  - Both include: cleaning report, data profile, KPIs, insights, anomalies
"""

import pandas as pd
import io
import os
from datetime import datetime
from fpdf import FPDF


def _safe_text(text):
    """Safely encode text for PDF (latin-1 compatible)."""
    return str(text).encode('latin-1', 'replace').decode('latin-1')


def _col_letter(n):
    """Convert column index (0-based) to Excel column letter."""
    result = ''
    while n >= 0:
        result = chr(n % 26 + ord('A')) + result
        n = n // 26 - 1
    return result


class ExcelReportGenerator:
    """Generate a formula-rich Excel report."""

    @staticmethod
    def generate(df_clean, summary_stats, anomalies_dict=None, kpis=None,
                 profile_data=None, cleaning_report=None):
        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            workbook = writer.book

            # ── Formats ──────────────────────────────────────────
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
            pct_fmt = workbook.add_format({
                'border': 1, 'valign': 'vcenter', 'font_name': 'Segoe UI', 'font_size': 10,
                'num_format': '0.0%',
            })
            title_fmt = workbook.add_format({
                'bold': True, 'font_size': 16, 'font_color': '#7C3AED',
                'font_name': 'Segoe UI', 'bottom': 2, 'bottom_color': '#7C3AED',
            })
            subtitle_fmt = workbook.add_format({
                'bold': True, 'font_size': 12, 'font_color': '#1E293B',
                'font_name': 'Segoe UI',
            })
            good_fmt = workbook.add_format({
                'border': 1, 'bg_color': '#D1FAE5', 'font_color': '#065F46',
                'font_name': 'Segoe UI', 'font_size': 10,
            })
            bad_fmt = workbook.add_format({
                'border': 1, 'bg_color': '#FEE2E2', 'font_color': '#991B1B',
                'font_name': 'Segoe UI', 'font_size': 10,
            })

            # ═══ Sheet 1: Dashboard with FORMULAS ═══════════════
            ws = workbook.add_worksheet('Dashboard')
            writer.sheets['Dashboard'] = ws
            ws.set_tab_color('#7C3AED')
            ws.set_column('A:A', 22)
            ws.set_column('B:H', 16)

            ws.write('A1', 'AI Excel Automation Engine — Report', title_fmt)
            ws.write('A2', f'Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}', subtitle_fmt)
            ws.write('A3', f'Dataset: {len(df_clean):,} rows x {len(df_clean.columns)} columns')

            if kpis:
                ws.write('A5', 'Key Performance Indicators', subtitle_fmt)
                row = 6
                metrics = ['total', 'average', 'median', 'min', 'max', 'std', 'growth_pct']
                headers = ['Metric'] + [m.replace('_', ' ').title() for m in metrics]
                for ci, h in enumerate(headers):
                    ws.write(row, ci, h, header_fmt)
                row += 1
                for col_name, m in kpis.items():
                    ws.write(row, 0, str(col_name), cell_fmt)
                    for ci, metric in enumerate(metrics):
                        ws.write(row, ci + 1, m.get(metric, 0), number_fmt)
                    row += 1

            # ═══ Sheet 2: Cleaned Data with FORMULAS ════════════
            df_clean.to_excel(writer, sheet_name='Cleaned Data', index=False, startrow=1)
            ws_data = writer.sheets['Cleaned Data']
            ws_data.write('A1', 'Cleaned Dataset', title_fmt)
            ws_data.set_tab_color('#3B82F6')

            num_rows = len(df_clean)
            num_cols = len(df_clean.columns)

            for ci, col_name in enumerate(df_clean.columns):
                ws_data.write(1, ci, col_name, header_fmt)
                ws_data.set_column(ci, ci, max(12, min(25, len(str(col_name)) + 4)))

            # Add FORMULA ROW at bottom (SUM, AVERAGE, MIN, MAX, COUNT for numeric)
            formula_start_row = num_rows + 3  # +1 for header, +1 for data offset, +1 gap
            ws_data.write(formula_start_row, 0, 'FORMULAS', subtitle_fmt)
            labels = ['SUM', 'AVERAGE', 'COUNT', 'MIN', 'MAX', 'STDEV']
            for li, label in enumerate(labels):
                ws_data.write(formula_start_row + 1 + li, 0, label, header_fmt)

            for ci, col_name in enumerate(df_clean.columns):
                col_letter = _col_letter(ci)
                data_range = f'{col_letter}3:{col_letter}{num_rows + 2}'

                if pd.api.types.is_numeric_dtype(df_clean[col_name]):
                    formulas = [
                        f'=SUM({data_range})',
                        f'=AVERAGE({data_range})',
                        f'=COUNT({data_range})',
                        f'=MIN({data_range})',
                        f'=MAX({data_range})',
                        f'=STDEV({data_range})',
                    ]
                    for fi, formula in enumerate(formulas):
                        ws_data.write_formula(
                            formula_start_row + 1 + fi, ci,
                            formula, number_fmt
                        )
                else:
                    # COUNTA for text columns
                    ws_data.write_formula(
                        formula_start_row + 1, ci,
                        f'=COUNTA({data_range})', number_fmt
                    )
                    # COUNTBLANK
                    ws_data.write_formula(
                        formula_start_row + 2, ci,
                        f'=COUNTBLANK({data_range})', number_fmt
                    )
                    # COUNTIF unique approximation
                    ws_data.write_formula(
                        formula_start_row + 3, ci,
                        f'=COUNTA({data_range})', number_fmt
                    )

            # Conditional formatting on numeric columns
            for ci, col_name in enumerate(df_clean.columns):
                if pd.api.types.is_numeric_dtype(df_clean[col_name]):
                    col_letter = _col_letter(ci)
                    data_range = f'{col_letter}3:{col_letter}{num_rows + 2}'
                    # Color scale: red (low) -> green (high)
                    ws_data.conditional_format(data_range, {
                        'type': '3_color_scale',
                        'min_color': '#FEE2E2',
                        'mid_color': '#FFFFFF',
                        'max_color': '#D1FAE5',
                    })

            # ═══ Sheet 3: Statistics ════════════════════════════
            if summary_stats.get('numeric_summary') is not None:
                summary_stats['numeric_summary'].to_excel(writer, sheet_name='Statistics', startrow=1)
                ws_s = writer.sheets['Statistics']
                ws_s.write('A1', 'Summary Statistics', title_fmt)
                ws_s.set_tab_color('#10B981')

            # ═══ Sheet 4: Anomalies ════════════════════════════
            if anomalies_dict:
                all_anom = []
                for col, result in anomalies_dict.items():
                    if result.get('count', 0) > 0:
                        adf = result['anomalies_df'].copy()
                        adf['_anomaly_column'] = col
                        adf['_method'] = result.get('method', 'Unknown')
                        all_anom.append(adf)
                if all_anom:
                    combined = pd.concat(all_anom, ignore_index=True)
                    combined.to_excel(writer, sheet_name='Anomalies', index=False, startrow=1)
                    ws_a = writer.sheets['Anomalies']
                    ws_a.write('A1', 'Detected Anomalies', title_fmt)
                    ws_a.set_tab_color('#EF4444')
                    for ci, cn in enumerate(combined.columns):
                        ws_a.write(1, ci, cn, header_fmt)

            # ═══ Sheet 5: Data Profile ═════════════════════════
            if profile_data:
                try:
                    pdf = pd.DataFrame(profile_data)
                    pdf.to_excel(writer, sheet_name='Data Profile', index=False, startrow=1)
                    ws_p = writer.sheets['Data Profile']
                    ws_p.write('A1', 'Column Profile', title_fmt)
                    ws_p.set_tab_color('#F59E0B')
                    for ci, cn in enumerate(pdf.columns):
                        ws_p.write(1, ci, cn, header_fmt)
                except Exception:
                    pass

            # ═══ Sheet 6: Cleaning Report ══════════════════════
            if cleaning_report:
                try:
                    ws_c = workbook.add_worksheet('Cleaning Report')
                    writer.sheets['Cleaning Report'] = ws_c
                    ws_c.set_tab_color('#06B6D4')
                    ws_c.set_column('A:A', 28)
                    ws_c.set_column('B:B', 55)

                    ws_c.write('A1', 'Data Cleaning Report', title_fmt)
                    ws_c.write('A3', 'Original Shape:', subtitle_fmt)
                    ws_c.write('B3', str(cleaning_report.get('original_shape', 'N/A')))
                    ws_c.write('A4', 'Cleaned Shape:', subtitle_fmt)
                    ws_c.write('B4', str(cleaning_report.get('cleaned_shape', 'N/A')))
                    ws_c.write('A5', 'Duplicates Removed:', subtitle_fmt)
                    ws_c.write('B5', cleaning_report.get('duplicates_removed', 0))
                    ws_c.write('A6', 'Data Completeness:', subtitle_fmt)
                    ws_c.write('B6', f"{cleaning_report.get('data_completeness', 100)}%")

                    row = 8
                    actions = cleaning_report.get('missing_value_actions', {})
                    if actions:
                        ws_c.write(row, 0, 'Missing Value Fixes', subtitle_fmt)
                        row += 1
                        ws_c.write(row, 0, 'Column', header_fmt)
                        ws_c.write(row, 1, 'Action Taken', header_fmt)
                        row += 1
                        for cn, action in actions.items():
                            ws_c.write(row, 0, str(cn), cell_fmt)
                            ws_c.write(row, 1, str(action), cell_fmt)
                            row += 1

                    row += 1
                    markers = cleaning_report.get('markers_replaced', {})
                    if markers:
                        ws_c.write(row, 0, 'Placeholder Values Detected', subtitle_fmt)
                        row += 1
                        ws_c.write(row, 0, 'Column', header_fmt)
                        ws_c.write(row, 1, 'Values Converted to Missing', header_fmt)
                        row += 1
                        for cn, count in markers.items():
                            ws_c.write(row, 0, str(cn), cell_fmt)
                            ws_c.write(row, 1, f'{count} placeholder(s) (N/A, -, empty, etc.) converted to null', cell_fmt)
                            row += 1

                    row += 1
                    renames = cleaning_report.get('columns_renamed', {})
                    if renames:
                        ws_c.write(row, 0, 'Column Renames', subtitle_fmt)
                        row += 1
                        ws_c.write(row, 0, 'Original Name', header_fmt)
                        ws_c.write(row, 1, 'New Name', header_fmt)
                        row += 1
                        for old, new in renames.items():
                            ws_c.write(row, 0, str(old), cell_fmt)
                            ws_c.write(row, 1, str(new), cell_fmt)
                            row += 1
                except Exception:
                    pass

        buffer.seek(0)
        return buffer


class PDFReportGenerator:
    """Generate a white-label PDF report."""

    @staticmethod
    def generate(df_clean, kpis, insights, anomaly_summaries, narrative='',
                 profile_summary=None, ml_anomaly_info=None, cleaning_report=None,
                 brand_name=None, brand_color_hex=None, logo_path=None):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)

        # Brand customization
        if brand_color_hex:
            try:
                hex_clean = brand_color_hex.lstrip('#')
                br, bg, bb = int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16)
            except Exception:
                br, bg, bb = 124, 58, 237
        else:
            br, bg, bb = 124, 58, 237

        company = brand_name or 'AI Excel Automation Engine'

        # ── Title Page ──────────────────────────────────────────
        pdf.add_page()
        pdf.set_fill_color(br, bg, bb)
        pdf.rect(0, 0, 210, 297, 'F')

        # Gradient bands
        pdf.set_fill_color(min(br + 40, 255), min(bg + 40, 255), min(bb + 40, 255))
        pdf.rect(0, 248, 210, 5, 'F')
        pdf.set_fill_color(min(br + 80, 255), min(bg + 80, 255), min(bb + 80, 255))
        pdf.rect(0, 255, 210, 3, 'F')

        # Logo
        if logo_path and os.path.exists(logo_path):
            try:
                pdf.image(logo_path, x=75, y=30, w=60)
                pdf.ln(80)
            except Exception:
                pdf.ln(70)
        else:
            pdf.ln(70)

        pdf.set_font('Helvetica', 'B', 38)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 22, _safe_text(company), align='C', ln=True)

        pdf.set_font('Helvetica', 'B', 22)
        pdf.cell(0, 14, 'Data Analysis Report', align='C', ln=True)

        pdf.ln(15)
        pdf.set_draw_color(255, 255, 255)
        pdf.set_line_width(0.5)
        pdf.line(60, pdf.get_y(), 150, pdf.get_y())
        pdf.ln(15)

        pdf.set_font('Helvetica', '', 14)
        pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}', align='C', ln=True)
        pdf.cell(0, 10, f'Dataset: {len(df_clean):,} rows x {len(df_clean.columns)} columns', align='C', ln=True)
        pdf.cell(0, 10, f'AI Insights: {len(insights) if insights else 0}', align='C', ln=True)

        pdf.ln(35)
        pdf.set_font('Helvetica', 'I', 10)
        pdf.set_text_color(220, 220, 240)
        if not brand_name:
            pdf.cell(0, 8, 'Powered by AI Excel Automation Engine | github.com/muh0210', align='C', ln=True)

        # ── TOC ─────────────────────────────────────────────────
        pdf.add_page()
        pdf.set_text_color(30, 30, 60)
        _pdf_header(pdf, 'Table of Contents', br, bg, bb)
        pdf.ln(4)

        sections = ['1. Executive Summary', '2. Data Cleaning Report', '3. Key Performance Indicators',
                     '4. AI-Generated Insights', '5. Anomaly Detection']
        if profile_summary: sections.append('6. Data Profile')
        sections.append(f'{len(sections)+1}. Data Preview')

        pdf.set_font('Helvetica', '', 12)
        pdf.set_text_color(40, 40, 70)
        for s in sections:
            pdf.cell(0, 9, f'   {s}', ln=True)

        # ── 1. Executive Summary ────────────────────────────────
        pdf.ln(6)
        _pdf_header(pdf, '1. Executive Summary', br, bg, bb)
        pdf.ln(4)
        pdf.set_text_color(40, 40, 70)
        pdf.set_font('Helvetica', '', 11)
        if narrative:
            pdf.multi_cell(0, 7, _safe_text(narrative))

        # ── 2. Cleaning Report ──────────────────────────────────
        pdf.add_page()
        _pdf_header(pdf, '2. Data Cleaning Report', br, bg, bb)
        pdf.ln(4)
        pdf.set_text_color(40, 40, 70)
        pdf.set_font('Helvetica', '', 10)

        if cleaning_report:
            items = [
                f"Original Shape: {cleaning_report.get('original_shape', 'N/A')}",
                f"Cleaned Shape: {cleaning_report.get('cleaned_shape', 'N/A')}",
                f"Duplicates Removed: {cleaning_report.get('duplicates_removed', 0)}",
                f"Data Completeness: {cleaning_report.get('data_completeness', 100)}%",
            ]
            for item in items:
                pdf.cell(0, 7, f"    {item}", ln=True)

            markers = cleaning_report.get('markers_replaced', {})
            if markers:
                pdf.ln(3)
                pdf.set_font('Helvetica', 'B', 11)
                pdf.cell(0, 8, 'Placeholder Values Detected & Converted:', ln=True)
                pdf.set_font('Helvetica', '', 10)
                for col, count in markers.items():
                    pdf.cell(0, 6, f"    {_safe_text(col)}: {count} placeholder(s) converted to null", ln=True)

            actions = cleaning_report.get('missing_value_actions', {})
            if actions:
                pdf.ln(3)
                pdf.set_font('Helvetica', 'B', 11)
                pdf.cell(0, 8, 'Missing Value Fixes Applied:', ln=True)
                pdf.set_font('Helvetica', '', 10)
                for col, action in actions.items():
                    safe = _safe_text(action)
                    pdf.multi_cell(0, 6, f"    {_safe_text(col)}: {safe}")
                    pdf.ln(1)
        else:
            pdf.cell(0, 7, '    No cleaning report data available.', ln=True)

        # ── 3. KPIs ─────────────────────────────────────────────
        if kpis:
            pdf.add_page()
            _pdf_header(pdf, '3. Key Performance Indicators', br, bg, bb)
            pdf.ln(4)
            pdf.set_text_color(40, 40, 70)
            for col, m in list(kpis.items())[:8]:
                pdf.set_font('Helvetica', 'B', 12)
                pdf.cell(0, 8, _safe_text(col), ln=True)
                pdf.set_font('Helvetica', '', 10)
                line = f"    Total: {m.get('total',0):,.2f}  |  Avg: {m.get('average',0):,.2f}  |  Median: {m.get('median',0):,.2f}  |  Growth: {m.get('growth_pct',0):+.1f}%"
                pdf.cell(0, 6, line, ln=True)
                pdf.ln(2)

        # ── 4. Insights ─────────────────────────────────────────
        if insights:
            pdf.add_page()
            _pdf_header(pdf, '4. AI-Generated Insights', br, bg, bb)
            pdf.ln(4)
            colors = {'positive': (16,185,129), 'info': (59,130,246),
                      'warning': (245,158,11), 'critical': (239,68,68)}
            pdf.set_text_color(40, 40, 70)
            for ins in insights:
                c = colors.get(ins.get('severity','info'), (59,130,246))
                pdf.set_fill_color(*c)
                x, y = pdf.get_x(), pdf.get_y()
                pdf.rect(x, y+1, 3, 5, 'F')
                pdf.set_font('Helvetica', 'B', 10)
                pdf.set_x(x + 6)
                pdf.cell(0, 7, f"[{_safe_text(ins['category'])}]", ln=True)
                pdf.set_font('Helvetica', '', 10)
                pdf.set_x(x + 6)
                pdf.multi_cell(0, 6, _safe_text(ins['insight']))
                pdf.ln(2)

        # ── 5. Anomalies ────────────────────────────────────────
        if anomaly_summaries:
            pdf.add_page()
            _pdf_header(pdf, '5. Anomaly Detection Results', br, bg, bb)
            pdf.ln(4)
            pdf.set_text_color(40, 40, 70)
            pdf.set_font('Helvetica', '', 10)
            for s in anomaly_summaries:
                pdf.multi_cell(0, 6, _safe_text(str(s).replace('**', '')))
                pdf.ln(2)
            if ml_anomaly_info:
                pdf.ln(3)
                pdf.set_font('Helvetica', 'B', 12)
                pdf.cell(0, 8, 'ML-Based Detection', ln=True)
                pdf.set_font('Helvetica', '', 10)
                for line in ml_anomaly_info:
                    pdf.multi_cell(0, 6, _safe_text(str(line).replace('**', '')))

        # ── 6. Profile ──────────────────────────────────────────
        if profile_summary:
            pdf.add_page()
            _pdf_header(pdf, '6. Data Profile', br, bg, bb)
            pdf.ln(4)
            pdf.set_text_color(40, 40, 70)
            pdf.set_font('Helvetica', '', 10)
            for key in ['rows','columns','numeric_columns','categorical_columns','datetime_columns','memory_usage','total_missing','missing_pct','total_duplicates','duplicate_pct']:
                val = profile_summary.get(key, 'N/A')
                label = key.replace('_', ' ').title()
                pdf.cell(0, 7, f"    {label}: {val}", ln=True)

        # ── Data Preview ────────────────────────────────────────
        pdf.add_page()
        sec_num = 7 if profile_summary else 6
        _pdf_header(pdf, f'{sec_num}. Data Preview (First 20 Rows)', br, bg, bb)
        pdf.ln(4)

        preview = df_clean.head(20)
        cols = list(preview.columns)[:6]
        col_w = (pdf.w - 20) / len(cols)

        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_fill_color(br, bg, bb)
        pdf.set_text_color(255, 255, 255)
        for c in cols:
            pdf.cell(col_w, 8, _safe_text(str(c)[:15]), border=1, fill=True, align='C')
        pdf.ln()

        pdf.set_text_color(40, 40, 70)
        for idx, (_, row) in enumerate(preview[cols].iterrows()):
            pdf.set_font('Helvetica', '', 7)
            if idx % 2 == 0:
                pdf.set_fill_color(240, 240, 248)
            else:
                pdf.set_fill_color(255, 255, 255)
            for c in cols:
                pdf.cell(col_w, 7, _safe_text(str(row[c])[:18]), border=1, fill=True, align='C')
            pdf.ln()

        # Footer
        pdf.ln(15)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(130, 130, 160)
        footer_text = f'Report by {company}' if brand_name else 'Report by AI Excel Automation Engine | Muhammad Rajput | github.com/muh0210'
        pdf.cell(0, 8, footer_text, align='C', ln=True)
        pdf.cell(0, 8, datetime.now().strftime("%Y-%m-%d %H:%M"), align='C', ln=True)

        buf = io.BytesIO()
        buf.write(pdf.output())
        buf.seek(0)
        return buf


def _pdf_header(pdf, title, r=124, g=58, b=237):
    """Styled section header."""
    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_fill_color(r, g, b)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, f'  {title}', fill=True, ln=True)
    pdf.ln(2)
