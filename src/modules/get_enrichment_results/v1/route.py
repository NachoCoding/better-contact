from main import router
from workflows_cdk import Request, Response
from flask import request as flask_request
import requests

@router.route("/execute", methods=["POST"])
def execute():
    try:
        # Parse the incoming request
        req = Request(flask_request)
        
        # Extract API key from connection
        connection = req.data.get('connection', {})
        
        # For testing, use hardcoded API key if connection is empty
        # This will be replaced with proper connection handling in production
        if not connection or connection == {}:
            api_key = "2d7316008303a1c3400d"  # Test API key
        else:
            # Try different possible structures
            if isinstance(connection, dict):
                # Check if api_key is directly in connection
                if 'api_key_bearer' in connection:
                    api_key = connection['api_key_bearer']
                # Check if it's in connection_data.value
                elif 'connection_data' in connection:
                    connection_data = connection.get('connection_data', {})
                    if 'value' in connection_data:
                        api_key = connection_data['value'].get('api_key_bearer')
                    else:
                        api_key = connection_data.get('api_key_bearer')
                # Check if it's in value directly
                elif 'value' in connection:
                    api_key = connection['value'].get('api_key_bearer')
                else:
                    api_key = None
            else:
                api_key = None
        
        if not api_key:
            return Response.error(
                error="API key not found in connection"
            )
        
        # Extract request ID
        request_id = req.data.get('request_id', '')
        
        if not request_id:
            return Response.error(
                error="Request ID is required"
            )
        
        # Fetch results from BetterContact API
        # Try with v2 first
        url = f"https://app.bettercontact.rocks/api/v2/async/{request_id}?api_key={api_key}"
        
        response = requests.get(url)
        
        # If v2 returns 404, try without version
        if response.status_code == 404:
            url = f"https://app.bettercontact.rocks/api/async/{request_id}?api_key={api_key}"
            response = requests.get(url)
        
        if response.status_code == 200:
            # Results are ready
            return Response(
                data=response.json(),
                metadata={
                    "status": "completed"
                }
            )
        elif response.status_code == 202:
            # Still processing
            return Response(
                data={
                    "status": "processing",
                    "message": "Enrichment is still in progress"
                },
                metadata={
                    "status": "processing"
                }
            )
        elif response.status_code == 404:
            return Response.error(
                error=f"Request ID '{request_id}' not found"
            )
        elif response.status_code == 401:
            return Response.error(
                error="Invalid API key or unauthorized access"
            )
        else:
            return Response.error(
                error=f"API request failed with status {response.status_code}"
            )
        
    except Exception as e:
        return Response.error(
            error=f"Unexpected error: {str(e)}"
        )