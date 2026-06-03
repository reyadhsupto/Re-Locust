from locust import SequentialTaskSet, task, between, User
from locust.contrib.fasthttp import FastHttpUser
from locust.exception import StopUser
from locust import LoadTestShape
import os
import random
import time
from clients import WebSocketClient, GraphQLClient

try:
    from dotenv import load_dotenv
    load_dotenv()  # safe: will just load .env if present
except ImportError:
    pass  # in Docker, dotenv may not be installed


class SancusFlow(SequentialTaskSet):
    """
    Executes sequential requests:
    1. Fetch user pocket → extract level
    2. Fetch deals list using extracted level
    3. Fetch Benefits list using extracted level
    """

    user_level = None

    @task
    def getPocketById(self):
        with self.client.get(
            "v1/pocket", params=self.user.params, headers=self.user.headers, catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
                try:
                    data = response.json()
                    self.user_level = data.get("level")
                except Exception as e:
                    response.failure(f"JSON parse failed: {e}")
            else:
                response.failure(f"Failed to fetch pocket=> status:{response.status_code} | body: {response.text}")

    @task
    def getDealsList(self):
        if not self.user_level:
            print("[WARN] user_level not found, skipping deals request")
            return

        with self.client.get(
            "v2/marketplace/deals",
            params={"level": self.user_level},
            headers=self.user.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to fetch deals=> status: {response.status_code} | body: {response.text}")

    @task
    def getBenefitsList(self):
        if not self.user_level:
            print("[WARN] user_level not found, skipping benefits request")
            return

        with self.client.get(
            "v1/marketplace/benefits",
            params={"level": self.user_level},
            headers=self.user.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to fetch deals=> status: {response.status_code} | body: {response.text}")


class Sancus(FastHttpUser):
    host = os.environ.get("API_HOST")
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

    tasks = [SancusFlow]  # <- attach the sequential flow


class AdspaceFlow(SequentialTaskSet):
    """
    Executes sequential requests:
    1. Fetch user ads (hard check ad existence)
    2. Create Analytics (ONLY if ad exists)
    """

    def on_start(self):
        self.ad_id = 322
        self.ad_found = False  # flow control flag


    @task
    def listUserAds(self):
        with self.client.get(
            f"/api/v1/advertisements/users/{os.environ.get('USER_ID')}",
            params=self.user.params,
            headers=self.user.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    ads = response.json().get("data", [])
                    matched_ad = next(
                        (ad for ad in ads if ad.get("id") == self.ad_id),
                        None
                    )
                    if matched_ad:
                        self.ad_found = True
                        response.success()
                    else:
                        response.failure(f"Ad {self.ad_id} not found in user ads")
                        raise StopUser(f"Stopping user: Ad {self.ad_id} not found in user ads")
                except Exception as e:
                    response.failure(f"JSON parse failed: {e}")
                    raise StopUser(f"Stopping user: JSON parse failed: {e}")
            else:
                response.failure(
                    f"Failed to fetch user ads => status:{response.status_code} | body: {response.text}"
                )
                raise StopUser("Stopping user: failed to fetch user ads")

    @task
    def createAnalytics(self):
        if not self.ad_found:
            self.interrupt(reschedule=True)
            return

        with self.client.put(
            f"/api/v1/analytics/{os.environ.get('USER_ID')}",
            headers={
                "Content-Type": "application/json",
                "Authorization": os.environ.get("AUTH")
            },
            json={
                "ad_id": self.ad_id,
                "action_type": "viewed"
            },
            catch_response=True
        ) as response:

            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Failed to create Analytics => status:{response.status_code},  | body: {response.text}"
                )

        # restart flow for next iteration
        self.interrupt(reschedule=True)


class Adspace(FastHttpUser):
    host = os.environ.get("API_HOST")
    wait_time = between(0, 0)

    # Reuse connections
    network_timeout = 5.0
    connection_timeout = 5.0

    tasks = [AdspaceFlow]  # <- attach the sequential flow

    headers = {
        "Content-Type": "application/json",
        "Authorization": os.environ.get("AUTH"),
        "Age": os.environ.get("AGE"),
        "City-ID": os.environ.get("CITY_ID"),
        "Country-ID": os.environ.get("COUNTRY_ID"),
        "Gender": os.environ.get("GENDER")
    }
    params = {"lat": os.environ.get("LAT"), "lon": os.environ.get("LON"), "page":os.environ.get("PAGE")}


class WebSocketFlow(SequentialTaskSet):
    """
    Example WebSocket test flow.
    Tests connection, sending messages, and receiving responses.
    """

    def on_start(self):
        """Initialize WebSocket client when user starts."""
        ws_url = os.environ.get("WS_URL", "wss://echo.websocket.org")
        
        # Optional: Add custom headers and query parameters
        ws_headers = {
            "Authorization": os.environ.get("WS_AUTH", ""),
            "User-Agent": "Locust-WebSocket-Client"
        }
        ws_params = {
            "token": os.environ.get("WS_TOKEN", ""),
            "user_id": os.environ.get("USER_ID", "")
        }
        
        # Create WebSocket client with headers and params
        self.ws_client = WebSocketClient(
            ws_url,
            headers=ws_headers,
            params=ws_params,
            pool_connections=True  # Enable connection pooling to reduce connections
        )
        
        # Connect to WebSocket server
        result = self.ws_client.connect()
        if result["status"] != "connected":
            raise StopUser(f"Failed to connect to WebSocket: {result.get('message')}")

    def on_stop(self):
        """Clean up WebSocket connection when user stops."""
        self.ws_client.disconnect()

    @task
    def send_message(self):
        """Send a message over WebSocket."""
        message = {
            "type": "message",
            "data": "Hello from Locust",
            "timestamp": time.time()
        }
        result = self.ws_client.send(message, name="send_message")
        if result["status"] == "error":
            raise StopUser(f"Failed to send WebSocket message: {result.get('message')}")

    @task
    def receive_message(self):
        """Receive a message from WebSocket."""
        result = self.ws_client.receive(name="receive_message", timeout=5)
        if result["status"] == "error":
            raise StopUser(f"Failed to receive WebSocket message: {result.get('message')}")
        elif result["status"] == "timeout":
            # Timeout is not critical, just log it
            pass


class WebSocketUser(User):
    """
    WebSocket load testing user.
    Use this instead of Adspace to test WebSocket endpoints.
    """
    host = os.environ.get("WS_HOST", "wss://echo.websocket.org")
    wait_time = between(1, 3)
    tasks = [WebSocketFlow]


class GraphQLFlow(SequentialTaskSet):
    """
    Example GraphQL test flow.
    Tests GraphQL queries and mutations.
    """

    def on_start(self):
        """Initialize GraphQL client when user starts."""
        gql_url = os.environ.get("GRAPHQL_URL", "https://api.example.com/graphql")
        
        # Optional: Add custom headers and query parameters
        gql_headers = {
            "Authorization": os.environ.get("GRAPHQL_AUTH", ""),
            "User-Agent": "Locust-GraphQL-Client"
        }
        gql_params = {
            "api_key": os.environ.get("GRAPHQL_API_KEY", ""),
            "version": os.environ.get("GRAPHQL_VERSION", "v1")
        }
        
        # Create GraphQL client with headers and params
        self.gql_client = GraphQLClient(
            gql_url,
            headers=gql_headers,
            params=gql_params
        )

    @task
    def execute_query(self):
        """Execute a GraphQL query."""
        query = """
            query {
                users {
                    id
                    name
                    email
                }
            }
        """
        result = self.gql_client.query(query, name="get_users")
        if result["status"] == "error":
            raise StopUser(f"GraphQL query failed: {result.get('message')}")

    @task
    def execute_mutation(self):
        """Execute a GraphQL mutation."""
        mutation = """
            mutation CreateUser($name: String!, $email: String!) {
                createUser(name: $name, email: $email) {
                    id
                    name
                    email
                }
            }
        """
        variables = {
            "name": f"User_{random.randint(1000, 9999)}",
            "email": f"user_{random.randint(1000, 9999)}@example.com"
        }
        result = self.gql_client.mutation(mutation, variables=variables, name="create_user")
        if result["status"] == "error":
            raise StopUser(f"GraphQL mutation failed: {result.get('message')}")


class GraphQLUser(User):
    """
    GraphQL load testing user.
    Use this to test GraphQL APIs.
    
    Run with: locust -f locustfile.py GraphQLUser
    """
    host = os.environ.get("GRAPHQL_HOST", "https://api.example.com")
    wait_time = between(1, 3)
    tasks = [GraphQLFlow]


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
        {"duration": 60, "users": 100, "spawn_rate": 1},    # 50 users in 10 sec
        {"duration": 60, "users": 250, "spawn_rate": 35},  # At 40sec mark
        {"duration": 60, "users": 500, "spawn_rate": 200}, # Big spike at 60 sec
        # {"duration": 120, "users": 2000, "spawn_rate": 200}, # Big spike at 70 sec
        # {"duration": 120, "users": 2500, "spawn_rate": 100},  # Decrease traffic
        # {"duration": 300, "users": 5000, "spawn_rate": 500},  # Another spike
    ]

    def tick(self):
        """Defines how many users exist at each timestamp (in seconds)."""
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]

        return None  # Done → Locust stops load test
