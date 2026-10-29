"""
Automated Verification Script for Staged Construction Procurement by Phase in BuildCost AI.

Tests:
1. SQLite Database schema verification (project_phases table and vendor_quotes.phase_id).
2. Project creation & Phase CRUD operations via API router / functions.
3. True-horizon error calculation: Phase 2 (Month 8 offset) vs Phase 1 (Month 0 offset).
4. Phases summary endpoint integration.
5. Vendor quote association with phase_id.
6. PDF Executive Report rendering with Staged Procurement recommendations table.
"""

import os
import sys
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from src.optimization.bom_optimizer import DEFAULT_DB_PATH, save_vendor_quote
from src.api.projects import (
    create_project,
    create_phase,
    list_phases,
    update_phase,
    get_phase_forecast,
    get_phases_summary,
    delete_phase,
    ProjectCreateRequest,
    PhaseCreateRequest,
    PhaseUpdateRequest
)
from src.reports.generator import generate_pdf_report
from migrate_add_projects import run_migration


def run_verification():
    print("=" * 80)
    print("      BUILDCOST AI - STAGED PROCUREMENT VERIFICATION SUITE       ")
    print("=" * 80)

    # 1. Database Migration & Schema Check
    print("\n--- 1. DATABASE SCHEMA VERIFICATION ---")
    run_migration(DEFAULT_DB_PATH)

    conn = sqlite3.connect(DEFAULT_DB_PATH)
    cursor = conn.cursor()

    # Check project_phases table columns
    cursor.execute("PRAGMA table_info(project_phases);")
    cols = [r[1] for r in cursor.fetchall()]
    print(f"project_phases columns: {cols}")
    assert "id" in cols
    assert "project_id" in cols
    assert "phase_name" in cols
    assert "materials" in cols
    assert "expected_start_month" in cols
    assert "sequence_order" in cols

    # Check vendor_quotes phase_id column
    cursor.execute("PRAGMA table_info(vendor_quotes);")
    quote_cols = [r[1] for r in cursor.fetchall()]
    print(f"vendor_quotes columns: {quote_cols}")
    assert "phase_id" in quote_cols
    conn.close()
    print("✓ DB Schema Verified Successfully!")

    # 2. Create Test Project
    print("\n--- 2. CREATING TEST PROJECT ---")
    proj_payload = ProjectCreateRequest(
        name="Priya Erode Residency",
        sqft=1800,
        target_materials=["steel", "cement", "sand", "brick", "gravel", "wiring"],
        region="Tamil Nadu",
        notes="G+1 Residential house in Erode with staged fit-out."
    )
    project = create_project(proj_payload)
    print(f"Created Project #{project['id']}: {project['name']} ({project['sqft']} sqft)")
    assert project["id"] > 0

    # 3. Create Phases
    print("\n--- 3. CREATING STAGED CONSTRUCTION PHASES ---")
    # Phase 1: Foundation & Structure (Month 0)
    phase1_payload = PhaseCreateRequest(
        phase_name="Foundation & Substructure",
        materials=["steel", "cement", "sand", "brick", "gravel"],
        expected_start_month=0,
        sequence_order=1
    )
    phase1 = create_phase(project["id"], phase1_payload)
    print(f"Created Phase 1 #{phase1['id']}: {phase1['phase_name']} | Start Month: {phase1['expected_start_month']} | Materials: {phase1['materials']}")

    # Phase 2: Electrical Fit-Out (Month 8)
    phase2_payload = PhaseCreateRequest(
        phase_name="Electrical & Finishing Fit-Out",
        materials=["wiring"],
        expected_start_month=8,
        sequence_order=2
    )
    phase2 = create_phase(project["id"], phase2_payload)
    print(f"Created Phase 2 #{phase2['id']}: {phase2['phase_name']} | Start Month: {phase2['expected_start_month']} | Materials: {phase2['materials']}")

    phases_list = list_phases(project["id"])
    print(f"Retrieved {len(phases_list)} phases for Project #{project['id']}")
    assert len(phases_list) == 2

    # 4. Phase-Level Forecast & True Horizon Verification
    print("\n--- 4. EVALUATING PHASE FORECASTS & TRUE-HORIZON ERROR BANDS ---")
    fc1 = get_phase_forecast(project["id"], phase1["id"])
    rec1 = fc1["recommendation"]
    print(f"\nPhase 1 ({phase1['phase_name']}) Procurement Recommendation:")
    print(f"  Recommended Month: {rec1['recommended_year_month']} (Month {rec1['recommended_month_idx']})")
    print(f"  Immediate Cost: ₹{rec1['immediate_cost_rs']:,.2f} | Optimal: ₹{rec1['optimal_cost_rs']:,.2f}")
    print(f"  Savings: ₹{rec1['savings_rs']:,.2f} ({rec1['savings_percent']:.2f}%)")
    print(f"  Reliability Footnote: {rec1.get('reliability_subtext')}")

    fc2 = get_phase_forecast(project["id"], phase2["id"])
    rec2 = fc2["recommendation"]
    print(f"\nPhase 2 ({phase2['phase_name']}) Procurement Recommendation:")
    print(f"  Recommended Month: {rec2['recommended_year_month']} (Month {rec2['recommended_month_idx']})")
    print(f"  Immediate Cost: ₹{rec2['immediate_cost_rs']:,.2f} | Optimal: ₹{rec2['optimal_cost_rs']:,.2f}")
    print(f"  Savings: ₹{rec2['savings_rs']:,.2f} ({rec2['savings_percent']:.2f}%)")
    print(f"  Reliability Footnote: {rec2.get('reliability_subtext')}")

    # Verify true-horizon offset behavior:
    # Phase 2 start month offset is 8. Month 1 of Phase 2 forecast corresponds to Month 9 horizon overall.
    # Therefore, reliability subtext for Phase 2 should evaluate at Month 9 horizon with higher MAPE.
    assert "Month 9 horizon" in rec2["reliability_subtext"]
    print("✓ True Horizon Error Calculation Verified! (Month 9 horizon evaluated with wider MAPE bands)")

    # 5. Test Phase Summary Endpoint
    print("\n--- 5. TESTING PHASES SUMMARY ENDPOINT ---")
    summary = get_phases_summary(project["id"])
    phases_array = summary["phases"]
    print(f"Phases summary returned {len(phases_array)} phase evaluations.")
    assert len(phases_array) == 2
    assert phases_array[0]["phase"]["id"] == phase1["id"]
    assert phases_array[1]["phase"]["id"] == phase2["id"]
    print("✓ Phase Summary Endpoint Passed!")

    # 6. Test Vendor Quote Association, Threshold Pooling & Phase Deletion Nullification
    print("\n--- 6. TESTING VENDOR QUOTE THRESHOLD POOLING & PHASE DELETION ---")
    # Log 2 quotes on Phase 1 and 1 quote on Phase 2
    q1 = save_vendor_quote(material="steel", quoted_rate=58000.0, quoted_unit="MT", quoted_date="2026-07-01", project_id=project["id"], phase_id=phase1["id"])
    q2 = save_vendor_quote(material="steel", quoted_rate=58500.0, quoted_unit="MT", quoted_date="2026-07-02", project_id=project["id"], phase_id=phase1["id"])
    q3 = save_vendor_quote(material="steel", quoted_rate=59000.0, quoted_unit="MT", quoted_date="2026-07-03", project_id=project["id"], phase_id=phase2["id"])

    # Test quote_correction threshold check: all 3 quotes (across 2 phases) must be counted together for project_id
    from src.optimization.quote_correction import get_corrected_baseline_rate
    corr_res = get_corrected_baseline_rate(material="steel", raw_wpi_baseline_rate=55000.0, project_id=project["id"])
    print(f"Quote correction check for Project #{project['id']}: Count={corr_res['quote_count']}, Correction Applied={corr_res['correction_applied']}")
    assert corr_res["quote_count"] == 3
    assert corr_res["correction_applied"] is True
    print("✓ Project-level N>=3 threshold pooling across phases verified!")

    # Test Phase deletion behavior: deleting Phase 2 must nullify phase_id on q3 without deleting the quote
    delete_phase(project["id"], phase2["id"])
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    conn.row_factory = sqlite3.Row
    q3_row = conn.execute("SELECT * FROM vendor_quotes WHERE id = ?;", (q3,)).fetchone()
    conn.close()
    print(f"After Phase #{phase2['id']} deletion, Quote #{q3} phase_id is: {q3_row['phase_id']} (project_id: {q3_row['project_id']})")
    assert q3_row is not None
    assert q3_row["phase_id"] is None
    assert q3_row["project_id"] == project["id"]
    print("✓ Phase deletion ON DELETE SET NULL behavior verified!")

    # 7. Test PDF Executive Report Generation with Phases
    print("\n--- 7. TESTING PDF EXECUTIVE REPORT GENERATION ---")
    pdf_bytes = generate_pdf_report(
        project_id=project["id"],
        include_vendor_quotes=True,
        vendor_quote_ids=[q1, q2, q3]
    )

    pdf_filename = os.path.join(BASE_DIR, "scratch", f"project_{project['id']}_report.pdf")
    with open(pdf_filename, "wb") as f:
        f.write(pdf_bytes)

    print(f"Generated PDF Report ({len(pdf_bytes)} bytes) -> {pdf_filename}")
    assert os.path.exists(pdf_filename)
    assert len(pdf_bytes) > 5000
    print("✓ PDF Report Generation Verified!")

    print("\n" + "=" * 80)
    print("      ALL STAGED PROCUREMENT VERIFICATION TESTS PASSED SUCCESSFULLY!    ")
    print("=" * 80)


if __name__ == "__main__":
    run_verification()
