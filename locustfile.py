from locust import task, between
from locust.contrib.fasthttp import FastHttpUser
from locust.exception import StopUser
from locust import LoadTestShape
import os

try:
    from dotenv import load_dotenv
    load_dotenv()  # safe: will just load .env if present
except ImportError:
    pass  # in Docker, dotenv may not be installed


class Sancus(FastHttpUser):
    """
    Locust User class that makes API calls against Sancus.
    Uses FastHttpUser for high-performance HTTP requests.
    """
    host = os.environ.get("API_HOST")
    # wait_time = between(1, 2)  # Wait between requests
    wait_time = between(0, 0)
    headers = {
        "Content-Type": "application/json",
        "id": os.environ.get("USER_ID"),
        "uuid": os.environ.get("UUID"),
        "number": os.environ.get("NUMBER"),
        "city_id": os.environ.get("CITY_ID"),
        "country_id": os.environ.get("COUNTRY_ID"),
        "user_type": os.environ.get("USER_TYPE")
    }

    params = {"lang": os.environ.get("LANG"), "include_offer_summary": "true"}


    # def on_start(self):
    #     """Executed once per simulated user when the load test starts"""
    #     self.request_count = 0

    @task
    def getPocketById(self):
        """Fetches a sancus pocket user"""

        with self.client.get(
            "/pocket", params=self.params, headers=self.headers, catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
                # print(f"[SUCCESS] Status Code: {response.status_code} --- Get User Pocket success")
            else:
                response.failure(f"[FAILED] Status Code: {response.status_code} | Response Body:{response.text}")

        # Stop after 2 requests per user
        # self.request_count += 1
        # if self.request_count >= 2:
        #     raise StopUser()


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
        {"duration": 60, "users": 100, "spawn_rate": 10},    # 50 users in 10 sec
        {"duration": 60, "users": 250, "spawn_rate": 20},  # At 40sec mark
        {"duration": 120, "users": 1000, "spawn_rate": 200}, # Big spike at 60 sec
        {"duration": 120, "users": 2000, "spawn_rate": 200}, # Big spike at 70 sec
        {"duration": 120, "users": 2500, "spawn_rate": 100},  # Decrease traffic
        {"duration": 300, "users": 5000, "spawn_rate": 500},  # Another spike
    ]

    def tick(self):
        """Defines how many users exist at each timestamp (in seconds)."""
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]

        return None  # Done → Locust stops load test
