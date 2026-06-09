import os
import sys
import httpx
from jose import jwt
from datetime import datetime, timedelta, timezone

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def get_token():
    payload = {
        "sub": "6a1fc3f31c8c218614ff5782",
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)

def main():
    token = get_token()
    print("Generated token:", token)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    url = "http://localhost:8000/api/forecast/dashboard"
    print(f"Querying real server endpoint: {url}")
    try:
        response = httpx.get(url, headers=headers, timeout=10.0)
        print("Status Code:", response.status_code)
        print("Response headers:", dict(response.headers))
        try:
            print("Response JSON:", response.json())
        except Exception as e:
            print("Response is not JSON:", e)
            print("Raw response content:", response.content)
    except Exception as e:
        print("HTTP request failed:", e)

if __name__ == "__main__":
    main()
