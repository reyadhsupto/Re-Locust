import websocket
import json
import time
from locust import events
import logging
import ssl
from threading import Lock
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


# Global connection pool to reuse WebSocket connections
_ws_pool = {}
_pool_lock = Lock()


class WebSocketClient:
    """
    Custom WebSocket client for Locust load testing with connection pooling.
    Provides an interface similar to Locust's HTTP client for WebSocket connections.
    Supports custom headers and query parameters.
    Reuses connections to avoid excessive connections from the same IP.
    """

    def __init__(self, base_url, timeout=10, verify_ssl=False, pool_connections=True, headers=None, params=None):
        """
        Initialize WebSocket client.
        
        Args:
            base_url: WebSocket URL (e.g., 'ws://localhost:8000/ws')
            timeout: Connection timeout in seconds (default: 10)
            verify_ssl: Whether to verify SSL certificates (default: False for testing)
            pool_connections: Whether to use connection pooling (default: True)
            headers: (Optional) Dict of custom headers to send with the connection
                     (e.g., {'Authorization': 'Bearer token', 'Custom': 'value'})
            params: (Optional) Dict of query parameters to append to URL
                    (e.g., {'token': 'abc123', 'user_id': '123'})
                    Multiple params are automatically joined with '&'
        
        Note:
            - headers and params are optional and default to empty dict
            - If not provided, no additional headers or query params will be sent
        """
        self.base_url = base_url
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.pool_connections = pool_connections
        self.headers = headers or {}
        self.params = params or {}
        self.ws = None
        self.is_connected = False
        self.is_pooled = False  # Whether this connection came from the pool
    
    def _build_url(self, url=None):
        """
        Build the final URL with query parameters.
        
        Args:
            url: Optional override URL
            
        Returns:
            Complete URL with query parameters
        """
        url = url or self.base_url
        if self.params:
            query_string = urlencode(self.params)
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{query_string}"
        return url

    def connect(self, url=None, headers=None, params=None):
        """
        Connect to WebSocket server. Uses pooling to reuse connections when possible.
        
        Args:
            url: Optional override URL. If not provided, uses base_url
            headers: Optional override headers. If not provided, uses self.headers
            params: Optional override params. If not provided, uses self.params
            
        Returns:
            Connection response or error
        """
        # Use provided headers/params or fall back to instance defaults
        headers = headers or self.headers
        params = params or self.params
        
        # Build URL with query parameters
        final_url = url or self.base_url
        if params:
            query_string = urlencode(params)
            separator = "&" if "?" in final_url else "?"
            final_url = f"{final_url}{separator}{query_string}"
        
        start_time = time.time()
        
        # Try to get a pooled connection if enabled
        if self.pool_connections:
            with _pool_lock:
                if final_url in _ws_pool and _ws_pool[final_url]['ws']:
                    try:
                        # Test if the pooled connection is still alive
                        pooled_ws = _ws_pool[final_url]['ws']
                        pooled_ws.ping()  # Send ping to verify connection
                        self.ws = pooled_ws
                        self.is_connected = True
                        self.is_pooled = True
                        response_time = (time.time() - start_time) * 1000
                        logger.info(f"WebSocket reused from pool: {final_url}")
                        return {"status": "connected", "response_time": response_time, "pooled": True}
                    except Exception as pool_error:
                        logger.debug(f"Pooled connection failed, creating new: {pool_error}")
                        _ws_pool[final_url] = {'ws': None}
        
        try:
            # Create SSL context if using wss protocol
            sslopt = None
            if final_url.startswith("wss://"):
                sslopt = {"cert_reqs": ssl.CERT_NONE, "check_hostname": False} if not self.verify_ssl else {}
            
            # Create connection with custom headers
            self.ws = websocket.create_connection(
                final_url, 
                timeout=self.timeout, 
                sslopt=sslopt,
                header=self._format_headers(headers) if headers else None
            )
            self.is_connected = True
            self.is_pooled = False
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Store connection in pool if pooling is enabled
            if self.pool_connections:
                with _pool_lock:
                    _ws_pool[final_url] = {'ws': self.ws}
            
            # Fire success event for Locust stats
            events.request.fire(
                request_type="WebSocket",
                name="connect",
                response_time=response_time,
                response_length=0,
                exception=None
            )
            
            logger.info(f"WebSocket connected to {final_url}")
            return {"status": "connected", "response_time": response_time, "pooled": False}
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.is_connected = False
            
            # Fire failure event for Locust stats
            events.request.fire(
                request_type="WebSocket",
                name="connect",
                response_time=response_time,
                response_length=0,
                exception=e
            )
            
            logger.error(f"WebSocket connection failed: {e}")
            return {"status": "error", "message": str(e), "response_time": response_time}
    
    def _format_headers(self, headers):
        """
        Format headers dict for websocket-client library.
        Converts {'Header-Name': 'value'} to ['Header-Name: value']
        
        Args:
            headers: Dict of headers
            
        Returns:
            List of formatted header strings
        """
        if not headers:
            return None
        return [f"{key}: {value}" for key, value in headers.items()]

    def send(self, message, name="send"):
        """
        Send a message over WebSocket.
        
        Args:
            message: Message to send (dict or string)
            name: Request name for Locust stats
            
        Returns:
            Response data or error
        """
        if not self.is_connected:
            logger.error("WebSocket not connected")
            return {"status": "error", "message": "WebSocket not connected"}
        
        start_time = time.time()
        
        try:
            if isinstance(message, dict):
                message = json.dumps(message)
            
            self.ws.send(message)
            response_time = (time.time() - start_time) * 1000
            
            events.request.fire(
                request_type="WebSocket",
                name=name,
                response_time=response_time,
                response_length=len(message),
                exception=None
            )
            
            logger.debug(f"WebSocket message sent: {message}")
            return {"status": "sent", "response_time": response_time}
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            events.request.fire(
                request_type="WebSocket",
                name=name,
                response_time=response_time,
                response_length=0,
                exception=e
            )
            
            logger.error(f"WebSocket send failed: {e}")
            return {"status": "error", "message": str(e), "response_time": response_time}

    def receive(self, name="receive", timeout=None):
        """
        Receive a message from WebSocket.
        
        Args:
            name: Request name for Locust stats
            timeout: Optional timeout override
            
        Returns:
            Received message or error
        """
        if not self.is_connected:
            logger.error("WebSocket not connected")
            return {"status": "error", "message": "WebSocket not connected"}
        
        start_time = time.time()
        timeout_val = timeout or self.timeout
        
        try:
            self.ws.settimeout(timeout_val)
            message = self.ws.recv()
            response_time = (time.time() - start_time) * 1000
            
            # Try to parse as JSON
            try:
                data = json.loads(message)
            except:
                data = message
            
            events.request.fire(
                request_type="WebSocket",
                name=name,
                response_time=response_time,
                response_length=len(message),
                exception=None
            )
            
            logger.debug(f"WebSocket message received: {message}")
            return {"status": "received", "data": data, "response_time": response_time}
            
        except websocket.WebSocketTimeoutException:
            response_time = (time.time() - start_time) * 1000
            
            events.request.fire(
                request_type="WebSocket",
                name=name,
                response_time=response_time,
                response_length=0,
                exception=Exception("WebSocket receive timeout")
            )
            
            logger.error(f"WebSocket receive timeout after {response_time}ms")
            return {"status": "timeout", "response_time": response_time}
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            events.request.fire(
                request_type="WebSocket",
                name=name,
                response_time=response_time,
                response_length=0,
                exception=e
            )
            
            logger.error(f"WebSocket receive failed: {e}")
            return {"status": "error", "message": str(e), "response_time": response_time}

    def disconnect(self):
        """
        Close WebSocket connection (or return to pool if pooling is enabled).
        Pooled connections are NOT closed, they're reused by other clients.
        """
        if self.ws and self.is_connected:
            try:
                # Don't close pooled connections - they'll be reused
                if not self.is_pooled:
                    self.ws.close()
                    logger.info("WebSocket disconnected")
                else:
                    logger.info("WebSocket connection returned to pool")
                self.is_connected = False
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
