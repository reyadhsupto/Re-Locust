"""
Locust custom clients for load testing.

This package contains custom client implementations for load testing:
- WebSocketClient: For WebSocket API testing with connection pooling
- GraphQLClient: For GraphQL API testing with batch support
"""

from .websocket_client import WebSocketClient
from .graphql_client import GraphQLClient

__all__ = ["WebSocketClient", "GraphQLClient"]
