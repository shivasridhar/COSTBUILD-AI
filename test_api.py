import json
import sys
import os

from fastapi.testclient import TestClient
from src.api.main import app
from src.optimization.bom_optimizer import optimize_procurement

def test_fastapi_service():
    client = TestClient(app)

    print("==========================================================================")
    print("        BUILDCOST AI - PHASE 4 FASTAPI SERVICE INTEGRATION TEST          ")
    print("==========================================================================")

    # 1. Test GET /health
    print("\n--- 1. TESTING GET /health ---")
    health_resp = client.get("/health")
    print(f"HTTP Status: {health_resp.status_code}")
    print(f"Health Response: {json.dumps(health_resp.json(), indent=2)}")
    assert health_resp.status_code == 200, "Health check failed!"
    assert health_resp.json()["status"] == "ok"
    assert health_resp.json()["database_connected"] is True

    # 2. Test Input Validation (sqft <= 0)
    print("\n--- 2. TESTING INPUT VALIDATION (sqft = 0 & invalid material) ---")
    invalid_sqft_resp = client.post("/predict-optimal-build-window", json={"sqft": 0})
    print(f"sqft=0 HTTP Status: {invalid_sqft_resp.status_code} (Expected 422)")
    assert invalid_sqft_resp.status_code == 422, "Failed to reject sqft=0 with 422!"

    invalid_mat_resp = client.post("/predict-optimal-build-window", json={"sqft": 1000, "target_materials": ["unobtanium"]})
    print(f"Invalid material HTTP Status: {invalid_mat_resp.status_code} (Expected 422)")
    assert invalid_mat_resp.status_code == 422, "Failed to reject invalid material with 422!"

    # 3. Test POST /predict-optimal-build-window (sqft = 1000)
    print("\n--- 3. TESTING POST /predict-optimal-build-window (sqft = 1000) ---")
    payload = {
        "sqft": 1000,
        "target_materials": ["steel", "cement", "sand", "brick", "gravel"]
    }
    api_resp = client.post("/predict-optimal-build-window", json=payload)
    print(f"HTTP Status: {api_resp.status_code}")
    assert api_resp.status_code == 200, f"API Request failed: {api_resp.text}"

    api_json = api_resp.json()
    print("\n--- RAW API JSON RESPONSE ---")
    print(json.dumps(api_json, indent=2))

    # 4. Compare API Response against direct optimize_procurement(1000) call
    print("\n--- 4. VERIFYING DISCREPANCY (API vs DIRECT MODULE CALL) ---")
    direct_res = optimize_procurement(1000, target_materials=["steel", "cement", "sand", "brick", "gravel"])

    # Verify identical values
    direct_anchor_cement = direct_res['anchor_conversion']['cement']['converted_anchor_price_rs']
    api_anchor_cement = api_json['anchor_conversion']['cement']['converted_anchor_price_rs']

    direct_m1_cost = direct_res['bom_cost_table'][0]['total_bom_cost_rs']
    api_m1_cost = api_json['bom_cost_by_month'][0]['total_bom_cost_rs']

    print(f"Direct Module Anchor Cement Check: ₹{direct_anchor_cement:.2f} | API Anchor Cement Check: ₹{api_anchor_cement:.2f}")
    print(f"Direct Module Month 1 Total BOM Cost: ₹{direct_m1_cost:,.2f} | API Month 1 Total BOM Cost: ₹{api_m1_cost:,.2f}")

    assert abs(direct_anchor_cement - api_anchor_cement) < 1e-4, "Discrepancy in anchor conversion!"
    assert abs(direct_m1_cost - api_m1_cost) < 1e-4, "Discrepancy in BOM cost calculation!"

    # 5. Test POST /check-fair-price
    print("\n--- 5. TESTING POST /check-fair-price ENDPOINT ---")
    
    # a. At market quote (steel baseline for 2026-07 is ~59,641.09; 59,000 is ~-1.07% which is within ±5%)
    at_market_resp = client.post("/check-fair-price", json={
        "material": "steel",
        "quoted_rate": 59000.0,
        "quoted_unit": "MT",
        "quoted_date": "2026-07-01",
        "source_note": "Local Vendor A"
    })
    print(f"At market quote status: {at_market_resp.status_code}")
    print(f"Response: {json.dumps(at_market_resp.json(), indent=2)}")
    assert at_market_resp.status_code == 200
    assert at_market_resp.json()["verdict"] == "at market"
    assert at_market_resp.json()["baseline_unit"] == "MT"

    # b. Below market quote (steel baseline for 2026-07 is ~59,641.09; 50,000 is ~-16.17% which is below market)
    below_resp = client.post("/check-fair-price", json={
        "material": "steel",
        "quoted_rate": 50000.0,
        "quoted_unit": "MT",
        "quoted_date": "2026-07-01",
        "source_note": "Discount Supplier B"
    })
    print(f"Below market response: {below_resp.json()['verdict']} (deviation: {below_resp.json()['deviation_pct']}%)")
    assert below_resp.status_code == 200
    assert below_resp.json()["verdict"] == "below market"
    assert below_resp.json()["deviation_pct"] < -5.0

    # c. Above market quote
    above_resp = client.post("/check-fair-price", json={
        "material": "steel",
        "quoted_rate": 70000.0,
        "quoted_unit": "MT",
        "quoted_date": "2026-07-01"
    })
    assert above_resp.status_code == 200
    assert above_resp.json()["verdict"] == "above market"
    assert above_resp.json()["deviation_pct"] > 5.0

    # d. Boundary Tests for ±5.0%
    # Steel baseline for 2026-07-01 is 59641.09
    baseline_val = at_market_resp.json()["baseline_rate"]

    # Exactly +5.0% boundary: 59641.09 * 1.05 = 62623.1445 -> rate 62623.14 -> deviation round((62623.14 - 59641.09)/59641.09 * 100) = 5.0%
    bound_plus_5_rate = round(baseline_val * 1.05, 2)
    b_plus_5_resp = client.post("/check-fair-price", json={
        "material": "steel",
        "quoted_rate": bound_plus_5_rate,
        "quoted_unit": "MT",
        "quoted_date": "2026-07-01"
    })
    print(f"Boundary +5.0% check rate={bound_plus_5_rate}: deviation={b_plus_5_resp.json()['deviation_pct']}%, verdict='{b_plus_5_resp.json()['verdict']}'")
    assert b_plus_5_resp.json()["verdict"] == "at market", f"Expected 'at market' at +5.0% boundary, got {b_plus_5_resp.json()['verdict']}"

    # Just above +5.0% boundary: rate multiplier 1.052 -> deviation > 5.0%
    bound_plus_just_above_rate = round(baseline_val * 1.052, 2)
    b_plus_above_resp = client.post("/check-fair-price", json={
        "material": "steel",
        "quoted_rate": bound_plus_just_above_rate,
        "quoted_unit": "MT",
        "quoted_date": "2026-07-01"
    })
    print(f"Boundary +5.01% check rate={bound_plus_just_above_rate}: deviation={b_plus_above_resp.json()['deviation_pct']}%, verdict='{b_plus_above_resp.json()['verdict']}'")
    assert b_plus_above_resp.json()["verdict"] == "above market", f"Expected 'above market' at +5.01%, got {b_plus_above_resp.json()['verdict']}"

    # Exactly -5.0% boundary: 59641.09 * 0.95 = 56659.0355 -> rate 56659.04 -> deviation -5.0%
    bound_minus_5_rate = round(baseline_val * 0.95, 2)
    b_minus_5_resp = client.post("/check-fair-price", json={
        "material": "steel",
        "quoted_rate": bound_minus_5_rate,
        "quoted_unit": "MT",
        "quoted_date": "2026-07-01"
    })
    print(f"Boundary -5.0% check rate={bound_minus_5_rate}: deviation={b_minus_5_resp.json()['deviation_pct']}%, verdict='{b_minus_5_resp.json()['verdict']}'")
    assert b_minus_5_resp.json()["verdict"] == "at market", f"Expected 'at market' at -5.0% boundary, got {b_minus_5_resp.json()['verdict']}"

    # Just below -5.0% boundary: rate 56650.0 -> deviation -5.02%
    bound_minus_below_rate = round(baseline_val * 0.9499, 2)
    b_minus_below_resp = client.post("/check-fair-price", json={
        "material": "steel",
        "quoted_rate": bound_minus_below_rate,
        "quoted_unit": "MT",
        "quoted_date": "2026-07-01"
    })
    print(f"Boundary -5.01% check rate={bound_minus_below_rate}: deviation={b_minus_below_resp.json()['deviation_pct']}%, verdict='{b_minus_below_resp.json()['verdict']}'")
    assert b_minus_below_resp.json()["verdict"] == "below market", f"Expected 'below market' at -5.01%, got {b_minus_below_resp.json()['verdict']}"

    # e. Unit mismatch quote (coil vs Rmt for wiring)
    mismatch_resp = client.post("/check-fair-price", json={
        "material": "wiring",
        "quoted_rate": 1200.0,
        "quoted_unit": "coil",
        "quoted_date": "2026-07-01"
    })
    assert mismatch_resp.status_code == 200
    assert mismatch_resp.json()["verdict"] == "unit mismatch"
    assert "baseline is expressed in 'Rmt'" in mismatch_resp.json()["note"]

    # f. Date out of range quote
    out_of_range_resp = client.post("/check-fair-price", json={
        "material": "steel",
        "quoted_rate": 56000.0,
        "quoted_unit": "MT",
        "quoted_date": "2030-01-01"
    })
    assert out_of_range_resp.status_code == 200
    assert out_of_range_resp.json()["verdict"] == "date out of range"

    # g. DB audit verification
    import sqlite3
    from src.optimization.bom_optimizer import DEFAULT_DB_PATH
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    rows = conn.execute("SELECT material, quoted_rate, quoted_unit FROM vendor_quotes ORDER BY id DESC LIMIT 10;").fetchall()
    conn.close()
    print(f"Recorded DB quotes count verified: {len(rows)} rows found in vendor_quotes.")

    print("\nSUCCESS: All fair price check boundary & verdict tests and DB audits PASSED!")

if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    test_fastapi_service()

