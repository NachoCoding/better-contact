import requests
import json
import time

BASE_URL = "http://localhost:2003"
API_KEY = "2d7316008303a1c3400d"

def test_check_credits_balance():
    print("\n=== Testing Check Credits Balance Module ===")
    
    # Test 1: Valid API key
    print("\nTest 1: Valid API key")
    payload = {
        "connection": {
            "connection_data": {
                "value": {
                    "api_key_bearer": API_KEY
                }
            }
        }
    }
    response = requests.post(f"{BASE_URL}/modules/check_credits_balance/v1/execute", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 2: Invalid API key
    print("\nTest 2: Invalid API key")
    payload["connection"]["connection_data"]["value"]["api_key_bearer"] = "invalid_key_123"
    response = requests.post(f"{BASE_URL}/modules/check_credits_balance/v1/execute", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 3: Missing connection
    print("\nTest 3: Missing connection")
    response = requests.post(f"{BASE_URL}/modules/check_credits_balance/v1/execute", json={})
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_enrich_leads():
    print("\n=== Testing Enrich Leads Module ===")
    
    # Test 1: Valid request with single lead
    print("\nTest 1: Valid request with single lead")
    payload = {
        "connection": {
            "connection_data": {
                "value": {
                    "api_key_bearer": API_KEY
                }
            }
        },
        "leads": [
            {
                "first_name": "John",
                "last_name": "Doe",
                "company": "Example Corp",
                "company_domain": "example.com"
            }
        ],
        "enrich_email_address": True,
        "enrich_phone_number": True
    }
    response = requests.post(f"{BASE_URL}/modules/enrich_leads/v1/execute", json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    # Save request_id for later test
    request_id = result.get("data", {}).get("request_id", "")
    
    # Test 2: Multiple leads
    print("\nTest 2: Multiple leads (3)")
    payload["leads"] = [
        {"first_name": "Jane", "last_name": "Smith", "company": "Tech Co"},
        {"first_name": "Bob", "company_domain": "startup.io"},
        {"linkedin_url": "https://linkedin.com/in/example"}
    ]
    response = requests.post(f"{BASE_URL}/modules/enrich_leads/v1/execute", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 3: Empty leads array
    print("\nTest 3: Empty leads array")
    payload["leads"] = []
    response = requests.post(f"{BASE_URL}/modules/enrich_leads/v1/execute", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 4: Too many leads (> 100)
    print("\nTest 4: Too many leads (101)")
    payload["leads"] = [{"first_name": f"User{i}"} for i in range(101)]
    response = requests.post(f"{BASE_URL}/modules/enrich_leads/v1/execute", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return request_id

def test_get_enrichment_results(request_id):
    print("\n=== Testing Get Enrichment Results Module ===")
    
    # Test 1: Valid request ID
    print(f"\nTest 1: Valid request ID: {request_id}")
    payload = {
        "connection": {
            "connection_data": {
                "value": {
                    "api_key_bearer": API_KEY
                }
            }
        },
        "request_id": request_id
    }
    response = requests.post(f"{BASE_URL}/modules/get_enrichment_results/v1/execute", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 2: Invalid request ID
    print("\nTest 2: Invalid request ID")
    payload["request_id"] = "invalid-request-id-12345"
    response = requests.post(f"{BASE_URL}/modules/get_enrichment_results/v1/execute", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 3: Missing request ID
    print("\nTest 3: Missing request ID")
    del payload["request_id"]
    response = requests.post(f"{BASE_URL}/modules/get_enrichment_results/v1/execute", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_module_schemas():
    print("\n=== Testing Module Schemas ===")
    
    modules = ["check_credits_balance", "enrich_leads", "get_enrichment_results"]
    
    for module in modules:
        print(f"\nTesting schema for {module}")
        response = requests.get(f"{BASE_URL}/modules/{module}/v1/schema")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Schema loaded successfully")
        else:
            print(f"Error: {response.text}")

if __name__ == "__main__":
    print("Starting comprehensive testing of BetterContact connector...")
    
    # Test module schemas
    test_module_schemas()
    
    # Test Check Credits Balance
    test_check_credits_balance()
    
    # Test Enrich Leads and get request ID
    request_id = test_enrich_leads()
    
    # Wait a bit for async processing
    if request_id:
        print("\nWaiting 2 seconds before testing results...")
        time.sleep(2)
        test_get_enrichment_results(request_id)
    
    print("\n=== Testing Complete ===")