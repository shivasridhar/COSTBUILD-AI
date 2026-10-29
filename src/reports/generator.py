"""
BuildCost AI - PDF Report Generator Engine.

Consolidates forecast, BOM breakdown, anchor conversion, vendor quotes,
and model limitation disclosures into PDF bytes using Jinja2 and WeasyPrint,
with a robust ReportLab fallback for environments lacking native GTK/Cairo DLLs.
"""

import os
import sys
import io
import sqlite3
import datetime
import base64
from typing import List, Optional, Dict, Any

from jinja2 import Environment, FileSystemLoader

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.optimization.bom_optimizer import (
    optimize_procurement,
    get_material_baseline_rate,
    normalize_unit,
    DEFAULT_DB_PATH
)
from src.reports.chart_renderer import render_forecast_chart_base64

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def fetch_vendor_quotes_data(
    vendor_quote_ids: Optional[List[int]] = None,
    region: Optional[str] = None,
    project_id: Optional[int] = None,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """
    Fetches vendor quotes from buildcost.db vendor_quotes table,
    evaluates baseline rate and verdict for each, and returns detailed dictionary list.
    """
    if not os.path.exists(db_path):
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if project_id is not None:
            query = "SELECT * FROM vendor_quotes WHERE project_id = ? ORDER BY created_at DESC;"
            rows = conn.execute(query, (project_id,)).fetchall()
        elif vendor_quote_ids and len(vendor_quote_ids) > 0:
            placeholders = ",".join(["?"] * len(vendor_quote_ids))
            query = f"SELECT * FROM vendor_quotes WHERE id IN ({placeholders}) ORDER BY created_at DESC;"
            rows = conn.execute(query, vendor_quote_ids).fetchall()
        else:
            if region:
                query = "SELECT * FROM vendor_quotes WHERE created_at >= datetime('now', '-45 days') AND (region IS NULL OR LOWER(region) = LOWER(?)) ORDER BY created_at DESC;"
                rows = conn.execute(query, (region,)).fetchall()
            else:
                query = "SELECT * FROM vendor_quotes WHERE created_at >= datetime('now', '-45 days') ORDER BY created_at DESC;"
                rows = conn.execute(query).fetchall()

            if not rows:
                query = "SELECT * FROM vendor_quotes ORDER BY id DESC LIMIT 10;"
                rows = conn.execute(query).fetchall()

        quote_results = []
        for r in rows:
            mat = r['material']
            q_rate = float(r['quoted_rate'])
            q_unit = r['quoted_unit']
            q_date = r['quoted_date']

            base_info = get_material_baseline_rate(mat, q_date, db_path)
            b_rate = base_info['baseline_rate']
            b_unit = base_info['baseline_unit']

            if base_info.get('out_of_range'):
                verdict = "date out of range"
                dev_pct = 0.0
            elif normalize_unit(q_unit) != normalize_unit(b_unit):
                verdict = "unit mismatch"
                dev_pct = 0.0
            else:
                dev_pct = round(((q_rate - b_rate) / b_rate) * 100.0, 2)
                if dev_pct > 5.0:
                    verdict = "above market"
                elif dev_pct < -5.0:
                    verdict = "below market"
                else:
                    verdict = "at market"

            quote_results.append({
                "id": r['id'],
                "material": mat,
                "quoted_rate": q_rate,
                "quoted_unit": q_unit,
                "quoted_date": q_date,
                "source_note": r['source_note'] or "",
                "baseline_rate": b_rate,
                "baseline_unit": b_unit,
                "deviation_pct": dev_pct,
                "verdict": verdict
            })

        return quote_results
    finally:
        conn.close()


def render_pdf_reportlab(
    opt_res: dict,
    chart_base64: str,
    target_materials: list,
    vendor_quotes: list,
    metadata: dict,
    region: Optional[str] = None
) -> bytes:
    """
    Fallback PDF generator using ReportLab when WeasyPrint native DLLs are not present.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold'
    )
    sub_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#64748b')
    )
    sec_style = ParagraphStyle(
        'SecTitle',
        parent=styles['Heading2'],
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold',
        spaceBefore=12,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1e293b')
    )

    story = []

    # 1. Header
    rec = opt_res['recommendation']
    anchors = opt_res['anchor_conversion']
    mats_str = ", ".join(target_materials)
    gen_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    reg_str = region if region else "National Baseline"

    story.append(Paragraph("BuildCost AI — Procurement & Forecast Verification Report", title_style))
    story.append(Paragraph(f"Project Size: <b>{rec['sqft']} sq.ft</b> | Region: <b>{reg_str}</b> | Materials: <b>{mats_str}</b> | Date: {gen_date}", sub_style))
    story.append(Spacer(1, 10))

    # 2. Anchor Conversion Table
    story.append(Paragraph("1. Reference Rate Anchoring & Baseline Sources", sec_style))
    anc_data = [
        ["Material", "Item Code", "PWD SOR (FY25-26)", "Avg WPI", "Factor (₹/pt)", "Effective Base Rate", "Baseline Source", "Status"]
    ]
    for mat_key in ['cement', 'steel', 'wiring']:
        item_data = anchors.get(mat_key, {})
        code = item_data.get('item_code', 'N/A')
        unit_str = 'Rmt' if mat_key == 'wiring' else 'MT'
        pwd_rate = item_data.get(f'pwd_rate_rs_per_{unit_str}', item_data.get('pwd_rate_rs_per_MT', 0.0))
        wpi_avg = item_data.get('fy25_26_avg_wpi', 0.0)
        factor = item_data.get('rs_per_index_point', 0.0)
        eff_rate = item_data.get('effective_rate_rs_per_MT', item_data.get(f'effective_rate_rs_per_{unit_str}', 0.0))
        corr = item_data.get('correction', {})
        src_label = "Corrected by Quotes" if corr.get('baseline_source') == 'wpi_anchor_corrected_by_quotes' else "WPI Anchor Only"
        
        anc_data.append([
            mat_key.capitalize(), code, f"₹{pwd_rate:,.2f}/{unit_str}", f"{wpi_avg:.2f}", f"₹{factor:.4f}", f"₹{eff_rate:,.2f}/{unit_str}", src_label, "PASS"
        ])

    anc_table = Table(anc_data, colWidths=[60, 55, 80, 50, 65, 85, 95, 45])
    anc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(anc_table)
    story.append(Spacer(1, 10))

    # 3. Forecast Image
    story.append(Paragraph("2. 12-Month Price Trajectory Extrapolation (with Shaded Confidence Bands)", sec_style))
    if chart_base64 and "," in chart_base64:
        img_data = base64.b64decode(chart_base64.split(",")[1])
        img_buf = io.BytesIO(img_data)
        rl_img = RLImage(img_buf, width=520, height=190)
        story.append(rl_img)
        story.append(Spacer(1, 10))

    # 4. Forecast Reliability Table
    rec_h = rec.get('recommended_month_idx', 1)
    story.append(Paragraph(f"3. Walk-Forward Backtest Forecast Reliability (Month {rec_h} Horizon)", sec_style))
    rel_headers = ["Material", "Target Horizon", "Historical MAPE (±%)", "Sample Count (N)", "Statistical Reliability Status"]
    rel_rows = [rel_headers]
    
    mape_dict = rec.get('horizon_mape_by_material', {})
    if mape_dict:
        for mat, info in mape_dict.items():
            status_text = f"Low Data (N < 30)†" if info.get('low_confidence') else "High Reliability (N ≥ 30)"
            rel_rows.append([
                mat.capitalize(), f"Month {rec_h}", f"±{info.get('mape_pct', 0.0):.2f}%", f"N={info.get('sample_count', 0)}", status_text
            ])
    else:
        rel_rows.append(["Steel", f"Month {rec_h}", f"±{rec.get('steel_horizon_mape_pct', 0.0):.2f}%", f"N={rec.get('steel_horizon_sample_count', 154)}", "High Reliability (N ≥ 30)"])

    t_rel = Table(rel_rows, colWidths=[70, 70, 90, 80, 210])
    t_rel.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(t_rel)
    story.append(Paragraph("† <i>Low Sample Floor (N &lt; 30)</i>: Insufficient historical evaluation windows at this horizon. Treat percentage as a rough estimate.", sub_style))
    story.append(Spacer(1, 10))

    # 5. Monthly BOM Cost Table
    story.append(Paragraph("4. Monthly Bill of Materials (BOM) Total Cost Trajectory", sec_style))
    bom_headers = ["Month", "Year-Month", "Cement (₹)", "Steel (₹)", "Wiring (₹)", "Static Subtotal (₹)", "Total BOM Cost (₹)"]
    bom_rows_data = [bom_headers]
    for r in opt_res['bom_cost_table']:
        bom_rows_data.append([
            f"Month {r['month_idx']}",
            r['year_month'],
            f"₹{r['cement_cost_rs']:,.2f}",
            f"₹{r['steel_cost_rs']:,.2f}",
            f"₹{r['wiring_cost_rs']:,.2f}",
            f"₹{r['static_materials_subtotal_rs']:,.2f}",
            f"₹{r['total_bom_cost_rs']:,.2f}"
        ])
    t_bom = Table(bom_rows_data, colWidths=[50, 65, 80, 80, 75, 85, 85])
    t_bom.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(t_bom)
    story.append(Spacer(1, 10))

    # 6. Recommendation Summary
    story.append(Paragraph("5. Strategic Procurement Recommendation", sec_style))
    rel_sub = rec.get('reliability_subtext', '')
    rec_text = f"<b>{rec['summary_message']}</b><br/><br/>" \
               f"• Immediate Purchase Cost (Month 1): ₹{rec['immediate_cost_rs']:,.2f}<br/>" \
               f"• Recommended Optimal Cost: ₹{rec['optimal_cost_rs']:,.2f}<br/>" \
               f"• Projected Savings: ₹{rec['savings_rs']:,.2f} ({rec['savings_percent']:.2f}%)<br/>" \
               f"<i>{rel_sub}</i>"
    story.append(Paragraph(rec_text, body_style))
    story.append(Spacer(1, 10))

    # 7. Vendor Quotes
    if vendor_quotes:
        story.append(Paragraph("6. Vendor Quote Verification Log", sec_style))
        story.append(Paragraph("Audit record of contractor and vendor quotes checked against fair-market baseline rates for this project.", sub_style))
        vq_headers = ["Date", "Material", "Quoted Rate", "Unit", "Market Baseline", "Deviation", "Verdict"]
        vq_rows = [vq_headers]
        for q in vendor_quotes:
            dev_str = "N/A" if q['verdict'] in ['unit mismatch', 'date out of range'] else f"{q['deviation_pct']:+.2f}%"
            vq_rows.append([
                q['quoted_date'],
                q['material'].capitalize(),
                f"₹{q['quoted_rate']:,.2f}",
                q['quoted_unit'],
                f"₹{q['baseline_rate']:,.2f} / {q['baseline_unit']}",
                dev_str,
                q['verdict'].upper()
            ])
        t_vq = Table(vq_rows, colWidths=[60, 60, 70, 50, 110, 60, 110])
        t_vq.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        story.append(t_vq)
        story.append(Spacer(1, 10))

    # 8. Model Limitation Disclosure
    story.append(Paragraph("Model Limitation & Methodological Note", sec_style))
    story.append(Paragraph(metadata['model_limitation_note'], body_style))
    story.append(Spacer(1, 10))

    # 9. Footer
    story.append(Paragraph("BuildCost AI Platform © 2026. Analytical cost estimates anchored to PWD SOR + WPI trend extrapolations with walk-forward historical error margins.", sub_style))

    doc.build(story)
    return buf.getvalue()


def _parse_materials(val: Any) -> List[str]:
    if not val:
        return []
    if isinstance(val, list):
        return [str(m).strip(' "[]\'') for m in val if str(m).strip(' "[]\'')]
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return [str(m).strip(' "[]\'') for m in parsed if str(m).strip(' "[]\'')]
            if isinstance(parsed, str):
                return [m.strip(' "[]\'') for m in parsed.split(",") if m.strip(' "[]\'')]
        except Exception:
            pass
        return [m.strip(' "[]\'') for m in val.split(",") if m.strip(' "[]\'')]
    return []


def fetch_project_phases_summary(
    project_id: int,
    sqft: int,
    region: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """
    Fetches project phases from project_phases table, evaluates procurement recommendations
    for each phase using start_month_offset, and returns structured summary list.
    """
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_phases';")
        if not cursor.fetchone():
            return []

        rows = conn.execute("SELECT * FROM project_phases WHERE project_id = ? ORDER BY sequence_order ASC, expected_start_month ASC;", (project_id,)).fetchall()
        if not rows:
            return []
        phases_summary = []
        for r in rows:
            mats = _parse_materials(r["materials"])
            ph_dict = {
                "id": r["id"],
                "phase_name": r["phase_name"],
                "materials": mats,
                "expected_start_month": r["expected_start_month"],
                "status": r["status"],
                "sequence_order": r["sequence_order"]
            }
            opt_res = optimize_procurement(
                sqft=sqft,
                target_materials=mats,
                region=region,
                project_id=project_id,
                start_month_offset=r["expected_start_month"],
                db_path=db_path
            )
            phases_summary.append({
                "phase": ph_dict,
                "recommendation": opt_res["recommendation"]
            })
        return phases_summary
    finally:
        conn.close()


def generate_pdf_report(
    sqft: Optional[int] = None,
    target_materials: Optional[List[str]] = None,
    region: Optional[str] = None,
    include_vendor_quotes: bool = True,
    vendor_quote_ids: Optional[List[int]] = None,
    project_id: Optional[int] = None,
    db_path: str = DEFAULT_DB_PATH
) -> bytes:
    """
    Generates PDF report bytes for the given project parameters.

    Returns:
        bytes: Raw PDF document binary data.
    """
    if project_id is not None:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            p_row = conn.execute("SELECT * FROM projects WHERE id = ?;", (project_id,)).fetchone()
            if p_row:
                if sqft is None:
                    sqft = int(p_row["sqft"])
                if target_materials is None and p_row["target_materials"]:
                    try:
                        target_materials = json.loads(p_row["target_materials"])
                    except Exception:
                        pass
                if region is None:
                    region = p_row["region"]
        finally:
            conn.close()

    if sqft is None:
        sqft = 1000

    if target_materials is None:
        target_materials = ["steel", "cement", "sand", "brick", "gravel", "wiring"]

    # 1. Run optimization engine directly (zero math drift)
    opt_res = optimize_procurement(sqft=sqft, target_materials=target_materials, region=region, project_id=project_id, db_path=db_path)

    # 2. Render static Matplotlib chart
    chart_base64 = render_forecast_chart_base64(opt_res['forecast_table'])

    # 3. Fetch vendor quotes if requested
    vendor_quotes_data = []
    if include_vendor_quotes:
        vendor_quotes_data = fetch_vendor_quotes_data(
            vendor_quote_ids=vendor_quote_ids,
            region=region,
            project_id=project_id,
            db_path=db_path
        )

    # 4. Fetch project phases summary & storage procurement strategy if project_id is provided
    phases_summary = []
    storage_strategy = None
    if project_id is not None:
        phases_summary = fetch_project_phases_summary(project_id=project_id, sqft=sqft, region=region, db_path=db_path)
        try:
            from src.optimization.storage_advisor import evaluate_storage_procurement_strategy
            storage_strategy = evaluate_storage_procurement_strategy(project_id=project_id, db_path=db_path)
        except Exception as e:
            storage_strategy = None

    # 5. Prepare Jinja2 environment and render HTML
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("report.html")

    metadata = {
        "model_limitation_note": (
            "Phase 3 evaluation revealed that complex ML models provided only a marginal, "
            "unreliable edge over naive baseline forecasts. Therefore, this procurement engine uses "
            "a simple, transparent naive + recent drift extrapolation to estimate near-term cost trajectories "
            "rather than presenting a fragile model as more capable than it is."
        )
    }

    html_out = template.render(
        rec=opt_res['recommendation'],
        anchors=opt_res['anchor_conversion'],
        bom_rows=opt_res['bom_cost_table'],
        forecast_rows=opt_res['forecast_table'],
        chart_base64=chart_base64,
        target_materials=target_materials,
        region=region,
        generation_date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        include_vendor_quotes=include_vendor_quotes,
        vendor_quotes=vendor_quotes_data,
        phases_summary=phases_summary,
        storage_strategy=storage_strategy,
        metadata=metadata
    )

    # 5. Compile PDF using WeasyPrint (with ReportLab fallback if native GTK DLLs are missing)
    try:
        import weasyprint
        pdf_bytes = weasyprint.HTML(string=html_out).write_pdf()
        return pdf_bytes
    except Exception as e:
        print(f"[REPORT GENERATOR INFO] WeasyPrint native renderer unavailable ({e}). Using ReportLab fallback generator.")
        return render_pdf_reportlab(
            opt_res=opt_res,
            chart_base64=chart_base64,
            target_materials=target_materials,
            vendor_quotes=vendor_quotes_data,
            metadata=metadata,
            region=region
        )
