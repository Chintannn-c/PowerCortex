import os
import sys

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.core.dependencies import get_current_user

# Mock dependency get_current_user to bypass authentication
app.dependency_overrides[get_current_user] = lambda: {"_id": "60d5ec4b9b1d8b2d888f4e12", "username": "test_user", "email": "test@example.com"}

print("Hitting /api/forecast/dashboard with TestClient lifespan...")
try:
    with TestClient(app) as client:
        response = client.get("/api/forecast/dashboard")
        print("Status Code:", response.status_code)
        print("Response JSON:")
        print(response.json())
except Exception as e:
    print("Failed during request:", e)
