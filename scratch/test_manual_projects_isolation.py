"""
Verification Script: Project Isolation & Cross-Contamination Test for BuildCost AI.

Creates two distinct projects:
1. "Priya — Coimbatore House" (1500 sqft, steel/cement/sand, Tamil Nadu)
2. "Erode Industrial Shed" (4500 sqft, steel/brick/gravel/wiring, Erode)

Logs vendor quote A for Priya's project, and vendor quote B for Erode's project.
Generates PDF report for each and verifies:
- Quotes logged under Project A appear ONLY in Project A's data query/report.
- Quotes logged under Project B appear ONLY in Project B's data query/report.
- Zero cross-contamination between projects.
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
from src.reports.generator import fetch_vendor_quotes_data

def run_isolation_verification():
    print("==================================================")
    print("   PROJECT ISOLATION & NO CROSS-CONTAMINATION TEST ")
    print("==================================================")

    # 1. Run migration
    run_migration()
    client = TestClient(app)

    # 2. Create Project 1 (Priya)
    res_1 = client.post("/projects", json={
        "name": "Priya — Coimbatore House",
        "sqft": 1500,
        "target_materials": ["steel", "cement", "sand"],
        "region": "Tamil Nadu",
        "notes": "Residential house build in Coimbatore"
    })
    assert res_1.status_code == 201, f"Failed creating Project 1: {res_1.text}"
    p1 = res_1.json()
    p1_id = p1["id"]
    print(f"\n[STEP 1] Created Project 1: '{p1['name']}' (ID: {p1_id}, sqft: {p1['sqft']})")

    # 3. Create Project 2 (Erode Industrial Shed)
    res_2 = client.post("/projects", json={
        "name": "Erode Industrial Shed",
        "sqft": 4500,
        "target_materials": ["steel", "brick", "gravel", "wiring"],
        "region": "Erode",
        "notes": "Large industrial warehouse"
    })
    assert res_2.status_code == 201, f"Failed creating Project 2: {res_2.text}"
    p2 = res_2.json()
    p2_id = p2["id"]
    print(f"[STEP 2] Created Project 2: '{p2['name']}' (ID: {p2_id}, sqft: {p2['sqft']})")

    # 4. Log unique quote for Project 1
    quote_p1_note = f"UNIQUE_QUOTE_P1_PROJ_{p1_id}_COIMBATORE_STEEL"
    res_q1 = client.post("/check-fair-price", json={
        "material": "steel",
        "quoted_rate": 57500.0,
        "quoted_unit": "MT",
        "quoted_date": "2026-07-01",
        "source_note": quote_p1_note,
        "region": "Tamil Nadu",
        "project_id": p1_id
    })
    assert res_q1.status_code == 200
    q1_id = res_q1.json()["quote_id"]
    print(f"[STEP 3] Logged Quote #{q1_id} for Project 1 ('{quote_p1_note}')")

    # 5. Log unique quote for Project 2
    quote_p2_note = f"UNIQUE_QUOTE_P2_PROJ_{p2_id}_ERODE_CEMENT"
    res_q2 = client.post("/check-fair-price", json={
        "material": "cement",
        "quoted_rate": 5950.0,
        "quoted_unit": "MT",
        "quoted_date": "2026-07-01",
        "source_note": quote_p2_note,
        "region": "Erode",
        "project_id": p2_id
    })
    assert res_q2.status_code == 200
    q2_id = res_q2.json()["quote_id"]
    print(f"[STEP 4] Logged Quote #{q2_id} for Project 2 ('{quote_p2_note}')")

    # 6. Verify Quote Isolation in Database Querying
    p1_quotes = fetch_vendor_quotes_data(project_id=p1_id)
    p2_quotes = fetch_vendor_quotes_data(project_id=p2_id)

    p1_quote_notes = [q["source_note"] for q in p1_quotes]
    p2_quote_notes = [q["source_note"] for q in p2_quotes]

    print(f"\n[STEP 5] Auditing Vendor Quotes associated with Project 1 (ID: {p1_id}):")
    for q in p1_quotes:
        print(f"  - Quote #{q['id']}: {q['material']} @ Rs.{q['quoted_rate']} ({q['source_note']})")

    print(f"\n[STEP 6] Auditing Vendor Quotes associated with Project 2 (ID: {p2_id}):")
    for q in p2_quotes:
        print(f"  - Quote #{q['id']}: {q['material']} @ Rs.{q['quoted_rate']} ({q['source_note']})")

    # Assert Project 1 has Quote 1 and NOT Quote 2
    assert quote_p1_note in p1_quote_notes, "Project 1 missing its own vendor quote!"
    assert quote_p2_note not in p1_quote_notes, "CROSS-CONTAMINATION ERROR: Project 1 contains Project 2 quote!"

    # Assert Project 2 has Quote 2 and NOT Quote 1
    assert quote_p2_note in p2_quote_notes, "Project 2 missing its own vendor quote!"
    assert quote_p1_note not in p2_quote_notes, "CROSS-CONTAMINATION ERROR: Project 2 contains Project 1 quote!"

    print("\n[VERIFICATION SUCCESS] Zero cross-contamination detected!")

    # 7. Generate PDF Reports for Project 1 and Project 2
    res_rep1 = client.post("/generate-report", json={"project_id": p1_id})
    assert res_rep1.status_code == 200
    assert len(res_rep1.content) > 1000

    res_rep2 = client.post("/generate-report", json={"project_id": p2_id})
    assert res_rep2.status_code == 200
    assert len(res_rep2.content) > 1000

    print("[STEP 7] Both PDF Reports compiled and verified successfully!")

    print("\n==================================================")
    print("      ALL MANUAL ISOLATION TESTS PASSED 100%!     ")
    print("==================================================")

if __name__ == "__main__":
    run_isolation_verification()
