from locust import User, task, constant, HttpUser, between
from locust.exception import LocustError, StopUser

class PetstoreUser(HttpUser):
    host = f"https://petstore.swagger.io/v2"
    wait_time = between(1, 2)
    create_user_payload = {
    "username": "reyadhassan",
    "firstName": "Reyad",
    "lastName": "Hassan",
    "email": "reyad@pathao.com",
    "password": "123456",
    "phone": "01843547674",
    "userStatus": 1
    }
    headers = {
            "Content-Type": "application/json"
        }
    
    def on_start(self):
        self.request_count = 0

    @task
    def CreateUser(self):
        self.client.post(f"/user", json=self.create_user_payload, headers=self.headers)
        print("Creating Users")

        self.request_count += 1
        if self.request_count >= 2:  # Replace 2 with `n` for n requests
            raise StopUser()

        
    