"""
Verification script for BuildCost AI Authentication & Per-Engineer Project Scoping.

Tests:
1. Registration & login for User A and User B.
2. User A creates Project A.
3. User B creates Project B.
4. User A's GET /projects list contains ONLY Project A.
5. User B's GET /projects list contains ONLY Project B (User A's project is completely absent).
6. User B attempting to access User A's Project A (GET, PATCH, DELETE) receives 403 Forbidden.
7. Unauthenticated call to /predict-optimal-build-window succeeds without headers.
8. Invalid token to protected route returns 401 Unauthorized.
"""

import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"


def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    
    req_headers = {"Content-Type": "application/json", "Accept": "application/json"}
    req_headers.update(headers)

    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            status_code = resp.status
            content = resp.read().decode("utf-8")
            data = json.loads(content) if content else {}
            return status_code, data
    except urllib.error.HTTPError as e:
        status_code = e.code
        content = e.read().decode("utf-8")
        try:
            data = json.loads(content)
        except Exception:
            data = {"detail": content}
        return status_code, data


def run_tests():
    print("==================================================================")
    print("STARTING AUTHENTICATION & PROJECT ISOLATION VERIFICATION TESTS")
    print("==================================================================")

    import time
    ts = time.time_ns()
    user_a_email = f"user_a_{ts}@buildcost.ai"
    user_b_email = f"user_b_{ts}@buildcost.ai"

    # 1. Register User A
    status, res = make_request(f"{BASE_URL}/auth/register", method="POST", data={
        "email": user_a_email,
        "password": "PasswordA123!",
        "name": "Engineer A"
    })
    assert status == 201, f"User A registration failed: {status} {res}"
    token_a = res["access_token"]
    user_a_id = res["user"]["id"]
    print(f"[PASS] Registered User A (ID: {user_a_id}, Email: {user_a_email})")

    # 2. Register User B
    status, res = make_request(f"{BASE_URL}/auth/register", method="POST", data={
        "email": user_b_email,
        "password": "PasswordB123!",
        "name": "Engineer B"
    })
    assert status == 201, f"User B registration failed: {status} {res}"
    token_b = res["access_token"]
    user_b_id = res["user"]["id"]
    print(f"[PASS] Registered User B (ID: {user_b_id}, Email: {user_b_email})")

    # 3. Test /auth/me for User A
    status, res = make_request(f"{BASE_URL}/auth/me", method="GET", headers={"Authorization": f"Bearer {token_a}"})
    assert status == 200 and res["id"] == user_a_id, f"GET /auth/me failed for User A: {status} {res}"
    print(f"[PASS] Verified GET /auth/me for User A")

    # 4. User A Creates Project A
    status, project_a = make_request(f"{BASE_URL}/projects", method="POST", data={
        "name": "User A — Coimbatore Villa",
        "sqft": 2000,
        "target_materials": ["steel", "cement", "sand"],
        "region": "Tamil Nadu"
    }, headers={"Authorization": f"Bearer {token_a}"})
    assert status == 201, f"User A failed to create project: {status} {project_a}"
    project_a_id = project_a["id"]
    print(f"[PASS] User A created Project A (ID: {project_a_id}, Name: '{project_a['name']}')")

    # 5. User B Creates Project B
    status, project_b = make_request(f"{BASE_URL}/projects", method="POST", data={
        "name": "User B — Chennai Tower",
        "sqft": 5000,
        "target_materials": ["steel", "cement", "wiring"],
        "region": "Tamil Nadu"
    }, headers={"Authorization": f"Bearer {token_b}"})
    assert status == 201, f"User B failed to create project: {status} {project_b}"
    project_b_id = project_b["id"]
    print(f"[PASS] User B created Project B (ID: {project_b_id}, Name: '{project_b['name']}')")

    # 6. Check User A's GET /projects list
    status, projects_list_a = make_request(f"{BASE_URL}/projects", method="GET", headers={"Authorization": f"Bearer {token_a}"})
    assert status == 200, f"User A GET /projects failed: {status} {projects_list_a}"
    ids_a = [p["id"] for p in projects_list_a]
    assert project_a_id in ids_a, f"Project A should be in User A's project list. Got: {ids_a}"
    assert project_b_id not in ids_a, f"CRITICAL LEAK: Project B found in User A's list! Got: {ids_a}"
    print(f"[PASS] Verified GET /projects for User A returns ONLY User A's projects")

    # 7. Check User B's GET /projects list (CONFIRM LIST FILTERING SCOPING)
    status, projects_list_b = make_request(f"{BASE_URL}/projects", method="GET", headers={"Authorization": f"Bearer {token_b}"})
    assert status == 200, f"User B GET /projects failed: {status} {projects_list_b}"
    ids_b = [p["id"] for p in projects_list_b]
    assert project_b_id in ids_b, f"Project B should be in User B's project list. Got: {ids_b}"
    assert project_a_id not in ids_b, f"CRITICAL LEAK: Project A found in User B's list! Got: {ids_b}"
    print(f"[PASS] Verified GET /projects for User B returns ONLY User B's projects (User A's project absent)")

    # 8. User B attempts to GET User A's Project A -> Expect HTTP 403 Forbidden
    status, res = make_request(f"{BASE_URL}/projects/{project_a_id}", method="GET", headers={"Authorization": f"Bearer {token_b}"})
    assert status == 403, f"Expected 403 Forbidden when User B accesses Project A. Got status: {status}, res: {res}"
    print(f"[PASS] Confirmed GET /projects/{project_a_id} returns 403 Forbidden for User B")

    # 9. User B attempts to PATCH User A's Project A -> Expect HTTP 403 Forbidden
    status, res = make_request(f"{BASE_URL}/projects/{project_a_id}", method="PATCH", data={"name": "Hacked Name"}, headers={"Authorization": f"Bearer {token_b}"})
    assert status == 403, f"Expected 403 Forbidden when User B updates Project A. Got status: {status}, res: {res}"
    print(f"[PASS] Confirmed PATCH /projects/{project_a_id} returns 403 Forbidden for User B")

    # 10. User B attempts to DELETE User A's Project A -> Expect HTTP 403 Forbidden
    status, res = make_request(f"{BASE_URL}/projects/{project_a_id}", method="DELETE", headers={"Authorization": f"Bearer {token_b}"})
    assert status == 403, f"Expected 403 Forbidden when User B archives Project A. Got status: {status}, res: {res}"
    print(f"[PASS] Confirmed DELETE /projects/{project_a_id} returns 403 Forbidden for User B")

    # 11. User B attempts to get forecast for User A's Project A -> Expect HTTP 403 Forbidden
    status, res = make_request(f"{BASE_URL}/projects/{project_a_id}/forecast", method="GET", headers={"Authorization": f"Bearer {token_b}"})
    assert status == 403, f"Expected 403 Forbidden when User B requests forecast for Project A. Got status: {status}, res: {res}"
    print(f"[PASS] Confirmed GET /projects/{project_a_id}/forecast returns 403 Forbidden for User B")

    # 12. Test Stateless /predict-optimal-build-window without any Authorization header
    status, res = make_request(f"{BASE_URL}/predict-optimal-build-window", method="POST", data={
        "sqft": 1200,
        "target_materials": ["steel", "cement"]
    })
    assert status == 200, f"Stateless forecast should work unauthenticated. Got status: {status}, res: {res}"
    assert "recommendation" in res and "bom_cost_by_month" in res, "Invalid forecast output structure"
    print(f"[PASS] Confirmed unauthenticated POST /predict-optimal-build-window succeeds without headers")

    # 13. Test Unauthenticated Access to /projects -> Expect 401 Unauthorized
    status, res = make_request(f"{BASE_URL}/projects", method="GET")
    assert status == 401, f"Expected 401 Unauthorized for unauthenticated GET /projects. Got: {status}"
    print(f"[PASS] Confirmed unauthenticated GET /projects returns 401 Unauthorized")

    # 14. Test Malformed Token -> Expect 401 Unauthorized
    status, res = make_request(f"{BASE_URL}/auth/me", method="GET", headers={"Authorization": "Bearer malformed.token.string"})
    assert status == 401 and "Invalid" in res.get("detail", ""), f"Expected 401 for malformed token. Got status: {status}, res: {res}"
    print(f"[PASS] Confirmed malformed JWT token returns 401 Unauthorized with clean error detail")

    # 15. Test Expired Token -> Expect 401 Unauthorized
    import jwt, datetime
    expired_token = jwt.encode({"sub": "999", "exp": datetime.datetime.utcnow() - datetime.timedelta(hours=1)}, "buildcost-secret-key-change-in-production-2026", algorithm="HS256")
    status, res = make_request(f"{BASE_URL}/auth/me", method="GET", headers={"Authorization": f"Bearer {expired_token}"})
    assert status == 401 and "expired" in res.get("detail", "").lower(), f"Expected 401 for expired token. Got status: {status}, res: {res}"
    print(f"[PASS] Confirmed expired JWT token returns 401 Unauthorized with clean expiration detail")

    print("==================================================================")
    print("ALL AUTHENTICATION & PROJECT ISOLATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================================")


if __name__ == "__main__":
    run_tests()
