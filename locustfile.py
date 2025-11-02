from locust import task, between
from locust.contrib.fasthttp import FastHttpUser
from locust.exception import StopUser
from locust import LoadTestShape

from utils.user_payload import new_user_payload


class PetstoreUser(FastHttpUser):
    """
    Locust User class that makes API calls against PetStore.
    Uses FastHttpUser for high-performance HTTP requests.
    """
    host = "https://petstore.swagger.io/v2"
    wait_time = between(1, 2)  # Wait between requests
    headers = {"Content-Type": "application/json"}

    def on_start(self):
        """Executed once per simulated user when the load test starts"""
        self.request_count = 0

    @task
    def create_user(self):
        """Creates a PetStore user"""
        payload = new_user_payload()

        with self.client.post(
            "/user", json=payload, headers=self.headers, catch_response=True
        ) as response:

            # Custom success/failure logging
            if response.status_code == 200:
                response.success()
                print(f"[SUCCESS] User created: {payload['username']}")
            else:
                response.failure(f"[FAILED] {response.status_code} | {response.text}")

        # Stop after 2 requests per user
        self.request_count += 1
        if self.request_count >= 2:
            raise StopUser()


class SpikeLoadShape(LoadTestShape):
    """
    Defines a spike load pattern with multiple stages:

    Stage 1: Rapid ramp to 50 users over first 10 seconds
    Stage 2: Traffic jump to 200 users for 30 seconds
    Stage 3: Huge spike to 500 users immediately
    Stage 4: Drop to 100 users for 15 seconds
    Stage 5: Spike again to 400 users for 20 seconds
    """

    stages = [
        {"duration": 10, "users": 50, "spawn_rate": 5},    # 50 users in 10 sec
        {"duration": 40, "users": 200, "spawn_rate": 20},  # At 40sec mark
        {"duration": 60, "users": 1000, "spawn_rate": 200}, # Big spike at 60 sec
        {"duration": 70, "users": 700, "spawn_rate": 100}, # Big spike at 70 sec
        {"duration": 85, "users": 100, "spawn_rate": 10},  # Decrease traffic
        {"duration": 95, "users": 400, "spawn_rate": 50},  # Another spike
    ]

    def tick(self):
        """Defines how many users exist at each timestamp (in seconds)."""
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]

        return None  # Done → Locust stops load test
