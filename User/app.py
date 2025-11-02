from locust import task, between
from locust.contrib.fasthttp import FastHttpUser
from locust.exception import StopUser


class PetstoreUser(FastHttpUser):
    host = "https://petstore.swagger.io/v2"
    wait_time = between(1, 2)

    # request body and headers
    create_user_payload = {
        "username": "reyadhassan",
        "firstName": "Reyad",
        "lastName": "Hassan",
        "email": "reyad@pathao.com",
        "password": "123456",
        "phone": "01843547674",
        "userStatus": 1
    }

    headers = {"Content-Type": "application/json"}

    def on_start(self):
        """Executed once per user when load test begins."""
        self.request_count = 0
        print("[START] New user started...")

    @task
    def create_user(self):
        """Task to create a user on Petstore"""
        with self.client.post(
            "/user",
            json=self.create_user_payload,
            headers=self.headers,
            catch_response=True
        ) as response:

            if response.status_code == 200:
                response.success()
                print("[SUCCESS] User created")
            else:
                response.failure(f"[FAILED] Status: {response.status_code} | {response.text}")

        self.request_count += 1

        # Stop after n requests
        if self.request_count >= 2:
            print("[STOP] User completed required requests")
            raise StopUser()
