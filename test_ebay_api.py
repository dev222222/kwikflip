# test_ebay_api.py
import os
import requests
import base64
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials
app_id = os.getenv("EBAY_APP_ID")
cert_id = os.getenv("EBAY_CERT_ID")

print(f"App ID available: {'Yes' if app_id else 'No'}")
print(f"Cert ID available: {'Yes' if cert_id else 'No'}")

# Test OAuth token process
def get_oauth_token():
    # Create auth string
    auth_string = f"{app_id}:{cert_id}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    # OAuth endpoint
    oauth_url = "https://api.ebay.com/identity/v1/oauth2/token"
    
    # Request headers
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_auth}"
    }
    
    # Request body
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/buy.item.feed"
    }
    
    # Make the request
    response = requests.post(
        oauth_url,
        headers=headers,
        data=data
    )
    
    print(f"OAuth Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

# Test Browse API
def test_browse_api(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        "Content-Type": "application/json"
    }
    
    # Simple search for "iphone"
    url = "https://api.ebay.com/buy/browse/v1/item_summary/search?q=iphone&limit=3"
    
    response = requests.get(url, headers=headers)
    
    print(f"Browse API Status: {response.status_code}")
    print(f"Found items: {json.dumps(response.json(), indent=2)[:500]}...")

# Run the tests
token = get_oauth_token()
if token:
    print("\n✅ Successfully got OAuth token!")
    test_browse_api(token)
else:
    print("\n❌ Failed to get OAuth token")