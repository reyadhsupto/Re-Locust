# Locust Spike Load Testing - PetStore API

This project demonstrates **spike load testing** of the [PetStore Swagger API](https://petstore.swagger.io/) using **Locust**. It simulates realistic traffic patterns with multiple stages including sudden spikes and drops in users.

---

## Project Structure
```
locust-load-test/
│
├── locustfile.py            # Main Locust entry point
├── requirements.txt         # Dependencies
├── utils/
│   └── user_payload.py      # Responsible for generating request payloads
└── README.md
```

---

## Features

- Uses **FastHttpUser** for high-performance HTTP requests
- Supports **custom payloads** for API requests
- Implements a **spike load pattern** using `LoadTestShape`
- Stops users gracefully after a set number of requests
- Fully modular and scalable structure for adding more endpoints

---

## Spike Load Pattern

The test simulates the following stages:

| Stage | Duration (seconds) | Users | Spawn Rate |
|-------|------------------|-------|------------|
| 1     | 0–10             | 50    | 5/sec      |
| 2     | 10–40            | 200   | 20/sec     |
| 3     | 40–60            | 500   | 200/sec    |
| 4     | 60–75            | 100   | 10/sec     |
| 5     | 75–95            | 400   | 50/sec     |

> Users are ramped up according to `spawn_rate` to simulate real-world traffic spikes.

Following the defined pattern, Locust will automatically adjust the number of users as the test progresses.

The load test is designed to simulate realistic traffic patterns with multiple spikes and drops in user activity. The flow is as follows:

1. **Initial Ramp-Up:**  
   The test begins with **10 users**, spawning at a rate of **2 users per second** for the first 30 seconds. This simulates a slow start, allowing the system to warm up gradually.

2. **Moderate Load:**  
   Over the next 60 seconds, the user count increases to **50 users** at a spawn rate of **5 users per second**. This stage represents normal traffic conditions.

3. **Temporary Drop:**  
   After 90 seconds, the user count drops to **20 users** for 30 seconds. This simulates a brief period of low activity, such as off-peak usage.

4. **Traffic Spike:**  
   A sudden surge occurs, increasing the user count to **80 users** over 40 seconds. This stage tests the system’s ability to handle sudden high traffic spikes.

5. **Post-Spike Decline:**  
   Following the spike, the user count reduces to **30 users** over 20 seconds, simulating a recovery period as traffic subsides.

6. **Gradual Shutdown:**  
   Finally, the test enters a shutdown phase where the number of users gradually decreases to **0 users** over 30 seconds. This stage ensures that the system returns to an idle state smoothly without abrupt drops.

> This pattern helps evaluate the system’s stability and performance under varying load conditions, including sudden spikes and recovery periods. It is particularly useful for identifying bottlenecks and verifying scalability under real-world traffic scenarios.

---

## HTTP Request Flow
```bash
+----------------+ +--------------------+
| Locust User | POST | PetStore /user |
| (FastHttpUser) |--------->| API Endpoint |
+----------------+ +--------------------+
| ^
| |
|<-------- Response --------|
|
v
Check status code → Success / Failure
```
---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/locust-load-test.git
cd locust-load-test
```
### 2. Create a Python virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```
### 3. Install dependencies
```bash
pip install -r requirements.txt
```
### 4. Run Locust
```bash
locust
```
Open your browser and navigate to:
```bash
http://localhost:8089
```
From the Locust Web UI, you can start the test and monitor metrics such as response time, failures, and request per second.

---

## Customization
- Change host URL: Update host in PetstoreUser class in locustfile.py

- Add more endpoints: Create new tasks under PetstoreUser class

- Randomize users: Modify utils/user_payload.py to generate dynamic payloads

- Adjust load shape: Modify the stages list in SpikeLoadShape class

---

## Metrics
Locust Web UI provides real-time metrics:

- Requests per second

- Failure count and rate

- Response times (min, max, avg, percentile)

- Number of active users

---

## Best Practises

- Use FastHttpUser for high-concurrency tests

- Modularize payloads and tasks for better maintainability

- Use virtual environments to isolate dependencies

- Start with small user counts and ramp up gradually during testing

- Monitor system resources on the target API server

- Ensure API supports idempotency to avoid test conflicts (e.g., duplicate users)

- Log failures with detailed info for debugging

---

## References

- [Locust Official Documentation](https://docs.locust.io/) – Complete guide for Locust features, APIs, and load test setup.
- [Swagger PetStore API](https://petstore.swagger.io/) – Official demo API used for testing.
- [FastHttpUser for High Performance](https://docs.locust.io/en/stable/api.html#fast-http-user) – Documentation on FastHttpUser for concurrent load tests.
- [LoadTestShape for Custom Load Patterns](https://docs.locust.io/en/stable/writing-a-locustfile.html#custom-load-shapes) – Guide for creating custom user load patterns.
- [Virtual Environments in Python](https://docs.python.org/3/library/venv.html) – How to create isolated Python environments for dependencies.
- [Geven Library](https://www.gevent.org/) – Underlying library used by Locust for asynchronous HTTP requests.
