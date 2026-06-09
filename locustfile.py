from locust import HttpUser, task, between

class SmartGridUser(HttpUser):
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        # We assume the user has a valid login credential for load testing
        # Replace with valid credentials in the load testing environment
        response = self.client.post("/api/v1/auth/login", json={
            "email": "admin@powercortex.com",
            "password": "load_test_password"
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")

    @task(3)
    def get_current_demand(self):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.client.get("/api/v1/demand/current", headers=headers)

    @task(2)
    def get_active_faults(self):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.client.get("/api/v1/faults/active", headers=headers)

    @task(1)
    def get_transformer_health(self):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.client.get("/api/v1/transformers/health", headers=headers)
