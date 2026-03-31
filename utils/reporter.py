"""
MODULE 7: AUTO REPORT GENERATOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generates downloadable PDF and Excel reports.
  • PDF: Title page, KPIs, insights, anomaly table
  • Excel: Multi-sheet workbook (cleaned data, stats, anomalies)
"""

import pandas as pd
import io
import os
from datetime import datetime

# PDF generation
from fpdf import FPDF


class ExcelReportGenerator:
    """Generate a multi-sheet Excel report."""

    @staticmethod
    def generate(df_clean, summary_stats, anomalies_dict=None, kpis=None):
        """
        Generate an Excel report as bytes buffer.

        Args:
            df_clean: cleaned DataFrame
            summary_stats: dict from basic_analysis
            anomalies_dict: dict from detect_all_anomalies (optional)
            kpis: dict from compute_kpis (optional)

        Returns:
            io.BytesIO buffer containing the Excel file
        """
        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Sheet 1: Cleaned Data
            df_clean.to_excel(writer, sheet_name='Cleaned Data', index=False)

            # Sheet 2: Summary Statistics
            if summary_stats.get('numeric_summary') is not None:
                summary_stats['numeric_summary'].to_excel(writer, sheet_name='Summary Statistics')

            # Sheet 3: KPIs
            if kpis:
                kpi_df = pd.DataFrame(kpis).T
                kpi_df.index.name = 'Metric'
                kpi_df.to_excel(writer, sheet_name='KPI Dashboard')

            # Sheet 4: Anomalies (if any)
            if anomalies_dict:
                all_anomalies = []
                for col, result in anomalies_dict.items():
                    if result['count'] > 0:
                        anom_df = result['anomalies_df'].copy()
                        anom_df['_anomaly_column'] = col
                        anom_df['_method'] = result['method']
                        all_anomalies.append(anom_df)
                if all_anomalies:
                    combined = pd.concat(all_anomalies, ignore_index=True)
                    combined.to_excel(writer, sheet_name='Anomalies', index=False)

            # Format sheets
            workbook = writer.book
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#7C3AED',
                'font_color': '#FFFFFF',
                'border': 1,
                'text_wrap': True,
                'valign': 'vcenter',
            })
            cell_format = workbook.add_format({'border': 1, 'valign': 'vcenter'})

            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                worksheet.set_column('A:Z', 16)

        buffer.seek(0)
        return buffer


class PDFReportGenerator:
    """Generate a professional PDF report."""

    @staticmethod
    def generate(df_clean, kpis, insights, anomaly_summaries, narrative=''):
        """
        Generate a PDF report as bytes buffer.

        Args:
            df_clean: cleaned DataFrame
            kpis: dict from compute_kpis
            insights: list of insight dicts
            anomaly_summaries: list of summary strings
            narrative: summary narrative string

        Returns:
            io.BytesIO buffer containing the PDF file
        """
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)

        # ── Title Page ───────────────────────────────────────────────
        pdf.add_page()
        pdf.set_fill_color(124, 58, 237)  # Purple
        pdf.rect(0, 0, 210, 297, 'F')

        pdf.set_font('Helvetica', 'B', 36)
        pdf.set_text_color(255, 255, 255)
        pdf.ln(80)
        pdf.cell(0, 20, 'AI Excel Automation', align='C', ln=True)
        pdf.set_font('Helvetica', '', 20)
        pdf.cell(0, 12, 'Engine Report', align='C', ln=True)

        pdf.ln(20)
        pdf.set_font('Helvetica', '', 14)
        pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}', align='C', ln=True)
        pdf.cell(0, 10, f'Dataset: {len(df_clean):,} rows x {len(df_clean.columns)} columns', align='C', ln=True)

        pdf.ln(40)
        pdf.set_font('Helvetica', 'I', 11)
        pdf.set_text_color(220, 220, 240)
        pdf.cell(0, 8, 'Automated analysis powered by AI Excel Automation Engine', align='C', ln=True)

        # ── Summary Page ─────────────────────────────────────────────
        pdf.add_page()
        pdf.set_text_color(30, 30, 60)

        pdf.set_font('Helvetica', 'B', 22)
        pdf.set_fill_color(124, 58, 237)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 14, '  Executive Summary', fill=True, ln=True)
        pdf.ln(8)

        pdf.set_text_color(40, 40, 70)
        pdf.set_font('Helvetica', '', 11)
        if narrative:
            # Encode to latin-1 safe characters
            safe_narrative = narrative.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 7, safe_narrative)
        pdf.ln(6)

        # ── KPI Section ──────────────────────────────────────────────
        if kpis:
            pdf.set_font('Helvetica', 'B', 22)
            pdf.set_fill_color(124, 58, 237)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 14, '  Key Performance Indicators', fill=True, ln=True)
            pdf.ln(6)

            pdf.set_text_color(40, 40, 70)
            for col, metrics in kpis.items():
                pdf.set_font('Helvetica', 'B', 13)
                safe_col = str(col).encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(0, 9, safe_col, ln=True)
                pdf.set_font('Helvetica', '', 10)

                total = metrics.get('total', 0)
                avg = metrics.get('average', 0)
                growth = metrics.get('growth_pct', 0)

                pdf.cell(0, 6, f"    Total: {total:,.2f}  |  Average: {avg:,.2f}  |  Growth: {growth:+.1f}%", ln=True)
                pdf.ln(3)

        # ── Insights Section ─────────────────────────────────────────
        if insights:
            pdf.add_page()
            pdf.set_font('Helvetica', 'B', 22)
            pdf.set_fill_color(124, 58, 237)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 14, '  AI-Generated Insights', fill=True, ln=True)
            pdf.ln(6)

            pdf.set_text_color(40, 40, 70)
            for insight in insights:
                pdf.set_font('Helvetica', 'B', 11)
                category = str(insight['category']).encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(0, 7, f"[{category}]", ln=True)
                pdf.set_font('Helvetica', '', 10)
                text = str(insight['insight']).encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 6, f"  {text}")
                pdf.ln(3)

        # ── Anomaly Section ──────────────────────────────────────────
        if anomaly_summaries:
            pdf.add_page()
            pdf.set_font('Helvetica', 'B', 22)
            pdf.set_fill_color(124, 58, 237)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 14, '  Anomaly Detection Results', fill=True, ln=True)
            pdf.ln(6)

            pdf.set_text_color(40, 40, 70)
            pdf.set_font('Helvetica', '', 10)
            for summary in anomaly_summaries:
                safe_summary = str(summary).encode('latin-1', 'replace').decode('latin-1')
                # Remove markdown bold markers for PDF
                safe_summary = safe_summary.replace('**', '')
                pdf.multi_cell(0, 6, safe_summary)
                pdf.ln(2)

        # ── Data Preview Section ─────────────────────────────────────
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 22)
        pdf.set_fill_color(124, 58, 237)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 14, '  Data Preview (First 20 Rows)', fill=True, ln=True)
        pdf.ln(6)

        # Render table (limited columns for PDF width)
        preview = df_clean.head(20)
        cols = list(preview.columns)[:6]  # Limit to 6 columns for readability
        col_width = (pdf.w - 20) / len(cols)

        # Header
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_fill_color(50, 50, 80)
        pdf.set_text_color(255, 255, 255)
        for col in cols:
            safe_col = str(col)[:15].encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(col_width, 8, safe_col, border=1, fill=True, align='C')
        pdf.ln()

        # Rows
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(40, 40, 70)
        for _, row in preview[cols].iterrows():
            for col in cols:
                val = str(row[col])[:18].encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(col_width, 7, val, border=1, align='C')
            pdf.ln()

        # ── Footer ───────────────────────────────────────────────────
        pdf.ln(15)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(130, 130, 160)
        pdf.cell(0, 8, 'Report generated by AI Excel Automation Engine', align='C', ln=True)
        pdf.cell(0, 8, f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', align='C', ln=True)

        # Output to buffer
        buffer = io.BytesIO()
        pdf_output = pdf.output()
        buffer.write(pdf_output)
        buffer.seek(0)
        return buffer
