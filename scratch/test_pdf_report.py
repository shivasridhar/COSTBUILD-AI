import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.reports.generator import generate_pdf_report
import pdfplumber

def test_pdf_generation():
    print("==========================================================================")
    print("            TESTING PDF REPORT GENERATION (WEASYPRINT / REPORTLAB)       ")
    print("==========================================================================")

    pdf_bytes = generate_pdf_report(
        sqft=1500,
        target_materials=["steel", "cement", "sand", "brick", "gravel", "wiring"],
        region="Tamil Nadu",
        include_vendor_quotes=True
    )

    out_path = os.path.join(BASE_DIR, "scratch", "test_report_output.pdf")
    with open(out_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"\n[PDF GENERATED SUCCESSFULLY]: Saved {len(pdf_bytes)} bytes to {out_path}")
    assert pdf_bytes.startswith(b"%PDF-"), "Generated file is not a valid PDF document!"

    # Parse with pdfplumber to check text content
    print("\n[PDF TEXT CONTENT AUDIT]:")
    full_text = ""
    with pdfplumber.open(out_path) as pdf:
        print(f"  - Total Pages Generated: {len(pdf.pages)}")
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            full_text += f"\n--- PAGE {i} ---\n" + text

    # Verify key sections
    check_items = [
        ("Header & Title", "BuildCost AI"),
        ("Project Size", "1500 sq.ft"),
        ("Region", "Tamil Nadu"),
        ("Anchor Table", "Reference Rate Anchoring"),
        ("Baseline Source Badge", "WPI Anchor Only"),
        ("Forecast Section", "12-Month Price Trajectory Extrapolation"),
        ("Reliability Section", "Walk-Forward Backtest Forecast Reliability"),
        ("Reliability Status", "High Reliability"),
        ("BOM Cost Table", "Monthly Bill of Materials"),
        ("Recommendation Banner", "Strategic Procurement Recommendation"),
        ("Quote Verification Log", "Vendor Quote Verification Log"),
        ("Model Disclosure", "Phase 3 evaluation revealed"),
    ]

    print("\n[VERIFICATION RESULTS - MONTH 1 RECOMMENDED HORIZON]:")
    all_passed = True
    for item_name, text_snippet in check_items:
        present = text_snippet.lower() in full_text.lower()
        status = "PASSED" if present else "FAILED"
        print(f"  - [{status}] {item_name}: Found '{text_snippet}' -> {present}")
        if not present:
            all_passed = False

    # Now run explicit Month 12 horizon test to verify Low Data (N < 30) footnote
    print("\n[RUNNING MONTH 12 HORIZON LOW-DATA (N < 30) TEST]:")
    from src.optimization.bom_optimizer import optimize_procurement
    opt_12 = optimize_procurement(sqft=1500, region="Tamil Nadu")
    # Simulate recommendation selecting Month 12 horizon where Wiring N=27 < 30
    opt_12['recommendation']['recommended_month_idx'] = 12
    opt_12['recommendation']['recommended_year_month'] = '2027-06'
    opt_12['recommendation']['horizon_mape_by_material']['wiring'] = {'mape_pct': 12.13, 'sample_count': 27, 'low_confidence': True}
    from src.reports.chart_renderer import render_forecast_chart_base64
    from src.reports.chart_renderer import render_forecast_chart_base64
    chart_b64 = render_forecast_chart_base64(opt_12['forecast_table'])
    from src.reports.generator import render_pdf_reportlab
    metadata = {"model_limitation_note": "Phase 3 evaluation revealed that complex ML models provided only a marginal, unreliable edge..."}
    pdf_12_bytes = render_pdf_reportlab(opt_12, chart_b64, ["steel", "cement", "wiring"], [], metadata, region="Tamil Nadu")
    
    out_12_path = os.path.join(BASE_DIR, "scratch", "test_report_month12.pdf")
    with open(out_12_path, "wb") as f:
        f.write(pdf_12_bytes)

    with pdfplumber.open(out_12_path) as pdf12:
        txt12 = "".join([p.extract_text() for p in pdf12.pages])

    low_data_present = "low data (n < 30)" in txt12.lower()
    print(f"  - [{'PASSED' if low_data_present else 'FAILED'}] Low Data (N < 30) Footnote in Month 12 Report: {low_data_present}")

    if all_passed and low_data_present:
        print("\nALL PDF REPORT SECTIONS & ACCURACY FEATURES (INCLUDING LOW DATA FOOTNOTE) SUCCESSFULLY VERIFIED!")
    else:
        print("\nSOME SECTIONS WERE MISSING IN TEXT EXTRACT - CHECK DETAILS ABOVE.")

if __name__ == "__main__":
    test_pdf_generation()
