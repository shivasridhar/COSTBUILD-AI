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

    print("\nSUCCESS: API Response matches direct module output IDENTICALLY to 0 decimal places!")

if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    test_fastapi_service()
