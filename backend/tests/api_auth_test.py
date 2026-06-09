import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

PROTECTED_ROUTES = [
    "/api/v1/demand/current",
    "/api/v1/faults/active",
    "/api/v1/transformers/health",
    "/api/v1/theft/suspects"
]

def test_auth_bypasses():
    print("Starting API Authentication Bypass Audit...")
    client = TestClient(app)
    failed = False
    
    for route in PROTECTED_ROUTES:
        try:
            response = client.get(route)
            if response.status_code in [401, 403]:
                print(f"PASSED (Secured): {route} returned {response.status_code}")
            else:
                print(f"FAILED (Vulnerable!): {route} returned {response.status_code} without auth token!")
                failed = True
        except Exception as e:
            print(f"FAILED (Exception): {route} threw an exception: {e}")
            failed = True
            
    if failed:
        sys.exit(1)

if __name__ == "__main__":
    test_auth_bypasses()
