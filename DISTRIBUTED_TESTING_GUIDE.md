# Distributed Testing Guide

Complete guide for running Locust in distributed mode with multiple user types (WebSocket, GraphQL, HTTP).

---

## Table of Contents

1. [User Types](#user-types)
2. [Quick Start](#quick-start)
3. [Method 1: CLI Commands](#method-1-cli-commands)
4. [Method 2: Helper Script](#method-2-helper-script)
5. [Method 3: Docker Compose](#method-3-docker-compose)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)

---

## User Types

| User Type | Protocol | Best For | Features |
|-----------|----------|----------|----------|
| **WebSocketUser** | WebSocket (ws/wss) | Real-time APIs, Chat, Streaming | Connection pooling, custom headers, query params |
| **GraphQLUser** | HTTP/HTTPS | GraphQL APIs | Queries, mutations, batch operations |
| **Adspace** | HTTP/HTTPS | REST APIs | Standard HTTP requests |

---

## Quick Start

### Fastest Way (Docker Compose)
```bash
# WebSocket with 4 workers
LOCUST_USER=WebSocketUser docker compose up --scale worker=4

# GraphQL with 2 workers
LOCUST_USER=GraphQLUser docker compose up --scale worker=2

# HTTP with 3 workers
LOCUST_USER=Adspace docker compose up --scale worker=3
```

### Easiest Way (Helper Script)
```bash
chmod +x run_distributed_test.sh

./run_distributed_test.sh --user WebSocketUser --workers 4
./run_distributed_test.sh --user GraphQLUser --workers 2
./run_distributed_test.sh --user Adspace --workers 3
```

### Pure CLI (No Docker)
```bash
# Terminal 1 - Start Master
locust -f locustfile.py --master WebSocketUser

# Terminal 2+ - Start Workers
locust -f locustfile.py --worker --master-host=localhost
```

---

## Method 1: CLI Commands

### Single Machine (No Distribution)

Run a specific user type on one machine:

```bash
# WebSocket
locust -f locustfile.py WebSocketUser

# GraphQL
locust -f locustfile.py GraphQLUser

# HTTP
locust -f locustfile.py Adspace
```

Then open http://localhost:8089 in browser to configure and start the test.

### Distributed Mode (Multiple Machines/Terminals)

#### Step 1: Start Master Process

```bash
# Master with WebSocket
locust -f locustfile.py --master WebSocketUser

# Master with GraphQL
locust -f locustfile.py --master GraphQLUser

# Master with HTTP
locust -f locustfile.py --master Adspace
```

Master will run on http://localhost:8089

#### Step 2: Start Worker Processes

In separate terminals:

```bash
# Worker 1
locust -f locustfile.py --worker --master-host=localhost

# Worker 2
locust -f locustfile.py --worker --master-host=localhost

# Worker 3
locust -f locustfile.py --worker --master-host=localhost
```

#### For Remote Workers

Master machine:
```bash
locust -f locustfile.py --master WebSocketUser --host=0.0.0.0
```

Worker machines:
```bash
# Replace 192.168.1.100 with master IP
locust -f locustfile.py --worker --master-host=192.168.1.100
```

---

## Method 2: Helper Script

The `run_distributed_test.sh` script simplifies Docker Compose operations.

### Initial Setup

```bash
chmod +x run_distributed_test.sh
```

### Running Tests

```bash
# WebSocket with 4 workers
./run_distributed_test.sh --user WebSocketUser --workers 4

# GraphQL with 2 workers
./run_distributed_test.sh --user GraphQLUser --workers 2

# HTTP with 5 workers
./run_distributed_test.sh --user Adspace --workers 5

# Short form
./run_distributed_test.sh -u WebSocketUser -w 4
```

### Other Actions

```bash
# View live logs
./run_distributed_test.sh --action logs
./run_distributed_test.sh -a logs

# List running containers
./run_distributed_test.sh --action ps
./run_distributed_test.sh -a ps

# Restart containers
./run_distributed_test.sh --action restart
./run_distributed_test.sh -a restart

# Stop containers
./run_distributed_test.sh --action down
./run_distributed_test.sh -a down

# Clean everything (remove all containers and volumes)
./run_distributed_test.sh --action clean
./run_distributed_test.sh -a clean
```

### Script Help

```bash
./run_distributed_test.sh --help
./run_distributed_test.sh -h
```

---

## Method 3: Docker Compose

### Quick Commands

The `docker-compose.yml` is pre-configured with the `LOCUST_USER` environment variable.

#### Start Tests

```bash
# WebSocket with 4 workers
LOCUST_USER=WebSocketUser docker compose up --scale worker=4

# GraphQL with 2 workers
LOCUST_USER=GraphQLUser docker compose up --scale worker=2

# HTTP with 3 workers
LOCUST_USER=Adspace docker compose up --scale worker=3

# Default (WebSocketUser) with 4 workers
docker compose up --scale worker=4
```

#### View Logs

```bash
# All services
docker compose logs -f

# Only master
docker compose logs -f master

# Only workers
docker compose logs -f worker

# Last 100 lines
docker compose logs --tail 100
```

#### Manage Services

```bash
# Stop services (keep containers)
docker compose stop

# Stop and remove containers
docker compose down

# Stop and remove everything (including volumes)
docker compose down -v

# Pause services
docker compose pause

# Resume services
docker compose unpause

# List running services
docker compose ps
```

#### Scale Workers

```bash
# 2 workers
docker compose up --scale worker=2

# 8 workers
docker compose up --scale worker=8

# 16 workers
docker compose up --scale worker=16
```

#### Custom Configuration

```bash
# Background mode
LOCUST_USER=WebSocketUser docker compose up -d --scale worker=4

# Specific user type in background
LOCUST_USER=GraphQLUser docker compose up -d --scale worker=2

# Check status
docker compose ps
```

#### Rebuild Images

```bash
# Rebuild and start
LOCUST_USER=WebSocketUser docker compose up --build --scale worker=4
```

---

## Configuration

### Environment Variables

Create or update `.env` file in project root:

#### WebSocket Configuration

```env
# WebSocket Server
WS_URL=wss://your-server.com/ws
WS_AUTH=Bearer your-token
WS_HEADERS=Custom-Header:value,Another-Header:value2

# User info
USER_ID=12345
SESSION_ID=abc123xyz

# SSL/TLS
WS_VERIFY_SSL=true
```

#### GraphQL Configuration

```env
# GraphQL Server
GRAPHQL_URL=https://api.example.com/graphql
GRAPHQL_AUTH=Bearer your-token
GRAPHQL_API_KEY=your-api-key

# User info
USER_ID=user123
```

#### HTTP Configuration

```env
# REST API Server
API_HOST=https://api.example.com
AUTH=Bearer your-token
USER_ID=user123

# Request parameters
REQUEST_TIMEOUT=30
```

### Docker Compose Environment

The variables in `.env` are automatically loaded by Docker Compose.

To verify:
```bash
docker compose config | grep -A 20 "environment:"
```

---

## Usage Examples

### Scenario 1: Load Test WebSocket API

**Using Docker Compose (Recommended):**
```bash
LOCUST_USER=WebSocketUser docker compose up --scale worker=6
```

**Using Helper Script:**
```bash
./run_distributed_test.sh --user WebSocketUser --workers 6
```

**Using Pure CLI:**
```bash
# Terminal 1
locust -f locustfile.py --master WebSocketUser

# Terminal 2-6 (5 workers)
locust -f locustfile.py --worker --master-host=localhost
```

### Scenario 2: Load Test GraphQL API

**Using Docker Compose:**
```bash
LOCUST_USER=GraphQLUser docker compose up --scale worker=4
```

**Using Helper Script:**
```bash
./run_distributed_test.sh --user GraphQLUser --workers 4
```

### Scenario 3: Load Test REST API

**Using Docker Compose:**
```bash
LOCUST_USER=Adspace docker compose up --scale worker=3
```

**Using Helper Script:**
```bash
./run_distributed_test.sh --user Adspace --workers 3
```

### Scenario 4: Multiple Worker Count Scaling

```bash
# Start with 2 workers
LOCUST_USER=WebSocketUser docker compose up --scale worker=2

# In another terminal, scale to 8 workers
LOCUST_USER=WebSocketUser docker compose up --scale worker=8

# Scale down to 4 workers
LOCUST_USER=WebSocketUser docker compose up --scale worker=4
```

### Scenario 5: Remote Distributed Testing

Master (on 192.168.1.100):
```bash
locust -f locustfile.py --master WebSocketUser --bind 0.0.0.0:5557
```

Workers (on other machines):
```bash
locust -f locustfile.py --worker --master-host=192.168.1.100 --master-port=5557
```

---

## Accessing the Web UI

After starting a test, open in browser:

```
http://localhost:8089
```

From the UI, you can:
- Configure number of users
- Set ramp-up rate
- Start/stop test
- View real-time statistics
- Download results

---

## Monitoring and Logs

### Docker Compose Logs

```bash
# Live logs from all services
docker compose logs -f

# Logs from last 50 lines
docker compose logs --tail 50

# Logs from specific time
docker compose logs --since 5m

# Follow specific service
docker compose logs -f master
```

### Statistics

The test reports display:
- Total requests and failures
- Request response times (min, max, average)
- Requests per second (RPS)
- Percentage of successful requests
- Distribution of response times

### Performance Tuning

If you need more load:
- Increase worker count: `--scale worker=16`
- Increase users in Web UI
- Increase spawn rate in Web UI

If services are struggling:
- Reduce worker count
- Reduce user count
- Check `.env` configuration

---

## Troubleshooting

### Issue: Connection Refused

**Error:** `Connection refused` or `Cannot connect to master`

**Solutions:**
```bash
# Check master is running
docker compose ps

# Check port 8089 is accessible
lsof -i :8089

# For CLI, ensure master started before workers
```

### Issue: Workers Not Connecting

**Error:** `Worker connect timeout` or workers stuck at "waiting"

**Solutions:**
```bash
# Check docker network
docker network ls

# Check container logs
docker compose logs master
docker compose logs worker

# Restart all services
docker compose down
docker compose up --scale worker=4
```

### Issue: Out of Memory

**Error:** `MemoryError` or containers crashing

**Solutions:**
```bash
# Reduce worker count
docker compose up --scale worker=2

# Increase Docker memory limit (Mac/Windows)
# Settings > Resources > Memory > Increase to 8GB or more

# Check resource usage
docker stats
```

### Issue: High CPU Usage

**Error:** Services using 100% CPU

**Solutions:**
```bash
# Reduce spawn rate in Web UI
# Or via command:
locust -f locustfile.py --spawn-rate 10

# Reduce number of workers
docker compose up --scale worker=2
```

### Issue: Network Errors in WebSocket

**Error:** `SSL error`, `Certificate verify failed`

**Solutions:**
```bash
# In .env, set
WS_VERIFY_SSL=false

# Or fix certificate issue:
# Ensure WS_URL points to valid domain
# Check certificate expiration
```

### Issue: GraphQL Errors

**Error:** `401 Unauthorized` or `GraphQL error`

**Solutions:**
```bash
# Check GRAPHQL_AUTH in .env
cat .env | grep GRAPHQL

# Verify token is valid
# Check GRAPHQL_URL is correct
```

### Debug: View All Environment Variables

```bash
# Check what Docker Compose loaded
docker compose config | grep -A 50 "environment:"

# Check running container variables
docker exec <container-id> env
```

### Clean Restart

```bash
# Remove everything and start fresh
docker compose down -v
LOCUST_USER=WebSocketUser docker compose up --scale worker=4
```

---

## Performance Comparison

| Method | Setup Time | Scaling | Flexibility | Best For |
|--------|-----------|---------|------------|----------|
| CLI | 2 min | Manual | Very high | Development |
| Helper Script | 1 min | Automatic | High | Quick testing |
| Docker Compose | 1 min | Automatic | Medium | Production |

---

## Next Steps

1. Configure `.env` with your API credentials
2. Choose a method (Docker Compose recommended)
3. Select your user type (WebSocketUser, GraphQLUser, or Adspace)
4. Run the test
5. Monitor from http://localhost:8089

---

## Additional Resources

- [Locust Documentation](https://docs.locust.io)
- [Testing Other Systems/Protocols in Locust](https://docs.locust.io/en/2.0.0/testing-other-systems.html)
- [Distributed Load Testing](https://docs.locust.io/en/stable/running-in-docker.html)
- Client implementations: See `clients/` directory
- Task definitions: See `locustfile.py`
