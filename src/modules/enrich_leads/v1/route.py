from main import router
from workflows_cdk import Request, Response
from flask import request as flask_request
import requests
import uuid

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
        
        # Extract lead data from individual fields
        first_name = req.data.get('first_name', '')
        last_name = req.data.get('last_name', '')
        company = req.data.get('company', '')
        company_domain = req.data.get('company_domain', '')
        linkedin_url = req.data.get('linkedin_url', '')
        
        # Validate required fields
        if not first_name:
            return Response.error(
                error="First name is required"
            )
            
        if not last_name:
            return Response.error(
                error="Last name is required"
            )
            
        if not company and not company_domain:
            return Response.error(
                error="Either company name or company domain is required"
            )
        
        # Extract enrichment options
        enrich_email = req.data.get('enrich_email_address', True)
        enrich_phone = req.data.get('enrich_phone_number', True)
        
        # Build lead object
        lead_data = {
            "first_name": first_name,
            "last_name": last_name,
            "custom_fields": {
                "uuid": str(uuid.uuid4()),
                "list_name": "StackSync Single Lead"
            }
        }
        
        if company:
            lead_data['company'] = company
        if company_domain:
            lead_data['company_domain'] = company_domain
        if linkedin_url:
            lead_data['linkedin_url'] = linkedin_url
        
        # Build request body with single lead in array
        request_body = {
            "data": [lead_data],  # API expects array even for single lead
            "enrich_email_address": enrich_email,
            "enrich_phone_number": enrich_phone
        }
        
        # Submit to BetterContact API
        url = f"https://app.bettercontact.rocks/api/v2/async?api_key={api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=request_body, headers=headers)
        
        if response.status_code == 401:
            return Response.error(
                error="Invalid API key or unauthorized access"
            )
        elif response.status_code == 400:
            error_msg = response.json().get('message', 'Bad request')
            return Response.error(
                error=f"Invalid request: {error_msg}"
            )
        elif response.status_code != 201:
            return Response.error(
                error=f"API request failed with status {response.status_code}"
            )
        
        # Return the response data
        response_data = response.json()
        
        return Response(
            data={
                "request_id": response_data.get("id", ""),
                "status": "submitted",
                "lead": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "company": company or company_domain
                }
            },
            metadata={
                "api_response": response_data
            }
        )
        
    except Exception as e:
        return Response.error(
            error=f"Unexpected error: {str(e)}"
        )