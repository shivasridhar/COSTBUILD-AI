"""
Backend automated verification test for BuildCost AI Persistent Projects.
"""

import sys
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from src.api.main import app
from migrate_add_projects import run_migration

def test_projects_backend():
    print("--- Running Migration ---")
    run_migration()

    client = TestClient(app)

    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[PASS] Health Check")

    # 2. Create Project A (Priya — Coimbatore House)
    proj_a_data = {
        "name": "Priya — Coimbatore House",
        "sqft": 1800,
        "target_materials": ["steel", "cement", "sand", "wiring"],
        "region": "Tamil Nadu",
        "notes": "Residential house build in Coimbatore"
    }
    res_a = client.post("/projects", json=proj_a_data)
    assert res_a.status_code == 201, f"Create Project A failed: {res_a.text}"
    proj_a = res_a.json()
    assert proj_a["id"] is not None
    assert proj_a["name"] == proj_a_data["name"]
    assert proj_a["status"] == "planning"
    print(f"[PASS] Created Project A (ID: {proj_a['id']})")

    # 3. Create Project B (Erode Industrial Site)
    proj_b_data = {
        "name": "Erode Industrial Site",
        "sqft": 3500,
        "target_materials": ["steel", "cement", "gravel", "brick"],
        "region": "Erode",
        "notes": "Factory warehouse"
    }
    res_b = client.post("/projects", json=proj_b_data)
    assert res_b.status_code == 201, f"Create Project B failed: {res_b.text}"
    proj_b = res_b.json()
    assert proj_b["id"] is not None
    print(f"[PASS] Created Project B (ID: {proj_b['id']})")

    # 4. List projects
    res_list = client.get("/projects")
    assert res_list.status_code == 200
    projects_list = res_list.json()
    assert len(projects_list) >= 2
    print(f"[PASS] Listed {len(projects_list)} projects")

    # 5. Fetch single project
    res_get = client.get(f"/projects/{proj_a['id']}")
    assert res_get.status_code == 200
    assert res_get.json()["name"] == proj_a_data["name"]
    print("[PASS] Get single project details")

    # 6. Update Project A (PATCH)
    res_patch = client.patch(f"/projects/{proj_a['id']}", json={"status": "in_progress", "notes": "Construction started"})
    assert res_patch.status_code == 200
    assert res_patch.json()["status"] == "in_progress"
    assert res_patch.json()["notes"] == "Construction started"
    print("[PASS] Update project (status & notes)")

    # 7. Get forecast for Project A
    res_forecast_a = client.get(f"/projects/{proj_a['id']}/forecast")
    assert res_forecast_a.status_code == 200
    forecast_a = res_forecast_a.json()
    assert "recommendation" in forecast_a
    assert forecast_a["recommendation"]["sqft"] == 1800
    print("[PASS] Get project forecast for Project A")

    # 8. Log vendor quote for Project A
    quote_a = {
        "material": "steel",
        "quoted_rate": 57000.0,
        "quoted_unit": "MT",
        "quoted_date": "2026-07-01",
        "source_note": "TMT Steel Supplier Coimbatore",
        "region": "Tamil Nadu",
        "project_id": proj_a["id"]
    }
    res_quote_a = client.post("/check-fair-price", json=quote_a)
    assert res_quote_a.status_code == 200
    quote_a_id = res_quote_a.json()["quote_id"]
    assert quote_a_id is not None
    print(f"[PASS] Logged vendor quote for Project A (Quote ID: {quote_a_id})")

    # 9. Log vendor quote for Project B
    quote_b = {
        "material": "cement",
        "quoted_rate": 5900.0,
        "quoted_unit": "MT",
        "quoted_date": "2026-07-01",
        "source_note": "Ultratech Erode Distributor",
        "region": "Erode",
        "project_id": proj_b["id"]
    }
    res_quote_b = client.post("/check-fair-price", json=quote_b)
    assert res_quote_b.status_code == 200
    quote_b_id = res_quote_b.json()["quote_id"]
    assert quote_b_id is not None
    print(f"[PASS] Logged vendor quote for Project B (Quote ID: {quote_b_id})")

    # 10. Generate PDF Report for Project A
    res_report_a = client.post("/generate-report", json={"project_id": proj_a["id"]})
    assert res_report_a.status_code == 200
    assert res_report_a.headers["content-type"] == "application/pdf"
    assert len(res_report_a.content) > 1000
    print("[PASS] PDF Report generated for Project A")

    # 11. Soft Delete (Archive) Project B
    res_del_b = client.delete(f"/projects/{proj_b['id']}")
    assert res_del_b.status_code == 200
    assert res_del_b.json()["status"] == "archived"
    print("[PASS] Soft deleted (archived) Project B")

    print("\n==================================================")
    print("      ALL BACKEND PROJECT TESTS PASSED!          ")
    print("==================================================")

if __name__ == "__main__":
    test_projects_backend()
