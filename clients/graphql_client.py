import requests
import json
import time
from locust import events
import logging

logger = logging.getLogger(__name__)


class GraphQLClient:
    """
    Custom GraphQL client for Locust load testing.
    Provides a simple interface for sending GraphQL queries and mutations.
    Integrates with Locust's event system for statistics tracking.
    """

    def __init__(self, endpoint, timeout=10, headers=None, params=None):
        """
        Initialize GraphQL client.
        
        Args:
            endpoint: GraphQL API endpoint URL (e.g., 'https://api.example.com/graphql')
            timeout: Request timeout in seconds (default: 10)
            headers: (Optional) Dict of custom headers to send with requests
                     (e.g., {'Authorization': 'Bearer token', 'Custom': 'value'})
            params: (Optional) Dict of query parameters to append to URL
                    (e.g., {'api_key': 'abc123'})
                    Multiple params are automatically joined with '&'
        
        Note:
            - headers and params are optional and default to empty dict
            - If not provided, default headers for GraphQL are set
        """
        self.endpoint = endpoint
        self.timeout = timeout
        self.headers = headers or {}
        self.params = params or {}
        
        # Set default GraphQL headers if not provided
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"

    def query(self, query_string:str, variables:dict=None, operation_name=None, name="query"):
        """
        Send a GraphQL query to the server.
        
        Args:
            query_string: GraphQL query string
            variables: (Optional) Dict of variables for the query
            operation_name: (Optional) Name of the operation to execute
            name: Request name for Locust stats (default: "query")
            
        Returns:
            Response data or error
        """
        payload = {
            "query": query_string
        }
        
        if variables:
            payload["variables"] = variables
        
        if operation_name:
            payload["operationName"] = operation_name
        
        return self._send_request(payload, name)

    def mutation(self, mutation_string, variables=None, operation_name=None, name="mutation"):
        """
        Send a GraphQL mutation to the server.
        
        Args:
            mutation_string: GraphQL mutation string
            variables: (Optional) Dict of variables for the mutation
            operation_name: (Optional) Name of the operation to execute
            name: Request name for Locust stats (default: "mutation")
            
        Returns:
            Response data or error
        """
        payload = {
            "query": mutation_string
        }
        
        if variables:
            payload["variables"] = variables
        
        if operation_name:
            payload["operationName"] = operation_name
        
        return self._send_request(payload, name)

    def _send_request(self, payload, name):
        """
        Send a GraphQL request to the server.
        
        Args:
            payload: GraphQL request payload (dict with 'query', 'variables', 'operationName')
            name: Request name for Locust stats
            
        Returns:
            Response data or error
        """
        start_time = time.time()
        
        # Build URL with params
        url = self.endpoint
        if self.params:
            from urllib.parse import urlencode
            query_string = urlencode(self.params)
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{query_string}"
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            
            response_time = (time.time() - start_time) * 1000
            response_data = response.json() if response.text else {}
            
            # Check for GraphQL errors
            if "errors" in response_data:
                error_msg = response_data["errors"][0].get("message", "Unknown error") if response_data["errors"] else "Unknown error"
                
                events.request.fire(
                    request_type="GraphQL",
                    name=name,
                    response_time=response_time,
                    response_length=len(response.text),
                    exception=Exception(error_msg)
                )
                
                logger.warning(f"GraphQL error: {error_msg}")
                return {
                    "status": "error",
                    "message": error_msg,
                    "errors": response_data.get("errors"),
                    "response_time": response_time
                }
            
            # Success
            events.request.fire(
                request_type="GraphQL",
                name=name,
                response_time=response_time,
                response_length=len(response.text)
            )
            
            logger.debug(f"GraphQL {name} successful")
            return {
                "status": "success",
                "data": response_data.get("data"),
                "response_time": response_time
            }
            
        except requests.exceptions.Timeout:
            response_time = (time.time() - start_time) * 1000
            
            events.request.fire(
                request_type="GraphQL",
                name=name,
                response_time=response_time,
                response_length=0,
                exception=Exception("Request timeout")
            )
            
            logger.error(f"GraphQL request timeout after {response_time}ms")
            return {
                "status": "timeout",
                "message": "Request timeout",
                "response_time": response_time
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            events.request.fire(
                request_type="GraphQL",
                name=name,
                response_time=response_time,
                response_length=0,
                exception=e
            )
            
            logger.error(f"GraphQL request failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "response_time": response_time
            }

    def batch_query(self, queries_list, name="batch_query"):
        """
        Send multiple GraphQL queries as a batch.
        
        Args:
            queries_list: List of query dicts, each with 'query', 'variables' (optional), 'operationName' (optional)
            name: Request name for Locust stats (default: "batch_query")
            
        Returns:
            Response data or error
        """
        start_time = time.time()
        
        # Build URL with params
        url = self.endpoint
        if self.params:
            from urllib.parse import urlencode
            query_string = urlencode(self.params)
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{query_string}"
        
        try:
            response = requests.post(
                url,
                json=queries_list,
                headers=self.headers,
                timeout=self.timeout
            )
            
            response_time = (time.time() - start_time) * 1000
            response_data = response.json() if response.text else {}
            
            # Check for errors in any of the batch responses
            has_errors = False
            if isinstance(response_data, list):
                for item in response_data:
                    if "errors" in item:
                        has_errors = True
                        break
            elif "errors" in response_data:
                has_errors = True
            
            if has_errors:
                events.request.fire(
                    request_type="GraphQL",
                    name=name,
                    response_time=response_time,
                    response_length=len(response.text),
                    exception=Exception("Batch query had errors")
                )
                
                logger.warning(f"GraphQL batch query had errors")
                return {
                    "status": "error",
                    "message": "Batch query had errors",
                    "data": response_data,
                    "response_time": response_time
                }
            
            # Success
            events.request.fire(
                request_type="GraphQL",
                name=name,
                response_time=response_time,
                response_length=len(response.text),
                exception=None
            )
            
            logger.debug(f"GraphQL batch query successful")
            return {
                "status": "success",
                "data": response_data,
                "response_time": response_time
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            events.request.fire(
                request_type="GraphQL",
                name=name,
                response_time=response_time,
                response_length=0,
                exception=e
            )
            
            logger.error(f"GraphQL batch query failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "response_time": response_time
            }
