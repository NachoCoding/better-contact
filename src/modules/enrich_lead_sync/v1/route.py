from main import router
from workflows_cdk import Request, Response
from flask import request as flask_request
import requests
import uuid
import time

@router.route("/execute", methods=["POST"])
def execute():
    """
    Synchronous lead enrichment function that combines submission and result retrieval.
    Follows the two-phase process strategy with smart polling and comprehensive error handling.
    """
    try:
        # Parse the incoming request
        req = Request(flask_request)
        
        # Extract API key from connection
        connection = req.data.get('connection', {})
        
        # For testing, use hardcoded API key if connection is empty
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
                "list_name": "StackSync Sync Lead"
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
        
        # Step 1: Submit to BetterContact API
        submit_url = f"https://app.bettercontact.rocks/api/v2/async?api_key={api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            submit_response = requests.post(submit_url, json=request_body, headers=headers, timeout=30)
        except requests.exceptions.Timeout:
            return Response.error(
                error="Timeout while submitting lead for enrichment"
            )
        except requests.exceptions.ConnectionError:
            return Response.error(
                error="Network error: Unable to connect to BetterContact API"
            )
        except requests.exceptions.RequestException as e:
            return Response.error(
                error=f"Request error during submission: {str(e)}"
            )
        
        # Handle submission response
        if submit_response.status_code == 401:
            return Response.error(
                error="Invalid API key or unauthorized access"
            )
        elif submit_response.status_code == 400:
            try:
                error_msg = submit_response.json().get('message', 'Bad request')
            except:
                error_msg = 'Bad request'
            return Response.error(
                error=f"Invalid request: {error_msg}"
            )
        elif submit_response.status_code != 201:
            return Response.error(
                error=f"API submission failed with status {submit_response.status_code}"
            )
        
        # Get the request ID from submission
        try:
            submit_data = submit_response.json()
            request_id = submit_data.get("id", "")
        except:
            return Response.error(
                error="Invalid response format from BetterContact submission"
            )
        
        if not request_id:
            return Response.error(
                error="No request ID returned from BetterContact"
            )
        
        # Step 2: Poll for results with smart waiting strategy
        results_url = f"https://app.bettercontact.rocks/api/v2/async/{request_id}?api_key={api_key}"
        
        # Polling configuration
        max_wait_time = 45  # 45 seconds total timeout
        initial_delay = 2   # Start with 2 seconds
        max_delay = 5       # Max 5 seconds between checks
        elapsed_time = 0
        poll_count = 0
        
        # Initial delay to allow API to register the request
        time.sleep(1)
        
        while elapsed_time < max_wait_time:
            # Calculate dynamic delay (increases with each poll, up to max_delay)
            current_delay = min(initial_delay + (poll_count * 0.5), max_delay)
            
            # Wait before checking (except on first iteration)
            if poll_count > 0:
                time.sleep(current_delay)
                elapsed_time += current_delay
            
            # Check for results
            try:
                results_response = requests.get(results_url, timeout=10)
            except requests.exceptions.Timeout:
                return Response.error(
                    error=f"Timeout while checking enrichment results. Request ID: {request_id}"
                )
            except requests.exceptions.ConnectionError:
                return Response.error(
                    error=f"Network error while checking results. Request ID: {request_id}"
                )
            except requests.exceptions.RequestException as e:
                return Response.error(
                    error=f"Error checking results: {str(e)}. Request ID: {request_id}"
                )
            
            # Handle different response scenarios
            if results_response.status_code == 200:
                # Results are ready - return the full enrichment data
                try:
                    enrichment_data = results_response.json()
                    return Response(
                        data=enrichment_data,
                        metadata={
                            "request_id": request_id,
                            "processing_time_seconds": elapsed_time,
                            "poll_attempts": poll_count + 1,
                            "status": "completed"
                        }
                    )
                except:
                    return Response.error(
                        error="Invalid response format from enrichment results"
                    )
                    
            elif results_response.status_code == 202:
                # Still processing - check the response for status
                try:
                    response_data = results_response.json()
                    status = response_data.get('status', '').lower()
                    
                    if status == 'completed':
                        # Results are included in 202 response
                        return Response(
                            data=response_data,
                            metadata={
                                "request_id": request_id,
                                "processing_time_seconds": elapsed_time,
                                "poll_attempts": poll_count + 1,
                                "status": "completed"
                            }
                        )
                    elif status in ['failed', 'error']:
                        # Enrichment failed
                        error_message = response_data.get('message', 'Enrichment failed')
                        return Response.error(
                            error=f"Enrichment failed: {error_message}",
                            data={
                                "request_id": request_id,
                                "status": status
                            }
                        )
                    # Otherwise continue polling (status is 'in progress' or similar)
                except:
                    # If we can't parse the response, continue polling
                    pass
                    
            elif results_response.status_code == 404:
                return Response.error(
                    error=f"Request ID '{request_id}' not found. It may have expired or been invalid."
                )
            elif results_response.status_code == 401:
                return Response.error(
                    error="Authentication failed while checking results"
                )
            elif results_response.status_code == 406:
                # Handle the "Unvalid request_id" error
                if poll_count == 0:
                    # If it fails on first attempt, wait a bit more and retry
                    time.sleep(2)
                    elapsed_time += 2
                else:
                    return Response.error(
                        error=f"Invalid request ID format: {request_id}"
                    )
            else:
                # Unexpected status code
                return Response.error(
                    error=f"Unexpected response status {results_response.status_code} while checking results"
                )
            
            poll_count += 1
            
            # Add some progress tracking for long-running enrichments
            if elapsed_time > 20 and poll_count % 3 == 0:
                print(f"Still waiting for enrichment... {elapsed_time}s elapsed")
        
        # Timeout reached
        return Response.error(
            error=f"Enrichment timeout after {max_wait_time} seconds. The request may still be processing. Request ID: {request_id}",
            data={
                "request_id": request_id,
                "status": "timeout",
                "elapsed_seconds": elapsed_time
            }
        )
        
    except Exception as e:
        # Catch-all for unexpected errors
        return Response.error(
            error=f"Unexpected error in synchronous enrichment: {str(e)}"
        )