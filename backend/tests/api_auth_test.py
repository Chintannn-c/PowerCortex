import httpx
import asyncio

BASE_URL = "http://127.0.0.1:8000/api/v1"

PROTECTED_ROUTES = [
    "/demand/current",
    "/faults/active",
    "/transformers/health",
    "/theft/suspects"
]

async def test_auth_bypasses():
    """
    Test suite to ensure that accessing protected routes without
    a JWT returns a strict 401 Unauthorized or 403 Forbidden.
    """
    print("🚀 Starting API Authentication Bypass Audit...")
    async with httpx.AsyncClient() as client:
        for route in PROTECTED_ROUTES:
            url = f"{BASE_URL}{route}"
            try:
                response = await client.get(url)
                if response.status_code in [401, 403]:
                    print(f"✅ PASSED (Secured): {route} returned {response.status_code}")
                else:
                    print(f"❌ FAILED (Vulnerable!): {route} returned {response.status_code} without auth token!")
            except httpx.ConnectError:
                print(f"⚠️ SKIPPED: Could not connect to {url}. Is the server running?")

if __name__ == "__main__":
    asyncio.run(test_auth_bypasses())
