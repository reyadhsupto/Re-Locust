# Locust Custom Clients

This directory contains custom client implementations for Locust load testing.

## Available Clients

### WebSocketClient
A WebSocket client with connection pooling and custom header/parameter support.

**Features:**
- WebSocket connection pooling to reduce connections from the same IP
- Custom headers and query parameters support
- Automatic SSL/TLS handling
- Request/response tracking integrated with Locust stats

**Usage:**
```python
from clients import WebSocketClient

# Basic usage
client = WebSocketClient("ws://localhost:8000/ws")
result = client.connect()
client.send({"message": "hello"})
data = client.receive()
client.disconnect()

# With headers and params
client = WebSocketClient(
    "ws://localhost:8000/ws",
    headers={"Authorization": "Bearer token"},
    params={"user_id": "123"}
)
result = client.connect()

# Connection pooling is enabled by default
# Disable it if needed
client = WebSocketClient(url, pool_connections=False)
```

**Methods:**
- `connect(url=None, headers=None, params=None)` - Connect to WebSocket server
- `send(message, name="send")` - Send a message
- `receive(name="receive", timeout=None)` - Receive a message
- `disconnect()` - Close the connection

### GraphQLClient
A GraphQL client for testing GraphQL APIs with batch query support.

**Features:**
- Query and mutation support
- Batch query support
- Variable and operation name support
- Custom headers and query parameters
- GraphQL error handling and tracking

**Usage:**
```python
from clients import GraphQLClient

# Basic usage
client = GraphQLClient("https://api.example.com/graphql")

# Send a query
query = """
    query GetUser($id: ID!) {
        user(id: $id) {
            id
            name
            email
        }
    }
"""
result = client.query(query, variables={"id": "123"})

# Send a mutation
mutation = """
    mutation CreateUser($name: String!) {
        createUser(name: $name) {
            id
            name
        }
    }
"""
result = client.mutation(mutation, variables={"name": "John"})

# Batch query
batch = [
    {"query": query1, "variables": {"id": "1"}},
    {"query": query2, "variables": {"id": "2"}},
]
result = client.batch_query(batch)

# With headers and params
client = GraphQLClient(
    "https://api.example.com/graphql",
    headers={"Authorization": "Bearer token"},
    params={"api_version": "v2"}
)
```

**Methods:**
- `query(query_string, variables=None, operation_name=None, name="query")` - Send a GraphQL query
- `mutation(mutation_string, variables=None, operation_name=None, name="mutation")` - Send a GraphQL mutation
- `batch_query(queries_list, name="batch_query")` - Send multiple queries as a batch

## Integration with Locust

Both clients automatically fire Locust `request` events with timing and exception information, which are tracked in the Locust statistics dashboard.

## Optional Parameters

Both clients support optional headers and query parameters:

```python
# Headers are optional
client = WebSocketClient(url, headers={"Authorization": "Bearer token"})

# Query params are optional - multiple params automatically joined with &
client = WebSocketClient(url, params={"token": "abc", "user_id": "123"})
# Results in: ws://localhost:8000/ws?token=abc&user_id=123
```

## SSL/TLS

For WebSocket connections using `wss://` protocol:
```python
# Disable SSL verification (useful for testing with self-signed certificates)
client = WebSocketClient("wss://localhost:8000/ws", verify_ssl=False)

# Enable SSL verification
client = WebSocketClient("wss://localhost:8000/ws", verify_ssl=True)
```

## Connection Pooling

WebSocket connections can be pooled to reduce the number of connections from the same IP:

```python
# Enable pooling (default)
client = WebSocketClient(url, pool_connections=True)

# Disable pooling
client = WebSocketClient(url, pool_connections=False)
```

When pooling is enabled, connections are reused across multiple users in the same process, significantly reducing the number of simultaneous connections.
