"""
Automated Integration Test Suite for Storage-Feasibility-Aware Procurement Strategy Advisory.
Verifies DB migration, storage_advisor.py decision matrix logic, API endpoint behavior, and report rendering.
"""

import os
import sys
import sqlite3
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from migrate_add_storage_properties import run_migration
from src.optimization.storage_advisor import (
    evaluate_storage_procurement_strategy,
    get_material_storage_properties
)
from src.api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

DB_PATH = os.path.join(BASE_DIR, "buildcost.db")


def test_storage_advisor_feature():
    print("\n--- 1. RUNNING STORAGE PROPERTIES MIGRATION ---")
    run_migration(DB_PATH)

    print("\n--- 2. VERIFYING SEEDED STORAGE PROPERTIES ---")
    props = get_material_storage_properties(DB_PATH)
    assert "cement" in props, "Cement storage property missing."
    assert props["cement"]["max_safe_storage_days"] == 75, f"Expected 75 days for cement, got {props['cement']['max_safe_storage_days']}"
    assert props["steel"]["max_safe_storage_days"] == 270, f"Expected 270 days for steel, got {props['steel']['max_safe_storage_days']}"
    assert props["sand"]["max_safe_storage_days"] is None, "Sand max_safe_storage_days should be None"
    print(f"Cement notes: {props['cement']['storage_notes']}")
    print(f"Steel notes: {props['steel']['storage_notes']}")
    print("[SUCCESS] Material storage properties reference table verified.")

    print("\n--- 3. CREATING TEST ENGINEER ACCOUNT & PERSISTENT PROJECT ---")
    reg_resp = client.post("/auth/register", json={
        "email": "storage_engineer@buildcost.ai",
        "password": "StoragePass123!",
        "name": "Storage Strategy Engineer"
    })

    if reg_resp.status_code == 201:
        token = reg_resp.json()["access_token"]
    else:
        login_resp = client.post("/auth/login", json={
            "email": "storage_engineer@buildcost.ai",
            "password": "StoragePass123!"
        })
        token = login_resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    proj_resp = client.post("/projects", headers=headers, json={
        "name": "Test Villa — Storage Strategy Evaluation",
        "sqft": 1500,
        "target_materials": ["steel", "cement", "sand", "brick", "gravel", "wiring"],
        "region": "Tamil Nadu",
        "notes": "Testing storage feasibility across Foundation and Structure phases."
    })
    assert proj_resp.status_code == 201, f"Project creation failed: {proj_resp.text}"
    project_id = proj_resp.json()["id"]
    print(f"Created Test Project ID #{project_id}")

    print("\n--- 4. CREATING TEST PHASES WITH 5-MONTH (150 DAY) GAP ---")
    # Phase 1: Foundation (Month 0) - Needs steel & cement
    p1_resp = client.post(f"/projects/{project_id}/phases", headers=headers, json={
        "phase_name": "Foundation",
        "materials": ["steel", "cement"],
        "expected_start_month": 0,
        "sequence_order": 1
    })
    assert p1_resp.status_code == 201, f"Phase 1 creation failed: {p1_resp.text}"
    print(f"Created Phase 1: Foundation (Month 0)")

    # Phase 2: Structure (Month 5 = 150 days gap) - Needs steel & cement
    p2_resp = client.post(f"/projects/{project_id}/phases", headers=headers, json={
        "phase_name": "Structure",
        "materials": ["steel", "cement"],
        "expected_start_month": 5,
        "sequence_order": 2
    })
    assert p2_resp.status_code == 201, f"Phase 2 creation failed: {p2_resp.text}"
    print(f"Created Phase 2: Structure (Month 5 = 150 days gap)")

    print("\n--- 5. EVALUATING STORAGE ADVISORY DIRECTLY ---")
    strategy_res = evaluate_storage_procurement_strategy(project_id, DB_PATH)
    assert strategy_res["shared_materials_count"] == 2, f"Expected 2 shared materials, got {strategy_res['shared_materials_count']}"

    advisories = {adv["material"]: adv for adv in strategy_res["advisories"]}

    # Verify Steel (150 days gap <= 270 days limit) -> Strategy should be "bulk"
    steel_adv = advisories["steel"]
    print("\n[STEEL ADVISORY]")
    print(f"Strategy: {steel_adv['strategy']}")
    print(f"Reasoning: {steel_adv['reasoning'].replace('₹', 'Rs.')}")
    print(f"Bulk Cost: Rs.{steel_adv['bulk_cost_estimate_rs']:,.2f} | Per-Phase Total: Rs.{steel_adv['per_phase_cost_estimate_rs']:,.2f}")
    assert steel_adv["strategy"] == "bulk", f"Expected 'bulk' strategy for steel, got '{steel_adv['strategy']}'"
    assert steel_adv["storage_safe"] is True, "Steel storage_safe should be True"

    # Verify Cement (150 days gap > 75 days limit) -> Strategy should be "per_phase" due to storage expiry
    cement_adv = advisories["cement"]
    print("\n[CEMENT ADVISORY]")
    print(f"Strategy: {cement_adv['strategy']}")
    print(f"Reasoning: {cement_adv['reasoning'].replace('₹', 'Rs.')}")
    print(f"Storage Safe: {cement_adv['storage_safe']}")
    assert cement_adv["strategy"] == "per_phase", f"Expected 'per_phase' strategy for cement, got '{cement_adv['strategy']}'"
    assert cement_adv["storage_safe"] is False, "Cement storage_safe should be False"
    assert "exceeds" in cement_adv["reasoning"].lower(), "Reasoning should cite safe storage limit exceeded"

    print("\n--- 6. TESTING GET /projects/{id}/procurement-strategy API ENDPOINT ---")
    api_resp = client.get(f"/projects/{project_id}/procurement-strategy", headers=headers)
    assert api_resp.status_code == 200, f"API endpoint failed: {api_resp.text}"
    api_data = api_resp.json()
    assert api_data["project_id"] == project_id
    assert len(api_data["advisories"]) == 2
    print("[SUCCESS] API endpoint returned valid storage advisories.")

    print("\n--- 7. TESTING EXECUTIVE PDF REPORT GENERATION WITH ADVISORY ---")
    pdf_resp = client.post("/generate-report", json={
        "project_id": project_id,
        "include_vendor_quotes": True
    })
    assert pdf_resp.status_code == 200, f"PDF report generation failed: {pdf_resp.text}"
    assert pdf_resp.headers["Content-Type"] == "application/pdf"
    assert len(pdf_resp.content) > 1000
    print(f"[SUCCESS] PDF report stream generated cleanly ({len(pdf_resp.content)} bytes).")

    print("\n=======================================================")
    print("ALL STORAGE-FEASIBILITY PROCUREMENT STRATEGY TESTS PASSED!")
    print("=======================================================")


if __name__ == "__main__":
    test_storage_advisor_feature()
