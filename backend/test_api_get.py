import requests

def test_api():
    try:
        # Authenticate first to get token
        login_url = "http://127.0.0.1:8000/api/v1/auth/login"
        payload = {"email": "sharmachintan585@gmail.com", "password": "Password123!"}
        
        r = requests.post(login_url, json=payload)
        print("Login status:", r.status_code)
        print("Login body:", r.json())
        if r.status_code != 200:
            # Try fallback admin credentials
            payload = {"email": "admin@guvnl.gov.in", "password": "Password123!"}
            r = requests.post(login_url, json=payload)
            print("Admin Login status:", r.status_code)
            print("Admin Login body:", r.json())
            
        token = r.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        suspicious_url = "http://127.0.0.1:8000/api/v1/theft/suspicious"
        r_susp = requests.get(suspicious_url, headers=headers)
        print("GET /api/v1/theft/suspicious status:", r_susp.status_code)
        data = r_susp.json()
        print("Number of items returned by API:", len(data))
        if data:
            print("First item:", data[0])
            
        dashboard_url = "http://127.0.0.1:8000/api/v1/theft/dashboard"
        r_dash = requests.get(dashboard_url, headers=headers)
        print("\nGET /api/v1/theft/dashboard status:", r_dash.status_code)
        print("Dashboard response:", r_dash.json())
        
    except Exception as e:
        print("API test failed:", e)

if __name__ == "__main__":
    test_api()
