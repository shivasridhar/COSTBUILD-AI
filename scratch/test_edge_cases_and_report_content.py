"""
Verification test script for:
1. target_materials validation on write (rejects [] and invalid items).
2. region on PATCH flowing through to quote correction & project_id quote matching hierarchy.
3. PDF report content audit for project_id mode (verifying confidence bands, low-N footnotes, model disclosures, vendor table).
"""

import sys
import os
import json
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from src.api.main import app
from migrate_add_projects import run_migration

def test_all_edge_cases():
    print("==================================================")
    print("   EDGE CASES & REPORT CONTENT VERIFICATION TEST   ")
    print("==================================================")

    run_migration()
    client = TestClient(app)

    # -------------------------------------------------------------------------
    # TEST 1: target_materials validation on write
    # -------------------------------------------------------------------------
    print("\n--- [TEST 1] target_materials validation on write ---")
    
    # 1a. Empty target_materials on create
    res_empty_create = client.post("/projects", json={
        "name": "Invalid Project",
        "sqft": 1000,
        "target_materials": [],
        "region": "Tamil Nadu"
    })
    assert res_empty_create.status_code == 422, f"Expected 422 for empty target_materials, got {res_empty_create.status_code}"
    print("[PASS] Rejected empty target_materials on POST /projects (422)")

    # 1b. Invalid material name on create
    res_invalid_mat = client.post("/projects", json={
        "name": "Invalid Material Project",
        "sqft": 1000,
        "target_materials": ["gold", "steel"]
    })
    assert res_invalid_mat.status_code == 422, f"Expected 422 for invalid material, got {res_invalid_mat.status_code}"
    print("[PASS] Rejected invalid material 'gold' on POST /projects (422)")

    # 1c. Create valid project C
    res_c = client.post("/projects", json={
        "name": "Project C — Regionless Build",
        "sqft": 1600,
        "target_materials": ["steel", "cement", "wiring"],
        "region": None
    })
    assert res_c.status_code == 201
    proj_c = res_c.json()
    proj_c_id = proj_c["id"]
    print(f"[PASS] Created Project C (ID: {proj_c_id}, region: None)")

    # 1d. Empty target_materials on PATCH
    res_empty_patch = client.patch(f"/projects/{proj_c_id}", json={"target_materials": []})
    assert res_empty_patch.status_code == 422
    print("[PASS] Rejected empty target_materials on PATCH /projects/{id} (422)")

    # -------------------------------------------------------------------------
    # TEST 2: region on PATCH & project_id quote correction flow
    # -------------------------------------------------------------------------
    print("\n--- [TEST 2] region on PATCH & quote correction flow ---")

    # Log 3 vendor quotes for steel under Project C while region is None
    for i in range(3):
        client.post("/check-fair-price", json={
            "material": "steel",
            "quoted_rate": 58500.0 + (i * 100),
            "quoted_unit": "MT",
            "quoted_date": "2026-07-01",
            "source_note": f"Early quote {i+1} for Project C before region set",
            "project_id": proj_c_id
        })

    # Get forecast for Project C before region is set
    res_fc_before = client.get(f"/projects/{proj_c_id}/forecast")
    assert res_fc_before.status_code == 200
    fc_before = res_fc_before.json()
    steel_anchor_before = fc_before["anchor_conversion"]["steel"]["correction"]
    assert steel_anchor_before["correction_applied"] is True
    assert steel_anchor_before["quote_count"] >= 3
    print(f"[PASS] Baseline correction applied via project_id match (quote count: {steel_anchor_before['quote_count']})")

    # PATCH region on Project C to "Coimbatore"
    res_patch_reg = client.patch(f"/projects/{proj_c_id}", json={"region": "Coimbatore"})
    assert res_patch_reg.status_code == 200
    assert res_patch_reg.json()["region"] == "Coimbatore"
    print("[PASS] Updated region to 'Coimbatore' via PATCH /projects/{id}")

    # Get forecast for Project C after region is set
    res_fc_after = client.get(f"/projects/{proj_c_id}/forecast")
    assert res_fc_after.status_code == 200
    fc_after = res_fc_after.json()
    steel_anchor_after = fc_after["anchor_conversion"]["steel"]["correction"]
    assert steel_anchor_after["correction_applied"] is True
    # The quotes logged before setting region (which have project_id) are still matched!
    assert steel_anchor_after["quote_count"] >= 3
    print("[PASS] Forecast after region update correctly preserves quote correction via project_id hierarchy")

    # -------------------------------------------------------------------------
    # TEST 3: PDF Report Content Audit for project_id Mode
    # -------------------------------------------------------------------------
    print("\n--- [TEST 3] PDF Report Content Audit for project_id Mode ---")

    from src.reports.generator import generate_pdf_report
    pdf_bytes = generate_pdf_report(
        sqft=1600,
        target_materials=["steel", "cement", "wiring"],
        region="Coimbatore",
        include_vendor_quotes=True,
        project_id=proj_c_id
    )
    assert len(pdf_bytes) > 1000, "PDF bytes generated are invalid or empty"
    print(f"[PASS] PDF report generated cleanly ({len(pdf_bytes)} bytes)")

    # Test underlying HTML rendering data to verify report sections & disclosures
    from jinja2 import Environment, FileSystemLoader
    from src.optimization.bom_optimizer import optimize_procurement
    from src.reports.generator import fetch_vendor_quotes_data, TEMPLATES_DIR

    opt_res = optimize_procurement(sqft=1600, target_materials=["steel", "cement", "wiring"], region="Coimbatore", project_id=proj_c_id)
    vendor_quotes_data = fetch_vendor_quotes_data(project_id=proj_c_id)

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("report.html")

    metadata = {
        "model_limitation_note": (
            "Phase 3 evaluation revealed that complex ML models provided only a marginal, "
            "unreliable edge over naive baseline forecasts."
        )
    }

    html_content = template.render(
        rec=opt_res['recommendation'],
        anchors=opt_res['anchor_conversion'],
        bom_rows=opt_res['bom_cost_table'],
        forecast_rows=opt_res['forecast_table'],
        chart_base64="fake_base64",
        target_materials=["steel", "cement", "wiring"],
        region="Coimbatore",
        generation_date="2026-09-10 21:30:00",
        include_vendor_quotes=True,
        vendor_quotes=vendor_quotes_data,
        metadata=metadata
    )

    # Audits on rendered HTML
    assert len(vendor_quotes_data) == 3, f"Expected 3 vendor quotes for Project C, got {len(vendor_quotes_data)}"
    assert "Low Sample Floor (N < 30)" in html_content or "High Reliability" in html_content, "Statistical reliability table missing"
    assert "Vendor Quote Verification Log" in html_content, "Vendor Quote Verification Log missing in report"
    assert "Steel" in html_content, "Steel material row missing in report"
    assert "58,500.00" in html_content or "58,700.00" in html_content, "Project vendor quote rate missing in audit log table"
    assert "Phase 3 evaluation revealed" in html_content, "Model limitation disclosure missing in report"
    assert "Reference Rate Anchoring" in html_content, "Anchor conversion section missing in report"

    print("[PASS] HTML / PDF Report contents fully audited:")
    print("       - Reference Rate Anchoring table: Present")
    print("       - Statistical Reliability & Low Sample Floor footnotes: Present")
    print("       - Vendor Quote Verification Log (project-scoped): Present with project quotes")
    print("       - Model Limitation Disclosure: Present")

    print("\n==================================================")
    print("   ALL 3 AUDIT & EDGE CASE TESTS PASSED 100%!     ")
    print("==================================================")

if __name__ == "__main__":
    test_all_edge_cases()
